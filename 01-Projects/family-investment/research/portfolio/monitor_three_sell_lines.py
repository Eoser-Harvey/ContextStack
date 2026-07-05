"""
三条卖出线每日自动监控脚本
- 线1 (Capex): 监控 MSFT/GOOGL/META/AMZN 股价 + Capex新闻
- 线2 (ARR): 监控 OpenAI/Anthropic ARR新闻
- 线3 (替代赛道): 市场热点新闻扫描

用法: python monitor_three_sell_lines.py
输出: reports/three-sell-lines-daily-YYYY-MM-DD.md
"""

import requests, json, re, sys
from pathlib import Path
from datetime import datetime, timedelta

# Windows UTF-8 兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent
REPORTS_DIR = BASE / "reports"
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
out_file = REPORTS_DIR / f"three-sell-lines-daily-{today_str}.md"

# ============================================================
# 一、线1 — Capex监控：拉取关键公司股价（代理指标）
# ============================================================

def fetch_sina_stock(symbol):
    """新浪实时股价 — 美股gb_格式: 0=名称,1=现价,2=涨跌额,3=时间"""
    try:
        r = requests.get(f"https://hq.sinajs.cn/list={symbol}", timeout=10,
                         headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = "gbk"
        if '"' in r.text:
            parts = r.text.split('"')[1].split(",")
            if len(parts) > 2 and parts[1]:
                price = float(parts[1])
                change_amt = float(parts[2]) if parts[2] else 0
                # 用涨跌额计算涨跌幅
                prev_close = price - change_amt
                pct = (change_amt / prev_close * 100) if prev_close != 0 else 0
                return price, pct
    except:
        pass
    return None, None

capex_tickers = {
    "MSFT": "gb_msft", "GOOGL": "gb_googl",
    "AMZN": "gb_amzn", "META": "gb_meta",
    "MRVL": "gb_mrvl", "NVDA": "gb_nvda"
}

capex_data = {}
for name, sym in capex_tickers.items():
    price, pct = fetch_sina_stock(sym)
    if price:
        sign = "+" if pct >= 0 else ""
        capex_data[name] = f"${price:.2f} ({sign}{pct:.2f}%)"
        print(f"  {name}: ${price:.2f} ({sign}{pct:.2f}%)")
    else:
        capex_data[name] = "N/A"
        print(f"  {name}: 获取失败")

# ============================================================
# 二、线1补充 — 搜索Capex相关新闻（只在季报季或每周一次详细查）
# ============================================================

# 工作日标记：周一和周二是财报季关键期（7月22日起）
is_earnings_season = today >= datetime(2026, 7, 22) and today <= datetime(2026, 8, 5)
is_monday = today.weekday() == 0

capex_news = []
if is_earnings_season or is_monday:
    try:
        url = "https://news.google.com/rss/search?q=AI+capex+Microsoft+Google+Amazon+Meta+earnings&hl=en-US&ceid=US:en"
        # Google News RSS 经常被墙，改用 Bing
        url_bing = f"https://www.bing.com/news/search?q=AI+capital+expenditure+earnings+2026&format=rss"
        r = requests.get(url_bing, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            items = re.findall(r'<title>(.*?)</title>', r.text)
            # 过滤掉XML头
            for t in items[:5]:
                if any(kw in t.lower() for kw in ['capex', 'capital expenditure', 'ai spend', 'earnings']):
                    capex_news.append(t)
        if not capex_news:
            capex_news.append("(无重大Capex新闻)")
    except:
        capex_news.append("(新闻抓取失败)")

# ============================================================
# 三、线2 — ARR监控：OpenAI/Anthropic收入新闻
# ============================================================

arr_news = []
try:
    r = requests.get("https://www.bing.com/news/search?q=OpenAI+Anthropic+annual+recurring+revenue+ARR&format=rss",
                     timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    if r.ok:
        items = re.findall(r'<title>(.*?)</title>', r.text)
        for t in items[:5]:
            if any(kw in t.lower() for kw in ['openai', 'anthropic', 'arr', 'revenue', 'recurring']):
                arr_news.append(t)
    if not arr_news:
        arr_news.append("(无ARR更新新闻)")
except:
    arr_news.append("(新闻抓取失败)")

# ============================================================
# 四、线3 — 替代赛道扫描
# ============================================================

alt_track_news = []
try:
    r = requests.get("https://www.bing.com/news/search?q=AI+sector+rotation+new+theme+2026&format=rss",
                     timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    if r.ok:
        items = re.findall(r'<title>(.*?)</title>', r.text)
        for t in items[:5]:
            alt_track_news.append(t)
    if not alt_track_news:
        alt_track_news.append("(无替代赛道新闻)")
except:
    alt_track_news.append("(新闻抓取失败)")

# ============================================================
# 五、快速判断 — 是否需要人工关注
# ============================================================

alerts = []
# 简单规则：任意股票单日跌幅 > 3% 提示
for name, val in capex_data.items():
    if "(" in val and "N/A" not in val:
        try:
            pct_str = val.split("(")[1].replace("%)","").replace("%","")
            pct = float(pct_str)
            if pct <= -5:
                alerts.append(f"🚨 {name} 单日暴跌 {pct:.1f}%，需要立即关注！")
            elif pct <= -3:
                alerts.append(f"⚠️ {name} 单日跌 {pct:.1f}%，关注是否CapEx相关负面")
        except:
            pass

if not alerts:
    alerts.append("✅ 无异常波动")

# ============================================================
# 六、生成日报
# ============================================================

lines = []
lines.append(f"---")
lines.append(f"date: {today_str}")
lines.append(f"type: three-sell-lines-daily")
lines.append(f"earnings_season: {is_earnings_season}")
lines.append(f"---\n")
lines.append(f"# 三条卖出线 — 每日监控 ({today_str})\n")
lines.append(f"> 自动生成 · {today.strftime('%H:%M')}\n")

# 线1
lines.append("## 线1：Capex 股价（代理指标）\n")
lines.append("| 公司 | 股价 | 关联持仓 |")
lines.append("|------|------|---------|")
lines.append(f"| MSFT | {capex_data.get('MSFT','N/A')} | — |")
lines.append(f"| GOOGL | {capex_data.get('GOOGL','N/A')} | 7.65股 ¥18,579 |")
lines.append(f"| AMZN | {capex_data.get('AMZN','N/A')} | — |")
lines.append(f"| META | {capex_data.get('META','N/A')} | — |")
lines.append(f"| MRVL | {capex_data.get('MRVL','N/A')} | 29.192股 ¥59,098 |")
lines.append(f"| NVDA | {capex_data.get('NVDA','N/A')} | — (行业风向标) |\n")

if capex_news:
    lines.append("### Capex 新闻\n")
    for n in capex_news:
        lines.append(f"- {n}")
    lines.append("")

# 线2
lines.append("## 线2：ARR 新闻\n")
for n in arr_news:
    lines.append(f"- {n}")
lines.append("")

# 线3
lines.append("## 线3：替代赛道扫描\n")
for n in alt_track_news:
    lines.append(f"- {n}")
lines.append("")

# 告警
lines.append("## ⚡ 今日告警\n")
for a in alerts:
    lines.append(f"- {a}")
lines.append("")

# 状态
days_to_earnings = (datetime(2026, 7, 22) - today).days
if days_to_earnings > 0:
    lines.append(f"> 📅 距Q2财报季（7月22日）还有 **{days_to_earnings}** 天，股价为早期预警，非卖出信号\n")
else:
    lines.append(f"> 🔴 已进入Q2财报季！请每日关注Capex新闻\n")

lines.append("---")
lines.append(f"相关文档：[[ai-stock-three-sell-lines-methodology]]")

# 写入
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ 日报已生成: {out_file.name}")

# ============================================================
# 七、关键日期提醒
# ============================================================
if days_to_earnings in [7, 3, 1, 0]:
    print(f"\n{'='*50}")
    print(f"🔔 提醒：距Q2财报季还有 {days_to_earnings} 天！")
    print(f"   请关注 MSFT/GOOGL/META/AMZN Capex数据")
    print(f"{'='*50}")
