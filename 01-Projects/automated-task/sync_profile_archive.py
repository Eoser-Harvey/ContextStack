"""
每日个人画像归档 — 自动读取最新持仓/职业档案/投资报告，生成 profile_archive 摘要

用法:
  python sync_profile_archive.py

输出:
  hour-push: 01-Projects/automated-task/0.trae-feishu-push-hour/profile_archive/profile_YYYYMMDD.md
  day-push:  01-Projects/automated-task/1.trae-feishu-push-day/profile_archive/profile_YYYYMMDD.md

设计说明:
  - profile_loader.py 自动从 archive 按日期取最新文件
  - 更新 archive 即自动生效，无需修改 config 或代码
  - 价格数据来自最新月度投资报告（含实时快照）
"""

import os
import re
import glob
import yaml
from datetime import datetime

# ======================================================================
# 路径常量
# ======================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.join(BASE_DIR, "01-Projects", "automated-task")

HOLDINGS_PATH = os.path.join(BASE_DIR, "01-Projects", "family-hub", "research", "portfolio", "holdings.yaml")
REPORTS_DIR = os.path.join(BASE_DIR, "01-Projects", "family-hub", "research", "portfolio", "reports")
CAREER_PATH = os.path.join(
    BASE_DIR, "02-Knowledge", "career-development", "career-strategy",
    "个人职业发展分析-端侧AI企业定制攻略.md"
)

HOUR_ARCHIVE_DIR = os.path.join(PROJECT_DIR, "0.trae-feishu-push-hour", "profile_archive")
DAY_ARCHIVE_DIR = os.path.join(PROJECT_DIR, "1.trae-feishu-push-day", "profile_archive")

TODAY = datetime.now().strftime("%Y%m%d")
TODAY_LABEL = datetime.now().strftime("%Y-%m-%d")
META_USD_CNY = 6.729
META_HKD_CNY = 0.857


# ======================================================================
# 日志
# ======================================================================

def log_error(msg):
    print(f"[ERROR] sync_profile_archive | {msg}")

def log_info(msg):
    print(f"[INFO] sync_profile_archive | {msg}")


# ======================================================================
# 1. 读取投资持仓
# ======================================================================

def load_holdings(path):
    if not os.path.isfile(path):
        log_error(f"holdings.yaml 不存在: {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        log_error("holdings.yaml 为空")
        return {}

    return data


# ======================================================================
# 2. 读取最新投资报告
# ======================================================================

def load_latest_report(reports_dir):
    if not os.path.isdir(reports_dir):
        log_error(f"报告目录不存在: {reports_dir}")
        return ""

    files = sorted(glob.glob(os.path.join(reports_dir, "*.md")), reverse=True)
    if not files:
        log_error(f"报告目录下无 .md 文件: {reports_dir}")
        return ""

    path = files[0]
    log_info(f"读取最新报告: {os.path.basename(path)}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ======================================================================
# 3. 从报告解析表格数据
# ======================================================================

def _parse_report_table(report_content, section_heading, col_count=None):
    """
    从 markdown 表格行中提取数据，按 section heading 定位
    返回 [{col1: val, col2: val, ...}] 字典列表
    """
    lines = report_content.split("\n")
    in_section = False
    in_table = False
    rows = []
    header = []

    for line in lines:
        stripped = line.strip()

        # 检测 section 标题 (支持 "## 一、资产总览" 和 "## 资产总览（含XXX）" 等)
        if not in_section:
            # 行内包含目标章节名且是二级标题
            if stripped.startswith("## ") and section_heading in stripped:
                in_section = True
                continue
            # 也支持 "### " 级别
            if stripped.startswith("##") and section_heading in stripped:
                in_section = True
                continue

        if not in_section:
            continue

        # 检测下一个 section 标题
        if stripped.startswith("#") and not stripped.startswith("###"):
            break

        # 跳过空行
        if not stripped:
            in_table = False
            continue

        # 表格行
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]

            # 跳过分隔行
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                continue

            if not in_table:
                # 第一行是表头
                header = cells
                in_table = True
                continue

            if col_count and len(cells) != col_count:
                continue

            row = {}
            for i, h in enumerate(header):
                val = cells[i] if i < len(cells) else ""
                row[h] = val
            rows.append(row)

    return rows, header


def _parse_overview(report_content):
    """解析 资产总览 表 → {label: value}"""
    rows, _ = _parse_report_table(report_content, "资产总览", col_count=3)
    result = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) >= 2:
            label = row[keys[0]].strip("*").replace("**", "")
            val = row[keys[1]].strip("*").replace("**", "")
            result[label] = val
    return result


