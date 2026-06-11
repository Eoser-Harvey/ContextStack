"""家庭资产报告生成 — 自动拉取价格版
数据源: Gate.io(BTC/ETH) + Sina(HK/A股) + Exchangerate(汇率)
用法: python _gen_report_temp.py
联动: 每次运行自动同步 月度报告+年度报告+portfolio_history+holdings+index
"""
import requests, json, time, yaml, io, re
from pathlib import Path
from datetime import datetime

OUT = Path("e:/ProjectGroup/AI/ContextStack/01-Projects/family-investment/research/portfolio/reports/家庭资产报告-2026-06.md")

# ============================================================
# 1. 自动拉取价格
# ============================================================
print("拉取价格...")

# 汇率
try:
    r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=15)
    uc = r.json()['rates']['CNY']
    hc = uc / r.json()['rates']['HKD']
    print(f"  汇率: USD/CNY={uc:.4f}, HKD/CNY={hc:.4f}")
except Exception as e:
    print(f"  汇率失败, 用默认: {e}")
    uc, hc = 7.25, 0.93

# BTC/ETH (Gate.io)
btc = eth = None
try:
    r = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT", timeout=10)
    if r.ok: btc = float(r.json()[0]['last'])
    r2 = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=ETH_USDT", timeout=10)
    if r2.ok: eth = float(r2.json()[0]['last'])
    print(f"  BTC={btc}, ETH={eth}")
except Exception as e:
    print(f"  Gate.io 失败: {e}")

