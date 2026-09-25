"""
每日0点执行：读取最新投资持仓和职业发展画像，生成两份归档摘要到 profile_archive 目录。
静默执行，异常时记录日志。

依赖: pip install pyyaml (若未安装)
"""

import os
import re
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None

# ── 路径配置 ──────────────────────────────────────────────
PROJECT_ROOT = Path(r"E:\ProjectGroup\AI\ContextStack")

HOLDINGS_PATH = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "holdings.yaml"
REPORTS_DIR = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "reports"
CAREER_PATH = PROJECT_ROOT / "02-Knowledge" / "career-development" / "career-strategy" / "个人职业发展分析-端侧AI企业定制攻略.md"

HOUR_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "0.trae-feishu-push-hour" / "profile_archive"
DAY_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "1.trae-feishu-push-day" / "profile_archive"

# ── 日志 ──────────────────────────────────────────────────
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"archive_profile_{datetime.now().strftime('%Y%m')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("archive_profile")


# ══════════════════════════════════════════════════════════
#  数据读取
# ══════════════════════════════════════════════════════════

def load_holdings() -> dict:
    """读取 holdings.yaml，返回结构化数据"""
    if not HOLDINGS_PATH.exists():
        raise FileNotFoundError(f"holdings.yaml 不存在: {HOLDINGS_PATH}")

    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    if yaml:
        data = yaml.safe_load(raw)
    else:
        # fallback 简易解析（仅提取关键字段）
        data = _simple_yaml_parse(raw)

    meta = data.get("meta", {})
    holdings_list = data.get("holdings", [])
    custody_list = data.get("custody", [])
    liabilities = data.get("liabilities", [])
    cash = data.get("cash", [])
    fixed_assets = data.get("fixed_assets", [])

    return {
        "meta": meta,
        "holdings": holdings_list,
        "custody": custody_list,
        "liabilities": liabilities,
        "cash": cash,
        "fixed_assets": fixed_assets,
    }


def _simple_yaml_parse(raw: str) -> dict:
    """极简 yaml 解析回退方案"""
    data = {"holdings": []}
    current_section = None
    current_item = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # section header
        if not line[0].isspace() and stripped.endswith(":"):
            current_section = stripped.rstrip(":")
            data.setdefault(current_section, [] if current_section in ("holdings", "custody", "liabilities", "cash", "fixed_assets") else {})
            current_item = None
            continue

        # list item
        if stripped.startswith("- "):
            current_item = {}
            data.setdefault(current_section, []).append(current_item)
            stripped = stripped[2:]
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                current_item[k.strip()] = v.strip()

        # key: value
        elif ":" in stripped and current_item is not None:
            k, v = stripped.split(":", 1)
            current_item[k.strip()] = v.strip().strip('"').strip("'")

        elif ":" in stripped and isinstance(data.get(current_section), dict):
            k, v = stripped.split(":", 1)
            data[current_section][k.strip()] = v.strip().strip('"').strip("'")

    return data


def find_latest_report() -> Optional[str]:
    """找到最新的月度报告文件，返回其内容"""
    if not REPORTS_DIR.exists():
        raise FileNotFoundError(f"报告目录不存在: {REPORTS_DIR}")

    files = sorted(REPORTS_DIR.glob("家庭资产报告-*.md"), reverse=True)
    if files:
        logger.info(f"使用最新报告: {files[0].name}")
        return files[0].read_text(encoding="utf-8")

    # fallback: 年度报告
    files = sorted(REPORTS_DIR.glob("家庭资产年度报告-*.md"), reverse=True)
    if files:
        logger.info(f"使用年度报告: {files[0].name}")
        return files[0].read_text(encoding="utf-8")

    logger.warning("未找到任何报告文件")
    return None


