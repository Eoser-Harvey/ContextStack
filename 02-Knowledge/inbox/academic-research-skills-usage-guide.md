# ARS (Academic Research Skills) 使用指南 — 从安装到实战

- **项目**: [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
- **版本**: v3.12.1 (2026-06-15)
- **定位**: Claude Code 学术研究 Skill 套件，覆盖从研究到发表的全流程
- **核心理念**: AI is your copilot, not the pilot

---

## 目录

1. [安装](#1-安装)
2. [四大 Skill 速查](#2-四大-skill-速查)
3. [Deep Research 深度研究](#3-deep-research-深度研究)
4. [Academic Paper 论文写作](#4-academic-paper-论文写作)
5. [Academic Paper Reviewer 论文评审](#5-academic-paper-reviewer-论文评审)
6. [Academic Pipeline 全流程编排](#6-academic-pipeline-全流程编排)
7. [费用与性能](#7-费用与性能)
8. [进阶配置](#8-进阶配置)
9. [实战建议](#9-实战建议)

---

## 1. 安装

### 1.1 前置条件

- Claude Code CLI / VS Code 插件 / JetBrains 插件
- `ANTHROPIC_API_KEY` 已设置
- 可选: Pandoc (DOCX 输出)、tectonic + 思源宋体 (PDF 输出)

### 1.2 推荐安装方式：Plugin (v3.7.0+)

```text
/plugin marketplace add Imbad0202/academic-research-skills
/plugin install academic-research-skills
```

装完后验证：
```text
/ars-plan
```
输入你的论文主题，ARS 会启动苏格拉底式对话帮你梳理章节结构。

**强烈建议开启自动更新**：ARS 每 1-2 周发版，在 `/plugin` UI 里找到 `academic-research-skills` 开启 auto-update。

### 1.3 其他安装方式

| 方式 | 适用场景 | 命令 |
|------|---------|------|
| **Plugin** (推荐) | Claude Code CLI / IDE | `/plugin install academic-research-skills` |
| **Project skills** | 单个项目使用 | `cp -R deep-research .claude/skills/` 等 |
| **Global skills** | 所有项目通用 | 复制到 `~/.claude/skills/` |
| **Standalone** | 直接在 ARS 仓库工作 | `git clone` 后 `claude` |
| **Claude Cowork** | Desktop 用户 | 每个 skill 单独打包 zip 上传 |

### 1.4 快速开始

```bash
# 1. 安装 Claude Code
irm https://claude.ai/install.ps1 | iex   # Windows
# curl -fsSL https://claude.ai/install.sh | bash  # macOS/Linux

# 2. 设置 API Key
$env:ANTHROPIC_API_KEY="sk-ant-xxxxx"   # Windows PowerShell
# export ANTHROPIC_API_KEY=sk-ant-xxxxx  # macOS/Linux

# 3. 启动
claude
```

---

## 2. 四大 Skill 速查

| Skill | 用途 | 模式数 | Agent 数 | 触发词 |
|-------|------|--------|---------|--------|
| **Deep Research** | 文献检索、综述、事实核查 | 8 | 13 | "research", "deep research", "文献综述" |
| **Academic Paper** | 论文写作、修订、格式转换 | 11 | 12 | "write a paper", "写论文", "帮我写" |
| **Paper Reviewer** | 多视角同行评审 | 6 | 7 | "review this paper", "评审", "审稿" |
| **Pipeline** | 10 阶段全流程编排 | 1+1 | — | "complete research paper", "全流程" |

### 27 种模式总览

```
Deep Research (8 modes):
  full, quick, review, lit-review, three-way-scan, fact-check, socratic, systematic-review

Academic Paper (11 modes):
  full, plan, outline-only, revision, revision-coach, abstract-only, 
  lit-review, format-convert, citation-check, disclosure, rebuttal-audit

Paper Reviewer (6 modes):
  full, re-review, quick, methodology-focus, guided, calibration

Pipeline (1 mode):
  full pipeline + resume_from_passport
```

---

## 3. Deep Research 深度研究

### 3.1 8 种模式详解

| 模式 | 触发方式 | 输出 |  oversight | 适用场景 |
|------|---------|------|-----------|---------|
| `full` | "Research the impact of..." | APA 7.0 报告，3000-8000 词 | 高 | 完整深度研究 |
| `quick` | "Give me a quick brief on X" | 研究简报，500-1500 词 | 中 | 快速了解一个主题 |
| `systematic-review` | "Do a systematic review on X with PRISMA" | PRISMA 2020 报告，5000-15000 词 | 中 | 系统性文献综述 |
| `socratic` | "Guide my research on X" | 研究计划 + INSIGHT 收集 | 极高 | 不确定研究方向时 |
| `fact-check` | "Fact-check these claims" | 逐条声明验证报告 | 中 | 验证已有声明 |
| `lit-review` | "Do a literature review on X" | 带注释的文献目录 + 综合 | 中 | 文献综述 |
| `three-way-scan` | "Compare these papers in WHY/HOW/WHAT format" | 论文短名单 + 跨论文综合 | 低 | 快速比较多篇论文 |
| `review` | "Review this paper's research quality" | 研究质量评审报告 | 高 | 评估单篇论文质量 |

### 3.2 实战示例

**示例 1：苏格拉底引导模式（推荐新手）**
```
你: "I have a vague idea about AI's impact on higher education QA,
      but I'm not sure how to frame the research question. Can you guide me?"
```
Claude 会进入苏格拉底模式，通过 5-15 轮对话帮你澄清思路，最终形成聚焦的研究问题和方法论方向。

**示例 2：快速文献综述**
```
你: "Do a literature review on federated learning in healthcare"
```

**示例 3：事实核查**
```
你: "Fact-check these claims: [粘贴声明列表]"
```

**示例 4：系统性综述（PRISMA）**
```
你: "Do a systematic review on the effectiveness of ChatGPT in 
      programming education with PRISMA methodology"
```

### 3.3 关键 Agent 角色

- `research_question_agent` — 研究问题提炼
- `research_architect_agent` — 研究架构设计
- `bibliography_agent` — 参考文献管理（v3.6.5+ 支持文献库预加载）
- `synthesis_agent` — 研究结果综合
- `source_verification_agent` — 来源验证
- `devils_advocate_agent` — 魔鬼代言人（挑战假设）
- `socratic_mentor_agent` — 苏格拉底导师（v3.5.1+ 阅读检查探针层）

---

## 4. Academic Paper 论文写作

### 4.1 11 种模式详解

| 模式 | 触发方式 | 输出 | oversight | 适用场景 |
|------|---------|------|-----------|---------|
| `full` | "Write a paper on X" | 完整论文草稿（IMRaD 或学科适配格式） | 高 | 从零写论文 |
| `plan` | "Guide me through writing a paper" | 章节计划 + INSIGHT 收集（苏格拉底式） | 极高 | 不确定结构时 |
| `outline-only` | "Build a paper outline" | 详细大纲 + 证据图 | 高 | 只需要大纲 |
| `revision` | "I have a draft, here are reviewer comments" | 修订稿 + 逐点回复 | 高 | 根据审稿意见修订 |
| `revision-coach` | "Parse these reviewer comments into a roadmap" | 修订路线图 + 回复信骨架 | 中 | 解析审稿意见 |
| `abstract-only` | "Write an abstract for this paper" | 双语摘要（繁中+英）+ 关键词 | 中 | 只写摘要 |
| `lit-review` | "Turn this into a literature review paper" | 文献综述格式论文 | 中 | 写综述论文 |
| `format-convert` | "Convert to LaTeX" / "Convert citations to IEEE" | 格式转换后的文档 | 低 | 格式转换 |
| `citation-check` | "Check citations" | 引用错误报告 | 低 | 检查引用 |
| `disclosure` | "Generate an AI disclosure statement for NeurIPS" | 会议特定的 AI 使用声明 | 低 | 生成披露声明 |
| `rebuttal-audit` | "Audit my rebuttal draft against the reviews" | 回复草稿的覆盖度/遗漏/风险标记 | 低 | 审计回复信 |

### 4.2 实战示例

**示例 1：苏格拉底式规划**
```
你: "Guide me through writing a paper about demographic decline 
      and its impact on private universities in Taiwan"
```
Claude 会逐章引导你规划，而不是直接给你答案。

**示例 2：完整写作**
```
你: "Write a paper on how agentic AI is reshaping student 
      learning outcome measurement"
```

**示例 3：修订教练**
```
你: "I got these reviewer comments: [粘贴]
      Parse them into a revision roadmap for me"
```

**示例 4：格式转换**
```
你: "Convert my paper to LaTeX with APA 7.0 citations"
```

### 4.3 核心能力

- **Style Calibration（风格校准）**: 从你过去的作品学习你的写作风格
- **Writing Quality Check（写作质量检查）**: 捕捉机器生成文本的模式
- **LaTeX Hardening**: 专业排版输出
- **Anti-leakage Protocol（反泄露协议）**: 防止内容泄露
- **VLM Figure Verification**: 视觉模型验证图表

---

## 5. Academic Paper Reviewer 论文评审

### 5.1 6 种模式详解

| 模式 | 触发方式 | 输出 | oversight | 适用场景 |
|------|---------|------|-----------|---------|
| `full` | "Review this paper" | 5 份评审报告 + 编辑决定 + 修订路线图 | 高 | 完整同行评审 |
| `quick` | "Quick assessment of this paper" | 主编快速评估 + 关键问题列表 | 低 | 快速评估 |
| `guided` | "Guide me to improve this paper" | 苏格拉底式逐问题对话 | 极高 | 逐条改进指导 |
| `methodology-focus` | "Check the methodology" | 方法论深度评审 | 中 | 专注方法部分 |
| `re-review` | "Verify the revisions" | 修订验证清单 + 残余问题 | 中 | 验证修订是否充分 |
| `calibration` | "Calibrate this reviewer against my gold set" | 校准报告（FNR/FPR/AUC）+ 置信度披露 | 中 | 测量评审准确性 |

### 5.2 评审团队组成

- **EIC（主编）**: 综合裁决
- **R1（方法论评审）**: 深度检查方法论
- **R2（领域评审）**: 领域专业知识评估
- **R3（跨学科视角）**: 跨学科视角
- **Devil's Advocate（魔鬼代言人）**: 主动攻击论文弱点

### 5.3 评审质量评分

| 分数 | 决策 |
|------|------|
| ≥80 | Accept（接受） |
| 65-79 | Minor Revision（小修） |
| 50-64 | Major Revision（大修） |
| <50 | Reject（拒稿） |

### 5.4 实战示例

**示例 1：完整评审**
```
你: "Review this paper" [粘贴或上传论文]
```

**示例 2：方法论专注**
```
你: "Check the methodology of this paper" [粘贴论文]
```

**示例 3：修订验证**
```
你: "I revised the paper based on reviewer comments. 
      Verify the revisions" [粘贴修订稿和审稿意见]
```

---

## 6. Academic Pipeline 全流程编排

### 6.1 10 阶段管线

```
Stage 0: INIT — 初始化
    ↓
Stage 1: RESEARCH — 深度研究 (Deep Research)
    ↓  🧑 用户确认: RQ Brief + Methodology Blueprint
Stage 2: WRITE — 论文写作 (Academic Paper)
    ↓  🧑 用户确认: 大纲批准
Stage 2.5: INTEGRITY GATE — 完整性验证（强制，不可跳过）
    ↓  ✓ 机器检查 7 种失败模式 + 用户确认
Stage 3: REVIEW — 同行评审 (Paper Reviewer)
    ↓  🧑 用户确认: 编辑决定
Stage 3→4: Revision Coaching — 修订指导（可选，最多 8 轮苏格拉底对话）
    ↓
Stage 4: REVISE — 修订 (Academic Paper)
    ↓  🧑 用户确认: 修订内容
Stage 3': RE-REVIEW — 重新评审
    ↓  🧑 用户确认: 验证决定
Stage 3'→4': Residual Coaching — 残余问题指导（可选，最多 5 轮）
    ↓
Stage 4': RE-REVISE — 最终修订
    ↓  🧑 用户确认: 内容冻结
Stage 4.5: FINAL INTEGRITY — 最终完整性验证（强制，不可跳过）
    ↓  ✓ 零回归确认 + 用户确认
Stage 5: FINALIZE — 格式化输出
    ↓  🧑 用户选择: MD / DOCX / LaTeX / PDF
Stage 6: PROCESS SUMMARY — 流程总结 + 协作质量评估
```

### 6.2 决策检查点

每个 🧑 标记都是**决策型检查点**，用户必须确认才能继续：

| # | 阶段 | 用户决定什么 |
|---|------|-----------|
| 1 | Stage 1 | 确认研究问题简报 + 方法论蓝图 |
| 2 | Stage 2 | 批准大纲后开始起草 |
| 3 | Stage 3 | 编辑决定（接受/小修/大修/拒稿） |
| 4 | 3→4 | 修订策略（最多 8 轮苏格拉底对话，可跳过） |
| 5 | Stage 4 | 确认修订内容 |
| 6 | Stage 3' | 验证评审决定 |
| 7 | 3'→4' | 残余问题权衡（最多 5 轮，可跳过） |
| 8 | Stage 4' | 内容冻结 — 不再进入评审循环 |
| 9 | Stage 5 | 选择输出格式 |
| 10 | Stage 6 | 确认语言 + 协作质量回顾 |

### 6.3 完整性验证门（不可跳过）

**Stage 2.5 和 Stage 4.5** 是机器验证 + 用户确认的双重门：

检查 7 种 AI 研究失败模式（基于 Lu et al. 2026）：
1. **M1** — 实现 bug 通过 AI 自审
2. **M2** — 幻觉引用
3. **M3** — 幻觉实验结果
4. **M4** — 捷径依赖
5. **M5** — 实现 bug 被重构为新见解
6. **M6** — 方法论伪造
7. **M7** — 早期阶段框架锁定

### 6.4 实战触发

```
你: "I want to write a complete research paper about 
      how agentic AI is reshaping student learning outcome measurement"
```

这会触发完整 10 阶段管线。预算约 $4-6 API 费用，2-4 小时协作时间。

---

## 7. 费用与性能

### 7.1 各模式 Token 预算

| Skill / Mode | Input Tokens | Output Tokens | 预估费用 |
|-------------|-------------|--------------|---------|
| `deep-research` socratic | ~30K | ~15K | ~$0.60 |
| `deep-research` full | ~60K | ~30K | ~$1.20 |
| `deep-research` systematic-review | ~100K | ~50K | ~$2.00 |
| `academic-paper` plan | ~40K | ~20K | ~$0.80 |
| `academic-paper` full | ~80K | ~50K | ~$1.80 |
| `academic-paper-reviewer` full | ~50K | ~30K | ~$1.10 |
| `academic-paper-reviewer` quick | ~15K | ~8K | ~$0.30 |
| **Full pipeline (10 stages)** | **~200K+** | **~100K+** | **~$4-6** |
| + Cross-model verification | +~10K | +~5K | +~$0.60-1.10 |

*基于约 15,000 词论文、约 60 条引用。实际费用因论文长度、修订轮数、对话深度而异。*

### 7.2 推荐设置

| 设置 | 作用 | 如何开启 |
|------|------|---------|
| **Skip Permissions** | 绕过每次工具使用确认，实现不间断自主执行 | `claude --dangerously-skip-permissions` |
| **Agent Team** (可选) | 启用 TeamCreate/SendMessage 工具手动协调多 Agent | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |

> ⚠️ Skip Permissions 会禁用所有工具使用确认对话框，仅在可信环境中使用。

---

## 8. 进阶配置

### 8.1 环境变量开关

| 变量 | 版本 | 作用 |
|------|------|------|
| `ARS_CROSS_MODEL` | v3.0 | 启用跨模型验证（GPT-5.4 Pro 或 Gemini 3.1 Pro） |
| `ARS_SOCRATIC_READING_PROBE=1` | v3.5.1 | 激活苏格拉底阅读检查探针 |
| `ARS_PASSPORT_RESET=1` | v3.6.3 | 每个 FULL 检查点成为上下文重置边界 |
| `ARS_CLAIM_AUDIT=1` | v3.8 | 启用声明忠实度审计 |
| `ARS_VERIFICATION_CACHE_PATH` | v3.11 | 自定义引用验证缓存路径 |

### 8.2 跨模型验证

```bash
# 设置第二个模型的 API Key
export OPENAI_API_KEY="sk-your-key-here"        # GPT-5.4 Pro
# 或: export GOOGLE_AI_API_KEY="AIza-your-key-here"  # Gemini 3.1 Pro

# 选择跨验证模型
export ARS_CROSS_MODEL="gpt-5.4-pro"

# 正常运行 Claude Code，跨验证自动激活
claude
```

启用后变化：
- 完整性验证：30% 样本由第二模型独立验证
- 魔鬼代言人：增加跨模型独立批评
- 费用增加：约 $0.60-1.10

### 8.3 文献库预加载 (v3.6.4+)

如果你有整理的文献库（Zotero、Obsidian、PDF 文件夹），可以预加载到 Material Passport：

```bash
pip install -r requirements-dev.txt

# 三种参考适配器
python scripts/adapters/zotero.py --input my-zotero-export.json --passport passport.yaml --rejection-log rejection_log.yaml
python scripts/adapters/obsidian.py --input ~/Obsidian/Lit\ Notes --passport passport.yaml --rejection-log rejection_log.yaml
python scripts/adapters/folder_scan.py --input /path/to/pdfs --passport passport.yaml --rejection-log rejection_log.yaml
```

ARS Phase 1 的 `bibliography_agent` 和 `literature_strategist_agent` 会优先读取你的文献库，不足时再搜索外部数据库。

### 8.4 引用验证缓存 (v3.11)

- 自动创建在 `~/.cache/ars/verification.db`
- 90 天 TTL
- 可自定义路径：`ARS_VERIFICATION_CACHE_PATH=/your/path.db`
- 手动失效：`/ars-cache-invalidate <citation_key>`

### 8.5 会话恢复 (v3.6.3+)

长管线可能跨越多天。通过 Material Passport 恢复：

```
# 在检查点处复制 passport hash
[PASSPORT-RESET: hash=abc123, stage=2, next=2.5]

# 新会话中恢复
resume_from_passport=abc123
# 或指定阶段: resume_from_passport=abc123 stage=3 mode=full
```

---

## 9. 实战建议

### 9.1 新手入门路径

```
第 1 步: 安装 Plugin → /plugin install academic-research-skills
第 2 步: 测试安装 → /ars-plan，描述一个论文想法
第 3 步: 快速体验 → /ars-lit-review "你的研究主题"
第 4 步: 深度体验 → 用 socratic 模式引导研究
第 5 步: 完整流程 → 触发 full pipeline
```

### 9.2 模式选择决策树

```
你想做什么？
  ├── 探索研究方向 → deep-research / socratic
  ├── 快速了解主题 → deep-research / quick
  ├── 系统性综述 → deep-research / systematic-review
  ├── 写论文
  │     ├── 不确定结构 → academic-paper / plan
  │     ├── 已有大纲 → academic-paper / full
  │     └── 只写摘要 → academic-paper / abstract-only
  ├── 审论文
  │     ├── 完整评审 → paper-reviewer / full
  │     ├── 快速看看 → paper-reviewer / quick
  │     └── 验证修订 → paper-reviewer / re-review
  └── 全流程 → pipeline / full
```

### 9.3 关键提醒

1. **ARS 不是替你写论文** — 它处理苦力活，你负责思考
2. **Human-in-the-loop 是设计前提** — 每个阶段都要你确认
3. **完整性门不可跳过** — 这是质量保证的底线
4. **苏格拉底模式不会给你答案** — 它会问你问题，帮你理清思路
5. **风格校准学习你的声音** — 但它不帮你隐藏使用 AI 的事实
6. **引用验证自动运行** — v3.11+ 交叉检查 4 个数据库
7. **长会话用 passport 恢复** — 不用从头再来

### 9.4 与 Experiment Agent 配合使用

如果研究涉及实验（代码或人体实验）：

```
ARS Stage 1 RESEARCH → 产生 RQ Brief + Methodology Blueprint
        ↓
  experiment-agent → 运行/管理实验 → 验证结果
        ↓
ARS Stage 2 WRITE → 用验证后的实验结果写论文
```

在 ARS Stage 1 暂停，用 experiment-agent 运行实验，然后将结果（带 Material Passport）带回 ARS Stage 2。

---

## 参考资源

| 资源 | 链接 |
|------|------|
| 项目主页 | https://github.com/Imbad0202/academic-research-skills |
| 架构文档 | `docs/ARCHITECTURE.md` |
| 安装指南 | `docs/SETUP.md` |
| 性能与成本 | `docs/PERFORMANCE.md` |
| 快速开始 | `QUICKSTART.md` |
| 模式注册表 | `MODE_REGISTRY.md` |
| 展示案例 | `examples/showcase/` |
| 配套 Experiment Agent | https://github.com/Imbad0202/experiment-agent |
| Codex CLI 版本 | https://github.com/Imbad0202/academic-research-skills-codex |
| 作者使用指南（EN） | https://open.substack.com/pub/edwardwu223235/p/academic-writing-shouldnt-be-a-solo |
| 作者使用指南（繁中） | https://open.substack.com/pub/edwardwu223235/p/ai |

---

> **一句话总结**: ARS 是 Claude Code 生态中最成熟的学术研究 Skill 套件。安装只需 30 秒（`/plugin install`），然后通过自然语言触发 27 种模式之一。核心原则是 **Human-in-the-loop** — AI 处理文献检索、引用格式化、数据验证等苦力活，你专注于定义问题、选择方法、解释数据含义。
