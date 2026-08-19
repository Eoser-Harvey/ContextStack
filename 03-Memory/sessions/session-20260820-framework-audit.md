# ContextStack 框架结构审计 — 2026-08-20

> 全量学习审计：检查四层架构规则与实际执行的一致性，识别索引滞后与设计缺口。
> 上一次审计：[framework-audit-2026-06-10](./framework-audit-2026-06-10.md)

---

## 一、审计方法

- 完整读取 L1（GLOBAL-RULES.md v3.2→v3.3）、L4 索引（MEMORY.md）、FRAMEWORK-README.md、TODO-DASHBOARD.md
- 并行 list_dir 全部一级目录与关键二级目录
- 对比规则声明 vs 实际文件状态

---

## 二、识别的问题

### 🔴 严重：索引文件全面滞后于实际状态（已在本次审计中修复）

| 文件 | 原最后更新 | 实际差异 | 修复 |
|---|---|---|---|
| `01-Projects/index.md` | 2026-07-08 | 只列 6 个主要项目，实际 10 个项目子目录（漏 automated-task / personal-website / personal-agents / topics） | ✅ 2026-08-20 同步 |
| `02-Knowledge/index.md` | 2026-06-19 | inbox 统计 40 条，实际 60+ .md + role-model 408 文件；skills 列 13 个，实际 20 个子目录 | ✅ 2026-08-20 同步 |
| `03-Memory/sessions/recent-sessions.md` | 2026-05-28 | 3 个月未更新，违反"每次对话后更新"规则 | ✅ 2026-08-20 补本次会话 |
| `FRAMEWORK-README.md` | 2026-07-22 (v3.0) | GLOBAL-RULES 已 v3.2，版本号不同步 | ✅ 2026-08-20 同步至 v3.3 |

**根因**：框架定义了"新建文件自动加 index.md"（铁律第3条），但**没有定义 index.md 的定期回顾机制**——index.md 一旦创建就无人维护。

**修复方案（已写入 GLOBAL-RULES.md v3.3 自检清单）**：AI 会话开始自检第 6 项「索引与文档同步」明确要求新建/重命名/删除文件时必须同步更新对应 index.md。建议另加月度 index 一致性自检。

---

### 🟠 中等：.gitignore `*.html` 全局忽略导致新增 .html 无法入库（已修复）

**问题**：
- `.gitignore` 第 92 行原为 `*.html` 全局忽略
- 框架内 git 实际跟踪了 90+ 个 .html 文件（主要在 `02-Knowledge/career-development/Learning notes/`，是 Evernote 导出的工作笔记，早于 .gitignore 规则）
- 风险：未来在 family-hub 健康分析、bazi-ziwei 排盘海报、personal-website 等场景**新增** .html 时会被 .gitignore 意外忽略，commit 时静默丢失

**修复**：删除全局 `*.html`，改为白名单制——只忽略明确不需要跟踪的特定路径：
- `01-Projects/automated-task/**/*.html`
- `02-Knowledge/skills/*/cache/**/*.html`
- `**/profile_archive/**/*.html`
- `**/.cache/**/*.html`

**验证**：git ls-files 显示 90+ 个 .html 仍被跟踪（已纳入版本控制，.gitignore 不影响），未来新增 .html 默认入库。

---

### 🟠 中等：04-Templates/project/ 缺 PROJECT-RULES.md 模板（未修复，待决策）

**问题**：
- `04-Templates/project/` 只有 5 个标准文件（WORKSPACE / STATE / ACTIONS / CONTEXT / REFERENCES）
- 缺 PROJECT-RULES.md 模板
- 根目录单独有 `04-Templates/project-rules-template.md`，位置不一致

**影响**：新建项目时从 `project/` 复制 5 个文件后，容易遗漏 PROJECT-RULES（与 framework-audit-2026-06-10 中 wechat-radar 零标准文件问题同根因——模板不完整）。

**待决策**：用户未授权重命名/移动文件。建议方案：把 `project-rules-template.md` 移到 `04-Templates/project/PROJECT-RULES.md`，让 `project/` 目录成为"一键复制即得完整六文件"入口。

---

### 🟠 中等：inbox 未归档内容严重堆积（未修复，待用户决策）

**实际状态**（2026-08-20）：
- `02-Knowledge/inbox/` 根目录 60+ 个 .md 文件（超过框架 30 条阈值）
- `inbox/role-model/` 子目录 408 文件（277 PDF + 94 jpg + 28 md + 5 png + 3 docx + 1 json）
- framework-audit-2026-06-10 当时记录"14 条未归档"，3 个月膨胀到 60+ 条 + 408 媒体文件

**疑似违规**：role-model 子目录 277 PDF 大概率是从外部源（如老薛课程 PDF）误拷贝进框架，违反"外部交付物写外部路径，绝不框架内建副本"规则。

