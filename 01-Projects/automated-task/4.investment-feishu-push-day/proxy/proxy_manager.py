"""
Mihomo 代理管理器 — 用于投资日报中的代理需求
自动下载订阅、启动 mihomo、提供 SOCKS5 代理
"""
import os
import json
import subprocess
import sys
import time
import signal
import socket
import requests
import yaml
from typing import Optional, Dict, Any

# ==================== 配置 ====================

MIHOMO_DIR = os.path.dirname(os.path.abspath(__file__))
MIHOMO_EXE = os.path.join(MIHOMO_DIR, "mihomo.exe")
CONFIG_PATH = os.path.join(MIHOMO_DIR, "clash_runtime.yaml")
SUBSCRIPTION_URL = "https://8y1yhsevv8.qinyues4.cc/46028dfe024bc994794c553403847114"
SUB_UA = "clash-verge/v2.0.0"

# 本地代理端口
SOCKS_PORT = 7898
HTTP_PORT = 7899
MIXED_PORT = 7897

_mihomo_process: Optional[subprocess.Popen] = None


# ==================== 订阅解析 ====================

def fetch_subscription() -> Dict[str, Any]:
    """获取并解析 Clash 订阅，提取第一个可用的 SS 节点"""
    print("[Proxy] 获取订阅配置...")
    resp = requests.get(SUBSCRIPTION_URL, headers={"User-Agent": SUB_UA}, timeout=15)
    resp.raise_for_status()
    config = yaml.safe_load(resp.text)

    proxies = config.get("proxies", [])
    if not proxies:
        raise RuntimeError("订阅中没有代理节点")

    # 优先使用香港节点
    hk = [p for p in proxies if "香港" in p.get("name", "")]
    selected = hk[0] if hk else proxies[0]

    print(f"[Proxy] 选择节点: {selected['name']} ({selected['server']}:{selected['port']})")
    return selected


def generate_clash_config(proxy: Dict[str, Any]) -> str:
    """生成临时的 Clash 运行时配置"""
    template = f"""# Auto-generated runtime config
mixed-port: {MIXED_PORT}
socks-port: {SOCKS_PORT}
port: {HTTP_PORT}
allow-lan: false
mode: global
log-level: warning
ipv6: true

dns:
  enable: true
  enhanced-mode: fake-ip
  nameserver:
    - 223.5.5.5
    - 119.29.29.29

proxies:
  - name: "SS-PROXY"
    type: ss
    server: "{proxy['server']}"
    port: {proxy['port']}
    cipher: {proxy['cipher']}
    password: "{proxy['password']}"
    udp: true

proxy-groups:
  - name: "Proxy"
    type: select
    proxies:
      - "SS-PROXY"

rules:
  - MATCH,Proxy
"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(template)
    return CONFIG_PATH


def _wait_for_proxy(timeout: float = 10) -> bool:
    """等待代理就绪"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sock = socket.create_connection(("127.0.0.1", SOCKS_PORT), timeout=1)
            sock.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


# ==================== 启动/停止代理 ====================

def start_proxy() -> bool:
    """启动 mihomo 代理（如果尚未运行）"""
    global _mihomo_process

    if _mihomo_process is not None:
        if _mihomo_process.poll() is None:
            print("[Proxy] 代理已在运行中")
            return True
        else:
            print("[Proxy] 之前的进程已退出，重新启动...")
            _mihomo_process = None

    if not os.path.exists(MIHOMO_EXE):
        raise FileNotFoundError(f"找不到 mihomo: {MIHOMO_EXE}")

    # 获取订阅并生成配置
    proxy = fetch_subscription()
    generate_clash_config(proxy)

    print(f"[Proxy] 启动 mihomo...")
    _mihomo_process = subprocess.Popen(
        [MIHOMO_EXE, "-d", MIHOMO_DIR, "-f", CONFIG_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    if _wait_for_proxy():
        print(f"[Proxy] 代理已就绪: socks5://127.0.0.1:{SOCKS_PORT}")
        return True
    else:
        print("[Proxy] 代理启动超时")
        stop_proxy()
        return False


def stop_proxy():
    """停止 mihomo 代理"""
    global _mihomo_process
    if _mihomo_process is not None:
        print("[Proxy] 停止代理...")
        try:
            _mihomo_process.terminate()
            _mihomo_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _mihomo_process.kill()
            _mihomo_process.wait()
        _mihomo_process = None


def get_proxy_url() -> str:
    """获取 SOCKS5 代理 URL"""
    return f"socks5://127.0.0.1:{SOCKS_PORT}"


def get_proxies() -> Dict[str, str]:
    """获取 requests 库可用的代理字典"""
    proxy_url = get_proxy_url()
    return {
        "http": proxy_url,
        "https": proxy_url,
    }


# ==================== 上下文管理器 ====================

class ProxyContext:
    """代理上下文管理器 — 自动启动和停止代理"""

    def __init__(self):
        self._started = False

    def __enter__(self):
        self._started = start_proxy()
        if not self._started:
            raise RuntimeError("无法启动代理")
        return self

    def __exit__(self, *args):
        stop_proxy()


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=== 测试 Mihomo 代理 ===")
    try:
        with ProxyContext() as ctx:
            proxies = get_proxies()
            print(f"代理地址: {get_proxy_url()}")

            # 测试访问 Polymarket
            print("\n测试 Polymarket API...")
            resp = requests.get(
                "https://gamma-api.polymarket.com/events?tag=fed&limit=3",
                proxies=proxies,
                timeout=15,
            )
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text[:500]}")
            print("\n=== 代理测试成功! ===")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_proxy()