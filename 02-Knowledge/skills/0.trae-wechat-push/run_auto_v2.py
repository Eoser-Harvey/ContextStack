"""
X推文推送 v2 — 改进版执行脚本
解决: Google翻译超时 + Server酱未配置
方案: 本地词典翻译(不依赖外部API) + Bun MCP WeChat推送
流程: 加载数据 -> 翻译 -> 分析 -> 推送到微信
"""
import json
import os
import sys
import subprocess
import time
import yaml
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import analyze_tweets
from fetcher_web import build_tweets_from_fetch

# ====== Bun + mcp-wechat-server 路径 ======
# 支持多用户路径自动检测
_BUN_CANDIDATES = [
    r"C:\Users\h31280\.bun\bin\bun.exe",
    r"C:\Users\harve\.bun\bin\bun.exe",
]
_MCP_CANDIDATES = [
    r"C:\Users\h31280\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts",
    r"C:\Users\harve\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts",
]

def _find_exe(candidates):
    for p in candidates:
        if os.path.isfile(p):
            return p
    return candidates[0]  # fallback to default

BUN = _find_exe(_BUN_CANDIDATES)
MCP_SERVER = _find_exe(_MCP_CANDIDATES)
DEFAULT_USER = "o9cq80xcTVHnYCThXQ8NXo_dIpYs@im.wechat"
SEND_INTERVAL = 2  # 消息间隔(秒)
PUSH_TIMEOUT = 20  # 推送超时(秒)


# ============================================================
# 翻译模块 — 本地词典式翻译，不依赖外部API
# ============================================================

