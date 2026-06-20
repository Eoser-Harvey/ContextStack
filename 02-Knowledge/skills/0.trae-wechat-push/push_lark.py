"""
飞书群推送模块 — 通过 lark-cli 发送推文到飞书群
调用链: Python → subprocess(lark-cli) → 飞书 IM API → 飞书群

关键: 使用 --content + json.dumps 传递完整多行文本，
避免 --text 模式下换行符被当作参数分隔符导致截断。
"""
import json
import os
import subprocess
import time
from datetime import datetime

# ====== 飞书群配置 ======
LARK_CHAT_ID = "oc_569a7503a8f86eeb1f4630f31f985e50"  # CodeBuddy推文推送①
SEND_INTERVAL = 2  # 消息间隔(秒)，防止飞书限流
LARK_CLI = r"C:\Users\harve\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\vm\tools\bin\lark-cli.cmd"
# 直接调用 node + lark-cli 脚本，避免 .cmd 文件中 cmd.exe 对 & 等特殊字符的误解析
LARK_NODE = r"D:\nodejs\node.exe"
LARK_SCRIPT = r"C:\Users\harve\AppData\Roaming\npm\node_modules\@larksuite\cli\scripts\run.js"
USE_DIRECT_NODE = os.path.exists(LARK_NODE) and os.path.exists(LARK_SCRIPT)


def send_text_lark(text, chat_id=LARK_CHAT_ID):
    """通过 lark-cli 发送一条纯文本消息到飞书群（完整多行内容）"""
    try:
        # 使用 --content + JSON 传递多行文本，避免换行符截断
        # 注：subprocess.run 传参列表不经过 shell 解析，双引号不会被吞掉
        content_json = json.dumps({"text": text}, ensure_ascii=False)
        # 优先使用 node 直接调用，避免 .cmd 中 cmd.exe 对特殊字符的误解析
        if USE_DIRECT_NODE:
            cmd = [LARK_NODE, LARK_SCRIPT, "im", "+messages-send",
                   "--chat-id", chat_id,
                   "--content", content_json,
                   "--as", "user"]
        else:
            cmd = [LARK_CLI, "im", "+messages-send",
                   "--chat-id", chat_id,
                   "--content", content_json,
                   "--as", "user"]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, encoding="utf-8",
            timeout=20
        )

        if result.returncode == 0:
            try:
                resp = json.loads(result.stdout)
                if resp.get("ok"):
                    print(f"[OK] 飞书推送成功 (msg_id: {resp.get('data', {}).get('message_id', '')})")
                    return True
                else:
                    err = resp.get("error", {})
                    print(f"[ERROR] 飞书推送失败: {err.get('message', 'unknown')}")
                    return False
            except json.JSONDecodeError:
                print(f"[ERROR] 飞书返回非JSON: {result.stdout[:200]}")
                return False
        else:
            stderr = result.stderr.strip()
            print(f"[ERROR] lark-cli 执行失败 (exit={result.returncode}): {stderr[:200]}")
            return False

    except FileNotFoundError:
        print("[ERROR] lark-cli 未找到")
        return False
    except subprocess.TimeoutExpired:
        print("[ERROR] lark-cli 超时(20秒)")
        return False
    except Exception as e:
        print(f"[ERROR] 飞书推送异常: {e}")
        return False


