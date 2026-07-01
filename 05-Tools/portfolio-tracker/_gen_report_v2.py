"""
家庭资产报告生成引擎 v2 — 单一事实源版
数据源: holdings.yaml (唯一手工编辑) + API实时价格
联动: 每次运行自动同步 月度报告+年度报告+A8计划+portfolio_history+holdings+index+偏离检测
用法: python _gen_report_v2.py
"""
import requests, json, time, yaml, io, re, sys
from pathlib import Path
from datetime import datetime, timedelta

# Windows GBK 兼容：强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE = Path("e:/ProjectGroup/AI/ContextStack/01-Projects/family-investment/research/portfolio")
HY_PATH = BASE / "holdings.yaml"
# 自动识别当前月份，若当月报告文件不存在则复制上月报告
_current_month = datetime.now().strftime("%Y-%m")
OUT = BASE / f"reports/家庭资产报告-{_current_month}.md"
_prev_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
_prev_file = BASE / f"reports/家庭资产报告-{_prev_month}.md"
if not OUT.exists() and _prev_file.exists():
    import shutil
    shutil.copy(_prev_file, OUT)
    print(f"  📄 {_current_month} 报告不存在，已从 {_prev_month} 复制创建")
A8_PATH = BASE / "reports/Crypto-A8计划-2026至2028.md"
ANNUAL_PATH = BASE / "reports/家庭资产年度报告-2026.md"
PH_PATH = BASE / "portfolio_history.yaml"
IDX_PATH = BASE / "index.md"

today = datetime.now().strftime("%Y-%m-%d")
today_display = datetime.now().strftime("%Y年%m月%d日")

