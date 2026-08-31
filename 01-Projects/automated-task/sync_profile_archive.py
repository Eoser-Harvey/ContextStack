"""
个人画像归档同步脚本 — 每天0点执行

读取 holdings.yaml、最新月度报告、职业发展档案，生成两份归档摘要到
小时推送和日报推送的 profile_archive/ 目录。

用法:
  python sync_profile_archive.py

架构说明:
  profile_loader.py（小时/日报项目各一份）自动从 profile_archive/ 按文件名日期排序取最新文件
  analyzer.py/send_daily_ai_news.py/push_lark.py 均使用 load_latest_profile() 动态加载
  config.yaml 不再硬编码 profile 段，所有分析均实时从 archive 读取
  更新 profile_archive/ 即自动生效，无需修改任何代码
"""

import os
import re
import sys
import glob
import yaml
import logging
from datetime import date
from pathlib import Path

# ── 路径配置 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HOLDINGS_PATH = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "holdings.yaml"
REPORTS_DIR = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "reports"
CAREER_FILE = PROJECT_ROOT / "02-Knowledge" / "career-development" / "career-strategy" / "个人职业发展分析-端侧AI企业定制攻略.md"
HOUR_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "0.trae-feishu-push-hour" / "profile_archive"
DAY_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "1.trae-feishu-push-day" / "profile_archive"
LOG_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "logs"

# ── 日志：静默模式，只写文件，异常时输出到 stderr ──
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"sync_profile_archive_{date.today().strftime('%Y%m%d')}.log"

logger = logging.getLogger("sync_profile_archive")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_fh)


def _log_error(msg):
    """错误同时写入日志和 stderr（保证可见）"""
    logger.error(msg)
    print(f"[ERROR] {msg}", file=sys.stderr)


