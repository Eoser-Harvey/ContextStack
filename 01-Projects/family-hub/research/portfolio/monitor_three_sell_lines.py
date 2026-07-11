"""
三条卖出线每日自动监控脚本 v4
- 线1 (Capex): 监控 MSFT/GOOGL/META/AMZN/NVDA/MRVL 股价 + Capex新闻 + 投资建议
- 线2 (ARR): 监控 OpenAI/Anthropic ARR新闻 + 投资建议
- 线3 (替代赛道): 美股板块ETF资金流向 + 行业轮动信号
- 新闻翻译: 英文新闻自动翻译为中文
- 投资建议: 基于方法论场景A/B/C，止盈止损 + 上车信号

用法: python monitor_three_sell_lines.py
输出: reports/three-sell-lines-daily-YYYY-MM-DD.md + 飞书推送
"""

import requests, json, re, sys, time, os, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Windows UTF-8 兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 飞书推送模块（从参考项目复制，未修改）
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
# 零、新闻翻译引擎（本地规则翻译）
# ============================================================

TRANSLATION_CACHE_FILE = BASE / ".translation_cache.json"

def _load_translation_cache():
    if TRANSLATION_CACHE_FILE.exists():
        try:
            return json.loads(TRANSLATION_CACHE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def _save_translation_cache(cache):
    TRANSLATION_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

# 金融术语映射表（英→中）
FINANCE_TERMS = {
    # 公司/机构
    "Marvell Technology": "迈威尔科技",
    "Marvell": "迈威尔",
    "Broadcom": "博通",
    "Cantor Fitzgerald": "Cantor Fitzgerald投行",
    "Berkshire Hathaway": "伯克希尔哈撒韦",
    "Alphabet": "Alphabet(谷歌母公司)",
    "Goldman Sachs": "高盛",
    "Lumentum": "Lumentum",
    "SK Hynix": "SK海力士",
    "Roundhill": "Roundhill",
    # 动作
    "Raises PT": "上调目标价",
    "Raises Price Target": "上调目标价",
    "Lowers PT": "下调目标价",
    "Upgrades": "上调评级",
    "Downgrades": "下调评级",
    "Strong Buy": "强烈买入",
    "Buy More": "增持",
    "Sell-Off": "抛售",
    "Rally": "上涨/反弹",
    "Pullback": "回调",
    "Surge": "飙升",
    "Plunge": "暴跌",
    "Beat": "超预期",
    "Miss": "不及预期",
    "Earnings": "财报",
    "Revenue": "营收",
    "Profit": "利润",
    "Match": "匹配",
    "Powering": "驱动",
    "Cashing In": "获利",
    "Challenge": "挑战",
    # 指标
    "YTD": "年内至今",
    "Quarterly": "季度",
    "Annual": "年度",
    "Market Cap": "市值",
    "Dividend": "股息",
    "P/E Ratio": "市盈率",
    "Growth": "增长",
    "Decline": "下降",
    "Outlook": "展望",
    "Forecast": "预测",
    "Guidance": "指引",
    "AUM": "管理资产规模",
    # 场景
    "Bullish": "看涨",
    "Bearish": "看跌",
    "Volatility": "波动",
    "Momentum": "动能",
    "Rebound": "反弹",
    "Correction": "回调/修正",
    "Crash": "崩盘",
    "Under the Radar": "低调的",
    "Runaway": "暴涨的",
    # 产品/行业
    "Semiconductor": "半导体",
    "Chip": "芯片",
    "Data Center": "数据中心",
    "AI": "人工智能",
    "Cloud": "云计算",
    "GPU": "图形处理器",
    "Memory": "存储",
    "Active Electrical Cables": "有源电缆",
    "Optical Networking": "光网络",
    "Crypto": "加密货币",
    "Quantum Security": "量子安全",
    "Encryption": "加密",
    # 常见句式
    "Still Have A Lot More Upside": "仍有较大上行空间",
    "Trades at a Discount": "折价交易",
    "Why Arm Is a Strong Buy Despite the": "为何Arm在经历...后仍值得买入",
    "How Much": "到底押注了多少",
    "Are You Really Betting On": "你到底在押注什么",
    "Reveals Why He Still Likes": "透露为何仍看好",
    "Here Are": "以下是",
    "Possible Reasons Why": "可能的原因",
    "ETF Inflows Top": "ETF资金流入突破",
    "at the Halfway Point of": "在...年中节点",
    "Is the Memory Rally Still Alive After": "存储芯片反弹在...后是否仍在",
    "Thoughts on": "对...的看法",
    "Why It May": "为何它可能",
    "Driving": "推动",
    "Despite": "尽管",
    "Peak Levels": "高点",
    "Buy More": "继续买入",
    "Investors": "投资者",
    "Analyst": "分析师",
    "Wall Street": "华尔街",
    "Got $10,000?": "手上有$10,000？",
    "Only One Will Match The": "只有一家能匹配",
    "Hype": "炒作热潮",
    "Chart of the Day": "今日图表",
    "Big Tech is paying for the": "科技巨头正在为",
    "and chipmakers are cashing in": "买单，芯片制造商从中获利",
    "Steps Up": "加速推进",
    "as Risks Accelerate": "随着风险加剧",
    "Sets Stage for": "为...铺路",
    "Trading Debut": "交易首秀",
    "Line Up to": "排队",
    "New Memory ETFs": "新存储ETF",
    "Nears $34B": "逼近340亿美元",
    "Under the Radar AI Chip Stocks": "低调的AI芯片股",
    "Next Trillion-Dollar Opportunity": "下一个万亿机会",
    "May Be the Biggest Winner": "可能是最大赢家",
    # 更多常见词（短词放后面避免误匹配）
    "Boom": "繁荣",
    "Paying for the": "为...买单",
    "Chipmakers": "芯片制造商",
    "League Tables": "排行榜",
    "Optical Networking": "光网络",
    "Steps Up Quantum Security Efforts": "加速量子安全布局",
    "as Encryption Risks Accelerate": "加密风险加剧",
    "Surge Sets Stage for": "飙升为...铺路",
    "U.S. Trading Debut": "美国交易首秀",
    "Line Up to Challenge": "排队挑战",
    "Runaway": "暴涨",
    "Runaway DRAM": "暴涨的DRAM",
    # 翻译引擎通用词（解决"高盛 Says"、"Synopsys 股票"这类半成品）
    " Says ": "称",
    " Is ": "",
    "Says ": "称",
    "Will Be Worth This In": "2030年估值将达到",
    "Price Prediction: ": "估值预测：",
    "Sector Update: ": "板块快讯：",
    "Advance Late Afternoon": "午后走高",
    "The Nuclear Energy Comeback Is Real. These 3 Energy ": "核能复苏是真的。这3只能源",
    "Are the Best Ways to Play the Revival.": "是布局复苏的最佳选择。",
    "Dow Jones Futures: Watch ": "道指期货：关注",
    "As Market Sets Up; Big ": "市场蓄势待发；重磅",
    "Due": "即将公布",
    "Why Today\u2019s Small ": "为什么今天微小的",
    "Could Become Tomorrow\u2019s Retirement Engine": "可能成为明天的退休引擎",
    "ETF Showdown Traditional Energy Meets Clean Energy. Which ETF Is the Better Buy?": "ETF对决：传统能源vs清洁能源，哪个更值得买入？",
    "人工智能's": "AI的",
    "AI's": "AI的",
    " Is Bullish on ": "看涨",
    "Bullish on ": "看涨",
    "Here Is What a": "看看",
    "Investment Could Return": "投资可能获得多少回报",
    "Here Is What": "看看",
    "Energy Stocks ": "能源股",
    "Taiwan 半导体's": "台积电",
    "Taiwan Semiconductor's": "台积电",
    "Nvidia CEO Jensen Huang Said ": "英伟达CEO黄仁勋称",
    "\"Most Profound Impact Will Be in Life Sciences.\" Does This Bet on a Biotech Stock Prove He Means It?": "\"最深远影响将在生命科学领域\"，这笔生物科技股投资能证明他此言不虚吗？",
    "Prediction: ": "预测：",
    "Will Soar on July 17": "将在7月17日飙升",
    " 半导体's Stock Will Soar on July 17": "将在7月17日飙升",
    "台积电 Stock ": "台积电",
    # 注意：不把 Stock/Stocks/Shares 放这里了，容易产生 "Synopsys 股票" 这种半成品
    "Got $10,000? Broadcom vs Marvell: Only One Will Match The AI Hype": "手上有$10,000？博通vs迈威尔：只有一家能匹配AI热潮",
    "5 Under the Radar AI Chip Stocks Powering the Data Center Boom": "5只低调AI芯片股推动数据中心繁荣",
    "Goldman Sachs Says Optical Networking Is AI's Next Trillion-Dollar Opportunity. Lumentum May Be the Biggest Winner": "高盛称光网络是AI的下一个万亿机会，Lumentum或是最大赢家",
    "Crypto Industry Steps Up Quantum Security Efforts as Encryption Risks Accelerate": "加密货币行业加速量子安全布局，加密风险加剧",
    "Big Tech is paying for the AI boom, and chipmakers are cashing in: Chart of the Day": "科技巨头为AI繁荣买单，芯片制造商从中获利：今日图表",
    "ETF League Tables: Roundhill AUM Nears $34B": "ETF排行榜：Roundhill管理资产规模逼近340亿美元",
    "Memory Stock Surge Sets Stage for SK Hynix's U.S. Trading Debut": "存储股飙升为SK海力士美国交易首秀铺路",
    "New Memory ETFs Line Up to Challenge Runaway DRAM": "新存储ETF排队挑战暴涨的DRAM",
}

def translate_en_to_zh(text):
    """翻译英文标题到中文：先查缓存，再用本地术语映射"""
    if not text:
        return text
    if not any(c.isascii() and c.isalpha() for c in text):
        return text

    cache = _load_translation_cache()
    cache_key = hashlib.md5(text.encode()).hexdigest()
    if cache_key in cache:
        return cache[cache_key]

    result = text
    # 按术语长度降序替换（长术语优先，避免部分匹配）
    sorted_terms = sorted(FINANCE_TERMS.items(), key=lambda x: len(x[0]), reverse=True)
    for en_term, zh_term in sorted_terms:
        result = result.replace(en_term, zh_term)

    # 去掉多余空格
    result = re.sub(r'\s+', ' ', result).strip()

    if result != text:
        cache[cache_key] = result
        _save_translation_cache(cache)
        return result

    return text

def translate_news_items(items):
    """批量翻译新闻条目的 title"""
    for item in items:
        if item.get("title") and "(" not in item["title"][:1]:  # 跳过占位文本
            item["title_zh"] = translate_en_to_zh(item["title"])
        else:
            item["title_zh"] = item.get("title", "")
    return items

# ============================================================
# 一、线1 — Capex监控：拉取关键公司股价
# ============================================================

def fetch_sina_stock(symbol):
    """新浪实时股价 — 美股gb_格式"""
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
                return price, pct, prev_close
    except Exception as e:
        print(f"  [股价] {symbol} 获取失败: {e}")
    return None, None, None

capex_tickers = {
    "MSFT": "gb_msft", "GOOGL": "gb_googl",
    "AMZN": "gb_amzn", "META": "gb_meta",
    "MRVL": "gb_mrvl", "NVDA": "gb_nvda"
}

# 持仓映射（从 holdings.yaml 同步）
# GOOGL 币安已于 2026-07-07 清仓，DRAM 币安已加仓至 57 股均价 $66.85
holdings_map = {
    "MRVL": {"shares": 29.192, "value_cny": 59098, "cost_usd": 287.74, "note": "AI芯片/数据中心互连(币安)", "line": "线1"},
    "DRAM": {"shares": 57, "value_cny": 18570, "cost_usd": 66.85, "note": "AI服务器存储(币安)", "line": "线1"},
}

capex_data = {}
capex_pct = {}
capex_price = {}
print("【线1】抓取股价...")
for name, sym in capex_tickers.items():
    price, pct, prev_close = fetch_sina_stock(sym)
    if price is not None:
        sign = "+" if pct >= 0 else ""
        capex_data[name] = f"${price:.2f} ({sign}{pct:.2f}%)"
        capex_pct[name] = pct
        capex_price[name] = price
        print(f"  {name}: ${price:.2f} ({sign}{pct:.2f}%)")
    else:
        capex_data[name] = "N/A"
        capex_pct[name] = 0
        capex_price[name] = None

# ============================================================
# 二、新闻抓取函数
# ============================================================

def fetch_yahoo_finance_rss(ticker, limit=5):
    """Yahoo Finance 个股 RSS — 含 description 摘要"""
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
                desc_m = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
                title = ""
                if title_m:
                    title = (title_m.group(1) or title_m.group(2) or "").strip()
                link = link_m.group(1).strip() if link_m else ""
                pub_date = date_m.group(1).strip() if date_m else ""
                # 抓取摘要（去掉HTML标签，截取前200字符）
                desc = ""
                if desc_m:
                    raw_desc = desc_m.group(1).strip()
                    raw_desc = re.sub(r'<[^>]+>', '', raw_desc)  # 去HTML标签
                    raw_desc = re.sub(r'&[a-z]+;', ' ', raw_desc)  # 去HTML实体
                    desc = raw_desc[:200].strip()
                if title:
                    items.append({
                        "title": title,
                        "link": link, "source": "Yahoo Finance",
                        "date": pub_date, "ticker": ticker,
                        "desc": desc
                    })
    except Exception as e:
        print(f"  [Yahoo RSS] {ticker} 失败: {e}")
    return items

def fetch_bing_news(query, limit=5):
    """Bing News RSS"""
    items = []
    try:
        url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        if r.ok:
            items_block = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
            for block in items_block[:limit*2]:
                title_m = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
                date_m = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
                title = title_m.group(1).strip() if title_m else ""
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
                    "link": link, "source": "Bing News",
                    "date": pub_date, "query": query
                })
    except Exception as e:
        print(f"  [Bing News] '{query}' 失败: {e}")
    return items

