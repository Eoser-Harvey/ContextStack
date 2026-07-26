---
title: WeChat CLI 使用说明（本地微信数据查询）
name: wechat-cli
description: 当用户要"读取/查询/导出/分析本地微信聊天记录、联系人、群成员、未读消息、收藏"，或提到"wechat-cli"、"微信命令行"、"微信聊天记录导出"、"本地微信数据"、"SQLCipher 解密微信"，或想在 AI Agent / Claude Code / MCP 中接入微信数据时使用。专为 AI Agent 设计，默认输出 JSON。
source: "https://github.com/huohuoer/wechat-cli"
tags:
  - wechat
  - local-data
  - agent-tool
  - json
  - sqlcipher
created: 2026-07-26
---

# WeChat CLI 使用说明

> **项目来源**：[github.com/huohuoer/wechat-cli](https://github.com/huohuoer/wechat-cli)（Apache 2.0，基于 `wechat-decrypt` 构建）
> **收录日期**：2026-07-26

## 一句话说明

wechat-cli 是一个**本地运行**的命令行工具，读取本机微信的加密数据库（SQLCipher），让你在终端直接查询聊天记录、联系人、群成员、统计、收藏等。所有命令**默认输出 JSON**，专为 LLM / AI Agent 调用设计；也可加 `--format text` 给人类阅读。

## 核心特征（为什么适合 AI Agent）

- **零配置**：`npm install -g` 即可，无云端、无账号。
- **完全本地**：SQLCipher 实时解密，数据不出本机，只读不写。
- **AI 优先**：默认 JSON 输出，可直接喂给 Claude / 任意 Agent。
- **富数据**：支持聊天记录、搜索、联系人、群成员、活跃度统计、收藏、未读/增量消息。
- **多格式导出**：Markdown / 纯文本。

## 平台支持

- macOS（Apple Silicon / Intel）、Windows(实际测试目前不支持)、Linux。
- 系统要求示例（README 原文）：macOS 需微信客户端运行；具体微信版本上限以仓库最新说明为准。

## 安装

```bash
# 方式一：npm 全局安装（推荐）
npm install -g @canghe_ai/wechat-cli

# 方式二：pip
pip install wechat-cli

# 方式三：从源码
git clone https://github.com/huohuoer/wechat-cli
cd wechat-cli && npm install && npm link
```

验证：`wechat-cli --help`

## 初始化（关键步骤）

```bash
wechat-cli init
```

- **作用**：扫描正在运行的微信进程内存，提取 SQLCipher 解密密钥并缓存到本地（状态存于 `~/.wechat-cli/`）。
- **macOS / Linux 需要 `sudo`**：`sudo wechat-cli init`，且终端需具备「完全磁盘访问权限」。
- 初始化只需做一次；后续命令按需解密。

## 命令总览（11 个）

> 详细参数、示例与字段说明见 [[wechat-cli-commands|命令详细参考]]（`references/commands.md`）。

| 命令 | 用途 | 常用选项 |
|------|------|----------|
| `init` | 初始化，提取 SQLCipher 密钥 | — |
| `sessions` | 最近聊天列表 | `--limit`, `--format text` |
| `history` | 读聊天记录 | `--limit`, `--type`, `--start-time`, `--end-time` |
| `search` | 搜索消息 | `--chat`（可重复）, `--type` |
| `contacts` | 联系人查询 | `--query`, `--detail` |
| `members` | 群成员 | `--format text` |
| `stats` | 发送量 / 活跃度统计 | `--format text`, 时间范围 |
| `export` | 导出对话 | `--format markdown\|txt`, `--output` |
| `favorites` | 收藏夹 | `--type`, `--query` |
| `unread` | 未读消息 | — |
| `new-messages` | 增量新消息（状态存 `~/.wechat-cli/`） | — |

**消息类型过滤**（`--type` 取值）：`text, image, voice, video, sticker, location, link, file, call, system`。

## 典型工作流

1. **首次使用**：`sudo wechat-cli init`（macOS/Linux）或 `wechat-cli init`（Windows）。
2. **确认能连上数据**：`wechat-cli sessions --limit 10` 看最近会话。
3. **读取某段聊天**：`wechat-cli history --limit 50 --type text`（可加时间范围）。
4. **搜索关键词**：`wechat-cli search "关键词" --chat "群名"`。
5. **导出存档**：`wechat-cli export --format markdown --output chat.md`。
6. **AI 分析**：默认 JSON 直接喂给 Agent，或 `--format text` 给人看。

## AI Agent 集成（CLAUDE.md / MCP）

把下面这段写进项目的 `CLAUDE.md`，让 Claude / Agent 知道可用此工具：

```markdown
## 本地微信数据查询（wechat-cli）

本机已安装 wechat-cli（本地只读，SQLCipher 解密）。需要查询微信聊天记录、
联系人、群成员、统计、收藏时，直接调用：

- 最近会话：`wechat-cli sessions --limit 20`
- 聊天记录：`wechat-cli history --limit 50 --type text`
- 搜索：`wechat-cli search "关键词"`
- 群成员：`wechat-cli members`
- 导出：`wechat-cli export --format markdown --output out.md`

所有命令默认输出 JSON，可直接解析。涉及 sudo 的初始化操作需用户授权后执行。
```

也可封装为 MCP / OpenClaw 工具供 Agent 调用。

## 关键坑点（Gotchas）⭐

- **`init` 必须提权**：macOS / Linux 下 `wechat-cli init` 需要 `sudo`，且终端要开启「完全磁盘访问权限」，否则读不到进程内存里的密钥。Windows 一般直接 `init` 即可。
- **macOS 可能需重签名**：部分版本需要对 WeChat.app 做 `codesign --force --sign - --entitlements ...` 添加 `get-task-allow` 权限才能读取内存。**注意：这会干扰微信自动更新机制**，且可能触发 Gatekeeper 警告——非必要不操作，且需用户明确授权。
- **默认输出是 JSON，不是文本**：Agent 解析用默认 JSON；给人看务必加 `--format text`，否则输出一堆 JSON 难以阅读。
- **增量状态存本地**：`unread` / `new-messages` 的已读状态保存在 `~/.wechat-cli/`，换机器或清缓存会重置。
- **只解密本地数据库**：必须先在本机登录并运行过微信、且有本地数据文件；纯远程 / 未登录账号查不到。
- **只读不写**：工具只读，不会发消息、不会改聊天记录，也不上传云端——这与"微信机器人/自动回复"类工具完全不同。
- **版本兼容性**：微信客户端版本更新可能改数据库结构或密钥提取方式，若 `init` 失败先查仓库 Issues 是否已有对应版本修复。

## 参考

- 命令详细参考（参数 / 示例 / 输出字段）：[[wechat-cli-commands|references/commands.md]]
- 项目仓库：https://github.com/huohuoer/wechat-cli
- 相关：[[../0.trae-wechat-push/README|X推文推送系统]]、[[../web-pack/index|Web-Pack 素材采集]]

---

**标签**：`#wechat` `#local-data` `#agent-tool` `#json` `#sqlcipher`
