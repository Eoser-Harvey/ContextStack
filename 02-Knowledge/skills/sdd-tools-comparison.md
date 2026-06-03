# AI 协作开发三大工具对比：SuperPowers vs Spec Kit vs OpenSpec

> 调研日期：2026-06-02（基于社区总结二次校对 2026-06-09）  
> 分类：`#AI` `#SDD` `#Skills` `#工具对比`  
> 关键洞察：**三者不是竞品，是两层叠用关系**

---

## 重新理解 SDD：两层架构

旧范式：
```
我跟AI对话 → AI直接改代码
```

SDD 新范式是两层：

```
┌─────────────────────────────────────────────┐
│  第1层：需求 → Spec（"要做什么"）              │
│  → OpenSpec / Spec-kit 负责                   │
├─────────────────────────────────────────────┤
│  第2层：Spec → 代码（"怎么做稳"）              │
│  → SuperPowers / ECC 负责                     │
└─────────────────────────────────────────────┘
```

**核心认知**：SuperPowers 不解决"怎么写 spec"，只解决 **"spec → 代码这段路怎么走得稳"**。三者不是竞品，可以同时叠用。

---

## 三大工具总览（修正版）

| 维度 | **OpenSpec** | **Spec Kit** | **SuperPowers / ECC** |
|------|:---:|:---:|:---:|
| **仓库** | `Fission-AI/OpenSpec` | `github/spec-kit` | `obra/superpowers` |
| **Stars** | 52.6k ⭐ | 108k ⭐⭐ | **217k** ⭐⭐⭐ |
| **作者** | Fission-AI | GitHub 官方 | Jesse Vincent / Prime Radiant |
| **架构层** | **第1层：需求→Spec** | **第1层：需求→Spec** | **第2层：Spec→代码** |
| **粒度** | 以 **"Change Proposal"** 为单元 | 以 **"特性(Feature)"** 为单元 | 以 **"任务(Task)"** 为单元 |
| **核心理念** | 轻量 SDD，spec 与 change 强绑定，可回溯 | 完整 SDD 主链，叙事强，三件套评审 | 给 Agent 装"工程纪律"：TDD + 审查 + 自检 |
| **产物** | `changes/xxx/` 文件夹（proposal + specs + design + tasks） | `specs/xxx/` 文件夹（spec + plan + tasks 三件套） | 无产出，纯执行层增强 |

---

## 逐工具详解（修正版）

### OpenSpec — 轻量 SDD（需求 → Spec）

| 维度 | 描述 |
|------|------|
| **粒度** | 以 "Change Proposal" 为单元，每个变更一个独立文件夹 |
| **流程** | `/opsx:propose` → `/opsx:apply` → `/opsx:archive` |
| **优势** | 粒度小、流程轻，已有项目切入成本低；spec 与 change 强绑定，归档后可回溯历史 |
| **特点** | 不预设固定主链命令（不强制 clarify → plan），编辑器/Agent 中立 |
| **适合** | 小粒度迭代、存量项目演进 |

### Spec Kit — 完整 SDD 主链（需求 → Spec）

| 维度 | 描述 |
|------|------|
| **粒度** | 以 "特性(Feature)" 为单元 |
| **流程** | `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` |
| **优势** | 主链命令固化，叙事强、易演示；产物（spec + plan + tasks 三件套）规范且方便评审追溯 |
| **劣势** | 较重，不太适合只改一两个点的小修小补 |
| **适合** | 从零构建、大特性开发、需要评审追溯 |

### SuperPowers / ECC — 执行层增强（Spec → 代码）

| 维度 | 描述 |
|------|------|
| **定位** | **不解决 spec 怎么写，只解决 spec → 代码这段路怎么走得稳** |
| **核心** | 给 Agent 装上「工程纪律」与「工作流模板」：强制 TDD、系统化调试、子代理评审、提交前自检 |
| **机制** | 社区整包模板，agents / hooks / commands / rules 一键就位 |
| **14个 Skills** | brainstorming、writing-plans、subagent-driven-development、test-driven-development、systematic-debugging、requesting-code-review、finishing-a-development-branch 等 |
| **与其他工具关系** | **可与 OpenSpec / Spec-kit 同时叠用**——上层用 OpenSpec/Spec-kit 定 spec，下层用 SuperPowers 执行 |