def deduplicate(items, key="title"):
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
    filtered = []
    for item in items:
        title_lower = item["title"].lower()
        if any(kw.lower() in title_lower for kw in keywords):
            filtered.append(item)
    return filtered[:limit]

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%m-%d")
    except:
        return date_str[:16] if date_str else ""

# ============================================================
# 三、线1 — Capex 新闻（Yahoo RSS 多 ticker 聚合）
# ============================================================

print("\n【线1】抓取Capex相关新闻...")
is_earnings_season = datetime(2026, 7, 22) <= today <= datetime(2026, 8, 5)
is_monday = today.weekday() == 0

# Yahoo RSS 覆盖的 ticker：持仓股 + 七姐妹 + 半导体/AI相关
# 每个 ticker 取5条，聚合去重
capex_ticker_list = ["MRVL", "DRAM", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "SMH", "AVGO", "AMD"]
if is_earnings_season or is_monday:
    # 财报季或周一加大覆盖
    capex_ticker_list.extend(["INTC", "ARM", "TSM", "MU"])

capex_news = []
for ticker in capex_ticker_list:
    yahoo_items = fetch_yahoo_finance_rss(ticker, limit=5)
    capex_news.extend(yahoo_items)

# 始终按关键词做宽松筛选（提升相关性），财报季/周一更严格
if is_earnings_season or is_monday:
    capex_news = filter_by_keywords(capex_news,
        ['capex', 'capital expenditure', 'ai spend', 'earnings', 'data center', 'gpu', 'chip', 'semiconductor', 'cloud',
         'revenue', 'guidance', 'upgrade', 'downgrade', 'analyst', 'price target', 'buy', 'sell'], limit=15)
