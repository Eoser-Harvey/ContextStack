"""
飞书消息推送通用模块 — 日报版
支持：获取 tenant_access_token（含缓存）、发送 interactive 卡片消息、验证消息完整性

凭证管理: 从本地 .secrets.yaml 加载（已在 .gitignore 排除，不提交 Git）。
          环境变量 LARK_APP_ID / LARK_APP_SECRET / LARK_CHAT_ID 可覆盖。
"""
import json
import os
import time
import yaml
import requests
from typing import Optional, Dict, Any


# ==================== 配置 ====================
BASE_URL = "https://open.feishu.cn/open-apis"
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".lark_token_cache.json")
TOKEN_EXPIRE_BUFFER = 300  # 提前5分钟刷新


def _get_script_dir() -> str:
    """获取当前脚本所在目录（兼容直接执行和 import）"""
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))
    return os.getcwd()


def load_secrets(secrets_path: Optional[str] = None) -> Dict[str, str]:
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
        print("请创建 .secrets.yaml 文件（参考小时推送项目的 .secrets.yaml）:")
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


# ==================== Token 管理 ====================

def _load_token_cache() -> Optional[Dict[str, Any]]:
    """从缓存文件读取 token"""
    if not os.path.exists(TOKEN_CACHE_FILE):
        return None
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError):
        return None


def _save_token_cache(token: str, expires_in: int):
    """保存 token 到缓存文件"""
    cache = {
        "token": token,
        "expires_at": int(time.time()) + expires_in,
        "fetched_at": int(time.time()),
    }
    try:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[WARN] 无法写入 token 缓存: {e}")


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token。

    优先使用缓存（提前5分钟过期刷新），缓存失效则重新请求。
    """
    # 1. 尝试从缓存读取
    cache = _load_token_cache()
    if cache and cache.get("token"):
        now = int(time.time())
        if now < cache.get("expires_at", 0) - TOKEN_EXPIRE_BUFFER:
            print(f"[INFO] 使用缓存的 token，有效期至 {time.strftime('%H:%M:%S', time.localtime(cache['expires_at']))}")
            return cache["token"]

    # 2. 请求新 token
    print("[INFO] 请求新的 tenant_access_token ...")
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"获取 tenant_access_token 网络请求失败: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 token 响应失败: {e}")

    if data.get("code") != 0:
        raise RuntimeError(f"获取 tenant_access_token 失败: code={data.get('code')}, msg={data.get('msg')}")

    token = data["tenant_access_token"]
    expires_in = data.get("expire", 7200)
    _save_token_cache(token, expires_in)
    print(f"[INFO] 新 token 获取成功，有效期 {expires_in}s")
    return token


# ==================== 飞书 API 调用 ====================

def send_interactive_card(chat_id: str, card_json: Dict[str, Any],
                          app_id: Optional[str] = None,
                          app_secret: Optional[str] = None) -> str:
    """发送 interactive 卡片消息到指定群聊。

    Args:
        chat_id: 群聊 ID
        card_json: 飞书 interactive 卡片 JSON
        app_id: 飞书 App ID（可选，不传则自动从 .secrets.yaml 或环境变量加载）
        app_secret: 飞书 App Secret（可选）

    Returns:
        message_id
    """
    if app_id is None or app_secret is None:
        secrets = load_secrets()
        app_id = secrets["app_id"]
        app_secret = secrets["app_secret"]

    token = get_tenant_access_token(app_id, app_secret)
    url = f"{BASE_URL}/im/v1/messages?receive_id_type=chat_id"

    payload = {
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card_json, ensure_ascii=False),
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"发送消息网络请求失败: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析发送消息响应失败: {e}")

    if data.get("code") != 0:
        raise RuntimeError(f"发送消息失败: code={data.get('code')}, msg={data.get('msg')}")

    message_id = data.get("data", {}).get("message_id", "")
    print(f"[INFO] 消息发送成功，message_id: {message_id}")
    return message_id


def verify_message(message_id: str, app_id: Optional[str] = None,
                   app_secret: Optional[str] = None) -> Dict[str, Any]:
    """通过 message_id 验证消息完整性（读取消息内容）。

    Args:
        message_id: 消息 ID
        app_id: 飞书 App ID（可选，不传则自动从 .secrets.yaml 或环境变量加载）
        app_secret: 飞书 App Secret（可选）

    Returns:
        dict: 飞书 API 原始响应
    """
    if app_id is None or app_secret is None:
        secrets = load_secrets()
        app_id = secrets["app_id"]
        app_secret = secrets["app_secret"]

    token = get_tenant_access_token(app_id, app_secret)
    url = f"{BASE_URL}/im/v1/messages/{message_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"验证消息网络请求失败: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析验证消息响应失败: {e}")

    if data.get("code") != 0:
        raise RuntimeError(f"验证消息失败: code={data.get('code')}, msg={data.get('msg')}")

    msg = data.get("data", {}).get("items", [{}])[0]
    msg_type = msg.get("msg_type", "")
    body = msg.get("body", {}).get("content", "")
    print(f"[INFO] 消息验证成功: msg_type={msg_type}, body_length={len(body)}")
    return data
