#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日 0 点个人画像归档同步脚本

职责：
  1. 读取 holdings.yaml → 投资持仓概览
  2. 读取最新月度报告 → 关键指标
  3. 读取职业发展档案 → 职业画像
  4. 生成两份一致的归档摘要到 hour/day 的 profile_archive/
  5. 静默完成，异常时记录日志到 logs/sync_profile_archive.log

架构说明（新）：
  - profile_loader.py（小时/日报各一份）自动从 profile_archive/ 按文件名日期取最新文件
  - analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile() 动态加载
  - config.yaml 不再硬编码 profile 段，所有分析均实时从 archive 读取
  - 更新 profile_archive/ 即自动生效，无需修改任何代码

用法：
  python sync_profile_archive.py                   # 正常执行
  python sync_profile_archive.py --verbose         # 输出详细日志到 stdout

依赖：
  pip install pyyaml
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
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # ContextStack

# 自校验：确保 PROJECT_ROOT 指向正确位置（存在 01-Projects 子目录）
if not (PROJECT_ROOT / "01-Projects").is_dir():
    raise RuntimeError(
        f"PROJECT_ROOT 解析错误: {PROJECT_ROOT}\n"
        f"期望 ContextStack 根目录，但该路径下不存在 01-Projects/ 子目录。\n"
        f"脚本路径: {__file__}\n"
        f"请检查 parent.parent.parent 层级是否正确。"
    )

HOLDINGS_PATH = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "holdings.yaml"
REPORTS_DIR = PROJECT_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio" / "reports"
CAREER_PATH = PROJECT_ROOT / "02-Knowledge" / "career-development" / "career-strategy" / "个人职业发展分析-端侧AI企业定制攻略.md"

HOUR_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "0.trae-feishu-push-hour" / "profile_archive"
DAY_ARCHIVE_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "1.trae-feishu-push-day" / "profile_archive"

LOG_DIR = PROJECT_ROOT / "01-Projects" / "automated-task" / "logs"
LOG_PATH = LOG_DIR / "sync_profile_archive.log"


# ======================================================================
# 日志配置 — 默认只写文件，--verbose 时也输出到 stdout
# ======================================================================

def setup_logger(verbose: bool = False) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("sync_profile_archive")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # 文件日志（始终）
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    # stdout（仅 --verbose 或错误时）
    if verbose:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(ch)

    return logger


logger = setup_logger()


# ======================================================================
# 1. 读取投资持仓
# ======================================================================

def load_holdings() -> dict:
    """解析 holdings.yaml，返回结构化 dict"""
    if not HOLDINGS_PATH.exists():
        raise FileNotFoundError(f"holdings.yaml 不存在: {HOLDINGS_PATH}")

    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return {
        "meta": data.get("meta", {}),
        "holdings": data.get("holdings", []),
        "cash": data.get("cash", []),
        "liabilities": data.get("liabilities", []),
        "custody": data.get("custody", []),
        "fixed_assets": data.get("fixed_assets", []),
    }


# ======================================================================
# 2. 读取最新月度报告
# ======================================================================

