"""
构建微信推送消息 + 通过 Bun JSON-RPC 直接推送
调用链: Python → subprocess(Bun) → mcp-wechat-server → JSON-RPC 2.0 → 微信

原理: 每次推送启动独立 Bun 进程运行 mcp-wechat-server，
通过 stdin/stdout JSON-RPC 2.0 协议通信，发送完成后进程退出。
不依赖 IDE session，不依赖外部 wechat_sender.js。
"""
import json
import os
import subprocess
import time
from datetime import datetime

# ====== Bun + mcp-wechat-server 路径 ======
BUN = r"C:\Users\h31280\.bun\bin\bun.exe"
MCP_SERVER = r"C:\Users\h31280\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts"
DEFAULT_USER = "o9cq80xcTVHnYCThXQ8NXo_dIpYs@im.wechat"
SEND_INTERVAL = 2  # 消息间隔(秒)，防止微信限流

# ====== 高价值关键词 ======
HIGH_VALUE_KEYWORDS = {
    "crypto": ["btc", "bitcoin", "crypto", "加密", "eth", "ethereum", "区块链", "binance",
               "ma120", "super cycle", "超级周期", "halving", "减半", "defi", "stablecoin"],
    "macro": ["fed", "rate", "利率", "降息", "通胀", "inflation", "iran", "伊朗", "peace",
              "oil", "油价", "g7", "tariff", "关税", "trade", "recession", "gdp"],
    "ai_tech": ["ai", "agi", "grok", "robot", "机器人", "compute", "算力", "spacex",
                "spcx", "starship", "星舰", "fsd", "自动驾驶", "芯片", "chip", "npu",
                "tflm", "嵌入式", "embedded", "iot", "边缘"],
    "stocks": ["tsla", "特斯拉", "crcl", "circle", "mrcl", "marvell", "nok", "诺基亚",
               "小米", "优必选", "nvda", "nvidia", "stock", "market", "股市", "ipo"],
    "china": ["china", "中国", "beijing", "北京", "h3c", "新华三", "a股", "港股"],
    # 投资/家庭/生活相关 — 提升关联度
    "life_family": ["孩子", "教育", "升学", "房贷", "月供", "保险", "家庭", "父母", "配偶",
                    "健康", "安全", "安心", "生活成本", "物价", "油价", "油价下降",
                    "省钱", "消费", "心态", "焦虑", "压力", "坚持", "耐心",
                    "好奇", "未来", "长期", "balance", "平衡", "休息", "睡眠",
                    "人命", "救援", "拯救", "医疗", "医院", "model y", "远程",
                    "人文", "意义", "初心", "兴奋", "热爱", "learn", "学习",
                    "builder", "构建", "create", "创造", "inspire", "激励"],
}

# 噪音关键词（降权但不完全跳过）
NOISE_KEYWORDS = [
    "rape", "raped", "abused", "white girls", "lured",  # 英国丑闻
    "censor", "审查", "protect the children",  # 审查类
]

