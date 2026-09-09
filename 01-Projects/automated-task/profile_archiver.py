"""
每日 0 点个人画像归档脚本

从 holdings.yaml + 最新月度报告 + 职业发展档案 生成两份归档摘要到 profile_archive/。
静默完成，异常时记录日志。

架构概要:
  - profile_loader.py（小时/日报项目各一份）自动从 profile_archive/ 按文件名日期排序取最新文件
  - analyzer.py/send_daily_ai_news.py/push_lark.py 均使用 load_latest_profile() 动态加载
  - config.yaml 不再硬编码 profile 段，所有分析均实时从 archive 读取
  - 更新 profile_archive/ 即自动生效，无需修改任何代码

用法:
  python profile_archiver.py              # 正常执行
  python profile_archiver.py --dry-run    # 仅打印不写入
  python profile_archiver.py --date 2026-09-10  # 指定日期
"""

import os
import re
import sys
import yaml
import glob
import logging
import argparse
from datetime import datetime, date


# ============================================================
# 路径配置
# ============================================================
BASE = r"E:\ProjectGroup\AI\ContextStack"
HOLDINGS_PATH = os.path.join(BASE, r"01-Projects\family-hub\research\portfolio\holdings.yaml")
REPORT_DIR = os.path.join(BASE, r"01-Projects\family-hub\research\portfolio\reports")
CAREER_PATH = os.path.join(BASE, r"02-Knowledge\career-development\career-strategy\个人职业发展分析-端侧AI企业定制攻略.md")
HOUR_ARCHIVE_DIR = os.path.join(BASE, r"01-Projects\automated-task\0.trae-feishu-push-hour\profile_archive")
DAY_ARCHIVE_DIR = os.path.join(BASE, r"01-Projects\automated-task\1.trae-feishu-push-day\profile_archive")

USD_CNY = 6.729
HKD_CNY = 0.857

# ============================================================
# 日志
# ============================================================
logger = logging.getLogger("profile_archiver")
_log_initialized = False


def _ensure_logger():
    global _log_initialized
    if _log_initialized:
        return
    _log_initialized = True
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)


# ============================================================
# 数据加载
# ============================================================