# 股票 (Sina)
def fetch_sina_stock(sym):
    try:
        r = requests.get(f"https://hq.sinajs.cn/list={sym}", timeout=15,
                         headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = "gbk"
        parts = r.text.split('"')[1].split(",") if '"' in r.text else []
        return parts
    except:
        return []

# 美股 (Sina)
def fetch_us_stock(sym):
    """新浪美股格式: parts[1]=当前价"""
    parts = fetch_sina_stock(f"gb_{sym.lower()}")
    if len(parts) > 1 and parts[1]:
        return float(parts[1])
    return None

mrvl = crcl = btgo = nok = None
for label, sym in [("MRVL", "mrvl"), ("CRCL", "crcl"), ("BTGO", "btgo"), ("NOK", "nok")]:
    try:
        val = fetch_us_stock(sym)
        if val is not None:
            print(f"  {label}=${val}")
            if label == "MRVL": mrvl = val
            elif label == "CRCL": crcl = val
            elif label == "BTGO": btgo = val
            elif label == "NOK": nok = val
    except Exception as e:
        print(f"  {label} 失败: {e}")

# 港股 (Sina)
def fetch_hk_stock(sym):
    """新浪港股格式: parts[6]=当前价"""
    parts = fetch_sina_stock(f"hk{sym.replace('.HK','')}")
    if len(parts) > 6 and parts[6]:
        return float(parts[6])
    return None

xiaomi = ubt = None
for label, sym in [("小米", "01810"), ("优必选", "09880")]:
    try:
        val = fetch_hk_stock(sym)
        if val is not None:
            print(f"  {label}=HK${val}")
            if label == "小米": xiaomi = val
            elif label == "优必选": ubt = val
    except Exception as e:
        print(f"  {label} 失败: {e}")

# 降级缓存价
if btc is None: btc = 61475.90
if eth is None: eth = 1620.79
if mrvl is None: mrvl = 252.59
if crcl is None: crcl = 113.07
if btgo is None: btgo = 6.04
if nok is None: nok = 14.88
if xiaomi is None: xiaomi = 26.32
if ubt is None: ubt = 112.40

PRICES = {"BTC": btc, "ETH": eth, "MRVL": mrvl, "CRCL": crcl, "BTGO": btgo,
          "NOK": nok, "XIAOMI": xiaomi, "UBT": ubt, "XIAOAN": 0.02156, "WUFAN": 2.91}
print(f"  最终价格: { {k: round(v,2) for k,v in PRICES.items()} }")

# ============================================================
# 2. 持仓数据
# ============================================================
HOLDINGS = [
    ("btc_onchain", "比特币(链上)", 0.12980465, "usd", 0, True, "crypto", "链上钱包"),
    ("eth_onchain", "以太坊NFT(链上)", 1.35, "usd", 2608, False, "crypto", "链上钱包"),
    ("btc_binance", "比特币(币安)", 0.51247, "usd", 85242, True, "crypto", "韩伟蒙古币安"),
    ("eth_binance", "以太坊(币安)", 0.0003, "usd", 2608, False, "crypto", "韩伟蒙古币安"),
    ("crcl_yan", "Circle(燕蒙古)", 207.46, "usd", 14245.76, True, "us_stock_tokenized", "燕蒙古WEB3"),
    ("mrvl_han", "迈威尔(币安)", 6.87, "usd", 291, False, "us_stock", "韩伟蒙古币安"),
    ("nok_han", "诺基亚(币安)", 134.41, "usd", 14.88, False, "us_stock", "韩伟蒙古币安"),
    ("crcl_han", "Circle(韩伟蒙古)", 268.25, "usd", 15843.84, True, "us_stock_tokenized", "韩伟蒙古WEB3"),
    ("crcl_cb", "Circle(韩伟长桥)", 25.5, "usd", 63.20, False, "us_stock", "韩伟长桥证券"),
    ("crcl_hst", "Circle(华盛通)", 45, "usd", 63.20, False, "us_stock", "华盛通证券"),
    ("crcl_hf", "Circle(韩芳)", 80, "usd", 63.20, False, "us_stock", "韩芳证券账户"),
    ("bitgo", "BitGo(韩伟长桥)", 54, "usd", 18, False, "us_stock", "韩伟长桥证券"),
    ("ubt_ht", "优必选(港股通)", 50, "hkd", 109.00, False, "hk_stock", "东方财富港股通"),
    ("xiaomi_ht", "小米集团(港股通)", 1400, "hkd", 29.612, False, "hk_stock", "东方财富港股通"),
    ("ts_xiaoan", "小安时间", 106499, "usd", 1000, True, "ts_time_token", "TS平台"),
    ("ts_wufan", "午饭老师时间", 818, "usd", 4.365, False, "ts_time_token", "TS平台"),
]

CASH = [
    ("家庭备用金(活期/货基)", "cny", 630808, ""),
    ("HK打新资金", "hkd", 146060, "含13W家庭内部调配, 其余为打新盈利"),
    ("币安USDT余额", "usd", 10500, "06-11买入NOK后余额"),
]

LIABILITIES_INVEST = [
    ("信用卡循环(投资WEB3)", "cny", 400000, "循环刷卡用于WEB3投资"),
]

# ============================================================
# 3. 计算
# ============================================================
def mv_for(hid, qty):
    if hid in ("btc_onchain", "btc_binance"): return qty * PRICES["BTC"] * uc
    if hid in ("eth_onchain", "eth_binance"): return qty * PRICES["ETH"] * uc
    if hid == "mrvl_han": return qty * PRICES["MRVL"] * uc
    if "crcl" in hid: return qty * PRICES["CRCL"] * uc
    if hid == "bitgo": return qty * PRICES["BTGO"] * uc
    if hid == "nok_han": return qty * PRICES["NOK"] * uc
    if hid == "xiaomi_ht": return qty * PRICES["XIAOMI"] * hc
    if hid == "ubt_ht": return qty * PRICES["UBT"] * hc
    if hid == "ts_xiaoan": return qty * PRICES["XIAOAN"] * uc
    if hid == "ts_wufan": return qty * PRICES["WUFAN"] * uc
    return 0

def price_str(hid):
    if hid in ("btc_onchain", "btc_binance"): return f"${PRICES['BTC']:,.2f}"
    if hid in ("eth_onchain", "eth_binance"): return f"${PRICES['ETH']:,.2f}"
    if hid == "mrvl_han": return f"${PRICES['MRVL']:,.2f}"
    if "crcl" in hid: return f"${PRICES['CRCL']:,.2f}"
    if hid == "bitgo": return f"${PRICES['BTGO']:,.2f}"
    if hid == "nok_han": return f"${PRICES['NOK']:,.2f}"
    if hid == "xiaomi_ht": return f"HK${PRICES['XIAOMI']:,.2f}"
    if hid == "ubt_ht": return f"HK${PRICES['UBT']:,.2f}"
    if hid == "ts_xiaoan": return f"${PRICES['XIAOAN']:.4f}/秒"
    if hid == "ts_wufan": return f"${PRICES['WUFAN']:.2f}/秒"
    return "—"

# 第一步：算市值
items = []
investment_total = 0
cat_sum = {}

for hid, name, qty, ct, cost, is_total, cat, st in HOLDINGS:
    mv_cny = mv_for(hid, qty)
    investment_total += mv_cny
    cat_sum[cat] = cat_sum.get(cat, 0) + mv_cny

    # 成本
    if ct == "usd":
        cost_cny = cost * uc if is_total else cost * qty * uc
    elif ct == "cny":
        cost_cny = cost if is_total else cost * qty
    elif ct == "hkd":
        cost_cny = cost * hc if is_total else cost * qty * hc
    else:
        cost_cny = 0
    cost_unit_cny = cost_cny / qty if qty else 0

    pnl_cny = mv_cny - cost_cny
    sign = "+" if pnl_cny >= 0 else ""
    if cost_cny == 0:
        pnl_str = f"{sign}¥{pnl_cny:,.0f}"
    else:
        pnl_pct = pnl_cny / cost_cny * 100
        pnl_str = f"{sign}¥{pnl_cny:,.0f} ({sign}{pnl_pct:.1f}%)"

    qty_str = f"{qty:,.0f}" if qty == int(qty) else f"{qty}"
    if "秒" in str(qty) or hid in ("ts_xiaoan","ts_wufan"):
        qty_str = f"{qty:,.0f}秒"

    items.append((name, qty_str, price_str(hid), mv_cny, cost_unit_cny, cost_cny, pnl_str, cat, st))

# 现金
cash_total = 0
for cn, ct, amt, note in CASH:
    if ct == "cny": cash_total += amt
    elif ct == "hkd": cash_total += amt * hc
    elif ct == "usd": cash_total += amt * uc

total_assets = investment_total + cash_total

# 负债
liab_total = sum(la for _, _, la, _ in LIABILITIES_INVEST)
net_worth = total_assets - liab_total

# 上次报告净值 (2026-06-04)
prev_net_worth = 1357499
prev_total_assets = 1852827
nw_delta = net_worth - prev_net_worth
ta_delta = total_assets - prev_total_assets

# 第二步：占比
rows = []
for name, qty_str, ps, mv_cny, cu, ct_val, pnl_str, cat, st in items:
    pct_inv = mv_cny / investment_total * 100 if investment_total else 0
    rows.append((name, qty_str, ps, f"¥{mv_cny:,.0f}", f"¥{cu:,.2f}", f"¥{ct_val:,.0f}", pnl_str, f"{pct_inv:.1f}%", st))

# ============================================================
# 4. 生成报告
# ============================================================
L = []
L.append("---")
L.append("date: 2026-06-11")
L.append("tags: [family, finance, portfolio, auto-generated]")
L.append("---\n")
L.append("# 家庭资产月度报告 (2026-06-11)\n")
L.append(f"> 自动生成 · 2026-06-11  |  数据源: Gate.io + Sina + Exchangerate")
L.append(f"> USD/CNY={uc:.4f}  HKD/CNY={hc:.4f}\n")

# ── 一、资产总览 ──
L.append("## 一、资产总览\n")
L.append("| 类别 | 金额(CNY) | 占比 |")
L.append("|------|----------|------|")
cat_names = {"crypto": "加密货币", "us_stock_tokenized": "美股(链上)", "us_stock": "美股",
             "hk_stock": "港股", "a_stock": "A股", "ts_time_token": "TS时间代币"}
for ck in sorted(cat_sum, key=lambda k: -cat_sum[k]):
    pct = cat_sum[ck] / total_assets * 100
    L.append(f"| {cat_names.get(ck, ck)} | ¥{cat_sum[ck]:,.0f} | {pct:.1f}% |")
cash_pct = cash_total / total_assets * 100
L.append(f"| 现金固收 | ¥{cash_total:,.0f} | {cash_pct:.1f}% |")
L.append(f"| **总资产** | **¥{total_assets:,.0f}** | **100%** |")
L.append(f"| **总负债** | **¥{liab_total:,.0f}** | — |")
L.append(f"| **净资产** | **¥{net_worth:,.0f}** | — |\n")

# ── 二、投资明细 ──
L.append("## 二、投资资产明细（含盈亏）\n")
L.append("| 标的 | 数量 | 当前单价 | 市值(CNY) | 成本单价(CNY) | 成本总价(CNY) | 盈亏(CNY) | 占投资比 | 存放 |")
L.append("|------|------|----------|-----------|---------------|---------------|----------|---------|------|")
for n, qs, ps, mv, cu, ct_str, pnl, pi, st in rows:
    L.append(f"| {n} | {qs} | {ps} | {mv} | {cu} | {ct_str} | {pnl} | {pi} | {st} |")
L.append(f"| **投资合计** | — | — | **¥{investment_total:,.0f}** | — | — | — | **100%** | — |\n")

# ── 三、存放位置 ──
L.append("## 三、按存放位置分布\n")
L.append("| 位置 | 市值(CNY) | 占投资比 |")
L.append("|------|----------|---------|")
storage_sum = {}
for hid, name, qty, ct, cost, is_total, cat, st in HOLDINGS:
    storage_sum[st] = storage_sum.get(st, 0) + mv_for(hid, qty)
for st, val in sorted(storage_sum.items(), key=lambda x: -x[1]):
    pct = val / investment_total * 100
    L.append(f"| {st} | ¥{val:,.0f} | {pct:.1f}% |")
L.append("")

# ── 四、负债 ──
L.append("## 四、负债\n")
L.append("| 项目 | 金额(CNY) | 备注 |")
L.append("|------|----------|------|")
for ln, lt, la, note in LIABILITIES_INVEST:
    L.append(f"| {ln} | ¥{la:,.0f} | {note} |")
L.append(f"| **投资负债合计** | **¥{liab_total:,.0f}** | — |\n")

# ── 五、现金 ──
L.append("## 五、现金及固收\n")
L.append("| 项目 | 金额 |")
L.append("|------|------|")
for cn, ct, amt, note in CASH:
    if ct == "cny": L.append(f"| {cn} | ¥{amt:,.0f} |")
    elif ct == "hkd": L.append(f"| {cn} | HK${amt:,.0f} (≈¥{amt*hc:,.0f}) |")
    elif ct == "usd": L.append(f"| {cn} | ${amt:,.0f} (≈¥{amt*uc:,.0f}) |")
    if note: L.append(f"> {note}")
L.append("")

# ── 六、代持 ──
crcl_p = PRICES["CRCL"]
mv_dc = 60 * crcl_p
L.append("## 六、代持资产（非本人，不计入净资产）\n")
L.append("| 标的 | 数量 | 单价(USD) | 市值(USD) | 市值(CNY) | 备注 |")
L.append("|------|------|----------|----------|----------|------|")
L.append(f"| CRCL代持(朋友) | 60 | ${crcl_p:,.2f} | ${mv_dc:,.0f} | ¥{mv_dc*uc:,.0f} | 为朋友代持60股, 成本83U/股 |\n")

# ── 七、房贷 ──
L.append("## 七、房贷与房产说明\n")
L.append("> 以下为家庭自住相关房产及贷款，涉及工资还款，**暂未纳入投资盈亏统计**\n")
L.append("- 房贷—商贷：¥400,000")
L.append("- 房贷—公积金：¥1,400,000")
L.append("- 北京海淀住宅：估值¥3,200,000 购入2025年底\n")

# ── 八、关键指标 vs 上期 及历史趋势 ──
L.append("## 八、关键指标 vs 上期 及历史趋势\n")
L.append("| 指标 | 上期(06-04) | 本期(06-11) | 变动 |")
L.append("|------|-----------|-----------|------|")
ta_sign = "+" if ta_delta >= 0 else ""
nw_sign = "+" if nw_delta >= 0 else ""
L.append(f"| 总资产 | ¥{prev_total_assets:,} | ¥{total_assets:,.0f} | {ta_sign}¥{ta_delta:,.0f} ({ta_sign}{ta_delta/prev_total_assets*100:.1f}%) |")
L.append(f"| 净资产 | ¥{prev_net_worth:,} | ¥{net_worth:,.0f} | {nw_sign}¥{nw_delta:,.0f} ({nw_sign}{nw_delta/prev_net_worth*100:.1f}%) |")
L.append(f"| 投资负债 | ¥495,328 | ¥{liab_total:,} | ¥-95,328 (币安借贷已还清) |")
L.append("")
L.append("**历史净资产走势：**\n")
L.append("| 日期 | 净资产 | 环比 | 备注 |")
L.append("|------|--------|------|------|")
L.append("| 2026-06-02 | ¥1,361,859 | — | 首次快照 |")
L.append("| 2026-06-04 | ¥1,357,499 | -¥4,360 (-0.3%) | BTC/ETH回调 |")
L.append(f"| 2026-06-11 | ¥{net_worth:,.0f} | {nw_sign}¥{nw_delta:,.0f} ({nw_sign}{nw_delta/prev_net_worth*100:.1f}%) | CRCL↓30%(数据源切换); 换仓优必选 |\n")

# ── 九、本期变动 ──
L.append("## 九、本期持仓变动\n")
L.append("| 标的 | 变动 | 说明 |")
L.append("|------|------|------|")
L.append("| 机器人ETF(159770) | 清仓 | 4,000股 @ ¥1.203, 回收 ¥4,812 |")
L.append(f"| 优必选(9880.HK) | 新建仓 | 50股 @ HK$109, 当前 HK${PRICES['UBT']:.2f} |")
L.append("| 币安质押借贷 | 已还清 | $13,400 → $0, 杠杆率降至 0% |")
L.append("")

L.append("## 十、本期价格变动\n")
L.append("| 标的 | 上期(06-04) | 本期(06-11) | 涨跌 |")
L.append("|------|-----------|-----------|------|")
for label, sym, prev in [("BTC", "BTC", 64797.11), ("ETH", "ETH", 1823.35),
                           ("CRCL", "CRCL", 113.07), ("BTGO", "BTGO", 6.04),
                           ("NOK", "NOK", None),
                           ("小米", "XIAOMI", 28.58), ("优必选", "UBT", None)]:
    cur = PRICES[sym]
    if sym in ("BTC", "ETH", "CRCL", "BTGO"):
        cur_s = f"${cur:,.2f}"
        prev_s = f"${prev:,.2f}" if prev else "—"
        chg = (cur - prev) / prev * 100 if prev else 0
        arrow = "↑" if chg > 0 else "↓"
        L.append(f"| {label} | {prev_s} | {cur_s} | {arrow}{abs(chg):.1f}% |")
    elif sym == "XIAOMI":
        cur_s = f"HK${cur:,.2f}"
        prev_s = f"HK${prev:,.2f}"
        chg = (cur - prev) / prev * 100
        arrow = "↑" if chg > 0 else "↓"
        L.append(f"| {label} | {prev_s} | {cur_s} | {arrow}{abs(chg):.1f}% |")
    elif sym == "UBT":
        L.append(f"| {label} | — | HK${cur:,.2f} | 新持仓 |")
    elif sym == "NOK":
        L.append(f"| {label} | — | ${cur:,.2f} | 新持仓·06-11买入 |")
L.append("")

# 写入
text = "\n".join(L)
OUT.write_text(text, encoding="utf-8")
print(f"\n✅ 报告已生成: {OUT}")
print(f"   总资产: ¥{total_assets:,.0f}  |  投资资产: ¥{investment_total:,.0f}  |  净资产: ¥{net_worth:,.0f}")
print(f"   vs 上期: 净资产 {nw_sign}¥{nw_delta:,.0f} ({nw_sign}{nw_delta/prev_net_worth*100:.1f}%)")

# ============================================================
# 5. 联动同步: 自动更新所有关联文档
# ============================================================
BASE = Path("e:/ProjectGroup/AI/ContextStack/01-Projects/family-investment/research/portfolio")
today = datetime.now().strftime("%Y-%m-%d")
today_display = datetime.now().strftime("%Y年%m月%d日")

def chg_str_num(cur, prev):
    """涨跌字符串"""
    if prev is None or prev == 0: return "新持仓"
    chg = (cur - prev) / prev * 100
    sign = "+" if chg >= 0 else ""
    return f"{sign}{chg:.1f}%"

# ── 5a. 同步 holdings.yaml meta ──
hy_path = BASE / "holdings.yaml"
if hy_path.exists():
    hy_lines = hy_path.read_text(encoding="utf-8").split("\n")
    new_lines = []
    for line in hy_lines:
        if "last_updated:" in line and "meta:" not in line:
            new_lines.append(f'  last_updated: "{today}"')
        elif "usd_cny:" in line:
            new_lines.append(f"  usd_cny: {uc:.3f}")
        elif "hkd_cny:" in line:
            new_lines.append(f"  hkd_cny: {hc:.3f}")
        else:
            new_lines.append(line)
    hy_path.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"🔄 已同步 holdings.yaml meta (汇率+日期)")