def load_tweets():
    path = os.path.join(os.path.dirname(__file__), "latest_tweets.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def tweet_relevance_score(tweet):
    """计算推文与用户画像的相关性得分（0-100）"""
    text = (tweet.get("content", "") + " " + tweet.get("translated", "")).lower()
    username = tweet.get("username", "")
    score = 5  # 基础分（所有推文都有最低价值）
    
    # 纯链接/无内容 → 0分
    if len(tweet.get("content", "").strip()) < 30:
        return 0
    
    # 噪音关键词 → 降权
    for kw in NOISE_KEYWORDS:
        if kw in text:
            score -= 15
            break
    
    # 加密相关
    for kw in HIGH_VALUE_KEYWORDS["crypto"]:
        if kw in text:
            score += 15
            break
    
    # 宏观
    for kw in HIGH_VALUE_KEYWORDS["macro"]:
        if kw in text:
            score += 15
            break
    
    # AI/科技
    for kw in HIGH_VALUE_KEYWORDS["ai_tech"]:
        if kw in text:
            score += 15
            break
    
    # 个股
    for kw in HIGH_VALUE_KEYWORDS["stocks"]:
        if kw in text:
            score += 10
            break
    
    # 中国相关
    for kw in HIGH_VALUE_KEYWORDS["china"]:
        if kw in text:
            score += 10
            break
    
    # 投资/家庭/生活相关 — 与用户画像直接关联
    for kw in HIGH_VALUE_KEYWORDS["life_family"]:
        if kw in text:
            score += 12
            break
    
    # CZ的推文对加密投资者天然高价值
    if username == "cz_binance":
        score += 8
    
    # 特朗普宏观政策推文天然高价值
    if username == "realDonaldTrump":
        score += 3
    
    # 马斯克科技/AI推文
    if username == "elonmusk":
        score += 3
    
    return max(score, 0)

def select_top_tweets(tweets, max_count=6):
    """筛选最高价值的推文，最多max_count条，每用户至少保留1条（如果有的话）"""
    scored = [(tweet_relevance_score(t), t) for t in tweets]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # 确保每个用户至少有1条（如果他们有推文）
    selected = []
    seen_users = set()
    
    # 第一轮：取每个用户得分最高的一条
    for s, t in scored:
        u = t.get("username", "")
        if u not in seen_users and s >= 5:
            selected.append(t)
            seen_users.add(u)
    
    # 第二轮：按得分补满
    for s, t in scored:
        if len(selected) >= max_count:
            break
        if t not in selected and s >= 8:
            selected.append(t)
    
    return selected

def build_messages(tweets):
    """构建分段消息列表，智能筛选，控制在3-5条"""
    # 筛选高价值推文
    top = select_top_tweets(tweets, max_count=5)
    
    msgs = []
    
    # 统计
    users = {}
    for t in tweets:
        u = t.get("display_name", t.get("username", ""))
        users[u] = users.get(u, 0) + 1
    
    user_summary = " | ".join(f"{u}({c})" for u, c in users.items())
    
    # 消息1: 摘要头
    now = datetime.now().strftime("%m-%d %H:%M")
    header = f"📡 X推文速递 | {now}\n"
    header += "━━━━━━━━━━━━━━━━\n"
    header += f"共{len(tweets)}条 → 精选{len(top)}条\n"
    header += f"关注: {user_summary}\n"
    header += "━━━━━━━━━━━━━━━━"
    msgs.append(header)
    
    # 消息2-N: 精选推文（每条一个消息，精简格式，四维度全覆盖）
    for tweet in top:
        username = tweet.get("display_name", tweet.get("username", ""))
        content = tweet.get("content", "")
        translated = tweet.get("translated", "")
        analysis = tweet.get("analysis", {})
        
        # 精简内容（截断过长推文）
        content_preview = content[:180] + ("..." if len(content) > 180 else "")
        translated_preview = translated[:120] + ("..." if len(translated) > 120 else "")
        
        msg = f"【{username}】\n"
        msg += f"{content_preview}\n"
        if translated and translated != content:
            msg += f"译: {translated_preview}\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        
        # 投资建议（最优先）
        if analysis.get("investment"):
            inv = analysis["investment"]
            lines = inv.split("\n")
            key_lines = [l for l in lines if any(l.startswith(p) for p in ["💰", "📌", "⚠️", "📈", "📊", "😄", "🕊️", "☢️"])]
            if key_lines:
                msg += key_lines[0][:180] + "\n"
            else:
                msg += inv[:220] + "\n"
        
        # 生活建议
        if analysis.get("life") and len(msg) < 500:
            life = analysis["life"]
            lines = life.split("\n")
            key_lines = [l for l in lines if any(l.startswith(p) for p in ["❤️", "🧘", "☮️", "🌟", "🤖", "📊", "💪", "⏳", "🔍"])]
            if key_lines:
                msg += key_lines[0][:150] + "\n"
        
        # 家庭建议
        if analysis.get("family") and len(msg) < 550:
            fam = analysis["family"]
            lines = fam.split("\n")
            key_lines = [l for l in lines if l.startswith("👨‍👩‍👧")]
            if key_lines:
                msg += key_lines[0][:150] + "\n"
        
        # 职业建议（最后，最低优先级）
        if analysis.get("career") and len(msg) < 600:
            car = analysis["career"]
            lines = car.split("\n")
            key_lines = [l for l in lines if l.startswith("💼")]
            if key_lines:
                msg += key_lines[0][:120]
        
        # 控制长度
        if len(msg) > 750:
            msg = msg[:750] + "..."
        
        msgs.append(msg)
    
    # 最后一条: 行动清单（投资+家庭+生活三维度）
    checklist = "📋 今日关注\n"
    checklist += "━━━━━━━━━━━━━━━━\n"
    checklist += "💰 投资: BTC 0.642个 | USDT $10.5K待命\n"
    checklist += "    MA120下方→暂存USDT，站回后定投\n"
    checklist += "⚠️ CRCL占47.9%→$100触发止盈\n"
    checklist += "✅ 币安借贷已还清 | 信用卡¥40W待降\n"
    checklist += "━━━━━━━━━━━━━━━━\n"
    checklist += "🏠 家庭: 保险韩伟✅重疾50W | 定寿待配置\n"
    checklist += "    薛燕重疾待配置 | 孩子升学规划\n"
    checklist += "    家庭账户与投资账户严格隔离\n"
    checklist += "━━━━━━━━━━━━━━━━\n"
    checklist += "🧘 生活: TFLM学习 | 每天30分钟信息摄入\n"
    checklist += "    减少盯盘焦虑 | 保持长期主义心态\n"
    checklist += "━━━━━━━━━━━━━━━━\n"
    checklist += "🤖 自动推送 | 四维度精简模式"
    msgs.append(checklist)
    
    return msgs


def send_one_wechat(text, to=DEFAULT_USER, timeout=20):
    """通过 Bun + JSON-RPC 直接发送一条微信消息（不依赖外部脚本）"""
    try:
        server = subprocess.Popen(
            [BUN, MCP_SERVER],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "HOME": os.environ.get("USERPROFILE", "")}
        )
        
        # JSON-RPC 2.0 握手
        def _send_json(obj):
            server.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
            server.stdin.flush()
        
        _send_json({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "x-tweets-pusher", "version": "1.0.0"}}
        })
        
        buffer = b""
        done = False
        
        while not done:
            chunk = server.stdout.readline()
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
                    # 初始化响应 → 发送 initialized 通知 + 发送消息请求
                    _send_json({"jsonrpc": "2.0", "method": "notifications/initialized"})
                    _send_json({
                        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "send_text_message",
                                   "arguments": {"to": to, "text": text}}
                    })
                
                elif resp.get("id") == 2:
                    done = True
                    if resp.get("error"):
                        print(f"[ERROR] 推送失败: {resp['error']}")
                        server.kill()
                        return False
                    else:
                        print("[OK] 微信推送成功")
                        server.kill()
                        return True
            except json.JSONDecodeError:
                continue
        
        server.kill()
        return False
        
    except FileNotFoundError as e:
        print(f"[ERROR] Bun 或 mcp-wechat-server 未找到: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 推送异常: {e}")
        return False


def push_to_wechat_bun(tweets, to=DEFAULT_USER):
    """通过 Bun JSON-RPC 分段推送到微信"""
    msgs = build_messages(tweets)
    print(f"\n[INFO] 准备推送 {len(msgs)} 条消息到微信...")
    
    success_count = 0
    for i, msg in enumerate(msgs):
        print(f"\n[{i+1}/{len(msgs)}] 发送中 ({len(msg)}字)...")
        if send_one_wechat(msg, to):
            success_count += 1
        else:
            print(f"[WARN] 第{i+1}条发送失败，继续下一条")
        
        if i < len(msgs) - 1:
            time.sleep(SEND_INTERVAL)
    
    print(f"\n[INFO] 推送完成: {success_count}/{len(msgs)} 成功")
    return success_count > 0


if __name__ == "__main__":
    tweets = load_tweets()
    msgs = build_messages(tweets)
    for i, m in enumerate(msgs):
        print(f"\n=== Message {i+1} ({len(m)} chars) ===")
        print(m)
    print(f"\nTotal: {len(msgs)} messages (filtered from {len(tweets)} tweets)")
    
    # 如果命令行带 --push 参数，执行推送
    if "--push" in __import__("sys").argv:
        push_to_wechat_bun(tweets)
