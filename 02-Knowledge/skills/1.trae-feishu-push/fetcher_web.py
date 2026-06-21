"""
推文数据模块 — 多源推文获取

数据源优先级:
1. fetched_tweets.json — AI 通过浏览器从 X.com 抓取的最新推文（实时）
2. 硬编码数据 — 作为兜底（当 fetched_tweets.json 不存在或为空时）

AI 抓取流程（由自动化任务执行）:
  - 使用浏览器访问 X.com 用户主页
  - 提取推文内容、时间、URL
  - 写入 fetched_tweets.json（标准格式）
"""
import json
import os
from datetime import datetime


def _get_fetched_tweets_path():
    """获取 AI 抓取推文的 JSON 文件路径"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetched_tweets.json")


def load_fetched_tweets():
    """从 fetched_tweets.json 加载 AI 浏览器抓取的推文"""
    path = _get_fetched_tweets_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            print(f"[INFO] 从 fetched_tweets.json 加载 {len(data)} 条抓取推文")
            return data
    except (ValueError, IOError) as e:
        print(f"[WARN] 读取 fetched_tweets.json 失败: {e}")
    return []


def _get_hardcoded_tweets():
    """硬编码推文数据（兜底方案）"""
    tweets = [
        # === 马斯克 (2026年6月20日 — 最新) ===
        {
            "id": "tweet_elon_20260620_grok420",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-20T08:00:00Z",
            "content": "Grok 4.20 is now live. Multi-agent architecture that actually works — no more hallucinations pretending to be confidence. The era of AI that admits when it doesn't know is here. SpaceXAI is building AI that is honest first, smart second. Trust is the foundation.",
            "url": "https://x.com/elonmusk",
            "source_note": "6/20: SpaceXAI发布Grok 4.20，多代理协作架构，幻觉率创行业新低"
        },
        {
            "id": "tweet_elon_20260620_geneva",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-20T07:00:00Z",
            "content": "The Geneva accord was signed yesterday. Historic day for humanity. But I notice Iran has already reconstituted 75% of its missile arsenal with Russian weapons during the ceasefire. Peace on paper doesn't mean peace in reality. Stay vigilant.",
            "url": "https://x.com/elonmusk",
            "source_note": "6/20: 评论日内瓦协议签署，警告伊朗在停火期间用俄制武器重建3/4导弹武库"
        },
        {
            "id": "tweet_elon_20260620_fisa",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-20T06:00:00Z",
            "content": "FISA Section 702 has lapsed for the first time since 2008. The government can no longer warrantlessly spy on Americans' communications. This is a win for civil liberties. The surveillance state needs to be dismantled, piece by piece.",
            "url": "https://x.com/elonmusk",
            "source_note": "6/20: FISA 702监控授权首次失效，称是公民自由的胜利"
        },
        # === CZ 赵长鹏 (2026年6月20日最新) ===
        {
            "id": "tweet_cz_20260620_sellnews",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-20T09:00:00Z",
            "content": "Geneva accord signed. BTC at $62K. Classic 'buy the rumor, sell the news' move. The fundamentals haven't changed — Iran deal is still bullish for macro, Fed rate cut is still coming. This dip is a gift for those with dry powder. Don't waste it.",
            "url": "https://x.com/cz_binance",
            "source_note": "6/20: 日内瓦协议签署后BTC回落至62K，经典'买预期卖事实'，称回调是礼物"
        },
        {
            "id": "tweet_cz_20260620_patience",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-20T08:00:00Z",
            "content": "Everyone expected BTC to pump after the Iran deal signing. Instead it dropped. This is why I say 'zoom out' — short-term price action is noise. The 60-day nuclear negotiation window just started. The real catalyst hasn't even arrived yet. Patience.",
            "url": "https://x.com/cz_binance",
            "source_note": "6/20: 伊朗协议签署后BTC不涨反跌，60天核谈判才是真正催化剂"
        },
        # === 特朗普 (2026年6月20日最新) ===
        {
            "id": "tweet_trump_20260620_geneva_signed",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-20T09:00:00Z",
            "content": "Yesterday was one of the greatest days in American history! The Geneva Accord has been SIGNED. The Strait of Hormuz is OPEN. Gas prices are dropping. Iran will NEVER have a nuclear weapon — we have 60 days to finalize the details, but the framework is set. PROMISES MADE, PROMISES KEPT! The fake news media said it couldn't be done. They were WRONG, as always!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "6/20: 宣布日内瓦协议昨日签署成功，霍尔木兹开放，60天核谈判启动"
        },
        {
            "id": "tweet_trump_20260620_independence_week",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-20T07:00:00Z",
            "content": "Just 4 days until the kick-off of our 250 Years of American Independence Celebration on June 24th! We're going to have the biggest, most beautiful celebration this country has ever seen. The golden age of America is HERE — and it's going to last a very long time!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "6/20: 倒计时4天，6/24美国独立250周年庆典启动"
        },
        # === Serenity 白毛股神 (2026年6月20日) ===
        {
            "id": "tweet_serenity_20260620_wafer_update",
            "username": "aleabitoreddit",
            "display_name": "Serenity (白毛股神)",
            "published_at": "2026-06-20T08:00:00Z",
            "content": "Japan WF6 production shutdown is now 19 days away (July 1). I'm seeing panic buying from foundries. The spot price for WF6 has jumped 40% in two weeks. This is the bottleneck I warned about — and it's accelerating. The specialty gas suppliers with domestic WF6 capacity are about to have their moment. Watch closely.",
            "url": "https://x.com/aleabitoreddit",
            "source_note": "6/20: 日本WF6停产倒计时19天，现货价两周涨40%，特种气体商迎来时刻"
        },
        {
            "id": "tweet_serenity_20260620_cpo_update",
            "username": "aleabitoreddit",
            "display_name": "Serenity (白毛股神)",
            "published_at": "2026-06-20T07:00:00Z",
            "content": "Post-Geneva accord: oil dropping, inflation expectations easing, Fed rate cut probability rising. This is the macro setup CPO needs. Lower rates mean cheaper capital for data center expansion, which means more CPO deployment. The Geneva deal isn't just geopolitics — it's a supply chain catalyst for photonics.",
            "url": "https://x.com/aleabitoreddit",
            "source_note": "6/20: 日内瓦协议后油价降、降息预期升，CPO迎来宏观利好+数据中心扩张催化剂"
        },
    ]
    return tweets


def build_tweets_from_fetch():
    """返回最新推文数据
    
    优先级:
    1. GitHub Actions 抓取 (github_fetcher.py → 实时推文)
    2. fetched_tweets.json (AI 浏览器抓取的推文，已废弃)
    3. 硬编码数据 (兜底)
    
    返回推文列表，每条推文格式:
    {
        "id": "唯一标识",
        "username": "X用户名",
        "display_name": "显示名称",
        "published_at": "发布时间 (ISO格式)",
        "content": "推文原文",
        "url": "推文链接",
        "source_note": "来源备注 (可选)"
    }
    """
    # 1. 优先从 GitHub Actions 拉取
    try:
        from github_fetcher import pull_tweets_from_github
        github_tweets = pull_tweets_from_github()
        if github_tweets:
            print("[INFO] 使用 GitHub Actions 抓取的实时推文 ({}) 条".format(len(github_tweets)))
            return github_tweets
    except ImportError:
        print("[INFO] github_fetcher.py 不可用，跳过")
    except Exception as e:
        print("[INFO] GitHub 拉取失败: {}，尝试其他数据源".format(e))
    
    # 2. 读取本地 fetched_tweets.json
    fetched = load_fetched_tweets()
    if fetched:
        print("[INFO] 使用 fetched_tweets.json 中的推文 ({}) 条".format(len(fetched)))
        return fetched
    
    # 3. 回退到硬编码数据
    print("[INFO] 所有实时数据源不可用，使用硬编码兜底数据")
    return _get_hardcoded_tweets()