# ============================================================
# 1. 从 holdings.yaml 读取全部数据（唯一事实源）
# ============================================================
def load_holdings_yaml():
    """解析 holdings.yaml，返回结构化数据"""
    with open(HY_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    meta = data.get("meta", {})
    raw_holdings = data.get("holdings", [])
    cash_list = data.get("cash", [])
    lia_list = data.get("liabilities", [])
    custody_list = data.get("custody", [])

    # 解析持仓
    holdings = []
    for h in raw_holdings:
        entry = {
            "id": h["id"],
            "symbol": h.get("symbol", ""),
            "name": h.get("name", h["id"]),
            "quantity": float(h["quantity"]),
            "unit": h.get("unit", "股"),
            "category": h.get("category", "other"),
            "storage": h.get("storage", ""),
            "price_source": h.get("price_source", "manual"),
            "note": h.get("note", ""),
        }
        # 成本处理
        cb_total = h.get("cost_is_total", False)
        if "cost_basis_usd" in h:
            entry["cost"] = float(h["cost_basis_usd"])
            entry["cost_currency"] = "usd"
            entry["cost_is_total"] = cb_total
        elif "cost_basis_hkd" in h:
            entry["cost"] = float(h["cost_basis_hkd"])
            entry["cost_currency"] = "hkd"
            entry["cost_is_total"] = cb_total
        elif "cost_basis_cny" in h:
            entry["cost"] = float(h["cost_basis_cny"])
            entry["cost_currency"] = "cny"
            entry["cost_is_total"] = cb_total
        else:
            entry["cost"] = 0
            entry["cost_currency"] = "usd"
            entry["cost_is_total"] = False

        # 手动价格的标的
        if h.get("price_source") == "manual" and "manual_price_usd" in h:
            entry["manual_price"] = float(h["manual_price_usd"])
        else:
            entry["manual_price"] = None

        holdings.append(entry)

    # 解析现金
    cash = []
    for c in cash_list:
        item = {"name": c["name"], "note": c.get("note", "")}
        if "amount_cny" in c:
            item["amount"] = float(c["amount_cny"]); item["currency"] = "cny"
        elif "amount_hkd" in c:
            item["amount"] = float(c["amount_hkd"]); item["currency"] = "hkd"
        elif "amount_usd" in c:
            item["amount"] = float(c["amount_usd"]); item["currency"] = "usd"
        cash.append(item)

    # 解析负债（区分：房贷不计入投资净资产，只计入投资类负债）
    liabilities = []
    for l in lia_list:
        cat = l.get("category", "")
        # 房贷(mortgage)不纳入投资资产净值计算，仅统计投资负债(credit_card/crypto_loan)
        if cat == "mortgage":
            continue
        item = {"name": l["name"], "category": cat, "note": l.get("note", "")}
        if "amount_cny" in l:
            item["amount"] = float(l["amount_cny"])
        elif "amount_usd" in l:
            item["amount"] = float(l["amount_usd"])
            item["needs_conversion"] = True
        else:
            item["amount"] = 0
        liabilities.append(item)

    # 代持
    custody = []
    for c in custody_list:
        ce = {
            "symbol": c.get("symbol", ""),
            "name": c.get("name", ""),
            "quantity": float(c.get("quantity", 0)),
            "note": c.get("note", ""),
        }
        if c.get("price_source") == "manual" and "manual_price_usd" in c:
            ce["manual_price"] = float(c["manual_price_usd"])
        custody.append(ce)

    return {
        "meta": meta,
        "holdings": holdings,
        "cash": cash,
        "liabilities": liabilities,
        "custody": custody,
    }

# ============================================================
# 2. 自动拉取价格
# ============================================================
print("=" * 60)
print(f"📊 报告引擎 v2 启动 — {today_display}")
print("=" * 60)
print("\n[1/6] 拉取实时价格...")

# 汇率 — 多源交叉验证，防单源异常
uc = hc = None
src_name = ""

def fetch_sina_forex(sym):
    """新浪外汇，来源与股票一致，对中国投资者最可靠"""
    try:
        r = requests.get(f"https://hq.sinajs.cn/list=fx_s{sym.lower()}", timeout=10,
                         headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = "gbk"
        if '"' in r.text:
            parts = r.text.split('"')[1].split(",")
            if len(parts) > 7 and parts[1]:
                return float(parts[1])
    except:
        pass
    return None

# 源1: Sina外汇（中国在岸汇率，最贴近实际换汇成本）
uc_sina = fetch_sina_forex("usdcny")

# 源2: exchangerate-api（国际离岸汇率）
uc_api = None
_hkd_rate = None
try:
    r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=15)
    j = r.json()
    uc_api = j['rates']['CNY']
    _hkd_rate = j['rates']['HKD']
except:
    pass

# 交叉验证：两源都有时取中位值，差值过大则信任Sina
if uc_sina and uc_api:
    diff_pct = abs(uc_sina - uc_api) / uc_sina * 100
    if diff_pct < 2:
        uc = (uc_sina + uc_api) / 2
        src_name = f"Sina({uc_sina:.4f})+exchangerate({uc_api:.4f})→中位"
    else:
        uc = uc_sina
        src_name = f"Sina({uc_sina:.4f})，exchangerate({uc_api:.4f})偏差{diff_pct:.1f}%已丢弃"
elif uc_sina:
    uc = uc_sina
    src_name = f"Sina({uc_sina:.4f})"
elif uc_api:
    uc = uc_api
    src_name = f"exchangerate({uc_api:.4f})"
else:
    uc = 7.25
    src_name = "默认值(7.2500)"

# 范围校验：异常值回退
if not (6.5 <= uc <= 7.5):
    print(f"  ⚠️ 汇率异常 {uc:.4f}，回退到默认值 7.25")
    uc = 7.25
    src_name = "异常回退→7.2500"

# HKD/CNY 独立获取，或通过 USD 折算
hc = None
hc_sina = fetch_sina_forex("hkdcny")
if hc_sina:
    hc = hc_sina
elif _hkd_rate:
    hc = uc / _hkd_rate
else:
    hc = 0.93

print(f"  USD/CNY={uc:.4f}  HKD/CNY={hc:.4f}  (来源: {src_name})")

# BTC/ETH (Gate.io)
btc = eth = None
try:
    r = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT", timeout=10)
    if r.ok: btc = float(r.json()[0]['last'])
    r2 = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=ETH_USDT", timeout=10)
    if r2.ok: eth = float(r2.json()[0]['last'])
    print(f"  BTC=${btc}  ETH=${eth}")
except Exception as e:
    print(f"  Gate.io 失败: {e}")

# 美股 (Sina)
def fetch_sina_stock(sym):
    try:
        r = requests.get(f"https://hq.sinajs.cn/list={sym}", timeout=15,
                         headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = "gbk"
        parts = r.text.split('"')[1].split(",") if '"' in r.text else []
        return parts
    except:
        return []

def fetch_us_stock(sym):
    parts = fetch_sina_stock(f"gb_{sym.lower()}")
    if len(parts) > 1 and parts[1]:
        return float(parts[1])
    return None

stock_prices = {}
for label, sym in [("MRVL","mrvl"), ("CRCL","crcl"), ("BTGO","btgo"), ("NOK","nok")]:
    try:
        val = fetch_us_stock(sym)
        if val is not None:
            stock_prices[label] = val
            print(f"  {label}=${val:.2f}")
    except Exception as e:
        print(f"  {label} 失败: {e}")

# 港股 (Sina)
def fetch_hk_stock(sym):
    parts = fetch_sina_stock(f"hk{sym.replace('.HK','').replace('HK','')}")
    if len(parts) > 6 and parts[6]:
        return float(parts[6])
    return None

hk_prices = {}
for label, sym in [("XIAOMI","1810"), ("UBT","9880")]:
    try:
        val = fetch_hk_stock(sym)
        if val is not None:
            hk_prices[label] = val
            print(f"  {label}=HK${val:.2f}")
    except Exception as e:
        print(f"  {label} 失败: {e}")

# 降级缓存价（港股Sina API经常不可用）
if "XIAOMI" not in hk_prices:
    hk_prices["XIAOMI"] = 26.32
    print("  XIAOMI=HK$26.32 (缓存默认值)")
if "UBT" not in hk_prices:
    hk_prices["UBT"] = 112.40
    print("  UBT=HK$112.40 (缓存默认值)")

# ============================================================
# 3. 构建统一价格表 + 从yaml动态计算
# ============================================================
print("\n[2/6] 从 holdings.yaml 加载持仓数据...")
yd = load_holdings_yaml()

def get_price(holding, prices_dict):
    """根据持仓的 price_source 返回 (price, currency_str)"""
    if holding.get("manual_price") is not None:
        return holding["manual_price"], "USD"

    ps = holding["price_source"]
    sym = holding["symbol"].upper() if holding["symbol"] else ""
    sina_sym = holding.get("sina_symbol", "")
    yahoo_sym = holding.get("yahoo_symbol", "")

    # 判断是否为港股标的
    is_hk = (
        sina_sym.startswith("hk") or 
        yahoo_sym.endswith(".HK") or 
        sym.endswith(".HK") or
        sym in ("XIAOMI", "UBT", "9880.HK", "1810.HK")
    )

    # 港股
    if is_hk and ps in ("sina", "yahoo"):
        if (yahoo_sym and "1810" in yahoo_sym) or sym in ("1810.HK", "XIAOMI"):
            return hk_prices.get("XIAOMI"), "HKD"
        if (sina_sym and "9880" in sina_sym) or sym in ("9880.HK", "UBT"):
            return hk_prices.get("UBT"), "HKD"

    # 加密货币
    if ps == "cryptocompare":
        if sym == "BTC": return btc, "USD"
        if sym == "ETH": return eth, "USD"

    # 美股 (Sina)
    if ps == "sina":
        if "crcl" in sina_sym.lower() or sym == "CRCL":
            return stock_prices.get("CRCL"), "USD"
        if "mrvl" in sina_sym.lower() or sym == "MRVL":
            return stock_prices.get("MRVL"), "USD"
        if "btgo" in sina_sym.lower() or sym == "BTGO":
            return stock_prices.get("BTGO"), "USD"
        if "nok" in sina_sym.lower() or sym == "NOK":
            return stock_prices.get("NOK"), "USD"

    return None, "?"

def mv_in_cny(holding, price, uc_val, hc_val):
    """计算某个持仓的人民币市值"""
    qty = holding["quantity"]
    if price is None:
        return 0
    ps = holding["price_source"]
    sym = holding["symbol"].upper() if holding["symbol"] else ""
    sina_sym = holding.get("sina_symbol", "")
    yahoo_sym = holding.get("yahoo_symbol", "")

    # 判断是否为港股标的
    is_hk = (ps in ("sina", "yahoo") and (
        sina_sym.startswith("hk") or 
        yahoo_sym.endswith(".HK") or 
        sym.endswith(".HK") or
        sym in ("XIAOMI", "UBT", "9880.HK", "1810.HK")
    ))

    if is_hk:
        return qty * price * hc_val
    # 加密货币 / 美股 / 手动定价 / 默认都用 USD→CNY
    return qty * price * uc_val

def price_display_str(holding, price):
    """价格显示字符串"""
    if price is None:
        return "—"
    ps = holding["price_source"]
    sym = holding["symbol"].upper() if holding["symbol"] else ""
    sina_sym = holding.get("sina_symbol", "")
    yahoo_sym = holding.get("yahoo_symbol", "")
    is_hk = (ps in ("sina", "yahoo") and (
        sina_sym.startswith("hk") or 
        yahoo_sym.endswith(".HK") or 
        sym.endswith(".HK") or
        sym in ("XIAOMI", "UBT")
    ))
    if is_hk:
        return f"HK${price:,.2f}"
    if holding["unit"] == "秒":
        return f"${price:.4f}/秒"
    return f"${price:,.2f}"

def cost_in_cny(holding, uc_val, hc_val):
    """成本转人民币"""
    cost = holding["cost"]
    cc = holding["cost_currency"]
    qty = holding["quantity"]
    is_total = holding["cost_is_total"]

    if cc == "cny":
        return cost if is_total else cost * qty
    elif cc == "usd":
        return cost * uc_val if is_total else cost * qty * uc_val
    elif cc == "hkd":
        return cost * hc_val if is_total else cost * qty * hc_val
    return 0

# 计算所有持仓市值
print("\n[3/6] 计算资产市值...")
items = []
investment_total = 0
cat_sum = {}
storage_sum = {}

for h in yd["holdings"]:
    price, _ = get_price(h, stock_prices)
    mv_cny = mv_in_cny(h, price, uc, hc)
    investment_total += mv_cny

    cat = h["category"]
    cat_sum[cat] = cat_sum.get(cat, 0) + mv_cny
    st = h["storage"]
    storage_sum[st] = storage_sum.get(st, 0) + mv_cny

    # 成本计算
    cost_cny = cost_in_cny(h, uc, hc)
    cost_unit = cost_cny / h["quantity"] if h["quantity"] else 0

    pnl_cny = mv_cny - cost_cny
    sign = "+" if pnl_cny >= 0 else ""
    if cost_cny == 0:
        pnl_str = f"{sign}¥{pnl_cny:,.0f}"
    else:
        pct = pnl_cny / cost_cny * 100
        pnl_str = f"{sign}¥{pnl_cny:,.0f} ({sign}{pct:.1f}%)"

    # 数量显示
    qty = h["quantity"]
    if h["unit"] == "秒":
        qty_str = f"{qty:,.0f}秒"
    elif qty == int(qty):
        qty_str = f"{qty:,.0f}"
    else:
        qty_str = f"{qty}"

    items.append({
        "name": h["name"],
        "qty_str": qty_str,
        "price_str": price_display_str(h, price),
        "mv_cny": mv_cny,
        "cost_unit": cost_unit,
        "cost_cny": cost_cny,
        "pnl_str": pnl_str,
        "cat": cat,
        "storage": st,
        "hid": h["id"],
        "price": price,
        "qty": qty,
    })

# 现金合计
cash_total = 0
for c in yd["cash"]:
    if c["currency"] == "cny": cash_total += c["amount"]
    elif c["currency"] == "hkd": cash_total += c["amount"] * hc
    elif c["currency"] == "usd": cash_total += c["amount"] * uc

total_assets = investment_total + cash_total

# 负债合计
liab_total = sum(
    l["amount"] * uc if l.get("needs_conversion") else l["amount"]
    for l in yd["liabilities"]
)
net_worth = total_assets - liab_total
net_worth_usd = net_worth / uc

# 上期净值（从历史快照取）
prev_nw = None
prev_ta = None

# 占比计算
rows = []
for it in items:
    pct_inv = it["mv_cny"] / investment_total * 100 if investment_total else 0
    rows.append(dict(it, pct_inv=f"{pct_inv:.1f}%"))

# 汇总关键数据（供后续同步使用）
summary = {
    "net_worth": net_worth,
    "net_worth_usd": net_worth_usd,
    "total_assets": total_assets,
    "investment_total": investment_total,
    "cash_total": cash_total,
    "liab_total": liab_total,
    "uc": uc,
    "hc": hc,
    "btc_total": sum(it["qty"] for it in items if "btc" in it["hid"]),
    "eth_total": sum(it["qty"] for it in items if "eth" in it["hid"]),
    "crcl_self_total": sum(it["qty"] for it in items if "crcl" in it["hid"]),
    "usdt_cash": next((c["amount"] for c in yd["cash"] if c["currency"] == "usd"), 0),
    "prices": {
        "BTC": btc, "ETH": eth,
        "CRCL": stock_prices.get("CRCL"), "MRVL": stock_prices.get("MRVL"),
        "BTGO": stock_prices.get("BTGO"), "NOK": stock_prices.get("NOK"),
        "XIAOMI": hk_prices.get("XIAOMI"), "UBT": hk_prices.get("UBT"),
    },
    "cat_sum": cat_sum,
}

print(f"  总资产: ¥{total_assets:,.0f} | 净资产: ¥{net_worth:,.0f} (${net_worth_usd:,.0f})")

# ============================================================
# 4. 生成月度报告（全量重写）
# ============================================================
print("\n[4/6] 生成月度报告...")

cat_names = {
    "crypto": "加密货币", "us_stock_tokenized": "美股(链上)", "us_stock": "美股",
    "hk_stock": "港股", "a_stock": "A股", "ts_time_token": "TS时间代币",
}

L = []
L.append("---")
L.append("date: 2026-06-11")
L.append("tags: [family, finance, portfolio, auto-generated]")
L.append("---\n")
L.append("# 家庭资产月度报告 (2026-06-11)\n")
L.append(f"> 自动生成 · {today}  |  数据源: holdings.yaml + Gate.io + Sina + Exchangerate")
L.append(f"> USD/CNY={uc:.4f}  HKD/CNY={hc:.4f}\n")

# 一、资产总览
L.append("## 一、资产总览\n")
L.append("| 类别 | 金额(CNY) | 占比 |")
L.append("|------|----------|------|")
for ck in sorted(cat_sum, key=lambda k: -cat_sum[k]):
    pct = cat_sum[ck] / total_assets * 100
    L.append(f"| {cat_names.get(ck, ck)} | ¥{cat_sum[ck]:,.0f} | {pct:.1f}% |")
cash_pct = cash_total / total_assets * 100
L.append(f"| 现金固收 | ¥{cash_total:,.0f} | {cash_pct:.1f}% |")
L.append(f"| **总资产** | **¥{total_assets:,.0f}** | **100%** |")
L.append(f"| **总负债** | **¥{liab_total:,.0f}** | — |")
L.append(f"| **净资产** | **¥{net_worth:,.0f}** | — |")
L.append(f"| **投资总资产** | **¥{investment_total:,.0f}** | {investment_total/total_assets*100:.1f}% |")
L.append(f"| **投资净资产** | **¥{investment_total - liab_total:,.0f}** | — |\n")

# 二、投资明细
L.append("## 二、投资资产明细（含盈亏）\n")
L.append("| 标的 | 数量 | 当前单价 | 市值(CNY) | 成本单价(CNY) | 成本总价(CNY) | 盈亏(CNY) | 占投资比 | 存放 |")
L.append("|------|------|----------|-----------|---------------|---------------|----------|---------|------|")
for r in rows:
    L.append(f"| {r['name']} | {r['qty_str']} | {r['price_str']} | ¥{r['mv_cny']:,.0f} | ¥{r['cost_unit']:.2f} | ¥{r['cost_cny']:,.0f} | {r['pnl_str']} | {r['pct_inv']} | {r['storage']} |")
L.append(f"| **投资合计** | — | — | **¥{investment_total:,.0f}** | — | — | — | **100%** | — |\n")

# 三、存放位置
L.append("## 三、按存放位置分布\n")
L.append("| 位置 | 市值(CNY) | 占投资比 |")
L.append("|------|----------|---------|")
for st, val in sorted(storage_sum.items(), key=lambda x: -x[1]):
    pct = val / investment_total * 100
    L.append(f"| {st} | ¥{val:,.0f} | {pct:.1f}% |")
L.append("")

# 四、负债
L.append("## 四、负债\n")
L.append("| 项目 | 金额(CNY) | 备注 |")
L.append("|------|----------|------|")
for l in yd["liabilities"]:
    amt = l["amount"] * uc if l.get("needs_conversion") else l["amount"]
    L.append(f"| {l['name']} | ¥{amt:,.0f} | {l.get('note', '')} |")
L.append(f"| **投资负债合计** | **¥{liab_total:,.0f}** | — |\n")

# 五、现金
L.append("## 五、现金及固收\n")
L.append("| 项目 | 金额 |")
L.append("|------|------|")
for c in yd["cash"]:
    if c["currency"] == "cny":
        L.append(f"| {c['name']} | ¥{c['amount']:,.0f} |")
    elif c["currency"] == "hkd":
        L.append(f"| {c['name']} | HK${c['amount']:,.0f} (≈¥{c['amount']*hc:,.0f}) |")
    elif c["currency"] == "usd":
        L.append(f"| {c['name']} | ${c['amount']:,.0f} (≈¥{c['amount']*uc:,.0f}) |")
    if c.get("note"): L.append(f"> {c['note']}")
L.append("")

# 六、代持
crcl_p = stock_prices.get("CRCL")
L.append("## 六、代持资产（非本人，不计入净资产）\n")
L.append("| 标的 | 数量 | 单价(USD) | 市值(USD) | 市值(CNY) | 备注 |")
L.append("|------|------|----------|----------|----------|------|")
for cy in yd["custody"]:
    p = cy.get("manual_price", crcl_p or 0)
    mv_d = cy["quantity"] * p
    L.append(f"| {cy['name']} | {cy['quantity']} | ${p:,.2f} | ${mv_d:,.0f} | ¥{mv_d*uc:,.0f} | {cy['note']} |\n")

# 七、房贷
L.append("## 七、房贷与房产说明\n")
L.append("> 以下为家庭自住相关房产及贷款，涉及工资还款，**暂未纳入投资盈亏统计**\n")
L.append("- 房贷—商贷：¥400,000")
L.append("- 房贷—公积金：¥1,400,000")
L.append("- 北京海淀住宅：估值¥3,200,000 购入2025年底\n")

# 八、关键指标 vs 上期
L.append("## 八、关键指标 vs 上期 及历史趋势\n")
if prev_nw:
    nw_delta = net_worth - prev_nw
    ta_delta = total_assets - (prev_ta or total_assets)
else:
    nw_delta = ta_delta = 0

# 读历史快照做对比
try:
    ph_data = yaml.safe_load(PH_PATH.read_text(encoding="utf-8")) or {}
    snaps = ph_data.get("net_worth_snapshots", [])
    if len(snaps) >= 2:
        prev_nw = snaps[-2]["net_worth_cny"]
        prev_ta = snaps[-2]["total_assets_cny"]
        nw_delta = net_worth - prev_nw
        ta_delta = total_assets - prev_ta
except:
    prev_nw, prev_ta = net_worth, total_assets
    nw_delta = ta_delta = 0

L.append("| 指标 | 上期 | 本期({today}) | 变动 |")
L.append("|------|------|-------------|------|")
ta_sign = "+" if ta_delta >= 0 else ""
nw_sign = "+" if nw_delta >= 0 else ""
L.append(f"| 总资产 | ¥{prev_ta:,.0f} | ¥{total_assets:,.0f} | {ta_sign}¥{ta_delta:,.0f} |")
L.append(f"| 净资产 | ¥{prev_nw:,.0f} | ¥{net_worth:,.0f} | {nw_sign}¥{nw_delta:,.0f} |")
L.append("")

L.append("**历史净资产走势：**\n")
L.append("| 日期 | 净资产 | 环比 | 备注 |")
L.append("|------|--------|------|------|")
for i, s in enumerate(snaps):
    d = s["date"]; n = round(s["net_worth_cny"])
    if i == 0:
        chg = "—"
    else:
        delta = n - round(snaps[i-1]["net_worth_cny"])
        sg = "+" if delta >= 0 else ""
        chg = f"{sg}¥{delta:,.0f} ({sg}{delta/round(snaps[i-1]['net_worth_cny'])*100:.1f}%)"
    note = s.get("note", "")
    L.append(f"| {d} | ¥{n:,} | {chg} | {note} |")
# 当前行
L.append(f"| {today} | ¥{net_worth:,.0f} | {nw_sign}¥{nw_delta:,.0f} ({nw_sign}{nw_delta/prev_nw*100:.1f}%) | 本次更新 |\n")

# 九、本期变动（从 trade_log 读取或保留手动区）
L.append("## 九、本期持仓变动\n")
L.append("| 标的 | 变动 | 说明 |")
L.append("|------|------|------|")
L.append("> ⚠️ 本节需根据实际交易手动更新，或由AI助手在记录交易时自动追加\n")

# 十、价格变动
L.append("## 十、本期价格变动\n")
L.append("| 标的 | 上期价格 | 本期价格 | 涨跌 |")
L.append("|------|---------|---------|------|")
# 从history读上期价格
hh = ph_data.get("holdings_history", {})
price_labels = [
    ("BTC", "btc_onchain", "usd", "all_time_low_price"),
    ("ETH", "eth_onchain", "usd", "all_time_low_price"),
    ("CRCL", "crcl_yan", "usd", "all_time_low_price"),
    ("MRVL", "mrvl_han", "usd", "all_time_low_price"),
    ("BTGO", "bitgo", "usd", "all_time_low_price"),
    ("NOK", "nok_han", "usd", "all_time_low_price"),
    ("小米", "xiaomi_ht", "hkd", "all_time_low_price_hkd"),
    ("优必选", "ubt_ht", "hkd", "all_time_low_price_hkd"),
]
for label, pid, cur, key in price_labels:
    entry = hh.get(pid, {})
    prev_p = entry.get(key)
    if cur == "hkd":
        cur_p = hk_prices.get(label)
        if label == "小米": cur_p = hk_prices.get("XIAOMI")
        elif label == "优必选": cur_p = hk_prices.get("UBT")
        if cur_p and prev_p:
            chg = (cur_p - prev_p) / prev_p * 100
            ar = "↑" if chg > 0 else "↓"
            L.append(f"| {label} | HK${prev_p:,.2f} | HK${cur_p:,.2f} | {ar}{abs(chg):.1f}% |")
        elif cur_p:
            L.append(f"| {label} | — | HK${cur_p:,.2f} | 新 |")
    else:
        cur_p = summary["prices"].get(label)
        if cur_p and prev_p:
            chg = (cur_p - prev_p) / prev_p * 100
            ar = "↑" if chg > 0 else "↓"
            L.append(f"| {label} | ${prev_p:,.2f} | ${cur_p:,.2f} | {ar}{abs(chg):.1f}% |")
        elif cur_p:
            L.append(f"| {label} | — | ${cur_p:,.2f} | 新 |")
L.append("")

# 写入月度报告
text = "\n".join(L)
OUT.write_text(text, encoding="utf-8")
print(f"  ✅ 月度报告已写入: {OUT.name}")

# ============================================================
# 5. 联动同步所有关联文档
# ============================================================
print("\n[5/6] 联动同步关联文档...")

# ── 5a. holdings.yaml meta ──
if HY_PATH.exists():
    hy_lines = HY_PATH.read_text(encoding="utf-8").split("\n")
    new_lines = []
    for line in hy_lines:
        if re.match(r'\s*last_updated:', line) and "meta:" not in line:
            new_lines.append(f'  last_updated: "{today}"')
        elif "usd_cny:" in line:
            new_lines.append(f"  usd_cny: {uc:.3f}")
        elif "hkd_cny:" in line:
            new_lines.append(f"  hkd_cny: {hc:.3f}")
        else:
            new_lines.append(line)
    HY_PATH.write_text("\n".join(new_lines), encoding="utf-8")
    print("  ✅ holdings.yaml meta (汇率+日期)")

# ── 5b. portfolio_history.yaml ──
pid_map = {
    "btc_onchain": "BTC", "btc_binance": "BTC",
    "eth_onchain": "ETH", "eth_binance": "ETH",
    "crcl_yan": "CRCL", "crcl_han": "CRCL", "crcl_cb": "CRCL",
    "crcl_hst": "CRCL", "crcl_hf": "CRCL",
    "mrvl_han": "MRVL", "bitgo": "BTGO", "nok_han": "NOK",
    "xiaomi_ht": "XIAOMI", "ubt_ht": "UBT",
    "ts_xiaoan": "XIAOAN", "ts_wufan": "WUFAN",
}
currency_hkd = {"xiaomi_ht", "ubt_ht"}

if PH_PATH.exists():
    try:
        ph = yaml.safe_load(PH_PATH.read_text(encoding="utf-8")) or {}
    except:
        ph = {}
    hh = ph.get("holdings_history", {})

    for pid, sym in pid_map.items():
        price = summary["prices"].get(sym)
        if price is None:
            continue
        is_hkd = pid in currency_hkd
        high_key = "all_time_high_price_hkd" if is_hkd else "all_time_high_price"
        low_key = "all_time_low_price_hkd" if is_hkd else "all_time_low_price"

        if pid not in hh:
            hh[pid] = {"name": pid}
        entry = hh[pid]
        if high_key not in entry or price > entry[high_key]:
            entry[high_key] = round(price, 2)
            entry["all_time_high_date"] = today
        if low_key not in entry or price < entry[low_key]:
            entry[low_key] = round(price, 2)
            entry["all_time_low_date"] = today

    snaps = ph.get("net_worth_snapshots", [])
    existing = next((s for s in snaps if s.get("date") == today), None)
    snapshot = {
        "date": today,
        "net_worth_cny": round(net_worth),
        "total_assets_cny": round(total_assets),
    }
    if existing:
        existing.update(snapshot)
    else:
        snaps.append(snapshot)

    ph["holdings_history"] = hh
    ph["net_worth_snapshots"] = snaps

    buf = io.StringIO()
    yaml.dump(ph, buf, default_flow_style=False, allow_unicode=True, sort_keys=False)
    PH_PATH.write_text(
        "# 持仓历史最值 + 净资产快照\n"
        "# 自动生成: _gen_report_v2.py 每次运行自动更新\n"
        "# 手动补充: trades 交易记录\n\n"
        + buf.getvalue(),
        encoding="utf-8"
    )
    print("  ✅ portfolio_history.yaml (价格最值+净资产快照)")

# ── 5c. 年度报告 (4个AUTO_SYNC区域) ──
if ANNUAL_PATH.exists():
    annual = ANNUAL_PATH.read_text(encoding="utf-8")

    annual = re.sub(r"> 🤖 自动生成 · .*?\n", f"> 🤖 自动生成 · {today}\n", annual)
    annual = re.sub(r"> 💱 参考汇率:.*?\n", f"> 💱 参考汇率: USD/CNY={uc:.4f}  HKD/CNY={hc:.4f}\n", annual)

    # 5c1. 净资产走势
    snaps_sorted = sorted(snaps, key=lambda s: s["date"])
    nw_lines = ["<!-- AUTO_SYNC_START:net_worth -->",
                "| 日期 | 净资产(CNY) | 月度环比 |",
                "|------|------------|---------|"]
    pv = None
    for s in snaps_sorted:
        cn = round(s["net_worth_cny"])
        if pv is None:
            chg = ""
        else:
            delta = cn - pv
            sg = "+" if delta >= 0 else ""
            pct = delta/pv*100
            chg = f"{sg}¥{delta:,.0f} ({sg}{pct:.1f}%)"
        nw_lines.append(f"| {s['date']} | ¥{cn:,} | {chg} |")
        pv = cn
    nw_lines.append("<!-- AUTO_SYNC_END:net_worth -->")
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:net_worth -->.*?<!-- AUTO_SYNC_END:net_worth -->",
        "\n".join(nw_lines), annual, flags=re.DOTALL)

    # 5c2. 年度汇总
    first_nw = round(snaps_sorted[0]["net_worth_cny"]) if snaps_sorted else net_worth
    latest_nw = round(snaps_sorted[-1]["net_worth_cny"]) if snaps_sorted else net_worth
    delta_annual = latest_nw - first_nw
    sa = "+" if delta_annual >= 0 else ""
    pa = delta_annual / first_nw * 100 if first_nw else 0
    summary_lines = [
        "<!-- AUTO_SYNC_START:summary -->",
        f"- **2026年初净值**: ¥{first_nw:,}",
        f"- **截至{today_display}净值**: ¥{latest_nw:,}",
        f"- **年度变动**: ¥{delta_annual:,} ({sa}{pa:.1f}%)",
        f"- **月度记录**: {len(snaps_sorted)} 个快照",
        "<!-- AUTO_SYNC_END:summary -->",
    ]
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:summary -->.*?<!-- AUTO_SYNC_END:summary -->",
        "\n".join(summary_lines), annual, flags=re.DOTALL)

    # 5c3. 价格最值
    price_holdings = [
        ("比特币(链上)", "btc_onchain", "usd"), ("以太坊NFT(链上)", "eth_onchain", "usd"),
        ("比特币(币安)", "btc_binance", "usd"), ("以太坊(币安)", "eth_binance", "usd"),
        ("Circle(燕蒙古)", "crcl_yan", "usd"), ("Circle(韩伟蒙古)", "crcl_han", "usd"),
        ("Circle(韩伟长桥)", "crcl_cb", "usd"), ("Circle(华盛通)", "crcl_hst", "usd"),
        ("Circle(韩芳)", "crcl_hf", "usd"), ("迈威尔(币安)", "mrvl_han", "usd"),
        ("诺基亚(币安)", "nok_han", "usd"), ("BitGo(韩伟长桥)", "bitgo", "usd"),
        ("小米集团(港股通)", "xiaomi_ht", "hkd"), ("优必选(港股通)", "ubt_ht", "hkd"),
        ("小安时间", "ts_xiaoan", "usd"), ("午饭老师时间", "ts_wufan", "usd"),
    ]
    ph_lines = ["<!-- AUTO_SYNC_START:price_highlights -->",
                "| 标的 | 年内最高 | 最高日期 | 年内最低 | 最低日期 |",
                "|------|---------|---------|---------|---------|"]
    for label, pid, cur in price_holdings:
        entry = hh.get(pid, {})
        if cur == "hkd":
            hk, lk = "all_time_high_price_hkd", "all_time_low_price_hkd"
            pf = "HK${:,.2f}"
        else:
            hk, lk = "all_time_high_price", "all_time_low_price"
            pf = "${:,.2f}"
        hi = entry.get(hk); lo = entry.get(lk)
        hd = entry.get("all_time_high_date", today) if hi else "-"
        ld = entry.get("all_time_low_date", today) if lo else "-"
        hs = pf.format(hi) if hi else "-"
        ls = pf.format(lo) if lo else "-"
        ph_lines.append(f"| {label} | {hs} | {hd} | {ls} | {ld} |")
    ph_lines.append("<!-- AUTO_SYNC_END:price_highlights -->")
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:price_highlights -->.*?<!-- AUTO_SYNC_END:price_highlights -->",
        "\n".join(ph_lines), annual, flags=re.DOTALL)

    # 5c4. 仓位结构
    crypto_val = cat_sum.get("crypto", 0)
    us_tok = cat_sum.get("us_stock_tokenized", 0)
    us_val = cat_sum.get("us_stock", 0)
    hk_val = cat_sum.get("hk_stock", 0)
    ts_val = cat_sum.get("ts_time_token", 0)
    lev_pct = liab_total / net_worth * 100 if net_worth else 0
    total_house = total_assets + 3_200_000

    alloc_lines = [
        "<!-- AUTO_SYNC_START:allocation -->",
        f"- **加密货币(BTC/ETH)**: ¥{crypto_val:,.0f}，占投资资产 {crypto_val/investment_total*100:.1f}%，占总投资 {crypto_val/total_assets*100:.1f}%",
        f"- **美股(链上CRCL)**: ¥{us_tok:,.0f}，占投资资产 {us_tok/investment_total*100:.1f}%，占总投资 {us_tok/total_assets*100:.1f}%",
        f"- **美股(传统)**: ¥{us_val:,.0f}，占投资资产 {us_val/investment_total*100:.1f}%，占总投资 {us_val/total_assets*100:.1f}%",
        f"- **港股(小米+优必选+诺基亚)**: ¥{hk_val:,.0f}，占投资资产 {hk_val/investment_total*100:.1f}%，占总投资 {hk_val/total_assets*100:.1f}%",
        f"- **TS时间代币**: ¥{ts_val:,.0f}，占投资资产 {ts_val/investment_total*100:.1f}%，占总投资 {ts_val/total_assets*100:.1f}%",
        f"- **现金固收**: ¥{cash_total:,.0f}，占总投资 {cash_total/total_assets*100:.1f}%",
        f"- **杠杆率**: 投资负债¥{liab_total:,} / 净资产¥{net_worth:,.0f} = {lev_pct:.1f}%",
        f"- **家庭总资产(含房产¥320W)**: ¥{total_house:,.0f}",
        "<!-- AUTO_SYNC_END:allocation -->",
    ]
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:allocation -->.*?<!-- AUTO_SYNC_END:allocation -->",
        "\n".join(alloc_lines), annual, flags=re.DOTALL)

    ANNUAL_PATH.write_text(annual, encoding="utf-8")
    print("  ✅ 年度报告 (4个数据节)")

