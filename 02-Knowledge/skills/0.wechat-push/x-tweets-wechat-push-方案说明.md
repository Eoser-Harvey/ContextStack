# X推文微信推送 — 方案演进与最终架构

## 需求
- 获取指定X用户（马斯克、CZ、特朗普）推文
- 原文 + 翻译 + 四维度建议（投资/职业/生活/家庭）
- 推送到用户微信

## 方案演进

### 方案1: WeChat MCP（IDE集成）❌ 不稳定
- 通过 IDE 内置 MCP 调用 `send_text_message`
- **问题**: bot 会话过期后断开，重新扫码会换 botId，需用户先发消息激活
- **根因**: WeChat MCP bot 只能回复不能主动发消息；IDE session 重启后 botId 变化

### 方案2: Server酱 ❌ 收费
- HTTP POST → sctapi.ftqq.com → 微信
- 免费版有限制，Turbo版收费

### 方案3: Bun + JSON-RPC 直连 ✅ 最终方案
- **调用链**: `Python subprocess → Bun → mcp-wechat-server → JSON-RPC 2.0 → 微信`
- **核心优势**:
  - 每次推送独立进程，不依赖 IDE session
  - 不依赖外部 wechat_sender.js，纯 Python 实现
  - 每次进程启动-发送-退出，无状态，天然稳定
  - bot 会话在进程内部自动管理

## 最终架构

```
run_auto.py (主入口)
  ├── fetcher_web.py  → web_search/web_fetch 实时抓取推文
  ├── translator.py   → Google 翻译
  ├── analyzer.py     → 个人画像四维度分析
  └── push_wechat.py  → 消息构建 + Bun JSON-RPC 推送
       └── send_one_wechat()
            ├── subprocess.Popen([bun, mcp-wechat-server/index.ts])
            ├── JSON-RPC 2.0: initialize → notifications/initialized
            ├── JSON-RPC 2.0: tools/call(send_text_message)
            └── process.kill() → 退出
```

## JSON-RPC 2.0 协议流程
1. Python 启动 `bun mcp-wechat-server/src/index.ts` 子进程
2. 发送 `initialize` 请求 (id=1)
3. 收到响应后发送 `notifications/initialized`
4. 发送 `tools/call` 请求 (id=2)，参数 `send_text_message {to, text}`
5. 收到响应 → kill 进程 → 完成

## 关键路径
| 组件 | 路径 |
|------|------|
| Bun | `C:\Users\h31280\.bun\bin\bun.exe` |
| MCP Server | `C:\Users\h31280\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts` |
| 推送模块 | `automation-20260616181324\x_tweets\push_wechat.py` |
| 目标用户 | `o9cq80xcTVHnYCThXQ8NXo_dIpYs@im.wechat` |

## 注意事项
- 消息间隔 2 秒，防止微信限流
- 超时 20 秒
- stderr 静默处理（Bun 日志）
- 每次调用独立进程，不需要预登录或保持会话
