# -*- coding: utf-8 -*-
"""
微信 Bot 独立保活进程 v2

原理:
  通过 Bun → mcp-wechat-server 建立与微信服务器的长连接。
  每30秒调用 get_messages(wait=false) 保持与微信服务器的连接活跃。
  这会阻止微信服务器认为 Bot 已离线而断开会话。

运行:
  python keepalive.py              # 前台运行
  python keepalive.py --daemon     # 后台运行（通过 pythonw）

依赖:
  Bun + mcp-wechat-server (路径在下方常量中定义)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

BUN = r"C:\Users\h31280\.bun\bin\bun.exe"
MCP_SERVER = r"C:\Users\h31280\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts"
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
    ".codebuddy", "automations", "x-3", "channel_state.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
    ".codebuddy", "automations", "x-3", "keepalive.log")

INTERVAL = 30  # 轮询间隔（秒）


def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def init_session():
    """初始化 Bun + mcp-wechat-server 会话"""
    server = subprocess.Popen(
        [BUN, MCP_SERVER],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "HOME": os.environ.get("USERPROFILE", "")}
    )

    def _send(obj):
        server.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
        server.stdin.flush()

    _send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "keepalive", "version": "2.0"}}})

    buf = b""
    start = time.time()
    while time.time() - start < 10:
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
                _send({"jsonrpc": "2.0", "method": "notifications/initialized"})
                return server
        except json.JSONDecodeError:
            continue

    server.kill()
    return None


def heartbeat(server):
    """发送一次心跳轮询"""
    try:
        rid = int(time.time() * 1000) % 100000
        req = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
               "params": {"name": "get_messages",
                          "arguments": {"wait": False, "timeout": 3000}}}
        server.stdin.write((json.dumps(req) + "\n").encode("utf-8"))
        server.stdin.flush()

        buf = b""
        start = time.time()
        while time.time() - start < 8:
            chunk = server.stdout.readline()
            if not chunk:
                time.sleep(0.2)
                continue
            buf += chunk
            try:
                line = buf.decode("utf-8").strip()
                buf = b""
                if not line:
                    continue
                resp = json.loads(line)
                if resp.get("id") == rid:
                    return True
            except json.JSONDecodeError:
                continue
        return False
    except:
        return False


def update_state():
    """更新状态文件"""
    try:
        state = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        state["keepalive_pid"] = os.getpid()
        state["keepalive_last"] = datetime.now().isoformat()
        state["keepalive_alive"] = True
        state["status"] = "active"
        state["last_active"] = datetime.now().isoformat()
        state["consecutive_failures"] = 0
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except:
        pass


def run():
    log("=" * 40)
    log("保活进程 v2 启动")
    log(f"PID: {os.getpid()}  |  间隔: {INTERVAL}s")

    session = init_session()
    if not session:
        log("❌ 无法建立Bun会话")
        return

    log("✅ Bun会话已建立，开始保活循环")
    update_state()

    count = 0
    fail_count = 0

    while True:
        time.sleep(INTERVAL)
        count += 1

        ok = heartbeat(session)
        if ok:
            fail_count = 0
            if count % 10 == 0:  # 每10次（5分钟）打一次日志
                log(f"♥ #{count} OK")
            update_state()
        else:
            fail_count += 1
            log(f"⚠️ #{count} 心跳失败 ({fail_count})")

            if fail_count >= 3:
                log("🔄 重建Bun会话...")
                try:
                    session.kill()
                except:
                    pass
                time.sleep(3)
                session = init_session()
                if not session:
                    log("❌ 重建失败，进程退出")
                    return
                fail_count = 0
                log("✅ 会话重建成功")
                update_state()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        log("收到终止信号，退出")
    except Exception as e:
        log(f"异常退出: {e}")