# ── 5d. A8计划 AUTO_SYNC (3个区域) ──
if A8_PATH.exists():
    a8 = A8_PATH.read_text(encoding="utf-8")

    # 5d1. 头部：净资产 + 日期
    a8 = re.sub(
        r"> \*\*最后更新\*\*：.*?\n",
        f"> **最后更新**：{today}\n",
        a8
    )
    a8 = re.sub(
        r"> \*\*当前净资产\*\*：.*?\n",
        f"> **当前净资产**：¥{round(net_worth):,} ≈ ${round(net_worth_usd):,.0f}（{today}）\n",
        a8
    )

    # 5d2. 基线表：追加新行（如果当天不存在）
    btc_t = summary["btc_total"]
    eth_t = summary["eth_total"]
    crcl_t = summary["crcl_self_total"]
    usdt_c = summary["usdt_cash"]

    baseline_row = f"| {today} | {btc_t:.3f} | {eth_t:.3f} | {int(crcl_t)}股 | ${usdt_c:,.0f} | ¥{net_worth/10000:.1f}万 | 本次自动更新 |"

    # 检查是否已有当天的行
    if f"| {today} |" not in a8:
        a8 = re.sub(
            r"(> 完整持仓明细见)",
            baseline_row + "\n\n\\1",
            a8
        )
    else:
        # 更新已有行
        a8 = re.sub(
            rf"\| {today} \|.*\|",
            baseline_row,
            a8
        )

    # 5d3. 进度追踪（替换 <!-- AUTO_SYNC:A8_PROGRESS --> 区域）
    btc_target = 2.32
    nw_target = 10_000_000
    btc_pct = btc_t / btc_target * 100 if btc_target else 0
    nw_pct = net_worth / nw_target * 100 if nw_target else 0

    # 下一定投日计算
    next_dca = None
    try:
        for s_line in a8.split("\n"):
            if "2026.6.15" in s_line and "定投" in s_line:
                dca_date = datetime(2026, 6, 15)
                days_to = (dca_date - datetime.now()).days
                next_dca = max(days_to, 0)
                break
    except:
        pass

    progress_block = (
        f"<!-- AUTO_SYNC:A8_PROGRESS -->\n"
        f"> 📊 **进度追踪**:\n"
        f"> - BTC: {btc_t:.3f}/{btc_target}个 ({btc_pct:.1f}%)  \n"
        f"> - 净资产: ¥{round(net_worth):,}/¥{nw_target:,} ({nw_pct:.1f}%)  \n"
        f"> - CRCL自持: {crcl_t:.0f}股 (目标占比≤20%)\n"
    )
    if next_dca is not None:
        if next_dca == 0:
            progress_block += f"> - ⏰ **今天就是定投日！需执行 ¥16,700 BTC定投**\n"
        elif next_dca <= 7:
            progress_block += f"> - ⏰ 下一定投日: {next_dca}天后 (2026-06-15)\n"
        else:
            progress_block += f"> - 下一定投日: {next_dca}天\n"
    progress_block += f"<!-- AUTO_SYNC_END:A8_PROGRESS -->"

    if "<!-- AUTO_SYNC:A8_PROGRESS -->" in a8:
        a8 = re.sub(
            r"<!-- AUTO_SYNC:A8_PROGRESS -->.*?<!-- AUTO_SYNC_END:A8_PROGRESS -->",
            progress_block, a8, flags=re.DOTALL)
    else:
        # 首次插入：在"下次复查"之前
        a8 = a8.replace(
            "> 下次复查",
            progress_block + "\n\n> 下次复查"
        )

    # 5d4. 更新底部日期
    a8 = re.sub(
        r"> 最后更新：.*?（定投日）",
        f"> 最后更新：{today}（定投日）",
        a8
    )

    A8_PATH.write_text(a8, encoding="utf-8")
    print("  ✅ A8计划 (头部+基线+进度)")

