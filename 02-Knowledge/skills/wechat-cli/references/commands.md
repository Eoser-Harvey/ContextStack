# WeChat CLI 命令详细参考

> 本文件为 `wechat-cli` 的渐进式披露补充文档。SKILL 主文件见 [[wechat-cli使用说明|../wechat-cli使用说明]]。
> 所有命令**默认输出 JSON**（AI 友好）；加 `--format text` 输出人类可读文本。

---

## init — 初始化

提取 SQLCipher 解密密钥并缓存到本地（`~/.wechat-cli/`）。**只需执行一次**。

```bash
wechat-cli init            # Windows
sudo wechat-cli init       # macOS / Linux（需完全磁盘访问权限）
```

- 扫描正在运行的微信进程内存提取密钥。
- macOS / Linux 必须 `sudo`；终端需开启「完全磁盘访问权限」。
- 若 `init` 失败，可能是微信版本不兼容或权限不足，先查仓库 Issues。

---

## sessions — 最近聊天列表

```bash
wechat-cli sessions --limit 20
wechat-cli sessions --limit 10 --format text
```

| 选项 | 说明 |
|------|------|
| `--limit N` | 返回最近 N 个会话 |
| `--format text` | 文本格式（默认 JSON） |

---

## history — 读聊天记录

```bash
wechat-cli history --limit 50 --type text
wechat-cli history --chat "群名" --limit 100 --start-time "2026-01-01" --end-time "2026-02-01"
```

| 选项 | 说明 |
|------|------|
| `--limit N` | 返回最近 N 条 |
| `--type` | 消息类型过滤（见下方类型表） |
| `--chat` | 指定会话 / 群（可重复） |
| `--start-time` / `--end-time` | 时间范围过滤（如 `2026-01-01`） |

---

## search — 搜索消息

```bash
wechat-cli search "关键词"
wechat-cli search "关键词" --chat "群名" --chat "张三"
wechat-cli search "关键词" --type file
```

| 选项 | 说明 |
|------|------|
| `--chat` | 限定搜索范围（可重复，多个群/人） |
| `--type` | 消息类型过滤 |

---

## contacts — 联系人查询

```bash
wechat-cli contacts --query "张"
wechat-cli contacts --query "张" --detail
```

| 选项 | 说明 |
|------|------|
| `--query` | 按名称/备注模糊查询 |
| `--detail` | 返回详细字段（微信号、备注、标签等） |

---

## members — 群成员

```bash
wechat-cli members --chat "群名"
wechat-cli members --chat "群名" --format text
```

| 选项 | 说明 |
|------|------|
| `--chat` | 指定群名 |
| `--format text` | 文本格式 |

---

## stats — 发送量 / 活跃度统计

```bash
wechat-cli stats --format text
wechat-cli stats --start-time "2026-01-01" --end-time "2026-12-31"
```

| 选项 | 说明 |
|------|------|
| `--format text` | 文本格式 |
| 时间范围选项 | 限定统计区间 |

---

## export — 导出对话

```bash
wechat-cli export --chat "群名" --format markdown --output chat.md
wechat-cli export --chat "张三" --format txt --output chat.txt
```

| 选项 | 说明 |
|------|------|
| `--format` | `markdown` 或 `txt` |
| `--output` | 输出文件路径 |
| `--chat` | 指定要导出的会话 / 群 |

---

## favorites — 收藏夹

```bash
wechat-cli favorites --type link
wechat-cli favorites --query "论文"
```

| 选项 | 说明 |
|------|------|
| `--type` | 收藏类型过滤 |
| `--query` | 关键词查询 |

---

## unread — 未读消息

```bash
wechat-cli unread
```

- 返回当前未读消息；已读状态保存在 `~/.wechat-cli/`。

---

## new-messages — 增量新消息

```bash
wechat-cli new-messages
```

- 返回自上次检查以来的新消息（增量）。
- 增量游标 / 状态保存在 `~/.wechat-cli/`，清缓存会重置。

---

## 消息类型（`--type` 取值）

`text`（文本）、`image`（图片）、`voice`（语音）、`video`（视频）、`sticker`（表情）、`location`（位置）、`link`（链接）、`file`（文件）、`call`（通话）、`system`（系统）。

---

## 输出字段提示（JSON）

不同命令字段略有差异，常见字段：

- `sessions`：`id` / `name` / `last_message` / `timestamp` / `unread_count`
- `history`：`sender` / `content` / `type` / `timestamp` / `is_self`
- `contacts`：`name` / `alias` / `remark` / `tags`
- `stats`：`chat` / `message_count` / `active_days`

> 实际字段以当前版本 `wechat-cli <cmd> --help` 为准。
