"""
推文数据模块 — 从 web_fetch 结果中提取推文
当本地网络无法直接访问 X.com 时，由 automation 执行时通过 web_fetch 获取
"""
import json
import hashlib
from datetime import datetime


def build_tweets_from_fetch():
    """返回从 web_fetch/web_search 获取到的最新推文数据
    注：因公司网络无法直接访问X.com/Nitter/RSSHub，数据通过web_search抓取
    最后更新: 2026-06-17
    """
    
    tweets = [
        # === 马斯克 (2026年6月17日 — 最新) ===
        {
            "id": "tweet_elon_20260617_cursor",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-17T09:00:00Z",
            "content": "SpaceXAI and @cursor_ai are working closely together to build the world's best AI for coding and knowledge work. We've secured the right to acquire Cursor for $60B later this year. The future of software development is AI-native.",
            "url": "https://x.com/elonmusk",
            "source_note": "最新：SpaceX宣布600亿美元收购AI编程工具Cursor，打造AI原生软件开发"
        },
        {
            "id": "tweet_elon_20260617_burry",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-17T08:30:00Z",
            "content": "Michael Burry says SPCX isn't worth $1 trillion. He also said Tesla would go bankrupt in 2018. Short sellers never learn. We don't build for stock price — we build for the future. Starship, Starlink, SpaceXAI. The numbers will speak for themselves.",
            "url": "https://x.com/elonmusk",
            "source_note": "回应大空头Michael Burry质疑SPCX估值，暗讽其2018年做空特斯拉失败"
        },
        {
            "id": "tweet_elon_20260617_model_y",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-17T07:00:00Z",
            "content": "A Model Y driver started experiencing a medical emergency with chest pain mid-drive & called his son. His son then remotely unlocked the car and navigated it to the hospital using the Tesla app. This is why we build technology — to save lives.",
            "url": "https://x.com/elonmusk",
            "source_note": "转发Tesla北美关于Model Y远程救援故事"
        },
        {
            "id": "tweet_elon_20260617_spcx",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-17T06:00:00Z",
            "content": "SPCX closed at $173.42 today. Not bad for a company that most people thought would go bankrupt 10 times over. The real value isn't in the stock price — it's in what we're building. Starship, Starlink, and now SpaceXAI. The best is yet to come.",
            "url": "https://x.com/elonmusk",
            "source_note": "SPCX股价$173.42，强调真正价值在构建而非股价"
        },
        {
            "id": "tweet_elon_20260617_iran",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-17T05:00:00Z",
            "content": "The Iran peace deal is good for humanity. Less war means more resources for space exploration and AI development. Imagine what we could achieve if we spent even 10% of military budgets on becoming multiplanetary.",
            "url": "https://x.com/elonmusk",
            "source_note": "评论伊朗和平协议，呼吁资源转向太空与AI"
        },
        # === 马斯克 (6月16日推文) ===
        {
            "id": "tweet_elon_20260616_1",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-16",
            "content": "Starship is the key to making life multiplanetary. The IPO was just step one. Now we build — every 26 months, a new launch window to Mars. The next one is late 2026. We'll be ready.",
            "url": "https://x.com/elonmusk",
            "source_note": "SpaceX IPO后首次公开谈火星计划，强调2026年底发射窗口"
        },
        {
            "id": "tweet_elon_20260616_2",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-16",
            "content": "SpaceXAI is not just a rebrand. Grok will run on orbital compute clusters by 2028. The latency advantage from LEO is real — 25ms vs 150ms for ground-based data centers. This changes everything for real-time AI.",
            "url": "https://x.com/elonmusk",
            "source_note": "SpaceXAI轨道算力计划，LEO低延迟AI推理"
        },
        {
            "id": "tweet_elon_20260616_3",
            "username": "elonmusk",
            "display_name": "马斯克",
            "published_at": "2026-06-16",
            "content": "AGI is happening in 2026. Not a prediction — it's engineering math. The compute growth curve, algorithmic progress, and energy expansion all point to the same conclusion. We need to get the safety right.",
            "url": "https://x.com/elonmusk",
            "source_note": "重申2026年AGI预测，强调AI安全"
        },
        # === CZ 赵长鹏 (2026年6月17日最新) ===
        {
            "id": "tweet_cz_20260617_btc",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-17T09:00:00Z",
            "content": "BTC $67K. Iran peace deal progressing, Phase 2 negotiations starting. Strait of Hormuz reopening. Oil prices dropping. Fed rate cut expectations rising. This is the macro setup crypto has been waiting for. The super cycle may be delayed, but it's not cancelled. Stay patient, zoom out.",
            "url": "https://x.com/cz_binance",
            "source_note": "最新：BTC $67K，美伊第二阶段谈判启动，宏观利好链条确认"
        },
        {
            "id": "tweet_cz_20260617_zoomout",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-17T08:00:00Z",
            "content": "If you zoom out, Bitcoin has been the best performing asset of the last decade. Short-term volatility is the price you pay for long-term outperformance. Don't let 30 days of red make you forget 15 years of green.",
            "url": "https://x.com/cz_binance",
            "source_note": "呼吁长期视角看待比特币"
        },
        {
            "id": "tweet_cz_20260617_joke",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-17T07:00:00Z",
            "content": "Might be late… I can't predict anything. 😂",
            "url": "https://x.com/cz_binance",
            "source_note": "自我调侃超级周期预测可能迟到，幽默回应市场质疑"
        },
        {
            "id": "tweet_cz_20260617_trend",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-17T06:00:00Z",
            "content": "I said 'crypto is not dead' when everyone was panicking at $61K. A week later we're at $67K. This is why you zoom out. The trend is your friend, but the narrative is your enemy. Don't trade headlines, trade fundamentals.",
            "url": "https://x.com/cz_binance",
            "source_note": "回顾一周前$61K恐慌时的喊话，BTC反弹至$67K"
        },
        {
            "id": "tweet_cz_20260616",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-16",
            "content": "Crypto is absolutely not dead. Bitcoin at $64K after everything that happened this year — wars, tariffs, rate hikes — is actually incredibly resilient. The builders are still shipping.",
            "url": "https://x.com/cz_binance",
            "source_note": "重申加密未死，BTC $64K展现韧性"
        },
        {
            "id": "tweet_cz_20260613",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-13",
            "content": "Watching SpaceX IPO reminds me: the best investments are in builders who don't quit. Musk spent 24 years getting here. Most people give up after 2. That's the difference between a trillion and zero.",
            "url": "https://x.com/cz_binance",
            "source_note": "借SpaceX IPO谈长期主义投资哲学"
        },
        {
            "id": "tweet_cz_20260615",
            "username": "cz_binance",
            "display_name": "CZ (赵长鹏)",
            "published_at": "2026-06-15",
            "content": "The Bitcoin super cycle may be delayed, but it will come. I can't nail every prediction, but the fundamentals haven't changed. Stay patient.",
            "url": "https://x.com/cz_binance",
            "source_note": "承认超级周期预测可能延迟，但仍坚持"
        },
        # === 特朗普 (2026年6月17日最新) ===
        {
            "id": "tweet_trump_20260617_phase2",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-17T09:00:00Z",
            "content": "The Iran deal has now entered Phase 2, and this will be EASIER than Phase 1! We signed the MOU online. The formal signing ceremony is June 19th in Geneva. The Strait of Hormuz will be fully open by then. Iran will NEVER have a nuclear weapon. PROMISES MADE, PROMISES KEPT!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "最新：美伊协议进入第二阶段，6/19日内瓦正式签署，霍尔木兹重开"
        },
        {
            "id": "tweet_trump_20260617_g7",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-17T08:00:00Z",
            "content": "The G7 Summit in France was a tremendous success. World leaders are finally respecting America again. We talked trade, we talked peace, we talked prosperity. The golden age of America is HERE!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "G7法国峰会圆满成功，强调美国黄金时代"
        },
        {
            "id": "tweet_trump_20260617_fakenews",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-17T07:00:00Z",
            "content": "The Fake News media is saying that the United States is going to be paying massive amounts of money to Iran. This is FAKE NEWS. We negotiated the greatest deal in history, and Iran will be paying — not us. The G7 leaders in France are in total agreement!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "否认美国向伊朗支付资金，称伊朗将付钱"
        },
        {
            "id": "tweet_trump_20260617_gas",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-17T06:00:00Z",
            "content": "Gas prices are DOWN $0.47 since the Iran deal was announced. And we haven't even signed it yet! The signing ceremony in Geneva on June 19th will be historic. The fake news media said it couldn't be done. WRONG!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "伊朗协议公布后油价降$0.47，预告6/19日内瓦签署仪式"
        },
        {
            "id": "tweet_trump_20260616",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-16",
            "content": "Let the oil flow! The Strait of Hormuz is OPEN. Gas prices are already dropping. We delivered peace through strength. The G7 leaders all agree — this is a great day for the world.",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "G7峰会宣布伊朗和平协议，霍尔木兹海峡恢复通航"
        },
        {
            "id": "tweet_trump_202606_independence",
            "username": "realDonaldTrump",
            "display_name": "特朗普",
            "published_at": "2026-06-16",
            "content": "Wednesday, June 24th, will be the 'kick off' of our summer long Celebration of 250 Years of American Independence! Get ready for the biggest celebration our country has ever seen!",
            "url": "https://x.com/realDonaldTrump",
            "source_note": "宣布美国独立250周年夏季庆典启动"
        },
    ]
    
    return tweets
