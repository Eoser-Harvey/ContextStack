"""
飞书群推送模块 — 直接调用飞书 Open API (Bot 身份)
调用链: Python → HTTP POST → 飞书 Open API → 飞书群

关键: 使用 Bot 身份 (appId + appSecret)，无需用户授权，永久有效。
      直接调用飞书 REST API，不依赖 lark-cli，不受 TRAE 环境限制。

凭证管理: 从本地 .secrets.yaml 加载（已在 .gitignore 排除，不提交 Git）。
          环境变量 LARK_APP_ID / LARK_APP_SECRET / LARK_CHAT_ID 可覆盖。
"""
import json
import os
import time
import yaml
import requests
from datetime import datetime


# ====== 默认值（优先从 .secrets.yaml 或环境变量读取） ======
SEND_INTERVAL = 2   # 消息间隔(秒)，防止飞书限流
LARK_API_BASE = "https://open.feishu.cn/open-apis"

# token 缓存
_token_cache = {"token": "", "expires_at": 0}


def _get_script_dir():
    """获取当前脚本所在目录（兼容直接执行和 import）"""
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))
    return os.getcwd()


def load_secrets(secrets_path=None):
    """加载飞书 Bot 凭证。

    优先级: 环境变量 > .secrets.yaml > 无（报错退出）

    Args:
        secrets_path: .secrets.yaml 的路径，默认脚本同目录下的 .secrets.yaml

    Returns:
        dict: {"app_id": str, "app_secret": str, "chat_id": str}
    """
    # 1) 环境变量优先（适合 CI/CD / GitHub Actions）
    app_id = os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("LARK_APP_SECRET")
    chat_id = os.environ.get("LARK_CHAT_ID")

    if app_id and app_secret and chat_id:
        print("[INFO] 使用环境变量中的飞书凭证")
        return {"app_id": app_id, "app_secret": app_secret, "chat_id": chat_id}

    # 2) 从 .secrets.yaml 读取（本地开发默认方式）
    if secrets_path is None:
        secrets_path = os.path.join(_get_script_dir(), ".secrets.yaml")

    if not os.path.exists(secrets_path):
        print("=" * 60)
        print("[FATAL] 未找到飞书凭证配置!")
        print("")
        print("请创建 .secrets.yaml 文件（参考 .secrets.yaml.example）:")
        print(f"  {secrets_path}")
        print("")
        print("文件内容格式:")
        print("  lark:")
        print('    app_id: "cli_xxxxxxxxxxxxxxxxxxxxx"')
        print('    app_secret: "your_app_secret_here"')
        print('    chat_id: "oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')
        print("")
        print("也可通过环境变量传入:")
        print("  环境变量 LARK_APP_ID / LARK_APP_SECRET / LARK_CHAT_ID")
        print("=" * 60)
        exit(1)

    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        lark_cfg = data.get("lark", {})
        app_id = lark_cfg.get("app_id", "")
        app_secret = lark_cfg.get("app_secret", "")
        chat_id = lark_cfg.get("chat_id", "")

        if not all([app_id, app_secret, chat_id]):
            raise ValueError(".secrets.yaml 中缺少 lark.app_id / app_secret / chat_id")

        print(f"[INFO] 从 .secrets.yaml 加载飞书凭证 (chat_id: {chat_id[:8]}...)")
        return {"app_id": str(app_id), "app_secret": str(app_secret), "chat_id": str(chat_id)}

    except Exception as e:
        print(f"[FATAL] 解析 .secrets.yaml 失败: {e}")
        exit(1)


# ====== 飞书 API 调用 ======

def get_tenant_access_token(app_id, app_secret):
    """获取 tenant_access_token (Bot 身份，自动缓存)"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    try:
        resp = requests.post(
            f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal",
            json=payload,
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 0:
            token = data["tenant_access_token"]
            expire = data.get("expire", 7200)
            _token_cache["token"] = token
            _token_cache["expires_at"] = now + expire - 300  # 提前5分钟刷新
            print("[INFO] Bot token 获取成功")
            return token
        else:
            print(f"[ERROR] 获取token失败: {data.get('msg', 'unknown')}")
            return None
    except Exception as e:
        print(f"[ERROR] 获取token异常: {e}")
        return None


def send_text_lark(text, chat_id, app_id, app_secret):
    """通过飞书 Open API 发送纯文本消息到群聊 (Bot 身份)"""
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        print("[ERROR] 无法获取token，跳过发送")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    params = {"receive_id_type": "chat_id"}

    try:
        resp = requests.post(
            f"{LARK_API_BASE}/im/v1/messages",
            headers=headers,
            json=payload,
            params=params,
            timeout=20,
        )
        data = resp.json()
        if data.get("code") == 0:
            msg_id = data.get("data", {}).get("message_id", "")
            print(f"[OK] 飞书推送成功 (msg_id: {msg_id})")
            return True
        else:
            print(f"[ERROR] 飞书推送失败: code={data.get('code')}, msg={data.get('msg', 'unknown')}")
            return False
    except requests.Timeout:
        print("[ERROR] 飞书API超时(20秒)")
        return False
    except Exception as e:
        print(f"[ERROR] 飞书推送异常: {e}")
        return False


# ====== 消息构建 ======

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
            "aleaborteddit": "👩‍🦳"
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

        if analysis.get("summary"):
            # 非关键推文 → 只显示摘要
            msg += f"\n💡 {analysis['summary']}\n"
        else:
            # 关键推文 → 显示完整建议
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
    checklist += "🤖 自动推送 ｜ Bot飞书群版"
    msgs.append(checklist)

    return msgs


# ====== 对外接口 ======

def push_to_lark(tweets, secrets=None):
    """通过飞书 Open API 分段推送到群聊 (Bot 身份)

    Args:
        tweets: 推文列表
        secrets: 可选，{"app_id", "app_secret", "chat_id"} 字典。
                 不传则自动从 .secrets.yaml 或环境变量加载。
    """
    if secrets is None:
        secrets = load_secrets()

    app_id = secrets["app_id"]
    app_secret = secrets["app_secret"]
    chat_id = secrets["chat_id"]

    msgs = build_lark_messages(tweets)
    print(f"\n[INFO] 准备推送 {len(msgs)} 条消息到飞书群 ({chat_id}) [Bot身份]...")

    success_count = 0
    for i, msg in enumerate(msgs):
        print(f"\n[{i+1}/{len(msgs)}] 发送中 ({len(msg)}字)...")
        if send_text_lark(msg, chat_id, app_id, app_secret):
            success_count += 1
        else:
            print(f"[WARN] 第{i+1}条发送失败，继续下一条")

        if i < len(msgs) - 1:
            time.sleep(SEND_INTERVAL)

    print(f"\n[INFO] 推送完成: {success_count}/{len(msgs)} 成功")
    return success_count > 0


# ====== 直接执行 ======

if __name__ == "__main__":
    secrets = load_secrets()

    base_dir = _get_script_dir()
    data_path = os.path.join(base_dir, "latest_tweets.json")

    if not os.path.exists(data_path):
        print(f"[ERROR] 未找到 {data_path}，请先运行 run_auto.py")
        exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    push_to_lark(tweets, secrets)
