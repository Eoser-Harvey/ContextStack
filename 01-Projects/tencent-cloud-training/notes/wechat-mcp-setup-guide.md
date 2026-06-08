# CodeBuddy MCP 微信连接配置指南

> 创建日期：2026-06-08  
> 目的：通过 MCP 让 CodeBuddy AI 直接收发微信消息，支持自动化定时推送（如每日 AI 新闻）

---

## 一、架构说明

```
CodeBuddy AI → MCP协议 → mcp-wechat-server → 微信 iLink Bot → 微信客户端
```

- **mcp-wechat-server**（v1.0.1, MIT）：将微信 iLink Bot 接口翻译成 MCP 标准工具
- **GitHub**：https://github.com/Howardzhangdqs/mcp-wechat-server
- **npm**：`mcp-wechat-server`

---

## 二、环境要求

| 依赖 | 状态 |
|------|------|
| Node.js v22.18.0 | ✅ 已安装 |
| npm 10.9.3 | ✅ 已安装 |
| CodeBuddy IDE | ✅ 已安装 |

> 原文档提到的 `bunx` 需要 Bun 运行时。由于 `mcp-wechat-server` 已在 npm 发布，改用 `npx` 替代，无需额外安装 Bun。

---

## 三、已完成的配置

### MCP 配置文件

**路径**：`C:\Users\h31280\.codebuddy\mcp.json`

```json
{
  "mcpServers": {
    "wechat": {
      "command": "npx",
      "args": ["-y", "mcp-wechat-server"]
    }
  }
}
```

> **下一步**：重启 CodeBuddy 使配置生效。

---

## 四、首次使用流程

### Step 1：扫码登录

重启 CodeBuddy 后，在对话中输入：

```
请帮我连接微信
```

AI 会调用 `login_qrcode` 工具生成登录二维码。有三种扫码方式：
1. 打开图片：`C:\Users\h31280\.mcp-wechat-server\qrcode.png`
2. 终端二维码：`C:\Users\h31280\.mcp-wechat-server\qrcode.txt`
3. URL 链接：复制到微信打开

> 提示：扫码后如果页面加载失败，切换到移动数据网络（关闭 WiFi）再试。

### Step 2：确认登录

AI 会调用 `check_qrcode_status` 检测扫码状态。确认登录后即可使用。

---

## 五、可用工具

| 工具 | 功能 | 示例 |
|------|------|------|
| `login_qrcode` | 生成登录二维码 | "帮我登录微信" |
| `check_qrcode_status` | 检查扫码状态 | 自动检测 |
| `logout` | 退出登录 | "退出微信" |
| `get_messages` | 拉取新消息（支持长轮询） | "看看有没有新消息" |
| `send_text_message` | 发送文本消息 | "给XXX发消息：今天AI新闻..." |
| `send_typing` | 显示/取消"正在输入" | 自动 |

---

## 六、自动化场景：每日 AI 新闻推送

### 方案设计

```
定时触发器（CodeBuddy 自动化）
  → AI 搜集当日 AI 新闻
    → 整理成结构化摘要
      → 调用 send_text_message 推送到指定微信联系人或群
```

### 设置步骤

1. **确保微信已连接**（扫码登录一次，凭证持久化在 `~/.mcp-wechat-server/`）
2. **创建 CodeBuddy 自动化任务**：每日固定时间执行
3. **编写 Prompt**：让 AI 搜集新闻 → 整理 → 发送

### 自动化 Prompt 示例

```
每天早上 9:00 执行以下任务：
1. 搜索最近 24 小时的 AI 领域重要新闻（国内+国际）
2. 整理成以下格式：
   🤖 今日 AI 早报 | {日期}
   ━━━━━━━━━━━━━━━━
   1. 【标题】一句话摘要
   2. ...
   ━━━━━━━━━━━━━━━━
   📌 今日关注：{重点推荐阅读的一条}
3. 调用微信 send_text_message 发送到我的微信
```

---

## 七、注意事项

### 安全性
- 登录凭证保存在 `C:\Users\h31280\.mcp-wechat-server\`（权限 600）
- 第三方开源项目（MIT 许可证），代码可审计
- 仅发送文本消息，不支持发送文件/图片

### 稳定性
- 重启 CodeBuddy 后登录状态保持（状态持久化）
- 如遇断连，重新执行 `login_qrcode` 即可

### 与已有 Bot 的关系
- `settings.json` 中已配置 `weixinClawBot`（iLink Bot），用于 WorkBuddy 渠道
- MCP 微信连接是独立通道，通过个人微信账号收发消息
- 两者互不冲突，可同时使用

---

## 八、故障排查

| 问题 | 解决方案 |
|------|----------|
| MCP 连接失败 | 确认 `npx -y mcp-wechat-server` 能正常运行 |
| 扫码后无法确认 | 切换移动数据网络（关闭 WiFi） |
| 登录态丢失 | 删除 `~/.mcp-wechat-server/` 重新登录 |
| 消息发送失败 | 检查是否已登录、联系人是否存在 |

---

## 相关文档

- [mcp-wechat-server GitHub](https://github.com/Howardzhangdqs/mcp-wechat-server)
- [知乎介绍文章](https://zhuanlan.zhihu.com/p/2019148415020315343)
- [CodeBuddy 官方文档](https://www.codebuddy.cn/docs/)
