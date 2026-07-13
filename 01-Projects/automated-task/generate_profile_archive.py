#!/usr/bin/env python3
"""
个人画像归档生成器 — 读取最新投资持仓、投资报告、职业发展档案，
生成两份归档摘要到 profile_archive 目录（小时推送和日报推送各一份）。

架构说明：
  - profile_loader.py 自动从 profile_archive/ 按文件名日期排序取最新文件
  - analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile() 动态加载
  - 更新 profile_archive/ 即自动生效，无需修改任何代码

用法：
  python generate_profile_archive.py

输出：
  - 0.trae-feishu-push-hour/profile_archive/profile_YYYYMMDD.md
  - 1.trae-feishu-push-day/profile_archive/profile_YYYYMMDD.md
"""

import os
import sys
import re
import yaml
import glob
import logging
from datetime import datetime, timezone, timedelta

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = r"E:\ProjectGroup\AI\ContextStack"
HOLDINGS_PATH = os.path.join(BASE_DIR, "01-Projects", "family-hub", "research", "portfolio", "holdings.yaml")
REPORTS_DIR = os.path.join(BASE_DIR, "01-Projects", "family-hub", "research", "portfolio", "reports")
CAREER_PATH = os.path.join(BASE_DIR, "02-Knowledge", "career-development", "career-strategy", "个人职业发展分析-端侧AI企业定制攻略.md")

HOUR_ARCHIVE_DIR = os.path.join(BASE_DIR, "01-Projects", "automated-task", "0.trae-feishu-push-hour", "profile_archive")
DAY_ARCHIVE_DIR = os.path.join(BASE_DIR, "01-Projects", "automated-task", "1.trae-feishu-push-day", "profile_archive")

# 北京时区
BJT = timezone(timedelta(hours=8))

# ============================================================
# 日志
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("profile_archive")


# ============================================================
# 数据读取
# ============================================================

def load_holdings():
    """读取投资持仓 YAML"""
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_latest_report():
    """读取最新月度投资报告"""
    reports = sorted(glob.glob(os.path.join(REPORTS_DIR, "家庭资产报告-*.md")), reverse=True)
    if not reports:
        raise FileNotFoundError(f"未找到投资报告: {REPORTS_DIR}")
    latest = reports[0]
    logger.info(f"读取最新投资报告: {os.path.basename(latest)}")
    with open(latest, "r", encoding="utf-8") as f:
        return f.read()


