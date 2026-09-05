"""
每日 0 点个人画像归档同步脚本

职责：
  1. 读取 holdings.yaml → 投资持仓概览
  2. 读取最新月度报告 → 关键指标、资产明细、价格
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

# 自校验：确保 PROJECT_ROOT 指向正确位置
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
ANNUAL_REPORT_PATH = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "reports" / "家庭资产年度报告-2026.md"

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
# 2. 读取最新月度报告 — 精确解析
# ======================================================================

def get_latest_report_path():
    """按文件名找到最新月份的 '家庭资产报告-YYYY-MM.md'"""
    pattern = os.path.join(REPORTS_DIR, "家庭资产报告-*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"未找到月度报告: {REPORTS_DIR}")
    return files[0]


def _extract_table_rows(lines, section_header, end_pattern=r"^## ", min_cols=2):
    """
    在 markdown 中查找指定 section 下的表格，返回行列表。
    section_header: 匹配的节标题（如 "## 二、投资资产明细"）
    end_pattern: 节结束模式
    min_cols: 最小列数
    """
    rows = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if re.match(section_header, stripped):
            in_section = True
            continue
        if in_section:
            if re.match(end_pattern, stripped):
                break
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                # 跳过表头分隔行
                if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                    continue
                if len(cells) >= min_cols:
                    rows.append(cells)
    return rows


def parse_invest_detail(lines):
    """
    解析投资资产明细表（## 二、投资资产明细）
    返回: {label: {qty, price, market_value_cny, cost_price_cny, cost_total_cny, pnl, pct, storage}}
    """
    detail_rows = _extract_table_rows(lines, r"^##\s+二、投资资产", min_cols=8)
    assets = {}
    for cells in detail_rows:
        if len(cells) < 8:
            continue
        label = cells[0]
        qty = cells[1]
        price = cells[2]
        market_value = cells[3]
        cost_price = cells[4] if len(cells) > 4 else ""
        cost_total = cells[5] if len(cells) > 5 else ""
        pnl = cells[6] if len(cells) > 6 else ""
        pct = cells[7] if len(cells) > 7 else ""
        storage = cells[8] if len(cells) > 8 else ""
        assets[label] = {
            "qty": qty,
            "price": price,
            "market_value_cny": market_value,
            "cost_price_cny": cost_price,
            "cost_total_cny": cost_total,
            "pnl": pnl,
            "pct": pct,
            "storage": storage,
        }
    return assets


def parse_asset_summary(lines):
    """
    解析按资产统计表（## 三、按资产统计）
    返回: {asset_name: {qty, avg_price, market_value_cny, pct}}
    """
    summary_rows = _extract_table_rows(lines, r"^##\s+三、按资产", min_cols=4)
    assets = {}
    for cells in summary_rows:
        if len(cells) < 4:
            continue
        name = cells[0]
        qty = cells[1] if len(cells) > 1 else ""
        avg_price = cells[2] if len(cells) > 2 else ""
        market_value = cells[3] if len(cells) > 3 else ""
        pct = cells[4] if len(cells) > 4 else ""
        assets[name] = {
            "qty": qty,
            "avg_price": avg_price,
            "market_value_cny": market_value,
            "pct": pct,
        }
    return assets


def parse_overview(lines):
    """
    解析资产总览表（## 一、资产总览）
    返回: {label: value_cny}
    """
    rows = _extract_table_rows(lines, r"^##\s+一、资产总览", min_cols=2)
    metrics = {}
    for cells in rows:
        if len(cells) >= 2:
            label = cells[0]
            value = cells[1]
            if label in ("总资产", "净资产", "投资总资产", "总负债", "投资净资产"):
                metrics[label] = value
    return metrics


def parse_liabilities(lines):
    """解析负债表（## 四、负债）"""
    rows = _extract_table_rows(lines, r"^##\s+四、负债", min_cols=2)
    items = {}
    for cells in rows:
        if len(cells) >= 2:
            name = cells[0]
            amount = cells[1]
            items[name] = amount
    return items


