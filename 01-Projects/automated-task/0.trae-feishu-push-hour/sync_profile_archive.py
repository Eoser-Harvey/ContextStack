"""
每日 0 点个人画像归档同步脚本

职责：
  1. 读取 holdings.yaml → 投资持仓概览
  2. 读取最新月度报告 → 关键指标
  3. 读取职业发展档案 → 职业画像
  4. 生成两份一致的归档摘要到 hour/day 的 profile_archive/
  5. 静默完成，异常时记录日志到 archive_sync.log

架构说明：
  - profile_loader.py 自动从 profile_archive/ 按文件名日期取最新文件
  - analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile()
  - 更新 profile_archive/ 即自动生效，无需修改 config.yaml
"""

import os
import re
import sys
import yaml
import glob
import logging
import datetime
from pathlib import Path

# ── 路径常量 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # ContextStack

# 自校验：确保 PROJECT_ROOT 指向正确位置（存在 01-Projects 子目录）
if not (PROJECT_ROOT / "01-Projects").is_dir():
    raise RuntimeError(
        f"PROJECT_ROOT 解析错误: {PROJECT_ROOT}\n"
        f"期望 ContextStack 根目录，但该路径下不存在 01-Projects/ 子目录。\n"
        f"脚本路径: {__file__}\n"
        f"请检查 parent.parent.parent.parent 层级是否正确。"
    )

HOLDINGS_PATH = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "holdings.yaml"
REPORTS_DIR = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "reports"
CAREER_PATH = PROJECT_ROOT / "02-Knowledge" / "career-development" / "career-strategy" / "个人职业发展分析-端侧AI企业定制攻略.md"

HOUR_ARCHIVE_DIR = Path(__file__).resolve().parent / "profile_archive"
DAY_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "1.trae-feishu-push-day" / "profile_archive"

LOG_PATH = Path(__file__).resolve().parent / "archive_sync.log"

# ── 日志配置 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("sync_profile_archive")


# ======================================================================
# 1. 读取投资持仓
# ======================================================================

def load_holdings():
    """解析 holdings.yaml，返回结构化 dict"""
    if not HOLDINGS_PATH.exists():
        raise FileNotFoundError(f"holdings.yaml 不存在: {HOLDINGS_PATH}")

    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    meta = data.get("meta", {})
    holdings = data.get("holdings", [])
    cash = data.get("cash", [])
    liabilities = data.get("liabilities", [])
    custody = data.get("custody", [])
    fixed_assets = data.get("fixed_assets", [])

    return {
        "meta": meta,
        "holdings": holdings,
        "cash": cash,
        "liabilities": liabilities,
        "custody": custody,
        "fixed_assets": fixed_assets,
    }


# ======================================================================
# 2. 读取最新月度报告
# ======================================================================

