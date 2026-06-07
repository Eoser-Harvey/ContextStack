# 图解 Skill — AI 提效实战指南（宝玉）

> 来源: GitHub [JimLiu/Illustrated-Agent-Skills](https://github.com/JimLiu/Illustrated-Agent-Skills)  
> 作者: 宝玉（JimLiu）  
> 收集日期: 2026-06-05  
> 分类: AI/技术 / Skill设计 / AI提效

---

## 项目简介

《图解 Skill —— AI 提效实战指南》的配套资源仓库。包含：
- 附录全文（术语表 / 安装指南 / 国内平台 / 完整技能）
- 各章配图与对应提示词
- 写作工作流技能完整版
- 章节示例代码与数据
- 生成本书插图所用的技能本身

**购买链接**:
- 京东: https://u.jd.com/RDY9YwC
- 电子书: https://www.ituring.com.cn/book/3616

---

## 仓库核心内容

### 1. 写作工作流技能模板（skill-templates/）

| 技能 | 作用 | 适用场景 |
|------|------|----------|
| content-analyzer.md | 素材深度分析 | 文章、推文、视频文稿等 |
| outliner.md | 大纲生成（多方案） | 生成3-5个差异化大纲 |
| writer.md | 写作 | 正式写作 |
| writing-style.md | 写作风格基调约束 | 保持统一风格 |
| article-polish.md | 文章润色 | 打磨稿件 |
| article-illustrator.md | 文章配图（简化版） | 自动配图 |
| meeting-analyzer.md | 会议素材分析 | 会议内容提取 |
| meeting-minutes.md | 会议纪要 | 结构化纪要 |

### 2. 完整可用技能（skills/）

| 技能 | 说明 | 亮点 |
|------|------|------|
| **book-illustrator** | 本书所有插图生成技能 | 一次分析整篇书稿、批量识别配图位置、subagent并行出图、自动回写书稿 |
| **content-analyzer** | 素材深度分析 | 支持多种内容类型，理解核心观点、批判性评估、提取写作素材 |
| **interview-analysis** | 访谈内容分析 | 播客/视频访谈→结构化写作素材包和提纲 |
| **interview-writing** | 访谈实录写作 | 访谈分析素材→正式文章，保留问答对话感 |
| **outliner** | 科技专栏提纲生成 | 3-5个差异化大纲方案，优先包含故事驱动型 |
| **adversarial-polish** | 多轮对抗式稿件打磨 | "批评→改写→综合→盲评"循环（⚠️仅供学习，当前平台不支持sub-agent隔离） |

### 3. 开源技能集（baoyu-skills）

**仓库**: https://github.com/JimLiu/baoyu-skills

20+ 个通用 Skill，适用于 Claude Code、Codex 等 Agent，覆盖三类场景：

**内容生成类**:
- 文章配图、信息图、图表、封面图
- 幻灯片、知识漫画
- Markdown 转 HTML、翻译

**AI 生成后端类**:
- YouTube 字幕提取
- 图片压缩

**日常效率类**:
- 发布到微信公众号/微博/X

**安装方式**:
```bash
npx skills add jimliu/baoyu-skills
# 或
/plugin marketplace add JimLiu/baoyu-skills
```

> ⚠️ 不要一次性安装全部 skills。每个启用的 skill 都会占用 Agent 上下文，装得越多越容易变慢变乱。只挑当前工作流真正会用到的几个安装。

### 4. 数据分析技能演化示例（examples/chapter-07）

`data-analysis-v1` → `v2` → `v3` 三次迭代版本，展示一个技能是怎么被"用"出来的。

---

## 附录要点

### 附录 B: 各平台技能安装指南

支持平台：
- Claude.ai
- Claude Code
- VS Code
- OpenCode

### 附录 C: 国内模型 API 平台

| 平台 | 说明 |
|------|------|
| 百炼 | 阿里云 |
| Kimi | 月之暗面 |
| 智谱 | 智谱AI |
| DeepSeek | 深度求索 |
| 火山方舟 | 字节跳动 |
| OpenClaw | 一键部署 |

---

## 与 ContextStack 的关联

**直接可用的技能**:
- `content-analyzer` → 替代当前的"总结文章"流程，更结构化
- `outliner` → 生成框架文档大纲
- `meeting-analyzer` + `meeting-minutes` → 替代会议纪要整理
- `article-polish` → 打磨框架内的文档

**Skill 设计方法论借鉴**:
- 宝玉的 Skill 设计哲学：每个 Skill 职责单一、可组合
- 写作工作流：素材分析 → 大纲 → 写作 → 润色 → 配图（五步流水线）
- 对抗式打磨：批评→改写→综合→盲评（学术同行评审模式）

**baoyu-skills 通用技能集**:
- 可直接安装到 Claude Code / Codex
- 建议优先安装：content-analyzer、outliner、writer、article-polish
- 与 ContextStack 的归档流程互补

---

## 行动建议

| 优先级 | 行动 |
|--------|------|
| ⭐ P0 | 阅读 `附录D` 完整版技能参考，理解 Skill 设计思路 |
| ⭐ P1 | 从 `skill-templates/` 挑 2-3 个模板试用 |
| ⭐ P2 | 安装 `baoyu-skills` 中与当前工作流相关的技能 |
| ⭐ P3 | 购买完整图书，系统学习 Skill 设计方法论 |

---

**最后更新**: 2026-06-05