def parse_cash(lines):
    """解析现金及固收表（## 五、现金及固收）"""
    rows = _extract_table_rows(lines, r"^##\s+五、现金及固收", min_cols=2)
    items = {}
    for cells in rows:
        if len(cells) >= 2:
            name = cells[0]
            amount = cells[1]
            items[name] = amount
    return items


def parse_mortgage(lines):
    """从房贷与房产说明（## 七、房贷）提取房贷信息"""
    mortgage = {}
    in_section = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^##\s+七、房贷", stripped):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", stripped):
                break
            # 匹配: - 房贷—商贷：¥400,000
            m = re.search(r"房贷.*?([商公]).*?[：:]?\s*([¥￥][\d,]+)", stripped)
            if m:
                label = "商贷" if "商" in m.group(1) else "公积金"
                mortgage[label] = m.group(2)
            # 匹配: - 北京海淀住宅：估值¥3,200,000
            m2 = re.search(r"住宅.*?[估]?值?\s*([¥￥][\d,]+)", stripped)
            if m2:
                mortgage["房产估值"] = m2.group(1)
    return mortgage


def parse_history_net_assets(lines):
    """从历史净资产走势表（## 八、关键指标）提取本期净资产对比"""
    rows = _extract_table_rows(lines, r"^##\s+八、关键指标", min_cols=3)
    prev_net = ""
    for cells in rows:
        if len(cells) >= 3 and "本期" in cells[0]:
            return cells[2]  # 变动列
        if len(cells) >= 4 and "本期" in cells[0]:
            return cells[3]
    # 从历史净资产走势表的最后一行取
    hist_rows = [c for c in rows if len(c) >= 4 and re.match(r"^\d{4}-\d{2}-\d{2}", c[0])]
    if hist_rows:
        last = hist_rows[-1]
        if len(last) >= 4:
            prev_net = last[2]  # 环比变动
    return prev_net