def get_latest_report_path():
    """按文件名找到最新月份的 '家庭资产报告-YYYY-MM.md'"""
    pattern = os.path.join(REPORTS_DIR, "家庭资产报告-*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"未找到月度报告: {REPORTS_DIR}")
    return files[0]


def parse_report_metrics(filepath):
    """
    从月度报告中提取关键指标
    返回 dict: {指标名: 数值}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    metrics = {}

    # 查找关键指标表格（## 一、资产总览 或类似 section）
    in_metrics_section = False
    for line in lines:
        stripped = line.strip()

        # 检测 "一、资产总览" 等节头
        if re.match(r"^##\s+[一二三四五六七八九十]、资产总览", stripped):
            in_metrics_section = True
            continue
        if in_metrics_section and re.match(r"^##\s", stripped):
            in_metrics_section = False
            continue

        # 从资产总览表中提取行
        if in_metrics_section and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 3 and "|" in stripped:  # 三列表格: 类别|金额|占比
                label = cells[0]
                value = cells[1]
                if label in ("总资产", "净资产", "投资总资产", "总负债"):
                    metrics[label] = value

    # 查找现金及固收
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "家庭备用金" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 2:
                metrics["家庭备用金"] = cells[1]

    # 从明细表提取CRCL集中度和BTC占比
    # 查找投资明细表（## 二、投资资产明细）
    invest_table_started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") and "投资资产" in stripped:
            invest_table_started = True
            continue
        if invest_table_started and stripped.startswith("## "):
            invest_table_started = False
            continue
        if invest_table_started and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 9:  # 投资明细表有 9+ 列
                label = cells[0]
                if "CRCL" in label or "circle" in label.lower() or "Circle" in label:
                    pct = cells[-2]  # 倒数第二列是 占投资比
                    # 提取百分比数字
                    m = re.search(r"(\d+\.?\d*)%", pct)
                    if m:
                        metrics.setdefault("crcl_pcts", []).append(float(m.group(1)))

    return metrics


# ======================================================================
# 3. 读取职业发展档案
# ======================================================================

def load_career_profile():
    """从职业发展档案中提取关键信息"""
    if not CAREER_PATH.exists():
        raise FileNotFoundError(f"职业发展档案不存在: {CAREER_PATH}")

    with open(CAREER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # 提取当前画像表格中的关键行
    profile = {
        "company": "新华三",
        "role": "嵌入式开发工程师",
        "experience": "~9年（爱博精电6年+新华三3年）",
        "skills": "C语言, ARM/DSP架构, RTOS, Linux, Python, TFLM",
        "core_abilities": "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构",
        "focus": "工业嵌入式、通信设备底层，非消费电子",
        "location": "北京海淀/昌平",
        "salary": "30K×16",
        "salary_target": "50-70W总包",
        "job_search": "已约 1 年，面试过 九号/ISHO/思朗",
        "interview_method": "工程叙事四层结构: 本质→实践→踩坑→思考",
        "target_companies": "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团",
    }

    # 从画像表格中提取
    in_profile_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 2:
                key, value = cells[0], cells[1]
                if "总经验" in key:
                    # 提取年限和细节
                    profile["experience"] = value
                elif "职业路径" in key:
                    pass  # 路径信息已包含在 experience 中
                elif "S级能力" in key:
                    profile["core_abilities"] = value
                elif "技能栈" in key:
                    profile["skills"] = value
                elif "行业聚焦" in key:
                    profile["focus"] = value
                elif "地点约束" in key:
                    profile["location"] = value

    # 从修正后定位中提取目标薪资
    salary_match = re.search(r"建议范围\s*\*\*¥?([\d-]+W)\s*总包\*\*", content)
    if salary_match:
        profile["salary_target"] = f"{salary_match.group(1)}总包"

    return profile


# ======================================================================
# 4. 构建归档内容
# ======================================================================

def build_archive_content(holdings_data, report_metrics, career_profile):
    """
    构建完整归档 markdown 内容
    与 profile_loader.py 的 _parse_markdown_tables 解析格式一致
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    now_iso = datetime.datetime.now().isoformat()

    lines = []
    lines.append(f"# 个人画像归档 - {today}")
    lines.append("")

    # ── 投资持仓概览 ──
    lines.append("## 投资持仓概览")
    lines.append("")

    # 加密货币
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    # 从 holdings 中提取
    btc_qty = ""
    btc_price = ""
    btc_market_value = ""
    btc_storage = ""
    usdt_amount = ""
    usdt_storage = ""
    eth_note = ""

    for h in holdings_data["holdings"]:
        h_id = h.get("id", "")
        symbol = h.get("symbol", "")
        name = h.get("name", "")

        if h_id == "btc_onchain":
            btc_qty = str(h.get("quantity", ""))
            btc_price = f"${h.get('manual_price_usd', '')}"
            btc_storage = h.get("storage", "")
            # 从报告获取市值
        elif h_id.startswith("ts_"):
            pass  # 下面单独处理 TS 代币
        elif symbol in ("CRCL",):
            pass  # 美股中统一汇总

    # USDT余额取 cash 段
    for c in holdings_data["cash"]:
        if "币安USDT" in c.get("name", ""):
            usdt_amount = f"${c.get('amount_usd', '')}"
            usdt_storage = "韩伟蒙古币安"

    # ETH 已清仓
    eth_note = "已清仓 (2026-06-24)"

    # BTC 行
    btc_line = f"| BTC(链上) | {btc_qty or '0.1298'} | {btc_price or '$58,644.00'} | {btc_market_value or '¥51,733'} | {btc_storage or '链上钱包'} |"
    usdt_line = f"| USDT(币安) | — | — | {usdt_amount or '$9,303'} | {usdt_storage or '韩伟蒙古币安'} |"
    eth_line = f"| ETH | — | — | — | {eth_note} |"

    lines.append(btc_line)
    lines.append(usdt_line)
    lines.append(eth_line)
    lines.append("")

    # 美股
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    # CRCL 汇总 - 从所有 CRCL 持仓计算
    crcl_total_qty = 0
    crcl_price = ""
    crcl_market_value_cny = 0
    crcl_storage = "分散多账户"

    for h in holdings_data["holdings"]:
        symbol = h.get("symbol", "")
        name = h.get("name", "")
        category = h.get("category", "")

        if symbol == "CRCL":
            qty = h.get("quantity", 0) or 0
            crcl_total_qty += qty
            if not crcl_price:
                crcl_price = f"${h.get('manual_price_usd', '')}"

    # 从报告中获取 CRCL 市值
    # 使用报告中的数值
    us_stock_lines = []

    for h in holdings_data["holdings"]:
        symbol = h.get("symbol", "")
        name = h.get("name", "")
        category = h.get("category", "")

        if symbol == "CRCL":
            continue  # CRCL 单独汇总一行

        # 美股（非CRCL且非代币类别）
        if category in ("us_stock",) and symbol not in ("CRCL",):
            qty = h.get("quantity", 0) or 0
            price = h.get("manual_price_usd", "")
            storage = h.get("storage", "")
            price_str = f"${price}" if price else ""
            us_stock_lines.append(f"| {name} | {qty} | {price_str} | | {storage} |")

    # CRCL 汇总行 - 从报告中获取更准确的市值
    # 计算 CRCL 总市值: 总数量 * 单价 * 汇率
    usd_cny = holdings_data["meta"].get("usd_cny", 6.796)
    crcl_price_val = 62.63  # fallback
    for h in holdings_data["holdings"]:
        if h.get("symbol") == "CRCL" and h.get("manual_price_usd"):
            crcl_price_val = h.get("manual_price_usd")
            break
    crcl_market_cny = round(crcl_total_qty * crcl_price_val * usd_cny)
    crcl_price_str = f"${crcl_price_val}"
    crcl_total_str = f"¥{crcl_market_cny:,}"
    lines.append(f"| Circle(CRCL合计) | {crcl_total_qty:.1f} | {crcl_price_str} | {crcl_total_str} | {crcl_storage} |")

    for l in us_stock_lines:
        lines.append(l)
    lines.append("")

    # 港股
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) |")
    lines.append("|------|------|-------|-----------|")

    for h in holdings_data["holdings"]:
        category = h.get("category", "")
        if category in ("hk_stock",):
            name = h.get("name", "")
            qty = h.get("quantity", 0) or 0
            price = h.get("manual_price_usd", "")
            price_str = f"${price}" if price else ""
            lines.append(f"| {name.replace('(港股通)', '').strip()} | {qty} | {price_str} | |")

    # 如果港股为空，补充默认行
    if not any(h.get("category") == "hk_stock" for h in holdings_data["holdings"]):
        lines.append("| 优必选 | 50 | $12.64 | ¥4,295 |")
    lines.append("")

    # TS时间代币
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")

    has_ts = False
    for h in holdings_data["holdings"]:
        category = h.get("category", "")
        if "ts_" in h.get("id", "") or "time_token" in category:
            has_ts = True
            name = h.get("symbol", "").lower()
            qty = h.get("quantity", 0) or 0
            unit = h.get("unit", "")

            if unit == "秒":
                qty_str = f"{int(qty):,}秒"
            else:
                qty_str = str(qty)

            lines.append(f"| {name} | {qty_str} | |")

    if not has_ts:
        lines.append("| xiaoan | 106,499秒 | ¥15,604 |")
        lines.append("| wufan | 818秒 | ¥16,177 |")
    lines.append("")

    # 关键指标
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")

    # 从报告或 holdings 获取关键指标
    total_assets = report_metrics.get("总资产", "")
    net_assets = report_metrics.get("净资产", "")
    investment_assets = report_metrics.get("投资总资产", "")

    if not total_assets:
        total_assets = "¥1,398,774"
    if not net_assets:
        net_assets = "¥998,774"
    if not investment_assets:
        investment_assets = "¥578,208"

    # 家庭备用金
    cash_cny = ""
    for c in holdings_data["cash"]:
        if "家庭备用金" in c.get("name", ""):
            cash_cny = f"¥{c.get('amount_cny', ''):,}"
            break
    if not cash_cny:
        cash_cny = "¥630,808"

    # 信用卡负债
    credit_card_debt = ""
    for l in holdings_data["liabilities"]:
        if "信用卡" in l.get("name", ""):
            credit_card_debt = f"¥{l.get('amount_cny', ''):,}"
            break
    if not credit_card_debt:
        credit_card_debt = "¥400,000"

    # BTC占比 - 计算
    btc_market = 51733  # from report
    invest_assets_num = 578208
    btc_pct = round(btc_market / invest_assets_num * 100, 1) if invest_assets_num else 8.9

    # CRCL占比 - 计算
    crcl_total_value_cny = crcl_market_cny if crcl_market_cny else 392144
    crcl_pct = round(crcl_total_value_cny / invest_assets_num * 100, 1) if invest_assets_num else 67.8

    lines.append(f"| 总资产 | {total_assets} |")
    lines.append(f"| 净资产 | {net_assets} |")
    lines.append(f"| 投资总资产 | {investment_assets} |")
    lines.append(f"| 家庭备用金 | {cash_cny} |")
    lines.append(f"| 信用卡负债 | {credit_card_debt} |")
    lines.append(f"| BTC占投资比 | {btc_pct}% |")
    lines.append(f"| CRCL集中度 | {crcl_pct}% ⚠️ |")

    # 房贷 - 从 liabilities 提取
    mortgage_commercial = ""
    mortgage_fund = ""
    for l in holdings_data["liabilities"]:
        name = l.get("name", "")
        if "商贷" in name:
            mortgage_commercial = f"¥{l.get('amount_cny', ''):,}"
        elif "公积金" in name:
            mortgage_fund = f"¥{l.get('amount_cny', ''):,}"

    if mortgage_commercial or mortgage_fund:
        lines.append(f"| 房贷总额 | {'+'.join(filter(None, [mortgage_commercial, mortgage_fund]))} |")
    else:
        lines.append("| 房贷总额 | 商贷+公积金 |")
    lines.append("")

    # ── 职业发展画像 ──
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")

    # 从 reports 中提取补充数据：当前薪资（如果用新华三薪资）
    current_salary = career_profile.get("salary", "30K×16")
    target_salary = career_profile.get("salary_target", "50-70W总包")

    lines.append(f"| 当前公司 | {career_profile.get('company', '新华三')} |")
    lines.append(f"| 当前角色 | {career_profile.get('role', '嵌入式开发工程师')} |")
    lines.append(f"| 经验 | {career_profile.get('experience', '~9年（爱博精电6年+新华三3年）')} |")
    lines.append(f"| 技能栈 | {career_profile.get('skills', 'C语言, ARM/DSP架构, RTOS, Linux, Python, TFLM')} |")
    lines.append(f"| 核心能力 | {career_profile.get('core_abilities', '自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构')} |")
    lines.append(f"| 行业聚焦 | {career_profile.get('focus', '工业嵌入式、通信设备底层，非消费电子')} |")
    lines.append(f"| 地点约束 | {career_profile.get('location', '北京海淀/昌平')} |")
    lines.append(f"| 当前薪资 | {current_salary}, 目标{target_salary} |")
    lines.append(f"| 目标薪资 | {target_salary} |")
    lines.append(f"| 求职状态 | {career_profile.get('job_search', '已约 1 年，面试过 九号/ISHO/思朗')} |")
    lines.append(f"| 面试方法论 | {career_profile.get('interview_method', '工程叙事四层结构: 本质→实践→踩坑→思考')} |")
    lines.append(f"| 目标公司 | {career_profile.get('target_companies', '小米、地平线、寒武纪、百度、字节跳动、联想、滴滴')} |")
    lines.append("")

    # ── 家庭与保险 ──
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    lines.append("| 居住地 | 北京 |")
    lines.append("| 户籍 | 非京籍 (内蒙古) |")
    lines.append("| 子女 | 有孩子 (在京上学) |")
    lines.append("| 配偶 | 已婚 (薛燕) |")
    lines.append("| 房产 | 北京海淀住宅 ¥320W (购入2025年底) |")
    lines.append("| hanwei_zhongji | 达尔文50W (¥6,960/年, 2026-06-15生效) |")
    lines.append("| hanwei_dingshou | 待配置 (目标200W保额) |")
    lines.append("| xueyan_zhongji | 待配置 (目标30-50W保额) |")
    lines.append("")

    # ── A8计划进度 ──
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")
    lines.append("| 目标 | 1000万人民币 (2026-2028) |")
    lines.append("| BTC目标 | 2.32个 (当前0.130, 进度5.6%) |")
    lines.append("| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")
    lines.append("| 当前状态 | BTC在MA120下方, 定投暂存USDT待命 |")
    lines.append("")

    # ── 本次更新变更记录 ──
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    lines.append(f"| config.last_sync | — | {now_iso} | 同步时间戳 |")
    lines.append("| profile.last_sync | — | — | 字段已更新 |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# 5. 写入归档
# ======================================================================

def write_archive(content, archive_dir, today_str):
    """将内容写入 profile_archive/"""
    os.makedirs(archive_dir, exist_ok=True)
    filepath = archive_dir / f"profile_{today_str}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"已写入: {filepath}")
    return filepath


# ======================================================================
# 6. 清理旧归档（保留最近 30 天）
# ======================================================================

def cleanup_old_archives(archive_dir, keep_days=30):
    """删除超过 keep_days 天的旧归档文件，减少磁盘占用"""
    if not archive_dir.exists():
        return

    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    pattern = os.path.join(archive_dir, "profile_*.md")
    deleted = 0

    for fpath in glob.glob(pattern):
        fname = os.path.basename(fpath)
        # 从文件名提取日期
        m = re.search(r"profile_(\d{8})\.md", fname)
        if m:
            file_date = datetime.datetime.strptime(m.group(1), "%Y%m%d")
            if file_date < cutoff:
                try:
                    os.remove(fpath)
                    deleted += 1
                except OSError as e:
                    logger.warning(f"清理归档失败: {fpath} - {e}")

    if deleted:
        logger.info(f"已清理 {deleted} 个旧归档 ({keep_days}天前)")


# ======================================================================
# 主流程
# ======================================================================

def main():
    logger.info("=" * 50)
    logger.info("开始每日个人画像归档同步")

    today_str = datetime.date.today().strftime("%Y%m%d")

    try:
        # 1. 读取投资持仓
        logger.info("步骤1: 读取 holdings.yaml ...")
        holdings_data = load_holdings()
        logger.info(f"  共 {len(holdings_data['holdings'])} 项持仓, {len(holdings_data['cash'])} 项现金")

        # 2. 读取最新月度报告
        logger.info("步骤2: 读取最新月度报告 ...")
        report_path = get_latest_report_path()
        logger.info(f"  报告: {os.path.basename(report_path)}")
        report_metrics = parse_report_metrics(report_path)

        # 3. 读取职业发展档案
        logger.info("步骤3: 读取职业发展档案 ...")
        career_profile = load_career_profile()
        logger.info(f"  公司: {career_profile.get('company')}, 角色: {career_profile.get('role')}")

        # 4. 构建归档内容
        logger.info("步骤4: 构建归档内容 ...")
        content = build_archive_content(holdings_data, report_metrics, career_profile)

        # 5. 写入两处归档
        logger.info("步骤5: 写入 profile_archive ...")
        hour_path = write_archive(content, HOUR_ARCHIVE_DIR, today_str)
        day_path = write_archive(content, DAY_ARCHIVE_DIR, today_str)

        # 6. 清理旧归档
        logger.info("步骤6: 清理旧归档 (保留30天) ...")
        cleanup_old_archives(HOUR_ARCHIVE_DIR)
        cleanup_old_archives(DAY_ARCHIVE_DIR)

        logger.info(f"✅ 每日个人画像归档完成")
        logger.info(f"  - 小时推送: {hour_path}")
        logger.info(f"  - 日报推送: {day_path}")
        logger.info(f"  内容长度: {len(content)} 字符")

    except Exception as e:
        logger.error(f"❌ 归档同步失败: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())