else:
    # 非财报季：宽松过滤，保留大部分新闻
    capex_news = filter_by_keywords(capex_news,
        ['capex', 'ai', 'chip', 'cloud', 'data center', 'gpu', 'semiconductor', 'earnings', 'revenue',
         'upgrade', 'downgrade', 'analyst', 'price target', 'buy', 'sell', 'bullish', 'bearish',
         'guidance', 'growth', 'market', 'stock', 'investor', 'fund', 'etf', 'tech', 'nvidia', 'amd'], limit=15)

capex_news = deduplicate(capex_news)[:15]
if not capex_news:
    capex_news.append({"title": "(今日无重大Capex相关新闻)", "source": "", "link": "", "date": ""})

# 翻译
capex_news = translate_news_items(capex_news)

# ============================================================
# 四、线2 — ARR 新闻（Yahoo RSS AI/科技 ticker + 关键词过滤）
# ============================================================

print("\n【线2】抓取ARR新闻...")
# 策略：从AI/科技相关ticker的新闻中筛选OpenAI/Anthropic相关内容
# 扩大ticker覆盖：加AVGO/AMD/TSM/MU，增加AI产业链新闻量
arr_ticker_list = ["MSFT", "GOOGL", "META", "NVDA", "AMZN", "AVGO", "AMD", "TSM"]
arr_news = []
for ticker in arr_ticker_list:
    yahoo_items = fetch_yahoo_finance_rss(ticker, limit=5)
    arr_news.extend(yahoo_items)