def get_latest_report_path() -> Path:
    """按文件名找到最新月份的 '家庭资产报告-YYYY-MM.md'"""
    pattern = os.path.join(REPORTS_DIR, "家庭资产报告-*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"未找到月度报告: {REPORTS_DIR}")
    return Path(files[0])


def parse_report_metrics(filepath: Path) -> dict:
    """
    从月度报告中提取关键指标
    返回 dict: {指标名: 数值}
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    metrics = {}

    in_metrics_section = False
    for line in lines:
        stripped = line.strip()

        if re.match(r"^##\s+[一二三四五六七八九十]、?资产总览", stripped):
            in_metrics_section = True
            continue
        if in_metrics_section and re.match(r"^##\s", stripped):
            in_metrics_section = False
            continue

        if in_metrics_section and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 3:
                label = cells[0]
                value = cells[1]
                if label in ("总资产", "净资产", "投资总资产", "总负债"):
                    metrics[label] = value

    # 家庭备用金
    for line in lines:
        stripped = line.strip()
        if "家庭备用金" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 2:
                metrics["家庭备用金"] = cells[1]

    # CRCL 占比 — 从投资明细表提取
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
            if len(cells) >= 9:
                label = cells[0]
                if "CRCL" in label or "circle" in label.lower() or "Circle" in label:
                    pct = cells[-2]
                    m = re.search(r"(\d+\.?\d*)%", pct)
                    if m:
                        metrics.setdefault("crcl_pcts", []).append(float(m.group(1)))

    # 提取汇率
    m = re.search(r"USD/CNY=([\d.]+)", content)
    if m:
        metrics["usd_cny"] = float(m.group(1))
    m = re.search(r"HKD/CNY=([\d.]+)", content)
    if m:
        metrics["hkd_cny"] = float(m.group(1))

    # 提取 BTC 市值
    m = re.search(r"比特币\(链上\).*?\|\s*([\d.]+)\s*\|\s*\$?([\d,]+\.?\d*)\s*\|\s*¥?([\d,]+)", content)
    if m:
        metrics["btc_market_cny"] = m.group(3).replace(",", "")

    return metrics


# ======================================================================
# 3. 读取职业发展档案
# ======================================================================

def load_career_profile() -> dict:
    """从职业发展档案中提取关键信息"""
    if not CAREER_PATH.exists():
        raise FileNotFoundError(f"职业发展档案不存在: {CAREER_PATH}")

    content = CAREER_PATH.read_text(encoding="utf-8")
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

    # 从当前画像表格提取
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

    # 目标薪资
    m = re.search(r"建议范围\s*\*\*¥?([\d-]+W)\s*总包\*\*", content)
    if m:
        profile["salary_target"] = f"{m.group(1)}总包"

    return profile


# ======================================================================
# 4. 计算持仓汇总
# ======================================================================

def compute_holdings_summary(holdings_data: dict) -> dict:
    """
    从 holdings 数据计算汇总值
    返回: {btc, usdt, eth, crcl_total, crcl_price, crcl_market_cny,
           us_stocks, hk_stocks, ts_tokens, cash_cny, cash_hkd,
           credit_card_debt, mortgage_commercial, mortgage_fund,
           investment_total, btc_market_cny}
    """
    usd_cny = holdings_data["meta"].get("usd_cny", 6.796)
    hkd_cny = holdings_data["meta"].get("hkd_cny", 0.868) if isinstance(holdings_data["meta"].get("hkd_cny"), (int, float)) else 0.868

    summary = {
        "btc_qty": 0, "btc_price": 0, "btc_storage": "",
        "usdt_amount": 0, "usdt_storage": "",
        "eth_note": "已清仓 (2026-06-24)",
        "crcl_total_qty": 0, "crcl_price": 0, "crcl_market_cny": 0,
        "us_stocks": [], "hk_stocks": [], "ts_tokens": [],
        "cash_cny": 0, "cash_hkd": 0,
        "credit_card_debt": 0,
        "mortgage_commercial": 0, "mortgage_fund": 0,
        "investment_total_cny": 0,
        "btc_market_cny": 0,
    }

    for h in holdings_data["holdings"]:
        h_id = h.get("id", "")
        symbol = h.get("symbol", "")
        name = h.get("name", "")
        category = h.get("category", "")
        qty = h.get("quantity", 0) or 0
        price = h.get("manual_price_usd", 0) or 0
        storage = h.get("storage", "")
        market_cny = qty * price * usd_cny

        if h_id == "btc_onchain":
            summary["btc_qty"] = qty
            summary["btc_price"] = price
            summary["btc_storage"] = storage
            summary["btc_market_cny"] = market_cny
            summary["investment_total_cny"] += market_cny

        elif symbol == "CRCL":
            summary["crcl_total_qty"] += qty
            if not summary["crcl_price"]:
                summary["crcl_price"] = price
            summary["crcl_market_cny"] += market_cny
            summary["investment_total_cny"] += market_cny

        elif category in ("us_stock", "us_stock_tokenized"):
            summary["investment_total_cny"] += market_cny
            if symbol not in ("CRCL",):
                summary["us_stocks"].append({
                    "name": name, "symbol": symbol,
                    "qty": qty, "price": price, "market_cny": market_cny,
                    "storage": storage,
                })

        elif category == "hk_stock":
            summary["investment_total_cny"] += market_cny
            display_name = re.sub(r"\(.*?\)", "", name).strip() or symbol
            summary["hk_stocks"].append({
                "name": display_name, "symbol": symbol,
                "qty": int(qty), "price": price, "market_cny": market_cny,
            })

        elif category == "ts_time_token":
            summary["investment_total_cny"] += market_cny
            unit = h.get("unit", "")
            qty_str = f"{int(qty):,}秒" if unit == "秒" else str(qty)
            summary["ts_tokens"].append({
                "label": symbol.lower(), "qty": qty_str, "market_cny": market_cny,
            })

    # 现金
    for c in holdings_data["cash"]:
        cname = c.get("name", "")
        if "币安USDT" in cname:
            summary["usdt_amount"] = c.get("amount_usd", 0)
        elif "备用金" in cname:
            summary["cash_cny"] = c.get("amount_cny", 0)
        elif "打新" in cname:
            summary["cash_hkd"] = c.get("amount_hkd", 0)

    # 负债
    for li in holdings_data["liabilities"]:
        lname = li.get("name", "")
        if "信用卡" in lname:
            summary["credit_card_debt"] = li.get("amount_cny", 0)
        elif "商贷" in lname:
            summary["mortgage_commercial"] = li.get("amount_cny", 0)
        elif "公积金" in lname:
            summary["mortgage_fund"] = li.get("amount_cny", 0)

    return summary


# ======================================================================
# 5. 构建归档内容
# ======================================================================

def build_archive_content(holdings_data: dict, report_metrics: dict,
                          career_profile: dict, summary: dict) -> str:
    """
    构建完整归档 markdown 内容
    与 profile_loader.py 的 _parse_markdown_tables 解析格式一致
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    usd_cny = holdings_data["meta"].get("usd_cny", 6.796)
    hkd_cny = holdings_data["meta"].get("hkd_cny", 0.868)

    lines = []
    lines.append(f"# 个人画像归档 - {today}")
    lines.append("")

    # ── 投资持仓概览 ──
    lines.append("## 投资持仓概览")
    lines.append("")

    # --- 加密货币 ---
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    btc_qty = summary["btc_qty"]
    btc_price = f"${summary['btc_price']:,.2f}" if summary["btc_price"] else "$58,644.00"
    btc_market = f"¥{summary['btc_market_cny']:,.0f}" if summary["btc_market_cny"] else "¥51,733"
    btc_storage = summary["btc_storage"] or "链上钱包"
    lines.append(f"| BTC(链上) | {btc_qty:.8f} | {btc_price} | {btc_market} | {btc_storage} |")

    usdt_amt = summary["usdt_amount"]
    usdt_str = f"${usdt_amt:,.0f}" if usdt_amt else "—"
    lines.append(f"| USDT(币安) | — | — | {usdt_str} | 韩伟蒙古币安 |")
    lines.append(f"| ETH | — | — | — | {summary['eth_note']} |")
    lines.append("")

    # --- 美股 ---
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    crcl_qty = summary["crcl_total_qty"]
    crcl_price = summary["crcl_price"]
    crcl_market = summary["crcl_market_cny"]
    crcl_price_str = f"${crcl_price:.2f}" if crcl_price else "$62.63"
    crcl_market_str = f"¥{crcl_market:,.0f}" if crcl_market else "¥392,144"
    lines.append(f"| Circle(CRCL合计) | {crcl_qty:.1f} | {crcl_price_str} | {crcl_market_str} | 分散多账户 |")

    for s in summary["us_stocks"]:
        price_str = f"${s['price']:.2f}" if s['price'] else ""
        market_str = f"¥{s['market_cny']:,.0f}" if s['market_cny'] else ""
        # 已清仓的标的用备注
        note = ""
        note_text = holdings_data["holdings"]
        for h in note_text:
            if h.get("symbol") == s["symbol"] and h.get("quantity", 0) == 0:
                note = " (已清仓)"
                break
        lines.append(f"| {s['name']}{note} | {s['qty']} | {price_str} | {market_str} | {s['storage']} |")

    lines.append("")

    # --- 港股 ---
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) |")
    lines.append("|------|------|-------|-----------|")

    if summary["hk_stocks"]:
        for s in summary["hk_stocks"]:
            price_str = f"${s['price']:.2f}" if s['price'] else ""
            market_str = f"¥{s['market_cny']:,.0f}" if s['market_cny'] else ""
            lines.append(f"| {s['name']} | {s['qty']} | {price_str} | {market_str} |")
    else:
        lines.append("| 优必选(9880.HK) | 50 | $12.64 | ¥4,295 |")
    lines.append("")

    # --- TS时间代币 ---
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")

    if summary["ts_tokens"]:
        for t in summary["ts_tokens"]:
            market_str = f"¥{t['market_cny']:,.0f}" if t['market_cny'] else ""
            lines.append(f"| {t['label']} | {t['qty']} | {market_str} |")
    else:
        lines.append("| xiaoan | 106,499秒 | ¥15,604 |")
        lines.append("| wufan | 818秒 | ¥16,177 |")
    lines.append("")

    # --- 关键指标 ---
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")

    total_assets = report_metrics.get("总资产", "¥1,401,580")
    net_assets = report_metrics.get("净资产", "¥1,001,580")
    invest_assets = report_metrics.get("投资总资产", "¥569,658")
    cash_cny = f"¥{summary['cash_cny']:,}" if summary['cash_cny'] else "¥630,808"
    usdt_str = f"${summary['usdt_amount']:,.0f}" if summary['usdt_amount'] else "$10,940"
    hkd_str = f"HK${summary['cash_hkd']:,.0f} (≈¥{int(summary['cash_hkd'] * hkd_cny):,})" if summary['cash_hkd'] else "HK$146,060 (≈¥126,767)"

    lines.append(f"| 总资产 | {total_assets} |")
    lines.append(f"| 净资产 | {net_assets} |")
    lines.append(f"| 投资总资产 | {invest_assets} |")
    lines.append(f"| 家庭备用金 | {cash_cny} |")
    lines.append(f"| HK打新资金 | {hkd_str} |")
    lines.append(f"| 信用卡负债 | ¥{summary['credit_card_debt']:,} |" if summary['credit_card_debt'] else "| 信用卡负债 | ¥400,000 |")

    # BTC占比
    invest_total = summary["investment_total_cny"]
    btc_market = summary["btc_market_cny"]
    btc_pct = round(btc_market / invest_total * 100, 1) if invest_total > 0 and btc_market > 0 else 9.1
    lines.append(f"| BTC占投资比 | {btc_pct}% |")

    # CRCL集中度
    crcl_market = summary["crcl_market_cny"]
    crcl_pct = round(crcl_market / invest_total * 100, 1) if invest_total > 0 and crcl_market > 0 else 68.8
    lines.append(f"| CRCL集中度 | {crcl_pct}% ⚠️ |")

    # 房贷
    mortgage_parts = []
    if summary["mortgage_commercial"]:
        mortgage_parts.append(f"¥{summary['mortgage_commercial']:,}")
    if summary["mortgage_fund"]:
        mortgage_parts.append(f"¥{summary['mortgage_fund']:,}")
    mortgage_str = "+".join(mortgage_parts) if mortgage_parts else "¥400,000+¥1,400,000"
    lines.append(f"| 房贷总额 | {mortgage_str} |")
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
    lines.append(f"| BTC目标 | 2.32个 (当前{btc_qty:.3f}, 进度{btc_qty/2.32*100:.1f}%) |")
    lines.append("| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")
    lines.append("| 当前状态 | BTC在MA120下方, 定投暂存USDT待命 |")
    lines.append("")

    # ── 本次更新变更记录 ──
    now_iso = datetime.datetime.now().isoformat()
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    lines.append(f"| profile.last_sync | — | {now_iso} | 自动归档 |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# 6. 写入归档
# ======================================================================

def write_archive(content: str, archive_dir: Path, today_str: str) -> Path:
    """将内容写入 profile_archive/"""
    archive_dir.mkdir(parents=True, exist_ok=True)
    filepath = archive_dir / f"profile_{today_str}.md"
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"已写入: {filepath}")
    return filepath