---

## 三者关系图（修正版）

```
需求 ──→ 第1层（需求→Spec）──→ Spec ──→ 第2层（Spec→代码）──→ 高质量代码

         ┌──────────────┐      │      ┌──────────────────┐
         │  OpenSpec     │      │      │  SuperPowers/ECC │
         │  (轻量 SDD)    │      │      │  (执行层增强)     │
         │  粒度小、成本低 │      │      │  TDD+审查+自检    │
         └──────────────┘      │      └──────────────────┘
                或              │              叠
         ┌──────────────┐      │      ┌──────────────────┐
         │  Spec Kit     │      │      │  Spec Kit 的      │
         │  (完整 SDD)    │      │      │  implement 阶段   │
         │  叙事强、三件套 │      │      │  也可以用 SP 增强  │
         └──────────────┘      │      └──────────────────┘
```

**关键**：SuperPowers 覆盖 "spec → 代码" 这段，而 Spec Kit 的 `/speckit.implement` 也覆盖这段。两者可以叠用（用 SP 的工程纪律增强 Kit 的执行环节），也可以各自独立。

---

## 与 ContextStack 现有体系的对应（修正版）

按两层架构理解后，ContextStack 的情况更清楚了：

| 层级 | 能力 | ContextStack 已有 | 缺口 |
|------|------|:---:|:---:|
| **第1层**（需求→Spec） | generate spec / clarify / plan | ❌ 无 | 可用 OpenSpec 或 Spec Kit 补充 |
| **第2层**（Spec→代码） | TDD + 系统化调试 + 任务拆解 | ✅ 已有 `brainstorming` `writing-plans` `systematic-debugging` `pua-governance` | 缺 `test-driven-development` `code-review` |

**结论**：ContextStack 的优势在**第2层**（执行纪律），已经对齐 SuperPowers 的核心方法论（4/14 Skills）。**第1层（规约生成）是空白**，可以引入 OpenSpec 或 Spec Kit 作为补充——两者与 ContextStack 不冲突，是叠用关系。

---

## 选型建议（修正版）

| 场景 | 第1层选型 | 第2层增强 |
|------|---------|----------|
| **小粒度迭代、已有项目** | **OpenSpec**（轻量切入） | + SuperPowers 或 ContextStack 现有 Skills |
| **从零构建、团队评审** | **Spec Kit**（规范三件套） | + SuperPowers（增强 implement 阶段） |
| **个人项目、快速原型** | OpenSpec（够轻）或不用 | ContextStack 现有 Skills 即可 |
| **已有 ContextStack 体系** | 可选 OpenSpec 补充第1层 | 继续用现有 Skills，或安装 SP 新增 TDD/Review |

---

## 来源

| 工具 | GitHub | 官网 |
|------|--------|------|
| OpenSpec | https://github.com/Fission-AI/OpenSpec | https://openspec.dev/ |
| Spec Kit | https://github.com/github/spec-kit | https://github.github.com/spec-kit/ |
| SuperPowers | https://github.com/obra/superpowers | — |
| SuperPowers 中文版 | https://github.com/jnMetaCode/superpowers-zh | — |

---

## 关联文档

- [[index|Skills 总索引]] — 所有 Skills 一览
- [[codebuddy-builtin-skills-analysis|WorkBuddy Top 10 Skills 适配分析]]
- [[../system/trae-skills-reference|TRAE 热门 Skills 参考]]
- [[brainstorming/brainstorming使用说明]] — ContextStack 已安装的 brainstorming Skill
- [[writing-plans/writing-plans使用说明]] — ContextStack 已安装的 writing-plans Skill