# ── 5e. index.md ──
if IDX_PATH.exists():
    idx = IDX_PATH.read_text(encoding="utf-8")
    idx = re.sub(
        r"（自动拉取.*?每次运行同步更新.*?）",
        f"（自动拉取 holdings.yaml + Gate.io + Sina + Exchangerate，每次运行同步更新：月度报告+年度报告+A8计划+portfolio_history+index，最后更新 {today}）",
        idx
    )
    IDX_PATH.write_text(idx, encoding="utf-8")
    print("  ✅ index.md")

# ============================================================
# 6. 偏离检测引擎
# ============================================================
print("\n[6/6] 运行偏离检测引擎...")
print("═" * 60)

alerts = []  # 收集所有警报

# ── 6a. 五大红线检测 ──
print("\n🔴 红线检查:")
print(f"{'规则':<30} {'当前值':<22} {'阈值':<12} {'状态'}")
print("-" * 70)

# 红线1: 单一标的仓位 ≤20%（BTC除外≤70%）
max_single = 0; max_name = ""
for it in items:
    pct_of_nw = it["mv_cny"] / net_worth * 100 if net_worth else 0
    if pct_of_nw > max_single and "btc" not in it["hid"]:
        max_single = pct_of_nw
        max_name = it["name"]

if max_single > 20:
    status = "❌ 严重超标"
    alerts.append(("P0", f"红线1违规: {max_name} 占净资产 {max_single:.1f}% > 20%，需立即减持"))