# 关键词过滤：OpenAI/Anthropic/ARR/ChatGPT/Claude/AI revenue（宽松版，limit提升到10）
arr_news = filter_by_keywords(arr_news,
    ['openai', 'anthropic', 'arr', 'revenue', 'recurring', 'chatgpt', 'claude', 'ai model', 'llm', 'gemini', 'copilot',
     'ai ', 'artificial intelligence', 'machine learning', 'cloud', 'data center', 'gpu', 'chip', 'semiconductor',
     'growth', 'earnings', 'guidance', 'analyst', 'upgrade', 'downgrade', 'price target', 'buy', 'sell',
     'nvidia', 'amd', 'broadcom', 'google', 'microsoft', 'amazon', 'meta'], limit=12)
arr_news = deduplicate(arr_news)[:8]

# 如果过滤后仍为空，展示AI行业通用新闻作为替代（扩大fallback覆盖）
if not arr_news:
    # 重新抓取不限关键词的AI相关新闻
    arr_fallback = []
    for ticker in ["MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD"]:
        yahoo_items = fetch_yahoo_finance_rss(ticker, limit=3)
        arr_fallback.extend(yahoo_items)
    arr_fallback = filter_by_keywords(arr_fallback,
        ['ai ', 'openai', 'anthropic', 'model', 'artificial intelligence', 'chatgpt', 'claude', 'gemini', 'llm',
         'chip', 'gpu', 'cloud', 'data center', 'revenue', 'growth', 'earnings', 'tech', 'nvidia', 'amd'], limit=6)
    arr_news = deduplicate(arr_fallback)[:5]

if not arr_news:
    arr_news.append({"title": "(今日无ARR更新新闻，ARR增速为季度数据，下次关键节点9月底)", "source": "", "link": "", "date": ""})

arr_news = translate_news_items(arr_news)

# ============================================================
# 五、线3 — 美股板块ETF资金流向 + 替代赛道扫描
# ============================================================

print("\n【线3】抓取美股板块数据...")
alt_news = []
alt_data = {}

# 5.1 美股主要板块ETF（新浪）
sector_etfs = {
    "QQQ": ("gb_qqq", "纳斯达克100"),
    "SPY": ("gb_spy", "标普500"),
    "XLK": ("gb_xlk", "科技板块"),
    "XLY": ("gb_xly", "可选消费"),
    "XLF": ("gb_xlf", "金融板块"),
    "XLE": ("gb_xle", "能源板块"),
}

