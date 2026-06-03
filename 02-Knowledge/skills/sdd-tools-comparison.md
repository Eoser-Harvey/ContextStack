# AI 协作开发三大工具对比：SuperPowers vs Spec Kit vs OpenSpec

> 调研日期：2026-06-02  
> 分类：`#AI` `#SDD` `#Skills` `#工具对比`

---

## 核心范式：SDD（Spec-Driven Development，规约驱动开发）

```
旧范式：我跟AI对话 → AI直接改代码
                       ↑  结果不可预测，debug成本高

新范式：我跟AI对话 → 先生成规约/计划 → AI根据规约改代码
                       ↑  这层"规约"就是中间代理
```

本质是**在用户和AI之间加一层"规约"作为中间代理**，把模糊需求先变成结构化计划，再驱动AI实现。

---

## 三大工具总览

| 维度 | **SuperPowers** | **Spec Kit** | **OpenSpec** |
|------|:---:|:---:|:---:|
| **仓库** | `obra/superpowers` | `github/spec-kit` | `Fission-AI/OpenSpec` |
| **Stars** | **217k** ⭐⭐⭐ | 108k ⭐⭐ | 52.6k ⭐ |
| **作者** | Jesse Vincent / Prime Radiant | GitHub 官方 | Fission-AI |
| **语言** | Shell + JS | Python | TypeScript |
| **定位** | Agentic Skills Framework | SDD 严格阶段工具 | 轻量 SDD 规约框架 |
| **核心理念** | "Skills 自动触发，Agent 自带超能力" | "规约即代码，阶段不可跳" | "Fluid not rigid，轻量即可" |

---

## 横向深度对比

### 1. 工作流

| 阶段 | SuperPowers | Spec Kit | OpenSpec |
|------|-------------|----------|----------|
| **需求澄清** | `brainstorming` Skill 自动触发，苏格拉底式提问 | `/speckit.specify` + `/speckit.clarify` 强制两步 | `/opsx:propose` 一步完成 |
| **方案设计** | `writing-plans` 拆解为 2~5 分钟粒度任务 | `/speckit.plan` 技术方案 → `/speckit.tasks` 任务列表 | `design.md` + `tasks.md` 自动生成 |
| **代码生成** | `subagent-driven-development` 每个任务独立子Agent | `/speckit.implement` 执行任务列表 | `/opsx:apply` 逐任务实现 |
| **质量保障** | TDD 强制 + 两阶段 Code Review | Checklist 机制 | 内嵌验证 |
| **完成归档** | `finishing-a-development-branch` | 无内置 | `/opsx:archive` |

### 2. 灵活性

| 维度 | SuperPowers | Spec Kit | OpenSpec |
|------|:---:|:---:|:---:|
| **阶段门控** | 自动触发，不强制跳过 | **刚性**：必须 clarify 才能 plan | 无门控，自由迭代 |
| **适用项目** | 新项目 + 老项目 | 偏 **Greenfield**（从零构建） | 偏 **Brownfield**（存量演进） |
| **团队规模** | 个人 → 企业 | **企业/团队**（有 constitution + presets） | 个人 → 中小企业 |
| **中文支持** | 官方英文 + 中文版 `superpowers-zh` | ❌ 英文为主 | ✅ 多语言（含中文） |
| **自定义** | 可写新 Skill + hook 脚本 | Presets + Extensions 体系 | Schema 定制 |

### 3. 安装与集成

| 集成 | SuperPowers | Spec Kit | OpenSpec |
|------|:---:|:---:|:---:|
| Claude Code | `✅ /plugin install` | ✅ | ✅ |
| Codex CLI | ✅ 插件市场 | ✅ `--integration codex` | ✅ |
| Codex App | ✅ 插件 | ✅ | ✅ |
| Gemini CLI | ✅ `extensions install` | ✅ | ✅ |
| Cursor | ✅ `@add-plugin` | ✅ | ✅ |
| GitHub Copilot CLI | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| CodeBuddy | 🟡 需适配（Skill 机制兼容） | 🟡 需适配 | 🟡 需适配 |

### 4. 与 ContextStack 现有体系的对应

| SuperPowers Skill | ContextStack 已有能力 | 对应方式 |
|-------------------|---------------------|---------|
| `brainstorming` | `@skill://brainstorming`（AR 规则已安装） | ✅ **完全对应** |
| `writing-plans` | `@skill://writing-plans` | ✅ **完全对应** |
| `systematic-debugging` | `@skill://systematic-debugging` | ✅ **完全对应** |
| `test-driven-development` | — | ❌ 未安装 |
| `subagent-driven-development` | Task 工具 | 🟡 部分对应 |
| `requesting-code-review` | — | ❌ 未安装 |
| `using-git-worktrees` | — | ❌ 未安装 |

> **结论**：ContextStack 已经拥有 SuperPowers 的 4/14 Skills，核心方法论一致。SuperPowers 的优势在于**自动触发**和**子Agent调度**，ContextStack 重在使用者**主动调用** Skills。

---

## 选择建议

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| **团队项目、需要积累规约** | Spec Kit | `constitution.md` + Presets 可沉淀团队经验 |
| **个人/小团队、快速迭代** | OpenSpec | 最轻量，无阶段门控，自由度高 |
| **希望 AI 全自动走完整流程** | **SuperPowers** | Skills 自动触发，不需要人记住命令 |
| **已有 ContextStack 体系** | 继续使用现有 Skills | 核心方法论已对齐，不必另学一套 |
| **当前 CodeBuddy 用户** | SuperPowers（适配后） | SuperPowers 的 Skill 机制与 CodeBuddy 最相似 |

---

## 三者关系图

```
SuperPowers (217k ★)
    ↓ 自动触发 14 个 Skills
    ↓ 覆盖全流程（brainstorming → code review）
    └── 子Agent调度 + TDD 强制执行

Spec Kit (108k ★)
    ↓ 阶段门控 6 个命令（/speckit.*）
    ↓ 产出规范化（spec/plan/tasks 各一文件）
    └── 企业级 Presets + Extensions 体系

OpenSpec (52.6k ★)
    ↓ 松散 3 步（propose/apply/archive）
    ↓ 最轻量（改一个建一个文件夹）
    └── "Fluid not rigid" 哲学
```

---

## 来源

| 工具 | GitHub | 官网 |
|------|--------|------|
| SuperPowers | https://github.com/obra/superpowers | — |
| SuperPowers 中文版 | https://github.com/jnMetaCode/superpowers-zh | — |
| Spec Kit | https://github.com/github/spec-kit | https://github.github.com/spec-kit/ |
| OpenSpec | https://github.com/Fission-AI/OpenSpec | https://openspec.dev/ |

---

## 关联文档

- [[index|Skills 总索引]] — 所有 Skills 一览
- [[codebuddy-builtin-skills-analysis|WorkBuddy Top 10 Skills 适配分析]]
- [[../system/trae-skills-reference|TRAE 热门 Skills 参考]]
- [[brainstorming/brainstorming使用说明]] — ContextStack 已安装的 brainstorming Skill
- [[writing-plans/writing-plans使用说明]] — ContextStack 已安装的 writing-plans Skill