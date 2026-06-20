# Ian Xiaohei Illustrations — 小黑怪诞正文配图 Skill

- **项目**: [helloianneo/ian-xiaohei-illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations)
- **作者**: Ian (伊恩) — 产品设计师 / 一人公司实践者 / AI Builder
- **类型**: Codex Skill
- **标签**: `illustration` `content-creation` `codex-skill` `visual-design`

---

## 一句话总结

把中文文章里的判断、流程、状态和隐喻，变成一张张白底、手绘、怪诞但清爽的正文配图。不是通用插画，而是**把文章里的一个关键认知动作画出来**。

---

## 核心定位

| 维度 | 说明 |
|------|------|
| **目标** | 为中文文章/帖子/博客/Notion文档生成正文配图 |
| **不是** | 通用插画prompt、PPT信息图、商业海报、儿童卡通 |
| **核心能力** | 先理解文章认知锚点，再选一个判断/流程/结构/状态/隐喻画成图 |
| **输出** | 16:9横版PNG，保存到 `assets/<article-slug>-illustrations/` |

---

## 视觉风格

- **纯白背景**，无纸纹、米色、阴影、渐变
- **黑色手绘线稿**，细线，轻微抖动
- **大量留白**，主体只占画面40%-60%
- **少量红橙蓝中文手写批注**
- **一张图只表达一个核心动作/结构/状态/隐喻**
- **小黑必须参与核心动作**，不能只是装饰
- **怪诞、有创意、清爽**，不幼稚、不卖萌

### 小黑IP

- 黑色实心、白点眼、细腿、空表情
- 不是吉祥物/贴纸/装饰物
- 是正在认真参与系统运转的**荒诞工作者**

---

## 使用方式

### 安装

```bash
git clone https://github.com/helloianneo/ian-xiaohei-illustrations.git
cp -R ./ian-xiaohei-illustrations/ian-xiaohei-illustrations "${CODEX_HOME:-$HOME/.codex}/skills/"
```

### 只做配图规划

```
Use $ian-xiaohei-illustrations 先不要生图。
请分析下面这篇文章哪里值得配图，输出5张左右的shot list。
每张图写清楚：放在哪段后、主题、核心意思、结构类型、小黑在做什么、建议中文标注词。

<粘贴文章>
```

### 直接生成正文配图

```
Use $ian-xiaohei-illustrations 把下面这篇文章生成4张小黑怪诞正文配图。
要求：16:9横版、纯白背景、黑色手绘线稿、少量红橙蓝中文手写批注。

<粘贴文章>
```

### 为单个概念生成一张图

```
Use $ian-xiaohei-illustrations 为"信任不是喊出来的，而是一块证据一块证据铺过去"生成一张正文配图。
画面要怪诞但清爽，小黑必须承担核心动作。
```

---

## 工作流程

1. 读取文章/Markdown/Notion内容/截图或用户给的主题
2. 提炼核心观点、认知转折、流程结构和适合视觉化的段落
3. 输出shot list：每张图只选一个认知锚点
4. 为每张图选择结构类型：Workflow、系统局部、前后对比、角色状态、概念隐喻、方法分层、地图路线、小漫画分镜
5. 重新发明一个低科技、怪诞但成立的物理隐喻
6. 让小黑承担核心动作
7. 每张图单独调用图像模型生成
8. QA检查：白底、留白、小黑动作、中文标注、非PPT感、非旧案例复刻
9. 保存最终PNG，报告用途和路径

---

## 示例效果

文章展示了8张示例图：
- 两个断点
- 按目的分拣
- 一鱼多吃
- 承接路径
- 信息井
- 想法压机
- 内容发酵
- 信任桥

---

## 注意事项

- 图片里的中文文字越短越稳定
- 每张图只讲一个核心结构，不要把文章做成说明书
- 小黑必须承担核心动作；如果去掉小黑画面仍然完全成立，说明小黑太装饰了
- 示例图只用于校准线条密度/留白/颜色克制/小黑参与方式，不要复刻构图
- AI图像模型可能出现错字、幻觉标签、风格漂移或多余标题，生成后需要检查
- 如果中文错字严重，优先减少标注词并重生成

---

## 相关项目

| 项目 | 说明 |
|------|------|
| [Ian Handdrawn PPT](https://github.com/helloianneo/ian-handdrawn-ppt) | 中文手绘技术PPT-style页面图生成Skill |
| [Awesome Claude Code Skills](https://github.com/helloianneo/awesome-claude-code-skills) | Claude Code Skills / Agents / Plugins精选合集 |
| [Obsidian + Claude AI Second Brain](https://github.com/helloianneo/obsidian-ai-second-brain) | Obsidian + Claude AI个人知识库搭建指南 |

---

## 对ContextStack的借鉴价值

1. **认知锚点可视化**：把抽象概念变成具象图像，与ARS的苏格拉底引导模式互补
2. **风格一致性**：通过Skill固化视觉语言，确保输出风格统一
3. **Shot List工作流**：先规划再执行，避免盲目生成
4. **QA Checklist**：生成后检查清单，保证质量

---

> **一句话**: 这是一个把中文知识内容变成怪诞手绘配图的Codex Skill。核心不是"配一张图"，而是把文章里的一个关键认知动作画出来。风格独特（小黑IP+纯白手绘+少量彩色批注），适合知识型/方法论内容的正文配图。
