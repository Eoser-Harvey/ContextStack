---
title: Tailored Resume Generator 使用说明（定制简历生成器）
name: tailored-resume-generator
description: 当用户要针对某个具体职位生成/定制简历，需要分析职位描述（JD）、提取关键词、映射个人经验、做 ATS 优化、量化成果、给出差距分析与面试建议时使用。触发词：定制简历、简历改写、投递某岗位、针对 JD 优化简历、ATS 通过率。
source: "https://github.com/composio-community/awesome-codex-skills/tree/master/tailored-resume-generator"
tags:
  - resume
  - job-search
  - ats
  - career
created: 2026-08-21
---

# Tailored Resume Generator 使用说明

> **项目来源**：[composio-community/awesome-codex-skills](https://github.com/composio-community/awesome-codex-skills/tree/master/tailored-resume-generator)
> **本体**：[[SKILL]]
> **收录日期**：2026-08-21

## 一句话说明

一个**简历定制工作流**：输入「职位描述 + 你的背景/现有简历」，输出一份针对该岗位、通过 ATS 筛选、突出量化成果的定制简历，并附差距分析与面试建议。

## 核心能力（7 步工作流）

| # | 步骤 | 做什么 |
|:--|:-----|:-------|
| 1 | 收集信息 | 解析 JD（公司/岗位/职责）+ 你的背景/现有简历 |
| 2 | 分析 JD | 提取硬性要求、关键技能、软技能、行业知识、ATS 关键词 |
| 3 | 映射经验 | 逐条匹配经验，找迁移技能，标注差距与亮点 |
| 4 | 结构化简历 | summary / 技能 / 经历 / 教育，量化成果 |
| 5 | ATS 优化 | 标准标题、关键词自然融入、无表格图片 |
| 6 | 格式化输出 | Markdown / 纯文本 / Word/PDF 建议 |
| 7 | 附加建议 | 优势分析、差距分析、面试准备、cover letter 钩子 |

## 使用方式

**基本用法**（粘贴 JD + 背景）：

```
我正在投这个岗位：

[粘贴职位描述]

我的背景：
- 8 年嵌入式开发经验（新华三 + 爱博精电）
- 自研 RTOS、TSN 六协议、DSP 优化
- C / Python
```

**带现有简历**：粘贴 JD + 你的现有简历，让 skill 在你现有简历基础上定制。

**转岗场景**：说明从 A 转到 B，列出可迁移经验。

## 对你求职的针对性

你当前在活跃求职（已面 7 家），这个 skill 补的是 `interview-prep` 没有的**简历定制**环节：

- `interview-prep`：输入公司名 → 生成面试准备清单（8 模块）
- `tailored-resume-generator`：输入 JD → 生成定制简历 + ATS 优化 + 差距分析

两者配合：**先用它定制简历投递，再用 interview-prep 准备面试**。

## 关键要点（Gotchas）⭐

- **量化成果是核心**：数字、百分比、规模、时间，这是 ATS 和人眼都吃的一套。
- **关键词用 JD 原词**：不要自己换说法，ATS 是字面匹配。
- **不用第一人称**（I/me/my），不用"references available upon request"。
- **ATS 安全格式**：标准标题（Professional Experience/Education/Skills），避免表格、图形、页眉页脚。
- **一岗一版**：不要一份简历投所有岗，同类岗位也要微调。

## 参考

- 本体原文：[[SKILL]]
- 项目仓库：https://github.com/composio-community/awesome-codex-skills
- 相关：[[../interview-prep/interview-prep使用说明|面试准备]]、[[../index|Skills 库总览]]

---

**标签**：`#resume` `#job-search` `#ats` `#career`