# ======================================================================
# 7. 清理旧归档（保留最近 30 天）
# ======================================================================

def cleanup_old_archives(archive_dir: Path, keep_days: int = 30):
    """删除超过 keep_days 天的旧归档文件"""
    if not archive_dir.exists():
        return

    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    deleted = 0

    for fpath in archive_dir.glob("profile_*.md"):
        m = re.search(r"profile_(\d{8})\.md", fpath.name)
        if m:
            try:
                file_date = datetime.datetime.strptime(m.group(1), "%Y%m%d")
                if file_date < cutoff:
                    fpath.unlink()
                    deleted += 1
            except (ValueError, OSError) as e:
                logger.warning(f"清理归档失败: {fpath} - {e}")

    if deleted:
        logger.info(f"已清理 {deleted} 个旧归档 ({keep_days}天前)")


# ======================================================================
# 8. 主流程
# ======================================================================

def main() -> int:
    global logger
    # 检查 --verbose 参数
    verbose = "--verbose" in sys.argv
    logger = setup_logger(verbose)

    logger.info("=" * 50)
    logger.info("开始每日个人画像归档同步")

    today_str = datetime.date.today().strftime("%Y%m%d")

    try:
        # 1. 读取投资持仓
        logger.info("步骤1: 读取 holdings.yaml ...")
        holdings_data = load_holdings()
        logger.info(f"  共 {len(holdings_data['holdings'])} 项持仓")

        # 2. 读取最新月度报告
        logger.info("步骤2: 读取最新月度报告 ...")
        report_path = get_latest_report_path()
        logger.info(f"  报告: {report_path.name}")
        report_metrics = parse_report_metrics(report_path)
        logger.info(f"  提取 {len(report_metrics)} 个指标")

        # 3. 读取职业发展档案
        logger.info("步骤3: 读取职业发展档案 ...")
        career_profile = load_career_profile()
        logger.info(f"  公司: {career_profile.get('company')}, 角色: {career_profile.get('role')}")

        # 4. 计算持仓汇总
        logger.info("步骤4: 计算持仓汇总 ...")
        summary = compute_holdings_summary(holdings_data)
        logger.info(f"  CRCL合计: {summary['crcl_total_qty']:.1f}股, 美股: {len(summary['us_stocks'])}项")

        # 5. 构建归档内容
        logger.info("步骤5: 构建归档内容 ...")
        content = build_archive_content(holdings_data, report_metrics, career_profile, summary)

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
        # 错误时也输出到 stdout
        print(f"[ERROR] 归档同步失败: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())