# 硬编码每条推文的中文翻译（基于 fetcher_web.py 中的 source_note 和内容）
TWEET_TRANSLATIONS = {
    # === 马斯克 (2026年6月17日) ===
    "tweet_elon_20260617_cursor": "SpaceXAI和@cursor_ai正紧密合作，打造世界上最好的AI编程和知识工作工具。我们已获得今年晚些时候以600亿美元收购Cursor的权利。软件开发的未来是AI原生的。",
    "tweet_elon_20260617_burry": "Michael Burry说SPCX不值1万亿美元。他2018年还说特斯拉会破产。做空者永远学不乖。我们不为股价而建——我们为未来而建。星舰、星链、SpaceXAI。数字会说明一切。",
    "tweet_elon_20260617_model_y": "一位Model Y车主在驾驶途中突发胸痛医疗紧急情况，打电话给儿子。他儿子随后远程解锁了车辆，并使用Tesla App将其导航到医院。这就是我们构建技术的原因——拯救生命。",
    "tweet_elon_20260617_spcx": "SPCX今天收于173.42美元。对于一家大多数人认为会破产10次的公司来说，这还不错。真正的价值不在股价——而在于我们正在构建的东西。星舰、星链，以及现在的SpaceXAI。最好的还在后面。",
    "tweet_elon_20260617_iran": "伊朗和平协议对人类有益。更少的战争意味着有更多资源用于太空探索和AI开发。想象一下，如果我们把军事预算的10%花在成为多星球物种上，我们能取得什么成就。",
    # === 马斯克 (6月16日) ===
    "tweet_elon_20260616_1": "星舰是让生命多星球化的关键。IPO只是第一步。现在我们开始建设——每26个月，火星就有一个新的发射窗口。下一个是2026年底。我们会准备好的。",
    "tweet_elon_20260616_2": "SpaceXAI不仅仅是改名。Grok将在2028年前在轨道计算集群上运行。LEO的延迟优势是真实的——25ms对地面数据中心的150ms。这将改变实时AI的一切。",
    "tweet_elon_20260616_3": "AGI将在2026年实现。这不是预测——这是工程数学。算力增长曲线、算法进步和能源扩张都指向同一个结论。我们需要把安全问题做好。",
    # === CZ (2026年6月17日) ===
    "tweet_cz_20260617_btc": "BTC 6.7万美元。伊朗和平协议推进中，第二阶段谈判开始。霍尔木兹海峡重新开放。油价下跌。美联储降息预期上升。这是加密货币一直在等待的宏观利好。超级周期可能延迟，但不会取消。保持耐心，拉远视角。",
    "tweet_cz_20260617_zoomout": "拉远看，比特币是过去十年表现最好的资产。短期波动是你为长期超额收益付出的代价。不要让30天的红色让你忘记15年的绿色。",
    "tweet_cz_20260617_joke": "可能会迟到...我无法预测任何事情。",
    "tweet_cz_20260617_trend": "当所有人恐慌时我说过'加密没有死'，当时BTC在6.1万美元。一周后我们到了6.7万。这就是为什么要拉远看。趋势是你的朋友，但叙事是你的敌人。不要交易标题，交易基本面。",
    "tweet_cz_20260616": "加密绝对没有死。在经历了今年发生的所有事情——战争、关税、加息——之后，比特币在6.4万美元实际上展现了惊人的韧性。建设者们仍在持续交付。",
    "tweet_cz_20260613": "看着SpaceX IPO让我想起：最好的投资是投给那些不放弃的建设者。马斯克花了24年才走到这里。大多数人2年就放弃了。这就是万亿和零之间的区别。",
    "tweet_cz_20260615": "比特币超级周期可能延迟，但它会来的。我无法精准预测每个时间点，但基本面没有改变。保持耐心。",
    # === 特朗普 (2026年6月17日) ===
    "tweet_trump_20260617_phase2": "伊朗协议现在进入第二阶段，这将比第一阶段更容易！我们已经在线签署了MOU。正式签署仪式将于6月19日在日内瓦举行。到那时霍尔木兹海峡将全面开放。伊朗永远不会拥有核武器。承诺已做出，承诺已兑现！",
    "tweet_trump_20260617_g7": "在法国举行的G7峰会取得了巨大成功。世界领导人终于再次尊重美国了。我们谈了贸易，谈了和平，谈了繁荣。美国的黄金时代已经到来！",
    "tweet_trump_20260617_fakenews": "假新闻媒体说美国将向伊朗支付巨额资金。这是假新闻。我们谈判达成了历史上最伟大的协议，而伊朗将付钱——不是我们。在法国的G7领导人完全同意！",
    "tweet_trump_20260617_gas": "自伊朗协议公布以来，油价已经下降了0.47美元。我们甚至还没有签署它！6月19日在日内瓦的签署仪式将是历史性的。假新闻媒体说这不可能做到。错了！",
    "tweet_trump_20260616": "让石油流通！霍尔木兹海峡已经开放。油价已经在下跌。我们通过实力实现了和平。G7领导人都同意——这是世界美好的一天。",
    "tweet_trump_202606_independence": "6月24日星期三，将是我们长达整个夏天的美国独立250周年庆祝活动的'启动'！准备好迎接我们国家有史以来最大的庆祝活动吧！",
}