for name, (sym, label) in sector_etfs.items():
    price, pct, _ = fetch_sina_stock(sym)
    if price is not None:
        alt_data[name] = {"price": price, "pct": pct, "label": label}
        print(f"  {name} ({label}): ${price:.2f} ({pct:+.2f}%)")
    else:
        alt_data[name] = {"price": None, "pct": 0, "label": label}

# 5.2 板块轮动信号
# 判断: 科技(QQQ+XLK) vs 其他板块的相对强弱
tech_pct = (alt_data.get("QQQ", {}).get("pct", 0) + alt_data.get("XLK", {}).get("pct", 0)) / 2
other_pct = (alt_data.get("XLY", {}).get("pct", 0) + alt_data.get("XLF", {}).get("pct", 0) + alt_data.get("XLE", {}).get("pct", 0)) / 3

if tech_pct > other_pct + 0.5:
    rotation_signal = "🟢 资金仍在科技/AI主线，无轮动信号"
elif tech_pct < other_pct - 0.5:
    rotation_signal = "🟡 资金从科技流向传统板块，关注轮动风险"
elif tech_pct < other_pct - 1.0:
    rotation_signal = "🔴 科技板块明显跑输，替代赛道信号加强"
else:
    rotation_signal = "⚪ 板块无明显分化，中性"

# 5.3 替代赛道新闻（从板块ETF相关ticker获取）
# 用 SPY/QQQ/XLF 相关关键词的 ticker 来获取板块轮动新闻
alt_news.extend(fetch_yahoo_finance_rss("SPY", limit=3))
alt_news.extend(fetch_yahoo_finance_rss("XLE", limit=2))
alt_news = filter_by_keywords(alt_news,
    ['sector', 'rotation', 'energy', 'financial', 'consumer', 'value', 'growth', 'defensive', 'cyclical'], limit=5)
alt_news = deduplicate(alt_news)[:5]
if not alt_news:
    alt_news.append({"title": "(今日无替代赛道信号)", "source": "", "link": "", "date": ""})

alt_news = translate_news_items(alt_news)

# ============================================================
# 六、暴跌股专项搜索
# ============================================================

print("\n【暴跌股专项搜索】...")
special_news = []
alert_tickers = []
for ticker, pct in capex_pct.items():
    if ticker in holdings_map and pct <= -3:
        alert_tickers.append(ticker)
        print(f"  ⚠️ {ticker} 跌 {pct:.1f}%，专项搜索利空新闻...")
        ticker_news = fetch_yahoo_finance_rss(ticker, limit=8)
        ticker_news = deduplicate(ticker_news)[:5]
        for n in ticker_news:
            n["alert_for"] = ticker
        special_news.extend(ticker_news)

special_news = translate_news_items(special_news)

# ============================================================
# 七、告警生成
# ============================================================

alerts = []
for name, pct in capex_pct.items():
    if pct <= -5:
        alerts.append({
            "level": "🚨", "ticker": name, "pct": pct,
            "msg": f"{name} 单日暴跌 {pct:.1f}%，需要立即关注！"
        })
    elif pct <= -3:
        alerts.append({
            "level": "⚠️", "ticker": name, "pct": pct,
            "msg": f"{name} 单日跌 {pct:.1f}%，关注是否CapEx相关负面"
        })

if not alerts:
    alerts.append({"level": "✅", "ticker": "", "pct": 0, "msg": "无异常波动"})

# ============================================================
# 八、投资建议引擎
# ============================================================

print("\n【投资建议引擎】计算中...")
days_to_earnings = (datetime(2026, 7, 22) - today).days

# 8.1 持仓盈亏计算
position_advice = []
for ticker, h in holdings_map.items():
    current_price = capex_price.get(ticker)
    if current_price is None:
        continue

    cost = h["cost_usd"]
    shares = h["shares"]
    pnl_pct = (current_price - cost) / cost * 100
    pnl_usd = (current_price - cost) * shares
    pnl_cny = pnl_usd * 6.796

    # 从最高点回撤（用新浪前一交易日收盘价作为近似）
    if pnl_pct >= 0:
        pnl_status = f"🟢 盈利 {pnl_pct:+.1f}%"
    elif pnl_pct >= -10:
        pnl_status = f"🟡 亏损 {pnl_pct:.1f}%"
    else:
        pnl_status = f"🔴 亏损 {pnl_pct:.1f}%"

    # 止损建议
    stop_loss_advice = ""
    if pnl_pct <= -15:
        stop_loss_advice = "🔴 触发止损线(-15%)，建议立即清仓"
    elif pnl_pct <= -10:
        stop_loss_advice = "⚠️ 接近止损线(-15%)，设置条件单"
    elif pnl_pct <= -5:
        stop_loss_advice = "🟡 浮亏扩大中，密切关注"

    # 止盈建议
    if pnl_pct >= 30:
        stop_loss_advice = "💰 盈利超30%，建议设置移动止盈(最高点回撤15%)"
    elif pnl_pct >= 20:
        stop_loss_advice = "📈 盈利超20%，可考虑部分止盈锁定利润"
    elif pnl_pct >= 10:
        stop_loss_advice = "✅ 盈利中，继续持有"

    position_advice.append({
        "ticker": ticker,
        "name": h["note"],
        "shares": shares,
        "cost": cost,
        "current": current_price,
        "pnl_pct": pnl_pct,
        "pnl_cny": pnl_cny,
        "status": pnl_status,
        "stop_loss": stop_loss_advice,
        "line": h["line"],
    })

