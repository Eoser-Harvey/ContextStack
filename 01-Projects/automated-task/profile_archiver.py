"""
每日 0 点个人画像归档脚本

从 holdings.yaml + 最新月度报告（取实时价格） + 职业发展档案 生成两份归档摘要。
静默完成（日志写入文件），异常时输出到 stderr。

用法:
  python profile_archiver.py
  python profile_archiver.py --date 2026-09-10
  python profile_archiver.py --dry-run

架构:
  - profile_loader.py（小时/日报项目各一份）自动从 profile_archive/ 按文件名日期排序取最新文件
  - analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile() 动态加载
  - 更新 profile_archive/ 即自动生效，无需修改代码
"""

import os
import re
import sys
import yaml
import glob
import logging
import argparse
from datetime import datetime, date, timedelta

# ============================================================
# 路径配置
# ============================================================
BASE = r"E:\ProjectGroup\AI\ContextStack"
HOLDINGS_PATH = os.path.join(BASE, r"01-Projects\family-hub\research\portfolio\holdings.yaml")
REPORT_DIR = os.path.join(BASE, r"01-Projects\family-hub\research\portfolio\reports")
CAREER_PATH = os.path.join(BASE, r"02-Knowledge\career-development\career-strategy\个人职业发展分析-端侧AI企业定制攻略.md")
LOG_PATH = os.path.join(BASE, r"01-Projects\automated-task\profile_archiver.log")
HOUR_ARCHIVE_DIR = os.path.join(BASE, r"01-Projects\automated-task\0.trae-feishu-push-hour\profile_archive")
DAY_ARCHIVE_DIR = os.path.join(BASE, r"01-Projects\automated-task\1.trae-feishu-push-day\profile_archive")

USD_CNY = 6.729
HKD_CNY = 0.857


# ============================================================
# 日志 — 默认写入文件，仅异常时输出到 stderr
# ============================================================

def setup_logger():
    logger = logging.getLogger("profile_archiver")
    logger.setLevel(logging.INFO)

    # 文件 handler（总是写入）
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8", mode="a")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(fh)

    return logger


logger = setup_logger()


# ============================================================
# 数据加载
# ============================================================

def load_holdings():
    if not os.path.isfile(HOLDINGS_PATH):
        raise FileNotFoundError(f"holdings.yaml 未找到: {HOLDINGS_PATH}")
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def load_latest_report():
    """返回 (filename, content) 优先月度报告"""
    if not os.path.isdir(REPORT_DIR):
        raise FileNotFoundError(f"报告目录未找到: {REPORT_DIR}")

    files = sorted(
        [f for f in os.listdir(REPORT_DIR) if f.endswith(".md") and f != ".gitkeep"],
        reverse=True
    )
    if not files:
        raise FileNotFoundError("reports/ 下无 .md 报告文件")

    latest = files[0]
    path = os.path.join(REPORT_DIR, latest)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return latest, content


def load_career_profile():
    """返回 (basename, content)"""
    if not os.path.isfile(CAREER_PATH):
        raise FileNotFoundError(f"职业发展档案未找到: {CAREER_PATH}")
    with open(CAREER_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    return os.path.basename(CAREER_PATH), content


# ============================================================
# 报告解析 — 从月度报告表格中提取当前价/市值
# ============================================================

def _parse_report_table(report_content, section_heading):
    """
    从报告中找到指定 section 下的表格, 返回 [{header: cell, ...}] 
    """
    lines = report_content.split("\n")
    in_section = False
    in_table = False
    rows = []
    header = []

    for line in lines:
        stripped = line.strip()

        if not in_section:
            if stripped.startswith("## ") and section_heading in stripped:
                in_section = True
                continue

        if not in_section:
            continue

        if stripped.startswith("#") and not stripped.startswith("###"):
            break

        if not stripped:
            in_table = False
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                continue
            if not in_table:
                header = cells
                in_table = True
                continue
            row = {}
            for i, h in enumerate(header):
                row[h] = cells[i] if i < len(cells) else ""
            rows.append(row)

    return rows, header


def parse_invest_detail_map(report_content):
    """
    解析'二、投资资产明细'表 → {label: {price, mkt_value, storage}}
    """
    rows, header = _parse_report_table(report_content, "投资资产明细")
    detail = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) < 3:
            continue
        label = row[keys[0]]
        # 找价格列
        price = ""
        for k in keys:
            if k.strip() in ("当前单价", "当前价", "当前价格"):
                price = row[k]
                break
        if not price:
            price = row[keys[2]] if len(keys) > 2 else ""
        # 找市值列
        mkt_value = ""
        for k in keys:
            if "市值" in k:
                mkt_value = row[k]
                break
        # 找存放列
        storage = ""
        for k in keys:
            if "存放" in k:
                storage = row.get(k, "")
                break
        detail[label] = {"price": price, "mkt_value": mkt_value, "storage": storage}
    return detail


