#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_profile_to_config.py
每天0点自动同步投资持仓 + 职业发展档案 → 飞书推送系统 config.yaml
静默完成，异常时记录日志
"""

import yaml
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from copy import deepcopy

# ── 路径配置 ──
HOLDINGS_PATH = Path(r"E:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\research\portfolio\holdings.yaml")
REPORTS_DIR = Path(r"E:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\research\portfolio\reports")
CAREER_FILE = Path(r"E:\ProjectGroup\AI\ContextStack\02-Knowledge\career-development\career-strategy\个人职业发展分析-端侧AI企业定制攻略.md")
CONFIG_PATH = Path(r"E:\ProjectGroup\AI\ContextStack\02-Knowledge\skills\1.trae-feishu-push\config.yaml")
HOUR_ARCHIVE_DIR = Path(r"E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\0.trae-feishu-push-hour\profile_archive")
DAY_ARCHIVE_DIR = Path(r"E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\1.trae-feishu-push-day\profile_archive")
LOG_FILE = Path(r"E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\sync_profile.log")

USD_CNY = 6.796
HKD_CNY = 0.866


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_yaml(path: Path) -> dict:
    if not path.exists():
        log(f"文件不存在: {path}", "WARN")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def find_latest_report(reports_dir: Path) -> Path:
    """找到最新月份的报告文件"""
    if not reports_dir.exists():
        return None
    reports = list(reports_dir.glob("家庭资产报告-*.md"))
    if not reports:
        return None
    # 按文件名中的日期排序
    def extract_date(p):
        m = re.search(r"(\d{4}-\d{2})", p.stem)
        return m.group(1) if m else "0000-00"
    reports.sort(key=extract_date, reverse=True)
    return reports[0]


def parse_report_totals(report_path: Path) -> dict:
    """从报告Markdown中提取总资产等关键数字"""
    if not report_path or not report_path.exists():
        return {}
    text = report_path.read_text(encoding="utf-8")
    result = {}

    # 提取表格行中的总资产/净资产/投资总资产
    m = re.search(r"\|\s*\*\*总资产\*\*\s*\|\s*\*\*¥([\d,]+)\*\*", text)
    if m:
        result["total_assets"] = m.group(1)

    m = re.search(r"\|\s*\*\*净资产\*\*\s*\|\s*\*\*¥([\d,]+)\*\*", text)
    if m:
        result["net_assets"] = m.group(1)

    m = re.search(r"\|\s*\*\*投资总资产\*\*\s*\|\s*\*\*¥([\d,]+)\*\*", text)
    if m:
        result["investment_assets"] = m.group(1)

    # 提取 USD/CNY 汇率
    m = re.search(r"USD/CNY=([\d.]+)", text)
    if m:
        result["usd_cny"] = m.group(1)
        global USD_CNY
        try:
            USD_CNY = float(m.group(1))
        except ValueError:
            pass

    # 提取 HKD/CNY 汇率
    m = re.search(r"HKD/CNY=([\d.]+)", text)
    if m:
        result["hkd_cny"] = m.group(1)
        global HKD_CNY
        try:
            HKD_CNY = float(m.group(1))
        except ValueError:
            pass

    return result


def extract_holdings_profile(holdings: dict) -> dict:
    """从holdings.yaml提取config需要的资产概要"""
    if not holdings:
        return {}

    profile = {
        "crypto": {},
        "stocks": {"us": [], "hk": []},
        "ts_tokens": {},
        "real_estate": [],
        "cash": "",
        "crcl_concentration": "",
        "key_indicators": {},
    }

    crcl_total_qty = 0
    crcl_price = 0
    investment_total_cny = 0
    btc_market_cny = 0
    crcl_market_cny = 0

    holdings_list = holdings.get("holdings", [])
    for h in holdings_list:
        cat = h.get("category", "")
        symbol = h.get("symbol", "")
        qty = h.get("quantity", 0)
        price = h.get("manual_price_usd", 0)
        market_val_cny = qty * price * USD_CNY

        if cat == "crypto":
            if symbol == "BTC":
                btc_market_cny = market_val_cny
                investment_total_cny += market_val_cny
                profile["crypto"]["btc"] = {
                    "qty": f"{qty:.4f}",
                    "price_usd": f"${price:,.2f}",
                    "market_cny": f"¥{market_val_cny:,.0f}",
                    "storage": "链上钱包",
                }

        elif cat in ("us_stock", "us_stock_tokenized"):
            investment_total_cny += market_val_cny
            if symbol == "CRCL":
                crcl_total_qty += qty
                crcl_price = price
                crcl_market_cny += market_val_cny
            else:
                profile["stocks"]["us"].append({
                    "symbol": symbol,
                    "name": h.get("name", symbol),
                    "qty": qty,
                    "price_usd": price,
                    "market_cny": market_val_cny,
                    "storage": h.get("storage", ""),
                })
        elif cat == "hk_stock":
            investment_total_cny += market_val_cny
            h_name = h.get("name", symbol)
            display_name = re.sub(r"\(.*?\)", "", h_name).strip()
            profile["stocks"]["hk"].append({
                "symbol": symbol,
                "name": display_name,
                "qty": qty,
                "price_usd": price,
                "market_cny": market_val_cny,
            })

        elif cat == "ts_time_token":
            investment_total_cny += market_val_cny
            if symbol == "XIAOAN":
                profile["ts_tokens"]["xiaoan"] = {
                    "qty": f"{qty:,}秒",
                    "market_cny": f"¥{market_val_cny:,.0f}",
                }
            elif symbol == "WUFAN":
                profile["ts_tokens"]["wufan"] = {
                    "qty": f"{qty}秒",
                    "market_cny": f"¥{market_val_cny:,.0f}",
                }

    # ETH状态检测
    has_eth = any(h.get("symbol") == "ETH" and h.get("quantity", 0) > 0 for h in holdings_list)
    if has_eth:
        profile["crypto"]["eth"] = {"status": "有持仓"}
    else:
        yaml_text = HOLDINGS_PATH.read_text(encoding="utf-8")
        if "eth" in yaml_text.lower() and "清仓" in yaml_text:
            profile["crypto"]["eth"] = {"status": "已清仓 (2026-06-24)"}

    # CRCL汇总 + 集中度
    if crcl_total_qty > 0:
        crcl_summary = {
            "symbol": "CRCL",
            "name": "Circle",
            "total_qty": crcl_total_qty,
            "total_market_cny": crcl_market_cny,
            "price_usd": crcl_price,
        }
        profile["stocks"]["crcl_summary"] = crcl_summary
        if investment_total_cny > 0 and crcl_price > 0:
            pct = crcl_market_cny / investment_total_cny * 100
            profile["crcl_concentration"] = f"CRCL {crcl_total_qty:.1f}股, 占投资约{pct:.0f}% ⚠️ 高度集中"

    # USDT余额
    cash_list = holdings.get("cash", [])
    usdt_balance = 0
    cny_cash = 0
    hkd_cash = 0
    for c in cash_list:
        name = c.get("name", "")
        if "USDT" in name:
            usdt_balance = c.get("amount_usd", 0)
        elif "备用金" in name:
            cny_cash = c.get("amount_cny", 0)
        elif "打新" in name:
            hkd_cash = c.get("amount_hkd", 0)

    profile["crypto"]["usdt"] = {"balance": f"${usdt_balance:,.0f}", "storage": "韩伟蒙古币安"}
    profile["cash"] = f"¥{cny_cash:,.0f} (家庭备用金) + HK${hkd_cash:,.0f} (打新资金) + ${usdt_balance:,.0f} (币安USDT)"

    # 固定资产
    fixed = holdings.get("fixed_assets", [])
    for fa in fixed:
        profile["real_estate"].append(f"{fa['name']} ¥{fa['value_cny']//10000:,}W ({fa.get('note', '')})")

    # 关键指标
    liabilities = holdings.get("liabilities", [])
    credit_card_debt = 0
    for li in liabilities:
        if "信用卡" in li.get("name", ""):
            credit_card_debt = li.get("amount_cny", 0)
    profile["key_indicators"] = {
        "btc_ratio": f"{btc_market_cny / investment_total_cny * 100:.1f}%" if investment_total_cny else "N/A",
        "crcl_ratio": f"{crcl_market_cny / investment_total_cny * 100:.0f}%" if investment_total_cny else "N/A",
        "credit_card_debt": credit_card_debt,
    }

    return profile


def extract_career_profile(career_text: str) -> dict:
    """从职业发展文档提取关键画像"""
    profile = {}

    # 提取技能栈 - 表格中查找
    m = re.search(r"技能栈\s*\|\s*(.+?)\s*\|", career_text)
    if m:
        skills_raw = m.group(1).strip()
        skills_raw = skills_raw.replace("**", "")
        skills = re.split(r"[、,]", skills_raw)
        skills = [s.strip() for s in skills if s.strip()]
        profile["skills"] = skills

    # 提取S级能力（核心能力）
    m = re.search(r"S级能力\s*\|\s*(.+?)\s*\|", career_text)
    if m:
        core_raw = m.group(1).strip()
        core_raw = core_raw.replace("**", "")
        profile["core_skills"] = core_raw

    # 提取目标公司
    target_companies = []
    for m in re.finditer(r"\*\*(小米|地平线|寒武纪|百度|字节跳动|联想|滴滴|美团|京东方|理想汽车|石头科技|北汽新能源|三一重工)\*\*", career_text):
        company = m.group(1)
        if company not in target_companies:
            target_companies.append(company)
    if target_companies:
        profile["target_companies"] = target_companies

    # 提取聚焦领域
    m = re.search(r"行业聚焦\s*\|\s*(.+?)\s*\|", career_text)
    if m:
        focus = m.group(1).strip()
        focus = focus.replace("**", "")
        profile["focus"] = focus

    # 提取地点约束
    m = re.search(r"地点约束\s*\|\s*\*\*(.+?)\*\*", career_text)
    if m:
        loc = m.group(1).strip()
        loc = re.sub(r"[，,]\s*优先\s*", "", loc)
        loc = loc.replace("，", "").replace(",", "")
        profile["location_constraint"] = loc

    # 提取求职状态
    m = re.search(r"求职周期\s*\|\s*(.+?)\s*\|", career_text)
    if m:
        profile["job_search_status"] = m.group(1).strip()

    # 提取薪资范围
    m = re.search(r"¥([\d\-]+W?)\s*总包", career_text)
    if m:
        profile["salary"] = f"当前30K×16, 目标{m.group(1)}总包"

    # 提取面试方法
    m = re.search(r"本质→实践→踩坑→思考", career_text)
    if m:
        profile["interview_method"] = "工程叙事四层结构: 本质→实践→踩坑→思考"

    return profile


def build_recent_trades(holdings: dict) -> list:
    """从holdings.yaml注释和note中提取近期交易"""
    trades = []
    seen = set()

    # 从注释中提取清仓记录
    yaml_text = HOLDINGS_PATH.read_text(encoding="utf-8")
    for m in re.finditer(r"# (.+?\s*(?:清仓|买入|卖出|建仓|加仓)\s*.+)", yaml_text):
        line = m.group(1).strip()
        if line and line not in seen:
            trades.append(line)
            seen.add(line)

    # 从活跃持仓note中提取近期交易
    for h in holdings.get("holdings", []):
        note = h.get("note", "")
        if note and ("2026-06" in note or "2026-07" in note):
            line = f"{h.get('symbol', '')}: {note}"
            if line not in seen:
                trades.append(line)
                seen.add(line)

    return trades[:15]


def deep_compare(old_val, new_val, path=""):
    """比较两个值，返回变更列表"""
    changes = []
    if isinstance(new_val, dict) and isinstance(old_val, dict):
        for k in set(list(old_val.keys()) + list(new_val.keys())):
            sub = deep_compare(old_val.get(k), new_val.get(k), f"{path}.{k}" if path else k)
            changes.extend(sub)
    elif isinstance(new_val, list) and isinstance(old_val, list):
        if old_val != new_val:
            changes.append(path)
    elif old_val != new_val:
        changes.append(path)
    return changes


def update_config(config: dict, holdings_profile: dict, report_totals: dict,
                  career_profile: dict, recent_trades: list) -> tuple:
    """更新config.yaml，返回(新config, 变更列表)"""
    old_profile = deepcopy(config.get("profile", {}))
    changes = []

    if "profile" not in config:
        config["profile"] = {}

    p = config["profile"]

    # ── 资产数据 ──
    if "assets" not in p:
        p["assets"] = {}

    a = p["assets"]

    # crypto
    a["crypto"] = holdings_profile.get("crypto", {})
    a["stocks"] = holdings_profile.get("stocks", {})
    a["ts_tokens"] = holdings_profile.get("ts_tokens", {})

    if holdings_profile.get("real_estate"):
        a["real_estate"] = holdings_profile["real_estate"][0] if len(holdings_profile["real_estate"]) == 1 else holdings_profile["real_estate"]

    a["cash"] = holdings_profile.get("cash", "")
    a["crcl_concentration"] = holdings_profile.get("crcl_concentration", "")
    a["key_indicators"] = holdings_profile.get("key_indicators", {})

    if report_totals.get("total_assets"):
        if report_totals.get("net_assets"):
            a["total_assets"] = f"¥{report_totals['total_assets']} (净资产 ¥{report_totals['net_assets']})"
        else:
            a["total_assets"] = f"¥{report_totals['total_assets']}"
    if report_totals.get("investment_assets"):
        a["investment_assets"] = f"¥{report_totals['investment_assets']}"

    # ── 负债 ──
    holdings_data = load_yaml(HOLDINGS_PATH)
    liabilities = holdings_data.get("liabilities", [])
    if "liabilities" not in a:
        a["liabilities"] = {}
    a_liab = a["liabilities"]
    if liabilities:
        name_to_key = {
            "房贷—商贷": "mortgage_commercial",
            "房贷—公积金": "mortgage_fund",
            "信用卡循环(投资WEB3)": "credit_card_invest",
            "币安BTC质押借贷": "binance_loan",
        }
        default_suffix = {
            "房贷—商贷": " (自住)",
            "房贷—公积金": " (自住)",
            "信用卡循环(投资WEB3)": " (投资WEB3)",
            "币安BTC质押借贷": " (2026-06-05已全部还清)",
        }
        for li in liabilities:
            name = li.get("name", "")
            key = name_to_key.get(name, name)
            amt_cny = li.get("amount_cny", None)
            amt_usd = li.get("amount_usd", None)
            if amt_cny is not None:
                val = f"¥{amt_cny:,.0f}"
            elif amt_usd is not None:
                val = f"${amt_usd:,.0f}"
            else:
                continue
            if li.get("note"):
                val += f" ({li['note']})"
            else:
                val += default_suffix.get(name, "")
            a_liab[key] = val

    # ── 职业画像 (experience不覆盖, 因config中已基于简历核实为~3年, 职业文档含冲突的9年) ──
    for key in ("role", "skills", "core_skills", "focus", "salary",
                "target_companies", "location_constraint", "job_search_status",
                "interview_method"):
        if career_profile.get(key):
            p.setdefault("career", {})[key] = career_profile[key]

    # ── 近期交易 ──
    if recent_trades:
        p["recent_trades"] = recent_trades

    # ── last_sync ──
    now = datetime.now().isoformat()
    p["last_sync"] = now

    # ── 对比差异 ──
    changes = deep_compare(old_profile, p, "profile")

    return config, changes


def generate_archive_table(holdings_profile: dict, report_totals: dict,
                            career_data: dict, config: dict, changes: list,
                            date_str: str) -> str:
    """生成归档Markdown内容（表格格式，与现有归档一致）"""
    today_display = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# 个人画像归档 - {today_display}",
        "",
        "## 投资持仓概览",
        "",
    ]

    # ── 加密货币 ──
    crypto = holdings_profile.get("crypto", {})
    if crypto:
        lines.append("### 加密货币")
        lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
        lines.append("|------|------|------------|-----------|------|")
        if "btc" in crypto:
            b = crypto["btc"]
            lines.append(f"| BTC(链上) | {b['qty']} | {b['price_usd']} | {b['market_cny']} | {b['storage']} |")
        if "usdt" in crypto:
            u = crypto["usdt"]
            lines.append(f"| USDT(币安) | — | — | {u['balance']} | {u['storage']} |")
        if "eth" in crypto:
            e = crypto["eth"]
            lines.append(f"| ETH | — | — | — | {e.get('status', '')} |")
        lines.append("")

    # ── 美股 ──
    stocks = holdings_profile.get("stocks", {})
    all_us_stocks = []

    # CRCL汇总
    crcl_summary = stocks.get("crcl_summary")
    if crcl_summary:
        all_us_stocks.append({
            "name": "Circle(CRCL合计)",
            "qty": f"{crcl_summary['total_qty']:.1f}",
            "price_usd": f"${crcl_summary['price_usd']:.2f}",
            "market_cny": f"¥{crcl_summary['total_market_cny']:,.0f}",
            "storage": "分散多账户",
        })

    # 其他美股
    for s in stocks.get("us", []):
        all_us_stocks.append({
            "name": s.get("name", s.get("symbol", "")),
            "qty": f"{s['qty']}",
            "price_usd": f"${s['price_usd']:.2f}" if isinstance(s['price_usd'], (int, float)) else s['price_usd'],
            "market_cny": f"¥{s['market_cny']:,.0f}",
            "storage": s.get("storage", ""),
        })

    if all_us_stocks:
        lines.append("### 美股")
        lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
        lines.append("|------|------|------------|-----------|------|")
        for s in all_us_stocks:
            lines.append(f"| {s['name']} | {s['qty']} | {s['price_usd']} | {s['market_cny']} | {s['storage']} |")
        lines.append("")

    # ── 港股 ──
    hk_stocks = stocks.get("hk", [])
    if hk_stocks:
        lines.append("### 港股")
        lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) |")
        lines.append("|------|------|-------|-----------|")
        for s in hk_stocks:
            lines.append(f"| {s['name']} | {s['qty']} | ${s['price_usd']:.2f} | ¥{s['market_cny']:,.0f} |")
        lines.append("")

    # ── TS时间代币 ──
    ts = holdings_profile.get("ts_tokens", {})
    if ts:
        lines.append("### TS时间代币")
        lines.append("| 标的 | 数量 | 市值(CNY) |")
        lines.append("|------|------|-----------|")
        for k, v in ts.items():
            lines.append(f"| {k} | {v['qty']} | {v['market_cny']} |")
        lines.append("")

    # ── 关键指标 ──
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总资产 | ¥{report_totals.get('total_assets', 'N/A')} |")
    lines.append(f"| 净资产 | ¥{report_totals.get('net_assets', 'N/A')} |")
    lines.append(f"| 投资总资产 | ¥{report_totals.get('investment_assets', 'N/A')} |")

    # 从config读取家庭备用金和打新资金
    cfg_profile = config.get("profile", {})
    cfg_assets = cfg_profile.get("assets", {})
    cash_str = holdings_profile.get("cash", "")
    # 提取备用金部分（不含括号后缀）
    cash_simple = cash_str.split("(")[0].strip() if "(" in cash_str else cash_str
    lines.append(f"| 家庭备用金 | {cash_simple} |")

    # 从指标中提取
    indicators = holdings_profile.get("key_indicators", {})
    if indicators.get("credit_card_debt"):
        lines.append(f"| 信用卡负债 | ¥{indicators['credit_card_debt']:,} |")
    if indicators.get("btc_ratio"):
        lines.append(f"| BTC占投资比 | {indicators['btc_ratio']} |")
    if indicators.get("crcl_ratio"):
        lines.append(f"| CRCL集中度 | {indicators['crcl_ratio']} ⚠️ |")

    # 房贷
    liab = cfg_assets.get("liabilities", {})
    if liab.get("mortgage_commercial") or liab.get("mortgage_fund"):
        lines.append(f"| 房贷总额 | 商贷+公积金 |")
    lines.append("")

    # ── 职业发展画像 ──
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")

    # 从config中读取职业信息（config保留简历核实版本）
    cfg_career = cfg_profile.get("career", {})
    lines.append(f"| 当前公司 | 新华三 |")
    lines.append(f"| 当前角色 | {cfg_career.get('role', '嵌入式开发工程师')} |")
    lines.append(f"| 经验 | {cfg_career.get('experience', '~3年嵌入式产品开发经验(新华三) + 爱博精电6年工业仪表/DSP基础')} |")
    lines.append(f"| 技能栈 | {', '.join(cfg_career.get('skills', ['C语言', 'ARM/DSP架构', 'RTOS', 'Linux', 'Python', 'TFLM']))} |")

    core_skills = cfg_career.get('core_skills', '')
    if core_skills:
        lines.append(f"| 核心能力 | {core_skills} |")
    lines.append(f"| 行业聚焦 | {cfg_career.get('focus', '工业嵌入式、通信设备底层，非消费电子')} |")
    lines.append(f"| 地点约束 | {cfg_career.get('location_constraint', '北京/海淀/昌平')} |")
    lines.append(f"| 当前薪资 | {cfg_career.get('salary', '30K×16')} |")
    lines.append(f"| 目标薪资 | 50-70W总包 |")
    lines.append(f"| 求职状态 | {cfg_career.get('job_search_status', '已约1年，面试过九号/ISHO/思朗')} |")

    im = cfg_career.get('interview_method', '')
    if im:
        lines.append(f"| 面试方法论 | {im} |")

    target_companies = cfg_career.get('target_companies', [])
    if target_companies:
        lines.append(f"| 目标公司 | {'、'.join(target_companies)} |")
    lines.append("")

    # ── 家庭与保险 ──
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")

    cfg_family = cfg_profile.get("family", {})
    lines.append(f"| 居住地 | {cfg_family.get('location', '北京')} |")
    lines.append(f"| 户籍 | {cfg_family.get('hukou', '非京籍(内蒙古)')} |")
    lines.append(f"| 子女 | {cfg_family.get('children', '有孩子(在京上学)')} |")
    lines.append(f"| 配偶 | {cfg_family.get('spouse', '已婚(薛燕)')} |")

    real_estate = holdings_profile.get("real_estate", [])
    if real_estate:
        for re_item in real_estate:
            lines.append(f"| 房产 | {re_item} |")

    cfg_insurance = cfg_profile.get("insurance", {})
    for k, v in cfg_insurance.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # ── A8计划进度 ──
    a8_plan = cfg_profile.get("a8_plan", {})
    if a8_plan:
        lines.append("## A8计划进度")
        lines.append("")
        lines.append("| 指标 | 进度 |")
        lines.append("|------|------|")
        lines.append(f"| 目标 | {a8_plan.get('target', 'N/A')} |")
        lines.append(f"| BTC目标 | {a8_plan.get('btc_target', 'N/A')} |")
        lines.append(f"| 策略 | {a8_plan.get('strategy', 'N/A')} |")
        lines.append(f"| 当前状态 | {a8_plan.get('current_mode', 'N/A')} |")
        lines.append("")

    # ── 本次更新变更记录 ──
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")

    # last_sync变更
    old_sync = cfg_profile.get("last_sync", "")
    new_sync = datetime.now().isoformat()
    lines.append(f"| config.last_sync | {old_sync} | {new_sync} | 同步时间戳 |")

    if changes:
        for c in changes:
            # 尝试提取旧值和新值
            parts = c.split(".")
            field_name = parts[-1] if len(parts) > 1 else c
            lines.append(f"| {c} | — | — | 字段已更新 |")
    else:
        lines.append("| 数据源 | holdings.yaml | — | 投资持仓数据无变化 |")
        lines.append("| 数据源 | 职业发展档案 | — | 职业画像数据无变化 |")
        lines.append("| 数据源 | 最新月度报告 | — | 资产报告数据无变化 |")

    lines.append("")
    return "\n".join(lines)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"===== 开始同步个人画像 ({today}) =====")

    try:
        # 1. 读取投资持仓
        log("读取 holdings.yaml ...")
        holdings = load_yaml(HOLDINGS_PATH)
        if not holdings:
            log("holdings.yaml 为空或不存在，跳过", "ERROR")
            sys.exit(1)

        # 2. 读取最新报告
        log("查找最新月度报告 ...")
        report_path = find_latest_report(REPORTS_DIR)
        report_totals = {}
        if report_path:
            log(f"读取报告: {report_path.name}")
            report_totals = parse_report_totals(report_path)
        else:
            log("未找到月度报告", "WARN")

        # 3. 读取职业发展档案
        log("读取职业发展档案 ...")
        career_text = ""
        career_profile = {}
        if CAREER_FILE.exists():
            career_text = CAREER_FILE.read_text(encoding="utf-8")
            career_profile = extract_career_profile(career_text)
        else:
            log("职业发展档案不存在", "WARN")

        # 4. 提取持仓概要
        log("提取持仓概要 ...")
        holdings_profile = extract_holdings_profile(holdings)

        # 5. 提取近期交易
        recent_trades = build_recent_trades(holdings)

        # 6. 更新config.yaml
        log("更新 config.yaml ...")
        config = load_yaml(CONFIG_PATH)
        config, changes = update_config(config, holdings_profile, report_totals,
                                        career_profile, recent_trades)
        save_yaml(CONFIG_PATH, config)
        log(f"config.yaml 已更新, last_sync={config['profile']['last_sync']}")

        # 重新读取更新后的config用于归档（含family/insurance完整信息）
        updated_config = load_yaml(CONFIG_PATH)

        # 7. 生成归档（表格格式）
        archive_content = generate_archive_table(
            holdings_profile, report_totals,
            career_profile, updated_config, changes, today
        )

        # hour归档
        HOUR_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        hour_archive_path = HOUR_ARCHIVE_DIR / f"profile_{today.replace('-', '')}.md"
        hour_archive_path.write_text(archive_content, encoding="utf-8")
        log(f"hour归档已生成: {hour_archive_path.name}")

        # day归档
        DAY_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        day_archive_path = DAY_ARCHIVE_DIR / f"profile_{today.replace('-', '')}.md"
        day_archive_path.write_text(archive_content, encoding="utf-8")
        log(f"day归档已生成: {day_archive_path.name}")

        # 8. 输出变更摘要
        if changes:
            log(f"本次变更字段({len(changes)}): {', '.join(changes[:20])}")
        else:
            log("本次无变更")

        log("===== 同步完成 =====")

    except Exception as e:
        log(f"同步失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()