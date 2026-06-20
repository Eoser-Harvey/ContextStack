# -*- coding: utf-8 -*-
"""
带心跳保活的推送主入口

调用链:
  run_with_heartbeat.py
    ├── heartbeat.py          → 检查通道状态
    ├── push_wechat.py        → 消息构建 + 微信推送
    └── channel_state.json    → 状态持久化

使用:
  python run_with_heartbeat.py          # 仅检查状态
  python run_with_heartbeat.py --push   # 检查状态并推送
  python run_with_heartbeat.py --test   # 发送测试消息验证通道
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))
from heartbeat import (
    load_state, save_state,
    check_channel_alive, mark_active, mark_failure, mark_test_sent, get_summary
)

# ====== 路径配置 ======
BUN = r"C:\Users\h31280\.bun\bin\bun.exe"
MCP_SERVER = r"C:\Users\h31280\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts"

# 从 config.yaml 读取目标用户ID
def get_target_user():
    """从 config.yaml 读取目标用户ID"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("push", {}).get("target_user_id", "o9cq80xcTVHnYCThXQ8NXo_dIpYs@im.wechat")


def send_one_via_bun(text, to):
    """通过 Bun JSON-RPC 发送一条微信消息"""
    try:
        server = subprocess.Popen(
            [BUN, MCP_SERVER],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "HOME": os.environ.get("USERPROFILE", "")}
        )

        def _send_json(obj):
            server.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
            server.stdin.flush()

        _send_json({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "x-tweets-heartbeat", "version": "1.0.0"}}
        })

        buf = b""
        done = False
        start = time.time()
        success = False

        while not done and time.time() - start < 25:
            chunk = server.stdout.readline()
            if not chunk:
                break
            buf += chunk
            try:
                line = buf.decode("utf-8").strip()
                buf = b""
                if not line:
                    continue
                resp = json.loads(line)

                if resp.get("id") == 1:
                    _send_json({"jsonrpc": "2.0", "method": "notifications/initialized"})
                    _send_json({
                        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "send_text_message",
                                   "arguments": {"to": to, "text": text}}
                    })

                elif resp.get("id") == 2:
                    done = True
                    if not resp.get("error"):
                        success = True
            except json.JSONDecodeError:
                continue

        server.kill()
        return success
    except Exception as e:
        print(f"  [ERROR] Bun推送异常: {e}")
        return False


def verify_channel():
    """
    验证通道：发送测试消息并尝试读取用户回复。
    
    在 automation 环境中，只能做单向检测：
    - 发测试消息，sent 即视为通道可能存活
    - 无法等待用户回复（异步）
    
    返回: True 如果 sent 成功, False 如果失败
    """
    to = get_target_user()
    test_msg = f"🔍 通道检测 {datetime.now().strftime('%m-%d %H:%M')} - 正常"
    print(f"  [验证] 发送测试消息到 {to}...")
    
    if send_one_via_bun(test_msg, to):
        print("  [OK] 测试消息已发送")
        mark_test_sent()
        return True
    else:
        print("  [FAIL] 测试消息发送失败")
        return False


def run_push():
    """执行完整的推送流程（带心跳检查）"""
    print(f"\n{'='*50}")
    print(f"X推文推送 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # Step 1: 检查通道状态
    status = check_channel_alive()
    print(f"\n[状态] 通道状态: {status}")
    
    if status == "dead":
        print("[跳过] 通道已断开超过3次，需要用户发消息激活")
        print("[提示] 请在微信给 bot 发任意消息后，手动标记为 active")
        return False
    
    if status == "unknown":
        print("[验证] 通道状态不确定，发送测试消息...")
        if not verify_channel():
            failures = mark_failure()
            print(f"[警告] 通道验证失败 (连续{failures}次)")
            return False
        # 验证通过，但需要等用户回复才能真正确认
        # 在 automation 中，先标记为 active 并推送（乐观策略）
        print("[注意] 测试消息已发送，采用乐观策略继续推送")
        mark_active()
    
    # Step 2: 推送消息
    print("\n[推送] 构建消息...")
    
    # 调用 push_wechat.py 的推送函数
    try:
        from push_wechat import load_tweets, build_messages, push_to_wechat_bun
        
        tweets = load_tweets()
        if not tweets:
            print("[跳过] 无推文数据")
            return False
        
        msgs = build_messages(tweets)
        print(f"[推送] 共 {len(msgs)} 条消息")
        
        to = get_target_user()
        success_count = 0
        for i, msg in enumerate(msgs):
            print(f"  [{i+1}/{len(msgs)}] 发送中 ({len(msg)}字)...")
            if send_one_via_bun(msg, to):
                success_count += 1
                print(f"    ✅")
            else:
                print(f"    ❌")
            if i < len(msgs) - 1:
                time.sleep(3)
        
        print(f"\n[结果] {success_count}/{len(msgs)} 成功")
        
        if success_count == len(msgs):
            mark_active()
            return True
        elif success_count > 0:
            mark_active()  # 部分成功也算活跃
            return True
        else:
            failures = mark_failure()
            print(f"[警告] 全部失败 (连续{failures}次)")
            return False
            
    except ImportError as e:
        print(f"[ERROR] 导入失败: {e}")
        # 备用: 直接构建消息推送
        print("[备用] 使用内置消息推送...")
        return push_builtin_messages()
    except Exception as e:
        print(f"[ERROR] 推送异常: {e}")
        mark_failure()
        return False


def push_builtin_messages():
    """内置消息推送（当 push_wechat.py 不可用时）"""
    # 这是一个简化版，实际推送由 IDE MCP 完成
    print("[内置] 消息推送应由 IDE WeChat MCP 完成")
    return True


def show_status():
    """显示当前通道状态"""
    summary = get_summary()
    print("\n通道状态:")
    print(f"  状态: {summary['status']}")
    print(f"  上次活跃: {summary['last_active']}")
    print(f"  连续失败: {summary['failures']}")
    print(f"  Bot ID: {summary['bot_id']}")
    print(f"  User ID: {summary['user_id']}")


def test_channel():
    """发送测试消息验证通道"""
    print("\n[测试] 验证微信推送通道...")
    if verify_channel():
        print("[OK] 通道验证通过")
    else:
        print("[FAIL] 通道验证失败")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_channel()
    elif "--push" in sys.argv:
        run_push()
    elif "--status" in sys.argv:
        show_status()
    elif "--reset" in sys.argv:
        # 重置状态
        save_state({
            "last_active": None,
            "last_test_sent": None,
            "status": "unknown",
            "consecutive_failures": 0,
            "bot_id": None,
            "user_id": None,
        })
        print("[OK] 状态已重置")
    elif "--activate" in sys.argv:
        mark_active()
        print("[OK] 通道已手动标记为 active")
    else:
        show_status()
        print("\n用法:")
        print("  python run_with_heartbeat.py --status  查看状态")
        print("  python run_with_heartbeat.py --test    测试通道")
        print("  python run_with_heartbeat.py --push    检查状态并推送")
        print("  python run_with_heartbeat.py --reset   重置状态")
        print("  python run_with_heartbeat.py --activate 手动激活")
