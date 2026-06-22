# 飞书 Bot 推送方案 — 标准化对接文档

> 适用场景: 任何需要 Python 自动化推送消息到飞书群的项目
> 核心优势: 不依赖 lark-cli，直接调用飞书 Open API，Bot 身份永久有效

---

## 一、方案对比

| 方案 | 依赖 | 授权方式 | 稳定性 | 适用环境 |
|------|------|----------|--------|----------|
| **lark-cli user 身份** | lark-cli + node.js | 用户 OAuth，需定期授权 | 中（token会过期） | 本地开发 |
| **lark-cli bot 身份** | lark-cli + node.js | appId+appSecret | 高 | 本地开发 |
| **直接调用 Open API** | 仅 Python + requests | appId+appSecret | **最高** | **任何环境** |

**推荐方案: 直接调用飞书 Open API** — 绕过 lark-cli 的所有限制，纯 HTTP 调用。

---

## 二、前置条件

1. **飞书开发者后台创建应用**
   - 访问: https://open.feishu.cn/app
   - 创建企业自建应用
   - 记录 `App ID` 和 `App Secret`

2. **开通权限**
   - 权限管理 → 添加权限 → 搜索 `im:message:send_as_bot` → 开通

3. **将 Bot 添加到群聊**
   - 进入目标飞书群 → 群设置 → 添加机器人 → 选择你的应用
   - 记录群聊的 `chat_id`（可在开发者工具中查询，或用 Bot 的 webhook 测试获取）

---

## 三、核心代码 (push_lark.py)

```python
"""
飞书群推送模块 — 直接调用飞书 Open API (Bot 身份)
调用链: Python → HTTP POST → 飞书 Open API → 飞书群
"""
import json
import time
import requests

# ====== 配置区 ======
LARK_APP_ID = "cli_xxxxxxxxxxxxxxxx"      # 从飞书开发者后台获取
LARK_APP_SECRET = "xxxxxxxxxxxxxxxx"      # 从飞书开发者后台获取
LARK_CHAT_ID = "oc_xxxxxxxxxxxxxxxx"    # 目标群聊ID

LARK_API_BASE = "https://open.feishu.cn/open-apis"
TOKEN_URL = f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal"
MESSAGE_URL = f"{LARK_API_BASE}/im/v1/messages"

# token 缓存（内存级，进程内复用）
_token_cache = {"token": "", "expires_at": 0}


def get_tenant_access_token():
    """获取 tenant_access_token (自动缓存，提前5分钟刷新)"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    payload = {"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    resp = requests.post(TOKEN_URL, json=payload, timeout=10)
    data = resp.json()
    
    if data.get("code") == 0:
        token = data["tenant_access_token"]
        expire = data.get("expire", 7200)
        _token_cache["token"] = token
        _token_cache["expires_at"] = now + expire - 300  # 提前5分钟刷新
        return token
    else:
        raise RuntimeError(f"获取token失败: {data.get('msg')}")


def send_text_to_lark(text, chat_id=LARK_CHAT_ID):
    """发送纯文本消息到飞书群 (Bot 身份)"""
    token = get_tenant_access_token()
    
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
    
    resp = requests.post(
        MESSAGE_URL,
        headers=headers,
        json=payload,
        params=params,
        timeout=20
    )
    data = resp.json()
    
    if data.get("code") == 0:
        return True, data.get("data", {}).get("message_id", "")
    else:
        return False, f"code={data.get('code')}, msg={data.get('msg')}"


# ====== 使用示例 ======
if __name__ == "__main__":
    success, msg_id = send_text_to_lark("Hello from Bot!\n第二行\n第三行")
    print(f"Success: {success}, msg_id: {msg_id}")
```

---

## 四、关键 API 说明

### 4.1 获取 tenant_access_token

```
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Content-Type: application/json

Body:
{
  "app_id": "cli_xxx",
  "app_secret": "xxx"
}

Response:
{
  "code": 0,
  "msg": "ok",
  "tenant_access_token": "t-xxx",
  "expire": 7200
}
```