def _parse_investment_detail(report_content):
    """解析 投资资产明细 表 → {name: {price, mkt_value, ...}}"""
    rows, header = _parse_report_table(report_content, "投资资产明细")
    result = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) < 3:
            continue
        name = row[keys[0]].strip("*").replace("**", "")
        price = row.get("当前单价", row.get(keys[2], "$—"))
        mkt_value = ""
        for k in keys:
            if "市值" in k or "市值(CNY)" in k:
                mkt_value = row[k]
                break
        storage = ""
        for k in keys:
            if "存放" in k:
                storage = row.get(k, "")
                break

        # 提取纯价格数字 — 保留原始货币符号
        price_clean = price
        if "$" not in price and "HK$" not in price and "¥" not in price and "￥" not in price:
            m = re.search(r'([\d,]+\.?\d*)', price)
            if m:
                price_clean = f"${m.group(1)}"
        # 已有货币符号则保持原样

        result[name] = {
            "price": price_clean,
            "mkt_value": mkt_value,
        }

        # 按标的分类存储位置
        for k in keys:
            if "存放" in k:
                result[name]["storage"] = row.get(k, "")

    return result


def _parse_asset_summary(report_content):
    """解析 按资产统计 表 → {asset: {qty, avg_price, mkt_value, pct}}"""
    rows, _ = _parse_report_table(report_content, "按资产统计")
    result = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) < 2:
            continue
        name = row[keys[0]].strip("*").replace("**", "")
        pct = ""
        for k in keys:
            if "占投资比" in k:
                pct = row.get(k, "")
                break
        mkt_val = ""
        for k in keys:
            if "市值" in k:
                mkt_val = row.get(k, "")
                break
        result[name] = {
            "pct": pct,
            "mkt_value": mkt_val,
        }
    return result


# ======================================================================
# 4. 读取职业发展档案
# ======================================================================

