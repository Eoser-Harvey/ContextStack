# Social Auto Upload — 多平台社交媒体自动上传工具

> 来源: GitHub [dreammis/social-auto-upload](https://github.com/dreammis/social-auto-upload)  
> Stars: 9k+ | 社群: 2000+ 人  
> 收集日期: 2026-05-30  
> 分类: AI/技术 / 自媒体工具 / 自动化

---

## 项目简介

**social-auto-upload** 是一个自动化工具，帮助内容创作者将视频/图文一键发布到多个国内外主流社交媒体平台。

**核心理念**: AI 虽然强大，但上传是高频、重复、无聊的工作，应该交给脚本和程序执行，而不是每次都让 Agent 重新解析网页。

---

## 支持平台与功能

| 平台 | 登录 | 视频上传 | 图文上传 | 定时发布 | CLI | Skill | 备注 |
|------|------|----------|----------|----------|-----|-------|------|
| **抖音** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 当前主线重构最完整 |
| **Bilibili** | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | 自动准备 `biliup` |
| **小红书** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 浏览器自动化 |
| **快手** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 浏览器自动化 |
| **视频号** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | `tencent_uploader` |
| **百家号** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | 浏览器自动化 |
| **TikTok** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | Chrome 版实现 |

---

## 核心特性

### 1. CLI 统一入口 (`sau`)

```bash
# 抖音示例
sau douyin login --account <account_name>
sau douyin check --account <account_name>
sau douyin upload-video --account <account_name> --file videos/demo.mp4 --title "标题" --desc "简介"
sau douyin upload-note --account <account_name> --images 1.png 2.png --title "图文标题" --note "正文"

# 快手、小红书、Bilibili 同理
```

- `account_name` 对应一个账号文件，支持多账号
- 浏览器平台统一约定：视频用 `title+desc+tags`，图文用 `title+note+tags`

### 2. AI Agent 集成

支持直接交给 AI Agent 使用：
- OpenClaw
- Codex / Claude Code / `cc`
- Qwen Code

**使用方法**: 把仓库发给 Agent + 附上一份 [Agent Bootstrap Prompt](https://github.com/dreammis/social-auto-upload/blob/main/docs/agent-bootstrap.md)

### 3. Skill 化

已提供 Skill 文档，支持在 Agent 中直接调用：
- [Douyin Upload Skill](https://github.com/dreammis/social-auto-upload/blob/main/skills/douyin-upload/SKILL.md)
- [Kuaishou Upload Skill](https://github.com/dreammis/social-auto-upload/blob/main/skills/kuaishou-upload/SKILL.md)
- [Xiaohongshu Upload Skill](https://github.com/dreammis/social-auto-upload/blob/main/skills/xiaohongshu-upload/SKILL.md)
- [Bilibili Upload Skill](https://github.com/dreammis/social-auto-upload/blob/main/skills/bilibili-upload/SKILL.md)

---

## 技术架构

| 组件 | 说明 |
|------|------|
| `uploader/` | 各平台上传器实现 |
| `sau_backend.py` | 后端服务 |
| `sau_frontend/` | 前端界面 (Vue) |
| `sau_cli.py` | CLI 入口 |
| `skills/` | Agent Skill 定义 |
| `examples/` | 使用示例 |

**技术栈**: Python 69.6% | Vue 24.8% | JavaScript 2.3%

---

## 重构计划（进行中）

作者 2026.03.24 宣布进入密集更新阶段，重点：

1. **更隐蔽稳定的自动化** — 降低平台检测风险
2. **补齐图文能力** — 逐步 CLI 化、Skill 化
3. **上架更多 Skill 平台** — 打通 AI 自媒体最后一道关
4. **更换 `patchright` 驱动** — 提升兼容性与隐蔽性
5. **主线优先无头模式** — 适合 CLI、服务端、自动任务

> Web 端代码保留但已不是主线，不保证可直接运行

---

## 使用建议

### 普通用户
- 参考 [安装说明](https://github.com/dreammis/social-auto-upload/blob/main/docs/install.md)
- 使用 `sau` CLI 命令操作

### AI Agent 用户
- 直接把仓库发给 Agent
- 附上 [Agent Bootstrap Prompt](https://github.com/dreammis/social-auto-upload/blob/main/docs/agent-bootstrap.md)
- Agent 会自动完成安装、配置、验证

---

## 与 ContextStack 的关联

**潜在使用场景**:
- 结合 `ai-agent-repos-collection.md` 中的视频/自媒体工具
- 与 `ruflo-agent-orchestration-research.md` 的多 Agent 编排能力结合
- 自动化内容发布流程，减少重复劳动

**建议关注**:
- Skill 化进展 — 可能直接集成到个人工作流
- 无头模式 — 适合服务器端自动化
- 多账号管理 — 适合矩阵运营

---

**最后更新**: 2026-05-30
