"""
三条卖出线每日自动监控脚本 v2
- 线1 (Capex): 监控 MSFT/GOOGL/META/AMZN/NVDA/MRVL 股价 + Capex新闻
- 线2 (ARR): 监控 OpenAI/Anthropic ARR新闻
- 线3 (替代赛道): 市场热点新闻扫描

v2 改进：
- 多源新闻抓取（Yahoo Finance RSS + Bing News RSS）
- 持仓股暴跌专项搜索（>3%跌幅自动拉取该股利空新闻）
- 新闻去重和无效结果清洗
- 告警附带新闻佐证
- 新闻带时间戳和来源标注

用法: python monitor_three_sell_lines.py
输出: reports/three-sell-lines-daily-YYYY-MM-DD.md
"""

import requests, json, re, sys, time, os
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Windows UTF-8 兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 飞书推送模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from push_lark import send_interactive_card, load_secrets
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False
    print("[WARN] push_lark.py 未找到，跳过飞书推送")

BASE = Path(__file__).parent
REPORTS_DIR = BASE / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
out_file = REPORTS_DIR / f"three-sell-lines-daily-{today_str}.md"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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
                prev_close = price - change_amt
                pct = (change_amt / prev_close * 100) if prev_close != 0 else 0
                return price, pct
    except Exception as e:
        print(f"  [股价] {symbol} 获取失败: {e}")
    return None, None


capex_tickers = {
    "MSFT": "gb_msft", "GOOGL": "gb_googl",
    "AMZN": "gb_amzn", "META": "gb_meta",
    "MRVL": "gb_mrvl", "NVDA": "gb_nvda"
}

capex_data = {}
capex_pct = {}  # 单独存涨跌幅用于告警判断
print("【线1】抓取股价...")
for name, sym in capex_tickers.items():
    price, pct = fetch_sina_stock(sym)
    if price is not None:
        sign = "+" if pct >= 0 else ""
        capex_data[name] = f"${price:.2f} ({sign}{pct:.2f}%)"
        capex_pct[name] = pct
        print(f"  {name}: ${price:.2f} ({sign}{pct:.2f}%)")
    else:
        capex_data[name] = "N/A"
        capex_pct[name] = 0

# 持仓映射（用于暴跌专项搜索）
holdings_map = {
    "MRVL": {"shares": 29.192, "value_cny": 59098, "note": "AI芯片/数据中心互连"},
    "GOOGL": {"shares": 7.65, "value_cny": 18579, "note": "七姐妹+Gemini AI"},
}

# ============================================================
# 二、新闻抓取函数（多源 + 去重）
# ============================================================

def fetch_yahoo_finance_rss(ticker, limit=5):
    """Yahoo Finance 个股 RSS — 不需要key，相对稳定"""
    items = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        if r.ok:
            items_block = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
            for block in items_block[:limit]:
                title_m = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', block, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
                date_m = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
                title = ""
                if title_m:
                    title = (title_m.group(1) or title_m.group(2) or "").strip()
                link = link_m.group(1).strip() if link_m else ""
                pub_date = date_m.group(1).strip() if date_m else ""
                if title:
                    items.append({
                        "title": title,
                        "link": link,
                        "source": "Yahoo Finance",
                        "date": pub_date,
                        "ticker": ticker
                    })
    except Exception as e:
        print(f"  [Yahoo RSS] {ticker} 失败: {e}")
    return items


def fetch_bing_news(query, limit=5):
    """Bing News RSS — 备用源，加强过滤无效结果"""
    items = []
    try:
        url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        if r.ok:
            items_block = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
            for block in items_block[:limit*2]:  # 多抓再过滤
                title_m = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
                date_m = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
                title = title_m.group(1).strip() if title_m else ""
                # 过滤无效结果
                if not title:
                    continue
                if title in ["搜索 - Microsoft 必应", "Bing 新闻", "Microsoft 必应"]:
                    continue
                if "必应" in title or "bing.com" in title.lower():
                    continue
                link = link_m.group(1).strip() if link_m else ""
                pub_date = date_m.group(1).strip() if date_m else ""
                items.append({
                    "title": title,
                    "link": link,
                    "source": "Bing News",
                    "date": pub_date,
                    "query": query
                })
    except Exception as e:
        print(f"  [Bing News] '{query}' 失败: {e}")
    return items


