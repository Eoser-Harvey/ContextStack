# PPT 制作 Skills 汇总

> 收集日期: 2026-05-24  
> 分类: AI / 技术  
> 来源: 用户分享（GitHub 链接汇总）

---

## 总览

| Skill | 产出格式 | 安装命令 | 特色 |
|-------|----------|----------|------|
| **guizang-ppt-skill** | HTML 单文件 | `npx skills add op7418/guizang-ppt-skill` | 双视觉系统（杂志风+瑞士风），22种锁定版式 |
| **frontend-slides** | HTML 单文件 | `/plugin marketplace add zarazhangrui/frontend-slides` | 12种预设风格，PPT转HTML，渐进式加载 |
| **magic-slide** | HTML 单文件 | `npx skills add daniel-style/magic-slide` | Magic Move转场，PipeLLM图片生成，Web搜索 |
| **huashu-design** | HTML + PPTX + MP4 + GIF | `npx skills add alchaincyf/huashu-design` | 全能设计：原型/动画/信息图/评审，品牌资产协议 |
| **html-ppt-skill** | HTML 单文件 | `npx skills add lewislulu/html-ppt-skill` | 36主题×31布局×47动画，演讲者模式 |
| **ppt-master** | **原生可编辑 PPTX** | `npx skills add hugohe3/ppt-master` | 产出真实PPTX，支持动画/配音/模板复制 |

---

## 详细对比

### 1. guizang-ppt-skill（归藏）

| 属性 | 内容 |
|------|------|
| **作者** | 歸藏 (@op7418) |
| **产出** | HTML 单文件横向翻页 PPT、配图、多平台封面 |
| **视觉系统** | Style A: 电子杂志×电子墨水（叙事） / Style B: 瑞士国际主义（事实） |
| **版式** | Style A: 10种布局 / Style B: 22种锁定版式 |
| **主题色** | A: 5套电子墨水 / B: 4套瑞士高饱和锚点色 |
| **特色** | Codex可调用GPT-Image生成配图，多平台封面（公众号/小红书/视频号） |
| **适合** | 线下分享、个人风格演讲、观点表达 |

### 2. frontend-slides

| 属性 | 内容 |
|------|------|
| **作者** | @zarazhangrui |
| **产出** | HTML 单文件（零依赖） |
| **风格** | 12种预设（暗色4+亮色4+特殊4），含Neon Cyber/Terminal Green等 |
| **特色** | PPT转HTML（保留图片内容）、视觉风格发现（生成预览让你选） |
| **架构** | 渐进式加载（SKILL.md仅180行，按需加载子文件） |
| **部署** | 支持 Vercel 部署 + PDF 导出 |

### 3. magic-slide

| 属性 | 内容 |
|------|------|
| **作者** | @daniel-style |
| **产出** | HTML 单文件 |
| **核心亮点** | **Magic Move转场**（FLIP动画，元素在页面间平滑过渡） |
| **AI能力** | PipeLLM图片生成 + PipeLLM Web搜索（研究支撑） |
| **工作流** | 10步流程（需求→搜索→大纲→设计→原型→视觉→生成→合并→注入→预览） |

### 4. huashu-design（画设）

| 属性 | 内容 |
|------|------|
| **作者** | @alchaincyf |
| **产出** | HTML / PPTX / MP4 / GIF / PDF |
| **能力** | 交互原型、演讲PPT、时间轴动画、信息图、设计评审、品牌顾问 |
| **核心机制** | 品牌资产协议（5步硬流程）、Junior Designer工作流、反AI slop规则 |
| **跨Agent** | Claude Code / Cursor / Codex / OpenClaw / Hermes 通用 |

### 5. html-ppt-skill

| 属性 | 内容 |
|------|------|
| **作者** | @lewislulu |
| **产出** | HTML 单文件 |
| **规模** | **36主题 × 15完整模板 × 31布局 × 47动画** |
| **演讲者模式** | 按 S 键弹出演讲窗口（当前页/下一页/逐字稿/计时器） |
| **特色** | iframe隔离预览、零构建、中英文一等公民 |

### 6. ppt-master

| 属性 | 内容 |
|------|------|
| **作者** | Hugo He (@hugohe3) |
| **产出** | **原生可编辑 PPTX**（真实DrawingML形状、文本框、图表） |
| **核心差异** | 唯一产出可在PowerPoint中逐元素编辑的PPTX |
| **输入** | PDF / DOCX / URL / Markdown |
| **特色** | 模板复制、动画、配音（edge-tts+声音克隆）、视频导出 |
| **依赖** | Python 3.10+ |

---

## 选型指南

| 你的需求 | 推荐 |
|----------|------|
| 需要真实PPTX，后续可编辑 | **ppt-master** ⭐ |
| 个人风格演讲，线下分享 | **guizang-ppt-skill** |
| 快速创建美观Web演示 | **frontend-slides** |
| 需要流畅动画效果 | **magic-slide** |
| 全能设计（PPT+动画+原型+信息图） | **huashu-design** |
| 最多主题和布局选择 | **html-ppt-skill** |

---

## 安装汇总

```bash
# guizang-ppt-skill（归藏）
npx skills add https://github.com/op7418/guizang-ppt-skill --skill guizang-ppt-skill

# magic-slide
npx skills add daniel-style/magic-slide

# huashu-design（画设）
npx skills add alchaincyf/huashu-design

# html-ppt-skill
npx skills add https://github.com/lewislulu/html-ppt-skill

# ppt-master
npx skills add hugohe3/ppt-master

# frontend-slides（Claude Code 插件市场）
/plugin marketplace add zarazhangrui/frontend-slides
/plugin install frontend-slides@frontend-slides
```