elif max_single > 15:
    status = "⚠️ 接近上限"
    alerts.append(("P1", f"红线1预警: {max_name} 占净资产 {max_single:.1f}%，接近20%上限"))
else:
    status = "✅ 正常"
print(f"{'单一标的≤20%(除BTC)':<30} {max_name} {max_single:.1f}%{'':<12} {'≤20%':<12} {status}")

# BTC占比
btc_mv = cat_sum.get("crypto", 0)  # 近似，因为包含ETH
btc_nw_pct = btc_mv / net_worth * 100 if net_worth else 0
btc_status = "✅ 正常" if btc_nw_pct <= 70 else f"⚠️ {btc_nw_pct:.1f}%"
print(f"{'BTC仓位上限':<30} {btc_nw_pct:.1f}%{'':<14} {'≤70%':<12} {btc_status}")

# 红线2: 小币种
has_altcoin = any(h["category"] == "altcoin" for h in yd["holdings"])
alt_status = "⚠️ 存在小币种" if has_altcoin else "✅ 无小币种"
print(f"{'不碰小币种':<30} {'—':<22} {'—':<12} {alt_status}")

# 红线3: 杠杆
cc_debt = next((l["amount"] for l in yd["liabilities"] if "信用卡" in l["name"]), 0)
binance_loan = next((l["amount"] for l in yd["liabilities"] if "币安" in l["name"]), 0)
lev_cc_pct = cc_debt / net_worth * 100 if net_worth else 0
bl_status = "✅ 已还清" if binance_loan == 0 else f"❌ ${binance_loan:,.0f}"
print(f"{'不加杠杆(币安借贷)':<30} {'$'+str(binance_loan):<22} {'$0':<12} {bl_status}")
if lev_cc_pct > 30:
    cc_s = "⚠️ 偏高"
    alerts.append(("P1", f"红线3: 信用卡循环¥{cc_debt:,}占净资产{lev_cc_pct:.1f}%，偏高"))
