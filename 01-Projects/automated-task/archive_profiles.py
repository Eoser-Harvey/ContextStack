"""
每日0点个人画像归档脚本

读取 holdings.yaml（最新投资持仓）和职业发展档案，
生成两份归档摘要到 hour 和 day 两个 profile_archive 目录。

profile_loader.py 自动从 archive 加载最新档案，
analyzer.py / send_daily_ai_news.py / push_lark.py 通过 profile_loader 实时读取，
更新 archive 即自动生效，无需修改任何代码。

用法：
  python archive_profiles.py

定时任务（Windows 任务计划程序）：
  触发器：每天 00:00
  操作：python E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\archive_profiles.py
"""

import os
import re
import sys
import yaml
from datetime import date
from collections import defaultdict

# ======================================================================
# 配置
# ======================================================================

ROOT = r"E:\ProjectGroup\AI\ContextStack"

PATHS = {
    "holdings": os.path.join(ROOT, "01-Projects", "family-hub", "research", "portfolio", "holdings.yaml"),
    "career": os.path.join(ROOT, "02-Knowledge", "career-development", "career-strategy", "个人职业发展分析-端侧AI企业定制攻略.md"),
    "reports_dir": os.path.join(ROOT, "01-Projects", "family-hub", "research", "portfolio", "reports"),
    "archive_hour": os.path.join(ROOT, "01-Projects", "automated-task", "0.trae-feishu-push-hour", "profile_archive"),
    "archive_day": os.path.join(ROOT, "01-Projects", "automated-task", "1.trae-feishu-push-day", "profile_archive"),
    "log": os.path.join(ROOT, "01-Projects", "automated-task", "archive_profiles.log"),
}

TODAY = date.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_TAG = TODAY.strftime("%Y%m%d")

# 汇率（从 holdings.yaml meta 动态获取，此处为默认值）
USD_CNY = 6.729
HKD_CNY = 0.857


# ======================================================================
# 日志
# ======================================================================

