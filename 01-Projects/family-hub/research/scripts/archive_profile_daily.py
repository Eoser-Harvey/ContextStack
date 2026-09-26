#!/usr/bin/env python3
"""
每日 00:00 自动归档个人画像

读取投资持仓(holdings.yaml) + 最新月度报告 + 职业发展档案，
生成两份 profile_YYYYMMDD.md 到小时推送和日报推送的 profile_archive/ 目录。
两份内容一致，profile_loader.py 自动按日期取最新文件。

工作流:
  holdings.yaml ──→ 最新报告(价格+指标) ──→ 职业档案 ──→ 两份归档
  静默完成，异常时记录日志不阻断。

架构说明:
  - profile_loader.py 自动从 profile_archive/ 按文件名日期排序取最新文件
  - analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile()
  - config.yaml 不再硬编码 profile 段
  - 更新 profile_archive/ 即自动生效，无需修改任何代码
"""

import os
import sys
import datetime
import re
import glob
import logging
import traceback
from pathlib import Path

# ── 依赖检查 ──────────────────────────────────────────────────────────
try:
    import yaml
except ImportError:
    print("[FATAL] 缺少依赖 PyYAML，请执行: pip install pyyaml")
    sys.exit(1)

# ── 路径配置 ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(r"E:\ProjectGroup\AI\ContextStack")
HOLDINGS_PATH = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "holdings.yaml"
REPORTS_DIR = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "reports"
CAREER_PATH = PROJECT_ROOT / "02-Knowledge" / "career-development" / "career-strategy" / "个人职业发展分析-端侧AI企业定制攻略.md"
OUTPUT_HOUR = PROJECT_ROOT / "01-Projects" / "automated-task" / "0.trae-feishu-push-hour" / "profile_archive"
OUTPUT_DAY = PROJECT_ROOT / "01-Projects" / "automated-task" / "1.trae-feishu-push-day" / "profile_archive"

# ── 日志配置 ──────────────────────────────────────────────────────────
log = logging.getLogger("archive_profile_daily")
log.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
log.addHandler(_handler)


# ======================================================================
# 1. 数据读取
# ======================================================================

def load_holdings():
    """解析 holdings.yaml，返回结构化 dict"""
    if not HOLDINGS_PATH.exists():
        log.error(f"holdings.yaml 不存在: {HOLDINGS_PATH}")
        return None
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def find_latest_report():
    """在 reports/ 目录中找到最新的月度报告文件"""
    if not REPORTS_DIR.exists():
        log.error(f"reports 目录不存在: {REPORTS_DIR}")
        return None
    files = sorted(REPORTS_DIR.glob("家庭资产报告-*.md"), reverse=True)
    if not files:
        log.error("未找到 家庭资产报告-*.md 文件")
        return None
    return files[0]