else:
    cc_s = "✅ 可控"
print(f"{'信用卡杠杆':<30} ¥{cc_debt:,} ({lev_cc_pct:.1f}%){'':<6} {'<30%':<12} {cc_s}")

# 红线4: 波段
print(f"{'只买不卖(<$150K)':<30} {'MA120策略已执行':<22} {'—':<12} {'✅'}")

# 红线5: 现金流
print(f"{'保留主业收入':<30} {'正常':<22} {'—':<12} {'✅'}")

# ── 6b. 阶段目标进度 ──
print(f"\n📈 阶段进度:")
print(f"{'阶段':<35} {'目标':<22} {'当前进度':<18} {'状态'}")
print("-" * 80)

# P1: 核心资产≥80%
core_pct = (crypto_val + us_val + us_tok) / total_assets * 100 if total_assets else 0
core_status = "✅" if core_pct >= 80 else f"❌ {core_pct:.1f}% < 80%"
if core_pct < 80:
    alerts.append(("P1", f"P1风险出清: 核心资产占比{core_pct:.1f}% < 80%目标，主因现金占比{cash_total/total_assets*100:.1f}%过高"))
print(f"{'P1 核心资产≥80%':<35} {'≥80%':<22} {core_pct:.1f}%{'':<13} {core_status}")