def deduplicate(items, key="title"):
    """基于标题相似度去重"""
    seen = []
    result = []
    for item in items:
        title = item.get(key, "").lower()
        is_dup = False
        for s in seen:
            if title == s or (len(title) > 20 and title in s) or (len(s) > 20 and s in title):
                is_dup = True
                break
        if not is_dup:
            seen.append(title)
            result.append(item)
    return result


def filter_by_keywords(items, keywords, limit=5):
    """按关键词过滤新闻"""
    filtered = []
    for item in items:
        title_lower = item["title"].lower()
        if any(kw.lower() in title_lower for kw in keywords):
            filtered.append(item)
    return filtered[:limit]


def format_date(date_str):
    """格式化RFC2822日期为 MM-DD"""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%m-%d")
    except:
        return date_str[:16] if date_str else ""


# ============================================================
# 三、线1 — Capex 新闻
# ============================================================

print("\n【线1】抓取Capex相关新闻...")
capex_news = []

# 财报季才详细查Capex新闻，平时只抓持仓股新闻
is_earnings_season = datetime(2026, 7, 22) <= today <= datetime(2026, 8, 5)
is_monday = today.weekday() == 0

if is_earnings_season or is_monday:
    capex_news.extend(fetch_bing_news("AI capex Microsoft Google Amazon Meta earnings 2026", limit=5))
    capex_news = filter_by_keywords(capex_news,
        ['capex', 'capital expenditure', 'ai spend', 'earnings', 'data center', 'gpu'], limit=5)

# 持仓股新闻（每天都抓）
for ticker in ["MRVL", "GOOGL"]:
    yahoo_items = fetch_yahoo_finance_rss(ticker, limit=5)
    capex_news.extend(yahoo_items)

capex_news = deduplicate(capex_news)[:8]
if not capex_news:
    capex_news.append({"title": "(今日无重大Capex相关新闻)", "source": "", "link": "", "date": ""})

# ============================================================
# 四、线2 — ARR 新闻
# ============================================================

print("\n【线2】抓取ARR新闻...")
arr_news = []
arr_news.extend(fetch_bing_news("OpenAI Anthropic annual recurring revenue ARR 2026", limit=5))
arr_news = filter_by_keywords(arr_news,
    ['openai', 'anthropic', 'arr', 'revenue', 'recurring', 'chatgpt', 'claude'], limit=5)
arr_news = deduplicate(arr_news)[:5]
if not arr_news:
    arr_news.append({"title": "(今日无ARR更新新闻)", "source": "", "link": "", "date": ""})

# ============================================================
# 五、线3 — 替代赛道扫描
# ============================================================

print("\n【线3】抓取替代赛道新闻...")
alt_news = []
alt_news.extend(fetch_bing_news("AI sector rotation new investment theme 2026", limit=5))
alt_news.extend(fetch_bing_news("美股 AI 板块 资金流向 2026", limit=5))
alt_news = deduplicate(alt_news)[:5]
if not alt_news:
    alt_news.append({"title": "(今日无替代赛道信号)", "source": "", "link": "", "date": ""})

# ============================================================
# 六、暴跌股专项搜索（持仓股跌幅>3%时触发）
# ============================================================

print("\n【暴跌股专项搜索】...")
special_news = []
alert_tickers = []
for ticker, pct in capex_pct.items():
    if ticker in holdings_map and pct <= -3:
        alert_tickers.append(ticker)
        print(f"  ⚠️ {ticker} 跌 {pct:.1f}%，专项搜索利空新闻...")
        ticker_news = fetch_yahoo_finance_rss(ticker, limit=5)
        ticker_news.extend(fetch_bing_news(f"{ticker} stock drop news why falling", limit=5))
        ticker_news = deduplicate(ticker_news)[:5]
        for n in ticker_news:
            n["alert_for"] = ticker
        special_news.extend(ticker_news)

# ============================================================
# 七、告警生成（附带新闻佐证）
# ============================================================

alerts = []
for name, pct in capex_pct.items():
    if pct <= -5:
        alerts.append({
            "level": "🚨",
            "ticker": name,
            "pct": pct,
            "msg": f"{name} 单日暴跌 {pct:.1f}%，需要立即关注！"
        })
    elif pct <= -3:
        alerts.append({
            "level": "⚠️",
            "ticker": name,
            "pct": pct,
            "msg": f"{name} 单日跌 {pct:.1f}%，关注是否CapEx相关负面"
        })