def load_report(report_path):
    """读取报告文件，提取关键数据的行"""
    if not report_path or not os.path.exists(report_path):
        return None
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def load_career_profile():
    """读取职业发展档案"""
    if not CAREER_PATH.exists():
        log.error(f"职业档案不存在: {CAREER_PATH}")
        return None
    with open(CAREER_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def load_previous_archive():
    """加载上一份归档（用于继承静态信息如家庭/保险）"""
    candidates = sorted(OUTPUT_HOUR.glob("profile_*.md"), reverse=True)
    if not candidates:
        log.warning("无上一份归档可继承")
        return None
    # 跳过今天已生成的（避免自我继承）
    today_str = datetime.date.today().strftime("%Y%m%d")
    prev = [f for f in candidates if today_str not in f.name]
    if not prev:
        return None
    with open(prev[0], "r", encoding="utf-8") as f:
        return f.read()


# ======================================================================
# 2. 数据解析
# ======================================================================

def parse_report_prices(report_text):
    """
    从报告中提取投资标的的价格映射
    返回 { 标的名称: { "qty": str, "price": str, "market_value": str, "storage": str } }
    """
    prices = {}
    in_section = False
    # 从 "二、投资资产明细（含盈亏）" 表中逐行解析
    for line in report_text.split("\n"):
        # 定位表格区域
        if "投资资产明细" in line or "| 标的 | 数量 | 当前单价" in line:
            in_section = True
            continue
        if in_section:
            # 遇到下一个 ## 或空行过多则退出
            if line.startswith("## ") and line.strip() and "持仓变动" not in line and "价格变动" not in line:
                break
            if line.startswith("|") and "|----" not in line and "| 标的 | 数量 |" not in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 6:
                    name = cells[0]
                    qty = cells[1]
                    price = re.sub(r'^[¥$]|^HK\$', '', cells[2]).strip()
                    mkt_val = cells[3]
                    storage = cells[-1] if len(cells) > 6 else ""
                    prices[name] = {"qty": qty, "price": price, "market_value": mkt_val, "storage": storage}
    return prices


def parse_report_metrics(report_text):
    """从报告##### 八、关键指标 中提取指标"""
    metrics = {}
    in_section = False
    for line in report_text.split("\n"):
        if "关键指标" in line and ("vs" in line or "上期" in line):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.startswith("|") and "|----" not in line and "指标" not in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 2:
                    k = cells[0]
                    v = cells[1] if len(cells) >= 2 else ""
                    metrics[k] = v
    return metrics


def parse_report_summary(report_text):
    """从报告 一、资产总览 提取汇总数据"""
    summary = {}
    in_section = False
    for line in report_text.split("\n"):
        if line.startswith("## 一、资产总览"):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.startswith("|") and "|----" not in line and "类别" not in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 2:
                    k = cells[0]
                    v = cells[1]
                    summary[k] = v
    return summary


def extract_section(text, section_title):
    """从 markdown 中提取指定 ## 节的内容"""
    lines = text.split("\n")
    result = []
    in_section = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and section_title in stripped:
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## "):
                break
            result.append(line)
    return "\n".join(result).strip()


def parse_career_from_md(text):
    """从职业发展档案中提取结构化数据"""
    career = {}
    lines = text.split("\n")

    # 提取当前画像表格
    in_table = False
    table_rows = {}
    for line in lines:
        stripped = line.strip()
        if "当前画像" in stripped and stripped.startswith("##"):
            in_table = True
            continue
        if in_table:
            if stripped.startswith("##"):
                break
            if stripped.startswith("|") and "|----" not in stripped and "维度" not in stripped:
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 2:
                    key = cells[0].replace("**", "").strip()
                    val = cells[1].replace("**", "").strip()
                    table_rows[key] = val

    # 目标公司清单（从 二、北京海淀/昌平目标公司 提取）
    companies = []
    in_company = False
    for line in lines:
        stripped = line.strip()
        if "北京海淀/昌平目标公司" in stripped and stripped.startswith("##"):
            in_company = True
            continue
        if in_company:
            if stripped.startswith("## "):
                break
            # 从公司表格行提取公司名
            if stripped.startswith("|") and "|----" not in stripped and "公司" not in stripped:
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if cells:
                    companies.append(cells[0])

    career["companies"] = companies
    career["experience"] = table_rows.get("总经验", "")
    career["role"] = table_rows.get("职业路径", "")
    career["skills"] = table_rows.get("技能栈", "")
    career["core_abilities"] = table_rows.get("S级能力", "")
    career["focus"] = table_rows.get("行业聚焦", "")
    career["location"] = table_rows.get("地点约束", "")
    career["job_search"] = table_rows.get("求职周期", "")

    # 提取薪资预期
    salary_match = re.search(r'建议范围\s*\*\*(¥?\d+[Kk]?[-\u2013~]\d+[Kk]?\s*万?\s*总包)\*\*', text)
    if salary_match:
        career["salary"] = salary_match.group(1)
    else:
        m = re.search(r'总包范围\s*\||\*\*¥?(\d+)[-\u2013~](\d+)W', text)
        if m:
            career["salary"] = f"¥{m.group(1)}-{m.group(2)}W总包"

    return career


def parse_holdings_for_portfolio(data):
    """
    从 holdings.yaml 中提取持仓列表，按类别分组
    """
    result = {
        "crypto": [],
        "us_stock": [],
        "hk_stock": [],
        "a_stock": [],
        "ts_token": [],
        "cash": [],
        "custody": [],
        "liabilities": [],
        "fixed_assets": [],
    }
    if not data:
        return result

    for h in data.get("holdings", []):
        cat = h.get("category", "")
        item = {
            "id": h.get("id", ""),
            "symbol": h.get("symbol", ""),
            "name": h.get("name", ""),
            "quantity": h.get("quantity", 0),
            "unit": h.get("unit", "股"),
            "storage": h.get("storage", ""),
            "cost_basis_usd": h.get("cost_basis_usd", 0),
            "raw": h,
        }
        if cat == "crypto" and "nft" not in h.get("id", ""):
            result["crypto"].append(item)
        elif cat == "crypto" and "nft" in h.get("id", ""):
            result["crypto"].append(item)  # NFT 也归入 crypto
        elif "us_stock" in cat:
            result["us_stock"].append(item)
        elif cat == "hk_stock":
            result["hk_stock"].append(item)
        elif cat == "a_stock":
            result["a_stock"].append(item)
        elif cat == "ts_time_token":
            result["ts_token"].append(item)

    result["cash"] = data.get("cash", [])
    result["custody"] = data.get("custody", [])
    result["liabilities"] = data.get("liabilities", [])
    result["fixed_assets"] = data.get("fixed_assets", [])
    return result


def get_report_name(report_path):
    """获取报告文件名"""
    if not report_path:
        return "未知"
    return os.path.basename(report_path)


# ======================================================================
# 3. 档案生成
# ======================================================================

def _fmt_qty(qty, unit="股"):
    """统一格式化数量"""
    if isinstance(qty, (int, float)):
        if qty == int(qty):
            return str(int(qty))
        return f"{qty:g}" if unit == "股" else f"{qty:g}{unit}"
    return str(qty)


def _fmt_price_usd(price):
    """格式化美元价格，避免双前缀"""
    if not price or price == "—":
        return "—"
    p = price.replace("$", "").replace("HK$", "").replace("¥", "").strip()
    return f"${p}"


def _fmt_price_hkd(price):
    """格式化港币价格，避免双前缀"""
    if not price or price == "—":
        return "—"
    p = price.replace("$", "").replace("HK$", "").replace("¥", "").strip()
    return f"HK${p}"


def _fmt_price_cny(price):
    """格式化人民币价格"""
    if not price or price == "—":
        return "—"
    p = price.replace("$", "").replace("HK$", "").replace("¥", "").strip()
    return p


def _fmt_value(val):
    """统一格式化关键指标值，避免双 **"""
    if not val or val == "—":
        return "—"
    return val.replace("**", "")


def build_portfolio_section(data, report_prices, report_summary, report_metrics):
    """构建投资持仓概览"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    report_name = get_report_name(find_latest_report())

    # --- 加密货币表 ---
    crypto_rows = []
    for item in data.get("crypto", []):
        name = item["name"]
        qty = item["quantity"]
        unit = item.get("unit", "股")
        storage = item.get("storage", "")

        # 从报告获取价格
        price_info = report_prices.get(name, {})
        price_usd = price_info.get("price", "—")
        mkt_val = price_info.get("market_value", "")

        qty_str = _fmt_qty(qty, unit)

        crypto_rows.append((name, qty_str, _fmt_price_usd(price_usd), mkt_val, storage))

    # --- 美股表 ---
    us_rows = []
    # 先计算 CRCL 合计
    crcl_total_qty = 0
    crcl_items = []
    for item in data.get("us_stock", []):
        if item["symbol"] == "CRCL":
            crcl_total_qty += item["quantity"]
            crcl_items.append(item)

    if crcl_total_qty > 0:
        crcl_price = report_prices.get("Circle(CRCL)", {}).get("price", report_prices.get("Circle(韩伟币安)", {}).get("price", "—"))
        crcl_mkt_val = report_prices.get("Circle(CRCL)", {}).get("market_value", "")
        if not crcl_mkt_val:
            crcl_item_price = report_prices.get("Circle(韩伟币安)", {}).get("price", "—")
            try:
                crcl_price_val = float(crcl_item_price.replace(",", "")) if crcl_item_price != "—" else 0
                crcl_mkt_val = f"¥{crcl_total_qty * crcl_price_val * 6.716:,.0f}"
            except (ValueError, TypeError):
                pass
        us_rows.append((f"Circle(CRCL合计)", str(int(crcl_total_qty)), _fmt_price_usd(str(crcl_price)), crcl_mkt_val, "分散多账户"))

    for item in data.get("us_stock", []):
        name = item["name"]
        qty = item["quantity"]
        storage = item.get("storage", "")

        price_info = report_prices.get(name, {})
        if not price_info:
            # 尝试按存储位置匹配
            for rn, rv in report_prices.items():
                if item["symbol"] in rn and storage[:2] in rn:
                    price_info = rv
                    break

        price_usd = price_info.get("price", "—")
        mkt_val = price_info.get("market_value", "")

        us_rows.append((name, _fmt_qty(qty),
                        _fmt_price_usd(price_usd),
                        mkt_val, storage))

    # --- 港股表 ---
    hk_rows = []
    for item in data.get("hk_stock", []):
        name = item["name"]
        qty = item["quantity"]
        storage = item.get("storage", "")

        price_info = report_prices.get(name, {})
        price_hkd = price_info.get("price", "—")
        mkt_val = price_info.get("market_value", "")

        hk_rows.append((name, _fmt_qty(qty),
                        _fmt_price_hkd(price_hkd),
                        mkt_val, storage))

    # --- A股表 ---
    a_rows = []
    for item in data.get("a_stock", []):
        name = item["name"]
        qty = item["quantity"]
        storage = item.get("storage", "")

        price_info = report_prices.get(name, {})
        price_cny = price_info.get("price", "—")
        mkt_val = price_info.get("market_value", "")

        a_rows.append((name, _fmt_qty(qty),
                       _fmt_price_cny(price_cny),
                       mkt_val, storage))

    # --- TS时间代币表 ---
    ts_rows = []
    for item in data.get("ts_token", []):
        name = item["name"]
        qty = item["quantity"]
        unit = item.get("unit", "股")

        price_info = report_prices.get(name, {})
        mkt_val = price_info.get("market_value", "")

        ts_rows.append((name, f"{qty:g}{unit}" if isinstance(qty, (int, float)) else str(qty), mkt_val))

    # --- 关键指标 ---
    metrics = {}
    # 从报告汇总提取
    total_assets = report_summary.get("投资资金总额", "—") if isinstance(report_summary, dict) else "—"
    net_assets = report_summary.get("投资净资产", "—") if isinstance(report_summary, dict) else "—"
    invest_total = report_summary.get("持仓市值", "—") if isinstance(report_summary, dict) else "—"

    if isinstance(report_summary, dict):
        for k, v in report_summary.items():
            if "投资资金总额" in k:
                total_assets = v
            elif "投资净资产" in k:
                net_assets = v
            elif "持仓市值" in k:
                invest_total = v

    # 从负债提取
    cc_debt = "—"
    mortgage_commercial = "—"
    mortgage_fund = "—"
    for l in data.get("liabilities", []):
        name = l.get("name", "")
        amt = l.get("amount_cny", 0)
        if "信用卡" in name:
            cc_debt = f"¥{amt:,}"
        elif "商贷" in name:
            mortgage_commercial = f"¥{amt:,}"
        elif "公积金" in name:
            mortgage_fund = f"¥{amt:,}"

    # 备用金
    reserve = "—"
    for fa in data.get("fixed_assets", []):
        name = fa.get("name", "")
        if "备用金" in name or "家庭备用金" in name:
            reserve = f"¥{fa.get('value_cny', 0):,}"

    # HK打新资金
    hk_fund = "—"
    for c in data.get("cash", []):
        name = c.get("name", "")
        if "HK打新" in name or "打新" in name:
            hk_fund = f"HK${c.get('amount_hkd', 0):,}"
            break
    else:
        for c in data.get("cash", []):
            if "抢融" in c.get("name", ""):
                hk_fund = f"${c.get('amount_usd', 0):,}"

    # 华盛通现金
    waston_cash = "—"
    for c in data.get("cash", []):
        if "华盛通" in c.get("name", ""):
            waston_cash = f"${c.get('amount_usd', 0):,}"

    metrics = {
        "总资产": total_assets,
        "净资产": net_assets,
        "投资总资产": invest_total,
        "家庭备用金": reserve,
        "HK打新资金": hk_fund,
        "华盛通现金": waston_cash,
        "信用卡负债": cc_debt,
    }

    # 从报告中获取 BTC 占比、CRCL 集中度
    metrics_from_report = {}
    if isinstance(report_summary, dict):
        for k, v in report_summary.items():
            if "BTC" in k:
                metrics_from_report["BTC占投资比"] = v
            elif "CRCL" in k or "Circle" in k:
                pass

    # 从投资资产明细表提取集中度
    for line in extract_section(report_prices if isinstance(report_prices, str) else "", "").split("\n"):
        pass

    # 构建输出
    sections = []
    sections.append("## 投资持仓概览\n")

    if crypto_rows:
        sections.append("### 加密货币")
        sections.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
        sections.append("|------|------|------------|-----------|------|")
        for row in crypto_rows:
            sections.append(f"| {' | '.join(str(c) for c in row)} |")
        sections.append("")

    if us_rows:
        sections.append("### 美股")
        sections.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
        sections.append("|------|------|------------|-----------|------|")
        for row in us_rows:
            sections.append(f"| {' | '.join(str(c) for c in row)} |")
        sections.append("")

    if hk_rows:
        sections.append("### 港股")
        sections.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
        sections.append("|------|------|-------|-----------|------|")
        for row in hk_rows:
            sections.append(f"| {' | '.join(str(c) for c in row)} |")
        sections.append("")

    if a_rows:
        sections.append("### A股")
        sections.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
        sections.append("|------|------|-------|-----------|------|")
        for row in a_rows:
            sections.append(f"| {' | '.join(str(c) for c in row)} |")
        sections.append("")

    if ts_rows:
        sections.append("### TS时间代币")
        sections.append("| 标的 | 数量 | 市值(CNY) |")
        sections.append("|------|------|-----------|")
        for row in ts_rows:
            sections.append(f"| {' | '.join(str(c) for c in row)} |")
        sections.append("")

    sections.append("### 关键指标")
    sections.append("| 指标 | 数值 |")
    sections.append("|------|------|")
    for k, v in metrics.items():
        fmt_v = _fmt_value(v)
        if fmt_v and fmt_v != "—":
            sections.append(f"| {k} | **{fmt_v}** |")
        else:
            sections.append(f"| {k} | {fmt_v} |")

    return "\n".join(sections)


def build_career_section(career_data):
    """构建职业发展画像"""
    c = career_data
    companies_str = "、".join(c.get("companies", [])) if c.get("companies") else "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团"
    experience = c.get("experience", "~9年（爱博精电 6年 + 新华三 3年）")
    role = "嵌入式开发工程师"  # 固定角色
    skills = c.get("skills", "")
    core = c.get("core_abilities", "")
    focus = c.get("focus", "")
    location = c.get("location", "北京，优先海淀/昌平")
    job_search = c.get("job_search", "已约 1 年，面试过 九号/ISHO/思朗")
    salary = c.get("salary", "50-70W总包")

    return f"""## 职业发展画像

| 维度 | 内容 |
|------|------|
| 当前公司 | 新华三 |
| 当前角色 | {role} |
| 经验 | **{experience}** |
| 技能栈 | {skills} |
| 核心能力 | {core} |
| 行业聚焦 | {focus} |
| 地点约束 | **{location}** |
| 目标薪资 | {salary} |
| 求职状态 | {job_search} |
| 面试方法论 | 工程叙事四层结构: 本质→实践→踩坑→思考 |
| 目标公司 | {companies_str} |"""


def build_family_section(data, report_text, prev_archive_text):
    """
    构建家庭与保险部分
    优先从上一份归档继承静态信息，从 holdings.yaml 更新资产负债
    """
    family = {}
    insurance = {}
    a8_plan = {}

    # 1. 从上一份归档继承家庭/保险信息
    if prev_archive_text:
        sec_family = extract_section(prev_archive_text, "家庭与保险")
        lines = sec_family.split("\n")
        in_table = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and "|----" not in stripped:
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 2:
                    k = cells[0]
                    v = cells[1]
                    if k == "居住地":
                        family["location"] = v
                    elif k == "户籍":
                        family["hukou"] = v
                    elif k == "子女":
                        family["children"] = v
                    elif k == "配偶":
                        family["spouse"] = v
                    elif k == "房产":
                        family["house"] = v
                    elif k == "房贷商贷":
                        family["mortgage_commercial"] = v
                    elif k == "房贷公积金":
                        family["mortgage_fund"] = v
                    elif k.startswith("hanwei_") or k.startswith("xueyan_"):
                        insurance[k] = v

        # 从上一份归档继承 A8 计划
        sec_a8 = extract_section(prev_archive_text, "A8计划进度")
        for line in sec_a8.split("\n"):
            stripped = line.strip()
            if stripped.startswith("|") and "|----" not in stripped:
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 2:
                    a8_plan[cells[0]] = cells[1]

    # 2. 从 holdings.yaml 更新负债
    for l in data.get("liabilities", []):
        name = l.get("name", "")
        amt = l.get("amount_cny", 0)
        if "商贷" in name:
            family["mortgage_commercial"] = f"¥{amt:,}"
        elif "公积金" in name:
            family["mortgage_fund"] = f"¥{amt:,}"

    # 3. 从 fixed_assets 更新房产
    for fa in data.get("fixed_assets", []):
        name = fa.get("name", "")
        if "住宅" in name:
            val = fa.get('value_cny', 0)
            family["house"] = f"北京海淀住宅 ¥{val // 10000}W (购入2025年底)" if val >= 10000 else f"北京海淀住宅 ¥{val:,} (购入2025年底)"

    family_str = f"""## 家庭与保险

| 项目 | 内容 |
|------|------|
| 居住地 | {family.get("location", "北京")} |
| 户籍 | {family.get("hukou", "非京籍 (内蒙古)")} |
| 子女 | {family.get("children", "有孩子 (在京上学)")} |
| 配偶 | {family.get("spouse", "已婚 (薛燕)")} |
| 房产 | {family.get("house", "北京海淀住宅 ¥320W (购入2025年底)")} |
| 房贷商贷 | {family.get("mortgage_commercial", "¥400,000")} |
| 房贷公积金 | {family.get("mortgage_fund", "¥1,400,000")} |
| hanwei_zhongji | {insurance.get("hanwei_zhongji", "达尔文50W (¥6,960/年, 2026-06-15生效)")} |
| hanwei_dingshou | {insurance.get("hanwei_dingshou", "待配置 (目标200W保额)")} |
| xueyan_zhongji | {insurance.get("xueyan_zhongji", "待配置 (目标30-50W保额)")} |"""

    # A8 计划
    if not a8_plan:
        a8_plan = {
            "目标": "1000万人民币 (2026-2028)",
            "当前净资产": "¥1,334,174 (13.3%)",
            "BTC目标": "2.32个 (当前0.12980465, 进度5.6%)",
            "策略": "MA120趋势 + 月度定投¥16,700 + 港股打新",
            "当前状态": "数据来自报告自动解析",
        }

    a8_str = f"""## A8计划进度

| 指标 | 进度 |
|------|------|
| 目标 | {a8_plan.get("目标", "1000万人民币 (2026-2028)")} |
| 当前净资产 | {a8_plan.get("当前净资产", "—")} |
| BTC目标 | {a8_plan.get("BTC目标", "—")} |
| 策略 | {a8_plan.get("策略", "MA120趋势 + 月度定投¥16,700 + 港股打新")} |
| 当前状态 | {a8_plan.get("当前状态", "数据自动解析")} |"""

    return family_str, a8_str


def build_changelog(today_str, report_name, career_file_path):
    """构建本次更新变更记录"""
    return f"""## 本次更新变更记录

| 变更项 | 旧值 | 新值 | 说明 |
|--------|------|------|------|
| profile.last_sync | — | {today_str} | 每日自动归档 |
| 数据源 | holdings.yaml + 最新报告 | {report_name} | 更新至最新报告 |
| 职业档案 | 无变更 | {os.path.basename(career_file_path)} | 无变更 |"""


# ======================================================================
# 4. 主流程
# ======================================================================

def main():
    today = datetime.date.today()
    today_str = today.strftime("%Y%m%d")
    today_human = today.strftime("%Y-%m-%d")

    log.info(f"开始每日个人画像归档: {today_human}")

    # ── 1. 读取数据 ──
    holdings_data = load_holdings()
    if not holdings_data:
        log.error("holdings.yaml 读取失败，跳过本次归档")
        return 1

    report_path = find_latest_report()
    if not report_path:
        log.error("未找到最新报告，跳过本次归档")
        return 1

    report_text = load_report(report_path)
    if not report_text:
        log.error("报告读取失败，跳过本次归档")
        return 1

    career_text = load_career_profile()
    if not career_text:
        log.warning("职业档案读取失败，使用默认值")

    prev_archive = load_previous_archive()

    # ── 2. 解析数据 ──
    report_prices = parse_report_prices(report_text) if report_text else {}
    report_summary = parse_report_summary(report_text) if report_text else {}
    report_metrics = parse_report_metrics(report_text) if report_text else {}

    portfolio = parse_holdings_for_portfolio(holdings_data)
    career_info = parse_career_from_md(career_text) if career_text else {}

    # ── 3. 构建内容 ──
    portfolio_section = build_portfolio_section(portfolio, report_prices, report_summary, report_metrics)
    career_section = build_career_section(career_info)
    family_section, a8_section = build_family_section(holdings_data, report_text, prev_archive)
    report_name = get_report_name(report_path)
    changelog = build_changelog(today_human, report_name, str(CAREER_PATH))

    content = f"""# 个人画像归档 - {today_human}

{portfolio_section}

{career_section}

{family_section}

{a8_section}

{changelog}
"""

    # ── 4. 写入两份归档 ──
    output_paths = [OUTPUT_HOUR, OUTPUT_DAY]
    written = 0
    for out_dir in output_paths:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"profile_{today_str}.md"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            log.info(f"已写入: {out_path}")
            written += 1
        except IOError as e:
            log.error(f"写入失败: {out_path} — {e}")

    if written == 2:
        log.info(f"个人画像归档完成: {today_human}")
        return 0
    else:
        log.warning(f"归档写入不完整: 成功 {written}/2")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log.error(f"归档脚本异常: {e}")
        log.error(traceback.format_exc())
        sys.exit(1)