# 8.2 线1建议（Capex）
line1_advice = ""
if is_earnings_season:
    line1_advice = "🔴 财报季进行中！每日追踪MSFT/GOOGL/META/AMZN Capex数据，等数据到手再做决策"
elif days_to_earnings <= 7:
    line1_advice = f"🟡 距Q2财报季仅{days_to_earnings}天！密切关注MRVL/DRAM/GOOGL持仓，季报前不做新操作"
else:
    line1_advice = f"🟢 距Q2财报季还有{days_to_earnings}天，Capex信号待季报发布后更新。当前仅监控股价波动"

# 检查MRVL是否触发减仓信号
mrvl_pct = capex_pct.get("MRVL", 0)
if mrvl_pct <= -5:
    line1_advice += "\n🔴 MRVL单日跌超5%，对照方法论：若连续3日跌幅>3%且无利好消息→减仓50%"

# 8.3 线2建议（ARR）
has_arr_news = any("无ARR" not in n.get("title", "") for n in arr_news)
if has_arr_news:
    line2_advice = "🟡 今日有ARR相关新闻，关注OpenAI/Anthropic收入增速是否放缓"
else:
    line2_advice = "🟢 今日无ARR重大更新。ARR增速为季度数据，下次关键节点9月底"

# 8.4 线3建议（替代赛道）
line3_advice = rotation_signal
if tech_pct > 0.5:
    line3_advice += "\n✅ AI/科技仍是主线，暂无替代赛道切换必要"
elif tech_pct < -1.0:
    line3_advice += "\n⚠️ 科技板块跑输，建议审视CRCL是否需要部分调仓"

# 8.5 综合操作清单
action_items = []

# CRCL超配检查
action_items.append("📋 CRCL占投资71.3%严重超配，建议减至50%以下（P1本月）")

# BitGo
action_items.append("📋 BitGo亏损69.6%，建议清仓认赔（P0立即）")

# MRVL止损
if mrvl_pct <= -3:
    action_items.append(f"⚠️ MRVL今日跌{mrvl_pct:.1f}%，设移动止盈：跌破$268(-10%)自动卖出")

# 还信用卡
action_items.append("📋 信用卡循环¥400,000需偿还，优先卖非核心仓(BitGo→优必选→TS→CRCL)")

# 财报季提醒
if days_to_earnings <= 7:
    action_items.append(f"🔔 {days_to_earnings}天后Q2财报季，提前准备Capex监控表格")

# ============================================================
# 九、生成日报
# ============================================================

print("\n生成日报...")
lines = []
lines.append("---")
lines.append(f"date: {today_str}")
lines.append("type: three-sell-lines-daily")
lines.append(f"earnings_season: {is_earnings_season}")
lines.append(f"version: v4")
lines.append("---")
lines.append("")
lines.append(f"# 三条卖出线 — 每日监控 ({today_str})")
lines.append("")
lines.append(f"> 自动生成 · {today.strftime('%H:%M')} · v4（含投资建议+新闻摘要）")
lines.append("")

# ── 线1 股价 ──
lines.append("## 线1：Capex 股价（代理指标）")
lines.append("")
lines.append("| 公司 | 股价 | 涨跌 | 关联持仓 |")
lines.append("|------|------|------|---------|")
holdings_label = {
    "MRVL": "29.192股 ¥59,098",
    "NVDA": "— (行业风向标)",
}
for name in ["MSFT", "GOOGL", "AMZN", "META", "MRVL", "NVDA"]:
    val = capex_data.get(name, "N/A")
    pct = capex_pct.get(name, 0)
    price_display = val.split(" (")[0] if val != "N/A" else "N/A"
    icon = "🔴" if pct <= -3 else ("🟡" if pct <= -1 else "")
    pct_display = f"{icon} {pct:+.2f}%" if val != "N/A" else "—"
    label = holdings_label.get(name, "—")
    lines.append(f"| {name} | {price_display} | {pct_display} | {label} |")
lines.append("")