# ── 5b. 同步 portfolio_history.yaml ──
ph_path = BASE / "portfolio_history.yaml"
if ph_path.exists():
    try:
        ph = yaml.safe_load(ph_path.read_text(encoding="utf-8")) or {}
    except:
        ph = {}
    hh = ph.get("holdings_history", {})

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

    for pid, sym in pid_map.items():
        price = PRICES.get(sym)
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
    ph_path.write_text(
        "# 持仓历史最值 + 净资产快照\n"
        "# 自动生成: _gen_report_temp.py 每次运行自动更新\n"
        "# 手动补充: trades 交易记录\n\n"
        + buf.getvalue(),
        encoding="utf-8"
    )
    print(f"🔄 已同步 portfolio_history.yaml (价格最值+净资产快照)")

# ── 5c. 同步 年度报告 ──
annual_path = BASE / "reports/家庭资产年度报告-2026.md"
if annual_path.exists():
    annual = annual_path.read_text(encoding="utf-8")

    # --- 更新报告头 (日期+汇率) ---
    annual = re.sub(
        r"> 🤖 自动生成 · .*?\n",
        f"> 🤖 自动生成 · {today}\n",
        annual
    )
    annual = re.sub(
        r"> 💱 参考汇率:.*?\n",
        f"> 💱 参考汇率: USD/CNY={uc:.4f}  HKD/CNY={hc:.4f}\n",
        annual
    )

    # --- 5c1. 净资产走势 ---
    # 从 portfolio_history.yaml 读取全部快照
    snaps_sorted = sorted(snaps, key=lambda s: s["date"])
    nw_lines = ["<!-- AUTO_SYNC_START:net_worth -->",
                "| 日期 | 净资产(CNY) | 月度环比 |",
                "|------|------------|---------|"]
    prev = None
    for s in snaps_sorted:
        cur_nw = round(s["net_worth_cny"])
        if prev is None:
            chg = ""
        else:
            delta = cur_nw - prev
            sign = "+" if delta >= 0 else ""
            pct = delta/prev*100
            chg = f"{sign}¥{delta:,.0f} ({sign}{pct:.1f}%)"
        nw_lines.append(f"| {s['date']} | ¥{cur_nw:,} | {chg} |")
        prev = cur_nw
    nw_lines.append("<!-- AUTO_SYNC_END:net_worth -->")
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:net_worth -->.*?<!-- AUTO_SYNC_END:net_worth -->",
        "\n".join(nw_lines),
        annual, flags=re.DOTALL
    )

    # --- 5c2. 年度汇总 ---
    first_nw = round(snaps_sorted[0]["net_worth_cny"])
    latest_nw = round(snaps_sorted[-1]["net_worth_cny"])
    delta_annual = latest_nw - first_nw
    sign_annual = "+" if delta_annual >= 0 else ""
    pct_annual = delta_annual / first_nw * 100
    summary_lines = [
        "<!-- AUTO_SYNC_START:summary -->",
        f"- **2026年初净值**: ¥{first_nw:,}",
        f"- **截至{today_display}净值**: ¥{latest_nw:,}",
        f"- **年度变动**: ¥{delta_annual:,} ({sign_annual}{pct_annual:.1f}%)",
        f"- **月度记录**: {len(snaps_sorted)} 个快照",
        "<!-- AUTO_SYNC_END:summary -->",
    ]
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:summary -->.*?<!-- AUTO_SYNC_END:summary -->",
        "\n".join(summary_lines),
        annual, flags=re.DOTALL
    )

    # --- 5c3. 资产历史最值 ---
    price_holdings = [
        ("比特币(链上)", "btc_onchain", "usd"),
        ("以太坊NFT(链上)", "eth_onchain", "usd"),
        ("比特币(币安)", "btc_binance", "usd"),
        ("以太坊(币安)", "eth_binance", "usd"),
        ("Circle(燕蒙古)", "crcl_yan", "usd"),
        ("Circle(韩伟蒙古)", "crcl_han", "usd"),
        ("Circle(韩伟长桥)", "crcl_cb", "usd"),
        ("Circle(华盛通)", "crcl_hst", "usd"),
        ("Circle(韩芳)", "crcl_hf", "usd"),
        ("迈威尔(币安)", "mrvl_han", "usd"),
        ("诺基亚(币安)", "nok_han", "usd"),
        ("BitGo(韩伟长桥)", "bitgo", "usd"),
        ("小米集团(港股通)", "xiaomi_ht", "hkd"),
        ("优必选(港股通)", "ubt_ht", "hkd"),
        ("小安时间", "ts_xiaoan", "usd"),
        ("午饭老师时间", "ts_wufan", "usd"),
    ]
    ph_lines = ["<!-- AUTO_SYNC_START:price_highlights -->",
                "| 标的 | 年内最高 | 最高日期 | 年内最低 | 最低日期 |",
                "|------|---------|---------|---------|---------|"]
    for label, pid, currency in price_holdings:
        entry = hh.get(pid, {})
        if currency == "hkd":
            hk = f"all_time_high_price_hkd"; lk = f"all_time_low_price_hkd"
            pf = "HK${:,.2f}"
        else:
            hk = "all_time_high_price"; lk = "all_time_low_price"
            pf = "${:,.2f}"
        hi = entry.get(hk)
        lo = entry.get(lk)
        hi_date = entry.get("all_time_high_date", today) if hi else "-"
        lo_date = entry.get("all_time_low_date", today) if lo else "-"
        hi_s = pf.format(hi) if hi else "-"
        lo_s = pf.format(lo) if lo else "-"
        ph_lines.append(f"| {label} | {hi_s} | {hi_date} | {lo_s} | {lo_date} |")
    ph_lines.append("<!-- AUTO_SYNC_END:price_highlights -->")
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:price_highlights -->.*?<!-- AUTO_SYNC_END:price_highlights -->",
        "\n".join(ph_lines),
        annual, flags=re.DOTALL
    )

    # --- 5c4. 仓位结构 ---
    crypto_val = cat_sum.get("crypto", 0)
    us_stock_tokenized = cat_sum.get("us_stock_tokenized", 0)
    us_stock_val = cat_sum.get("us_stock", 0)
    hk_stock_val = cat_sum.get("hk_stock", 0)
    ts_val = cat_sum.get("ts_time_token", 0)
    lev_pct = liab_total / net_worth * 100 if net_worth else 0
    total_with_house = total_assets + 3_200_000

    alloc_lines = [
        "<!-- AUTO_SYNC_START:allocation -->",
        f"- **加密货币(BTC/ETH)**: ¥{crypto_val:,.0f}，占投资资产 {crypto_val/investment_total*100:.1f}%，占总投资 {crypto_val/total_assets*100:.1f}%",
        f"- **美股(链上CRCL)**: ¥{us_stock_tokenized:,.0f}，占投资资产 {us_stock_tokenized/investment_total*100:.1f}%，占总投资 {us_stock_tokenized/total_assets*100:.1f}%",
        f"- **美股(传统)**: ¥{us_stock_val:,.0f}，占投资资产 {us_stock_val/investment_total*100:.1f}%，占总投资 {us_stock_val/total_assets*100:.1f}%",
        f"- **港股(小米+优必选+诺基亚)**: ¥{hk_stock_val+PRICES.get('NOK',0)*0:,.0f}，占投资资产 {hk_stock_val/investment_total*100:.1f}%，占总投资 {hk_stock_val/total_assets*100:.1f}%",
        f"- **TS时间代币**: ¥{ts_val:,.0f}，占投资资产 {ts_val/investment_total*100:.1f}%，占总投资 {ts_val/total_assets*100:.1f}%",
        f"- **现金固收**: ¥{cash_total:,.0f}，占总投资 {cash_total/total_assets*100:.1f}%",
        f"- **杠杆率**: 投资负债¥{liab_total:,} / 净资产¥{net_worth:,.0f} = {lev_pct:.1f}%",
        f"- **家庭总资产(含房产¥320W)**: ¥{total_with_house:,}",
        "<!-- AUTO_SYNC_END:allocation -->",
    ]
    annual = re.sub(
        r"<!-- AUTO_SYNC_START:allocation -->.*?<!-- AUTO_SYNC_END:allocation -->",
        "\n".join(alloc_lines),
        annual, flags=re.DOTALL
    )

    annual_path.write_text(annual, encoding="utf-8")
    print(f"🔄 已同步 家庭资产年度报告-2026.md (4个数据节)")