def parse_report_summary(report_text: str, cash_data: list) -> dict:
    """从报告文本中提取关键指标"""
    summary = {}

    _bold_key = r'\*{0,2}'  # 表头关键词两侧可能有 **

    m = re.search(rf'\| {_bold_key}投资净资产{_bold_key} \|\s*\*\*¥?([\d,]+)\*\*', report_text)
    if m:
        summary["investment_net_asset"] = float(m.group(1).replace(",", ""))

    m = re.search(rf'\| {_bold_key}持仓市值{_bold_key} \|\s*\*\*¥?([\d,]+)\*\*', report_text)
    if m:
        summary["position_value"] = float(m.group(1).replace(",", ""))

    m = re.search(rf'\| {_bold_key}投资资金总额{_bold_key} \|\s*\*\*¥?([\d,]+)\*\*', report_text)
    if m:
        summary["investment_total"] = float(m.group(1).replace(",", ""))

    # HK打新资金
    m = re.search(r'HK打新资金\s*\|\s*HK\$?([\d,]+)[^|]*\|\s*≈?¥?([\d,]+)?', report_text)
    if m:
        summary["hk_new_share"] = f"HK${m.group(1)} (≈¥{m.group(2)})" if m.group(2) else f"HK${m.group(1)}"

    # 信用卡负债
    m = re.search(r'\|\s*信用卡循环[^|]*\|\s*¥?([\d,]+)', report_text)
    if m:
        summary["credit_card_debt"] = float(m.group(1).replace(",", ""))

    # BTC占投资比
    m = re.search(r'比特币[^|]*\|\s*([\d.]+%)', report_text)
    if m:
        summary["btc_pct"] = m.group(1)

    # 房贷
    mortgages = []
    for line in report_text.splitlines():
        if '房贷' in line and '¥' in line:
            m2 = re.search(r'¥?([\d,]+)', line)
            if m2:
                mortgages.append(float(m2.group(1).replace(",", "")))

    # 家庭备用金
    m = re.search(r'家庭备用金[^)]*\)[：:]\s*¥?([\d,]+)', report_text)
    if m:
        summary["emergency_fund"] = float(m.group(1).replace(",", ""))
    else:
        m = re.search(r'家庭备用金[^|]*\|\s*¥?([\d,]+)', report_text)
        if m:
            summary["emergency_fund"] = float(m.group(1).replace(",", ""))

    # 房产
    m = re.search(r'北京海淀住宅[：:]\s*¥?([\d,]+)', report_text)
    if m:
        summary["house_value"] = float(m.group(1).replace(",", ""))

    return summary


def parse_career_profile(career_text: str) -> dict:
    """从职业发展文档中提取关键画像"""
    profile = {}
    lines = career_text.splitlines()

    def _clean(value: str) -> str:
        """去除 markdown 表格行尾的 ` |` 和首尾空白"""
        return re.sub(r'\s*\|\s*$', '', value).strip()

    for i, line in enumerate(lines):
        if "总经验" in line and "年" in line:
            m = re.search(r'\*\*~?(\d+)\s*年\*\*', line)
            if m:
                profile["experience_years"] = m.group(1)
        if "职业路径" in line:
            m = re.search(r'爱博精电.*?→\s*(.+)', line)
            if m:
                profile["career_path"] = _clean(m.group(1))
        if "S级能力" in line:
            m = re.search(r'S级能力[^|]+\|\s*(.+)', line)
            if m:
                profile["s_level_skills"] = _clean(m.group(1))
        if "技能栈" in line:
            m = re.search(r'技能栈[^|]+\|\s*(.+)', line)
            if m:
                profile["skills"] = _clean(m.group(1))
        if "行业聚焦" in line:
            m = re.search(r'行业聚焦[^|]+\|\s*(.+)', line)
            if m:
                profile["industry"] = _clean(m.group(1))
        if "地点约束" in line:
            m = re.search(r'地点约束[^|]+\|\s*(.+)', line)
            if m:
                profile["location"] = _clean(m.group(1))
        if "求职周期" in line:
            m = re.search(r'求职周期[^|]+\|\s*(.+)', line)
            if m:
                profile["job_search"] = _clean(m.group(1))

    # 目标公司
    profile["target_companies"] = []
    in_section = False
    for line in lines:
        if line.startswith("### 海淀区") or line.startswith("### 昌平区") or line.startswith("### 北京其他区域"):
            in_section = True
            continue
        if line.startswith("---"):
            in_section = False
            continue
        if in_section and line.startswith("| **") and "|" in line:
            parts = line.split("|")
            if len(parts) >= 2:
                company = parts[1].strip().strip("**").strip()
                if company:
                    profile["target_companies"].append(company)

    # 角色信息
    profile["role"] = "嵌入式开发工程师"
    profile["company"] = "新华三"

    # 薪资
    m = re.search(r'建议范围\s*\*\*¥?(\d+)[–-]?(\d+)?', career_text)
    if m:
        low = m.group(1)
        high = m.group(2) or ""
        profile["salary_range"] = f"{low}-{high}W" if high else f"{low}W"

    return profile


# ══════════════════════════════════════════════════════════
#  归档生成
# ══════════════════════════════════════════════════════════

