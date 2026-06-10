---
name: note-organizer
description: >
  This skill organizes unstructured input (inspirations, articles, links, images, hypotheses, resource discoveries)
  into structured markdown notes and saves them to the user's inbox directory under ContextStack framework conventions.
  It should be used when the user pastes or shares content with intent to save, organize, or capture — including
  WeChat articles, tweets, URLs, screenshots, quick ideas, unverified hypotheses, and tool/resource discoveries.
  Trigger phrases include: "整理一下", "保存笔记", "记录一下", "收藏", or any content drop with "帮我整理".
---

# Note Organizer — 智能笔记整理

## Purpose

将非结构化的输入（灵感、文章、链接、图片、假设、工具发现）自动识别类型，套用对应模板，
输出结构化 Markdown 笔记，保存到 ContextStack 框架的 `02-Knowledge/inbox/` 目录。

## Trigger Conditions

当用户执行以下任一操作时激活此 Skill：
- 粘贴一段文字并附带"整理""保存""记录""收藏"等意图
- 分享链接并希望保存
- 输入灵感/闪念（即使没有明确说"整理"）
- 提出待验证的想法/假设
- 分享工具/资源发现
- 发送图片并说"这个记一下"

## Content Type Classification

收到内容后，首先分类。按以下决策树判断：

1. **包含 URL 且主要内容来自该链接** → `article`（文章/帖子）
2. **只有一个 URL，无明显文章内容** → `link`（链接收藏）
3. **以"如果...会怎样""能不能...""是否可能..."开头** → `hypothesis`（待验证假设）
4. **短句/片段，表达突发想法** → `idea`（灵感闪念）
5. **介绍某个工具/平台/资源** → `resource`（资源发现）

如果内容模糊，按主导特征分类。分类后有疑问，简要向用户确认分类是否正确。

## Categories (领域分类)

分类使用以下标准领域标签：
- `AI/技术` — AI、编程、技术工具
- `投资理财` — 股票、基金、券商、ETF
- `职业发展` — 求职、面试、技能提升
- `生活工具` — 效率工具、生活技巧
- `学习方法` — 学习策略、认知方法论
- `网络/通信` — 网络设备、协议、通信技术
- `嵌入式` — 嵌入式系统、MCU、RTOS
- `未分类` — 无法归入以上类别

领域分类用于 inbox index 的归档列以及笔记内 `> 分类:` 字段。

## File Naming Convention

```
{type}-{date}-{slug}.md
```

Rules:
- **type**: `article`, `idea`, `link`, `hypothesis`, `resource`
- **date**: `YYYYMMDD`（当天日期）
- **slug**: 英文小写、连字符分隔、3-8个词、描述核心主题
- **示例**: `article-20260526-ai-agent-beginner-guide.md`

> **注意**: 文件名不包含中文，这是框架约定。标题（文件内 `# Title`）使用中文。

## Workflow

### Step 1: Classify

分析用户输入，确定内容类型（article/idea/link/hypothesis/resource）。

### Step 2: Load Template

从 `assets/templates/` 加载对应类型模板：
- `assets/templates/article.md` — 文章类
- `assets/templates/idea.md` — 灵感类
- `assets/templates/link.md` — 链接类
- `assets/templates/hypothesis.md` — 假设类
- `assets/templates/resource.md` — 资源类

### Step 3: Fill Template

根据用户输入内容，填充模板中的所有 `{{PLACEHOLDER}}` 字段：

- **TITLE**: 中文标题，简洁准确概括核心内容
- **DATE**: 当天日期 YYYY-MM-DD
- **CATEGORY**: 从分类列表中选择最匹配的
- 其他字段：从用户输入中提取，无法确定的标注 `（待补充）` 或合理推断

**填充原则**：
- 优先使用用户原文中的表述
- 链接类：如果 URL 可访问，尝试 fetch 页面获取标题和摘要
- 核心要点/摘要：用 3-5 条要点概括，不是全文复制
- 个人思考/关联信息：如果用户未提供，标注 `（待补充）`
- 标签：用 3-5 个 `#tag` 标记

### Step 4: Save File

写入 `d:\MyFile\AI\ContextStack\02-Knowledge\inbox\{filename}.md`。

写入前检查：
- 文件名不与已有文件重复
- 如果 slug 重复，在末尾追加 `-2`, `-3` 等

### Step 5: Update Inbox Index

更新 `d:\MyFile\AI\ContextStack\02-Knowledge\inbox\index.md`：

在处理日志表格中追加一行：
```markdown
| {DATE} | {来源简述} | `{filename}.md` | {CATEGORY} |
```

> **插入位置**: 在 `处理日志` 表格的最后一个数据行之后、分隔行 `| — | — | — | — |` 之前。

### Step 6: Confirm

向用户简要报告：
1. 识别的内容类型
2. 保存的文件名和路径
3. 询问是否需要调整分类或补充内容

## Handling Special Cases

### 图片输入
- 图片内容可能无法直接读取
- 请用户补充文字描述
- 类型暂定为 `resource` 或询问用户意图

### 多段混合内容
- 如果用户同时发送文章链接 + 个人评论 → 以文章为主，评论填入"个人思考"
- 如果明显是多个独立条目 → 询问用户是否拆分保存

### 内容过短
- 如果输入只有一句话 → 可能是 `idea` 类型
- 尝试从语境中推断更多信息填充模板

### 微信文章
- URL 可能无法直接访问（微信封闭生态）
- 基于用户粘贴的内容整理，标注来源为"微信公众号"

## Framework Conventions

严格遵循 ContextStack 框架约定：
- **文件名**: 英文小写 + 连字符
- **文件内容**: 中文
- **Inbox 规则**: 产物留在 inbox/，不主动移动到其他目录
- **Index 维护**: 每次新增文件后更新 inbox/index.md
- **归档**: 用户明确要求归档时，在 `inbox/archive/archive-log.md` 登记，不创建单独归档文件

## Template Reference

All templates are stored in `assets/templates/`. Each template file contains the full markdown structure with `{{PLACEHOLDER}}` fields.
Load the relevant template via `read_file` when processing a note, fill in the placeholders, then save to inbox.