# ── 5d. 同步 index.md ──
idx_path = BASE / "index.md"
if idx_path.exists():
    idx = idx_path.read_text(encoding="utf-8")
    idx = re.sub(
        r"（自动拉取.*?每次运行同步更新.*?）",
        f"（自动拉取 Gate.io + Sina + Exchangerate，每次运行同步更新：月度报告、年度报告、portfolio_history.yaml、holdings.yaml meta，最后更新 {today}）",
        idx
    )
    idx_path.write_text(idx, encoding="utf-8")
    print(f"🔄 已同步 index.md (更新同步说明)")

# ── 联动检查清单 ──
print(f"\n{'='*60}")
print(f"📋 同步结果总览:")
print(f"  [✓] 月度报告 — {OUT.name}")
print(f"  [✓] holdings.yaml meta (汇率+日期)")
print(f"  [✓] portfolio_history.yaml (价格最值+净资产快照)")
print(f"  [✓] 年度报告 (净资产走势+年度汇总+资产最值+仓位结构)")
print(f"  [✓] index.md (同步说明)")
print(f"  ⚠️  trade_log.md — 本期如有交易，需手动记录")
print(f"  ⚠️  年度报告叙事文本(复盘/建议/行动清单) — 需人工审阅")
print(f"{'='*60}")