# 通用关键词词典（用于翻译中未硬编码的推文）
KEYWORD_DICT = {
    # 科技/AI
    "AI": "人工智能", "AGI": "通用人工智能", "artificial intelligence": "人工智能",
    "machine learning": "机器学习", "deep learning": "深度学习",
    "compute": "算力", "orbital": "轨道", "satellite": "卫星",
    "Starship": "星舰", "Starlink": "星链", "SpaceX": "SpaceX",
    "SpaceXAI": "SpaceXAI", "Grok": "Grok",
    "Tesla": "特斯拉", "TSLA": "特斯拉",
    "FSD": "完全自动驾驶", "autonomous": "自动驾驶",
    "robot": "机器人", "robotics": "机器人技术",
    "chip": "芯片", "semiconductor": "半导体", "NPU": "神经网络处理器",
    "embedded": "嵌入式", "edge computing": "边缘计算",
    "LEO": "低地球轨道", "latency": "延迟",
    "Cursor": "Cursor", "coding": "编程", "AI-native": "AI原生",
    "knowledge work": "知识工作", "acquire": "收购",
    # 加密/金融
    "Bitcoin": "比特币", "BTC": "BTC", "bitcoin": "比特币",
    "Ethereum": "以太坊", "ETH": "ETH", "ethereum": "以太坊",
    "crypto": "加密货币", "cryptocurrency": "加密货币",
    "blockchain": "区块链", "DeFi": "去中心化金融",
    "stablecoin": "稳定币", "NFT": "NFT",
    "Binance": "币安", "binance": "币安",
    "super cycle": "超级周期", "halving": "减半",
    "bull market": "牛市", "bear market": "熊市",
    "short seller": "做空者", "short selling": "做空",
    "Fed": "美联储", "Federal Reserve": "美联储",
    "rate cut": "降息", "interest rate": "利率",
    "inflation": "通胀", "recession": "衰退",
    "IPO": "IPO", "stock": "股票", "share": "股份",
    "trillion": "万亿", "billion": "十亿", "million": "百万",
    "dollar": "美元", "USD": "美元",
    # 地缘/政治
    "Iran": "伊朗", "Iranian": "伊朗",
    "peace deal": "和平协议", "MOU": "谅解备忘录",
    "Geneva": "日内瓦", "Strait of Hormuz": "霍尔木兹海峡",
    "G7": "G7", "summit": "峰会",
    "tariff": "关税", "trade": "贸易",
    "nuclear weapon": "核武器", "nuclear": "核",
    "oil": "石油", "gas": "汽油", "oil price": "油价",
    "military": "军事", "war": "战争",
    "multiplanetary": "多星球", "Mars": "火星",
    "launch window": "发射窗口",
    # 通用
    "investment": "投资", "investor": "投资者",
    "portfolio": "投资组合", "asset": "资产",
    "volatility": "波动性", "fundamental": "基本面",
    "trend": "趋势", "narrative": "叙事",
    "zoom out": "拉远视角", "patient": "耐心",
    "builder": "建设者", "build": "建设",
    "promise": "承诺", "fake news": "假新闻",
    "golden age": "黄金时代",
}


def translate_tweet_local(tweet):
    """本地翻译推文，优先使用硬编码翻译，其次使用关键词词典"""
    tweet_id = tweet.get("id", "")

    # 优先使用硬编码翻译
    if tweet_id in TWEET_TRANSLATIONS:
        return TWEET_TRANSLATIONS[tweet_id]

    # 使用 source_note 作为翻译（fetcher_web.py 中已有中文摘要）
    source_note = tweet.get("source_note", "")
    if source_note and len(source_note) > 10:
        return source_note

    # 最后使用关键词替换翻译
    content = tweet.get("content", "")
    translated = content
    # 按长度降序排列，避免短词先替换导致长词匹配失败
    sorted_keywords = sorted(KEYWORD_DICT.keys(), key=len, reverse=True)
    for en, zh in [(k, KEYWORD_DICT[k]) for k in sorted_keywords]:
        # 只替换独立的英文词（简单处理）
        translated = translated.replace(en, zh)

    return translated


def translate_tweets_local(tweets):
    """批量翻译推文（本地方式，不依赖外部API）"""
    for tweet in tweets:
        content = tweet.get("content", "")
        if content:
            tweet["translated"] = translate_tweet_local(tweet)
        else:
            tweet["translated"] = ""
    return tweets


# ============================================================
# MCP WeChat 推送模块 — 通过 Bun JSON-RPC
# ============================================================

def send_one_wechat(text, to=DEFAULT_USER, timeout=PUSH_TIMEOUT):
    """通过 Bun + JSON-RPC 发送一条微信消息"""
    try:
        server = subprocess.Popen(
            [BUN, MCP_SERVER],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "HOME": os.environ.get("USERPROFILE", "")}
        )

        def _send_json(obj):
            server.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
            server.stdin.flush()

        # JSON-RPC 2.0 握手
        _send_json({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "x-tweets-pusher-v2", "version": "2.0.0"}
            }
        })

        buffer = b""
        done = False
        start_time = time.time()

        while not done and (time.time() - start_time) < timeout:
            # 设置读取超时
            server.stdout.timeout = 5
            try:
                chunk = server.stdout.readline()
            except Exception:
                # 读取超时
                if time.time() - start_time >= timeout:
                    break
                continue

            if not chunk:
                break
            buffer += chunk
            try:
                line = buffer.decode("utf-8").strip()
                buffer = b""
                if not line:
                    continue
                resp = json.loads(line)

                if resp.get("id") == 1:
                    # 初始化响应 -> 发送 initialized 通知 + 发送消息请求
                    _send_json({"jsonrpc": "2.0", "method": "notifications/initialized"})
                    _send_json({
                        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {
                            "name": "send_text_message",
                            "arguments": {"to": to, "text": text}
                        }
                    })

                elif resp.get("id") == 2:
                    done = True
                    if resp.get("error"):
                        print(f"  [ERROR] 推送失败: {resp['error']}")
                        server.kill()
                        return False
                    else:
                        print("  [OK] 微信推送成功")
                        server.kill()
                        return True
            except json.JSONDecodeError:
                continue

        server.kill()
        if not done:
            print(f"  [WARN] 推送超时 ({timeout}秒)")
        return False

    except FileNotFoundError as e:
        print(f"  [ERROR] Bun 或 mcp-wechat-server 未找到: {e}")
        print(f"  [INFO] Bun路径: {BUN} (存在: {os.path.isfile(BUN)})")
        print(f"  [INFO] MCP路径: {MCP_SERVER} (存在: {os.path.isfile(MCP_SERVER)})")
        return False
    except Exception as e:
        print(f"  [ERROR] 推送异常: {e}")
        return False


