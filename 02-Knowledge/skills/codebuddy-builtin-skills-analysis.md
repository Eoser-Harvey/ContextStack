# CodeBuddy WorkBuddy 零成本 Top 10 Skills — 适配分析

> 来源：[CodeBuddy 官方文档](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10) · [博客园转载](https://www.cnblogs.com/itech/p/20099773)  
> 分析日期：2026-05-27  
> 分类：AI/技术

---

## 背景

WorkBuddy（Claw/Hermes 桌面智能体）精选了 10 个零成本 Skills，覆盖信息获取、文档处理、知识管理、系统增强四大维度。本文分析这些 Skills 在 CodeBuddy（AI 编程助手 IDE）中的可行性。

---

## 对照分析

| # | Skill | 分类 | WorkBuddy 安装名 | CodeBuddy 状态 | 说明 |
|---|-------|------|------------------|---------------|------|
| 1 | Agent Browser | 信息获取 | `agent-browser` | ✅ 已内置 | `@skill://agent-browser` 直接使用 |
| 2 | Web Search | 信息获取 | `web-search` | ✅ 原生工具 | CodeBuddy 已有 `web_search`/`web_fetch` 工具，无需额外 Skill |
| 3 | yt-dlp-downloader | 信息获取 | `yt-dlp-downloader` | 🟡 需安装 | 视频下载提取字幕，CodeBuddy 可通过命令行调用 |
| 4a | PDF | 文档处理 | `pdf` | ✅ 已内置 | `@skill://pdf` 直接使用 |
| 4b | DOCX | 文档处理 | `docx` | ✅ 已内置 | `@skill://docx` 直接使用 |
| 4c | PPTX | 文档处理 | `pptx` | ✅ 已内置 | `@skill://pptx` 直接使用 |
| 4d | XLSX | 文档处理 | `xlsx` | ✅ 已内置 | `@skill://xlsx` 直接使用 |
| 5 | Obsidian | 知识管理 | `obsidian` | 🟡 需安装 | 需创建 CodeBuddy 兼容版本 |
| 6 | Local Whisper | 知识管理 | `local-whisper` | 🔴 不适用 | CodeBuddy 无音频输入通道 |
| 7 | Self-improvement | 系统增强 | `self-improvement` | ✅ 已有替代 | ContextStack 已有 Memory 系统 + 工作台记忆 + always rules |
| 8 | Skill Scanner | 系统增强 | `skill-scanner` | 🟡 需安装 | 安装第三方 Skill 前安全审查 |
| 9 | Find Skills | 系统增强 | `find-skills` | ✅ 已内置 | `@skill://find-skills` 直接使用 |
| 10 | Frontend Design | 系统增强 | `frontend-design` | 🟡 需安装 | 前端页面美化，需创建 CodeBuddy 兼容版本 |

---

## 分类汇总

| 状态 | 数量 | Skills |
|------|------|--------|
| ✅ 已可用 | 6 | agent-browser、web-search(原生)、pdf、docx、pptx、xlsx、find-skills |
| ✅ 已有替代 | 2 | web-search（原生工具替代）、self-improvement（Memory系统替代） |
| 🟡 需安装 | 3 | yt-dlp-downloader、obsidian、frontend-design |
| 🔴 不适用 | 1 | local-whisper（无音频通道） |

---

## 已安装记录

| Skill | 安装位置 | 安装日期 | 版本 | 备注 |
|-------|----------|----------|------|------|
| obsidian | `~/.codebuddy/skills/obsidian/` | 2026-05-27 | v1.0.0 (steipete) | 用户级通用，依赖 `obsidian-cli` |
| — | — | — | — | — |

> 新增安装后请更新此表。

---

## 关联文档

- [[index|Skills 总索引]] — 所有 Skills（自定义 + 内置）一览
- [[find-skills/Skill|Find Skills 使用说明]] — Skill 发现与推荐
- [[../system/trae-skills-reference|TRAE 热门 Skills 参考]] — 外部参考
- [[../../../.codebuddy/skills/note-organizer/SKILL|note-organizer]] — 智能笔记整理 Skill