# ── 线1 新闻 ──
lines.append("### 📰 Capex / 持仓股新闻")
lines.append("")
for n in capex_news:
    title = n["title"]
    title_zh = n.get("title_zh", "")
    desc = n.get("desc", "")
    source = n.get("source", "")
    ticker_tag = n.get("ticker", "")
    link = n.get("link", "")
    date_display = format_date(n.get("date", ""))
    date_part = f" | {date_display}" if date_display else ""
    source_part = f" · {source}" if source else ""
    ticker_part = f" [{ticker_tag}]" if ticker_tag else ""
    if link:
        lines.append(f"- [{title}]({link}){ticker_part}{source_part}{date_part}")
    else:
        lines.append(f"- {title}{ticker_part}{source_part}{date_part}")
    if title_zh and title_zh != title:
        lines.append(f"  > 📝 {title_zh}")
    if desc:
        lines.append(f"  > 📄 {desc}")
lines.append("")

# ── 暴跌专项 ──
if special_news:
    lines.append("### 🎯 暴跌股专项新闻")
    lines.append("")
    for n in special_news:
        title = n["title"]
        title_zh = n.get("title_zh", "")
        source = n.get("source", "")
        link = n.get("link", "")
        alert_for = n.get("alert_for", "")
        tag = f"**[{alert_for}]** " if alert_for else ""
        source_part = f" · {source}" if source else ""
        if link:
            lines.append(f"- {tag}[{title}]({link}){source_part}")
        else:
            lines.append(f"- {tag}{title}{source_part}")
        if title_zh and title_zh != title:
            lines.append(f"  > 📝 {title_zh}")
    lines.append("")

# ── 线2 ──
lines.append("## 线2：ARR 新闻（OpenAI / Anthropic）")
lines.append("")
for n in arr_news:
    title = n["title"]
    title_zh = n.get("title_zh", "")
    desc = n.get("desc", "")
    source = n.get("source", "")
    link = n.get("link", "")
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}")
    else:
        lines.append(f"- {title}{source_part}")
    if title_zh and title_zh != title:
        lines.append(f"  > 📝 {title_zh}")
    if desc:
        lines.append(f"  > 📄 {desc}")
lines.append("")

# ── 线3 ──
lines.append("## 线3：替代赛道 — 美股板块ETF")
lines.append("")
lines.append("| 板块 | 价格 | 涨跌 |")
lines.append("|------|------|------|")
for name in ["QQQ", "SPY", "XLK", "XLY", "XLF", "XLE"]:
    d = alt_data.get(name, {})
    price = f"${d['price']:.2f}" if d.get("price") else "N/A"
    pct = f"{d['pct']:+.2f}%" if d.get("price") else "—"
    lines.append(f"| {name} ({d.get('label', '')}) | {price} | {pct} |")
lines.append("")
lines.append(f"**板块轮动信号**: {rotation_signal}")
lines.append("")

lines.append("### 📰 替代赛道新闻")
lines.append("")
for n in alt_news:
    title = n["title"]
    title_zh = n.get("title_zh", "")
    desc = n.get("desc", "")
    source = n.get("source", "")
    link = n.get("link", "")
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}")
    else:
        lines.append(f"- {title}{source_part}")
    if title_zh and title_zh != title:
        lines.append(f"  > 📝 {title_zh}")
    if desc:
        lines.append(f"  > 📄 {desc}")
lines.append("")

# ── 告警 ──
lines.append("## ⚡ 今日告警")
lines.append("")
for a in alerts:
    lines.append(f"- {a['level']} {a['msg']}")
lines.append("")

# ── 投资建议 ──
lines.append("## 💡 投资建议")
lines.append("")

lines.append("### 持仓盈亏速览")
lines.append("")
lines.append("| 标的 | 成本 | 现价 | 盈亏% | 盈亏¥ | 建议 |")
lines.append("|------|------|------|-------|-------|------|")
for pa in position_advice:
    lines.append(f"| {pa['ticker']}({pa['name']}) | ${pa['cost']:.2f} | ${pa['current']:.2f} | {pa['pnl_pct']:+.1f}% | ¥{pa['pnl_cny']:+,.0f} | {pa['stop_loss']} |")
lines.append("")

lines.append(f"### 线1（Capex）: {line1_advice}")
lines.append("")
lines.append(f"### 线2（ARR）: {line2_advice}")
lines.append("")
lines.append(f"### 线3（替代赛道）: {line3_advice}")
lines.append("")

lines.append("### 📋 综合操作清单")
lines.append("")
for item in action_items:
    lines.append(f"- {item}")
lines.append("")

# ── 状态 ──
if days_to_earnings > 0:
    lines.append(f"> 📅 距Q2财报季（7月22日）还有 **{days_to_earnings}** 天，股价为早期预警，非卖出信号")
else:
    lines.append("> 🔴 已进入Q2财报季！请每日关注Capex新闻")
lines.append("")
lines.append("---")
lines.append("相关文档：[[ai-stock-three-sell-lines-methodology]]")
lines.append("> 数据源：新浪财经（股价+ETF）+ Yahoo Finance RSS（多ticker聚合+摘要）+ 本地术语翻译")

# 写入
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ 日报已生成: {out_file.name}")
print(f"   股价: {len(capex_data)}只 | Capex新闻: {len(capex_news)}条 | 暴跌专项: {len(special_news)}条")
print(f"   ARR新闻: {len(arr_news)}条 | 替代赛道: {len(alt_news)}条 | 板块ETF: {len(alt_data)}个")
print(f"   告警: {len(alerts)}条 | 持仓建议: {len(position_advice)}个")