def parse_overview_map(report_content):
    """
    解析'一、资产总览'表 → {label: value}
    报告表格格式: | 类别 | 金额(CNY) | 占比 | 说明 |
    关键指标在行标签中（如"投资资金总额"、"投资净资产"、"持仓市值"、"持仓净值"）
    """
    rows, header = _parse_report_table(report_content, "资产总览")
    result = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) < 2:
            continue
        # 第一列是类别名
        label = row[keys[0]].replace("**", "").strip()
        val = row[keys[1]].replace("**", "").strip()
        # 匹配关键指标行
        if any(k in label for k in ("投资资金总额", "投资净资产", "总资产", "净资产", "持仓市值", "持仓净值")):
            result[label] = val
    return result


def parse_asset_summary_map(report_content):
    """解析'三、按资产统计'表 → {asset_name: {qty, pct}}"""
    rows, _ = _parse_report_table(report_content, "按资产统计")
    result = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) < 2:
            continue
        name = row[keys[0]].replace("**", "").strip()
        pct = ""
        for k in keys:
            if "占投资比" in k:
                pct = row.get(k, "").replace("⚠", "").strip()
                break
        result[name] = {"pct": pct}
    return result


def parse_liabilities_map(report_content):
    """解析'四、负债'表 → {name: amount}"""
    rows, _ = _parse_report_table(report_content, "负债")
    items = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) >= 2:
            name = row[keys[0]]
            amount = row[keys[1]]
            items[name] = amount
    return items


def parse_cash_map(report_content):
    """解析'五、现金及固收'表 → {name: amount}"""
    rows, _ = _parse_report_table(report_content, "现金及固收")
    items = {}
    for row in rows:
        keys = list(row.keys())
        if len(keys) >= 2:
            name = row[keys[0]]
            amount = row[keys[1]]
            items[name] = amount
    return items


# ============================================================
# 职业档案解析
# ============================================================

def parse_career_from_markdown(content):
    career = {
        "company": "新华三",
        "role": "嵌入式开发工程师",
        "experience": "**~9年**（爱博精电 6年 + 新华三 3年）",
        "skills": "C语言, ARM/DSP架构, RTOS, Linux, Python, TFLM",
        "core_capabilities": "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构",
        "focus": "工业嵌入式、通信设备底层，**非消费电子**",
        "location": "**北京，优先海淀/昌平**（已在海淀买房）",
        "target_salary": "50-70W总包",
        "job_search": "已约 1 年，面试过 九号/ISHO/思朗",
        "interview_method": "工程叙事四层结构: 本质→实践→踩坑→思考",
        "target_companies": "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团",
    }

    lines = content.split("\n")
    in_profile_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 2:
                key, val = cells[0], cells[1]
                val_clean = val.replace("**", "")
                if "总经验" in key:
                    career["experience"] = val_clean
                elif "技能栈" in key:
                    career["skills"] = val_clean
                elif "S级能力" in key:
                    career["core_capabilities"] = val_clean
                elif "核心能力" in key:
                    career["core_capabilities"] = val_clean
                elif "行业聚焦" in key:
                    career["focus"] = val_clean
                elif "地点约束" in key:
                    career["location"] = val_clean
                elif "角色" in key or "岗位" in key:
                    career["role"] = val_clean

    # 尝试解析薪资
    m = re.search(r"建议范围\s*\*\*¥?([\d-]+W)\s*总包\*\*", content)
    if m:
        career["target_salary"] = f"{m.group(1)}总包"

    return career


