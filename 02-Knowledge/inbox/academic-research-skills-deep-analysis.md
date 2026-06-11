# Academic Research Skills (ARS) — 深度分析与可借鉴设计

- **项目**: [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
- **作者**: Cheng-I Wu（吳政宜）
- **版本**: v3.12.0（2026-06-08）
- **数据**: 30,001 Star / 2,489 Fork / 11 Open Issues
- **许可证**: CC-BY-NC 4.0
- **语言**: Python + Markdown Skills
- **标签**: `academic-pipeline` `claude-code` `literature-review` `peer-review` `prompt-engineering`

---

## 目录

1. [项目定位与核心理念](#1-项目定位与核心理念)
2. [架构总览](#2-架构总览)
3. [四大 Skill 详解](#3-四大-skill-详解)
   - [3.1 Deep Research（深度研究）](#31-deep-research深度研究)
   - [3.2 Academic Paper（论文写作）](#32-academic-paper论文写作)
   - [3.3 Academic Paper Reviewer（论文评审）](#33-academic-paper-reviewer论文评审)
   - [3.4 Academic Pipeline（编排器）](#34-academic-pipeline编排器)
4. [关键设计模式](#4-关键设计模式)
   - [4.1 苏格拉底式引导](#41-苏格拉底式引导)
   - [4.2 魔鬼代言人 + 让步阈值协议](#42-魔鬼代言人--让步阈值协议)
   - [4.3 完整性验证门（Integrity Gates）](#43-完整性验证门integrity-gates)
   - [4.4 风格校准协议](#44-风格校准协议)
   - [4.5 引用真实性验证体系](#45-引用真实性验证体系)
   - [4.6 数据访问级别元数据](#46-数据访问级别元数据)
   - [4.7 范围写入守卫](#47-范围写入守卫)
   - [4.8 实验来源摄入](#48-实验来源摄入)
   - [4.9 跨论文矛盾清单](#49-跨论文矛盾清单)
   - [4.10 部分证据陷阱分解](#410-部分证据陷阱分解)
5. [技术亮点与版本演进关键节点](#5-技术亮点与版本演进关键节点)
6. [对个人可借鉴的设计思路](#6-对个人可借鉴的设计思路)
7. [与 ContextStack 框架的对比与启发](#7-与-contextstack-框架的对比与启发)
8. [核心提醒汇总](#8-核心提醒汇总)
9. [参考资源](#9-参考资源)

---

## 1. 项目定位与核心理念

**ARS 不是"让 AI 替你写论文"的工具，而是"AI 帮你处理学术苦力活，你专注思考"的协作系统。**

### 核心设计哲学

> **"AI is your copilot, not the pilot."** — 工具不替你写论文。它处理参考文献搜索、格式化引用、验证数据、检查逻辑一致性等苦力活，让你专注于真正需要大脑的部分：定义问题、选择方法、解释数据含义、写出"I argue that..."后面的句子。

### 为什么是 Human-in-the-loop，不是全自动化？

基于 Lu et al.（2026, *Nature* 651:914-919）的 **The AI Scientist** 研究：
- 首个通过盲审的全自主 AI 研究系统（ICLR 2025 workshop，得分 6.33/10 vs 平均值 4.87）
- 但论文 Limitations 章节列举了全自主 AI 研究管线的失败模式：**实现错误、幻觉结果、捷径依赖、Bug-as-Insight 重构、方法论伪造、框架锁定（frame-lock）、引用幻觉**

ARS 的设计前提：**人类研究者 + AI 增强 > 各自单独**

### 引用幻觉的实证基础

Zhao et al.（2026-05）审计了 arXiv/bioRxiv/SSRN/PMC 上 250 万篇论文中的 1.11 亿条引用：
- **保守估计 2025 年有 146,932 条幻觉引用**
- 2024 年中出现明显拐点（LLM 大规模使用后）
- bioRxiv→PMC 配对显示 85.3% 的预印本引用在发表后持续存在

ARS v3.7.1+ 在此基础上建立了三层引用锚点系统来应对此问题。

---

## 2. 架构总览

### 管道流程图

```
┌──────────────────────────────────────────────────────────┐
│                    Academic Pipeline (10 Stage)            │
│                                                          │
│  Stage 0: INIT ──────────────────────────────────┐       │
│    ↓                                             │       │
│  Stage 1: RESEARCH (Deep Research)               │       │
│    ↓  13 agents, 7 modes                        │       │
│  Stage 2: WRITE (Academic Paper)                 │       │
│    ↓  12 agents, 10 modes                       │       │
│  Stage 2.5: INTEGRITY GATE (Mandatory)  ←─── 不可跳过  │
│    ↓  引用验证 + 数据一致性 + 完整性检查              │       │
│  Stage 3: REVIEW (Paper Reviewer)                 │       │
│    ↓  EIC + R1/R2/R3 + Devil's Advocate          │       │
│  Stage 3': RE-REVIEW (Verification)               │       │
│    ↓                                              │       │
│  Stage 4: REVISE (Revision Coaching)              │       │
│    ↓                                              │       │
│  Stage 4.5: INTEGRITY GATE (Mandatory)  ←─── 不可跳过  │       │
│    ↓  零回归确认                                    │       │
│  Stage 5: FINALIZE (Formatting)                   │       │
│    ↓                                              │       │
│  Stage 6: PROCESS SUMMARY                         │       │
│    (6维协作质量评估: 1-100 分)                      │       │
└──────────────────────────────────────────────────────────┘
```

### 四大 Skill 矩阵

| Skill | 版本 | Agent 数 | Mode 数 | 核心能力 |
|-------|------|---------|---------|---------|
| **Deep Research** | v2.9.4 | 13 | 7 | 文献检索、PRISMA系统综述、事实核查、苏格拉底式引导 |
| **Academic Paper** | v3.2.0 | 12 | 10 | 写作、风格校准、LaTeX、可视化、修订教练 |
| **Paper Reviewer** | v1.10.0 | 7 | 6 | 多视角同行评审、0-100评分量表、魔鬼代言人 |
| **Pipeline** | v3.12.0 | — | — | 10阶段编排、完整性门、协作评估 |

### 决策映射

**评审评分 → 决策**:
| 分数 | 决策 |
|------|------|
| ≥80 | Accept |
| 65–79 | Minor Revision |
| 50–64 | Major Revision |
| <50 | Reject |

### 输出格式

MD → DOCX（via Pandoc）→ LaTeX → PDF（APA 7.0 / IEEE / Chicago）

---

## 3. 四大 Skill 详解

### 3.1 Deep Research（深度研究）

**13-Agent 研究团队，7 种模式**：

| 模式 | 触发 | 用途 |
|------|------|------|
| `full` | "Research the impact of..." | 完整研究 |
| `quick` | "Give me a quick brief on X" | 快速简报 |
| `systematic-review` | "Do a systematic review on X with PRISMA" | PRISMA 系统综述 |
| `socratic` | "Guide my research on X" | 苏格拉底式引导 |
| `fact-check` | "Fact-check these claims" | 事实核查 |
| `lit-review` | "Do a literature review on X" | 文献综述 |
| `review` | "Review this paper's research quality" | 研究质量评审 |

**关键 Agent 角色**:
- `synthesis_agent` — 综合研究结果
- `research_architect_agent` — 研究架构设计
- `report_compiler_agent` — 报告编译
- `bibliography_agent` — 参考文献管理
- `timeline_extraction_agent` — 时间线提取（v3.9.4）

**苏格拉底模式**的特点：
- 意图检测层：区分探索型 vs 目标导向型
- 对话健康监测：每 5 轮自评（持续同意/回避冲突/过早收敛）
- 探索模式：禁用自动收敛，最大 60 轮，禁止"需要我总结吗？"

### 3.2 Academic Paper（论文写作）

**12-Agent 写作管线，10 种模式**：

| 模式 | 用途 |
|------|------|
| `full` | 完整论文写作 |
| `plan` | 苏格拉底式规划引导 |
| `outline-only` | 仅大纲 |
| `revision` | 修订模式 |
| `revision-coach` | 修订教练（解析审稿意见→路线图） |
| `abstract-only` | 仅摘要 |
| `lit-review` | 文献综述论文 |
| `format-convert` | 格式转换（LaTeX/引文格式） |
| `citation-check` | 引用检查 |
| `disclosure` | AI 披露声明生成 |

**关键能力**:
- **风格校准（Style Calibration）**: 从过去作品中学习个人写作风格
- **写作质量检查（Writing Quality Check）**: 捕捉机器生成文本的模式
- **LaTeX 硬化**: 专业排版输出
- **反泄露协议（Anti-leakage Protocol）**: 防止内容泄露
- **VLM 图表验证**: 视觉模型验证图表

### 3.3 Academic Paper Reviewer（论文评审）

**7-Agent 多视角同行评审，6 种模式**：

**评审团队组成**:
- **EIC（主编）**: 综合裁决
- **R1/R2/R3（3 位动态评审）**: 多角度评审
- **Devil's Advocate（魔鬼代言人）**: 论文攻击者

**评审质量评分表（0-100）**:
- ≥80: Accept
- 65-79: Minor Revision
- 50-64: Major Revision
- <50: Reject

**特殊模式**:
- `calibration` — 校准模式：对用户提供的黄金标准集测量 FNR/FPR
- `re-review` — 验证修订是否充分
- `methodology-focus` — 方法论深度检查

**魔鬼代言人让步阈值协议**:
1. DA 在回复前对每个反驳打分（1-5）
2. 仅当得分 ≥4 时才允许让步
3. 得分 ≤3：坚守立场并重申原始攻击
4. 反讨好规则：不允许连续让步，跟踪让步率

### 3.4 Academic Pipeline（编排器）

**10 阶段编排器，核心保证**:
- 每个阶段都需要用户确认检查点
- **完整性验证（Stage 2.5 + 4.5）不可跳过**
- **R&R 可追溯性矩阵**：独立验证作者的修订声明
- **协作深度观察器**：在每次 checkpoint 评估人机协作深度（Wang & Zhang, 2026）

**v3.4 新增**：合规代理（Compliance Agent）在 Stage 2.5/4.5 执行 PRISMA-trAIce + RAISE 检查

---

## 4. 关键设计模式

### 4.1 苏格拉底式引导

**意图检测层**：
- 在对话开始和每 3 轮后分类用户意图（探索型 vs 目标导向型）
- 探索模式：禁用自动收敛、提高最大轮数、禁止过早总结
- 目标导向模式：标准收敛行为

**对话健康指示器**：
- 每 5 轮无声自评三个维度：持续同意、回避冲突、过早收敛
- 检测到同意模式时自动注入挑战性问题
- 对用户不可见（防止被游戏化），但日志可用于会话后审查

**借鉴价值**: 这个设计可直接用于 ContextStack 的任何需要深度讨论的 Skill 中。

### 4.2 魔鬼代言人 + 让步阈值协议

**问题发现（v3.0）**:
1. **框架锁定（Frame-lock）**: DA 攻击论点，从不攻击前提。从没问"我们讨论的问题本身对吗？"
2. **对抗下的讨好（Sycophancy under pushback）**: 用户每次反驳，DA 让步太快
3. **意图误判（Intent misdetection）**: 苏格拉底导师在用户还在探索时就急着收敛

**解决方案**:
- 让步阈值协议：1-5 打分制，≥4 才让步
- 反讨好规则：禁止连续让步
- 框架锁定检测：每个 checkpoint 后检查
- 意图检测：区分探索 vs 目标导向

**⚠️ 关键洞察**: "这些优化不是解决 AI 的结构性限制——它们让限制变得可见和可管理。"

### 4.3 完整性验证门（Integrity Gates）

**Stage 2.5（写作后）和 Stage 4.5（修订后）**：
- 强制执行，不可跳过
- 7 种失败模式检查（基于 Lu et al. 2026）
- 引用验证、数据一致性、统计错误检测
- 展示案例：Stage 2.5 抓到 15 条伪造引用 + 3 个统计错误

**审计追踪**: 每项检查产生独立报告，可追溯。

### 4.4 风格校准协议

**功能**：从用户的过往作品中学习写作风格特征，使 AI 辅助写作不显"机器味"。

**与"人类化器"的区别**: ARS 不帮你隐藏使用 AI 的事实——它帮你写得更好。

### 4.5 引用真实性验证体系

这是 ARS 最复杂的子系统，经历了多版本迭代：

#### v3.7.3：三层引用锚点系统

每条 `<!--ref:slug-->` 携带 `<!--anchor:<kind>:<value>-->`：
- `<kind>` ∈ `{quote, page, section, paragraph, none}`
- Quote 锚点上限 25 词（URL 编码）

#### v3.8.0：L3 声明忠实度审计

- 可选审计代理（`ARS_CLAIM_AUDIT=1`）
- 对每条采样引用获取原文并判断是否真正支持声明
- 5 种 HIGH-WARN 类别：CLAIM-NOT-SUPPORTED / NEGATIVE-CONSTRAINT-VIOLATION / FABRICATED-REFERENCE / ANCHORLESS / CONSTRAINT-VIOLATION-UNCITED
- 20 元组黄金校准集（FNR<0.15 + FPR<0.10）

#### v3.9.0：三索引三角测量

- 从单一 Semantic Scholar 扩展到 Semantic Scholar + OpenAlex + Crossref
- 4 级建议矩阵（k=0/1/2/3）
- 所有检测为**建议级别**，v3.10 才加入严格模式选项

#### v3.11.0：确定性引用验证门

- 每个引用交叉检查 4 个索引：S2 + OpenAlex + Crossref + **arXiv resolver**
- 持久化 SQLite 缓存（`~/.cache/ars/verification.db`，90天 TTL）
- `lookup_verified` ∈ `{true, false, unresolvable}`
- `false` = ID 精确匹配失败（DOI/arXiv 证明不存在）
- `unresolvable` = 合法未索引（人文学科/非英语/地区性期刊）不阻塞

### 4.6 数据访问级别元数据

每个 Skill 声明 `data_access_level`（`raw` / `redacted` / `verified_only`），由 `scripts/check_data_access_level.py` 强制执行。

此模式改编自 Anthropic 的 automated-w2s-researcher（2026）。

### 4.7 范围写入守卫

**v3.10 引入的确定性 `PreToolUse` 钩子**：
- 将 23 个单阶段 Agent 限制在各自阶段目录内
- 禁止 Bash 访问（仅允许 Grep/Glob + 结构化编辑工具）
- 默认开启（唯一的默认行为变更）

### 4.8 实验来源摄入

**v3.12.0（#260）新增**：
- 每个 Material Passport 上的 `experiment_provenance[]` 数组
- 学者在 ARS 外部运行实验，录入来源信息
- 论文声明通过 `planned_experiment_ids[]` 关联到实验
- 完整性门审计每个实验支持的声明：`ALIGNED` / `OVERSTATED` / `NOT_SUPPORTED_BY_PROVENANCE` / `PROVENANCE_INSUFFICIENT`
- `no_experiments_declared` 也是合法声明

### 4.9 跨论文矛盾清单

**v3.12.0（#262）新增**：
- 结构化的跨论文矛盾清单
- 使评估的论文对可枚举，供学者确认

### 4.10 部分证据陷阱分解

**v3.12.0（#213/#214）新增**：
- 在引用判断器（#213）和编辑综合器（#214）两个层面进行子声明分解
- 解决部分证据陷阱（§F.3.2）：一个引用支持声明的部分但不是全部

---

## 5. 技术亮点与版本演进关键节点

### 版本路线图（v3.0 → v3.12.0）

| 版本 | 日期 | 关键变更 |
|------|------|---------|
| v3.12.0 | 2026-06-08 | 实验来源摄入、图表忠实度门、跨论文矛盾、部分证据分解 |
| v3.11.0 | 2026-06-04 | 确定性引用验证门（4索引交叉检查 + SQLite 缓存） |
| v3.10.0 | 2026-06-01 | 三角测量策略层、Kong 调查采纳、评估工具、范围写入守卫 |
| v3.9.0 | 2026-05-17 | 三索引三角测量（S2+OpenAlex+Crossref） |
| v3.8.0 | 2026-05-16 | L3 声明忠实度定位器+审计（端到端） |
| v3.7.0 | 2026-05-05 | Claude Code 插件化包装（一行安装） |
| v3.6.8 | 2026-05-03 | 生成器-评估器合约门 |
| v3.3.2+ | — | 数据访问级别元数据、任务类型注释 |
| v3.0 | 2026-02 | 让步阈值协议、意图检测、对话健康指示器 |

### 关键架构决策

1. **插件化 vs 传统安装**：v3.7.0 同时支持两种方式（Plugin + symlink），不破坏已有用户
2. **模型路由**：`opus` 用于架构/审稿解释深度任务，`sonnet` 用于其余 8 种模式，禁用 Haiku
3. **Model: inherit**：插件代理使用 inherit 而非固定模型，让用户会话的模型选择传递
4. **符号链接而非复制**：skills/ 目录使用相对符号链接，保持单一真相源
5. **合约门设计**：生成器-评估器合约门（v3.6.8）确保输出质量可验证

### 性能与成本

- 完整管线（15k 词论文）：约 $4-6
- 每种模式的 token 预算见 `docs/PERFORMANCE.md`
- 推荐设置：Skip Permissions + Agent Team 可选

---

## 6. 对个人可借鉴的设计思路

### 6.1 直接可用于 ContextStack 的模式

| ARS 设计模式 | ContextStack 应用场景 | 优先级 |
|-------------|----------------------|--------|
| **苏格拉底式引导** | inbox 文档整理时与用户的深度讨论 | 🔴 高 |
| **意图检测层** | 区分用户是"探索学习"还是"目标执行" | 🔴 高 |
| **对话健康指示器** | 防止 AI 讨好用户、过早收敛 | 🟡 中 |
| **风格校准** | 学习用户的写作/代码风格 | 🟡 中 |
| **完整性门** | 重要文档输出前的自动检查清单 | 🔴 高 |
| **引用验证锚点** | 技术文档中引用的可追溯性 | 🟡 中 |
| **数据访问级别** | 不同 Skill 的权限边界 | 🟢 低 |
| **范围写入守卫** | 防止 Agent 越权操作 | 🟡 中 |

### 6.2 对你当前工作流的启发

**1. 文档整理流程可加入"完整性门"**

当前 inbox 文档整理是单向的（获取→整理→归档）。可借鉴 ARS 的 Stage 2.5/4.5 概念：
- 整理完成后自动运行一致性检查（引用是否准确、数据是否矛盾、结构是否完整）
- 归档前触发最终验证

**2. "让步阈值协议"可防 AI 讨好**

你在使用 AI 助手时，如果 AI 太快同意你的观点，可以用类似机制：
- 要求 AI 先给你的反驳打分再回应
- 设立"反讨好"规则

**3. 引用可追溯性**

技术笔记中的外部引用（论文、文档、推文）可以模仿三层锚点系统：
- 每条引用标注来源 + 具体定位（段落/页码/URL 锚点）
- 方便日后验证

**4. 实验来源摄入 — 适合嵌入式开发场景**

你的嵌入式/TFLM 项目中的实验结果（性能对比、内存占用等）可以像 ARS 的 experiment_provenance 一样结构化记录，确保声明有据可查。

---

## 7. 与 ContextStack 框架的对比与启发

| 维度 | ARS | ContextStack | 差距/启发 |
|------|-----|-------------|----------|
| **定位** | Claude Code 学术研究 Skill 套件 | 个人 AI 协作知识管理框架 | ARS 是专用工具，ContextStack 是通用框架 |
| **Agent 数量** | 32+ 专用 Agent | 1 个通用 AI 助手 | ARS 的多 Agent 分正是关键优势 |
| **质量保证** | 完整性门 + 引用验证 + 校准 | 用户手动检查 | **ARS 的自动化质量门可直接借鉴** |
| **反讨好机制** | 让步阈值协议 + 对话健康监测 | 无 | **重要缺失** |
| **风格适配** | Style Calibration 学习用户风格 | MEMORY.md 记忆偏好 | ContextStack 的记忆系统更通用 |
| **插件化** | 一行安装 + 10 个 slash 命令 | Git 仓库 + 手动同步 | ARS 的分发体验更好 |
| **引用验证** | 4 索引交叉 + SQLite 缓存 | 手动 URL/来源标注 | ARS 的验证深度远超当前需要 |
| **版本管理** | 语义版本 + 详细 CHANGELOG | 无版本概念 | 可借鉴 CHANGELOG 格式 |

### 核心差距

ContextStack 目前缺少的最大一块是 **"自动化质量门"**——文档整理完成后没有自动检查环节。ARS 的 Integrity Gate 概念可以直接改造为 ContextStack 的"输出前检查清单"。

---

## 8. 核心提醒汇总

| # | 提醒 | 重要性 |
|---|------|--------|
| 1 | ARS 不是"AI替你写论文"——是"AI处理苦力，你负责思考" | 🔴 |
| 2 | 全自主 AI 研究有 7 种已知失败模式，Human-in-the-loop 是 ARS 的核心设计前提 | 🔴 |
| 3 | v3.0 的三个发现（frame-lock/sycophancy/intent-misdetection）是 AI 的结构性限制，不是 prompt engineering 能解决的 | 🔴 |
| 4 | 让步阈值协议（1-5分制）是反 AI 讨好的实用方案 | 🟡 |
| 5 | 完整性门不可跳过——这是质量保证的底线 | 🔴 |
| 6 | 引用验证从建议到严格的演进路径值得学习：检测永远运行，阻断可选开启 | 🟡 |
| 7 | 范围写入守卫（禁止 Bash + 限制目录）是 Agent 安全的基础设施 | 🟡 |
| 8 | Style Calibration 学习风格但不隐藏 AI 使用痕迹——透明度优先 | 🟡 |
| 9 | 4 索引交叉验证 + SQLite 缓存（90天 TTL）是引用验证的工程最佳实践 | 🟢 |
| 10 | 插件化分发（一行安装 + slash 命令）极大降低使用门槛 | 🟡 |
| 11 | "unresolvable ≠ false" 的区分保护了人文学科/非英语引用不被误判 | 🟢 |
| 12 | 对话健康指示器对用户不可见（防止游戏化），但日志可审查 | 🟢 |

---

## 9. 参考资源

| 资源 | 链接 |
|------|------|
| 项目主页 | https://github.com/Imbad0202/academic-research-skills |
| 架构文档 | `docs/ARCHITECTURE.md`（41KB） |
| 性能与成本 | `docs/PERFORMANCE.md`（14KB） |
| 安装指南 | `docs/SETUP.md` |
| 展示案例 | `examples/showcase/`（完整 10 阶段管线产物） |
| 配套 Experiment Agent | https://github.com/Imbad0202/experiment-agent |
| Codex CLI 版本 | https://github.com/Imbad0202/academic-research-skills-codex |
| 作者使用指南（EN） | https://open.substack.com/pub/edwardwu223235/p/academic-writing-shouldnt-be-a-solo |
| 作者使用指南（繁中） | https://open.substack.com/pub/edwardwu223235/p/ai |
| Lu et al. (2026) | *Nature* 651:914-919 — The AI Scientist |
| Zhao et al. (2026) | arXiv:2605.07723 — 1.11亿引用审计 |
| PaperOrchestra | arXiv:2604.05018 — Google 论文（v3.3 灵感来源） |
| Kong et al. (2026) | arXiv:2605.18661 — 自动研究特征跟踪（v3.12 灵感来源） |

---

> **一句话总结**: ARS 是 Claude Code 生态中最成熟的学术 Skill 套件——不是因为它能写论文，而是因为它建立了一套完整的"AI协作质量保证体系"：从意图检测到反讨好，从引用验证到完整性门，从风格校准到实验来源追溯。对 ContextStack 最大的启发是**"自动化质量门"**的概念——在输出前加入不可跳过的检查点。
