"""测试微信MCP Server连接和推送"""
import json, os, subprocess, time, threading, sys

NODE = r"D:\nodejs\node.exe"
MCP_SERVER = r"C:\Users\harve\AppData\Roaming\npm\node_modules\mcp-wechat-server\dist\index.js"
TO = "o9cq80xcTVHnYCThXQ8NXo_dIpYs@im.wechat"

print(f"Node: {NODE} (exists: {os.path.exists(NODE)})")
print(f"MCP: {MCP_SERVER} (exists: {os.path.exists(MCP_SERVER)})")
print(f"Starting server...", flush=True)

server = subprocess.Popen(
    [NODE, MCP_SERVER],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env={**os.environ, "HOME": os.environ.get("USERPROFILE", "")}
)

# Read stderr in background
def read_stderr():
    while True:
        line = server.stderr.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").strip()
        if text:
            print(f"[STDERR] {text}", flush=True)

t = threading.Thread(target=read_stderr, daemon=True)
t.start()

time.sleep(2)
print("Server started, sending init...", flush=True)

def send(obj):
    data = (json.dumps(obj) + "\n").encode("utf-8")
    print(f"[SEND] {data[:200].decode()}", flush=True)
    server.stdin.write(data)
    server.stdin.flush()

def read(eid, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = server.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        text = line.decode("utf-8").strip()
        if not text:
            continue
        print(f"[RECV] {text[:300]}", flush=True)
        try:
            resp = json.loads(text)
            if resp.get("id") == eid:
                return resp
        except:
            pass
    print(f"[TIMEOUT] id={eid}", flush=True)
    return None

# Init
send({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0.0"}
    }
})

r = read(1, timeout=10)
if not r:
    print("Init failed!", flush=True)
    server.kill()
    sys.exit(1)

send({"jsonrpc": "2.0", "method": "notifications/initialized"})
print("Initialized!", flush=True)

# Get QR code
send({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "login_qrcode", "arguments": {}}
})

r2 = read(2, timeout=20)
if not r2:
    print("QR code failed!", flush=True)
    server.kill()
    sys.exit(1)

qr_url = ""
for c in r2.get("result", {}).get("content", []):
    txt = c.get("text", "")
    print(txt, flush=True)
    if "liteapp.weixin.qq.com" in txt:
        qr_url = txt.split("open it: ")[-1].strip()

print(f"\nQR URL: {qr_url}", flush=True)
print("Opening QR image...", flush=True)
os.system("start C:\\Users\\harve\\.mcp-wechat-server\\qrcode.png")

# Wait for scan
print("Waiting for scan (up to 120s)...", flush=True)
logged_in = False
for i in range(24):
    time.sleep(5)
    send({
        "jsonrpc": "2.0", "id": 10+i, "method": "tools/call",
        "params": {"name": "check_qrcode_status", "arguments": {}}
    })
    cr = read(10+i, timeout=8)
    if cr:
        for c in cr.get("result", {}).get("content", []):
            ct = c.get("text", "")
            print(f"[{i}] {ct}", flush=True)
            if "success" in ct.lower() or "logged in" in ct.lower():
                logged_in = True
                break
    if logged_in:
        break

if not logged_in:
    print("Login timeout!", flush=True)
    server.kill()
    sys.exit(1)

print("Login success! Sending test message...", flush=True)
time.sleep(1)

send({
    "jsonrpc": "2.0", "id": 50, "method": "tools/call",
    "params": {
        "name": "send_text_message",
        "arguments": {"to": TO, "text": "X推文推送测试成功! 链路已打通!"}
    }
})

sr = read(50, timeout=15)
if sr:
    result = sr.get("result", {})
    if result.get("isError"):
        for c in result.get("content", []):
            print(f"[ERROR] {c.get('text', '')}", flush=True)
    else:
        print("Message sent successfully!", flush=True)
else:
    print("Send timeout!", flush=True)

server.kill()
print("Done.", flush=True)
