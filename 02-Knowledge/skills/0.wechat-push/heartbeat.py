# -*- coding: utf-8 -*-
"""
WeChat Bot 心跳保活模块

原理:
  mcp-wechat-server 使用微信网页版协议。bot 必须用户先发消息才能激活回复通道。
  通道激活后，在一定时间内（通常数小时）保持可用。
  如果通道断开，需要用户主动发一条消息重新激活。

本模块职责:
  1. 每次推送前检查通道是否存活
  2. 存活 → 正常推送
  3. 断开 → 无法自动修复，记录日志，等用户手动激活

通道存活检测方法:
  - 方法A: 发一条测试消息，如果用户反馈"收到了"则通道存活
  - 方法B: 依赖 get_messages 是否有最近的用户消息来判断
  - 实际: 两种方法结合 —— 先发测试消息，如果 sent 但用户无反馈，标记为可疑

状态文件: .codebuddy/automations/x-3/channel_state.json
  - last_active: 上次确认通道存活的时间
  - last_test_sent: 上次测试消息发送时间
  - status: "active" | "unknown" | "dead"
  - consecutive_failures: 连续失败次数
"""

import json
import os
import time
from datetime import datetime, timedelta

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    ".codebuddy", "automations", "x-3", "channel_state.json"
)

# 通道存活有效期（小时）：超过此时间未确认，视为 unknown
CHANNEL_TTL_HOURS = 2

# 连续失败 N 次后标记为 dead
MAX_FAILURES = 3


def load_state():
    """加载通道状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "last_active": None,
        "last_test_sent": None,
        "status": "unknown",
        "consecutive_failures": 0,
        "bot_id": None,
        "user_id": None,
    }


def save_state(state):
    """保存通道状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _parse_dt(dt_str):
    """兼容 Python 3.6 的 ISO 时间解析"""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")


def check_channel_alive():
    """
    检查通道是否存活。
    
    返回:
      "active"  - 通道确认存活，可以推送
      "unknown" - 通道状态不确定，建议先发测试消息验证
      "dead"    - 通道已确认断开，需要用户激活
    """
    state = load_state()
    
    if state["status"] == "dead":
        return "dead"
    
    if state["last_active"]:
        last = _parse_dt(state["last_active"])
        if datetime.now() - last > timedelta(hours=CHANNEL_TTL_HOURS):
            return "unknown"
        return "active"
    
    return "unknown"


def mark_active(bot_id=None, user_id=None):
    """标记通道为活跃"""
    state = load_state()
    state["status"] = "active"
    state["last_active"] = datetime.now().isoformat()
    state["consecutive_failures"] = 0
    if bot_id:
        state["bot_id"] = bot_id
    if user_id:
        state["user_id"] = user_id
    save_state(state)


def mark_test_sent():
    """记录测试消息已发送"""
    state = load_state()
    state["last_test_sent"] = datetime.now().isoformat()
    save_state(state)


def mark_failure():
    """记录一次推送失败"""
    state = load_state()
    state["consecutive_failures"] += 1
    if state["consecutive_failures"] >= MAX_FAILURES:
        state["status"] = "dead"
    save_state(state)
    return state["consecutive_failures"]


def get_summary():
    """获取通道状态摘要（供日志使用）"""
    state = load_state()
    return {
        "status": state["status"],
        "last_active": state["last_active"],
        "failures": state["consecutive_failures"],
        "bot_id": state.get("bot_id"),
        "user_id": state.get("user_id"),
    }


if __name__ == "__main__":
    print("当前通道状态:")
    print(json.dumps(get_summary(), indent=2, ensure_ascii=False))
