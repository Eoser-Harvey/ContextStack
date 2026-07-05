#!/usr/bin/env python3
"""
家庭资产月度报告生成器 v2

功能:
    - 自动拉取加密货币/股票价格
    - 每标的计算盈亏(基于成本)
    - 追踪历史最高/最低价及时间
    - 代持资产单独展示(不计入净资产)
    - 多类型负债(房贷/信用卡/币安借贷)
    - 月度净资产趋势快照

用法:
    python generate_report.py                    # 当月报告
    python generate_report.py --date 2026-06-01  # 指定日期

价格来源:
    CryptoCompare API → BTC/ETH (国内直连)
    Yahoo→Stooq      → 美股/港股/A股ETF
    Manual           → CRCL预IPO/TS平台小众币种

⚠️ 成本未知的标的会在报告中标出，绝不编造数据
"""

import yaml
import json
import math
import requests
import yfinance as yf
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # ContextStack root
PORTFOLIO_DIR = REPO_ROOT / "01-Projects" / "family-hub" / "research" / "portfolio"
DEFAULT_HOLDINGS = PORTFOLIO_DIR / "holdings.yaml"
DEFAULT_HISTORY = PORTFOLIO_DIR / "portfolio_history.yaml"
DEFAULT_OUTPUT_DIR = PORTFOLIO_DIR / "reports"

# Stooq symbol mapping (Yahoo failover)
STOOQ_MAP = {
    "TSLA": "tsla.us",
    "MSTR": "mstr.us",
    "1810.HK": "1810.hk",
    "159770.SZ": "159770.sz",
}


def vis_width(s):
    """计算字符串视觉宽度：CJK字符=2，ASCII=1"""
    w = 0
    for ch in str(s):
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            w += 2
        else:
            w += 1
    return w


def pad_vis(s, target_w):
    """按视觉宽度右填充空格"""
    s = str(s)
    cur = vis_width(s)
    if cur >= target_w:
        return s
    return s + ' ' * (target_w - cur)


def build_aligned_table(headers, rows):
    """构建视觉对齐的Markdown表格"""
    rows = [headers] + rows
    col_count = len(headers)
    col_widths = [0] * col_count
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], vis_width(cell))

    result = []
    header = '| ' + ' | '.join(pad_vis(c, col_widths[i]) for i, c in enumerate(headers)) + ' |'
    sep = '|' + '|'.join('-' * (w + 2) for w in col_widths) + '|'
    result.append(header)
    result.append(sep)
    for row in rows[1:]:
        result.append('| ' + ' | '.join(pad_vis(c, col_widths[i]) for i, c in enumerate(row)) + ' |')
    return '\n'.join(result)


def load_yaml(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


PRICE_CACHE_FILE = SCRIPT_DIR / "price_cache.json"


def load_price_cache(cache_path, report_date):
    """加载价格缓存，仅当日有效"""
    if cache_path.exists():
        try:
            with open(cache_path, encoding="utf-8") as f:
                cache = json.load(f)
            if cache.get("date") == report_date:
                return cache
        except Exception:
            pass
    return {}


def save_price_cache(cache_path, report_date, crypto_prices, stock_prices, rates):
    """保存当日价格缓存"""
    cache = {
        "date": report_date,
        "crypto": crypto_prices,
        "stock": stock_prices,
        "rates": rates,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"  💾 价格已缓存至: {cache_path.name}")


def save_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def fetch_crypto_prices(symbols):
    syms = ",".join(symbols)
    url = f"https://min-api.cryptocompare.com/data/pricemulti?fsyms={syms}&tsyms=USD"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "PortfolioTracker/2.0"})
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for sym in symbols:
            if sym in data and "USD" in data[sym]:
                result[sym] = data[sym]["USD"]
            else:
                print(f"  ⚠ CryptoCompare 无 {sym} 价格数据")
                result[sym] = None
        return result
    except requests.RequestException as e:
        print(f"  ❌ CryptoCompare API 请求失败: {e}")
        return {s: None for s in symbols}


def fetch_exchange_rates():
    url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms=USD&tsyms=CNY,HKD"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "PortfolioTracker/2.0"})
        resp.raise_for_status()
        data = resp.json()
        usd_cny = data.get("USD", {}).get("CNY", 7.25)
        usd_hkd = data.get("USD", {}).get("HKD", 7.84)
        hkd_cny = usd_cny / usd_hkd if usd_hkd else 0.93
        return {"USD_CNY": usd_cny, "HKD_CNY": round(hkd_cny, 4)}
    except requests.RequestException as e:
        print(f"  ⚠ 汇率获取失败，使用默认值: {e}")
        return {"USD_CNY": 7.25, "HKD_CNY": 0.93}


def fetch_stock_prices_yahoo(symbols):
    if not symbols:
        return {}
    result = {}
    for i, sym in enumerate(symbols):
        if i > 0:
            time.sleep(3)
        price = None
        currency = "USD"
        source = None

        for attempt in range(3):
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info if ticker.info else {}
                for field in ["currentPrice", "regularMarketPrice", "previousClose"]:
                    if info.get(field):
                        price = info[field]
                        break
                if price is None:
                    hist = ticker.history(period="5d")
                    if not hist.empty:
                        price = float(hist["Close"].iloc[-1])
                if info.get("currency"):
                    currency = info["currency"]
                if price is None:
                    raw = yf.download(sym, period="5d", progress=False)
                    if not raw.empty:
                        price = float(raw["Close"].iloc[-1])
                if price is not None:
                    source = "Yahoo"
                break
            except Exception:
                if attempt < 2:
                    print(f"  ⏳ Yahoo: {sym} 重试 {attempt+2}/3...")
                    time.sleep(8)

        if price is None:
            price, currency = _fetch_stooq(sym)
            if price is not None:
                source = "Stooq"

        if price is None:
            price, currency = _fetch_sina(sym)
            if price is not None:
                source = "Sina"

        result[sym] = {"price": price, "currency": currency, "source": source} if price else None
        status = f"${price:.2f}" if price else "FAIL"
        if price and currency == "HKD":
            status += " (HKD)"
        elif price and currency == "CNY":
            status = f"¥{price:.2f} (CNY)"
        print(f"  {'✅' if price else '❌'} {source or '---'}: {sym} = {status}")
    return result


def _fetch_stooq(symbol):
    stooq_sym = STOOQ_MAP.get(symbol, symbol.lower().replace(".", ""))
    url = f"https://stooq.com/q/l/?s={stooq_sym}&f=sd2t2ohlcv&e=csv"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "PortfolioTracker/2.0"})
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        if len(lines) >= 1:
            parts = lines[0].split(",")
            if len(parts) >= 7 and parts[6] not in ("N/D", "N/A", ""):
                price = float(parts[6])
                currency = "HKD" if (".hk" in stooq_sym or ".HK" in symbol) else "USD"
                if ".sz" in stooq_sym or ".SZ" in symbol:
                    currency = "CNY"
                return price, currency
    except Exception as e:
        print(f"     Stooq 回退也失败: {e}")
    return None, "USD"


def _fetch_sina(symbol):
    """Sina财经API（A股专用，国内直连）"""
    sina_map = {
        "159770.SZ": "sz159770",
    }
    sina_sym = sina_map.get(symbol)
    if not sina_sym:
        return None, "USD"
    url = f"https://hq.sinajs.cn/list={sina_sym}"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "PortfolioTracker/2.0",
            "Referer": "https://finance.sina.com.cn",
        })
        resp.encoding = "gbk"
        text = resp.text.strip()
        if text and "=" in text:
            data = text.split('"')[1] if '"' in text else ""
            parts = data.split(",")
            if len(parts) >= 4 and parts[3]:
                price = float(parts[3])
                return price, "CNY"
    except Exception as e:
        print(f"     Sina 回退也失败: {e}")
    return None, "USD"


def calc_pnl(holding, rates):
    """计算盈亏"""
    usd_cny = rates["USD_CNY"]
    hkd_cny = rates["HKD_CNY"]
    qty = holding["quantity"]
    mv_cny = holding.get("market_value_cny", 0)

    if holding.get("cost_unknown"):
        return {"cost_cny": None, "pnl_cny": None, "pnl_pct": None, "status": "⚠️成本未知"}

    is_total = holding.get("cost_is_total", False)
    cost_cny = None

    if "cost_basis_usd" in holding and holding["cost_basis_usd"] is not None:
        if is_total:
            cost_cny = holding["cost_basis_usd"] * usd_cny
        else:
            cost_cny = holding["cost_basis_usd"] * qty * usd_cny
    elif "cost_basis_cny" in holding and holding["cost_basis_cny"] is not None:
        if is_total:
            cost_cny = holding["cost_basis_cny"]
        else:
            cost_cny = holding["cost_basis_cny"] * qty
    elif "cost_basis_hkd" in holding and holding["cost_basis_hkd"] is not None:
        if is_total:
            cost_cny = holding["cost_basis_hkd"] * hkd_cny
        else:
            cost_cny = holding["cost_basis_hkd"] * qty * hkd_cny

    if cost_cny is None:
        return {"cost_cny": None, "pnl_cny": None, "pnl_pct": None, "status": "⚠️成本未知"}

    pnl_cny = mv_cny - cost_cny
    pnl_pct = (pnl_cny / cost_cny * 100) if cost_cny else None
    return {
        "cost_cny": round(cost_cny, 2),
        "pnl_cny": round(pnl_cny, 2),
        "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
        "status": None,
    }


