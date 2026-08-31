"""
推文数据模块 — 多源推文获取

数据源优先级:
1. GitHub Actions 拉取 (github_fetcher.py → Eoser-Harvey/twitter-feed-fetcher)
2. FxTwitter API v2 (直接实时拉取，Cloudflare Worker，免认证)
3. fetched_tweets.json (AI 浏览器抓取，已废弃)
4. 硬编码数据 (兜底)
"""
import json
import os
import time
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


def load_fxtwitter_tweets():
    """从 FxTwitter API v2 直接拉取实时推文 (Cloudflare Worker, 免认证, GFW友好)
    API: GET /2/profile/{handle}/statuses
    Rate limit: 1000 req/min per IP
    """
    import requests as req_lib

    USERS = [
        {"username": "elonmusk", "display_name": "马斯克"},
        {"username": "cz_binance", "display_name": "CZ (赵长鹏)"},
        {"username": "realDonaldTrump", "display_name": "特朗普"},
        {"username": "aleaborteddit", "display_name": "Serenity (白毛股神)"},
        {"username": "qinbafrank", "display_name": "秦巴Frank"},
        {"username": "xiaomustock", "display_name": "小米股"},
        {"username": "xingpt", "display_name": "星Prompt"},
        {"username": "hibtc37", "display_name": "HiBTC"},
        {"username": "supezen", "display_name": "Supezen"},
    ]
    TWEETS_PER_USER = 3
    all_tweets = []
    success_count = 0
    fail_count = 0

    print("[INFO] FxTwitter API v2: 直接拉取实时推文...")
    for user in USERS:
        try:
            url = "https://api.fxtwitter.com/2/profile/{}/statuses".format(user["username"])
            resp = req_lib.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200 and "results" in data:
                    count = 0
                    for item in data["results"]:
                        if count >= TWEETS_PER_USER:
                            break
                        if item.get("type") == "status":
                            tweet_id = item.get("id", "")
                            if not tweet_id:
                                continue
                            content = item.get("text", "") or item.get("raw_text", {}).get("text", "")
                            if not content:
                                continue
                            all_tweets.append({
                                "id": "tweet_{}_{}".format(user["username"], tweet_id),
                                "username": user["username"],
                                "display_name": user["display_name"],
                                "published_at": item.get("created_at", item.get("timestamp", "")),
                                "content": content,
                                "url": item.get("url", "https://x.com/{}/status/{}".format(user["username"], tweet_id)),
                                "translated": "",
                                "source_note": "FxTwitter API v2: {}".format(datetime.now().isoformat()),
                            })
                            count += 1
                    if count > 0:
                        success_count += 1
                        print("  [OK] @{}: {} tweets".format(user["username"], count))
                    else:
                        fail_count += 1
                        print("  [WARN] @{}: 0 tweets parsed".format(user["username"]))
                else:
                    fail_count += 1
                    print("  [WARN] @{}: API error code={}".format(user["username"], data.get("code")))
            elif resp.status_code == 429:
                fail_count += 1
                print("  [RATE] @{}: Rate limited (429)".format(user["username"]))
                break
            else:
                fail_count += 1
                print("  [WARN] @{}: HTTP {}".format(user["username"], resp.status_code))
        except Exception as e:
            fail_count += 1
            print("  [ERROR] @{}: {}".format(user["username"], str(e)[:60]))
        time.sleep(1)  # 间隔1秒避免触发限流

    print("[INFO] FxTwitter: {}/{} users, {} tweets total".format(success_count, success_count + fail_count, len(all_tweets)))
    return all_tweets


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
    1. GitHub Actions 抓取 (github_fetcher.py → Eoser-Harvey/twitter-feed-fetcher)
    2. FxTwitter API v2 (直接实时拉取，Cloudflare Worker，免认证)
    3. fetched_tweets.json (AI 浏览器抓取，已废弃)
    4. 硬编码数据 (兜底)
    
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
    # 1. 优先从 GitHub Actions 拉取 (仅用24小时内的新鲜数据)
    try:
        from github_fetcher import pull_tweets_from_github
        github_tweets = pull_tweets_from_github()
        if github_tweets:
            # 检查数据时效性: 最新推文是否在24小时内
            latest_time = max((t.get("published_at", "") for t in github_tweets), default="")
            if latest_time:
                try:
                    from datetime import timezone
                    # 尝试解析时间
                    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S", "%a %b %d %H:%M:%S %z %Y"):
                        try:
                            from datetime import datetime as dt2
                            parsed = dt2.strptime(latest_time.replace("GMT", "UTC").replace("+0000", "").strip(), fmt)
                            if (datetime.now(timezone.utc) - parsed.replace(tzinfo=timezone.utc)).total_seconds() < 86400:
                                print("[INFO] 使用 GitHub Actions 新鲜推文 ({}) 条".format(len(github_tweets)))
                                return github_tweets
                            else:
                                print("[INFO] GitHub 数据已过期 (最新: {}), 尝试 FxTwitter".format(latest_time[:19]))
                                break
                        except ValueError:
                            continue
                except Exception as e2:
                    print("[INFO] 时效性检查失败: {}, 使用 FxTwitter".format(e2))
            else:
                print("[INFO] GitHub 数据无时间戳, 使用 FxTwitter")
    except ImportError:
        print("[INFO] github_fetcher.py 不可用，跳过")
    except Exception as e:
        print("[INFO] GitHub 拉取失败: {}，尝试其他数据源".format(e))
    
    # 2. FxTwitter API v2 直接拉取 (Cloudflare Worker, 免认证, 实时)
    try:
        fxtwitter_tweets = load_fxtwitter_tweets()
        if fxtwitter_tweets:
            print("[INFO] 使用 FxTwitter API v2 实时推文 ({}) 条".format(len(fxtwitter_tweets)))
            return fxtwitter_tweets
    except Exception as e:
        print("[INFO] FxTwitter 拉取失败: {}，尝试其他数据源".format(e))
    
    # 3. 读取本地 fetched_tweets.json
    fetched = load_fetched_tweets()
    if fetched:
        print("[INFO] 使用 fetched_tweets.json 中的推文 ({}) 条".format(len(fetched)))
        return fetched
    
    # 4. 回退到硬编码数据
    print("[INFO] 所有实时数据源不可用，使用硬编码兜底数据")
    return _get_hardcoded_tweets()