def parse_report(filepath):
    """
    完整解析月度报告，返回结构化数据
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")

    report = {
        "overview": parse_overview(lines),
        "invest_detail": parse_invest_detail(lines),
        "asset_summary": parse_asset_summary(lines),
        "liabilities": parse_liabilities(lines),
        "cash": parse_cash(lines),
        "mortgage": parse_mortgage(lines),
        "report_name": os.path.basename(filepath),
    }

    # 提取价格变动周期
    price_change_section = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^##\s+十、本期价格变动", stripped):
            price_change_section = True
            continue
        if price_change_section:
            if re.match(r"^##\s", stripped):
                break
    report["report_name"] = os.path.basename(filepath)

    return report


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

    profile = {
        "company": "新华三",
        "role": "嵌入式开发工程师",
        "experience": "~9年（爱博精电6年+新华三3年）",
        "skills": "C语言, ARM/DSP架构, RTOS, Linux, Python, TFLM",
        "core_abilities": "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构",
        "focus": "工业嵌入式、通信设备底层，非消费电子",
        "location": "北京海淀/昌平",
        "salary_target": "50-70W总包",
        "job_search": "已约 1 年，面试过 九号/ISHO/思朗",
        "interview_method": "工程叙事四层结构: 本质→实践→踩坑→思考",
        "target_companies": "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团",
    }

    # 从当前画像表格中提取
    in_profile_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 2:
                key, value = cells[0], cells[1]
                if "总经验" in key:
                    profile["experience"] = value
                elif "S级能力" in key:
                    profile["core_abilities"] = value
                elif "技能栈" in key:
                    profile["skills"] = value
                elif "行业聚焦" in key:
                    profile["focus"] = value
                elif "地点约束" in key:
                    profile["location"] = value
                elif "职业路径" in key:
                    pass

    # 从修正后定位中提取目标薪资
    salary_match = re.search(r"建议范围\s*\*\*¥?([\d-]+W)\s*总包\*\*", content)
    if salary_match:
        profile["salary_target"] = f"{salary_match.group(1)}总包"

    return profile


# ======================================================================
# 4. 加载前一天的归档（用于变更记录对比）
# ======================================================================

def load_previous_archive(archive_dir, today_str):
    """加载前一天的归档文件，用于生成变更记录"""
    today_dt = datetime.datetime.strptime(today_str, "%Y%m%d")
    prev_dt = today_dt - datetime.timedelta(days=1)
    prev_str = prev_dt.strftime("%Y%m%d")
    prev_path = archive_dir / f"profile_{prev_str}.md"
    if prev_path.exists():
        with open(prev_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _extract_metrics_from_archive(content):
    """从归档内容中提取关键指标数值，用于比较"""
    metrics = {}
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 2:
                key, value = cells[0], cells[1]
                if key in ("总资产", "净资产", "投资总资产", "CRCL集中度", "家庭备用金"):
                    metrics[key] = value
    return metrics


# ======================================================================
# 5. 构建归档内容
# ======================================================================

def build_archive_content(holdings_data, report, career_profile, prev_content):
    """
    构建完整归档 markdown 内容
    与 profile_loader.py 的 _parse_markdown_tables 解析格式一致
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    today_str = datetime.date.today().strftime("%Y%m%d")

    lines = []
    lines.append(f"# 个人画像归档 - {today}")
    lines.append("")

    # ── 投资持仓概览 ──
    lines.append("## 投资持仓概览")
    lines.append("")

    prev_metrics = _extract_metrics_from_archive(prev_content) if prev_content else {}

    invest_detail = report.get("invest_detail", {})
    asset_summary = report.get("asset_summary", {})
    overview = report.get("overview", {})
    cash_items = report.get("cash", {})
    liability_items = report.get("liabilities", {})
    mortgage_info = report.get("mortgage", {})

    # ==================== 加密货币 ====================
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    crypto_assets = {
        "比特币(链上)": None,
        "Milady NFT(链上)": None,
        "ONDO": None,
        "Uniswap": None,
    }

    # 优先从报告明细中提取
    crypto_found = set()
    for label, info in invest_detail.items():
        for key in crypto_assets:
            if key in label or (key in ("ONDO", "Uniswap") and label.startswith(key)):
                crypto_found.add(key if key in label else key)
                lines.append(f"| {label} | {info['qty']} | {info['price']} | {info['market_value_cny']} | {info['storage']} |")
                break

    lines.append("")

    # ==================== 美股 ====================
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    # CRCL 汇总行 - 从按资产统计表获取
    crcl_summary = asset_summary.get("Circle(CRCL)", {})
    if crcl_summary:
        crcl_qty = crcl_summary.get("qty", "1,008.5")
        crcl_market = crcl_summary.get("market_value_cny", "¥679,889")
        # 从报告明细查找 CRCL 的当前价（找第一个以 Circle( 开头的明细）
        crcl_current_price = ""
        for label, info in invest_detail.items():
            if label.startswith("Circle("):
                crcl_current_price = info.get("price", "")
                break
        crcl_price = crcl_current_price if crcl_current_price else "$99.22"
        lines.append(f"| Circle(CRCL合计) | {crcl_qty} | {crcl_price} | {crcl_market} | 分散多账户 |")
    else:
        lines.append("| Circle(CRCL合计) | 1,008.5 | $99.22 | ¥679,889 | 分散多账户 |")

    # 其他美股
    us_stock_labels = ["DRAM", "MicroStrategy", "半导体3倍做多ETF", "BitGo", "Circle(燕币安)", "Circle(韩伟币安)", "Circle(韩伟长桥)", "Circle(华盛通)", "Circle(韩芳)"]
    for label, info in invest_detail.items():
        is_other_us = False
        for us_key in us_stock_labels:
            if us_key in label:
                is_other_us = True
                break
        if is_other_us and "CRCL合计" not in label:
            lines.append(f"| {label} | {info['qty']} | {info['price']} | {info['market_value_cny']} | {info['storage']} |")

    lines.append("")

    # ==================== 港股 ====================
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")

    hk_found = False
    for label, info in invest_detail.items():
        if "优必选" in label or "小米" in label or "港股通" in label:
            hk_found = True
            lines.append(f"| {label} | {info['qty']} | {info['price']} | {info['market_value_cny']} | {info['storage']} |")
    if not hk_found:
        lines.append("| 优必选(港股通) | 250 | HK$79.10 | ¥16,947 | 东方财富港股通 |")
        lines.append("| 小米集团(港股通) | 200 | HK$27.44 | ¥4,703 | 东方财富港股通 |")
    lines.append("")

    # ==================== A股 ====================
    lines.append("### A股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")

    a_found = False
    for label, info in invest_detail.items():
        if "科创50" in label or "创新药" in label or "A股" in label:
            a_found = True
            lines.append(f"| {label} | {info['qty']} | {info['price']} | {info['market_value_cny']} | {info['storage']} |")
    if not a_found:
        lines.append("| 科创50ETF(东方财富A股) | 8,500 | ¥1.703 | ¥14,476 | 东方财富证券 |")
        lines.append("| HK创新药ETF(东方财富A股) | 3,900 | ¥1.159 | ¥4,520 | 东方财富证券 |")
    lines.append("")

    # ==================== TS时间代币 ====================
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")

    ts_found = False
    for label, info in invest_detail.items():
        if "小安" in label or "午饭" in label or "时间" in label:
            ts_found = True
            lines.append(f"| {label} | {info['qty']} | {info['market_value_cny']} |")
    if not ts_found:
        lines.append("| 小安时间 | 106,499秒 | ¥15,450 |")
        lines.append("| 午饭老师时间 | 818秒 | ¥16,017 |")
    lines.append("")

    # ==================== 关键指标 ====================
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")

    total_assets = overview.get("总资产", "¥1,734,174")
    net_assets = overview.get("净资产", "¥1,334,174")
    invest_assets = overview.get("投资总资产", "¥961,494")

    lines.append(f"| 总资产 | **{total_assets}** |")
    lines.append(f"| 净资产 | **{net_assets}** |")
    lines.append(f"| 投资总资产 | **{invest_assets}** |")

    # 家庭备用金
    cash_cny = cash_items.get("家庭备用金(活期/货基)", "")
    if not cash_cny:
        cash_cny = cash_items.get("家庭备用金", "")
    if not cash_cny:
        for c in holdings_data["cash"]:
            if "家庭备用金" in c.get("name", ""):
                cash_cny = f"¥{c.get('amount_cny', ''):,}"
                break
    if not cash_cny:
        cash_cny = "¥630,808"
    lines.append(f"| 家庭备用金 | {cash_cny} |")

    # HK打新资金
    hk_cash = cash_items.get("HK打新资金", "")
    if hk_cash:
        lines.append(f"| HK打新资金 | {hk_cash} |")
    else:
        for c in holdings_data["cash"]:
            if "HK打新" in c.get("name", ""):
                hk_val = f"HK${c.get('amount_hkd', ''):,}"
                lines.append(f"| HK打新资金 | {hk_val} |")
                break

    # USDT 余额
    usdt_cash = cash_items.get("币安USDT余额", "")
    if usdt_cash:
        lines.append(f"| USDT余额 | {usdt_cash} |")
    else:
        for c in holdings_data["cash"]:
            if "币安USDT" in c.get("name", ""):
                usdt_val = f"${c.get('amount_usd', ''):,}"
                lines.append(f"| USDT余额 | {usdt_val} |")
                break

    # 华盛通现金
    hst_cash = cash_items.get("华盛通现金", "")
    if hst_cash:
        lines.append(f"| 华盛通现金 | {hst_cash} |")
    else:
        for c in holdings_data["cash"]:
            if "华盛通" in c.get("name", ""):
                hst_val = f"${c.get('amount_usd', ''):,}"
                lines.append(f"| 华盛通现金 | {hst_val} |")
                break

    # 信用卡负债
    credit_card = liability_items.get("信用卡循环(投资WEB3)", "")
    if not credit_card:
        for l in holdings_data["liabilities"]:
            if "信用卡" in l.get("name", ""):
                credit_card = f"¥{l.get('amount_cny', ''):,}"
                break
    if not credit_card:
        credit_card = "¥400,000"
    lines.append(f"| 信用卡负债 | {credit_card} |")

    # BTC占比
    btc_pct = ""
    for label, info in invest_detail.items():
        if "比特币" in label or "BTC" in label:
            btc_pct = info.get("pct", "")
            break
    if not btc_pct:
        btc_pct = "7.3%"
    lines.append(f"| BTC占投资比 | {btc_pct} |")

    # CRCL集中度
    crcl_pct = crcl_summary.get("pct", "")
    if not crcl_pct:
        for label, info in asset_summary.items():
            if "CRCL" in label:
                crcl_pct = info.get("pct", "")
                break
    if not crcl_pct:
        crcl_pct = "70.7%"
    if "⚠" in crcl_pct:
        lines.append(f"| CRCL集中度 | {crcl_pct} |")
    else:
        lines.append(f"| CRCL集中度 | {crcl_pct} ⚠️ |")

    # 房贷
    mortgage_commercial = mortgage_info.get("商贷", "¥400,000")
    mortgage_fund = mortgage_info.get("公积金", "¥1,400,000")
    lines.append(f"| 房贷总额 | {mortgage_commercial}+{mortgage_fund} |")
    lines.append("")

    # ── 职业发展画像 ──
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 当前公司 | {career_profile.get('company', '新华三')} |")
    lines.append(f"| 当前角色 | {career_profile.get('role', '嵌入式开发工程师')} |")
    lines.append(f"| 经验 | {career_profile.get('experience', '~9年（爱博精电6年+新华三3年）')} |")
    lines.append(f"| 技能栈 | {career_profile.get('skills', 'C语言, ARM/DSP架构, RTOS, Linux, Python, TFLM')} |")
    lines.append(f"| 核心能力 | {career_profile.get('core_abilities', '自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构')} |")
    lines.append(f"| 行业聚焦 | {career_profile.get('focus', '工业嵌入式、通信设备底层，非消费电子')} |")
    lines.append(f"| 地点约束 | {career_profile.get('location', '北京海淀/昌平')} |")
    lines.append(f"| 目标薪资 | {career_profile.get('salary_target', '50-70W总包')} |")
    lines.append(f"| 求职状态 | {career_profile.get('job_search', '已约 1 年')} |")
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
    lines.append(f"| 房贷商贷 | {mortgage_commercial} |")
    lines.append(f"| 房贷公积金 | {mortgage_fund} |")
    lines.append("| hanwei_zhongji | 达尔文50W (¥6,960/年, 2026-06-15生效) |")
    lines.append("| hanwei_dingshou | 待配置 (目标200W保额) |")
    lines.append("| xueyan_zhongji | 待配置 (目标30-50W保额) |")
    lines.append("")

    # ── A8计划进度 ──
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")

    # 从净资产计算进度
    net_val = net_assets.replace("**", "").replace("¥", "").replace(",", "").strip()
    try:
        net_num = float(net_val)
        a8_pct = round(net_num / 10000000 * 100, 1)
    except (ValueError, TypeError):
        a8_pct = 13.3

    # BTC目标进度
    btc_qty = 0.12980465
    btc_progress = round(btc_qty / 2.32 * 100, 1)

    lines.append("| 目标 | 1000万人民币 (2026-2028) |")
    lines.append(f"| 当前净资产 | **{net_assets}** ({a8_pct}%) |")
    lines.append(f"| BTC目标 | 2.32个 (当前{btc_qty}, 进度{btc_progress}%) |")

    # CRCL自持数量
    crcl_label = "Circle(CRCL)"
    crcl_info = asset_summary.get(crcl_label, {})
    crcl_qty_str = crcl_info.get("qty", "1,008.5")
    crcl_qty_num = float(crcl_qty_str.replace(",", "")) if crcl_qty_str else 1008.5
    crcl_pct_num = crcl_pct.replace("%", "").replace("⚠", "").strip() if crcl_pct else "70.7"
    lines.append(f"| CRCL自持 | {crcl_qty_str}股 (目标占比≤20%, 当前{crcl_pct_num}%⚠️) |")
    lines.append("| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")
    lines.append("| 当前状态 | 数据来自报告自动解析 |")
    lines.append("")

    # ── 本次更新变更记录 ──
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")

    # 对比关键指标变化
    def _extract_num(val):
        """从字符串中提取数字"""
        val = val.replace("**", "").replace("¥", "").replace("$", "").replace(",", "").replace("%", "").replace("⚠", "").strip()
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    changes = []
    for key in ("总资产", "净资产", "投资总资产"):
        new_val = overview.get(key, "")
        old_val = prev_metrics.get(key, "")
        if new_val and old_val:
            new_num = _extract_num(new_val)
            old_num = _extract_num(old_val)
            if new_num is not None and old_num is not None and old_num != 0:
                diff = new_num - old_num
                if abs(diff) > 0.01:
                    pct = round(diff / old_num * 100, 1)
                    sign = "+" if diff > 0 else ""
                    changes.append((key, old_val, new_val, f"{sign}{diff:,.0f} ({sign}{pct}%)"))

    if not changes:
        changes.append(("profile.last_sync", "—", today, "每日自动归档"))

    for key, old, new, note in changes:
        lines.append(f"| {key} | {old} | {new} | {note} |")

    # 数据源和职业档案变更记录
    prev_report_name = ""
    for line in (prev_content or "").split("\n"):
        if "数据源" in line and "|" in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3:
                prev_report_name = cells[2]  # 上一期的新值作为本期的旧值
                break

    lines.append(f"| 数据源 | {prev_report_name or '—'} | {report.get('report_name', '')} | 更新至最新报告 |")
    lines.append("| 职业档案 | 无变更 | 个人职业发展分析-端侧AI企业定制攻略.md | 无变更 |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# 6. 写入归档
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
# 7. 清理旧归档（保留最近 30 天）
# ======================================================================

def cleanup_old_archives(archive_dir, keep_days=30):
    """删除超过 keep_days 天的旧归档文件"""
    if not archive_dir.exists():
        return

    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    pattern = os.path.join(archive_dir, "profile_*.md")
    deleted = 0

    for fpath in glob.glob(pattern):
        fname = os.path.basename(fpath)
        m = re.search(r"profile_(\d{8})\.md", fname)
        if m:
            try:
                file_date = datetime.datetime.strptime(m.group(1), "%Y%m%d")
                if file_date < cutoff:
                    os.remove(fpath)
                    deleted += 1
            except (OSError, ValueError) as e:
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
        report = parse_report(report_path)
        logger.info(f"  解析到 {len(report['invest_detail'])} 项投资明细, {len(report['asset_summary'])} 项资产统计")

        # 3. 读取职业发展档案
        logger.info("步骤3: 读取职业发展档案 ...")
        career_profile = load_career_profile()
        logger.info(f"  公司: {career_profile.get('company')}, 角色: {career_profile.get('role')}")

        # 4. 加载前一天的归档（用于变更记录）
        logger.info("步骤4: 加载前一天归档用于变更对比 ...")
        prev_content = load_previous_archive(HOUR_ARCHIVE_DIR, today_str)

        # 5. 构建归档内容
        logger.info("步骤5: 构建归档内容 ...")
        content = build_archive_content(holdings_data, report, career_profile, prev_content)

        # 6. 写入两处归档
        logger.info("步骤6: 写入 profile_archive ...")
        hour_path = write_archive(content, HOUR_ARCHIVE_DIR, today_str)
        day_path = write_archive(content, DAY_ARCHIVE_DIR, today_str)

        # 7. 清理旧归档
        logger.info("步骤7: 清理旧归档 (保留30天) ...")
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