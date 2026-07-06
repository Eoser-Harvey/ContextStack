---
title: Skills 制作最佳实践（Anthropic 官方方法论）
created: 2026-06-23
updated: 2026-06-23
tags:
  - Skills
  - AI-Coding
  - Anthropic
  - 最佳实践
  - 大赛
source: "[[AI 大赛工具及场景推荐]]"
---

# Skills 制作最佳实践

> **核心来源**：Anthropic 技术团队成员 Thariq Shihipar（Claude Code 项目）于 2026-06-03 发布博客 *《Lessons from Building Claude Code: How We Use Skills》*
>
> **原文链接**：[claude.com/blog/lessons-from-building-claude-code-how-we-use-skills](https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills)
>
> 本文抽取自 [[AI 大赛工具及场景推荐]]

---

## 什么是真正的 Skill

> 原文：*"A common misconception we hear about skills is that they are 'just markdown files.' They're actually folders that can include scripts, assets, data, etc. that the agent can discover, explore and manipulate."*

**常见误区**：很多人认为 Skill "只是 Markdown 文件"。

**实际上**：Skill 是**文件夹**，包含指令、脚本、资源和数据文件。agent能**发现、探索和操作**这个文件夹中的所有内容。

**Skill 的三种组成要素**：

| 要素 | 说明 | 示例 |
|------|------|------|
| **指令** (Instructions) | SKILL.md 核心文件 | 描述触发条件、工作流程模板 |
| **脚本** (Scripts) | 可执行的辅助代码 | `scripts/` 目录中的 Python/Bash 脚本 |
| **资源** (Resources) | 参考文档、数据文件、模板 | `references/api.md`、`assets/template.md`、`config.json` |

---

## 四大设计哲学

| 设计原则          | 含义                                                               | 大赛启示                                                          |
| ------------- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| **渐进式信息披露**   | 把文件系统作为上下文工程手段，让 AI 按需读取，不一次性塞满上下文窗口                             | Skill 应是一个文件夹，SKILL.md 只做"目录"，详细信息拆分到 `references/`、`assets/` |
| **灵活性优于严格指令** | 避免"轨道化" AI，给信息但保留适应空间。Claude 会尽量遵循指令，但过于具体的指令反而有害                | 不要写成 SOP 流水线，要写成"知识 + 工具"，让 AI 自主判断                           |
| **为模型而非人类编写** | Claude Code 启动会话时构建所有 Skill 及其描述的列表，模型扫描它们来决定"有 Skill 能处理这个请求吗？" | 描述中要包含**触发词**，让模型自动匹配；描述字段不是摘要，是触发说明                          |
| **从实践中演化**    | 最佳 Skills 都是"几行指令 + 一个 gotcha"起步，遇到新边界情况不断迭代                     | 不要追求一步到位，大赛从 MVP Skill 开始，持续积累 Gotchas                        |

---

## 九条制作最佳实践（核心干货）

### 实践 1：不要陈述显而易见的内容

> 原文：*"Claude already knows how to code and can read your codebase. A skill that restates what Claude would do by default adds context without adding value."*

Claude 已经会编码、能读代码库。重述默认行为的 Skill 只会浪费上下文。**把精力集中在能把 AI 推出"舒适区"的信息上**。

**正面示例**：Anthropic [前端设计 Skill](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)——由 Anthropic 工程师通过与客户迭代改进 Claude 的设计品味构建，**专门避开了 Inter 字体和紫色渐变**（Claude 的默认舒适区输出），转而引导生成更独特的 UI。

### 实践 2：构建"Gotchas"（坑点/易错点）⭐⭐⭐ 信号密度最高

> 原文：*"The highest signal-to-noise content in any skill is the gotchas section."*

这是任何 Skill 中**信号价值最高**的部分。应该从 Claude 使用 Skill 时遇到的常见失败点**持续积累**。理想情况下，随着时间推移不断更新 Skill 以捕获这些坑点。

```
"subscriptions 表是仅追加的。你需要的是版本号最高的行，
不是 created_at 最近的。"

"这个字段在 API 网关叫 @request_id，在计费服务叫 trace_id。
它们是同一个值。"

"Staging 环境即使 Stripe webhook 未处理也返回 200。
检查 payment_events 获取真实状态。"
```

**关键做法**：每遇到一次 AI 犯错，就往 Skill 里加一条 Gotcha。这比花时间写大段说明文字效率高得多。

### 实践 3：善用文件系统的渐进式信息披露

> 原文：*"Think of the entire file system as a form of context engineering and progressive disclosure. Tell Claude what files are in your skill, and it will read them at appropriate times."*