def log(msg, level="INFO"):
    timestamp = DATE_STR
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(PATHS["log"]), exist_ok=True)
        with open(PATHS["log"], "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ======================================================================
# 数据读取
# ======================================================================

def load_holdings():
    """读取 holdings.yaml，返回完整 dict。"""
    path = PATHS["holdings"]
    if not os.path.isfile(path):
        log(f"holdings.yaml 不存在: {path}", "ERROR")
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 提取汇率
    global USD_CNY, HKD_CNY
    if data and "meta" in data:
        meta = data["meta"]
        USD_CNY = meta.get("usd_cny", USD_CNY)
        HKD_CNY = meta.get("hkd_cny", HKD_CNY)

    log(f"已加载 holdings.yaml（last_updated: {data.get('meta', {}).get('last_updated', 'unknown')}）")
    return data


def load_previous_archive(archive_dir):
    """读取最新一份已经存在的归档档案，用于继承上期价格。"""
    if not os.path.isdir(archive_dir):
        return None
    files = sorted(
        [f for f in os.listdir(archive_dir) if f.startswith("profile_") and f.endswith(".md")],
        reverse=True,
    )
    if not files:
        return None
    path = os.path.join(archive_dir, files[0])
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_previous_prices(previous_md):
    """从上一期归档中提取各标的的 '当前价' 信息，返回 {标的名: 价格文本}。"""
    prices = {}
    if not previous_md:
        return prices

    # 扫描所有表格行：| 标的 | ... | 当前价 | ... |
    for line in previous_md.split("\n"):
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        label = cells[0]
        # 对于加密货币/美股表：| 标的 | 数量 | 当前价 | 市值 | 存放 |
        # 对于港股：| 标的 | 数量 | 当前价 | 市值 | 存放 |
        # 对于 TS：| 标的 | 数量 | 市值 |
        # 对于关键指标：| 指标 | 数值 |
        if len(cells) >= 3:
            price_cell = cells[2]  # 第三列是"当前价"
            if price_cell and price_cell != "当前价(USD)" and price_cell != "当前价":
                prices[label] = price_cell
    return prices


def load_career():
    """读取职业发展档案，返回关键字段 dict。"""
    path = PATHS["career"]
    if not os.path.isfile(path):
        log(f"职业发展档案不存在: {path}", "WARN")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 从 Markdown 表格中提取关键字段
    career = {}
    in_table = False
    for line in content.split("\n"):
        line_stripped = line.strip()
        if line_stripped.startswith("|") and line_stripped.endswith("|"):
            cells = [c.strip() for c in line_stripped.split("|")[1:-1]]
            if len(cells) == 2:
                key, val = cells[0].strip(), cells[1].strip()
                career[key] = val

    log(f"已加载职业发展档案")
    return career


def get_latest_report_name():
    """获取最近月度报告的文件名。"""
    d = PATHS["reports_dir"]
    if not os.path.isdir(d):
        return None
    files = sorted(
        [f for f in os.listdir(d) if f.endswith(".md")],
        key=lambda x: os.path.getmtime(os.path.join(d, x)),
        reverse=True,
    )
    return files[0] if files else None


# ======================================================================
# 数值计算辅助
# ======================================================================

def fmt_usd(val):
    if val is None:
        return "$0.00"
    return f"${val:,.2f}"


def fmt_cny(val):
    if val is None:
        return "¥0"
    return f"¥{val:,.0f}"


def fmt_hkd(val):
    if val is None:
        return "HK$0"
    return f"HK${val:,.0f}"


# ======================================================================
# 核心：生成归档内容
# ======================================================================

def build_profile_md(holdings_data, career_data, previous_prices, report_name):
    """
    从原始数据构建个人画像 Markdown 内容。
    返回符合 profile_loader.py 解析格式的纯文本。
    """
    holdings = holdings_data.get("holdings", [])
    liabilities = holdings_data.get("liabilities", [])
    cash_items = holdings_data.get("cash", [])
    fixed_assets = holdings_data.get("fixed_assets", [])
    custody = holdings_data.get("custody", [])

    # ── 按类别分组持仓 ──
    crypto_items = [h for h in holdings if h.get("category") == "crypto"]
    us_stock_items = [h for h in holdings if h.get("category") in ("us_stock", "us_stock_tokenized")]
    hk_stock_items = [h for h in holdings if h.get("category") == "hk_stock"]
    a_stock_items = [h for h in holdings if h.get("category") == "a_stock"]
    ts_items = [h for h in holdings if h.get("category") == "ts_time_token"]

    # ── CRCL 合计 ──
    crcl_all = [h for h in holdings if h.get("symbol") == "CRCL"]
    crcl_total_qty = sum(h["quantity"] for h in crcl_all)
    crcl_yb = next((h for h in crcl_all if "燕币安" in h.get("name", "")), None)
    crcl_hb = next((h for h in crcl_all if "韩伟币安" in h.get("name", "")), None)
    crcl_cb = next((h for h in crcl_all if "长桥" in h.get("name", "")), None)
    crcl_hst = next((h for h in crcl_all if "华盛通" in h.get("name", "")), None)
    crcl_hf = next((h for h in crcl_all if "韩芳" in h.get("name", "")), None)

    # ── 从上一期继承价格 ──
    def get_price(label, default_price):
        return previous_prices.get(label, fmt_usd(default_price))

    def get_cny_price(label, default_price):
        price_str = previous_prices.get(label, "")
        return price_str if price_str else fmt_cny(default_price)

    # 构造行数据: (label, qty, price_usd, market_value_cny, storage)
    crypto_rows = []
    for h in crypto_items:
        label = h["name"]
        qty = h["quantity"]
        unit = h.get("unit", "")
        qty_str = f"{qty:,.8f}".rstrip("0").rstrip(".") if isinstance(qty, float) else str(qty)
        if unit:
            qty_str += unit
        price = h.get("cost_basis_usd", 0)
        price_str = get_price(label, price)
        # 尝试从 price_str 解析数值用于计算市值
        m = re.search(r'[\d,]+\.?\d*', price_str.replace(",", ""))
        price_num = float(m.group().replace(",", "")) if m else price
        mkt_cny = price_num * qty * USD_CNY
        mkt_str = fmt_cny(mkt_cny)
        storage = h.get("storage", "")
        crypto_rows.append((label, qty_str, price_str, mkt_str, storage))

    us_rows = []
    for h in us_stock_items:
        label = h["name"]
        qty = h["quantity"]
        qty_str = f"{qty:,.4f}".rstrip("0").rstrip(".") if isinstance(qty, float) else str(qty)
        price = h.get("cost_basis_usd", 0)
        price_str = get_price(label, price)
        m = re.search(r'[\d,]+\.?\d*', price_str.replace(",", ""))
        price_num = float(m.group().replace(",", "")) if m else price
        mkt_cny = price_num * qty * USD_CNY
        mkt_str = fmt_cny(mkt_cny)
        storage = h.get("storage", "")
        us_rows.append((label, qty_str, price_str, mkt_str, storage))

    # 插入 CRCL 合计行
    # 计算合计价格（按加权平均 cost_basis）
    if crcl_all:
        total_cost = sum(h["cost_basis_usd"] * h["quantity"] for h in crcl_all if h.get("cost_basis_usd"))
        avg_price = total_cost / crcl_total_qty if crcl_total_qty > 0 else 0
    else:
        avg_price = 0
    crcl_total_price = get_price("Circle(CRCL合计)", avg_price)
    m = re.search(r'[\d,]+\.?\d*', crcl_total_price.replace(",", ""))
    crcl_price_num = float(m.group().replace(",", "")) if m else avg_price
    crcl_total_mkt = fmt_cny(crcl_price_num * crcl_total_qty * USD_CNY)
    us_rows.insert(0, ("Circle(CRCL合计)", f"{crcl_total_qty:,.4f}".rstrip("0").rstrip("."), crcl_total_price, crcl_total_mkt, "分散多账户"))

    hk_rows = []
    for h in hk_stock_items:
        label = h["name"]
        qty = h["quantity"]
        qty_str = f"{qty:,.2f}".rstrip("0").rstrip(".") if isinstance(qty, float) else str(qty)
        cost_hkd = h.get("cost_basis_hkd", 0)
        price_str = get_cny_price(label, cost_hkd * HKD_CNY)
        # 从 price_str 尝试解析数值用于计算市值
        m = re.search(r'[\d,]+\.?\d*', price_str.replace("HK$", "").replace(",", ""))
        price_num = float(m.group().replace(",", "")) if m else cost_hkd
        mkt_cny = price_num * qty * HKD_CNY
        mkt_str = fmt_cny(mkt_cny)
        storage = h.get("storage", "")
        hk_rows.append((label, qty_str, price_str, mkt_str, storage))

    a_rows = []
    for h in a_stock_items:
        label = h["name"]
        qty = h["quantity"]
        qty_str = f"{qty:,.0f}"
        cost_cny = h.get("cost_basis_cny", 0)
        price_str = get_cny_price(label, cost_cny)
        # 从 price_str 尝试解析数值用于计算市值
        m = re.search(r'[\d,]+\.?\d*', price_str.replace("¥", "").replace(",", ""))
        price_num = float(m.group().replace(",", "")) if m else cost_cny
        mkt_cny = price_num * qty
        mkt_str = fmt_cny(mkt_cny)
        storage = h.get("storage", "")
        a_rows.append((label, qty_str, price_str, mkt_str, storage))

    ts_rows = []
    for h in ts_items:
        label = h["name"]
        qty = h["quantity"]
        unit = h.get("unit", "")
        qty_str = f"{qty:,.0f}{unit}" if unit else f"{qty:,.0f}"
        price_manual = h.get("manual_price_usd", 0)
        mkt_cny = price_manual * qty * USD_CNY
        mkt_str = fmt_cny(mkt_cny)
        ts_rows.append((label, qty_str, mkt_str))

    # ── 负债解析（须在市值计算前完成） ──
    mortgage_commercial = 0
    mortgage_fund = 0
    credit_card = 0
    for l in liabilities:
        name = l.get("name", "")
        if "商贷" in name:
            mortgage_commercial = l.get("amount_cny", 0)
        if "公积金" in name:
            mortgage_fund = l.get("amount_cny", 0)
        if "信用卡" in name:
            credit_card = l.get("amount_cny", 0)
    total_mortgage = mortgage_commercial + mortgage_fund

    # 房产
    house_value = 0
    for fa in fixed_assets:
        if "住宅" in fa.get("name", ""):
            house_value = fa.get("value_cny", 0)

    # ── 关键指标 ──
    # 计算各资产市值汇总
    total_crypto_mkt = 0
    for label, qty_str, price_str, mkt_str, _ in crypto_rows:
        m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
        if m:
            total_crypto_mkt += float(m.group())

    total_us_mkt = 0
    for label, qty_str, price_str, mkt_str, _ in us_rows:
        m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
        if m:
            total_us_mkt += float(m.group())

    total_hk_mkt = 0
    for _, _, _, mkt_str, _ in hk_rows:
        m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
        if m:
            total_hk_mkt += float(m.group())

    total_a_mkt = 0
    for _, _, _, mkt_str, _ in a_rows:
        m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
        if m:
            total_a_mkt += float(m.group())

    total_ts_mkt = 0
    for _, _, mkt_str in ts_rows:
        m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
        if m:
            total_ts_mkt += float(m.group())

    investment_total = total_crypto_mkt + total_us_mkt + total_hk_mkt + total_a_mkt + total_ts_mkt

    # 现金
    cash_home = cash_items[0]["amount_cny"] if len(cash_items) > 0 else 0
    cash_hk = cash_items[1]["amount_hkd"] if len(cash_items) > 1 else 0
    cash_hk_cny = cash_hk * HKD_CNY
    cash_usdt = 0
    cash_usdt_note = ""
    for c in cash_items:
        n = c.get("name", "")
        if "USDT" in n:
            cash_usdt = c.get("amount_usd", 0)
            cash_usdt_note = c.get("note", "")
        elif "华盛通现金" in n:
            pass  # handled separately below
    cash_sihuatong = 0
    for c in cash_items:
        if "华盛通现金" in c.get("name", ""):
            cash_sihuatong = c.get("amount_usd", 0)

    cash_invest = cash_usdt * USD_CNY + cash_sihuatong * USD_CNY
    # 总资产 = 投资资产 + 现金（不含房产）
    total_assets = investment_total + cash_home + cash_hk_cny + cash_invest
    # 净资产 = 总资产 - 信用卡负债（房贷不计入投资组合负债）
    net_assets = total_assets - credit_card

    # CRCL 集中度
    crcl_mkt = 0
    for label, qty_str, price_str, mkt_str, _ in us_rows:
        if "CRCL合计" in label or "Circle(" in label:
            m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
            if m:
                crcl_mkt += float(m.group())
    crcl_pct = (crcl_mkt / investment_total * 100) if investment_total > 0 else 0

    # BTC 占比
    btc_mkt = 0
    for label, qty_str, price_str, mkt_str, _ in crypto_rows:
        if "比特币" in label or "BTC" in label:
            m = re.search(r'[\d,]+', mkt_str.replace("¥", "").replace(",", ""))
            if m:
                btc_mkt += float(m.group())
    btc_pct = (btc_mkt / investment_total * 100) if investment_total > 0 else 0

    # 从职业发展档案构建 table
    career_table = {}
    if career_data:
        career_table["当前公司"] = "新华三"
        career_table["当前角色"] = "嵌入式开发工程师"
        career_table["经验"] = career_data.get("总经验", "**~9年**（爱博精电 6年 + 新华三 3年）")
        career_table["技能栈"] = career_data.get("技能栈", "C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM")
        career_table["核心能力"] = career_data.get("S级能力", "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构")
        career_table["行业聚焦"] = career_data.get("行业聚焦", "工业嵌入式、通信设备底层，**非消费电子**")
        career_table["地点约束"] = career_data.get("地点约束", "**北京，优先海淀/昌平**（已在海淀买房）")
        career_table["目标薪资"] = career_data.get("目标薪资", "50-70W总包")
        raw_status = career_data.get("求职周期", "已约 1 年，面试过 九号/ISHO/思朗")
        # 统一 "MS过" → "面试过"
        raw_status = raw_status.replace("MS过", "面试过")
        career_table["求职状态"] = raw_status
        career_table["面试方法论"] = "工程叙事四层结构: 本质→实践→踩坑→思考"
        career_table["目标公司"] = "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团"

    # ==================================================================
    # 构建 Markdown
    # ==================================================================
    lines = []
    lines.append(f"# 个人画像归档 - {DATE_STR}")
    lines.append("")

    # ── 投资持仓概览 ──
    lines.append("## 投资持仓概览")
    lines.append("")

    # 加密货币
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    for label, qty, price, mkt, storage in crypto_rows:
        lines.append(f"| {label} | {qty} | {price} | {mkt} | {storage} |")
    lines.append("")

    # 美股
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    for label, qty, price, mkt, storage in us_rows:
        lines.append(f"| {label} | {qty} | {price} | {mkt} | {storage} |")
    lines.append("")

    # 港股
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")
    for label, qty, price, mkt, storage in hk_rows:
        lines.append(f"| {label} | {qty} | {price} | {mkt} | {storage} |")
    lines.append("")

    # A股
    lines.append("### A股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")
    for label, qty, price, mkt, storage in a_rows:
        lines.append(f"| {label} | {qty} | {price} | {mkt} | {storage} |")
    lines.append("")

    # TS 时间代币
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")
    for label, qty, mkt in ts_rows:
        lines.append(f"| {label} | {qty} | {mkt} |")
    lines.append("")

    # 关键指标
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总资产 | **{fmt_cny(total_assets)}** |")
    lines.append(f"| 净资产 | **{fmt_cny(net_assets)}** |")
    lines.append(f"| 投资总资产 | **{fmt_cny(investment_total)}** |")
    lines.append(f"| 家庭备用金 | {fmt_cny(cash_home)} |")
    lines.append(f"| HK打新资金 | {fmt_hkd(cash_hk)} (≈{fmt_cny(cash_hk_cny)}) |")
    lines.append(f"| USDT余额 | {fmt_usd(cash_usdt)} (≈{fmt_cny(cash_usdt * USD_CNY)}) |")
    lines.append(f"| 华盛通现金 | {fmt_usd(cash_sihuatong)} (≈{fmt_cny(cash_sihuatong * USD_CNY)}) |")
    lines.append(f"| 信用卡负债 | {fmt_cny(credit_card)} |")
    lines.append(f"| BTC占投资比 | {btc_pct:.1f}% |")
    lines.append(f"| CRCL集中度 | {crcl_pct:.1f}% ⚠️ |")
    lines.append(f"| 房贷总额 | {fmt_cny(mortgage_commercial)}+{fmt_cny(mortgage_fund)} |")
    lines.append("")

    # ── 职业发展画像 ──
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")
    for key in ("当前公司", "当前角色", "经验", "技能栈", "核心能力", "行业聚焦",
                 "地点约束", "目标薪资", "求职状态", "面试方法论", "目标公司"):
        val = career_table.get(key, "")
        lines.append(f"| {key} | {val} |")
    lines.append("")

    # ── 家庭与保险 ──
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 居住地 | 北京 |")
    lines.append(f"| 户籍 | 非京籍 (内蒙古) |")
    lines.append(f"| 子女 | 有孩子 (在京上学) |")
    lines.append(f"| 配偶 | 已婚 (薛燕) |")
    lines.append(f"| 房产 | 北京海淀住宅 {fmt_cny(house_value)} (购入2025年底) |")
    lines.append(f"| 房贷商贷 | {fmt_cny(mortgage_commercial)} |")
    lines.append(f"| 房贷公积金 | {fmt_cny(mortgage_fund)} |")
    lines.append(f"| hanwei_zhongji | 达尔文50W (¥6,960/年, 2026-06-15生效) |")
    lines.append(f"| hanwei_dingshou | 待配置 (目标200W保额) |")
    lines.append(f"| xueyan_zhongji | 待配置 (目标30-50W保额) |")
    lines.append("")

    # ── A8计划进度 ──
    btc_qty = 0
    for h in crypto_items:
        if h.get("symbol") == "BTC":
            btc_qty = h["quantity"]
            break
    btc_target = 2.32
    btc_progress = (btc_qty / btc_target * 100) if btc_target > 0 else 0

    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")
    lines.append(f"| 目标 | 1000万人民币 (2026-2028) |")
    lines.append(f"| 当前净资产 | **{fmt_cny(net_assets)}** ({net_assets / 10_000_000 * 100:.1f}%) |")
    lines.append(f"| BTC目标 | {btc_target}个 (当前{btc_qty}, 进度{btc_progress:.1f}%) |")
    lines.append(f"| CRCL自持 | {crcl_total_qty}股 (目标占比≤20%, 当前{crcl_pct:.1f}%⚠️) |")
    lines.append(f"| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")
    lines.append(f"| 当前状态 | 数据来自报告自动解析 |")
    lines.append("")

    # ── 本次更新变更记录 ──
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    lines.append(f"| profile.last_sync | — | {DATE_STR} | 每日自动归档 |")
    lines.append(f"| 数据源 | — | holdings.yaml | 从持仓 YAML 自动解析 |")
    lines.append(f"| 职业档案 | 无变更 | 个人职业发展分析-端侧AI企业定制攻略.md | 无变更 |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# 写入归档
# ======================================================================

def write_archive(content, archive_dir):
    """将归档内容写入指定目录的 profile_YYYYMMDD.md。"""
    os.makedirs(archive_dir, exist_ok=True)
    filepath = os.path.join(archive_dir, f"profile_{DATE_TAG}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    log(f"已写入: {filepath}")
    return filepath


# ======================================================================
# 入口
# ======================================================================

def main():
    log("=" * 50)
    log(f"开始每日个人画像归档 (date={DATE_STR})")

    # 1. 加载 holdings
    holdings_data = load_holdings()
    if holdings_data is None:
        log("持仓数据加载失败，终止归档", "ERROR")
        sys.exit(1)

    # 2. 加载职业档案
    career_data = load_career()

    # 3. 获取最新报告名
    report_name = get_latest_report_name()
    log(f"最新报告: {report_name}")

    # 4. 从上一期归档继承价格（用小时推送目录作为继承源）
    previous = load_previous_archive(PATHS["archive_hour"])
    previous_prices = extract_previous_prices(previous) if previous else {}
    log(f"上期归档价格继承: {len(previous_prices)} 个标的有上期价格")

    # 5. 构建归档内容
    content = build_profile_md(holdings_data, career_data, previous_prices, report_name)

    # 6. 写入两份归档
    hour_path = write_archive(content, PATHS["archive_hour"])
    day_path = write_archive(content, PATHS["archive_day"])

    log(f"归档完成: {os.path.basename(hour_path)} | {os.path.basename(day_path)}")
    log("=" * 50)


if __name__ == "__main__":
    main()