def load_career_profile(path):
    if not os.path.isfile(path):
        log_error(f"职业发展档案不存在: {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    career = {}
    for line in content.split("\n"):
        line_s = line.strip()
        if line_s.startswith("|") and line_s.endswith("|"):
            cells = [c.strip() for c in line_s.split("|")[1:-1]]
            if len(cells) == 2:
                key, val = cells
                val_clean = val.replace("**", "")
                if "总经验" in key:
                    career["experience"] = val_clean
                elif "技能栈" in key:
                    career["skills"] = val_clean
                elif "核心能力" in key:
                    career["core_abilities"] = val_clean
                elif "行业聚焦" in key:
                    career["focus"] = val_clean
                elif "地点约束" in key:
                    career["location"] = val_clean
                elif "求职" in key:
                    career["job_search"] = val_clean

    m = re.search(r'薪资预期[：:].*?(\d+[Ww]-\d+[Ww]总包|\d+-\d+W)', content)
    if m:
        career["salary"] = m.group(1)

    career["role"] = "嵌入式开发工程师"

    # 目标公司
    target_companies = []
    in_target = False
    for line in content.split("\n"):
        if "目标公司" in line and ("海淀" in line or "昌平" in line or "北京" in line):
            in_target = True
            continue
        if in_target:
            if line.strip().startswith("|") and "|" in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 2:
                    company = cells[0]
                    if company and company not in ("公司", "公司名称"):
                        target_companies.append(company)
            elif line.strip().startswith("---"):
                continue
            elif not line.strip().startswith("|"):
                break
    if target_companies:
        career["target_companies"] = target_companies

    if "工程叙事" in content:
        career["interview_method"] = "工程叙事四层结构: 本质→实践→踩坑→思考"

    return career


# ======================================================================
# 5. 生成归档 Markdown
# ======================================================================

def build_profile(holdings, report_content, career):
    date_label = TODAY_LABEL

    # 从报告解析表格
    overview = _parse_overview(report_content)
    detail = _parse_investment_detail(report_content)
    summary = _parse_asset_summary(report_content)

    # 关键指标
    total_assets = overview.get("总资产", "—")
    net_assets = overview.get("净资产", "—")
    investment_assets = overview.get("投资总资产", "—")

    # ----- 持仓数据 -----
    h = holdings.get("holdings", [])
    cash_data = holdings.get("cash", [])
    liabilities = holdings.get("liabilities", [])
    fixed = holdings.get("fixed_assets", [])

    crypto_items = [x for x in h if x.get("category") in ("crypto",)]
    us_stock_items = [x for x in h if x.get("category") in ("us_stock", "us_stock_tokenized")]
    hk_stock_items = [x for x in h if x.get("category") == "hk_stock"]
    a_stock_items = [x for x in h if x.get("category") == "a_stock"]
    ts_items = [x for x in h if x.get("category") == "ts_time_token"]

    crcl_items = [x for x in h if x.get("symbol") == "CRCL"]
    crcl_total_qty = sum(x.get("quantity", 0) for x in crcl_items)

    # 现金
    cash_family = cash_hk = cash_usdt = cash_wst = ""
    for c in cash_data:
        n = c.get("name", "")
        if "备用金" in n or "活期" in n or "货基" in n:
            cash_family = c.get("amount_cny", "")
        elif "HK" in n or "打新" in n:
            cash_hk = c.get("amount_hkd", "")
        elif "USDT" in n or "币安" in n:
            cash_usdt = c.get("amount_usd", "")
        elif "华盛" in n:
            cash_wst = c.get("amount_usd", "")

    # 负债
    mortgage_commercial = mortgage_fund = credit_card = ""
    for l in liabilities:
        n = l.get("name", "")
        if "商贷" in n:
            mortgage_commercial = "¥{:,.0f}".format(l.get("amount_cny", 0))
        elif "公积金" in n:
            mortgage_fund = "¥{:,.0f}".format(l.get("amount_cny", 0))
        elif "信用卡" in n:
            credit_card = "¥{:,.0f}".format(l.get("amount_cny", 0))

    house_value = ""
    for fa in fixed:
        if "北京" in fa.get("name", ""):
            house_value = "¥{:,.0f}".format(fa.get("value_cny", 0))

    # ----- 职业信息 -----
    exp = career.get("experience", "~9年")
    skills = career.get("skills", "C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM")
    core = career.get("core_abilities", "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构")
    focus = career.get("focus", "工业嵌入式、通信设备底层，非消费电子")
    location = career.get("location", "北京，优先海淀/昌平（已在海淀买房）")
    salary = career.get("salary", "50-70W总包")
    job_search = career.get("job_search", "已约 1 年，MS过 九号/ISHO/思朗")
    targets_str = "、".join(career.get("target_companies", ["小米", "地平线", "寒武纪", "百度", "字节跳动", "联想", "滴滴", "三一重工", "北汽新能源", "京东方", "理想汽车", "石头科技", "美团"]))
    interview_method = career.get("interview_method", "工程叙事四层结构: 本质→实践→踩坑→思考")

    # 保险 & 家庭
    hukou = "非京籍 (内蒙古)"
    children = "有孩子 (在京上学)"
    spouse = "已婚 (薛燕)"
    hanwei_zhongji = "达尔文50W (¥6,960/年, 2026-06-15生效)"
    hanwei_dingshou = "待配置 (目标200W保额)"
    xueyan_zhongji = "待配置 (目标30-50W保额)"

    # ----- A8 -----
    a8_current = net_assets if net_assets and net_assets != "—" else "¥1,334,174"
    try:
        a8_pct = float(a8_current.replace("¥", "").replace("￥", "").replace(",", "")) / 10_000_000 * 100
        a8_pct_str = f"{a8_pct:.1f}%"
    except:
        a8_pct_str = "13.3%"

    btc_qty = 0
    for item in h:
        if item.get("symbol") == "BTC":
            btc_qty = item.get("quantity", 0)
    btc_pct = btc_qty / 2.32 * 100 if btc_qty else 0

    # CRCL集中度 — 从 按资产统计 表提取
    crcl_concentration = "—"
    for name, info in summary.items():
        if "CRCL" in name.upper() or "Circle" in name:
            crcl_concentration = info.get("pct", "—")
            if crcl_concentration and crcl_concentration != "—":
                crcl_concentration = crcl_concentration.strip() + " ⚠️"
            break
    if crcl_concentration == "—" or crcl_concentration == " ⚠️":
        crcl_concentration = "≈70% ⚠️"

    # 构建 changelog
    latest_report_basename = ""
    report_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.md")), reverse=True)
    if report_files:
        latest_report_basename = os.path.basename(report_files[0])

    changelog = [
        ("profile.last_sync", "—", TODAY_LABEL, "每日自动归档"),
        ("数据源", "—", latest_report_basename or "—", "更新至最新报告"),
        ("职业档案", "无变更", "个人职业发展分析-端侧AI企业定制攻略.md", "无变更"),
    ]

    # ==================================================================
    # 构建 Markdown
    # ==================================================================
    lines = []
    lines.append(f"# 个人画像归档 - {TODAY_LABEL}")
    lines.append("")
    lines.append("## 投资持仓概览")
    lines.append("")

    # --- 加密货币 ---
    crypto_lines = ["### 加密货币", "| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |",
                    "|------|------|------------|-----------|------|"]
    for item in crypto_items:
        symbol = item.get("symbol", "")
        name_orig = item.get("name", "")
        if symbol == "BTC":
            label = "BTC(链上)"
        elif symbol == "MILADY":
            label = "MILADY NFT(链上)"
        else:
            label = name_orig
        qty = item.get("quantity", 0)
        unit = item.get("unit", "")
        qty_str = f"{qty:,}{' ' + unit if unit else ''}" if qty else "0"
        storage = item.get("storage", "")
        # 从报告 detail 取价格
        price_str = "$—"
        mkt_val = "—"
        for dname, dinfo in detail.items():
            if item.get("symbol", "").lower() in dname.lower() or item.get("name", "").lower() in dname.lower():
                price_str = dinfo.get("price", "$—")
                mkt_val = dinfo.get("mkt_value", "—")
                break
        crypto_lines.append(f"| {label} | {qty_str} | {price_str} | {mkt_val} | {storage} |")

    # USDT 行
    if cash_usdt:
        usdt_val = float(cash_usdt) if isinstance(cash_usdt, (int, float)) else 0
        crypto_lines.append(f"| USDT(币安) | ${usdt_val:,.0f} | $1.00 | — | 币安 |")
    lines.extend(crypto_lines)
    lines.append("")

    # --- 美股 ---
    us_lines = ["### 美股", "| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |",
                "|------|------|------------|-----------|------|"]

    # CRCL 合计（从 detail 取价格）
    crcl_price = "$—"
    crcl_mkt = "—"
    for dname, dinfo in detail.items():
        if "CRCL" in dname.upper() or "Circle" in dname:
            if "合计" not in dname:
                crcl_price = dinfo.get("price", "$—")
                crcl_mkt = dinfo.get("mkt_value", "—")
            break
    us_lines.append(f"| Circle(CRCL合计) | {crcl_total_qty:,.1f} | {crcl_price} | — | 分散多账户 |")

    for item in us_stock_items:
        name = item.get("name", "")
        qty = item.get("quantity", 0)
        qty_str = f"{qty:,.1f}" if qty == int(qty) else f"{qty:,}"
        storage = item.get("storage", "")
        # 从 detail 取价格
        us_price = "$—"
        for dname, dinfo in detail.items():
            if item.get("name", "").lower() in dname.lower() or item.get("symbol", "").lower() in dname.lower():
                us_price = dinfo.get("price", "$—")
                break
        us_lines.append(f"| {name} | {qty_str} | {us_price} | — | {storage} |")
    lines.extend(us_lines)
    lines.append("")

    # --- 港股 ---
    hk_lines = ["### 港股", "| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |",
                "|------|------|-------|-----------|------|"]
    for item in hk_stock_items:
        name = item.get("name", "")
        qty = item.get("quantity", 0)
        storage = item.get("storage", "")
        hk_price = "—"
        for dname, dinfo in detail.items():
            if item.get("name", "").lower() in dname.lower() or item.get("symbol", "").lower() in dname.lower():
                hk_price = dinfo.get("price", "—")
                break
        hk_lines.append(f"| {name} | {qty} | {hk_price} | — | {storage} |")
    lines.extend(hk_lines)
    lines.append("")

    # --- A股 ---
    a_lines = ["### A股", "| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |",
               "|------|------|-------|-----------|------|"]
    for item in a_stock_items:
        name = item.get("name", "")
        qty = item.get("quantity", 0)
        storage = item.get("storage", "")
        a_price = "—"
        for dname, dinfo in detail.items():
            if item.get("name", "").lower() in dname.lower() or item.get("symbol", "").lower() in dname.lower():
                a_price = dinfo.get("price", "—")
                break
        a_lines.append(f"| {name} | {qty:,} | {a_price} | — | {storage} |")
    lines.extend(a_lines)
    lines.append("")

    # --- TS时间代币 ---
    ts_lines = ["### TS时间代币", "| 标的 | 数量 | 市值(CNY) |",
                "|------|------|-----------|"]
    for item in ts_items:
        name = item.get("name", "")
        qty = item.get("quantity", 0)
        unit = item.get("unit", "")
        qty_str = f"{qty:,}{unit}" if unit else str(qty)
        ts_mkt = "—"
        for dname, dinfo in detail.items():
            if item.get("name", "").lower() in dname.lower():
                ts_mkt = dinfo.get("mkt_value", "—")
                break
        ts_lines.append(f"| {name} | {qty_str} | {ts_mkt} |")
    lines.extend(ts_lines)
    lines.append("")

    # --- 关键指标 ---
    usdt_fmt = ""
    if cash_usdt:
        usdt_val = float(cash_usdt) if isinstance(cash_usdt, (int, float)) else 0
        usdt_fmt = f"${usdt_val:,.0f} (≈¥{usdt_val * META_USD_CNY:,.0f})"

    wst_fmt = ""
    if cash_wst:
        wst_val = float(cash_wst) if isinstance(cash_wst, (int, float)) else 0
        wst_fmt = f"${wst_val:,.0f} (≈¥{wst_val * META_USD_CNY:,.0f})"

    cash_family_fmt = f"¥{int(cash_family):,}" if cash_family else "—"
    cash_hk_fmt = ""
    if cash_hk:
        hk_val = float(cash_hk) if isinstance(cash_hk, (int, float)) else 0
        cash_hk_fmt = f"HK${hk_val:,.0f} (≈¥{hk_val * META_HKD_CNY:,.0f})"

    # BTC占投资比 — 从 summary 表取
    btc_invest_pct = "—"
    for name, info in summary.items():
        if "BTC" in name.upper() or "比特币" in name:
            btc_invest_pct = info.get("pct", "—")
            break

    metrics_lines = [
        "### 关键指标",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 总资产 | **{total_assets}** |",
        f"| 净资产 | **{net_assets}** |",
        f"| 投资总资产 | **{investment_assets}** |",
        f"| 家庭备用金 | {cash_family_fmt} |",
        f"| HK打新资金 | {cash_hk_fmt} |",
        f"| USDT余额 | {usdt_fmt} |",
        f"| 华盛通现金 | {wst_fmt} |",
        f"| 信用卡负债 | {credit_card} |",
        f"| BTC占投资比 | {btc_invest_pct} |",
        f"| CRCL集中度 | {crcl_concentration} |",
        f"| 房贷总额 | {mortgage_commercial}+{mortgage_fund} |",
    ]
    lines.extend(metrics_lines)
    lines.append("")

    # --- 职业发展画像 ---
    career_lines = [
        "## 职业发展画像", "",
        "| 维度 | 内容 |",
        "|------|------|",
        f"| 当前公司 | 新华三 |",
        f"| 当前角色 | 嵌入式开发工程师 |",
        f"| 经验 | ~{exp}" if not exp.startswith("~") else f"| 经验 | {exp} |",
        f"| 技能栈 | {skills} |",
        f"| 核心能力 | {core} |",
        f"| 行业聚焦 | {focus} |",
        f"| 地点约束 | {location} |",
        f"| 目标薪资 | {salary} |",
        f"| 求职状态 | {job_search} |",
        f"| 面试方法论 | {interview_method} |",
        f"| 目标公司 | {targets_str} |",
    ]
    lines.extend(career_lines)
    lines.append("")

    # --- 家庭与保险 ---
    family_lines = [
        "## 家庭与保险", "",
        "| 项目 | 内容 |",
        "|------|------|",
        "| 居住地 | 北京 |",
        f"| 户籍 | {hukou} |",
        f"| 子女 | {children} |",
        f"| 配偶 | {spouse} |",
        f"| 房产 | 北京海淀住宅 {house_value} (购入2025年底) |" if house_value else "| 房产 | 北京海淀住宅 ¥3,200,000 (购入2025年底) |",
        f"| 房贷商贷 | {mortgage_commercial} |",
        f"| 房贷公积金 | {mortgage_fund} |",
        f"| hanwei_zhongji | {hanwei_zhongji} |",
        f"| hanwei_dingshou | {hanwei_dingshou} |",
        f"| xueyan_zhongji | {xueyan_zhongji} |",
    ]
    lines.extend(family_lines)
    lines.append("")

    # --- A8计划进度 ---
    a8_lines = [
        "## A8计划进度", "",
        "| 指标 | 进度 |",
        "|------|------|",
        f"| 目标 | 1000万人民币 (2026-2028) |",
        f"| 当前净资产 | **{a8_current}** ({a8_pct_str}) |",
        f"| BTC目标 | 2.32个 (当前{btc_qty:,.8f}, 进度{btc_pct:.1f}%) |",
        f"| CRCL自持 | {crcl_total_qty:,.1f}股 (目标占比≤20%, 当前{crcl_concentration}) |",
        "| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |",
        "| 当前状态 | 数据来自报告自动解析 |",
    ]
    lines.extend(a8_lines)
    lines.append("")

    # --- 变更记录 ---
    changelog_lines = [
        "## 本次更新变更记录", "",
        "| 变更项 | 旧值 | 新值 | 说明 |",
        "|--------|------|------|------|",
    ]
    for item in changelog:
        changelog_lines.append(f"| {item[0]} | {item[1]} | {item[2]} | {item[3]} |")
    lines.extend(changelog_lines)

    return "\n".join(lines)


# ======================================================================
# 6. 写出归档
# ======================================================================

def write_archive(content, archive_dir):
    os.makedirs(archive_dir, exist_ok=True)
    filename = f"profile_{TODAY}.md"
    path = os.path.join(archive_dir, filename)

    old_content = ""
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                old_content = f.read()
        except:
            pass

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    if old_content:
        log_info(f"更新 {filename}（覆盖旧文件）")
    else:
        log_info(f"新建 {filename}")


# ======================================================================
# 7. 主流程
# ======================================================================

def main():
    log_info("=== 开始每日个人画像归档 ===")

    holdings = load_holdings(HOLDINGS_PATH)
    if not holdings:
        log_error("holdings 读取失败，终止")
        return

    report_content = load_latest_report(REPORTS_DIR)
    career = load_career_profile(CAREER_PATH)

    profile_md = build_profile(holdings, report_content, career)

    write_archive(profile_md, HOUR_ARCHIVE_DIR)
    write_archive(profile_md, DAY_ARCHIVE_DIR)

    log_info("=== 归档完成 ===")


if __name__ == "__main__":
    main()