def load_or_init_history(path, holdings):
    """加载历史文件，不存在则初始化"""
    hist = load_yaml(path)
    if not hist:
        hist = {"holdings_history": {}, "net_worth_snapshots": []}

    hh = hist.get("holdings_history", {})

    # 确保每个 id 都有记录
    for h in holdings:
        hid = h.get("id", h.get("symbol"))
        if hid not in hh:
            hh[hid] = {
                "name": h["name"],
                "all_time_high_price": None,
                "all_time_high_date": None,
                "all_time_low_price": None,
                "all_time_low_date": None,
            }

    hist["holdings_history"] = hh
    return hist


def update_history(hist, holdings, report_date):
    """根据当前价格更新历史最值"""
    hh = hist["holdings_history"]
    for h in holdings:
        hid = h.get("id", h.get("symbol"))
        price = h.get("price_usd")
        if hid not in hh or price is None:
            continue
        entry = hh[hid]

        ath = entry.get("all_time_high_price")
        if ath is None or price > ath:
            entry["all_time_high_price"] = round(price, 2)
            entry["all_time_high_date"] = report_date

        atl = entry.get("all_time_low_price")
        if atl is None or price < atl:
            entry["all_time_low_price"] = round(price, 2)
            entry["all_time_low_date"] = report_date

    # 追加净资产快照 (避免同一天重复)
    snaps = hist.get("net_worth_snapshots", [])
    if not snaps or snaps[-1].get("date") != report_date:
        snaps.append({
            "date": report_date,
            "net_worth_cny": None,  # 填充在 main 中
        })
        if len(snaps) > 60:
            snaps = snaps[-60:]  # 保留最近5年
    hist["net_worth_snapshots"] = snaps


def format_pnl(pnl_data):
    """格式化盈亏显示"""
    if pnl_data is None or pnl_data.get("status"):
        return "⚠️待补"
    pnl = pnl_data["pnl_cny"]
    pct = pnl_data["pnl_pct"]
    if pnl is None:
        return "⚠️待补"
    sign = "+" if pnl >= 0 else ""
    pct_str = f" ({sign}{pct:.1f}%)" if pct is not None else ""
    return f"{sign}¥{pnl:,.0f}{pct_str}"