def categorize_holdings(holdings: list) -> dict:
    """将持仓列表按类别分组"""
    categories = {
        "crypto": [],       # 加密货币
        "us_stock": [],     # 美股
        "hk_stock": [],     # 港股
        "a_stock": [],      # A股
        "ts_token": [],     # TS时间代币
        "other": [],        # 其他
    }

    for h in holdings:
        cat = h.get("category", "")
        symbol = h.get("symbol", "")
        name = h.get("name", "")
        quantity = h.get("quantity", 0)
        storage = h.get("storage", "")
        price_source = h.get("price_source", "")

        if cat in ("crypto",) and symbol not in ("MILADY",):
            categories["crypto"].append(h)
        elif cat == "crypto" and symbol == "MILADY":
            categories["crypto"].append(h)
        elif cat in ("us_stock_tokenized", "us_stock"):
            categories["us_stock"].append(h)
        elif cat == "hk_stock":
            categories["hk_stock"].append(h)
        elif cat == "a_stock":
            categories["a_stock"].append(h)
        elif cat == "ts_time_token":
            categories["ts_token"].append(h)
        else:
            categories["other"].append(h)

    return categories


def generate_holdings_tables(holdings_data: dict) -> str:
    """生成持仓概览的 Markdown 表格"""
    categories = categorize_holdings(holdings_data)

    lines = []

    # ── 加密货币 ──
    crypto_items = categories["crypto"]
    if crypto_items:
        lines.append("### 加密货币")
        lines.append("| 标的 | 数量 | 存放 |")
        lines.append("|------|------|------|")
        for h in crypto_items:
            name = h.get("name", h.get("symbol", ""))
            qty = h.get("quantity", "")
            unit = h.get("unit", "")
            qty_str = f"{qty:,}{unit}" if isinstance(qty, (int, float)) and unit else str(qty)
            storage = h.get("storage", "")
            lines.append(f"| {name} | {qty_str} | {storage} |")
        lines.append("")

    # ── 美股（含代币化美股） ──
    us_items = categories["us_stock"]
    # 合并 CRCL
    crcl_total_qty = 0
    crcl_breakdown = []
    non_crcl = []
    for h in us_items:
        if h.get("symbol") == "CRCL":
            qty = h.get("quantity", 0)
            crcl_total_qty += qty
            crcl_breakdown.append((h.get("name", ""), qty, h.get("storage", "")))
        else:
            non_crcl.append(h)

    if us_items:
        lines.append("### 美股")
        lines.append("| 标的 | 数量 | 存放 |")
        lines.append("|------|------|------|")

        # Circle(CRCL) 合并行
        if crcl_total_qty > 0:
            lines.append(f"| **Circle(CRCL合计)** | **{crcl_total_qty}** | **分散多账户** |")

        for h in non_crcl:
            name = h.get("name", h.get("symbol", ""))
            qty = h.get("quantity", 0)
            qty_str = f"{qty:,}" if isinstance(qty, (int, float)) else str(qty)
            storage = h.get("storage", "")
            lines.append(f"| {name} | {qty_str} | {storage} |")
        lines.append("")

    # ── 港股 ──
    hk_items = categories["hk_stock"]
    if hk_items:
        lines.append("### 港股")
        lines.append("| 标的 | 数量 | 存放 |")
        lines.append("|------|------|------|")
        for h in hk_items:
            name = h.get("name", h.get("symbol", ""))
            qty = h.get("quantity", 0)
            qty_str = f"{qty:,}" if isinstance(qty, (int, float)) else str(qty)
            storage = h.get("storage", "")
            lines.append(f"| {name} | {qty_str} | {storage} |")
        lines.append("")

    # ── A股 ──
    a_items = categories["a_stock"]
    if a_items:
        lines.append("### A股")
        lines.append("| 标的 | 数量 | 存放 |")
        lines.append("|------|------|------|")
        for h in a_items:
            name = h.get("name", h.get("symbol", ""))
            qty = h.get("quantity", 0)
            qty_str = f"{qty:,}" if isinstance(qty, (int, float)) else str(qty)
            storage = h.get("storage", "")
            lines.append(f"| {name} | {qty_str} | {storage} |")
        lines.append("")

    # ── TS时间代币 ──
    ts_items = categories["ts_token"]
    if ts_items:
        lines.append("### TS时间代币")
        lines.append("| 标的 | 数量 |")
        lines.append("|------|------|")
        for h in ts_items:
            name = h.get("name", "")
            qty = h.get("quantity", 0)
            unit = h.get("unit", "")
            qty_str = f"{qty:,}{unit}" if isinstance(qty, (int, float)) and unit else str(qty)
            lines.append(f"| {name} | {qty_str} |")
        lines.append("")

    return "\n".join(lines)