def load_career_profile():
    """读取职业发展档案"""
    with open(CAREER_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# 数据提取
# ============================================================

def extract_holdings_summary(holdings_data):
    """从 holdings.yaml 提取持仓概览"""
    data = holdings_data
    holdings = data.get("holdings", [])
    cash = data.get("cash", [])
    liabilities = data.get("liabilities", [])
    meta = data.get("meta", {})

    # 按类别分类
    crypto_items = []
    us_stock_items = []
    hk_stock_items = []
    ts_items = []
    crcl_total_qty = 0.0

    for h in holdings:
        sym = h.get("symbol", "")
        name = h.get("name", "")
        qty = h.get("quantity", 0)
        cat = h.get("category", "")
        price = h.get("manual_price_usd", 0)
        storage = h.get("storage", "")

        if cat == "crypto":
            # BTC
            if sym == "BTC":
                crypto_items.append({
                    "label": "BTC(链上)",
                    "qty": f"{qty}",
                    "price_usd": f"${price:,.2f}" if price else "$0",
                    "storage": storage
                })
        elif cat in ("us_stock_tokenized", "us_stock"):
            if sym == "CRCL":
                crcl_total_qty += qty
            # 汇总美股，但不逐个列出，后面用报告数据
        elif cat == "hk_stock":
            pass  # 从报告取
        elif cat == "ts_time_token":
            ts_items.append({
                "label": "xiaoan" if "小安" in name else "wufan",
                "qty": f"{qty:,}秒" if "秒" in str(h.get("unit", "")) else f"{qty}",
            })

    # 从报告提取更精确的美股/港股数据
    return crcl_total_qty


def parse_report_metrics(report_text):
    """从投资报告解析关键指标和持仓明细"""
    metrics = {}

    # ---- 资产总览（从 ## 一、资产总览 下的表格解析） ----
    overview_section = re.search(
        r"## 一、资产总览(.+?)(?=\n## |\Z)", report_text, re.DOTALL
    )
    if overview_section:
        overview_text = overview_section.group(1)
        # 提取表格行
        table_rows = re.findall(r"^\|(.+?)\|$", overview_text, re.MULTILINE)
        for row in table_rows:
            cells = [c.strip() for c in row.split("|")]
            if len(cells) >= 2:
                key = cells[0]
                val = cells[1]
                if key in ("总资产", "净资产", "投资总资产"):
                    m = re.search(r"¥?([\d,]+\.?\d*)", val)
                    if m:
                        metrics[key] = f"¥{m.group(1)}"

    # ---- 投资资产明细表 ----
    # 找到 ## 二、投资资产明细 下的表格
    section_match = re.search(
        r"## 二、投资资产明细[^#]*?\n(\|.+?\|[\s\S]*?)(?=\n##|\Z)",
        report_text
    )
    investments = []
    if section_match:
        table_text = section_match.group(1)
        rows = re.findall(r"^\|.+?\|$", table_text, re.MULTILINE)
        # 跳过表头行（含 ----- 分隔行）
        data_rows = []
        for row in rows:
            cells = [c.strip() for c in row.split("|")[1:-1]]
            if len(cells) >= 9 and not all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                data_rows.append(cells)
        for cells in data_rows:
            investments.append({
                "name": cells[0].strip(),
                "qty": cells[1].strip(),
                "price": cells[2].strip(),
                "market_value": cells[3].strip(),
                "cost_price": cells[4].strip() if len(cells) > 4 else "",
                "cost_total": cells[5].strip() if len(cells) > 5 else "",
                "pnl": cells[6].strip() if len(cells) > 6 else "",
                "ratio": cells[7].strip() if len(cells) > 7 else "",
                "storage": cells[8].strip() if len(cells) > 8 else "",
            })

    # ---- 现金及固收 ----
    cash_match = re.search(r"## 五、现金及固收(.+?)(?=\n##|\Z)", report_text, re.DOTALL)
    cash_items = {}
    if cash_match:
        cash_text = cash_match.group(1)
        # 家庭备用金
        m = re.search(r"家庭备用金[^\n]*¥([\d,]+\.?\d*)", cash_text)
        if m:
            cash_items["家庭备用金"] = f"¥{m.group(1)}"
        # HK打新资金
        m = re.search(r"HK打新资金[^\n]*HK\$([\d,]+\.?\d*)", cash_text)
        if m:
            cash_items["HK打新资金"] = f"HK${m.group(1)}"
        # USDT余额 — 用明确锚定: 先找"$"再捕获数字
        m = re.search(r"币安USDT余额[^\n]*\$([\d,]+\.?\d*)", cash_text)
        if m:
            cash_items["USDT余额"] = f"${m.group(1)}"

    # ---- 负债 ----
    liability_match = re.search(r"## 四、负债(.+?)(?=\n##|\Z)", report_text, re.DOTALL)
    liabilities = {}
    if liability_match:
        liab_text = liability_match.group(1)
        m = re.search(r"信用卡循环[^\n]*¥([\d,]+\.?\d*)", liab_text)
        if m:
            liabilities["信用卡负债"] = f"¥{m.group(1)}"

    # ---- 房贷 ----
    mortgage_match = re.search(r"## 七、房贷与房产说明(.+?)(?=\n##|\Z)", report_text, re.DOTALL)
    mortgage_str = ""
    if mortgage_match:
        mortgage_text = mortgage_match.group(1)
        m1 = re.search(r"商贷[：:]\s*¥([\d,]+\.?\d*)", mortgage_text)
        m2 = re.search(r"公积金[：:]\s*¥([\d,]+\.?\d*)", mortgage_text)
        if m1 and m2:
            mortgage_str = f"¥{m1.group(1)}+¥{m2.group(1)}"
        elif m1:
            mortgage_str = f"¥{m1.group(1)}"

    # ---- 提取 CRCL 集中度 ----
    # 从投资明细中计算 CRCL 占比
    crcl_ratio = ""
    for inv in investments:
        if "CRCL" in inv["name"] and "合计" in inv["name"]:
            crcl_ratio = inv["ratio"]
            break
    if not crcl_ratio:
        # 从投资合计行找
        for inv in investments:
            if "投资合计" in inv["name"]:
                break
        # 手动计算 CRCL 市值占比
        crcl_market_value = 0
        total_invest = 0
        for inv in investments:
            if "投资合计" in inv["name"]:
                vm = re.search(r"¥?([\d,]+\.?\d*)", inv["market_value"])
                if vm:
                    total_invest = float(vm.group(1).replace(",", ""))
                break
            if "CRCL" in inv["name"] or "Circle" in inv["name"]:
                vm = re.search(r"¥?([\d,]+\.?\d*)", inv["market_value"])
                if vm:
                    crcl_market_value += float(vm.group(1).replace(",", ""))
        if total_invest > 0:
            crcl_ratio = f"{crcl_market_value / total_invest * 100:.1f}%"

    # 从中提取 BTC 占比
    btc_ratio = ""
    for inv in investments:
        if "比特币" in inv["name"] or "BTC" in inv["name"]:
            btc_ratio = inv["ratio"]
            break

    return {
        "metrics": metrics,
        "investments": investments,
        "cash": cash_items,
        "liabilities": liabilities,
        "mortgage": mortgage_str,
        "crcl_ratio": crcl_ratio,
        "btc_ratio": btc_ratio,
    }


def extract_career_summary(career_text):
    """从职业发展档案提取关键信息"""
    summary = {}

    # 经验年限
    m = re.search(r"\*\*~?(\d+)年\*\*", career_text)
    if m:
        summary["experience"] = m.group(0)

    # 当前角色
    m = re.search(r"当前角色.*?\|(.+?)(?:\||$)", career_text)
    if m:
        summary["role"] = m.group(1).strip()
    else:
        summary["role"] = "嵌入式开发工程师"

    # 技能栈
    m = re.search(r"技能栈.*?\|(.+?)(?:\||$)", career_text)
    if m:
        summary["skills"] = m.group(1).strip()
    else:
        summary["skills"] = "C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM"

    # 核心能力
    m = re.search(r"S级能力.*?\|(.+?)(?:\||$)", career_text)
    if m:
        summary["core"] = m.group(1).strip()
    else:
        summary["core"] = "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构"

    # 行业聚焦
    m = re.search(r"行业聚焦.*?\|(.+?)(?:\||$)", career_text)
    if m:
        summary["focus"] = m.group(1).strip()
    else:
        summary["focus"] = "工业嵌入式、通信设备底层"

    # 地点约束
    m = re.search(r"地点约束.*?\|(.+?)(?:\||$)", career_text)
    if m:
        summary["location"] = m.group(1).strip()
    else:
        summary["location"] = "北京，优先海淀/昌平"

    # 目标公司
    m = re.search(r"目标公司.*?\|(.+?)(?:\||$)", career_text)
    if m:
        summary["target_companies"] = m.group(1).strip()
    else:
        summary["target_companies"] = ""

    # 目标薪资
    m = re.search(r"薪资预期[：:]\s*\*\*¥?(\d+-\d+W)", career_text)
    if m:
        summary["salary"] = m.group(1)
    else:
        m = re.search(r"建议范围[：:]\s*\*\*¥?(\d+-\d+W)", career_text)
        if m:
            summary["salary"] = m.group(1)
        else:
            summary["salary"] = "50-70W"

    # 面试方法论
    summary["interview_method"] = "工程叙事四层结构: 本质→实践→踩坑→思考"

    # 目标公司列表
    companies = []
    for section in ["海淀区（优先级从高到低）", "昌平区", "北京其他区域（可接受）"]:
        m = re.search(rf"## {re.escape(section)}(.+?)(?=##|\Z)", career_text, re.DOTALL)
        if m:
            section_text = m.group(1)
            # 提取公司名
            company_names = re.findall(r"\*\*([^*]+?)\*\*", section_text)
            companies.extend(company_names)
    summary["target_companies"] = "、".join(companies) if companies else "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团"

    return summary


# ============================================================
# 归档生成
# ============================================================

def generate_profile_content(holdings_data, report_text, career_text, today_str, yesterday_str, holdings_last_updated):
    """生成完整的归档 markdown 内容"""
    report_parsed = parse_report_metrics(report_text)
    career = extract_career_summary(career_text)
    crcl_total = extract_holdings_summary(holdings_data)

    # 从报告投资明细中提取分类数据
    investments = report_parsed["investments"]
    metrics = report_parsed["metrics"]
    cash = report_parsed["cash"]
    liab = report_parsed["liabilities"]
    mortgage_str = report_parsed["mortgage"]
    crcl_ratio = report_parsed.get("crcl_ratio", "68.8%")
    btc_ratio = report_parsed.get("btc_ratio", "9.1%")

    # 分类提取 — 过滤表头行和合计行
    def _is_data_row(inv):
        name = inv.get("name", "")
        if name in ("标的", "**投资合计**", "投资合计"):
            return False
        return True

    investments = [i for i in investments if _is_data_row(i)]

    crypto_inv = [i for i in investments if "比特币" in i["name"] or "BTC" in i["name"]]
    us_inv = [i for i in investments if i["storage"] and i["storage"] not in ("TS平台", "东方财富港股通") and "比特币" not in i["name"]]
    hk_inv = [i for i in investments if "东方财富港股通" in i.get("storage", "")]
    ts_inv = [i for i in investments if "TS平台" in i.get("storage", "")]

    # USDT 信息
    usdt_val = cash.get("USDT余额", "")
    hk_cash = cash.get("HK打新资金", "")
    family_cash = cash.get("家庭备用金", "¥630,808")
    credit_card = liab.get("信用卡负债", "¥400,000")

    # 总计
    total_assets = metrics.get("总资产", "¥1,401,580")
    net_assets = metrics.get("净资产", "¥1,001,580")
    invest_assets = metrics.get("投资总资产", "¥569,658")

    # 检查数据是否有变化
    has_changes = False
    # 比较旧值（从上一期归档读取）
    # 简单起见，这里只做逻辑标记，实际变更记录在下方生成

    lines = []
    lines.append(f"# 个人画像归档 - {today_str}")
    lines.append("")
    lines.append("## 投资持仓概览")
    lines.append("")
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    # BTC — 使用 key BTC(链上) 以兼容 profile_loader.py 的解析逻辑
    for inv in crypto_inv:
        if "比特币" in inv["name"] or "BTC" in inv["name"]:
            lines.append(f"| BTC(链上) | {inv['qty']} | {inv['price']} | {inv['market_value']} | {inv['storage']} |")
        else:
            lines.append(f"| {inv['name']} | {inv['qty']} | {inv['price']} | {inv['market_value']} | {inv['storage']} |")

    # USDT
    if usdt_val:
        lines.append(f"| USDT(币安) | — | — | {usdt_val} | 韩伟蒙古币安 |")
    else:
        lines.append("| USDT(币安) | — | — | $10,940 | 韩伟蒙古币安 |")
    lines.append("| ETH | — | — | — | 已清仓 (2026-06-24) |")
    lines.append("")
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    # CRCL 合计
    crcl_items = [i for i in us_inv if "CRCL" in i["name"] or "Circle" in i["name"]]
    non_crcl = [i for i in us_inv if "CRCL" not in i["name"] and "Circle" not in i["name"]]

    crcl_total_qty = 0.0
    crcl_total_market = 0.0
    for i in crcl_items:
        qty_str = i["qty"].replace(",", "").strip()
        try:
            crcl_total_qty += float(qty_str)
        except ValueError:
            pass
        m = re.search(r"¥?([\d,]+\.?\d*)", i["market_value"])
        if m:
            crcl_total_market += float(m.group(1).replace(",", ""))

    lines.append(f"| Circle(CRCL合计) | {crcl_total_qty:.1f} | — | ¥{crcl_total_market:,.0f} | 分散多账户 |")
    for i in non_crcl:
        lines.append(f"| {i['name']} | {i['qty']} | {i['price']} | {i['market_value']} | {i['storage']} |")

    lines.append("")
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) |")
    lines.append("|------|------|-------|-----------|")
    for i in hk_inv:
        lines.append(f"| {i['name']} | {i['qty']} | {i['price']} | {i['market_value']} |")
    if not hk_inv:
        # 优必选
        for i in investments:
            if "优必选" in i["name"]:
                lines.append(f"| {i['name']} | {i['qty']} | {i['price']} | {i['market_value']} |")
                break

    lines.append("")
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")
    for i in ts_inv:
        name_short = "xiaoan" if "小安" in i["name"] else "wufan"
        lines.append(f"| {name_short} | {i['qty']} | {i['market_value']} |")

    lines.append("")
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总资产 | {total_assets} |")
    lines.append(f"| 净资产 | {net_assets} |")
    lines.append(f"| 投资总资产 | {invest_assets} |")
    lines.append(f"| 家庭备用金 | {family_cash} |")
    lines.append(f"| HK打新资金 | {hk_cash} |")
    lines.append(f"| 信用卡负债 | {credit_card} |")
    lines.append(f"| BTC占投资比 | {btc_ratio} |")
    lines.append(f"| CRCL集中度 | {crcl_ratio} ⚠️ |")
    lines.append(f"| 房贷总额 | {mortgage_str} |")

    lines.append("")
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 当前公司 | 新华三 |")
    lines.append(f"| 当前角色 | {career['role']} |")
    lines.append(f"| 经验 | {career['experience']} |")
    lines.append(f"| 技能栈 | {career['skills']} |")
    lines.append(f"| 核心能力 | {career['core']} |")
    lines.append(f"| 行业聚焦 | {career['focus']} |")
    lines.append(f"| 地点约束 | {career['location']} |")
    lines.append(f"| 目标薪资 | {career['salary']}总包 |")
    lines.append(f"| 求职状态 | 已约 1 年，面试过 九号/ISHO/思朗 |")
    lines.append(f"| 面试方法论 | {career['interview_method']} |")
    lines.append(f"| 目标公司 | {career['target_companies']} |")

    lines.append("")
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
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")
    lines.append("| 目标 | 1000万人民币 (2026-2028) |")
    lines.append("| BTC目标 | 2.32个 (当前0.130, 进度5.6%) |")
    lines.append("| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")
    lines.append("| 当前状态 | BTC在MA120下方, 定投暂存USDT待命 |")

    lines.append("")
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    lines.append(f"| profile.last_sync | {yesterday_str}T00:00:00 | {today_str}T00:00:00 | 自动归档 |")
    lines.append(f"| holdings.last_updated | {holdings_last_updated} | {holdings_last_updated} | 持仓数据未更新 |")
    lines.append(f"| price.data_date | 2026-07-01 | 2026-07-01 | 价格数据未更新 |")

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    """主入口：读取数据 → 生成归档 → 写入两份"""
    logger.info("=" * 60)
    logger.info("个人画像归档生成器 v2.0")
    logger.info("=" * 60)

    try:
        # 1. 读取数据源
        logger.info("读取投资持仓...")
        holdings_data = load_holdings()

        logger.info("读取最新投资报告...")
        report_text = load_latest_report()

        logger.info("读取职业发展档案...")
        career_text = load_career_profile()

        # 2. 确定日期
        now = datetime.now(BJT)
        today_str = now.strftime("%Y-%m-%d")
        today_compact = now.strftime("%Y%m%d")
        yesterday = now - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        holdings_last_updated = holdings_data.get("meta", {}).get("last_updated", "2026-07-08")

        # 3. 生成内容
        logger.info("生成归档内容...")
        content = generate_profile_content(
            holdings_data, report_text, career_text,
            today_str, yesterday_str, holdings_last_updated
        )

        # 4. 写入两份
        hour_path = os.path.join(HOUR_ARCHIVE_DIR, f"profile_{today_compact}.md")
        day_path = os.path.join(DAY_ARCHIVE_DIR, f"profile_{today_compact}.md")

        # 确保目录存在
        for d in [HOUR_ARCHIVE_DIR, DAY_ARCHIVE_DIR]:
            os.makedirs(d, exist_ok=True)

        with open(hour_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"小时推送归档: {hour_path}")

        with open(day_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"日报推送归档: {day_path}")

        # 5. 验证
        logger.info("验证归档文件...")
        if os.path.getsize(hour_path) > 100:
            logger.info("✓ 归档文件生成成功")
        else:
            logger.warning("⚠ 归档文件过小，可能内容异常")

        logger.info("=" * 60)
        logger.info("完成！静默归档成功")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"归档生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()