if not alerts:
    alerts.append({"level": "✅", "ticker": "", "pct": 0, "msg": "无异常波动"})

# ============================================================
# 八、生成日报
# ============================================================

print("\n生成日报...")
lines = []
lines.append("---")
lines.append(f"date: {today_str}")
lines.append("type: three-sell-lines-daily")
lines.append(f"earnings_season: {is_earnings_season}")
lines.append("---")
lines.append("")
lines.append(f"# 三条卖出线 — 每日监控 ({today_str})")
lines.append("")
lines.append(f"> 自动生成 · {today.strftime('%H:%M')} · v2")
lines.append("")

# 线1 股价
lines.append("## 线1：Capex 股价（代理指标）")
lines.append("")
lines.append("| 公司 | 股价 | 涨跌 | 关联持仓 |")
lines.append("|------|------|------|---------|")
holdings_label = {
    "MRVL": "29.192股 ¥59,098",
    "GOOGL": "7.65股 ¥18,579",
    "NVDA": "— (行业风向标)",
}
for name in ["MSFT", "GOOGL", "AMZN", "META", "MRVL", "NVDA"]:
    val = capex_data.get(name, "N/A")
    pct = capex_pct.get(name, 0)
    price_display = val.split(" (")[0] if val != "N/A" else "N/A"
    pct_str = f"{pct:+.2f}%" if val != "N/A" else "—"
    icon = "🔴" if pct <= -3 else ("🟡" if pct <= -1 else "")
    pct_display = f"{icon} {pct_str}".strip()
    label = holdings_label.get(name, "—")
    lines.append(f"| {name} | {price_display} | {pct_display} | {label} |")
lines.append("")

# 线1 新闻
lines.append("### 📰 Capex / 持仓股新闻")
lines.append("")
for n in capex_news:
    title = n["title"]
    source = n.get("source", "")
    link = n.get("link", "")
    date_display = format_date(n.get("date", ""))
    date_part = f" | {date_display}" if date_display else ""
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}{date_part}")
    else:
        lines.append(f"- {title}{source_part}{date_part}")
lines.append("")

# 暴跌股专项
if special_news:
    lines.append("### 🎯 暴跌股专项新闻")
    lines.append("")
    for n in special_news:
        title = n["title"]
        source = n.get("source", "")
        link = n.get("link", "")
        alert_for = n.get("alert_for", "")
        tag = f"**[{alert_for}]** " if alert_for else ""
        source_part = f" · {source}" if source else ""
        if link:
            lines.append(f"- {tag}[{title}]({link}){source_part}")
        else:
            lines.append(f"- {tag}{title}{source_part}")
    lines.append("")

# 线2
lines.append("## 线2：ARR 新闻（OpenAI / Anthropic）")
lines.append("")
for n in arr_news:
    title = n["title"]
    source = n.get("source", "")
    link = n.get("link", "")
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}")
    else:
        lines.append(f"- {title}{source_part}")
lines.append("")

# 线3
lines.append("## 线3：替代赛道扫描")
lines.append("")
for n in alt_news:
    title = n["title"]
    source = n.get("source", "")
    link = n.get("link", "")
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}")
    else:
        lines.append(f"- {title}{source_part}")
lines.append("")

# 告警
lines.append("## ⚡ 今日告警")
lines.append("")
for a in alerts:
    lines.append(f"- {a['level']} {a['msg']}")
lines.append("")

# 状态
days_to_earnings = (datetime(2026, 7, 22) - today).days
if days_to_earnings > 0:
    lines.append(f"> 📅 距Q2财报季（7月22日）还有 **{days_to_earnings}** 天，股价为早期预警，非卖出信号")
else:
    lines.append("> 🔴 已进入Q2财报季！请每日关注Capex新闻")
lines.append("")
lines.append("---")
lines.append("相关文档：[[ai-stock-three-sell-lines-methodology]]")
lines.append("> 数据源：新浪财经（股价）+ Yahoo Finance RSS + Bing News RSS")

# 写入
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ 日报已生成: {out_file.name}")
print(f"   股价: {len(capex_data)}只 | Capex新闻: {len(capex_news)}条 | 暴跌专项: {len(special_news)}条")
print(f"   ARR新闻: {len(arr_news)}条 | 替代赛道: {len(alt_news)}条 | 告警: {len(alerts)}条")