def generate_key_metrics(report_summary: dict, holdings_data: dict, cash_data: list) -> str:
    """生成关键指标表格"""
    lines = []
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")

    inv_net = report_summary.get("investment_net_asset", 0)
    inv_total = report_summary.get("investment_total", 0)
    pos_value = report_summary.get("position_value", 0)
    hk_fund = report_summary.get("hk_new_share", "")

    if inv_total:
        lines.append(f"| 投资总资产 | **¥{inv_total:,.0f}** |")
    if pos_value:
        lines.append(f"| 持仓市值 | **¥{pos_value:,.0f}** |")
    if inv_net:
        lines.append(f"| 投资净资产 | **¥{inv_net:,.0f}** |")

    # 备用金
    ef = report_summary.get("emergency_fund", 0)
    if ef:
        lines.append(f"| 家庭备用金 | ¥{ef:,.0f} |")
    else:
        lines.append("| 家庭备用金 | ¥480,808 |")

    if hk_fund:
        lines.append(f"| HK打新资金 | {hk_fund} |")

    # 现金（排除 HK打新资金，已从报告提取）
    for c in cash_data:
        name = c.get("name", "")
        if "打新" in name:
            continue
        usd = c.get("amount_usd", 0)
        hkd = c.get("amount_hkd", 0)
        if usd:
            lines.append(f"| {name} | ${usd:,} USD |")
        if hkd:
            lines.append(f"| {name} | HK${hkd:,} |")

    # 信用卡负债
    cc = report_summary.get("credit_card_debt", 0)
    if cc:
        lines.append(f"| 信用卡负债 | ¥{cc:,.0f} |")

    # BTC占投资比 and CRCL集中度
    btc_pct = report_summary.get("btc_pct", "")
    if btc_pct:
        lines.append(f"| BTC占投资比 | {btc_pct} |")

    crcl_qty = sum(h.get("quantity", 0) for h in holdings_data if h.get("symbol") == "CRCL")
    lines.append(f"| CRCL集中度 | {crcl_qty:.0f}股 ⚠️ |")
    lines.append(f"| 房贷总额 | ¥400,000+¥1,400,000 |")

    return "\n".join(l for l in lines if l)


def generate_career_section(career_profile: dict) -> str:
    """生成职业发展画像表格"""
    lines = []
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")

    lines.append(f"| 当前公司 | {career_profile.get('company', '新华三')} |")
    lines.append(f"| 当前角色 | {career_profile.get('role', '嵌入式开发工程师')} |")
    lines.append(f"| 经验 | **~{career_profile.get('experience_years', '9')}年**（爱博精电 6年 + 新华三 3年） |")
    lines.append(f"| 技能栈 | {career_profile.get('skills', '')} |")
    lines.append(f"| 核心能力 | {career_profile.get('s_level_skills', '')} |")
    lines.append(f"| 行业聚焦 | {career_profile.get('industry', '')} |")
    lines.append(f"| 地点约束 | {career_profile.get('location', '')} |")
    salary = career_profile.get('salary_range', '50-70W')
    lines.append(f"| 目标薪资 | {salary}总包 |")
    lines.append(f"| 求职状态 | {career_profile.get('job_search', '')} |")
    lines.append(f"| 面试方法论 | 工程叙事四层结构: 本质→实践→踩坑→思考 |")

    companies = career_profile.get("target_companies", [])
    if companies:
        lines.append(f"| 目标公司 | {'、'.join(companies[:8])}{'等' if len(companies) > 8 else ''} |")

    return "\n".join(lines)


def generate_family_section(report_summary: dict, fixed_assets: list) -> str:
    """生成家庭与保险信息"""
    lines = []
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")

    lines.append("| 居住地 | 北京 |")
    lines.append("| 户籍 | 非京籍 (内蒙古) |")
    lines.append("| 子女 | 暂无（计划明后年备孕） |")
    lines.append("| 配偶 | 已婚 (薛燕) |")

    house = report_summary.get("house_value", 0)
    if house:
        lines.append(f"| 房产 | 北京海淀住宅 ¥{house:,.0f} (购入2025年底) |")
    else:
        lines.append("| 房产 | 北京海淀住宅 ¥320W (购入2025年底) |")

    lines.append("| 房贷商贷 | ¥400,000 |")
    lines.append("| 房贷公积金 | ¥1,400,000 |")
    lines.append("| hanwei_zhongji | 达尔文50W (¥6,960/年, 2026-06-15生效) |")
    lines.append("| hanwei_dingshou | 待配置 (目标200W保额) |")
    lines.append("| xueyan_zhongji | 待配置 (目标30-50W保额) |")

    return "\n".join(lines)