**核心理念**：把整个文件系统视为上下文工程的一种形式。告诉 Claude Skill 中有哪些文件，它会在适当的时机读取它们。

**推荐的 Skill 目录结构**：

```
skill-folder/
├── SKILL.md              # 主指令文件，指向其他文件
├── config.json           # 用户配置（可选）
├── references/
│   └── api.md            # 详细的函数签名和使用示例
├── assets/
│   └── template.md       # 输出模板文件，供复制使用
├── scripts/
│   └── helpers.py        # 辅助脚本
└── stuck-jobs.md         # 特定情况参考（如：处理挂起的任务时）
```

**关键原则**：SKILL.md 只做目录，指向其他文件。例如：

> *"如果任务是 pending 状态，应该参考 stuck-jobs.md。"*

- 最简单的形式：将详细函数签名和使用示例拆分到 `references/api.md`
- 如果最终输出是 Markdown 文件，在 `assets/` 中包含模板文件

### 实践 4：避免过度限制 Claude 的灵活性

> 原文：*"Claude will generally try to follow instructions, but because skills are highly reusable, instructions that are too specific need caution."*

Claude 通常会尽量遵循指令，但因为 Skill 高度可复用，**过于具体的指令需要谨慎**。

**反面示例**（过于限制）：
```
❌ "你必须先检查 package.json，然后运行 npm install，然后..."
```

**正确方式**（给信息 + 留灵活性）：
```
✅ "确保依赖已安装。如果使用 npm，运行 npm install；
   如果使用 yarn，运行 yarn add。"
```

**核心原则**：给 AI **知识 + 工具**，而不是 SOP。让它根据具体情况灵活决策。

### 实践 5：仔细考虑设置流程

> 原文：*"Certain skills may need context from the user to be set up. A good pattern is to store this setup information in a config.json file in the skill directory."*

某些 Skill 需要用户提供上下文才能设置。

**推荐模式**：将设置信息存储在 Skill 目录中的 `config.json` 文件中。

```json
// skill-folder/config.json
{
  "slack_channel": "未配置",
  "notify_on_deploy": true,
  "default_reviewers": []
}
```

- 如果配置未设置，代理可以**向用户询问信息**
- 需要结构化多选问题时，可以指示 Claude 使用 **AskUserQuestion 工具**

### 实践 6：为模型编写描述——而非人类 ⭐

> 原文：*"When you start a Claude Code session, it builds a list of every skill available to the session along with their descriptions. Claude scans this list when deciding if there's a skill to handle a particular request."*

Claude Code 启动会话时，构建所有可用 Skill 及其**描述**的列表。Claude 扫描这个列表来决定"有 Skill 能处理这个请求吗？"

**描述字段不是摘要，是何时触发该 Skill 的说明。**

```
❌ 人类导向的描述（错误）：
"这个技能帮助你管理 PR。"

✅ 模型导向的描述（正确）：
"当用户提到 'babysit'、'监控 PR' 或 '自动合并' 时触发。
监控 PR → 重试不稳定的 CI → 解决合并冲突 → 启用自动合并。"
```

**关键技巧**：在描述中包含**触发词**能显著提高命中率。

### 实践 7：帮 Claude 构建"记忆"

> 原文：*"Certain skills can include a form of memory by storing data inside the skill, from simple append-only text log files or JSON files to SQLite databases for complex cases."*

某些 Skill 可以通过在内部存储数据来包含一种**记忆形式**。

**三级记忆方案**：

| 级别 | 方式 | 适用场景 |
|------|------|---------|
| **简单** | 仅追加文本日志 `.log` | 站会记录、工作流执行历史 |
| **中等** | JSON 文件 | 结构化配置、状态追踪 |
| **复杂** | SQLite 数据库 | 大量结构化查询数据 |

**示例：`standup-post` Skill 的 `standups.log`**：

```
[2026-06-02] 站会报告: 审查了 Sarah 的 auth PR, 合并了 3 个 fix 分支...
[2026-06-03] 站会报告: 完成了计费模块重构, 创建了 2 个新工单...
```

每次运行 `standup-post` 时，Claude 读取历史记录，判断昨天以来的变化，**只生成增量内容**。