# 关键日期提醒
if days_to_earnings in [7, 3, 1, 0]:
    print(f"\n{'='*50}")
    print(f"🔔 提醒：距Q2财报季还有 {days_to_earnings} 天！")
    print(f"   请关注 MSFT/GOOGL/META/AMZN Capex数据")
    print(f"{'='*50}")

# 如果有告警，打印醒目提醒
if alert_tickers:
    print(f"\n{'='*50}")
    print(f"🚨 持仓股告警: {', '.join(alert_tickers)}")
    print(f"{'='*50}")


# ============================================================
# 九、飞书推送（interactive卡片）
# ============================================================

def build_lark_card():
    """构建飞书 interactive 卡片 JSON"""
    elements = []

    # --- 线1 股价表 ---
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "**线1：Capex 股价（代理指标）**"}
    })
    table_lines = ["| 公司 | 股价 | 涨跌 | 持仓 |", "|---|---|---|---|"]
    holdings_label = {
        "MRVL": "29.192股 ¥59,098",
        "GOOGL": "7.65股 ¥18,579",
        "NVDA": "风向标",
    }
    for name in ["MSFT", "GOOGL", "AMZN", "META", "MRVL", "NVDA"]:
        val = capex_data.get(name, "N/A")
        pct = capex_pct.get(name, 0)
        price_display = val.split(" (")[0] if val != "N/A" else "N/A"
        icon = "🔴" if pct <= -3 else ("🟡" if pct <= -1 else "")
        pct_str = f"{icon}{pct:+.2f}%" if val != "N/A" else "—"
        label = holdings_label.get(name, "—")
        table_lines.append(f"| {name} | {price_display} | {pct_str} | {label} |")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(table_lines)}
    })

    # --- 线1 新闻（前3条） ---
    elements.append({"tag": "hr"})
    news_lines = ["**📰 Capex/持仓股新闻**"]
    for n in capex_news[:3]:
        title = n["title"]
        source = n.get("source", "")
        date_d = n.get("date", "")[:11] if n.get("date") else ""
        source_part = f" · {source}" if source else ""
        date_part = f" · {date_d}" if date_d else ""
        news_lines.append(f"- {title}{source_part}{date_part}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(news_lines)}
    })

    # --- 线2 ARR ---
    elements.append({"tag": "hr"})
    arr_lines = ["**线2：ARR 新闻（OpenAI/Anthropic）**"]
    for n in arr_news[:3]:
        title = n["title"]
        source = n.get("source", "")
        source_part = f" · {source}" if source else ""
        arr_lines.append(f"- {title}{source_part}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(arr_lines)}
    })

    # --- 告警 ---
    elements.append({"tag": "hr"})
    alert_lines = ["**⚡ 今日告警**"]
    for a in alerts:
        alert_lines.append(f"- {a['level']} {a['msg']}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(alert_lines)}
    })

    # --- 页脚 ---
    elements.append({"tag": "hr"})
    footer = f"📅 距Q2财报季（7月22日）还有 {days_to_earnings} 天 | 数据源：新浪财经+Yahoo Finance+Bing News"
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": footer}]
    })

    # 根据告警级别选卡片颜色
    has_alert = any(a["level"] in ("🚨", "⚠️") for a in alerts)
    header_color = "red" if has_alert else "blue"
    header_title = f"🔴 三条卖出线监控 | {today_str}" if has_alert else f"三条卖出线监控 | {today_str}"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": header_title},
            "template": header_color,
        },
        "elements": elements,
    }
    return card


# 飞书推送
if LARK_AVAILABLE:
    print("\n【飞书推送】发送 interactive 卡片...")
    try:
        secrets = load_secrets()
        card = build_lark_card()
        card_str = json.dumps(card, ensure_ascii=False)
        print(f"  卡片 JSON 长度: {len(card_str)} 字符")
        message_id = send_interactive_card(
            secrets["chat_id"], card,
            app_id=secrets["app_id"], app_secret=secrets["app_secret"]
        )
        print(f"  ✅ 飞书推送成功！message_id: {message_id}")
    except Exception as e:
        print(f"  ❌ 飞书推送失败: {e}")
else:
    print("\n【飞书推送】跳过（push_lark.py 不可用）")
