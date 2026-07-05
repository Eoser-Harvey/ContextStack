"""
飞书消息推送通用模块 — 端侧AI日报版
支持：获取 tenant_access_token（含缓存）、发送 interactive 卡片消息、验证消息完整性
"""
import json
import os
import time
import yaml
import requests
from typing import Optional, Dict, Any


# ==================== 配置 ====================
BASE_URL = "https://open.feishu.cn/open-apis"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_CACHE_FILE = os.path.join(SCRIPT_DIR, ".lark_token_cache.json")
TOKEN_EXPIRE_BUFFER = 300


def _get_script_dir() -> str:
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))
    return os.getcwd()


def load_secrets(secrets_path: Optional[str] = None) -> Dict[str, str]:
    """加载飞书 Bot 凭证。优先级: 环境变量 > .secrets.yaml"""
    app_id = os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("LARK_APP_SECRET")
    chat_id = os.environ.get("LARK_CHAT_ID")

    if app_id and app_secret and chat_id:
        print("[INFO] 使用环境变量中的飞书凭证")
        return {"app_id": app_id, "app_secret": app_secret, "chat_id": chat_id}

    if secrets_path is None:
        secrets_path = os.path.join(_get_script_dir(), ".secrets.yaml")

    if not os.path.exists(secrets_path):
        print("[FATAL] 未找到飞书凭证配置!")
        print(f"请创建 {secrets_path}")
        exit(1)

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


# ==================== Token 管理 ====================

def _load_token_cache() -> Optional[Dict[str, Any]]:
    if not os.path.exists(TOKEN_CACHE_FILE):
        return None
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_token_cache(token: str, expires_in: int):
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
    cache = _load_token_cache()
    if cache and cache.get("token"):
        now = int(time.time())
        if now < cache.get("expires_at", 0) - TOKEN_EXPIRE_BUFFER:
            print(f"[INFO] 使用缓存的 token")
            return cache["token"]

    print("[INFO] 请求新的 tenant_access_token ...")
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: code={data.get('code')}, msg={data.get('msg')}")

    token = data["tenant_access_token"]
    expires_in = data.get("expire", 7200)
    _save_token_cache(token, expires_in)
    print(f"[INFO] 新 token 获取成功，有效期 {expires_in}s")
    return token


# ==================== 飞书 API 调用 ====================

def send_interactive_card(chat_id: str, card_json: Dict[str, Any],
                          app_id: Optional[str] = None,
                          app_secret: Optional[str] = None) -> str:
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

    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"发送消息失败: code={data.get('code')}, msg={data.get('msg')}")

    message_id = data.get("data", {}).get("message_id", "")
    print(f"[INFO] 消息发送成功，message_id: {message_id}")
    return message_id