**持久化数据路径**：使用环境变量（Claude Code 中为 `${CLAUDE_PLUGIN_DATA}`）获取存储数据的稳定目录。参见：[持久化数据目录文档](https://code.claude.com/docs/en/plugins-reference#persistent-data-directory)

### 实践 8：存储脚本并生成代码

> 原文：*"One of the most powerful tools you can give Claude is code itself. Giving Claude scripts and libraries lets it spend its turns on composition, deciding what to do next rather than reconstructing boilerplate."*

给 Claude 最强大的工具之一是**代码本身**。给 Claude 脚本和库可以让他把精力花在**组合**上——决定下一步做什么——而不是重复构建模板代码。

**Skill 中的辅助函数库** (`data-science/helpers.py`)：

```python
def fetch_events_from_source(source_id, date_range):
    """从事件源获取事件数据"""
    ...

def aggregate_events(events, grouping_key):
    """按指定键聚合事件"""
    ...

def detect_anomalies(data, threshold=2.0):
    """检测数据中的异常"""
    ...
```

**Claude 动态生成的组合脚本**：

```python
# Claude 为回答 "周二发生了什么？" 而动态生成
events = fetch_events_from_source("main_prod", ("2026-06-02", "2026-06-02"))
aggregated = aggregate_events(events, "event_type")
anomalies = detect_anomalies(aggregated, threshold=1.5)
print(anomalies)
```

**核心价值**：Claude 不需要重写样板代码，只需要**组合已有函数**并处理业务逻辑。

### 实践 9：使用按需钩子（On-Demand Hooks）

> 原文：*"Skills can include hooks that activate only when the skill is invoked and only last for the session. They're useful for situations where you don't want something running all the time but it's very useful occasionally."*

Skill 可以包含**仅在 Skill 被调用时激活**的钩子，且**仅在会话期间**持续。用于你不想一直运行、但偶尔非常有用的情况。

**示例 1：`/careful` 钩子**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'rm -rf\\|DROP TABLE\\|force-push\\|kubectl delete' && exit 2 || exit 0"
      }]
    }]
  }
}
```

阻止：`rm -rf`、`DROP TABLE`、`force-push`、`kubectl delete` 等危险操作。只在你知道正在操作生产环境时启用。一直开着会让人抓狂。

**示例 2：`/freeze` 钩子**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "echo \"$CLAUDE_FILE_PATHS\" | grep -q \"^/safe/dir/\" && exit 0 || exit 2"
      }]
    }]
  }
}
```

阻止任何不在指定目录中的 Edit/Write 操作。使用场景：调试时——"我想加日志但我老是不小心'修复'不相关的代码"。

---

## 总结

> 原文：*"Skills best practices are still evolving. Most of our best skills began as a few lines and a single gotcha, then got better because people kept adding to them as Claude hit new edge cases."*

**Skill 的最佳实践仍在不断演进**。大多数最优秀的 Skill 都是从几行指令和一个坑点开始，然后随着 Claude 遇到新的边界情况而不断改进。

**三大核心洞察**：

1. **把文件系统当作上下文工程工具**——通过渐进式披露让 AI 在正确时机获取正确信息
2. **把"坑点"当作最高密度信号**——持续从 AI 失败中积累，每一条都是黄金
3. **把验证类 Skill 当作 ROI 最高的投资**——建议花至少一周专门打磨

**最好的 Skill 不是给 AI 更多通用知识，而是给它那些"不说不知道"的关键信息和可复用的代码能力。**