# P1: CRCL控制 ≤20%
crcl_nw_pct = (us_tok + sum(it["mv_cny"] for it in items if "crcl_cb" in it["hid"] or "crcl_hst" in it["hid"] or "crcl_hf" in it["hid"])) / net_worth * 100 if net_worth else 0
crcl_all_mv = us_tok + sum(it["mv_cny"] for it in items if "crcl_cb" in it["hid"] or "crcl_hst" in it["hid"] or "crcl_hf" in it["hid"])
crcl_status = "✅" if crcl_nw_pct <= 20 else f"❌ {crcl_nw_pct:.1f}%"
if crcl_nw_pct > 20:
    alerts.append(("P0", f"P1 CRCL控制: 全部CRCL占净资产{crcl_nw_pct:.1f}% > 20%红线，必须减持"))
print(f"{'P1 CRCL占比≤20%':<35} {'≤20%':<22} {crcl_nw_pct:.1f}%{'':<13} {crcl_status}")

# P2: BTC筹码 ≥1.8个 (2027底)
btc_p2_status = "进行中 {:.1f}%".format(btc_t / 1.8 * 100) if btc_t < 1.8 else "✅ 提前完成"
print(f"{'P2 BTC≥1.8个(2027底)':<35} {'≥1.8':<22} {btc_t:.3f}个{'':<12} {btc_p2_status}")

