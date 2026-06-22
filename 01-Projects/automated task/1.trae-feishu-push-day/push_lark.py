"""
飞书消息推送通用模块
支持：获取 tenant_access_token（含缓存）、发送 interactive 卡片消息、验证消息完整性
"""

import json
import os
import time
import requests
from typing import Optional, Dict, Any

# ==================== 配置 ====================
APP_ID = "LARK_APP_ID_REMOVED"
APP_SECRET = "LARK_APP_SECRET_REMOVED"
BASE_URL = "https://open.feishu.cn/open-apis"
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".lark_token_cache.json")
TOKEN_EXPIRE_BUFFER = 300  # 提前5分钟刷新


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


def get_tenant_access_token() -> str:
    """
    获取 tenant_access_token。
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
        "app_id": APP_ID,
        "app_secret": APP_SECRET,
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


def send_interactive_card(chat_id: str, card_json: Dict[str, Any]) -> str:
    """
    发送 interactive 卡片消息到指定群聊。
    返回 message_id。
    """
    token = get_tenant_access_token()
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


def verify_message(message_id: str) -> Dict[str, Any]:
    """
    通过 message_id 验证消息完整性（读取消息内容）。
    """
    token = get_tenant_access_token()
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