# ============================================================
# 辅助函数
# ============================================================

def _num(val):
    """从字符串提取数字"""
    if isinstance(val, (int, float)):
        return float(val)
    val = val.replace("**", "").replace("¥", "").replace("￥", "").replace("$", "").replace(",", "").replace("%", "").replace("⚠", "").replace("HK", "").strip()
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _parse_price(val):
    """解析价格字符串, 保留货币符号"""
    val = val.strip()
    if val in ("—", "-", ""):
        return "—"
    return val


def fmt_qty(h):
    qty = h.get("quantity", 0)
    unit = h.get("unit", "")
    if unit:
        return f"{qty:,}{unit}"
    if isinstance(qty, float) and qty < 1:
        return f"{qty:,.8f}"
    return f"{qty:,.4f}" if isinstance(qty, float) else f"{qty:,}"


# ============================================================
# 主生成逻辑
# ============================================================

def generate_archive(target_date=None):
    if target_date is None:
        target_date = date.today()
    date_str = target_date.strftime("%Y-%m-%d")
    date_compact = target_date.strftime("%Y%m%d")

    # 加载数据
    holdings_data = load_holdings()
    report_filename, report_content = load_latest_report()
    career_filename, career_content = load_career_profile()

    holdings_list = holdings_data.get("holdings", [])
    cash_list = holdings_data.get("cash", [])
    liabilities_list = holdings_data.get("liabilities", [])
    meta = holdings_data.get("meta", {})
    usd_cny = meta.get("usd_cny", USD_CNY)
    hkd_cny = meta.get("hkd_cny", HKD_CNY)

    # 报告解析
    detail = parse_invest_detail_map(report_content)
    overview = parse_overview_map(report_content)
    summary = parse_asset_summary_map(report_content)
    liability_table = parse_liabilities_map(report_content)
    cash_table = parse_cash_map(report_content)

    career = parse_career_from_markdown(career_content)

    # ---------- 持仓分组 ----------
    crypto_items = [h for h in holdings_list if h.get("category") in ("crypto",) and h.get("storage") != "TS平台"]
    us_stock_items = [h for h in holdings_list if h.get("category") in ("us_stock", "us_stock_tokenized")]
    hk_stock_items = [h for h in holdings_list if h.get("category") == "hk_stock"]
    a_stock_items = [h for h in holdings_list if h.get("category") == "a_stock"]
    ts_items = [h for h in holdings_list if h.get("category") == "ts_time_token"]

    # CRCL 汇总
    crcl_items = [h for h in holdings_list if h.get("symbol") == "CRCL" and h.get("category") != "custody"]
    crcl_total_qty = sum(h.get("quantity", 0) for h in crcl_items)
    crcl_total_cost = sum(h.get("quantity", 0) * (h.get("cost_basis_usd") or 0) for h in crcl_items)
    crcl_weighted_avg = crcl_total_cost / crcl_total_qty if crcl_total_qty > 0 else 0

    # 从报告找CRCL当前价
    crcl_price_str = "$—"
    for label, info in detail.items():
        if "CRCL" in label.upper() or "Circle" in label:
            if "合计" not in label:
                crcl_price_str = info.get("price", "$—")
                break

    # CRCL 集中度
    crcl_pct_str = "—"
    for name, info in summary.items():
        if "CRCL" in name.upper() or "Circle" in name:
            crcl_pct_str = info.get("pct", "—")
            break

    # ---------- 现金 ----------
    cash_family = 630808
    cash_hk = 0
    usdt_totals = 0
    ht_cash = 0
    for c in cash_list:
        n = c.get("name", "")
        v_cny = c.get("amount_cny") or 0
        v_hkd = c.get("amount_hkd") or 0
        v_usd = c.get("amount_usd") or 0
        if "备用金" in n:
            cash_family = v_cny or 630808
        elif "打新" in n:
            cash_hk += v_hkd
        if "币安U" in n or "币安" in n:
            usdt_totals += v_usd
        if "华盛" in n:
            ht_cash += v_usd

    # 从报告现金表补充
    for label, val in cash_table.items():
        if "HK" in label or "打新" in label:
            m = re.search(r'HK\$?([\d,]+)', val)
            if m:
                cash_hk = max(cash_hk, _num(m.group(1)))

    # ---------- 负债 ----------
    credit_card = 450000
    mortgage_commercial = 400000
    mortgage_fund = 1400000
    for l in liabilities_list:
        n = l.get("name", "")
        amt = l.get("amount_cny") or 0
        if "商贷" in n:
            mortgage_commercial = amt or 400000
        elif "公积金" in n:
            mortgage_fund = amt or 1400000
        elif "信用卡" in n:
            credit_card = amt or 450000

    # ---------- 构建归档内容 ----------
    lines = []
    _w = lines.append

    _w(f"# 个人画像归档 - {date_str}")
    _w("")
    _w("## 投资持仓概览")
    _w("")

    # --- 加密货币 ---
    _w("### 加密货币")
    _w("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    _w("|------|------|------------|-----------|------|")
    for h in crypto_items:
        name_key = h.get("name", "")
        sym = h.get("symbol", "")
        qty = h.get("quantity", 0)

        # 找报告中的价格
        price_str = "—"
        mkt_str = "—"
        storage = h.get("storage", "未知")
        for dk, dv in detail.items():
            if sym.lower() in dk.lower() or name_key in dk:
                price_str = dv.get("price", "—")
                mkt_str = dv.get("mkt_value", "—")
                if dv.get("storage"):
                    storage = dv.get("storage")
                break

        qty_str = fmt_qty(h)
        _w(f"| {name_key} | {qty_str} | {price_str} | {mkt_str} | {storage} |")
    _w("")

    # --- 美股 ---
    _w("### 美股")
    _w("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    _w("|------|------|------------|-----------|------|")
    _w(f"| Circle(CRCL合计) | {crcl_total_qty:,.1f} | {crcl_price_str} | — | 分散多账户 |")

    for h in us_stock_items:
        name_key = h.get("name", "")
        sym = h.get("symbol", "")
        qty = h.get("quantity", 0)
        storage = h.get("storage", "未知")
        if sym == "CRCL":
            # 用存放去重（避免重复列出CRCL合计行以外的明细）
            pass
        price_str = "—"
        for dk, dv in detail.items():
            if (name_key in dk or sym in dk) and "CRCL合计" not in dk:
                price_str = dv.get("price", "—")
                if dv.get("storage"):
                    storage = dv.get("storage")
                break
        qty_str = fmt_qty(h)
        _w(f"| {name_key} | {qty_str} | {price_str} | — | {storage} |")
    _w("")

    # --- 港股 ---
    _w("### 港股")
    _w("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    _w("|------|------|-------|-----------|------|")
    for h in hk_stock_items:
        name_key = h.get("name", "")
        sym = h.get("symbol", "")
        qty = h.get("quantity", 0)
        storage = h.get("storage", "未知")
        price_str = "—"
        for dk, dv in detail.items():
            if name_key in dk or sym in dk:
                price_str = dv.get("price", "—")
                break
        _w(f"| {name_key} | {fmt_qty(h)} | {price_str} | — | {storage} |")
    _w("")

    # --- A股 ---
    _w("### A股")
    _w("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    _w("|------|------|-------|-----------|------|")
    for h in a_stock_items:
        name_key = h.get("name", "")
        qty = h.get("quantity", 0)
        storage = h.get("storage", "未知")
        price_str = "—"
        for dk, dv in detail.items():
            if name_key in dk:
                price_str = dv.get("price", "—")
                break
        _w(f"| {name_key} | {fmt_qty(h)} | {price_str} | — | {storage} |")
    _w("")

    # --- TS时间代币 ---
    _w("### TS时间代币")
    _w("| 标的 | 数量 | 市值(CNY) |")
    _w("|------|------|-----------|")
    for h in ts_items:
        name_key = h.get("name", "")
        mkt_str = "—"
        for dk, dv in detail.items():
            if name_key in dk:
                mkt_str = dv.get("mkt_value", "—")
                break
        _w(f"| {name_key} | {fmt_qty(h)} | {mkt_str} |")
    _w("")

    # --- 关键指标 ---
    # 报告中文标签映射
    total_assets = overview.get("总资产", overview.get("持仓市值", "—"))
    net_assets = overview.get("净资产", overview.get("投资净资产", "—"))
    invest_assets = overview.get("投资总资产", overview.get("投资资金总额", "—"))

    usdt_fmt = f"${usdt_totals:,.0f} (≈¥{usdt_totals * usd_cny:,.0f})" if usdt_totals else "—"
    ht_fmt = f"${ht_cash:,.0f} (≈¥{ht_cash * usd_cny:,.0f})" if ht_cash else "—"
    hk_fmt = f"HK${cash_hk:,.0f} (≈¥{cash_hk * hkd_cny:,.0f})" if cash_hk else "—"
    cc_fmt = f"¥{credit_card:,}" if credit_card else "—"

    # BTC占比
    btc_pct = "—"
    for name, info in summary.items():
        if "BTC" in name.upper() or "比特币" in name:
            btc_pct = info.get("pct", "—")
            break

    _w("### 关键指标")
    _w("| 指标 | 数值 |")
    _w("|------|------|")
    _w(f"| 总资产 | **{total_assets}** |")
    _w(f"| 净资产 | **{net_assets}** |")
    _w(f"| 投资总资产 | **{invest_assets}** |")
    _w(f"| 家庭备用金 | ¥{cash_family:,} |")
    _w(f"| HK打新资金 | {hk_fmt} |")
    _w(f"| USDT余额 | {usdt_fmt} |")
    _w(f"| 华盛通现金 | {ht_fmt} |")
    _w(f"| 信用卡负债 | {cc_fmt} |")
    _w(f"| BTC占投资比 | {btc_pct} |")
    _w(f"| CRCL集中度 | {crcl_pct_str} ⚠️ |" if "⚠" not in crcl_pct_str else f"| CRCL集中度 | {crcl_pct_str} |")
    _w(f"| 房贷总额 | ¥{mortgage_commercial:,}+¥{mortgage_fund:,} |")
    _w("")

    # --- 职业发展画像 ---
    _w("## 职业发展画像")
    _w("")
    _w("| 维度 | 内容 |")
    _w("|------|------|")
    _w(f"| 当前公司 | {career['company']} |")
    _w(f"| 当前角色 | {career['role']} |")
    _w(f"| 经验 | {career['experience']} |")
    _w(f"| 技能栈 | {career['skills']} |")
    _w(f"| 核心能力 | {career['core_capabilities']} |")
    _w(f"| 行业聚焦 | {career['focus']} |")
    _w(f"| 地点约束 | {career['location']} |")
    _w(f"| 目标薪资 | {career['target_salary']} |")
    _w(f"| 求职状态 | {career['job_search']} |")
    _w(f"| 面试方法论 | {career['interview_method']} |")
    _w(f"| 目标公司 | {career['target_companies']} |")
    _w("")

    # --- 家庭与保险 ---
    _w("## 家庭与保险")
    _w("")
    _w("| 项目 | 内容 |")
    _w("|------|------|")
    _w("| 居住地 | 北京 |")
    _w("| 户籍 | 非京籍 (内蒙古) |")
    _w("| 子女 | 有孩子 (在京上学) |")
    _w("| 配偶 | 已婚 (薛燕) |")
    _w("| 房产 | 北京海淀住宅 ¥3,200,000 (购入2025年底) |")
    _w(f"| 房贷商贷 | ¥{mortgage_commercial:,} |")
    _w(f"| 房贷公积金 | ¥{mortgage_fund:,} |")
    _w("| hanwei_zhongji | 达尔文50W (¥6,960/年, 2026-06-15生效) |")
    _w("| hanwei_dingshou | 待配置 (目标200W保额) |")
    _w("| xueyan_zhongji | 待配置 (目标30-50W保额) |")
    _w("")

    # --- A8计划进度 ---
    btc_holding = 0
    for h in holdings_list:
        if h.get("symbol") == "BTC":
            btc_holding = h.get("quantity", 0)
            break
    btc_progress = btc_holding / 2.32 * 100 if btc_holding else 0

    net_val = _num(net_assets)
    a8_pct = net_val / 10_000_000 * 100 if net_val else 0

    _w("## A8计划进度")
    _w("")
    _w("| 指标 | 进度 |")
    _w("|------|------|")
    _w("| 目标 | 1000万人民币 (2026-2028) |")
    _w(f"| 当前净资产 | **{net_assets}** ({a8_pct:.1f}%) |")
    _w(f"| BTC目标 | 2.32个 (当前{btc_holding:.8f}, 进度{btc_progress:.1f}%) |")
    _w(f"| CRCL自持 | {crcl_total_qty:,.1f}股 (目标占比≤20%, 当前{crcl_pct_str}⚠️) |" if "⚠" not in crcl_pct_str else f"| CRCL自持 | {crcl_total_qty:,.1f}股 (目标占比≤20%, 当前{crcl_pct_str}) |")
    _w("| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")
    _w("| 当前状态 | 数据来自报告自动解析 |")
    _w("")

    # --- 变更记录 ---
    _w("## 本次更新变更记录")
    _w("")
    _w("| 变更项 | 旧值 | 新值 | 说明 |")
    _w("|--------|------|------|------|")
    _w(f"| profile.last_sync | — | {date_str} | 每日自动归档 |")
    _w(f"| 数据源 | — | {report_filename} | 基于报告实时价归档 |")
    _w(f"| 职业档案 | — | {career_filename} | 无变更 |")
    _w("")

    return "\n".join(lines), date_compact


# ============================================================
# 写入 & 清理
# ============================================================

def write_archive(content, date_compact, dry_run=False):
    paths = [HOUR_ARCHIVE_DIR, DAY_ARCHIVE_DIR]
    for archive_dir in paths:
        os.makedirs(archive_dir, exist_ok=True)
        out_path = os.path.join(archive_dir, f"profile_{date_compact}.md")
        if dry_run:
            logger.info(f"[DRY-RUN] 将写入: {out_path}")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"已写入: {out_path}")


def cleanup_old(keep_days=30):
    """清理超过 keep_days 天的旧归档"""
    cutoff = datetime.now() - timedelta(days=keep_days)
    for archive_dir in (HOUR_ARCHIVE_DIR, DAY_ARCHIVE_DIR):
        if not os.path.isdir(archive_dir):
            continue
        pattern = os.path.join(archive_dir, "profile_*.md")
        deleted = 0
        for fpath in glob.glob(pattern):
            fname = os.path.basename(fpath)
            m = re.search(r"profile_(\d{8})\.md", fname)
            if m:
                try:
                    fd = datetime.strptime(m.group(1), "%Y%m%d")
                    if fd < cutoff:
                        os.remove(fpath)
                        deleted += 1
                except (OSError, ValueError) as e:
                    logger.warning(f"清理失败: {fpath} - {e}")
        if deleted:
            logger.info(f"清理 {archive_dir}: 删除 {deleted} 个旧归档")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="每日个人画像归档脚本")
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写入")
    parser.add_argument("--date", type=str, default=None, help="指定日期 YYYY-MM-DD")
    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"日期格式错误: {args.date}")
            print(f"[ERROR] 日期格式错误: {args.date}", file=sys.stderr)
            sys.exit(1)

    try:
        content, date_compact = generate_archive(target_date)
        write_archive(content, date_compact, dry_run=args.dry_run)
        cleanup_old(keep_days=30)
        if not args.dry_run:
            logger.info(f"[OK] 个人画像归档完成 ({date_compact})")
    except Exception as e:
        logger.error(f"归档失败: {e}", exc_info=True)
        print(f"[ERROR] 归档失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()