def build_lark_messages(tweets):
    """构建飞书推送消息列表（纯文本格式，完整内容）"""
    msgs = []

    # 统计
    users = {}
    for t in tweets:
        u = t.get("display_name", t.get("username", ""))
        users[u] = users.get(u, 0) + 1

    user_summary = " ｜ ".join(f"{u}({c})" for u, c in users.items())

    # 消息1: 摘要头
    now = datetime.now().strftime("%m-%d %H:%M")
    header = f"📡 X推文速递 ｜ {now}\n"
    header += "━━━━━━━━━━━━━━━━━━━━\n"
    header += f"共{len(tweets)}条 → 精选推送\n"
    header += f"关注: {user_summary}\n"
    header += "━━━━━━━━━━━━━━━━━━━━"
    msgs.append(header)

    # 消息2-N: 每条推文（完整内容，不截断）
    for tweet in tweets:
        username = tweet.get("display_name", tweet.get("username", ""))
        content = tweet.get("content", "")
        translated = tweet.get("translated", "")
        analysis = tweet.get("analysis", {})
        published = tweet.get("published_at", "")

        emoji_map = {
            "elonmusk": "🚀",
            "cz_binance": "₿",
            "realDonaldTrump": "🇺🇸",
            "aleabitoreddit": "👩‍🦳"
        }
        emoji = emoji_map.get(tweet.get("username", ""), "📢")

        msg = f"{emoji} 【{username}】\n"
        if published:
            msg += f"时间: {published}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"原文: {content}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"

        if translated and translated != content:
            msg += f"翻译: {translated}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━\n"

        if analysis.get("investment"):
            msg += f"\n💰 投资:\n{analysis['investment']}\n"
        if analysis.get("career"):
            msg += f"\n💼 职业:\n{analysis['career']}\n"
        if analysis.get("life"):
            msg += f"\n🧘 生活:\n{analysis['life']}\n"
        if analysis.get("family"):
            msg += f"\n👨‍👩‍👧 家庭:\n{analysis['family']}\n"

        msg += "\n━━━━━━━━━━━━━━━━━━━━"
        msgs.append(msg)

    # 最后一条: 行动清单
    checklist = "📋 今日关注\n"
    checklist += "━━━━━━━━━━━━━━━━━━━━\n"
    checklist += "💰 投资:\n"
    checklist += "  ├─ BTC 0.642个 ｜ USDT 10.5K待命\n"
    checklist += "  ├─ MA120下方→暂存USDT，站回后定投\n"
    checklist += "  ├─ CRCL占47.9%→100触发止盈\n"
    checklist += "  └─ ✅ 币安借贷已还清 ｜ 信用卡40W待降\n"
    checklist += "━━━━━━━━━━━━━━━━━━━━\n"
    checklist += "🏠 家庭:\n"
    checklist += "  ├─ 保险韩伟✅重疾50W ｜ 定寿待配置\n"
    checklist += "  ├─ 薛燕重疾待配置 ｜ 孩子升学规划\n"
    checklist += "  └─ 家庭账户与投资账户严格隔离\n"
    checklist += "━━━━━━━━━━━━━━━━━━━━\n"
    checklist += "🧘 生活:\n"
    checklist += "  ├─ TFLM学习 ｜ 每天30分钟信息摄入\n"
    checklist += "  └─ 减少盯盘焦虑 ｜ 保持长期主义心态\n"
    checklist += "━━━━━━━━━━━━━━━━━━━━\n"
    checklist += "🤖 自动推送 ｜ 飞书群版"
    msgs.append(checklist)

    return msgs


def push_to_lark(tweets, chat_id=LARK_CHAT_ID):
    """通过 lark-cli 分段推送到飞书群"""
    msgs = build_lark_messages(tweets)
    print(f"\n[INFO] 准备推送 {len(msgs)} 条消息到飞书群 ({chat_id})...")

    success_count = 0
    for i, msg in enumerate(msgs):
        print(f"\n[{i+1}/{len(msgs)}] 发送中 ({len(msg)}字)...")
        if send_text_lark(msg, chat_id):
            success_count += 1
        else:
            print(f"[WARN] 第{i+1}条发送失败，继续下一条")

        if i < len(msgs) - 1:
            time.sleep(SEND_INTERVAL)

    print(f"\n[INFO] 推送完成: {success_count}/{len(msgs)} 成功")
    return success_count > 0


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "latest_tweets.json")

    if not os.path.exists(data_path):
        print(f"[ERROR] 未找到 {data_path}，请先运行 run_auto.py")
        exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    push_to_lark(tweets)