- `tenant_access_token` 有效期 2 小时（7200秒）
- **必须缓存**，不要每次发消息都重新获取
- 建议提前 5 分钟刷新缓存

### 4.2 发送文本消息

```
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id
Authorization: Bearer {tenant_access_token}
Content-Type: application/json

Body:
{
  "receive_id": "oc_xxx",
  "msg_type": "text",
  "content": "{\"text\":\"消息内容\\n多行支持\"}"
}
```

- `content` 字段是 JSON 字符串，外层需 `json.dumps()` 序列化
- 支持 `\n` 换行符
- `msg_type` 可选: `text` / `post` / `image` / `interactive` 等

---

## 五、常见问题

### Q1: 发送失败，code=99991663
**原因**: Bot 不在群聊中，或没有 `im:message:send_as_bot` 权限
**解决**: 
1. 在飞书开发者后台开通 `im:message:send_as_bot` 权限
2. 将 Bot 添加到目标群聊

### Q2: 发送失败，code=99991661
**原因**: 权限未开通或 token 无效
**解决**: 检查 `tenant_access_token` 是否正确获取，权限是否已开通并发布

### Q3: 为什么不用 lark-cli？
**原因**: 
- lark-cli 在 TRAE 等托管环境中不支持 `config init` 配置 bot 凭证
- lark-cli 的 `--as bot` 需要预先配置 appId/appSecret，无法通过命令行参数传入
- 直接调用 Open API 更轻量、更可控、无外部依赖

### Q4: 多行文本怎么传？
**解决**: `content` 字段传 `json.dumps({"text": "line1\nline2"})`，飞书 API 原生支持 `\n` 换行。

---

## 六、与其他 AI 对接说明

### 6.1 对接时需要提供的信息

| 信息 | 说明 | 获取方式 |
|------|------|----------|
| `App ID` | Bot 应用标识 | 飞书开发者后台 → 应用详情 |
| `App Secret` | Bot 应用密钥 | 飞书开发者后台 → 凭证与基础信息 |
| `chat_id` | 目标群聊ID | 开发者工具查询，或让 Bot 加入群后通过 API 查询 |

### 6.2 最小可运行代码

```python
import json, requests

APP_ID = "cli_xxx"
APP_SECRET = "xxx"
CHAT_ID = "oc_xxx"

def send(text):
    # 1. 获取 token
    r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                      json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    token = r.json()["tenant_access_token"]
    
    # 2. 发送消息
    r = requests.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                      headers={"Authorization": f"Bearer {token}"},
                      json={"receive_id": CHAT_ID, "msg_type": "text",
                            "content": json.dumps({"text": text})}, timeout=20)
    return r.json()["code"] == 0

# 使用
send("Hello from AI Bot!")
```

---

## 七、本项目的完整调用链

```
TRAE 定时任务 (每小时)
    ↓
python run_auto.py
    ↓
build_tweets_from_fetch()  ← fetcher_web.py (硬编码推文数据)
    ↓
translator.translate_tweets()  ← translator.py (读 translation_cache.json)
    ↓
analyze_tweets()  ← analyzer.py (基于 config.yaml profile 生成四维度建议)
    ↓
push_to_lark()  ← push_lark.py (直接调用飞书 Open API)
    ↓
HTTP POST → 飞书 Open API → 飞书群 (CodeBuddy推文推送①)
```

---

## 八、文件位置

- 项目目录: `E:\ProjectGroup\AI\ContextStack\02-Knowledge\skills\1.feishu-push\`
- 核心推送模块: `push_lark.py`
- 主控脚本: `run_auto.py`
- 配置文件: `config.yaml`
- 翻译缓存: `translation_cache.json`
- 历史记录: `tweet_history.json`

---

> 最后更新: 2026-06-20
> 作者: AI Agent (TRAE)