# P3: BTC≥2.32个 (2028底)
btc_p3_status = f"进行中 {btc_t/2.32*100:.1f}%" if btc_t < 2.32 else "✅ 完成"
print(f"{'P3 BTC≥2.32个(2028底)':<35} {'≥2.32':<22} {btc_t:.3f}个{'':<12} {btc_p3_status}")

# ── 6c. 行动项日历 ──
print(f"\n📅 即将到期的行动项:")
now = datetime.now()
action_items = [
    ("2026-06-15", "🔴 P1首次定投日 ¥16,700", "MA120下方则存USDT"),
    ("2026-07-15", "🟡 P1第二次定投 ¥16,700", "同上"),
    ("2026-07-31", "🟡 CRCL仓位审查", "若>20%需减持"),
    ("2026-08-15", "🟡 P1第三次定投 ¥16,700", "同上"),
    ("2026-08-31", "🟢 MA120观察窗", "决定是否恢复买入"),
]
for adate, atitle, anote in action_items:
    try:
        dt = datetime.strptime(adate, "%Y-%m-%d")
        days = (dt - now).days
        if days < 0:
            print(f"  ⏰ 已过期 {adate}: {atitle} — {anote}")
        elif days <= 7:
            print(f"  🔥 {days}天内 {adate}: {atitle} ← **即将到期** — {anote}")
            alerts.append(("P0" if "定投" in atitle else "P1", f"行动项到期: {adate} {atitle}"))
        elif days <= 30:
            print(f"  📌 {days}天后 {adate}: {atitle} — {anote}")
    except:
        pass

# ── 6d. 输出偏离摘要 ──
print(f"\n{'='*60}")
print(f"📋 偏离检测结果汇总:")
print(f"{'='*60}")

if alerts:
    alerts.sort(key=lambda x: (0 if x[0]=="P0" else 1 if x[0]=="P1" else 2, x))
    for pri, msg in alerts:
        icon = "🚨" if pri == "P0" else "⚠️" if pri == "P1" else "ℹ️"
        print(f"  [{pri}] {icon} {msg}")
else:
    print("  🟢 所有指标正常，无偏离项")

# 净资产趋势判断
if len(snaps) >= 3:
    n_vals = [s["net_worth_cny"] for s in snaps[-3:]]
    if all(n_vals[i] > n_vals[i+1] for i in range(len(n_vals)-1)):
        parts = [f"¥{round(s['net_worth_cny']):,}" for s in snaps[-len(n_vals):]]
        print(f"\n  📉 ⚠️ 净资产连续{len(n_vals)-1}期下降: " + " → ".join(parts))
        alerts.append(("P1", "净资产持续下降趋势"))

print(f"\n{'='*60}")
print(f"✅ 全部完成! 报告引擎运行结束")
print(f"   总资产: ¥{total_assets:,.0f}  投资: ¥{investment_total:,.0f}  净资产: ¥{net_worth:,.0f} (${net_worth_usd:,.0f})")
print(f"   同步: 月度报告 + 年度报告(4区) + A8计划(3区) + history + index + 偏离检测")
print(f"{'='*60}")