if days_to_earnings in [7, 3, 1, 0]:
    print(f"\n{'='*50}")
    print(f"🔔 提醒：距Q2财报季还有 {days_to_earnings} 天！")
    print(f"   请关注 MSFT/GOOGL/META/AMZN Capex数据")
    print(f"{'='*50}")

if alert_tickers:
    print(f"\n{'='*50}")
    print(f"🚨 持仓股告警: {', '.join(alert_tickers)}")
    print(f"{'='*50}")


# ============================================================
# 十、飞书推送（interactive卡片）
# ============================================================

def build_lark_card():
    """构建飞书 interactive 卡片 JSON — 三线完整 + 中文翻译 + 投资建议"""
    elements = []

    # --- 线1 股价表 ---
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "**📊 线1：Capex 股价**"}
    })
    table_lines = ["| 公司 | 股价 | 涨跌 | 持仓 |", "|---|---|---|---|"]
    for name in ["MSFT", "GOOGL", "AMZN", "META", "MRVL", "NVDA"]:
        val = capex_data.get(name, "N/A")
        pct = capex_pct.get(name, 0)
        price_display = val.split(" (")[0] if val != "N/A" else "N/A"
        icon = "🔴" if pct <= -3 else ("🟡" if pct <= -1 else "")
        pct_str = f"{icon}{pct:+.2f}%" if val != "N/A" else "—"
        label_map = {"MRVL": "29.2股 ¥5.9万", "NVDA": "风向标"}
        table_lines.append(f"| {name} | {price_display} | {pct_str} | {label_map.get(name, '—')} |")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(table_lines)}
    })

    # --- 线1 新闻（前5条，中文翻译优先） ---
    elements.append({"tag": "hr"})
    news_lines = ["**📰 持仓股新闻**"]
    for n in capex_news[:5]:
        title_en = n["title"]
        title_zh = n.get("title_zh", "")
        # 飞书卡片优先展示中文翻译，如果翻译不完整则显示英文
        if title_zh and title_zh != title_en and len(title_zh) > 5:
            display_title = title_zh
        else:
            display_title = title_en
        source = n.get("source", "")
        news_lines.append(f"- {display_title} · {source}" if source else f"- {display_title}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(news_lines)}
    })

    # --- 线2 ARR ---
    elements.append({"tag": "hr"})
    arr_lines = ["**📈 线2：ARR（OpenAI/Anthropic）**"]
    for n in arr_news[:3]:
        title_en = n["title"]
        title_zh = n.get("title_zh", "")
        if title_zh and title_zh != title_en and len(title_zh) > 5:
            display_title = title_zh
        else:
            display_title = title_en
        arr_lines.append(f"- {display_title}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(arr_lines)}
    })

    # --- 线3 板块ETF ---
    elements.append({"tag": "hr"})
    etf_lines = ["**🔄 线3：美股板块ETF**"]
    etf_table = ["| 板块 | 涨跌 |", "|---|---|"]
    for name in ["QQQ", "SPY", "XLK", "XLY", "XLF", "XLE"]:
        d = alt_data.get(name, {})
        pct = d.get("pct", 0)
        icon = "🔴" if pct <= -1 else ("🟢" if pct >= 0 else "🟡")
        etf_table.append(f"| {name}({d.get('label', '')}) | {icon} {pct:+.2f}% |")
    etf_lines.append("\n".join(etf_table))
    etf_lines.append(rotation_signal)
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(etf_lines)}
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

    # --- 投资建议 ---
    elements.append({"tag": "hr"})
    advice_lines = ["**💡 投资建议**"]
    advice_lines.append(f"线1: {line1_advice}")
    advice_lines.append(f"线2: {line2_advice}")
    advice_lines.append(f"线3: {rotation_signal}")
    # 关键操作
    for pa in position_advice:
        if "清仓" in pa["stop_loss"] or "止损" in pa["stop_loss"]:
            advice_lines.append(f"⚠️ {pa['ticker']}: {pa['stop_loss']}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(advice_lines)}
    })

    # --- 页脚 ---
    elements.append({"tag": "hr"})
    footer = f"📅 距Q2财报季还有 {days_to_earnings} 天 | v4 | 新浪+Yahoo RSS聚合"
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": footer}]
    })

    # 卡片颜色
    has_red = any(a["level"] == "🚨" for a in alerts)
    has_yellow = any(a["level"] == "⚠️" for a in alerts)
    header_color = "red" if has_red else ("yellow" if has_yellow else "blue")
    header_title = f"🔴 三条卖出线 | {today_str}" if has_red else (f"🟡 三条卖出线 | {today_str}" if has_yellow else f"三条卖出线 | {today_str}")

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": header_title},
            "template": header_color,
        },
        "elements": elements,
    }


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