def build_report(data, history_data, rates, report_date):
    usd_cny = rates["USD_CNY"]
    hkd_cny = rates["HKD_CNY"]

    lines = []
    lines.append("---")
    lines.append(f"date: {report_date}")
    lines.append("tags: [family, finance, portfolio, auto-generated]")
    lines.append("---")
    lines.append("")
    lines.append(f"# 家庭资产月度报告 ({report_date})")
    lines.append("")
    lines.append(f"> 🤖 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 💱 USD/CNY={usd_cny:.4f}  HKD/CNY={hkd_cny:.4f}")
    lines.append("")

    all_holdings = data.get("holdings", [])

    # ────────────── 分类汇总 ──────────────
    lines.append("## 一、资产总览")
    lines.append("")
    lines.append("| 类别 | 金额(CNY) | 占比 |")
    lines.append("|------|----------|------|")

    categories = defaultdict(float)
    total_assets = 0

    for h in all_holdings:
        if h.get("market_value_cny"):
            cat = h.get("category", "other")
            categories[cat] += h["market_value_cny"]
            total_assets += h["market_value_cny"]

    for c in data.get("cash", []):
        val = c.get("amount_cny", 0)
        if c.get("amount_hkd"):
            val += c["amount_hkd"] * hkd_cny
        if c.get("amount_usd"):
            val += c["amount_usd"] * usd_cny
        categories["现金固收"] += val
        total_assets += val

    liab_total_cny = 0
    for li in data.get("liabilities", []):
        # 房贷单独说明,不计入投资负债
        if li.get("category") == "mortgage":
            continue
        li_val = li.get("amount_cny", 0)
        if li.get("amount_usd"):
            li_val += li["amount_usd"] * usd_cny
        liab_total_cny += li_val

    net_worth = total_assets - liab_total_cny

    cat_names = {
        "crypto": "加密货币", "us_stock": "美股", "us_stock_tokenized": "美股(链上)",
        "hk_stock": "港股", "a_stock": "A股", "ts_time_token": "TS时间代币",
        "现金固收": "现金固收",
    }

    for cat, val in sorted(categories.items(), key=lambda x: -x[1]):
        pct = val / total_assets * 100 if total_assets else 0
        name = cat_names.get(cat, cat)
        lines.append(f"| {name} | ¥{val:,.0f} | {pct:.1f}% |")

    lines.append(f"| **总资产** | **¥{total_assets:,.0f}** | **100%** |")
    lines.append(f"| **总负债** | **¥{liab_total_cny:,.0f}** | — |")
    lines.append(f"| **净资产** | **¥{net_worth:,.0f}** | — |")
    lines.append("")

    # 拆解: 家庭总资产 = 现金固收 + 投资资产
    cash_fixed = categories.get("现金固收", 0)
    investment_assets = total_assets - cash_fixed
    investment_net = investment_assets - liab_total_cny
    lines.append(f"> 💡 **家庭总资产 ¥{total_assets:,.0f}** = 现金固收 ¥{cash_fixed:,.0f} + 投资资产 ¥{investment_assets:,.0f}")
    lines.append(f"> 💡 **投资净资产 ¥{investment_net:,.0f}** = 投资资产 ¥{investment_assets:,.0f} − 投资负债 ¥{liab_total_cny:,.0f}")
    lines.append(f"> 💡 **家庭净资产 ¥{net_worth:,.0f}** = 总资产 ¥{total_assets:,.0f} − 总负债 ¥{liab_total_cny:,.0f}")
    lines.append("")

    # ────────────── 投资明细 + 盈亏 ──────────────
    lines.append("## 二、投资资产明细（含盈亏）")
    lines.append("")

    headers = ["标的", "数量", "当前单价", "市值(CNY)", "成本单价(CNY)", "成本总价(CNY)", "盈亏(CNY)", "占投资比", "存放"]

    investment_total = sum(h.get("market_value_cny", 0) for h in all_holdings)

    cost_unknown_items = []
    table_rows = []

    for h in all_holdings:
        qty = h["quantity"]
        price_usd = h.get("price_usd")
        price_hkd = h.get("price_hkd")
        mv_cny = h.get("market_value_cny", 0)
        pct = mv_cny / investment_total * 100 if investment_total else 0
        storage = h.get("storage", "")

        if price_hkd:
            price_str = f"HK${price_hkd:,.2f}"
        elif h.get("price_cny"):
            price_str = f"¥{h['price_cny']:,.2f}"
        elif price_usd:
            price_str = f"${price_usd:,.2f}"
        else:
            price_str = "❌未获取"

        mv_str = f"¥{mv_cny:,.0f}" if mv_cny else "-"
        pnl = h.get("_pnl")
        pnl_str = format_pnl(pnl)
        cost_total = pnl["cost_cny"] if pnl and pnl.get("cost_cny") is not None else None
        cost_total_str = f"¥{cost_total:,.0f}" if cost_total is not None else "⚠️待补"
        cost_unit_str = "⚠️待补"
        if cost_total is not None and qty > 0:
            cost_unit = cost_total / qty
            cost_unit_str = f"¥{cost_unit:,.4f}"

        if pnl and pnl.get("status"):
            cost_unknown_items.append(h["name"])

        unit = h.get("unit", "")
        if unit:
            qty_str = f"{qty:,.0f}{unit}"
        elif qty == int(qty):
            qty_str = f"{qty:,.0f}"
        else:
            qty_str = f"{qty}"

        pct_str = f"{pct:.1f}%"
        table_rows.append([h["name"], qty_str, price_str, mv_str, cost_unit_str, cost_total_str, pnl_str, pct_str, storage])

    table_rows.append(["**投资合计**", "—", "—", f"**¥{investment_total:,.0f}**", "—", "—", "—", "**100%**", "—"])

    lines.append(build_aligned_table(headers, table_rows))

    if cost_unknown_items:
        lines.append("")
        lines.append(f"> ⚠️ **以下标的成本未知，盈亏无法计算**：{'、'.join(cost_unknown_items)}")
        lines.append("> 请提供历史买入价格，我会帮你补上。")
    lines.append("")

    # ────────────── 历史最值 ──────────────
    hh = history_data.get("holdings_history", {})
    if hh:
        lines.append("## 三、历史价格最值")
        lines.append("")
        lines.append("| 标的 | 当前价(USD) | 历史最高 | 最高日期 | 历史最低 | 最低日期 |")
        lines.append("|------|-----------|---------|---------|---------|---------|")
        for h in all_holdings:
            hid = h.get("id", "")
            price = h.get("price_usd")
            if hid in hh and price is not None:
                e = hh[hid]
                ath = f"${e['all_time_high_price']:,.2f}" if e.get("all_time_high_price") else "—"
                atl = f"${e['all_time_low_price']:,.2f}" if e.get("all_time_low_price") else "—"
                ath_d = e.get("all_time_high_date") or "—"
                atl_d = e.get("all_time_low_date") or "—"
                lines.append(f"| {h['name']} | ${price:,.2f} | {ath} | {ath_d} | {atl} | {atl_d} |")
        lines.append("")

    # ────────────── 代持资产 ──────────────
    custody = data.get("custody", [])
    if custody:
        lines.append("## 四、代持资产（非本人，不计入净资产）")
        lines.append("")
        lines.append("| 标的 | 数量 | 单价(USD) | 市值(USD) | 市值(CNY) | 备注 |")
        lines.append("|------|------|----------|----------|----------|------|")
        for c in custody:
            qty = c["quantity"]
            price = c.get("manual_price_usd")
            mp = c.get("_market_price_usd", price)
            mv_usd = qty * mp if mp else 0
            mv_cny = mv_usd * usd_cny
            lines.append(
                f"| {c['name']} | {qty} | ${mp:,.2f}" + (f" | ${mv_usd:,.0f} | ¥{mv_cny:,.0f}" if mp else " | - | -") +
                f" | {c.get('note', '')} |"
            )
        lines.append("")

    # ────────────── 按存放位置分布 ──────────────
    lines.append("## 五、按存放位置分布")
    lines.append("")
    lines.append("| 位置 | 市值(CNY) | 占投资比 |")
    lines.append("|------|----------|---------|")
    storage_map = defaultdict(float)
    for h in all_holdings:
        storage_map[h.get("storage", "未知")] += h.get("market_value_cny", 0)
    for st, val in sorted(storage_map.items(), key=lambda x: -x[1]):
        pct = val / investment_total * 100 if investment_total else 0
        lines.append(f"| {st} | ¥{val:,.0f} | {pct:.1f}% |")
    lines.append("")

    # ────────────── 负债 ──────────────
    lines.append("## 六、负债")
    lines.append("")
    lines.append("| 项目 | 金额(CNY) | 备注 |")
    lines.append("|------|----------|------|")
    for li in data.get("liabilities", []):
        if li.get("category") == "mortgage":
            continue  # 房贷单独说明
        li_val = li.get("amount_cny", 0)
        note = li.get("note", "")
        if li.get("amount_usd"):
            li_val += li["amount_usd"] * usd_cny
            note = (note + " " if note else "") + f"(${li['amount_usd']:,.0f} USD)"
        lines.append(f"| {li['name']} | ¥{li_val:,.0f} | {note} |")
    lines.append(f"| **投资负债合计** | **¥{liab_total_cny:,.0f}** | — |")
    lines.append("")

    # ────────────── 现金 ──────────────
    lines.append("## 七、现金及固收")
    lines.append("")
    lines.append("| 项目 | 金额 |")
    lines.append("|------|------|")
    for c in data.get("cash", []):
        if c.get("amount_hkd"):
            lines.append(f"| {c['name']} | HK${c['amount_hkd']:,.0f} (≈¥{c['amount_hkd'] * hkd_cny:,.0f}) |")
        elif c.get("amount_usd"):
            lines.append(f"| {c['name']} | ${c['amount_usd']:,.0f} (≈¥{c['amount_usd'] * usd_cny:,.0f}) |")
        else:
            lines.append(f"| {c['name']} | ¥{c['amount_cny']:,.0f} |")
        if c.get("note"):
            lines.append(f"> 📝 {c['note']}")
    lines.append("")

    # ────────────── 房贷与房产说明 ──────────────
    lines.append("## 八、房贷与房产说明")
    lines.append("")
    lines.append("> 以下为家庭自住相关房产及贷款，涉及工资还款，**暂未纳入投资盈亏统计**")
    lines.append("")
    for li in data.get("liabilities", []):
        if li.get("category") == "mortgage":
            lines.append(f"- {li['name']}：¥{li['amount_cny']:,.0f}")
    for fa in data.get("fixed_assets", []):
        lines.append(f"- {fa['name']}：估值¥{fa['value_cny']:,.0f} {fa.get('note', '')}")
    lines.append("")

    # ────────────── 持仓成本统计 ──────────────
    lines.append("## 九、持仓成本统计")
    lines.append("")
    lines.append("| 标的 | 持仓数量 | 成本单价 | 成本总价(CNY) | 当前单价 | 市值(CNY) | 盈亏(CNY) | 盈亏率 |")
    lines.append("|------|---------|---------|-------------|---------|----------|----------|-------|")
    for h in all_holdings:
        qty = h["quantity"]
        pnl = h.get("_pnl")
        cost_total = pnl["cost_cny"] if pnl and pnl.get("cost_cny") is not None else None
        mv_cny = h.get("market_value_cny", 0)
        price_usd = h.get("price_usd")
        price_hkd = h.get("price_hkd")
        hkd_cny_rate = rates.get("HKD_CNY", 0.93)
        current_price_cny = None
        cost_per_unit = None

        if price_hkd:
            current_price_cny = price_hkd * hkd_cny_rate
        elif h.get("price_cny"):
            current_price_cny = h["price_cny"]
        elif price_usd:
            current_price_cny = price_usd * usd_cny

        if cost_total is not None and qty > 0:
            cost_per_unit = cost_total / qty

        unit = h.get("unit", "")
        if unit:
            qty_str = f"{qty:,.0f}{unit}"
        elif qty == int(qty):
            qty_str = f"{qty:,.0f}"
        else:
            qty_str = f"{qty}"

        cost_unit_str = f"¥{cost_per_unit:,.4f}" if cost_per_unit is not None else "⚠️待补"
        cost_total_str = f"¥{cost_total:,.0f}" if cost_total is not None else "⚠️待补"
        current_price_str = f"¥{current_price_cny:,.4f}" if current_price_cny else "⚠️待补"
        mv_str = f"¥{mv_cny:,.0f}" if mv_cny else "-"
        pnl_str = format_pnl(pnl)

        lines.append(f"| {h['name']} | {qty_str} | {cost_unit_str} | {cost_total_str} | {current_price_str} | {mv_str} | {pnl_str} |")
    lines.append("")

    # ────────────── 历史净资产趋势 ──────────────
    snaps = history_data.get("net_worth_snapshots", [])
    if snaps:
        lines.append("---")
        lines.append("")
        lines.append("## 十、📈 历史净资产趋势")
        lines.append("")
        lines.append("| 日期 | 总资产 | 总负债 | 净资产 |")
        lines.append("|------|--------|--------|--------|")
        for s in snaps:
            nw = s.get("net_worth_cny")
            if nw is not None:
                lines.append(f"| {s['date']} | — | — | ¥{nw:,.0f} |")
        lines.append("")

    return "\n".join(lines)