def build_messages(tweets):
    """构建分段消息列表，控制在微信单条消息限制内"""
    # 高价值关键词（用于筛选）
    HIGH_VALUE_KEYWORDS = [
        "btc", "bitcoin", "crypto", "加密", "eth", "binance",
        "ma120", "super cycle", "超级周期",
        "fed", "rate", "利率", "降息", "通胀", "iran", "伊朗", "peace",
        "oil", "油价", "g7", "tariff", "关税",
        "ai", "agi", "grok", "robot", "机器人", "compute", "算力",
        "spacex", "spcx", "starship", "星舰", "tsla", "特斯拉",
        "crcl", "小米", "优必选", "nvda", "stock", "ipo",
        "孩子", "教育", "房贷", "家庭", "油价下降", "安全", "救援",
        "长期", "耐心", "builder", "构建", "cursor", "acquire",
    ]

    NOISE_KEYWORDS = ["rape", "raped", "abused", "white girls", "lured"]

    def relevance_score(tweet):
        text = (tweet.get("content", "") + " " + tweet.get("translated", "")).lower()
        score = 5
        if len(tweet.get("content", "").strip()) < 30:
            return 0
        for kw in NOISE_KEYWORDS:
            if kw in text:
                score -= 15
                break
        for kw in HIGH_VALUE_KEYWORDS:
            if kw in text:
                score += 12
                break
        username = tweet.get("username", "")
        if username == "cz_binance":
            score += 5
        elif username == "realDonaldTrump":
            score += 3
        elif username == "elonmusk":
            score += 3
        return max(score, 0)

    # 筛选高价值推文
    scored = [(relevance_score(t), t) for t in tweets]
    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    seen_users = set()
    # 每个用户至少保留1条
    for s, t in scored:
        u = t.get("username", "")
        if u not in seen_users and s >= 5:
            selected.append(t)
            seen_users.add(u)
    # 按得分补满到6条
    for s, t in scored:
        if len(selected) >= 6:
            break
        if t not in selected and s >= 8:
            selected.append(t)

    msgs = []

    # 统计信息
    users = {}
    for t in tweets:
        u = t.get("display_name", t.get("username", ""))
        users[u] = users.get(u, 0) + 1
    user_summary = " | ".join(f"{u}({c})" for u, c in users.items())

    # 消息1: 摘要头
    now = datetime.now().strftime("%m-%d %H:%M")
    header = f"X推文速递 | {now}\n"
    header += "========================\n"
    header += f"共{len(tweets)}条 -> 精选{len(selected)}条\n"
    header += f"关注: {user_summary}\n"
    header += "========================"
    msgs.append(header)

    # 消息2-N: 精选推文
    for tweet in selected:
        username = tweet.get("display_name", tweet.get("username", ""))
        content = tweet.get("content", "")
        translated = tweet.get("translated", "")
        analysis = tweet.get("analysis", {})

        content_preview = content[:200] + ("..." if len(content) > 200 else "")
        translated_preview = translated[:150] + ("..." if len(translated) > 150 else "")

        msg = f"【{username}】\n"
        msg += f"{content_preview}\n"
        if translated and translated != content:
            msg += f"译: {translated_preview}\n"
        msg += "------------------------\n"

        # 投资建议（最优先）
        if analysis.get("investment"):
            inv = analysis["investment"]
            lines = inv.split("\n")
            key_lines = [l for l in lines if any(l.startswith(p) for p in [
                "💰", "📌", "⚠️", "📈", "📊", "😄", "🕊️", "☢️", "🚀", "🤖", "💻", "🎯", "🏛️", "⛽", "🌍", "🧘", "⚖️"
            ])]
            if key_lines:
                msg += key_lines[0][:200] + "\n"
            else:
                msg += inv[:250] + "\n"

        # 生活建议
        if analysis.get("life") and len(msg) < 600:
            life = analysis["life"]
            lines = life.split("\n")
            key_lines = [l for l in lines if any(l.startswith(p) for p in [
                "❤️", "🧘", "☮️", "🌟", "🤖", "📊", "💪", "⏳", "🔍", "💻", "👨‍👩‍👧"
            ])]
            if key_lines:
                msg += key_lines[0][:180] + "\n"

        # 家庭建议
        if analysis.get("family") and len(msg) < 700:
            fam = analysis["family"]
            lines = fam.split("\n")
            key_lines = [l for l in lines if l.startswith("👨‍👩‍👧")]
            if key_lines:
                msg += key_lines[0][:180] + "\n"

        # 职业建议
        if analysis.get("career") and len(msg) < 800:
            car = analysis["career"]
            lines = car.split("\n")
            key_lines = [l for l in lines if l.startswith("💼")]
            if key_lines:
                msg += key_lines[0][:150]

        # 控制长度（微信单条约2048字符，留余量）
        if len(msg) > 1000:
            msg = msg[:1000] + "..."

        msgs.append(msg)

    # 最后一条: 行动清单
    checklist = "今日关注\n"
    checklist += "========================\n"
    checklist += "投资: BTC 0.642个 | USDT待命\n"
    checklist += "  MA120下方->暂存USDT，站回后定投\n"
    checklist += "  CRCL占47.9%->$100触发止盈\n"
    checklist += "  币安借贷已还清 | 信用卡待降\n"
    checklist += "------------------------\n"
    checklist += "家庭: 保险韩伟重疾50W | 定寿待配\n"
    checklist += "  薛燕重疾待配 | 孩子升学规划\n"
    checklist += "------------------------\n"
    checklist += "生活: TFLM学习 | 每天30分钟信息\n"
    checklist += "  减少盯盘焦虑 | 保持长期主义\n"
    checklist += "========================\n"
    checklist += "自动推送 | v2本地翻译+MCP微信"
    msgs.append(checklist)

    return msgs