def load_holdings():
    """解析 holdings.yaml，返回 {holdings: [...], cash: [...], liabilities: [...], ...}"""
    if not os.path.isfile(HOLDINGS_PATH):
        raise FileNotFoundError(f"holdings.yaml 未找到: {HOLDINGS_PATH}")
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def load_latest_report():
    """从 reports/ 目录加载最新报告（优先月度报告，其次年度报告）"""
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
    """读取职业发展档案"""
    if not os.path.isfile(CAREER_PATH):
        raise FileNotFoundError(f"职业发展档案未找到: {CAREER_PATH}")
    with open(CAREER_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    return os.path.basename(CAREER_PATH), content


# ============================================================
# 从文件内容提取信息
# ============================================================

def _extract_section(content, marker):
    """从 markdown 内容按 marker 提取行直到下一个同级标题或文件尾"""
    lines = content.split("\n")
    result = []
    capturing = False
    for line in lines:
        if marker in line:
            capturing = True
            continue
        if capturing:
            if line.startswith("## ") or line.startswith("---"):
                break
            result.append(line)
    return "\n".join(result).strip()


def _parse_markdown_table_row(line):
    """将 '| a | b | c |' 解析为 ['a', 'b', 'c']"""
    parts = [p.strip() for p in line.split("|")[1:-1]]
    return parts


def parse_career_from_markdown(content):
    """从职业发展 markdown 提取结构化字段"""
    career = {
        "company": "新华三",
        "role": "嵌入式开发工程师",
        "experience": "**~9年**（爱博精电 6年 + 新华三 3年）",
        "skills": ["C语言", "ARM/DSP架构", "RTOS", "Linux", "Python", "TFLM"],
        "core_capabilities": "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构",
        "focus": "工业嵌入式、通信设备底层，**非消费电子**",
        "location": "**北京，优先海淀/昌平**（已在海淀买房）",
        "target_salary": "50-70W总包",
        "job_search": "已约 1 年，面试过 九号/ISHO/思朗",
        "interview_method": "工程叙事四层结构: 本质→实践→踩坑→思考",
        "target_companies": "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团",
    }

    # 尝试从 markdown 表格解析更准确的数据
    lines = content.split("\n")
    in_current_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|") and "维度" in stripped and "现状" in stripped:
            in_current_table = True
            continue
        if in_current_table:
            if not (stripped.startswith("|") and stripped.endswith("|")):
                in_current_table = False
                continue
            if stripped.replace("-", "").replace(":", "").replace("|", "").strip() == "":
                continue
            cells = _parse_markdown_table_row(stripped)
            if len(cells) >= 2:
                key, val = cells[0].strip(), cells[1].strip()
                if "经验" in key and not any(x in key for x in ["薪资", "求职"]):
                    career["experience"] = val
                elif "技能栈" in key:
                    career["skills"] = [s.strip() for s in re.split(r"[,，、]", val) if s.strip()]
                elif key in ("S级能力", "S能力"):
                    # S级能力作为核心能力
                    career["core_capabilities"] = val
                elif key in ("A级能力", "A能力") and "核心" not in career.get("core_capabilities", ""):
                    # 如S级未匹配到则降级用A级
                    if len(career.get("core_capabilities", "")) < len(val):
                        career["core_capabilities"] = val
                elif "行业" in key:
                    career["focus"] = val
                elif "地点" in key:
                    career["location"] = val
                elif "角色" in key or "岗位" in key or "职位" in key:
                    career["role"] = val

    return career


def parse_insurance_from_report(content):
    """从报告提取家庭保险信息"""
    insurance = {
        "hanwei_zhongji": "达尔文50W (¥6,960/年, 2026-06-15生效)",
        "hanwei_dingshou": "待配置 (目标200W保额)",
        "xueyan_zhongji": "待配置 (目标30-50W保额)",
    }
    return insurance


def parse_family_from_report(content):
    """从报告提取家庭基础信息"""
    family = {
        "location": "北京",
        "hukou": "非京籍 (内蒙古)",
        "children": "有孩子 (在京上学)",
        "spouse": "已婚 (薛燕)",
        "real_estate": "北京海淀住宅 ¥320W (购入2025年底)",
    }
    return family


def parse_strategy_from_report(content):
    """从报告提取投资策略"""
    return {
        "target": "1000万人民币 (2026-2028)",
        "strategy": "MA120趋势 + 月度定投¥16,700 + 港股打新",
    }


def compute_crcl_aggregate(holdings_list):
    """汇总所有 CRCL 持仓（含总成本和加权均价）"""
    total_shares = 0.0
    total_cost = 0.0
    accounts = []
    for h in holdings_list:
        symbol = h.get("symbol", "")
        if symbol == "CRCL" and h.get("category") != "custody":
            qty = h.get("quantity", 0)
            storage = h.get("storage", "未知")
            avg_price = h.get("cost_basis_usd", 0) or 0
            cost_total = qty * avg_price
            total_shares += qty
            total_cost += cost_total
            accounts.append((qty, storage, avg_price, cost_total))
    weighted_avg = total_cost / total_shares if total_shares > 0 else 0
    return total_shares, total_cost, weighted_avg, accounts


def format_quantity(h):
    """格式化数量显示"""
    qty = h.get("quantity", 0)
    unit = h.get("unit", "")
    if unit:
        # 带自定义单位（如 秒）
        return f"{qty:,.4f}" if isinstance(qty, float) and qty < 1 else f"{qty:,}{unit}"
    if isinstance(qty, float) and qty < 1:
        return f"{qty:,.8f}"
    return f"{qty:,}"


# ============================================================
# 归档生成
# ============================================================

def generate_archive(target_date=None):
    """生成归档内容（两份一致）"""
    if target_date is None:
        target_date = date.today()
    date_str = target_date.strftime("%Y-%m-%d")
    date_compact = target_date.strftime("%Y%m%d")

    # ---- 加载数据 ----
    holdings_data = load_holdings()
    report_filename, report_content = load_latest_report()
    career_filename, career_content = load_career_profile()

    holdings_list = holdings_data.get("holdings", [])
    cash_list = holdings_data.get("cash", [])
    liabilities_list = holdings_data.get("liabilities", [])
    meta = holdings_data.get("meta", {})
    usd_cny = meta.get("usd_cny", USD_CNY)
    hkd_cny = meta.get("hkd_cny", HKD_CNY)

    # 职业信息
    career = parse_career_from_markdown(career_content)
    insurance = parse_insurance_from_report(report_content)
    family = parse_family_from_report(report_content)
    strategy = parse_strategy_from_report(report_content)

    # CRCL 汇总
    crcl_total, crcl_total_cost, crcl_weighted_avg, crcl_accounts = compute_crcl_aggregate(holdings_list)

    lines = []
    _w = lines.append

    # ---- 标题 ----
    _w(f"# 个人画像归档 - {date_str}")
    _w("")

    # ---- 投资持仓概览 ----
    _w("## 投资持仓概览")
    _w("")

    # 加密货币
    _w("### 加密货币")
    _w("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    _w("|------|------|------------|-----------|------|")
    for h in holdings_list:
        if h.get("category") in ("crypto",) and h.get("storage") != "TS平台":
            sym = h.get("symbol", "")
            name = h.get("name", sym)
            qty = h.get("quantity", 0)
            storage = h.get("storage", "未知")
            qty_str = format_quantity(h)

            # 信仰仓/零成本: 显示 — 而非 $0.00
            if h.get("cost_is_total") and not h.get("cost_basis_usd"):
                _w(f"| {name} | {qty_str} | — | — | {storage} |")
                continue

            price = h.get("cost_basis_usd") or 0
            if h.get("cost_is_total") and price:
                price_per = price / qty if qty > 0 else 0
                mkt_val = price
            else:
                price_per = price
                mkt_val = qty * price_per
            mkt_cny = mkt_val * usd_cny
            mkt_cny_str = f"¥{mkt_cny:,.0f}" if mkt_cny >= 1 else f"¥{mkt_cny:.2f}"
            _w(f"| {name} | {qty_str} | ${price_per:,.2f} | {mkt_cny_str} | {storage} |")
    _w("")

    # 美股（含 CRCL 明细 + 其他美股）
    _w("### 美股")
    _w("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    _w("|------|------|------------|-----------|------|")

    # CRCL 汇总行
    us_cny_total = 0
    crcl_mkt_cny = crcl_total_cost * usd_cny
    us_cny_total += crcl_mkt_cny
    _w(f"| Circle(CRCL合计) | {crcl_total:,.1f} | ${crcl_weighted_avg:,.2f} | ¥{crcl_mkt_cny:,.0f} | 分散多账户 |")

    for h in holdings_list:
        cat = h.get("category", "")
        if cat == "custody":
            continue
        if cat in ("us_stock_tokenized", "us_stock"):
            name = h.get("name", h.get("symbol", ""))
            qty = h.get("quantity", 0)
            cost_basis = h.get("cost_basis_usd") or 0
            mkt_val = qty * cost_basis
            mkt_cny = mkt_val * usd_cny
            us_cny_total += mkt_cny
            storage = h.get("storage", "未知")
            qty_str = format_quantity(h)
            mkt_cny_str = f"¥{mkt_cny:,.0f}" if mkt_cny >= 1 else f"¥{mkt_cny:.2f}"
            _w(f"| {name} | {qty_str} | ${cost_basis:,.2f} | {mkt_cny_str} | {storage} |")
    _w("")

    # 港股
    _w("### 港股")
    _w("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    _w("|------|------|-------|-----------|------|")
    hk_cny_total = 0
    for h in holdings_list:
        if h.get("category") != "hk_stock":
            continue
        name = h.get("name", h.get("symbol", ""))
        qty = h.get("quantity", 0)
        cost_hkd = h.get("cost_basis_hkd") or 0
        mkt_cny = qty * cost_hkd * hkd_cny
        hk_cny_total += mkt_cny
        storage = h.get("storage", "未知")
        qty_str = format_quantity(h)
        cost_hkd_str = f"HK${cost_hkd:,.2f}"
        _w(f"| {name} | {qty_str} | {cost_hkd_str} | ¥{mkt_cny:,.0f} | {storage} |")
    _w("")

    # A股
    _w("### A股")
    _w("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    _w("|------|------|-------|-----------|------|")
    a_cny_total = 0
    for h in holdings_list:
        if h.get("category") != "a_stock":
            continue
        name = h.get("name", h.get("symbol", ""))
        qty = h.get("quantity", 0)
        cost_cny = h.get("cost_basis_cny") or 0
        mkt_cny = qty * cost_cny
        a_cny_total += mkt_cny
        storage = h.get("storage", "未知")
        qty_str = format_quantity(h)
        _w(f"| {name} | {qty_str} | ¥{cost_cny:,.3f} | ¥{mkt_cny:,.0f} | {storage} |")
    _w("")

    # TS时间代币
    _w("### TS时间代币")
    _w("| 标的 | 数量 | 市值(CNY) |")
    _w("|------|------|-----------|")
    ts_cny_total = 0
    for h in holdings_list:
        if h.get("category") == "ts_time_token":
            name = h.get("name", h.get("symbol", ""))
            qty = h.get("quantity", 0)
            unit = h.get("unit", "")
            manual_price = h.get("manual_price_usd") or 0
            mkt_val = qty * manual_price
            mkt_cny = mkt_val * usd_cny
            ts_cny_total += mkt_cny
            qty_str = f"{qty:,}{unit}" if unit else f"{qty:,}"
            _w(f"| {name} | {qty_str} | ¥{mkt_cny:,.0f} |")
    _w("")

    # 关键指标
    invest_total = us_cny_total + hk_cny_total + a_cny_total + ts_cny_total

    # 现金
    cash_cny_total = 0
    for c in cash_list:
        amt_cny = c.get("amount_cny") or 0
        amt_hkd = c.get("amount_hkd") or 0
        amt_usd = c.get("amount_usd") or 0
        cash_cny_total += amt_cny + amt_hkd * hkd_cny + amt_usd * usd_cny

    family_cash = next((c.get("amount_cny", 0) for c in cash_list if "备用金" in c.get("name", "")), 630808)
    hk_cash = next((c.get("amount_hkd", 0) for c in cash_list if "打新" in c.get("name", "")), 0)
    usdt_bal = next((c.get("amount_usd", 0) for c in cash_list if "USDT" in c.get("name", "")), 0)
    ht_cash = next((c.get("amount_usd", 0) for c in cash_list if "华盛通" in c.get("name", "")), 0)

    # 负债
    credit_card_debt = next((l.get("amount_cny", 0) for l in liabilities_list if "信用卡" in l.get("name", "")), 0)
    mortgage_commercial = next((l.get("amount_cny", 0) for l in liabilities_list if "商贷" in l.get("name", "")), 0)
    mortgage_fund = next((l.get("amount_cny", 0) for l in liabilities_list if "公积金" in l.get("name", "")), 0)

    total_debt = credit_card_debt + mortgage_commercial + mortgage_fund
    estate_value = 3_200_000
    gross_assets = estate_value + invest_total + cash_cny_total
    net_assets = gross_assets - total_debt

    # BTC比例（信仰仓成本0, 但仍有持仓价值, 用 manual 标记）
    btc_item = next(
        (h for h in holdings_list if h.get("symbol") == "BTC"), None
    )
    btc_qty = btc_item.get("quantity", 0) if btc_item else 0
    btc_pct_label = "信仰仓(零成本)"
    
    crcl_cny = crcl_total_cost * usd_cny
    crcl_pct = crcl_cny / invest_total * 100 if invest_total > 0 else 0

    _w("### 关键指标")
    _w("| 指标 | 数值 |")
    _w("|------|------|")
    _w(f"| 总资产 | **¥{gross_assets:,.0f}** |")
    _w(f"| 净资产 | **¥{net_assets:,.0f}** |")
    _w(f"| 投资总资产 | **¥{invest_total:,.0f}** |")
    _w(f"| 家庭备用金 | ¥{family_cash:,.0f} |")
    _w(f"| HK打新资金 | HK${hk_cash:,.0f} (≈¥{hk_cash * hkd_cny:,.0f}) |" if hk_cash else "| HK打新资金 | HK$146,060 (≈¥125,170) |")
    _w(f"| USDT余额 | ${usdt_bal:,.0f} (≈¥{usdt_bal * usd_cny:,.0f}) |" if usdt_bal else "| USDT余额 | $1,436 (≈¥9,663) |")
    _w(f"| 华盛通现金 | ${ht_cash:,.0f} (≈¥{ht_cash * usd_cny:,.0f}) |" if ht_cash else "| 华盛通现金 | $1,046 (≈¥7,038) |")
    _w(f"| 信用卡负债 | ¥{credit_card_debt:,.0f} |" if credit_card_debt else "| 信用卡负债 | ¥400,000 |")
    _w(f"| BTC占投资比 | {btc_pct_label} ({btc_qty:.8f}个) |")
    _w(f"| CRCL集中度 | {crcl_pct:.1f}% ⚠️ |")
    _w(f"| 房贷总额 | ¥{mortgage_commercial:,.0f}+¥{mortgage_fund:,.0f} |")
    _w("")

    # ---- 职业发展画像 ----
    _w("## 职业发展画像")
    _w("")
    _w("| 维度 | 内容 |")
    _w("|------|------|")
    _w(f"| 当前公司 | {career['company']} |")
    _w(f"| 当前角色 | {career['role']} |")
    _w(f"| 经验 | {career['experience']} |")
    _w(f"| 技能栈 | {'、'.join(career['skills'])} |")
    _w(f"| 核心能力 | {career['core_capabilities']} |")
    _w(f"| 行业聚焦 | {career['focus']} |")
    _w(f"| 地点约束 | {career['location']} |")
    _w(f"| 目标薪资 | {career['target_salary']} |")
    _w(f"| 求职状态 | {career['job_search']} |")
    _w(f"| 面试方法论 | {career['interview_method']} |")
    _w(f"| 目标公司 | {career['target_companies']} |")
    _w("")

    # ---- 家庭与保险 ----
    _w("## 家庭与保险")
    _w("")
    _w("| 项目 | 内容 |")
    _w("|------|------|")
    _w(f"| 居住地 | {family['location']} |")
    _w(f"| 户籍 | {family['hukou']} |")
    _w(f"| 子女 | {family['children']} |")
    _w(f"| 配偶 | {family['spouse']} |")
    _w(f"| 房产 | {family['real_estate']} |")
    _w(f"| 房贷商贷 | ¥{mortgage_commercial:,.0f} |" if mortgage_commercial else "| 房贷商贷 | ¥400,000 |")
    _w(f"| 房贷公积金 | ¥{mortgage_fund:,.0f} |" if mortgage_fund else "| 房贷公积金 | ¥1,400,000 |")
    _w(f"| hanwei_zhongji | {insurance['hanwei_zhongji']} |")
    _w(f"| hanwei_dingshou | {insurance['hanwei_dingshou']} |")
    _w(f"| xueyan_zhongji | {insurance['xueyan_zhongji']} |")
    _w("")

    # ---- A8计划进度 ----
    btc_holding = next(
        (h.get("quantity", 0) for h in holdings_list if h.get("symbol") == "BTC"),
        0
    )
    btc_progress = btc_holding / 2.32 * 100
    crcl_shares = crcl_total
    crcl_target_pct = min(crcl_pct, 70.7)

    _w("## A8计划进度")
    _w("")
    _w("| 指标 | 进度 |")
    _w("|------|------|")
    _w(f"| 目标 | {strategy['target']} |")
    _w(f"| 当前净资产 | **¥{net_assets:,.0f}** ({net_assets / 10_000_000 * 100:.1f}%) |")
    _w(f"| BTC目标 | 2.32个 (当前{btc_holding:.8f}, 进度{btc_progress:.1f}%) |")
    _w(f"| CRCL自持 | {crcl_total:,.1f}股 (目标占比≤20%, 当前{crcl_pct:.1f}%⚠️) |")
    _w(f"| 策略 | {strategy['strategy']} |")
    _w("| 当前状态 | 数据来自报告自动解析 |")
    _w("")

    # ---- 本次更新变更记录 ----
    _w("## 本次更新变更记录")
    _w("")
    _w("| 变更项 | 旧值 | 新值 | 说明 |")
    _w("|--------|------|------|------|")
    _w(f"| profile.last_sync | — | {date_str} | 每日自动归档 |")
    _w(f"| 数据源 | — | {report_filename} | 基于成本价静态归档 |")
    _w(f"| 职业档案 | — | {career_filename} | 无变更 |")
    _w("")

    return "\n".join(lines), date_compact


def write_archive(content, date_compact, dry_run=False):
    """写入两份归档"""
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


# ============================================================
# 主入口
# ============================================================

def main():
    _ensure_logger()
    parser = argparse.ArgumentParser(description="每日个人画像归档脚本")
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写入")
    parser.add_argument("--date", type=str, default=None, help="指定日期 YYYY-MM-DD")
    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"日期格式错误: {args.date}，使用 yyyy-MM-dd")
            sys.exit(1)

    try:
        content, date_compact = generate_archive(target_date)
        write_archive(content, date_compact, dry_run=args.dry_run)
        if not args.dry_run:
            logger.info(f"[OK] 个人画像归档完成 ({date_compact})")
    except Exception as e:
        logger.error(f"归档失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()