def generate_a8_section(report_summary: dict, holdings_data: list) -> str:
    """生成 A8 计划进度"""
    lines = []
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")
    lines.append("| 目标 | 1000万人民币 (2026-2028) |")

    inv_net = report_summary.get("investment_net_asset", 0)
    if inv_net:
        pct = inv_net / 10_000_000 * 100
        lines.append(f"| 当前净资产 | **¥{inv_net:,.0f}** ({pct:.1f}%) |")

    # BTC count
    btc_qty = 0
    for h in holdings_data:
        if h.get("symbol") == "BTC":
            btc_qty = h.get("quantity", 0)
    btc_progress = (btc_qty / 2.32) * 100 if btc_qty else 0
    lines.append(f"| BTC目标 | 2.32个 (当前{btc_qty}, 进度{btc_progress:.1f}%) |")

    # CRCL
    crcl_qty = sum(h.get("quantity", 0) for h in holdings_data if h.get("symbol") == "CRCL")
    lines.append(f"| CRCL自持 | {crcl_qty:.0f}股 (目标占比≤20%, 当前集中度⚠️) |")

    lines.append("| 策略 | MA120趋势 + 月度定投 + 港股打新 |")
    lines.append("| 当前状态 | 数据来自 holdings.yaml 实时解析 |")

    return "\n".join(lines)


def generate_change_log() -> str:
    """生成变更记录"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    lines.append(f"| profile.last_sync | — | {today} | 每日自动归档 |")
    lines.append(f"| 数据源 | holdings.yaml + 最新报告 | holdings.yaml + 最新报告 | 实时解析 |")
    lines.append(f"| 职业档案 | 无变更 | 个人职业发展分析-端侧AI企业定制攻略.md | 无变更 |")

    return "\n".join(lines)


def build_archive(
    holdings_data: list,
    report_text: Optional[str],
    report_summary: dict,
    career_profile: dict,
    cash_data: list,
    fixed_assets: list,
) -> str:
    """组装完整的归档内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    parts = []

    parts.append(f"# 个人画像归档 - {today}")
    parts.append("")

    parts.append("## 投资持仓概览")
    parts.append("")
    parts.append(generate_holdings_tables(holdings_data))
    parts.append(generate_key_metrics(report_summary, holdings_data, cash_data))
    parts.append("")
    parts.append(generate_career_section(career_profile))
    parts.append("")
    parts.append(generate_family_section(report_summary, fixed_assets))
    parts.append("")
    parts.append(generate_a8_section(report_summary, holdings_data))
    parts.append("")
    parts.append(generate_change_log())

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════
#  主流程
# ══════════════════════════════════════════════════════════

def main():
    today_str = datetime.now().strftime("%Y%m%d")
    logger.info(f"=== 开始每日归档: {today_str} ===")

    try:
        # 1. 读取持仓
        holdings_data_raw = load_holdings()
        holdings_list = holdings_data_raw["holdings"]
        cash_data = holdings_data_raw["cash"]
        fixed_assets = holdings_data_raw["fixed_assets"]
        logger.info(f"holdings.yaml 读取完成, 共 {len(holdings_list)} 个标的")

        # 2. 读取投资报告
        report_text = find_latest_report()
        if report_text:
            report_summary = parse_report_summary(report_text, cash_data)
            logger.info("报告解析完成")
        else:
            report_summary = {}
            logger.warning("无报告可用，使用 holdings.yaml 数据")

        # 3. 读取职业档案
        if CAREER_PATH.exists():
            career_text = CAREER_PATH.read_text(encoding="utf-8")
            career_profile = parse_career_profile(career_text)
            logger.info("职业档案读取完成")
        else:
            career_profile = {}
            logger.warning(f"职业档案不存在: {CAREER_PATH}")

        # 4. 生成归档
        archive_content = build_archive(
            holdings_list, report_text, report_summary,
            career_profile, cash_data, fixed_assets,
        )

        # 5. 写入两个目录
        for archive_dir in [HOUR_ARCHIVE_DIR, DAY_ARCHIVE_DIR]:
            archive_dir.mkdir(parents=True, exist_ok=True)
            output_path = archive_dir / f"profile_{today_str}.md"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(archive_content)

            logger.info(f"归档写入成功: {output_path}")

        # 6. 清理旧归档（保留最近30天）
        for archive_dir in [HOUR_ARCHIVE_DIR, DAY_ARCHIVE_DIR]:
            if archive_dir.exists():
                all_files = sorted(archive_dir.glob("profile_*.md"), reverse=True)
                for f in all_files[30:]:
                    f.unlink(missing_ok=True)
                    logger.info(f"清理旧归档: {f.name}")

        logger.info(f"=== 归档完成: {today_str} ===")

    except Exception as e:
        logger.error(f"归档失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()