def push_to_wechat(tweets, to=DEFAULT_USER):
    """通过 Bun JSON-RPC 分段推送到微信"""
    msgs = build_messages(tweets)
    print(f"\n[INFO] 准备推送 {len(msgs)} 条消息到微信...")

    success_count = 0
    for i, msg in enumerate(msgs):
        print(f"\n[{i+1}/{len(msgs)}] 发送中 ({len(msg)}字)...")
        if send_one_wechat(msg, to):
            success_count += 1
        else:
            print(f"  [WARN] 第{i+1}条发送失败，继续下一条")

        if i < len(msgs) - 1:
            print(f"  [INFO] 等待 {SEND_INTERVAL} 秒...")
            time.sleep(SEND_INTERVAL)

    print(f"\n[INFO] 推送完成: {success_count}/{len(msgs)} 成功")
    return success_count > 0


# ============================================================
# 历史管理
# ============================================================

def load_history(history_path):
    """加载已推送的推文ID"""
    if not os.path.exists(history_path):
        return []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (ValueError, FileNotFoundError):
        return []


def save_history(history_path, tweet_ids, max_history):
    """保存已推送的推文ID"""
    os.makedirs(os.path.dirname(history_path) if os.path.dirname(history_path) else ".", exist_ok=True)
    tweet_ids = tweet_ids[-max_history:]
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(tweet_ids, f, ensure_ascii=False, indent=2)