**待决策**：需用户审视后决定：
1. inbox 60+ .md 逐条判断 → 归档到 archive/ 或正式知识分区，或删除（仅建议，不执行）
2. role-model 408 文件是否移回外部路径（**需用户明确授权才能执行移动**）

---

### 🟡 轻微：03-Memory 子目录内容稀疏（保持现状）

- `03-Memory/personal/` 只有 index.md（personal/todo.md 已删除，合理）
- `03-Memory/projects/` 只有 index.md（项目记忆都散落在各项目 STATE.md，未归档）
- `03-Memory/sessions/` 1 次归档 + 模板 + recent-sessions（本次补第 2 次）

**建议**：明确 03-Memory/projects/ 定位为"项目完结后归档总结"，活跃项目记忆存放在项目 STATE.md。在 03-Memory/index.md 中明确写出此定位，避免未来混淆。

---

### 🟡 轻微：5 个可能僵尸的项目状态不清

embedded-ai-learning / network-device-debug / tencent-cloud-training / btc-temperature-gauge / wechat-radar 状态需明确"完成/暂停/放弃"，避免框架隐性债务。待用户决策。

---

## 三、本次审计修复清单

| 优先级 | 行动 | 状态 |
|:--:|------|:--:|
| P0 | 4 个 index.md 文件同步实际结构 | ✅ 已修复 |
| P0 | .gitignore `*.html` 全局忽略改为白名单 | ✅ 已修复 |
| P0 | GLOBAL-RULES.md 新增 AI 行为约束自检清单（v3.3） | ✅ 已修复 |
| P0 | 创建本审计文件沉淀到 03-Memory/knowledge/ | ✅ 已创建 |
| P0 | 03-Memory/sessions/recent-sessions.md 补本次会话 | ✅ 已修复 |
| P0 | FRAMEWORK-README.md 版本号同步至 v3.3 | ✅ 已修复 |
| P1 | 04-Templates/project/ 补 PROJECT-RULES.md 模板 | ⏳ 待用户决策 |
| P1 | inbox 60+ 文件归档清理 | ⏳ 待用户决策 |
| P1 | role-model 408 文件审视 | ⏳ 待用户决策 |
| P2 | 5 个僵尸项目状态明确 | ⏳ 待用户决策 |
| P2 | Skills 目录命名统一（拼音/连字符） | ⏳ 待用户决策 |
| P2 | 增加月度 index 一致性自检自动化脚本 | ⏳ 建议中 |

---

## 四、设计层级的肯定（无需修复）

- **铁律5「保持批判性立场」** 是稀缺设计——绝大多数 AI 框架默认讨好型，此框架把它升级为等同安全红线且明确"先讲用户自身可改点再谈外部归因"
- **费曼复述纪律 + 80 分考核机制**（2026-07-28/29）堵住了"收藏式学习"漏洞
- **TODO-DASHBOARD 双向同步**（2026-08-11）解决了 personal/todo.md 与项目 ACTIONS.md 分裂
- **记忆系统三层分工**（2026-07-31，.workbuddy vs 03-Memory vs MEMORY.md）清晰解决了"换 AI 工具时记忆是否带走"痛点
- **文件操作红线演进** 4 次违规教训层层加码，最终形成"未经明确授权不执行任何写盘/移动/删除"

---

## 五、新增机制：AI 行为约束自检清单（v3.3）

已写入 GLOBAL-RULES.md。每次会话开始 AI 主动过 6 项自检：
1. 铁律5 批判性立场
2. 文件操作红线
3. 修改用户文件必须先讨论
4. 临时文件清理
5. 学习讨论收尾纪律
6. 索引与文档同步

**判据**：6 项全部"是/已准备"= 通过；任何一项"不确定"= 立即重读对应铁律。
**输出规则**：通过后内部确认即可，无需每次回复输出（避免噪音）；用户询问时必须如实报告。

---

## 六、CodeBuddy 记忆库 vs 03-Memory 同步问题（本次识别）

**发现**：本次审计结论已通过 `update_memory` 工具同步到 CodeBuddy 记忆库（ID 31759151 / 33785241），但**违反了 `framework-maintenance.md` 中"`.workbuddy/memory/` 中有价值的内容必须同步沉淀到 03-Memory/"规则**——CodeBuddy 记忆库本质等同 `.workbuddy/memory/`（AI 工具绑定记忆）。

**修复**：本文件即沉淀产物。今后每次 `update_memory` 后，有价值的部分应同步写到 03-Memory/knowledge/ 对应文件。

---

## 相关
- [[../index|03-Memory 索引]]
- [[../knowledge/framework-audit-2026-06-10|上次审计 2026-06-10]]
- [[../knowledge/framework-maintenance|框架维护经验]]
- [[../../GLOBAL-RULES|全局规则]]
- [[../../MEMORY|MEMORY.md 索引]]
- [[../../FRAMEWORK-README|框架总览]]

---

**审计人**: ContextStack AI 协作助手
**审计日期**: 2026-08-20
**下次审计建议**: 2026-09-20（建议月度频次）