> **行动建议**：最佳理解方式是开始实践、实验。查看 [官方 Skills 文档](https://code.claude.com/docs/en/skills) 和 [可自定义的示例 Skill](https://github.com/anthropics/skills)。

---

## 大赛启示：从实例中提炼可操作的 Skill 构建模板

**最简 Skill 模板（5 分钟起步版）**：

```yaml
---
name: my-skill-name
description: 何时触发这个 Skill？包含触发词。例如："当用户提到 X、Y、Z 时使用。"
---

# Skill 标题

## 一句话说清楚这个 Skill 做什么

（让 AI 知道是否该激活此 Skill）

## 关键坑点（Gotchas）

- 坑点 1：AI 最容易在这里犯错的具体情况
- 坑点 2：字段命名不一致（A 叫 X，B 叫 Y，它们是同一个值）
- 坑点 3：看似正常但实际有问题的默认行为

## 工作流程

1. 第一步做什么
2. 第二步做什么
3. 第三步做什么

## 参考

- 如果场景 A，参考 references/a.md
- 如果场景 B，使用 scripts/b.py
```

**成熟 Skill 模板（迭代多轮后）**：

```
skill-name/
├── SKILL.md           # 指令目录（指向所有子文件）
├── config.json        # 用户配置（Slack 频道、默认值等）
├── references/
│   └── api.md         # 详细 API 文档（函数签名、边界情况）
├── assets/
│   └── template.md    # 输出模板（报告格式、PR 模板等）
├── scripts/
│   ├── helpers.py     # 辅助函数库（获取数据、格式化等）
│   └── validate.py    # 验证脚本（检查输出合法性）
└── gotchas.md         # 按场景组织的坑点汇总
```

> **记住 Anthropic 的核心经验**：最好的 Skill 都是从 "几行指令 + 一个坑点" 开始的。不要试图一步到位写出 900 行的 SKILL.md，而是从 MVP 开始，**每次 AI 犯错就加一条 Gotcha**。

---

## 优秀 Skill 实例剖析（来自 Anthropic 官方仓库）

> **来源**：[github.com/anthropics/skills](https://github.com/anthropics/skills) — Anthropic 官方开源 Skills 仓库，14.9 万 Star。
>
> 以下选取官方仓库中三个代表性 Skill 作为实例，展示不同复杂度的 Skill 如何组织、如何编写。

---

### 实例 1：`frontend-design` — 设计哲学型 Skill（最简结构）

**仓库路径**：`skills/frontend-design/`

**目录结构**：

```
frontend-design/
├── SKILL.md       # 唯一的指令文件
└── LICENSE.txt    # 许可证
```

> 这是 Anthropic 博客中**点名表扬的 Skill**。它的价值不在文件数量，而在**每一句话都把 AI 推出默认舒适区**。

**SKILL.md 完整内容**：

```yaml
---
name: frontend-design
description: Guidance for distinctive, intentional visual design when building 
  new UI or reshaping an existing one. Helps with aesthetic direction, typography, 
  and making choices that don't read as templated defaults.
license: Complete terms in LICENSE.txt
---
```

```markdown
# Frontend Design

Approach this as the design lead at a small studio known for giving every
client a visual identity that could not be mistaken for anyone else's.

## Ground it in the subject

If the brief does not pin down what the product or subject is, pin it 
yourself before designing: name one concrete subject, its audience, and 
the page's single job, and state your choice.

## Design principles

For web designs, the hero is a thesis. Open with the most characteristic 
thing in the subject's world.

Typography carries the personality of the page. Pair the display and body 
faces deliberately, not the same families you would reach for on any other 
project.

Structure is information. Structural devices, numbering, dividers, labels, 
should encode something true about the content, not decorate it.

Leverage motion deliberately. An orchestrated moment usually lands harder 
than scattered effects.

## Process: brainstorm, explore, plan, critique, build, critique again

For calibration: AI-generated design right now clusters around three looks:
(1) warm cream background + serif display + terracotta accent
(2) near-black background + acid-green or vermilion accent
(3) broadsheet layout with hairline rules, zero border-radius

All three are defaults rather than choices. Where the brief leaves an axis 
free, don't spend that freedom on one of these defaults.

Work in two passes. First, brainstorm a compact token system with color, 
type, layout, and signature. Then review against the brief: if any part 
reads like a generic default — revise it.

## Restraint and self-critique

Spend your boldness in one place. Let the signature element be the one 
memorable thing. Critique your own work as you build. Consider Chanel's 
advice: before leaving the house, take a look in the mirror and remove 
one accessory.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand. 
Write from the end user's side of the screen. Use active voice. Treat 
failure and emptiness as moments for direction, not mood.
```

> **原文链接**：[SKILL.md 完整版](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)

**这个 Skill 为什么写得好？**

| 维度 | 分析 |
|------|------|
| **单一类别** | 清晰属于「创意与设计」类，不越界 |
| **不说废话** | 没有"使用 CSS 的 color 属性设置颜色"这种 AI 本来就知道的东西 |
| **推出舒适区** | 明确指出 AI 默认倾向的三种"模板化"设计风格，要求避开 |
| **具体而灵活** | 给设计原则但不给 SOP，AI 有判断空间 |
| **角色定位** | 第一句话 "Approach this as the design lead at a small studio..." 设定了 AI 的角色心态 |
| **过程驱动** | 两步走流程：brainstorm→critique→build→critique again |
| **高密度描述** | description 字段精确描述了触发场景，而非人类摘要 |

---

### 实例 2：`docx` — 复杂工具型 Skill（多文件结构）

**仓库路径**：`skills/docx/`

**目录结构**：

```
docx/
├── SKILL.md           # 主指令（900+ 行）：快速参考 + 代码模板 + 坑点
├── LICENSE.txt
├── scripts/
│   ├── accept_changes.py    # 接受修订跟踪的辅助脚本
│   └── office/
│       ├── soffice.py       # LibreOffice 无头模式封装
│       ├── unpack.py        # 解包 .docx 为可编辑 XML
│       ├── pack.py          # 重新打包 XML 为 .docx
│       └── validate.py      # 验证生成的 .docx 合法性
```

**SKILL.md 核心结构**：

```
SKILL.md
├── 快速参考表（读 / 创建 / 编辑 → 工具对照）
├── 创建新文档（docx-js 完整 API 参考）
│   ├── 页面尺寸（CRITICAL: 默认 A4 非 Letter）
│   ├── 样式覆盖（Heading1 / Heading2 精确 ID）
│   ├── 列表（CRITICAL: 绝不用 unicode 项目符号）
│   ├── 表格（CRITICAL: 双宽度设置）
│   ├── 图片 / 超链接 / 脚注 / 制表位 / 多栏
│   └── 关键规则汇总（20+ 条 CRITICAL 标记）
├── 编辑已有文档（解包→编辑 XML→打包 三步法）
│   ├── 修订跟踪（Tracked Changes）XML 模板
│   ├── 批注系统（Comment）XML 模板
│   └── 常见坑点
├── XML 参考手册
└── 依赖说明
```

> **原文链接**：[docx SKILL.md 完整版](https://github.com/anthropics/skills/blob/main/skills/docx/SKILL.md)

**这个 Skill 为什么写得好？**

| 维度 | 分析 |
|------|------|
| **文件夹思维** | `scripts/` 中的 Python 脚本是 AI 的工具箱，AI 只需调用脚本组合逻辑，不用重新实现 |
| **高密度坑点** | 20+ 处 `CRITICAL` 标记。例如："PageBreak must be inside a Paragraph"、"Never use unicode bullets"、"Tables need dual widths" |
| **渐进式披露** | SKILL.md 是快速参考和代码模板，详细 API 可指向外部文档。用户不需要读完 900 行才能使用 |
| **代码模板即工具** | JavaScript 代码块不是"说明文档"，而是**可直接复制使用的模板**，AI 只需替换业务内容 |
| **验证闭环** | `validate.py` 确保 AI 输出合法；`unpack.py → pack.py` 提供可逆编辑工作流 |
| **三步标准化流程** | 编辑文档固定为 Unpack→Edit XML→Pack，避免每次重新决策 |
| **为模型写描述** | description 包含 "Word doc"、"word document"、".docx"、"report"、"memo" 等触发词 |

---

### 实例 3：`pdf` — 中等复杂度工具型 Skill

**仓库路径**：`skills/pdf/`

**目录结构**：

```
pdf/
├── SKILL.md        # 主指令：Python API + 命令行 + 常见任务
├── REFERENCE.md    # 进阶参考（pypdfium2、pdf-lib、故障排查）
├── FORMS.md        # 表单填写专项指南
└── LICENSE.txt
```

> **这个结构的精髓**：SKILL.md 只放"90% 场景够用"的内容，10% 的进阶场景和故障排查拆分到 REFERENCE.md。AI 根据需要按需读取，不浪费上下文。

**SKILL.md 核心结构**：

```
SKILL.md
├── Quick Start（5 行代码即可读 PDF）
├── Python 库（pypdf / pdfplumber / reportlab）
│   ├── 合并 / 拆分 / 旋转 / 元数据
│   ├── 文本提取 / 表格提取（含 pandas 导出）
│   └── 创建 PDF（含上下标坑点：绝不用 Unicode 字符）
├── 命令行工具（pdftotext / qpdf / pdftk）
├── 常见任务（OCR 扫描件 / 水印 / 提取图片 / 密码保护）
├── 快速参考表（任务 → 工具 → 代码）
└── 下一步：指向 REFERENCE.md 和 FORMS.md
```

> **原文链接**：[pdf SKILL.md 完整版](https://github.com/anthropics/skills/blob/main/skills/pdf/SKILL.md)

**Skill 之间的依赖引用模式**：

```
SKILL.md 末尾：
  - For advanced pypdfium2 usage, see REFERENCE.md
  - For JavaScript libraries (pdf-lib), see REFERENCE.md
  - If you need to fill out a PDF form, follow the instructions in FORMS.md
  - For troubleshooting guides, see REFERENCE.md
```

这就是 **渐进式披露的核心机制**：AI 读 SKILL.md 看到这些引用，会根据当前任务判断是否需要进一步读取子文件。

---

> **版本说明**：本文抽取自 [[AI 大赛工具及场景推荐]] 第一章。完整原文包含 AI 编程工具链生态、MCP 工具、参赛策略建议等，请查阅原文。
>
> **最后更新**：2026-06-23