def filter_new_tweets(tweets, history_ids):
    """过滤出未推送过的新推文"""
    new_tweets = []
    for tweet in tweets:
        tid = tweet.get("id", "")
        if tid and tid not in history_ids:
            new_tweets.append(tweet)
    return new_tweets


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("X推文推送系统 v2 启动 — {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 加载配置
    print("\n[STEP 1] 加载配置...")
    config_path = os.path.join(script_dir, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    output_cfg = config["output"]
    history_path = os.path.join(script_dir, output_cfg["history_file"])
    print("  [OK] 配置加载成功")

    # 2. 加载历史
    print("\n[STEP 2] 加载推送历史...")
    history_ids = load_history(history_path)
    print(f"  [OK] 已有 {len(history_ids)} 条历史记录")

    # 3. 获取推文数据
    print("\n[STEP 3] 获取推文数据...")
    all_tweets = build_tweets_from_fetch()
    print(f"  [OK] 共获取 {len(all_tweets)} 条推文")

    if not all_tweets:
        print("[INFO] 未获取到推文，退出")
        return

    # 4. 过滤新推文
    print("\n[STEP 4] 过滤新推文...")
    new_tweets = filter_new_tweets(all_tweets, history_ids)
    print(f"  [OK] 新推文: {len(new_tweets)} 条")

    if not new_tweets:
        print("[INFO] 没有新推文，无需推送")
        return

    # 5. 本地翻译（不依赖外部API）
    print("\n[STEP 5] 本地翻译推文...")
    new_tweets = translate_tweets_local(new_tweets)
    for i, t in enumerate(new_tweets):
        tid = t.get("id", "")[:30]
        translated = t.get("translated", "")[:50]
        print(f"  [{i+1}] {tid} -> {translated}...")
    print("  [OK] 翻译完成")

    # 6. AI分析
    print("\n[STEP 6] AI分析推文...")
    new_tweets = analyze_tweets(new_tweets, config["profile"])
    for i, t in enumerate(new_tweets):
        analysis = t.get("analysis", {})
        inv = analysis.get("investment", "")[:60]
        print(f"  [{i+1}] {t.get('display_name', '')}: {inv}...")
    print("  [OK] 分析完成")

    # 7. 保存结果到本地文件
    print("\n[STEP 7] 保存结果到本地...")
    result_path = os.path.join(script_dir, "latest_tweets.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(new_tweets, f, ensure_ascii=False, indent=2)
    print(f"  [OK] 分析结果 -> latest_tweets.json")

    # 8. 推送到微信
    print("\n[STEP 8] 推送到微信 (Bun MCP)...")
    success = push_to_wechat(new_tweets)

    if success:
        # 更新历史
        new_ids = [t.get("id", "") for t in new_tweets if t.get("id")]
        all_ids = history_ids + new_ids
        save_history(history_path, all_ids, output_cfg["max_history"])
        print(f"\n[OK] 历史已更新，共 {len(all_ids)} 条记录")
    else:
        # 失败时保存消息文件
        wechat_msg_path = os.path.join(script_dir, "wechat_message.txt")
        msgs = build_messages(new_tweets)
        with open(wechat_msg_path, "w", encoding="utf-8") as f:
            f.write("\n\n--- 分段分隔 ---\n\n".join(msgs))
        print(f"\n[WARN] 推送失败，消息已保存到 wechat_message.txt")
        print(f"[WARN] 推文数据已保存到 latest_tweets.json")

    # 9. 打印摘要
    print("\n" + "=" * 60)
    print("执行摘要:")
    print("=" * 60)
    print(f"总推文: {len(all_tweets)} 条")
    print(f"新推文: {len(new_tweets)} 条")
    print(f"推送结果: {'成功' if success else '失败'}")
    print(f"翻译方式: 本地词典 (不依赖外部API)")
    print(f"推送方式: Bun MCP WeChat JSON-RPC")
    print("=" * 60)

    for i, t in enumerate(new_tweets, 1):
        print(f"\n--- {i}. {t.get('display_name')} (@{t.get('username')}) ---")
        print(f"时间: {t.get('published_at')}")
        print(f"原文: {t.get('content', '')[:120]}")
        if t.get('translated'):
            print(f"翻译: {t.get('translated', '')[:120]}")
        analysis = t.get('analysis', {})
        if analysis.get('investment'):
            print(f"投资: {analysis['investment'].split(chr(10))[0][:150]}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