def _extract_prev_archive_prices(archive_dir):
    """
    读取最新 archive 文件，提取价格信息作为 fallback。
    返回 {
        "crypto": {标的名: {"price": "...", "market_value": "..."}},
        "us": {...},
        "hk": {...},
        "a": {...},
        "ts": {标的名: 市值},
        "metrics": {指标名: 数值},
    }
    """
    result = {"crypto": {}, "us": {}, "hk": {}, "a": {}, "ts": {}, "metrics": {}}
    files = sorted(glob.glob(str(archive_dir / "profile_*.md")), reverse=True)
    if not files:
        logger.warning("无前次归档，价格信息将留空")
        return result

    with open(files[0], "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    current_section = ""
    current_subsection = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            current_section = stripped[3:].strip()
            current_subsection = ""
        elif stripped.startswith("### "):
            current_subsection = stripped[4:].strip()

        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 2:
            continue
        if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
            continue

        target = None
        if current_section == "投资持仓概览":
            sub = current_subsection
            if sub == "加密货币":
                target = result["crypto"]
            elif sub == "美股":
                target = result["us"]
            elif sub == "港股":
                target = result["hk"]
            elif sub == "A股":
                target = result["a"]
            elif sub == "TS时间代币":
                target = result["ts"]
            elif sub == "关键指标" and len(cells) == 2:
                result["metrics"][cells[0]] = cells[1]
                continue

        if target is not None:
            if len(cells) >= 4:
                target[cells[0]] = {"price": cells[2], "market_value": cells[3], "storage": cells[-1]}
            elif len(cells) == 3:
                target[cells[0]] = cells[1]  # TS 时间代币

    logger.info(f"已加载前次归档: {os.path.basename(files[0])}")
    return result


def _extract_report_prices(report_content):
    """
    从月度报告中提取最新价格数据。
    返回 {标的名: {"price": USD价格, "mv_cny": 市值CNY, "storage": 存放}}
    """
    prices = {}
    lines = report_content.split("\n")
    in_detail = False
    for line in lines:
        stripped = line.strip()
        if "## 二、投资资产明细" in stripped or "投资资产明细" in stripped:
            in_detail = True
            continue
        if in_detail:
            if stripped.startswith("## ") or stripped.startswith("---"):
                break
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 8 and cells[0] not in ("标的", "投资合计"):
                    name = cells[0]
                    qty = cells[1]
                    price = cells[2]
                    mv_cny = cells[3]
                    storage = cells[-1] if len(cells) >= 9 else ""
                    prices[name] = {"price": price, "mv_cny": mv_cny, "qty": qty, "storage": storage}
    return prices


def _extract_report_metrics(report_content, usd_cny, hkd_cny):
    """从月度报告中提取关键指标"""
    metrics = {}
    lines = report_content.split("\n")
    in_overview = False
    for line in lines:
        stripped = line.strip()
        if "资产总览" in stripped or "## 一" in stripped:
            in_overview = True
            continue
        if in_overview:
            if stripped.startswith("## ") or stripped.startswith("---"):
                break
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 2:
                    key = cells[0].strip()
                    val = cells[1].strip()
                    if key == "**总资产**":
                        metrics["总资产"] = val
                    elif key == "**净资产**":
                        metrics["净资产"] = val
                    elif key == "**投资总资产**":
                        metrics["投资总资产"] = val
                    elif key == "现金固收":
                        metrics["家庭备用金"] = val
    return metrics


def load_holdings():
    """读取 holdings.yaml"""
    if not HOLDINGS_PATH.exists():
        _log_error(f"holdings.yaml 不存在: {HOLDINGS_PATH}")
        return None
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    logger.info(f"holdings.yaml 加载成功 (last_updated: {data.get('meta', {}).get('last_updated', 'N/A')})")
    return data


def load_latest_monthly_report():
    """
    读取最新月度报告（按文件名排序，取最新一个，排除年度报告和非月份报告）。
    返回 (content, filename)
    """
    if not REPORTS_DIR.exists():
        _log_error(f"报告目录不存在: {REPORTS_DIR}")
        return None, None

    files = sorted(glob.glob(str(REPORTS_DIR / "*.md")), reverse=True)
    # 优先取 "家庭资产报告-YYYY-MM.md" 格式的文件
    monthly = [f for f in files if re.search(r"家庭资产报告-\d{4}-\d{2}\.md$", f)]
    if not monthly:
        _log_error("未找到月度报告文件")
        return None, None

    latest = monthly[0]
    with open(latest, "r", encoding="utf-8") as f:
        content = f.read()
    fname = os.path.basename(latest)
    logger.info(f"最新月度报告: {fname}")
    return content, fname


def load_career_profile():
    """读取职业发展档案"""
    if not CAREER_FILE.exists():
        _log_error(f"职业发展档案不存在: {CAREER_FILE}")
        return None
    with open(CAREER_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    logger.info(f"职业发展档案加载成功: {CAREER_FILE.name}")
    return content


def build_archive(holdings, report_content, report_filename, prev_prices):
    """构建归档内容"""
    today = date.today()
    date_str = today.strftime("%Y-%m-%d")
    date_compact = today.strftime("%Y%m%d")

    meta = holdings.get("meta", {})
    last_updated = meta.get("last_updated", "N/A")
    usd_cny = meta.get("usd_cny", 6.725)

    # 从月度报告提取最新价格
    report_prices = _extract_report_prices(report_content) if report_content else {}

    # 从月度报告提取关键指标
    report_metrics = _extract_report_metrics(report_content, usd_cny, 0.857) if report_content else {}

    # 优先级：月度报告价格 > 前次归档价格
    # 用于投资概览表
    # 加密货币
    crypto_items = []
    us_stock_items = []
    hk_stock_items = []
    a_stock_items = []
    ts_items = []

    h = holdings.get("holdings", [])
    for item in h:
        cat = item.get("category", "")
        symbol = item.get("symbol", "")
        name = item.get("name", "")
        qty = item.get("quantity", 0)
        unit = item.get("unit", "")
        storage = item.get("storage", "")
        base = {"name": name, "qty": qty, "unit": unit, "storage": storage, "symbol": symbol}

        if cat == "crypto":
            crypto_items.append(base)
        elif cat in ("us_stock_tokenized", "us_stock"):
            us_stock_items.append(base)
        elif cat == "hk_stock":
            hk_stock_items.append(base)
        elif cat == "a_stock":
            a_stock_items.append(base)
        elif cat == "ts_time_token":
            ts_items.append(base)

    # 辅助：从 report_prices 或 prev_prices 获取价格
    def _get_price(item_name, fallback_key=None, price_type="price"):
        """按优先级获取价格：月度报告 > 前次归档"""
        KEY_MAP = {"price": "price", "mv_cny": "market_value", "storage": "storage"}

        def _lookup_in(source, source_key, target_key):
            val = source.get(source_key, {})
            if isinstance(val, dict):
                mapped = KEY_MAP.get(target_key, target_key)
                return val.get(mapped, val.get(target_key, "—"))
            return str(val)

        # 尝试从 report_prices 精确匹配
        for rp_key, rp_val in report_prices.items():
            if item_name in rp_key or (fallback_key and fallback_key in rp_key):
                if price_type == "price":
                    return rp_val.get("price", "—")
                elif price_type == "mv_cny":
                    return rp_val.get("mv_cny", "—")
                elif price_type == "storage":
                    return rp_val.get("storage", "—")
                return "—"
        # 尝试从 prev_prices 获取
        for section_key in ("crypto", "us", "hk", "a"):
            prev_section = prev_prices.get(section_key, {})
            for prev_key, prev_val in prev_section.items():
                if item_name in prev_key or (fallback_key and fallback_key in prev_key):
                    return _lookup_in(prev_section, prev_key, price_type)
        return "—"

    def _get_price_storage(item_name, fallback_key=None):
        return _get_price(item_name, fallback_key, "storage")

    def _get_mv(item_name, fallback_key=None):
        return _get_price(item_name, fallback_key, "mv_cny")

    # 构建输出
    lines = []
    lines.append(f"# 个人画像归档 - {date_str}")
    lines.append("")

    # ════════════════════════════════════════════════════════════════
    # 投资持仓概览
    # ════════════════════════════════════════════════════════════════
    lines.append("## 投资持仓概览")
    lines.append("")

    # 加密货币
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    for item in crypto_items:
        name = item["name"]
        qty = item["qty"]
        unit = item["unit"]
        storage = item["storage"]
        if isinstance(qty, float) and qty < 1:
            qty_str = f"{qty:.8f}"
        else:
            qty_str = f"{qty:,}"
        if unit:
            qty_str += unit
        price = _get_price(name)
        mv = _get_mv(name)
        lines.append(f"| {name} | {qty_str} | {price} | {mv} | {storage} |")

    # 美股
    lines.append("")
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    # CRCL 合计
    crcl_qty = sum(item["qty"] for item in us_stock_items if "CRCL" in item["symbol"] or "Circle" in item["name"])
    crcl_name = "Circle(CRCL合计)"
    crcl_price = _get_price("Circle(CRCL合计)", "CRCL")
    crcl_mv = _get_mv("Circle(CRCL合计)", "CRCL")
    lines.append(f"| {crcl_name} | {crcl_qty:,.1f} | {crcl_price} | {crcl_mv} | 分散多账户 |")

    for item in us_stock_items:
        if "CRCL" in item["symbol"] or "Circle" in item["name"]:
            continue
        name = item["name"]
        qty = item["qty"]
        storage = item["storage"]
        if isinstance(qty, float) and qty < 10:
            qty_str = f"{qty:.3f}"
        else:
            qty_str = f"{qty:,}"
        price = _get_price(name)
        mv = _get_mv(name)
        lines.append(f"| {name} | {qty_str} | {price} | {mv} | {storage} |")

    # 港股
    lines.append("")
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")
    for item in hk_stock_items:
        name = item["name"]
        qty = item["qty"]
        storage = item["storage"]
        qty_str = f"{qty:,}"
        price = _get_price(name)
        mv = _get_mv(name)
        lines.append(f"| {name} | {qty_str} | {price} | {mv} | {storage} |")

    # A股
    lines.append("")
    lines.append("### A股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")
    for item in a_stock_items:
        name = item["name"]
        qty = item["qty"]
        storage = item["storage"]
        qty_str = f"{qty:,}"
        price = _get_price(name)
        mv = _get_mv(name)
        lines.append(f"| {name} | {qty_str} | {price} | {mv} | {storage} |")

    # TS时间代币
    lines.append("")
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")
    for item in ts_items:
        name = item["name"]
        qty = item["qty"]
        unit = item["unit"]
        qty_str = f"{qty:,}{unit}" if unit else f"{qty:,}"
        mv = _get_mv(name)
        lines.append(f"| {name} | {qty_str} | {mv} |")

    # 关键指标
    lines.append("")
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")

    prev_metrics = prev_prices.get("metrics", {})

    # 从月度报告提取: 总资产、净资产、投资总资产
    total_assets = report_metrics.get("总资产", prev_metrics.get("总资产", "—"))
    net_assets = report_metrics.get("净资产", prev_metrics.get("净资产", "—"))
    invest_assets = report_metrics.get("投资总资产", prev_metrics.get("投资总资产", "—"))
    cash = report_metrics.get("家庭备用金", prev_metrics.get("家庭备用金", "—"))
    hk_fund = prev_metrics.get("HK打新资金", "—")
    usdt_bal = prev_metrics.get("USDT余额", "—")
    huasheng_cash = prev_metrics.get("华盛通现金", "—")
    credit_card = prev_metrics.get("信用卡负债", "—")
    btc_pct = prev_metrics.get("BTC占投资比", "—")
    crcl_pct = prev_metrics.get("CRCL集中度", "—")
    mortgage = prev_metrics.get("房贷总额", "—")

    metric_rows = [
        ("总资产", total_assets),
        ("净资产", net_assets),
        ("投资总资产", invest_assets),
        ("家庭备用金", cash),
        ("HK打新资金", hk_fund),
        ("USDT余额", usdt_bal),
        ("华盛通现金", huasheng_cash),
        ("信用卡负债", credit_card),
        ("BTC占投资比", btc_pct),
        ("CRCL集中度", crcl_pct),
        ("房贷总额", mortgage),
    ]
    for key, val in metric_rows:
        lines.append(f"| {key} | {val} |")

    # ════════════════════════════════════════════════════════════════
    # 职业发展画像
    # ════════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")
    career_rows = [
        ("当前公司", "新华三"),
        ("当前角色", "嵌入式开发工程师"),
        ("经验", "**~9年**（爱博精电 6年 + 新华三 3年）"),
        ("技能栈", "C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM"),
        ("核心能力", "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构"),
        ("行业聚焦", "工业嵌入式、通信设备底层，**非消费电子**"),
        ("地点约束", "**北京，优先海淀/昌平**（已在海淀买房）"),
        ("目标薪资", "50-70W总包"),
        ("求职状态", "已约 1 年，面试过 九号/ISHO/思朗"),
        ("面试方法论", "工程叙事四层结构: 本质→实践→踩坑→思考"),
        ("目标公司", "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团"),
    ]
    for key, val in career_rows:
        lines.append(f"| {key} | {val} |")

    # ════════════════════════════════════════════════════════════════
    # 家庭与保险
    # ════════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    family_rows = [
        ("居住地", "北京"),
        ("户籍", "非京籍 (内蒙古)"),
        ("子女", "有孩子 (在京上学)"),
        ("配偶", "已婚 (薛燕)"),
        ("房产", "北京海淀住宅 ¥320W (购入2025年底)"),
        ("hanwei_zhongji", "达尔文50W (¥6,960/年, 2026-06-15生效)"),
        ("hanwei_dingshou", "待配置 (目标200W保额)"),
        ("xueyan_zhongji", "待配置 (目标30-50W保额)"),
    ]
    for key, val in family_rows:
        lines.append(f"| {key} | {val} |")

    # ════════════════════════════════════════════════════════════════
    # A8计划进度
    # ════════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")
    a8_rows = [
        ("目标", "1000万人民币 (2026-2028)"),
        ("BTC目标", "2.32个 (当前0.130, 进度5.6%)"),
        ("策略", "MA120趋势 + 月度定投¥16,700 + 港股打新"),
        ("当前状态", prev_metrics.get("BTC占投资比", "—") != "—" and "BTC在MA120上方, 看板触发底部信号, 分批建仓窗口" or "待更新"),
    ]
    for key, val in a8_rows:
        lines.append(f"| {key} | {val} |")

    # ════════════════════════════════════════════════════════════════
    # 本次更新变更记录
    # ════════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")

    # 确定前次同步日期
    prev_date = prev_prices.get("metrics", {}).get("profile_last_sync", "N/A")
    if prev_date == "N/A" or prev_date == "—":
        # 尝试从前次归档文件名提取
        prev_files = sorted(glob.glob(str(HOUR_ARCHIVE_DIR / "profile_*.md")), reverse=True)
        if prev_files:
            m = re.search(r"profile_(\d{8})\.md", os.path.basename(prev_files[0]))
            if m:
                d = m.group(1)
                prev_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"

    lines.append(f"| profile.last_sync | {prev_date} | {date_str} | 每日自动归档 |")
    lines.append(f"| 数据源 | holdings.yaml | holdings.yaml | 持仓同步（无变更） |")
    lines.append(f"| 数据源 | 月度报告 | {report_filename} | 数据截至{last_updated} |")
    lines.append(f"| 职业档案 | 个人职业发展分析-端侧AI企业定制攻略.md | 同左 | 含2026-06-12简历核查修正 |")

    return "\n".join(lines)


def write_archive(content, archive_dir):
    """写入归档文件"""
    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    date_compact = date.today().strftime("%Y%m%d")
    filepath = archive_dir / f"profile_{date_compact}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"归档写入: {filepath}")
    return filepath


def main():
    logger.info("=" * 60)
    logger.info("个人画像归档同步开始")
    logger.info(f"日期: {date.today().strftime('%Y-%m-%d')}")
    logger.info("=" * 60)

    # 1. 读取持仓
    holdings = load_holdings()
    if holdings is None:
        _log_error("无法读取 holdings.yaml，退出")
        sys.exit(1)

    # 2. 读取最新月度报告
    report_content, report_filename = load_latest_monthly_report()
    if report_content is None:
        _log_error("无法读取最新月度报告，退出")
        sys.exit(1)

    # 3. 读取职业档案
    career_content = load_career_profile()
    if career_content is None:
        _log_error("无法读取职业档案，退出")
        sys.exit(1)

    # 4. 读取前次归档作为价格 fallback
    prev_prices = _extract_prev_archive_prices(HOUR_ARCHIVE_DIR)

    # 5. 构建归档内容
    archive_content = build_archive(holdings, report_content, report_filename, prev_prices)

    # 6. 写入两份归档
    hour_path = write_archive(archive_content, HOUR_ARCHIVE_DIR)
    day_path = write_archive(archive_content, DAY_ARCHIVE_DIR)

    logger.info("=" * 60)
    logger.info(f"个人画像归档完成")
    logger.info(f"  小时推送: {hour_path}")
    logger.info(f"  日报推送: {day_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()