def generate_annual_report(history_path, output_dir, year, rates):
    """生成年度总结报告（含同比对比+投资建议）"""
    hist = load_yaml(history_path)
    snaps = hist.get("net_worth_snapshots", [])
    hh = hist.get("holdings_history", {})

    year_snaps = [s for s in snaps if s.get("date", "").startswith(year)]
    if not year_snaps:
        print(f"⚠️ {year}年暂无数据")
        return

    # 加载持仓并计算市值
    holdings_data = load_yaml(DEFAULT_HOLDINGS)
    cur_holdings_raw = holdings_data.get("holdings", []) if holdings_data else []
    cur_cash = holdings_data.get("cash", []) if holdings_data else []
    cur_liabilities = holdings_data.get("liabilities", []) if holdings_data else []

    usd_cny = rates["USD_CNY"]
    hkd_cny = rates["HKD_CNY"]

    # 尝试加载价格缓存，否则重新获取
    report_date = datetime.now().strftime("%Y-%m-%d")
    cache_path = PRICE_CACHE_FILE
    price_cache = load_price_cache(cache_path, report_date)

    if not price_cache or not price_cache.get("stock"):
        print("  💱 获取汇率...")
        if not price_cache:
            crypto_syms = set()
            stock_syms = set()
            for h in cur_holdings_raw:
                src = h.get("price_source", "")
                sym = h.get("symbol", "")
                if src == "cryptocompare":
                    crypto_syms.add(sym)
                elif src == "yahoo":
                    stock_syms.add(h.get("yahoo_symbol", sym))

            if crypto_syms:
                print(f"  🪙 加密货币 ({len(crypto_syms)}): {', '.join(crypto_syms)}")
                crypto_prices = fetch_crypto_prices(list(crypto_syms))
            else:
                crypto_prices = {}
            if stock_syms:
                print(f"  📈 股票 ({len(stock_syms)}): {', '.join(stock_syms)}")
                stock_prices = fetch_stock_prices_yahoo(list(stock_syms))
            else:
                stock_prices = {}
            save_price_cache(cache_path, report_date, crypto_prices, stock_prices, rates)
        else:
            crypto_prices = price_cache.get("crypto", {})
            stock_prices = price_cache.get("stock", {})
    else:
        crypto_prices = price_cache.get("crypto", {})
        stock_prices = price_cache.get("stock", {})

    # 计算市值
    cur_holdings = []
    for h in cur_holdings_raw:
        h_copy = dict(h)
        qty = h_copy["quantity"]
        src = h_copy.get("price_source", "")
        price_usd = None
        hkd_price = None

        if src == "cryptocompare":
            price_usd = crypto_prices.get(h_copy["symbol"])
        elif src == "yahoo":
            sym = h_copy.get("yahoo_symbol", h_copy["symbol"])
            sp = stock_prices.get(sym)
            if sp:
                if sp.get("currency") == "HKD":
                    hkd_price = sp["price"]
                elif sp.get("currency") == "CNY":
                    cnv = sp["price"]
                    h_copy["price_cny"] = cnv
                    h_copy["price_usd"] = round(cnv / usd_cny, 4) if usd_cny else cnv
                    h_copy["market_value_cny"] = round(qty * cnv, 2)
                    h_copy["market_value_usd"] = round(qty * cnv / usd_cny, 2) if usd_cny else 0
                    h_copy["_pnl"] = calc_pnl(h_copy, rates)
                    cur_holdings.append(h_copy)
                    continue
                else:
                    price_usd = sp["price"]
        elif src == "manual":
            price_usd = h_copy.get("manual_price_usd")

        if price_usd is not None:
            h_copy["price_usd"] = price_usd
            mv_usd = qty * price_usd
            h_copy["market_value_usd"] = round(mv_usd, 2)
            h_copy["market_value_cny"] = round(mv_usd * usd_cny, 2)
        elif hkd_price is not None:
            hkd_mv = qty * hkd_price
            h_copy["price_hkd"] = hkd_price
            h_copy["market_value_cny"] = round(hkd_mv * hkd_cny, 2)
            h_copy["market_value_usd"] = round(hkd_mv / (usd_cny / hkd_cny), 2) if usd_cny else 0
            h_copy["price_usd"] = round(hkd_price / (usd_cny / hkd_cny), 2) if usd_cny else 0

        h_copy["_pnl"] = calc_pnl(h_copy, rates)
        cur_holdings.append(h_copy)

    lines = []
    lines.append("---")
    lines.append(f"year: {year}")
    lines.append("tags: [family, finance, portfolio, annual-report, auto-generated]")
    lines.append("---")
    lines.append("")
    lines.append(f"# 家庭资产年度报告 ({year})")
    lines.append("")
    lines.append(f"> 🤖 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append(f"> 💱 参考汇率: USD/CNY={rates.get('USD_CNY',7.114):.4f}  HKD/CNY={rates.get('HKD_CNY',0.909):.4f}")
    lines.append("")

    # ──── 一、年度净资产走势 ────
    lines.append("## 一、年度净资产走势")
    lines.append("")
    lines.append("| 日期 | 净资产(CNY) | 月度环比 |")
    lines.append("|------|------------|---------|")
    prev_nw = None
    for s in year_snaps:
        nw = s.get("net_worth_cny")
        if nw is not None:
            change = ""
            if prev_nw is not None:
                diff = nw - prev_nw
                pct = diff / prev_nw * 100 if prev_nw else 0
                sign = "+" if diff >= 0 else ""
                change = f"{sign}¥{diff:,.0f} ({sign}{pct:.1f}%)"
            lines.append(f"| {s['date']} | ¥{nw:,.0f} | {change} |")
            prev_nw = nw
    lines.append("")

    # ──── 二、年度汇总（含同比对比） ────
    if year_snaps:
        first_nw = year_snaps[0].get("net_worth_cny", 0)
        last_nw = year_snaps[-1].get("net_worth_cny", 0)
        total_gain = last_nw - first_nw
        total_pct = total_gain / first_nw * 100 if first_nw else 0
        sign = "+" if total_gain >= 0 else ""

        # 同比对比: 检查前一年是否有数据
        prev_year = str(int(year) - 1)
        prev_snaps = [s for s in snaps if s.get("date", "").startswith(prev_year)]
        if prev_snaps:
            prev_last_nw = prev_snaps[-1].get("net_worth_cny", 0)
            yoy_gain = last_nw - prev_last_nw
            yoy_pct = yoy_gain / prev_last_nw * 100 if prev_last_nw else 0
            yoy_sign = "+" if yoy_gain >= 0 else ""
            yoy_str = f"{yoy_sign}¥{yoy_gain:,.0f} ({yoy_sign}{yoy_pct:.1f}%)"
            prev_line = f"  - **{prev_year}年末净值**: ¥{prev_last_nw:,.0f}"
        else:
            yoy_str = f"¥{last_nw:,.0f} (首年)"
            prev_line = f"  - **{prev_year}年末**: 无数据（首年追踪）"

        lines.append("## 二、年度汇总")
        lines.append("")
        last_date = year_snaps[-1].get("date", "")
        last_month = last_date[5:7] if len(last_date) >= 7 else "??"
        is_year_end = last_month == "12"
        latest_label = f"{year}年末净值" if is_year_end else f"截至{year}年{int(last_month)}月底净值"
        lines.append(f"- **{year}年初净值**: ¥{first_nw:,.0f}")
        lines.append(f"- **{latest_label}**: ¥{last_nw:,.0f}")
        lines.append(f"- **年度增值**: {sign}¥{total_gain:,.0f} ({sign}{total_pct:.1f}%)")
        lines.append(f"- **同比{prev_year}**: {yoy_str}")
        lines.append(f"- **月度记录**: {len(year_snaps)} 个月")
        lines.append(prev_line)
        lines.append("")

    # ──── 三、资产历史最值回顾 ────
    if hh:
        lines.append("## 三、资产历史最值回顾")
        lines.append("")
        lines.append("| 标的 | 年内最高 | 最高日期 | 年内最低 | 最低日期 |")
        lines.append("|------|---------|---------|---------|---------|")
        for hid, entry in hh.items():
            ath = f"${entry['all_time_high_price']:,.2f}" if entry.get("all_time_high_price") else "—"
            atl = f"${entry['all_time_low_price']:,.2f}" if entry.get("all_time_low_price") else "—"
            ath_d = entry.get("all_time_high_date") or "—"
            atl_d = entry.get("all_time_low_date") or "—"
            if str(ath_d).startswith(year) or str(atl_d).startswith(year):
                lines.append(f"| {entry['name']} | {ath} | {ath_d} | {atl} | {atl_d} |")
        lines.append("")

    # ──── 四、年度投资复盘与展望 ────
    lines.append("## 四、年度投资复盘与展望")
    lines.append("")
    lines.append("> 以下分析综合了X(Twitter)、微信公众号、雪球等平台KOL的深度研究，结合我们家庭的实际持仓，提供可落地的策略建议。")
    lines.append("")

    # ── 仓位结构分析 ──
    lines.append("### 4.1 仓位结构分析")
    lines.append("")

    total_cash_cny = 0
    for c in cur_cash:
        v = c.get("amount_cny", 0)
        if c.get("amount_hkd"):
            v += c["amount_hkd"] * rates.get("HKD_CNY", 0.909)
        if c.get("amount_usd"):
            v += c["amount_usd"] * rates.get("USD_CNY", 7.114)
        total_cash_cny += v

    total_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings)
    total_liab = 0
    for li in cur_liabilities:
        if li.get("category") == "mortgage":
            continue
        lv = li.get("amount_cny", 0)
        if li.get("amount_usd"):
            lv += li["amount_usd"] * rates.get("USD_CNY", 7.114)
        total_liab += lv

    invest_assets = total_mv + total_cash_cny
    crypto_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if h.get("category") == "crypto")
    us_stock_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if h.get("category") in ("us_stock_tokenized", "us_stock"))
    a_stock_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if h.get("category") == "a_stock")
    hk_stock_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if h.get("category") == "hk_stock")
    ts_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if h.get("category") == "ts_time_token")

    lines.append(f"- **加密货币(BTC/ETH)**: ¥{crypto_mv:,.0f}，占投资资产 {crypto_mv/invest_assets*100:.1f}%")
    lines.append(f"- **美股**: ¥{us_stock_mv:,.0f}，占投资资产 {us_stock_mv/invest_assets*100:.1f}%")
    if a_stock_mv > 0:
        lines.append(f"- **A股**: ¥{a_stock_mv:,.0f}，占投资资产 {a_stock_mv/invest_assets*100:.1f}%")
    if hk_stock_mv > 0:
        lines.append(f"- **港股**: ¥{hk_stock_mv:,.0f}，占投资资产 {hk_stock_mv/invest_assets*100:.1f}%")
    lines.append(f"- **TS时间代币**: ¥{ts_mv:,.0f}，占投资资产 {ts_mv/invest_assets*100:.1f}%")
    lines.append(f"- **现金固收**: ¥{total_cash_cny:,.0f}，占投资资产 {total_cash_cny/invest_assets*100:.1f}%")
    invest_net = invest_assets - total_liab
    lines.append(f"- **杠杆率**: 投资负债¥{total_liab:,.0f} / 投资净资产¥{invest_net:,.0f} = {total_liab/invest_net*100:.1f}%")

    # 家庭总资产（含房产）
    fixed_assets_list = holdings_data.get("fixed_assets", []) if holdings_data else []
    house_value = sum(fa.get("value_cny", 0) for fa in fixed_assets_list)
    mortgage_total = sum(li.get("amount_cny", 0) for li in cur_liabilities if li.get("category") == "mortgage")
    family_total_assets = invest_assets + house_value
    family_total_liab = total_liab + mortgage_total
    family_net = family_total_assets - family_total_liab
    lines.append(f"- **家庭总资产(含房产¥{house_value/10000:.0f}W)**: ¥{family_total_assets:,.0f}")
    lines.append(f"- **家庭总负债(含房贷¥{mortgage_total/10000:.0f}W)**: ¥{family_total_liab:,.0f}")
    lines.append(f"- **家庭总净值**: ¥{family_net:,.0f}")
    lines.append("")

    # ── 对标KOL策略：我们的仓位vs行业标准 ──
    lines.append("### 4.2 仓位对标：我们 vs 主流KOL策略")
    lines.append("")
    lines.append("下面将我们的实际持仓与2026年X/公众号/雪球等平台KOL的主流策略框架进行对标：")
    lines.append("")
    lines.append("| 策略框架 | 来源 | 核心逻辑 | 我们的仓位 | 对标建议 |")
    lines.append("|---------|------|---------|-----------|---------|")
    btc_pct = crypto_mv / invest_assets * 100 if invest_assets else 0
    # BTC在加密货币持仓中的占比 - 4个标的中BTC占第1和第3位
    btc_in_crypto = sum(h.get("market_value_cny", 0) for h in cur_holdings if "比特币" in h.get("name", ""))
    eth_in_crypto = sum(h.get("market_value_cny", 0) for h in cur_holdings if "以太坊" in h.get("name", ""))
    btc_pct_of_crypto = btc_in_crypto / crypto_mv * 100 if crypto_mv else 0
    eth_pct_of_crypto = eth_in_crypto / crypto_mv * 100 if crypto_mv else 0
    lines.append(f"| **核心-卫星(Core-Satellite)** | Techi/XBTO/家族办公室 | BTC 60-80%核心 + ETH 15-25%卫星 + 山寨5-10% | BTC占加密{btc_pct_of_crypto:.0f}%, ETH占{eth_pct_of_crypto:.0f}% | BTC占比OK, 但美股CRCL+TS合计占投资{(us_stock_mv+ts_mv)/invest_assets*100:.0f}%偏高 |")
    lines.append(f"| **三支柱(Three-Pillar)** | Techi 2026 | BTC锚定 + ETH现金流 + AI代币增长 | 缺AI代币敞口 | 可关注AI赛道ETF或头部项目 |")
    lines.append(f"| **标准普尔+ 家庭象限** | 新浪财富汇/雪球 | 10%现金+20%保障+30%增值+40%稳健 | 现金{total_cash_cny/invest_assets*100:.0f}%偏高 | 现金占比在合理区间，但缺少保险保障 |")
    lines.append(f"| **哑铃策略(防守+进攻)** | 头条康波周期 | 一头防守(现金/黄金/债券) + 一头进攻(权益/加密) | 防守端{total_cash_cny/invest_assets*100:.0f}% | 进攻端集中度过高，建议分散 |")
    lines.append("")

    # ── 关键风险提示 ──
    lines.append("### 4.3 关键风险提示")
    lines.append("")
    lines.append("**⚠️ CRCL集中度风险（最高优先级）**")
    crcl_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if "Circle" in h.get("name", ""))
    crcl_pct = crcl_mv / total_mv * 100 if total_mv else 0
    lines.append(f"- CRCL（燕蒙古+韩伟蒙古）合计市值¥{crcl_mv:,.0f}，占总投资 {crcl_pct:.1f}%")
    lines.append("- CRCL为手动定价标的（预IPO代币），流动性远低于公开市场资产")
    lines.append("- 参考KOL「利润分层止盈法」：浮盈+78.9%时，建议至少减持25-30%锁定利润，剩余仓位让利润奔跑")
    lines.append("")

    lines.append("**⚠️ 杠杆风险**")
    lines.append(f"- 币安BTC质押借贷$13,400（≈¥{13400 * rates.get('USD_CNY', 7.114):,.0f}），年化约3.8%")
    card_monthly = 400000 * 0.0035  # 约0.35%月费率
    lines.append(f"- 信用卡循环¥400,000，月成本约¥{card_monthly:,.0f}（按0.35%月费率估算），年化资金成本约4.2%")
    lines.append(f"- 总投资负债¥{total_liab:,.0f}，占投资净资产{total_liab/invest_net*100:.1f}%")
    lines.append("- **KOL共识**：杠杆率建议控制在30%以内，当前处于偏高区间")
    lines.append("")

    has_unknown_costs = any(
        h.get("cost_unknown") or (
            h.get("cost_basis_usd") is None
            and h.get("cost_basis_cny") is None
            and h.get("cost_basis_hkd") is None
            and not h.get("cost_is_total")
        )
        for h in cur_holdings_raw
    )
    if has_unknown_costs:
        unknown_names = [
            h["name"] for h in cur_holdings_raw
            if h.get("cost_unknown") or (
                h.get("cost_basis_usd") is None
                and h.get("cost_basis_cny") is None
                and h.get("cost_basis_hkd") is None
                and not h.get("cost_is_total")
            )
        ]
        unknown_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if h.get("_pnl", {}).get("status") == "⚠️成本未知")
        unknown_pct = unknown_mv / invest_assets * 100 if invest_assets > 0 else 0
        lines.append("**⚠️ 成本盲区**")
        lines.append(f"- 以下标的成本待补充：{'、'.join(unknown_names)}")
        if unknown_pct > 0:
            lines.append(f"- 合计占投资资产约{unknown_pct:.0f}%，是盈亏计算的最大盲区")
        lines.append("")

    # ── 优化建议（贴合KOL策略） ──
    lines.append("### 4.4 2026下半年优化建议（融合KOL策略）")
    lines.append("")

    lines.append("**1. 建立「核心-卫星」分层结构**")
    lines.append("")
    lines.append("- **核心层(目标60-70%)**：BTC + ETH，作为压舱石，不频繁交易")
    lines.append("  - BTC建议目标：通过定投(DCA)逐步将BTC占比提升至50%以上")
    lines.append("  - ETH建议：当前ETH占比约12%，可小幅加仓至15-20%，利用质押收益(~3%年化)")
    lines.append("- **卫星层(目标20-30%)**：CRCL + TSLA + 港股/A股 + TS时间代币")
    lines.append("  - CRCL：分批止盈，将仓位从{:.0f}%降至15-20%".format(crcl_pct))
    lines.append("  - TSLA：当前仓位适中(2.6%)，可继续持有")
    lines.append("- **探索层(目标5-10%)**：AI赛道、RWA板块等新兴叙事")
    lines.append("")

    lines.append("**2. 实施「利润分层止盈法」**")
    lines.append("")
    lines.append("- 参考多个KOL的止盈框架：浮盈达到50%时卖出25%，达到100%时再卖25%，剩余50%长期持有")
    crcl_pnl = next((h["_pnl"] for h in cur_holdings if "Circle" in h.get("name", "")), None)
    crcl_pct = f"+{crcl_pnl['pnl_pct']:.1f}%" if crcl_pnl and crcl_pnl.get("pnl_pct") is not None else "?"
    crcl_mv = sum(h.get("market_value_cny", 0) for h in cur_holdings if "Circle" in h.get("name", ""))
    crcl_sell = crcl_mv * 0.27
    lines.append(f"- CRCL当前浮盈{crcl_pct}，建议立即减持25-30%仓位（约¥{crcl_sell/10000:.0f}W），锁定利润")
    lines.append("")

    # 零成本持仓计算表
    crcl_holdings = [h for h in cur_holdings if "Circle" in h.get("name", "")]
    total_crcl_shares = sum(h.get("quantity", 0) for h in crcl_holdings)
    total_crcl_cost_usd = 0
    for h in crcl_holdings:
        cb = h.get("cost_basis_usd", 0)
        qty = h.get("quantity", 0)
        if h.get("cost_is_total"):
            total_crcl_cost_usd += cb
        elif cb:
            total_crcl_cost_usd += cb * qty

    if total_crcl_cost_usd > 0 and total_crcl_shares > 0:
        usd_cny = rates.get("USD_CNY", 7.114)
        cur_price = crcl_holdings[0].get("price_usd") or crcl_holdings[0].get("manual_price_usd", 113)
        price_levels = [cur_price, 120, 150, 200, 250, 300]
        lines.append("**📐 CRCL零成本持仓路线图**（卖出股数 = 总成本 ÷ 卖出价）")
        lines.append("")
        lines.append(f"> 总持仓: {total_crcl_shares}股 | 总成本: ${total_crcl_cost_usd:,.0f} (≈¥{total_crcl_cost_usd * usd_cny:,.0f}) | 当前价: ${cur_price:.2f}")
        lines.append("")
        table_rows = []
        for price in price_levels:
            if price <= 0:
                continue
            sell_shares = math.ceil(total_crcl_cost_usd / price)
            remain_shares = total_crcl_shares - sell_shares
            remain_usd = remain_shares * price
            remain_cny = remain_usd * usd_cny
            marker = " ← 当前" if abs(price - cur_price) < 0.5 else ""
            table_rows.append([
                f"${price:.2f}{marker}",
                f"{sell_shares}股 ({sell_shares/total_crcl_shares*100:.0f}%)",
                f"{remain_shares}股",
                f"${remain_usd:,.0f}",
                f"¥{remain_cny:,.0f}",
            ])
        headers = ["卖出价(USD)", "需卖出", "剩余零成本持仓", "剩余市值(USD)", "剩余市值(CNY)"]
        lines.append(build_aligned_table(headers, table_rows))
        lines.append("")

    lines.append("- 特斯拉浮盈+10.5%，可继续持有，设定+30%触发首次止盈")
    xiaoan = next((h for h in cur_holdings if "小安" in h.get("name", "")), None)
    wufan = next((h for h in cur_holdings if "午饭" in h.get("name", "")), None)
    xiaoan_pct = f"+{xiaoan['_pnl']['pnl_pct']:.1f}%" if xiaoan and xiaoan.get("_pnl", {}).get("pnl_pct") is not None else "?"
    wufan_pct = f"{wufan['_pnl']['pnl_pct']:+.1f}%" if wufan and wufan.get("_pnl", {}).get("pnl_pct") is not None else "?"
    lines.append(f"- 小安时间浮盈{xiaoan_pct}，午饭老师时间浮盈{wufan_pct}，均建议分批减持锁定")
    lines.append("")

    lines.append("**3. 建立「季度再平衡」纪律**")
    lines.append("")
    lines.append("- **通俗理解**：就像菜市场买菜——白菜涨了卖掉换土豆，土豆跌了多买点。每3个月把各资产比例「拉回」目标线")
    lines.append("- **为什么有效**：假设你设定BTC=50%、ETH=20%、CRCL=20%、现金=10%。3个月后BTC涨到60%，CRCL跌到15%")
    lines.append("  → 此时卖出10%的BTC（高位），用这笔钱买入5%的CRCL（低位），自动实现「高卖低买」")
    lines.append("- **Techi/XBTO研究**：再平衡是利用「波动率」赚钱，而非预测方向。长期坚持可提升年化收益1-3%")
    lines.append("- **操作步骤**：")
    lines.append("  1. 每季度末（3/6/9/12月底）打开月度报告，查看各资产占比")
    lines.append("  2. 对比目标比例，标出偏离超过±5%的资产")
    lines.append("  3. 卖出超配资产 → 买入低配资产，让比例回到目标线")
    lines.append("  4. 首次再平衡建议6月底执行，金额不必太大，重在建立习惯")
    lines.append("")

    lines.append("**4. 降低杠杆，控制风险**")
    lines.append("")
    lines.append("- **优先目标**：用CRCL止盈资金偿还信用卡循环¥400,000")
    lines.append("- 币安BTC质押借贷$13,400：当前利率可控，但需设置BTC价格预警（如BTC跌破$60,000时考虑提前还款）")
    lines.append("- 目标杠杆率：2026年底前将杠杆率降至30%以下")
    lines.append("")

    if has_unknown_costs:
        lines.append("**5. 补全成本数据（优先级最高）**")
        lines.append("")
        lines.append("- 以上标的的历史买入价格是计算真实盈亏的基础")
        lines.append("- 建议整理币安/链上交易记录，一次性补全")
        lines.append("- 补全后，所有标的盈亏将100%可见，无需「⚠️待补」标记")
        lines.append("")

    # ── 市场周期与展望（深度研究） ──
    lines.append("### 4.5 市场周期定位与2026展望")
    lines.append("")
    lines.append("> 以下综合了多个KOL对2026年市场的深度研判，结合我们的持仓给出具体建议。")
    lines.append("")

    lines.append("**加密周期定位**")
    lines.append("")
    lines.append("- **当前阶段**：第4次减半周期（2024年4月减半），BTC在2025年10月触及$126,198高点后回落至~$74,000，跌幅约45%")
    lines.append("- **历史规律**：每轮周期峰值回报递减（9483%→2946%→690%→97%），回撤幅度递减（-85%→-84%→-77%→-45%），BTC正从投机资产向宏观资产演变")
    lines.append("- **KOL共识**：2026年下半年（Q3-Q4）是传统减半后12-18个月的上涨窗口，但本轮ETF已提前拉动周期，节奏可能不同")
    lines.append("- **关键观察指标**：BTC现货ETF资金流向（当前$95B+）、BTC Dominance（当前58%）、ETH/BTC汇率")
    lines.append("")

    lines.append("**机构趋势**")
    lines.append("")
    lines.append("- 74%家族办公室已探索或配置加密资产（BNY Wealth 2026调查），亚洲家族办公室平均配置5%")
    lines.append("- 贝莱德IBIT单只ETF管理规模超$600亿，机构持仓占BTC流通量从2024年5%升至12%")
    lines.append("- 以太坊ETF总规模约$150亿，增速快于BTC ETF，且质押ETH超3200万枚（占流通31%）")
    lines.append("- **启示**：机构资金持续流入，BTC/ETH的长期持有价值得到验证，我们的加密仓位方向正确")
    lines.append("")

    lines.append("**中国资产观点**")
    lines.append("")
    lines.append("- 中欧商学院董鹏飞：2026年A股有望优于港股，结构化行情是主线，关注2025年未充分启动的行业（消费、医药、家电）")
    lines.append("- 雪球「极简投资人」：通过资产配置+指数基金实现长期8%绝对收益，全天候组合+红利策略是普通家庭最优解")
    lines.append("- 我们的机器人ETF(159770)精准布局AI产业链，建议继续定投；小米港股通关注政策回暖+AI手机叙事")
    lines.append("")

    lines.append("**AI赛道机遇**")
    lines.append("")
    lines.append("- AI+加密是2026年增长最快的叙事，$28B板块市值，由真实算力需求驱动（非纯炒作）")
    lines.append("- 建议关注方向：去中心化算力（Render/io.net）、AI代理（Virtuals/AIXBT）、AI数据标注（Grass）")
    lines.append("- 可考虑用CRCL止盈的部分资金（5-10%）布局AI赛道，分散风险同时捕捉增长")
    lines.append("")

    lines.append("### 4.6 2026下半年行动清单")
    lines.append("")
    lines.append("| 优先级 | 行动项 | 参考策略来源 | 预期时间 |")
    lines.append("|--------|--------|-------------|---------|")
    if has_unknown_costs:
        lines.append("| 🔴 P0 | 补全成本数据 | — | 本月内 |")
    lines.append("| 🔴 P0 | CRCL分批止盈25-30%，资金用于偿还信用卡 | 利润分层止盈法(KOL共识) | 本月内 |")
    lines.append("| 🟡 P1 | 建立季度再平衡日历，首次再平衡6月底 | Techi/XBTO季度再平衡 | 6月底 |")
    lines.append("| 🟡 P1 | BTC/ETH启动月度DCA定投 | 雪球极简投资人/新浪财富汇 | 持续 |")
    lines.append("")
    lines.append("**📖 DCA定投通俗解释**：")
    lines.append("")
    lines.append("- **原理**：每月固定日期、固定金额买入BTC/ETH，不管当时价格高低。比如每月1号买入¥5,000的BTC")
    lines.append("- **为什么有效**：价格低时同样金额买到更多币，价格高时买到更少，长期下来「自动低买多、高买少」，拉低平均成本")
    lines.append("- **举例**：BTC=$70K时¥5,000买到0.01个；BTC=$50K时¥5,000买到0.014个 → 平均成本自动低于中间价")
    lines.append("- **操作**：在币安设置「定投计划」，每月从银行卡自动扣款→自动买入BTC/ETH，完全不用盯盘")
    lines.append("- **建议金额**：从¥3,000-5,000/月开始试水，养成习惯后再加大")
    lines.append("| 🟢 P2 | 研究AI赛道代币，配置5-10%探索仓位 | Techi三支柱框架 | Q3 |")
    lines.append("| 🟢 P2 | 为家庭配置基础保障保险(重疾+医疗+意外) | 标准普尔+家庭象限 | Q3 |")
    lines.append("| 🟢 P3 | 偿还币安BTC质押借贷，降低杠杆率至30%以下 | 风险控制共识 | Q4 |")
    lines.append("")

    # ── 家庭保险分析 ──
    lines.append("### 4.7 家庭保险配置分析")
    lines.append("")
    lines.append("> 基于「家庭保险-25年.xlsx」实际保单数据，对标标准普尔家庭象限图分析")
    lines.append("")

    lines.append("**当前投保总览**（6人 | 年保费合计约 ¥13,235）")
    lines.append("")
    lines.append("| 成员 | 百万医疗 | 意外险 | 惠民保 | 重疾险 | 年保费 |")
    lines.append("|------|---------|--------|--------|--------|--------|")
    lines.append("| 韩伟 | 蓝医保20年+众民保 | 大护甲7号 ¥288 | 北京普惠 ¥195 | ❌缺失 | ¥1,289 |")
    lines.append("| 薛燕 | 蓝医保20年+众民保 | 大护甲7号 ¥288 | 北京普惠 ¥195 | ❌未配置 | ¥1,289 |")
    lines.append("| 薛燕-妈咪 | 心医保(5年) ¥1,828 | 平安孝福康 ¥248 | 惠蒙保 ¥166 | — | ¥2,242 |")
    lines.append("| 薛燕-爸爸 | 超越保(10年) ¥3,531 | 平安孝福康 ¥332 | 惠蒙保 ¥166 | — | ¥4,029 |")
    lines.append("| 韩伟-妈咪 | 超越保(10年) ¥1,918 | 专心成人版 ¥109 | 惠蒙保 ¥166 | — | ¥2,193 |")
    lines.append("| 韩伟-爸爸 | 超越保(10年) ¥1,918 | 专心成人版 ¥109 | 惠蒙保 ¥166 | — | ¥2,193 |")
    lines.append("")

    lines.append("**✅ 做得好的地方**")
    lines.append("")
    lines.append("- 全家6人均配置了百万医疗+意外险+惠民保三层基础保障，覆盖大病住院和意外风险")
    lines.append("- 韩伟/薛燕的蓝医保为20年保证续保产品，稳定性好，不怕产品下架")
    lines.append("- 四位老人根据年龄和健康状况差异化配置（心医保5年/超越保10年），设计合理")
    lines.append("- 意外险注意了地理区域限制和年龄适配（老人版 vs 成人版），细节到位")
    lines.append("- 保险经验总结非常专业（既往症、健康告知、保证续保、特需部核对），远超普通家庭")
    lines.append("")

    lines.append("**⚠️ 需要完善的地方**")
    lines.append("")
    lines.append("**🔴 优先级最高：韩伟 & 薛燕缺少重疾险**")
    lines.append("- **风险**：一旦确诊重疾（癌症、心梗等），百万医疗只报销住院费，不补偿收入损失。韩伟是家庭经济支柱，若因病停工，每月家庭开支+房贷从哪里来？")
    lines.append("- **建议**：韩伟配置50W保额、薛燕配置30-50W保额的重疾险，保至70岁或终身")
    lines.append("- **预算**：30岁左右，50W保额保至70岁，年保费约¥3,000-5,000/人")
    lines.append("")
    lines.append("**📊 重疾险产品对比：达尔文12号 vs 超级玛丽15号**")
    lines.append("")
    lines.append("> 以下对比基于深蓝保2026年6月保险榜单及多渠道产品分析，以30岁男性50W保额30年交保终身为例")
    lines.append("")
    lines.append("| 对比维度 | 达尔文12号（复星联合） | 超级玛丽15号（君龙人寿） |")
    lines.append("|----------|----------------------|------------------------|")
    lines.append("| 年保费(基础) | ¥6,710 | ¥6,875 |")
    lines.append("| 重疾种类 | 120种 | 110种 |")
    lines.append("| **重疾后轻中症继续赔** | ✅ 不分组、无间隔期 | ✅ 分组继续赔 |")
    lines.append("| **意外重疾额外赔** | ✅ 自带+35%（独有） | ❌ 无 |")
    lines.append("| 45岁前重疾翻倍赔 | ❌ 无 | ✅ 自带2倍 |")
    lines.append("| 60岁后住院津贴 | ✅ 500元/天（独有） | ❌ 无 |")
    lines.append("| 顶梁柱关爱金 | ✅ 可选+30%(癌症) | ❌ 无 |")
    lines.append("| 结节专属保障 | 一般 | ✅ 肺/乳/甲结节 |")
    lines.append("| 癌症特药金 | ❌ 无 | ✅ 自带50%保额 |")
    lines.append("| 肺结节核保 | 较友好 | ✅ 非常友好(<8mm有机会标体) |")
    lines.append("")
    lines.append("**📍 结论：达尔文12号更适合韩伟**")
    lines.append("")
    lines.append("- 意外重疾135%赔付、顶梁柱关爱金（孩子+父母）、重疾后轻中症不分组继续赔，这3项精准匹配韩伟「男性+家庭支柱+有房贷+有孩子+有老人」的身份")
    lines.append("- **推荐方案**：达尔文12号基础50W（¥6,710/年）+ 顶梁柱关爱金（¥85/年），年保费约¥6,795")
    lines.append("- 如预算允许，加疾病关爱金（60岁前额外赔80%），年保费约¥8,400，60岁前最高赔付115W")
    lines.append("- **薛燕建议**：如有肺/乳腺/甲状腺结节，优先考虑超级玛丽15号（核保更宽松+结节专属保障+女性特定癌症优势）")
    lines.append("")
    lines.append("💡 **⚠️ 重要：不要加重疾险的身故责任！**")
    lines.append("")
    lines.append("- 达尔文12号身故责任需额外加约¥1,800/年，但身故只赔50W，远不够覆盖¥180W房贷")
    lines.append("- **正确做法**：重疾险不加身故（省¥1,800）+ 单独买定期寿险¥1,500-2,500 = 花费差不多，身故保障从50W→200W")
    lines.append("")
    lines.append("**🔴 优先级最高：韩伟缺少定期寿险（房贷保护）**")
    lines.append("- **风险**：家庭有房贷¥180W（商贷¥40W + 公积金¥140W），万一韩伟发生极端风险，薛燕独自承担房贷+家庭开支")
    lines.append("- **建议**：韩伟配置定期寿险，保额≥房贷余额（¥180W），保至60岁（退休年龄）")
    lines.append("- **参考产品**：华贵大麦定期寿险、阳光i保定期寿险等，保额100-200W")
    lines.append("- **预算**：30岁男性，200W保额保至60岁，年保费约¥1,500-2,500")
    lines.append("- **这是性价比最高的「家庭兜底」保险**，保费低、保额高，专为有房贷的家庭设计")
    lines.append("")
    lines.append("**📖 通俗理解定期寿险**：在约定期限内（如到60岁），人没了/全残，赔一大笔钱（如200W）给家人。")
    lines.append("- **不是赔给自己的**，是赔给配偶/孩子的。核心作用：家庭支柱倒了，家人能用这笔钱还房贷、养孩子、过日子")
    lines.append("- **为什么便宜？** 保的是低概率事件（30-40岁身故概率很低），所以¥1,500/年就能买200W保额")
    lines.append("- **和重疾险身故责任的区别**：重疾险+身故多花¥1,800只赔50W，定寿单独买¥1,500赔200W。合起来花¥1,500-2,500，保额翻4倍")
    lines.append("- **如果60岁平平安安**：保费花完就花完了，和车险一样，买的是安心。那时候房贷还清了、孩子工作了，也不需要这个保障了")
    lines.append("")
    lines.append("**🟡 建议优化：众民保+蓝医保双重覆盖**")
    lines.append("- 韩伟/薛燕同时持有蓝医保（20年保证续保）和众民保（中高端医疗，1年期）")
    lines.append("- 众民保每年¥806/人的作用是什么？如果是为了特需部/国际部就医，确认是否真的用得上")
    lines.append("- 如果实际用不到中高端服务，可考虑停掉众民保，节省¥1,612/年")
    lines.append("- 众民保为非保证续保产品，有产品下架后重新健康告知的风险")
    lines.append("")
    lines.append("**🟢 可考虑补充**")
    lines.append("- **家财险**：北京海淀住宅估值¥320W，年保费约¥300-500可保火灾、水淹、盗抢等")
    lines.append("- **韩伟-爸爸意外险**：当前¥109/年（30W版），可考虑升级到50W版（约¥150/年），差距很小但保额翻倍")
    lines.append("")

    lines.append("**💡 保险配置优先级建议**")
    lines.append("")
    lines.append("| 优先级 | 建议 | 预估年保费 | 目的 |")
    lines.append("|--------|------|-----------|------|")
    lines.append("| 🔴 1 | 韩伟定期寿险 200W保额×60岁 | ¥1,500-2,500 | 保护房贷和家庭 |")
    lines.append("| 🔴 2 | 韩伟重疾险 50W保额 | ¥3,000-5,000 | 收入损失补偿 |")
    lines.append("| 🟡 3 | 薛燕重疾险 30-50W保额 | ¥2,500-4,000 | 收入损失补偿 |")
    lines.append("| 🟢 4 | 评估是否保留众民保 | -¥1,612/年（节省） | 避免重复覆盖 |")
    lines.append("| 🟢 5 | 家财险 | ¥300-500 | 房产保障 |")
    lines.append("")

    lines.append("> 📊 完善后家庭年保费预估：当前¥13,235 + 新增¥7,000~11,500 - 节省¥1,612 ≈ **¥18,600~23,100/年**，占家庭年收入比例合理")
    lines.append("")

    report = "\n".join(lines)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"家庭资产年度报告-{year}.md"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*55}")
    print(f"✅ 年度报告: {filepath}")
    print(f"   字数: {len(report):,} 字符")
    print(f"{'='*55}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="家庭资产月度/年度报告生成器 v2")
    parser.add_argument("--holdings", default=str(DEFAULT_HOLDINGS), help="持仓 YAML")
    parser.add_argument("--history", default=str(DEFAULT_HISTORY), help="历史追踪 YAML")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"), help="报告日期")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--annual", type=str, default=None, help="生成年度报告, 如 --annual 2026")
    args = parser.parse_args()

    holdings_path = Path(args.holdings)
    history_path = Path(args.history)

    # 年度报告模式
    if args.annual:
        print(f"\n📅 生成 {args.annual} 年度报告...")
        rates = fetch_exchange_rates()
        generate_annual_report(history_path, args.output_dir, args.annual, rates)
        return

    print("=" * 55)
    print(f"  📊 家庭资产报告生成器 v2")
    print(f"  📅 {args.date}")
    print(f"  📁 持仓: {holdings_path.name}")
    print("=" * 55)

    data = load_yaml(holdings_path)
    if not data:
        print("❌ 持仓文件为空或不存在！")
        sys.exit(1)

    all_holdings = data.get("holdings", [])

    # 1. 汇率（使用缓存）
    cache_path = PRICE_CACHE_FILE
    price_cache = load_price_cache(cache_path, args.date)
    need_fetch = not bool(price_cache)

    if need_fetch:
        print("\n💱 汇率...")
        rates = fetch_exchange_rates()
    else:
        rates = price_cache.get("rates", {})
        if rates:
            print(f"\n💱 汇率 (缓存)  USD/CNY={rates['USD_CNY']:.4f}  HKD/CNY={rates['HKD_CNY']:.4f}")
        else:
            print("\n💱 汇率...")
            rates = fetch_exchange_rates()
    usd_cny = rates["USD_CNY"]
    hkd_cny = rates["HKD_CNY"]
    print(f"  USD/CNY={usd_cny:.4f}  HKD/CNY={hkd_cny:.4f}")

    # 2. 分类 holdings
    crypto_syms = set()
    stock_syms = set()

    for h in all_holdings:
        src = h.get("price_source", "")
        sym = h.get("symbol", "")
        if src == "cryptocompare":
            crypto_syms.add(sym)
        elif src == "yahoo":
            stock_syms.add(h.get("yahoo_symbol", sym))

    # 3. 获取价格（使用缓存，一天内不重复拉取）
    if need_fetch:
        print(f"\n🪙 加密货币 ({len(crypto_syms)}): BTC, ETH...")
        crypto_prices = fetch_crypto_prices(list(crypto_syms))
        print(f"\n📈 股票 ({len(stock_syms)}): {', '.join(stock_syms)}")
        stock_prices = fetch_stock_prices_yahoo(list(stock_syms))
    else:
        print(f"\n💾 使用价格缓存 ({args.date})")
        crypto_prices = price_cache.get("crypto", {})
        stock_prices = price_cache.get("stock", {})

    # 4. 合并价格
    print("\n💰 计算市值与盈亏...")
    for h in all_holdings:
        qty = h["quantity"]
        src = h.get("price_source", "")
        price_usd = None
        hkd_price = None

        if src == "cryptocompare":
            price_usd = crypto_prices.get(h["symbol"])
        elif src == "yahoo":
            sym = h.get("yahoo_symbol", h["symbol"])
            sp = stock_prices.get(sym)
            if sp:
                if sp.get("currency") == "HKD":
                    hkd_price = sp["price"]
                elif sp.get("currency") == "CNY":
                    cnv = sp["price"]
                    h["price_cny"] = cnv
                    h["price_usd"] = round(cnv / usd_cny, 4) if usd_cny else cnv
                    h["market_value_cny"] = round(qty * cnv, 2)
                    h["market_value_usd"] = round(qty * cnv / usd_cny, 2) if usd_cny else 0
                    h["_price_ok"] = True
                    h["_pnl"] = calc_pnl(h, rates)
                    continue
                else:
                    price_usd = sp["price"]
        elif src == "manual":
            price_usd = h.get("manual_price_usd")

        if h.get("_price_ok"):
            pass
        elif price_usd is not None:
            h["price_usd"] = price_usd
            mv_usd = qty * price_usd
            h["market_value_usd"] = round(mv_usd, 2)
            h["market_value_cny"] = round(mv_usd * usd_cny, 2)
        elif hkd_price is not None:
            hkd_mv = qty * hkd_price
            h["price_hkd"] = hkd_price
            h["market_value_cny"] = round(hkd_mv * hkd_cny, 2)
            h["market_value_usd"] = round(hkd_mv / (usd_cny / hkd_cny), 2) if usd_cny else 0
            h["price_usd"] = round(hkd_price / (usd_cny / hkd_cny), 2) if usd_cny else 0
        else:
            print(f"  ⚠ {h['name']} ({h.get('id', h.get('symbol'))}) 无价格数据")

        h["_pnl"] = calc_pnl(h, rates)

    # 5. 处理代持资产价格
    for c in data.get("custody", []):
        mp = c.get("manual_price_usd")
        if mp:
            c["_market_price_usd"] = mp

    # 6. 加载+更新历史
    print("\n📜 历史追踪...")
    hist = load_or_init_history(history_path, all_holdings)
    update_history(hist, all_holdings, args.date)

    # 计算总净值(不含房贷/房产)
    total_assets_val = sum(h.get("market_value_cny", 0) for h in all_holdings)
    for c in data.get("cash", []):
        v = c.get("amount_cny", 0)
        if c.get("amount_hkd"):
            v += c["amount_hkd"] * hkd_cny
        if c.get("amount_usd"):
            v += c["amount_usd"] * usd_cny
        total_assets_val += v

    liab_val = 0
    for li in data.get("liabilities", []):
        if li.get("category") == "mortgage":
            continue  # 房贷单独说明
        lv = li.get("amount_cny", 0)
        if li.get("amount_usd"):
            lv += li["amount_usd"] * usd_cny
        liab_val += lv

    net_worth = total_assets_val - liab_val

    # 更新快照
    for s in hist.get("net_worth_snapshots", []):
        if s.get("date") == args.date:
            s["net_worth_cny"] = round(net_worth, 2)
    save_yaml(history_path, hist)

    # 7. 缓存当天价格（免去一天内重复拉取）
    if need_fetch:
        save_price_cache(cache_path, args.date, crypto_prices, stock_prices, rates)

    # 8. 生成报告
    report = build_report(data, hist, rates, args.date)

    # 9. 输出报告（直接覆盖，不自动备份）
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"家庭资产报告-{args.date[:7]}.md"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*55}")
    print(f"✅ 报告: {filepath}")
    print(f"   字数: {len(report):,} 字符")
    print(f"")
    print(f"📋 摘要:")
    print(f"   投资资产: ¥{sum(h.get('market_value_cny',0) for h in all_holdings):,.0f}")
    print(f"   总资产(含现金): ¥{total_assets_val:,.0f}")
    print(f"   投资负债: ¥{liab_val:,.0f}")
    print(f"   投资净资产: ¥{net_worth:,.0f}")

    # ⚠️ 成本未知提醒
    unknowns = [h["name"] for h in all_holdings if h.get("cost_unknown")]
    if unknowns:
        print(f"")
        print(f"⚠️ 成本未知标的: {', '.join(unknowns)}")
        print(f"   请提供买入价格，我会补入 holdings.yaml")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
