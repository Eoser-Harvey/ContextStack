# 写给 Codex 小白用户的全网最详细教程 — MaynorAI

> 来源: GitHub [xianyu110/gpt-codex](https://github.com/xianyu110/gpt-codex)  
> 作者: MaynorAI  
> 更新日期: 2026-04-27  
> 收集日期: 2026-05-30  
> 分类: AI/技术 / 编程工具 / Codex

---

## 文章定位

**目标读者**: 完全不懂 Codex 的小白用户  
**核心目标**: 从 0 到 1 真正把 Codex 用起来  
**文章特点**:
- 图片全部保留
- 重点信息加粗
- 表格化呈现
- 补充 GPT-5.5 最新官方信息

---

## 一、什么是 Codex？

### 1.1 核心定义

**Codex 是 OpenAI 对标 Claude Code 的编程 Agent 产品。**

不是只会聊天的 AI，而是**能围绕项目目录、文件、任务目标持续干活的 AI 助手**。

| 特性 | Codex | Claude Code |
|------|-------|-------------|
| 开发商 | OpenAI | Anthropic |
| 底层模型 | GPT-5.5 / GPT-5.3-codex | Claude Opus 4.6 |
| 定位 | 编程 Agent（趋近通用 Agent） | 编程 Agent |

**关键区别**:
- 更像**工作流工具**
- 会**围绕任务持续推进**
- 重点不是回答一句，而是**把一件事往前做**

### 1.2 为什么编程 Agent 重要？

> "编程 Agent 正在从'辅助工具'，变成一种新的通用生产力接口。"

所有信息化成果都沉淀在：代码、软件、接口、自动化流程、系统配置、数据处理链路。

**AI 正在通过代码，开始接管越来越多的实际工作流程。**

### 1.3 GPT-5.5 最新定位（2026-04-23 发布）

| 维度 | 旧认知 | GPT-5.5 最新补充 |
|------|--------|------------------|
| 主打模型 | GPT-5.3-codex | **GPT-5.5 已成为最新旗舰** |
| 模型风格 | 纯编程特化 | **强推理 + 强执行 + 更稳的工具使用** |
| 适合场景 | 代码生成、重构 | **复杂工程、长上下文、多阶段任务** |
| 对小白意义 | 专业编码工具 | **会规划、会执行、会复盘的工程负责人** |

**核心变化**: GPT-5.3-codex 像"代码工人"，GPT-5.5 像"工程负责人"。

### 1.4 会员权限

| 会员类型 | Codex 可用模型 |
|----------|----------------|
| Plus / Pro / Business / Enterprise | ✅ GPT-5.5 可在 ChatGPT 和 Codex 中使用 |
| Edu / Go | ✅ 官方列入 Codex 可用范围 |
| 免费用户 | ⚠️ 未明确包含，以账号内模型列表为准 |

---

## 二、如何获取 Codex

### 2.1 方式一：官网订阅（需自备魔法）

- 充值链接: https://maynorai.jichiyun.sbs/buy/7
- 特点: 路径直、理解成本低、更接近官方体验

### 2.2 方式二：第三方中转（无需魔法）

| 方案 | 说明 | 链接 |
|------|------|------|
| 国内官网入口 | 进入 Codex 国内站登录和配置 | https://codex.chatgpt-plus.top/login |
| 备用网址 | 主入口不稳定时使用 | https://codex2.chatgpt-plus.top/login |
| Codex&GPTimage2 套餐 | 第三方中转套餐 | https://maynorai.jichiyun.sbs/buy/30 |
| 配置中转 API | 配合 cc-switch，每天 150 刀额度 | https://maynorai.jichiyun.sbs/buy/13 |

### 2.3 方式三：安装 cc-switch

| 步骤 | 说明 | 链接 |
|------|------|------|
| 1. 下载安装 | GitHub 自行安装 | https://github.com/farion1231/cc-switch/releases/ |
| 2. 配置中转 API | 第三方中转 | https://maynorai.jichiyun.sbs/buy/13 |
| 3. 详细配置教程 | 飞书文档 | https://ai.feishu.cn/wiki/JnefwEQRKiNyg6kTnN4cNphnnSh |
| 4. 完整上手教程 | 飞书文档 | https://my.feishu.cn/wiki/Vjulwif06izNiMkPor0cM9uYn1e |

### 2.4 下载安装

**官方入口**: https://chatgpt.com/codex

**Mac**: App Store 搜索 Codex，或下载 dmg:
- https://persistent.oaistatic.com/codex-app-prod/Codex.dmg

**Windows**: 微软商店，或夸克网盘:
- https://pan.quark.cn/s/0f1763fe2ac9?pwd=rTQw
- 系统要求: Windows 10 19041 以上

### 2.5 第一次使用建议流程

| 步骤 | 动作 | 目的 |
|------|------|------|
| 1 | 打开 Codex App 并登录 | 确认账号和模型可用 |
| 2 | 添加一个项目文件夹 | 让 Codex 能看到要处理的文件 |
| 3 | 新建一条 Thread | 把本次任务单独装起来 |
| 4 | 用一句话描述目标 | 例如：把 README 的下载方式同步到首页 |
| 5 | 先让它列计划 | 确认会改哪些文件、怎么改 |
| 6 | 执行后检查结果 | 看 diff、预览页面、必要时再微调 |

**核心原则**: 第一次不要追求大而全，先追求**可验证**。

---

## 三、核心概念：Threads（线程）系统

### 3.1 两层结构

| 层级 | 名称 | 作用 | 类比 |
|------|------|------|------|
| 第一层 | 文件夹（工作区） | 项目目录 / 主题盒子 | 像一个项目群 |
| 第二层 | Thread | 独立的对话任务线 | 像群里的具体话题贴 |

**文件夹装项目，Thread 装任务。**

### 3.2 为什么这样设计？

| 传统方式的痛点 | Codex 的解决方案 |
|--------------|------------------|
| 上午写网页、下午算 Excel、晚上改文案，所有内容搅在一起 | 不同任务放进不同 Thread |
| 上下文污染严重 | 对话和目标互不污染 |
| AI 开始胡编乱造 | 可以断点续写，重新收束任务 |
| 找不到文件在哪 | 文件和资源分层更清晰 |

### 3.3 黄金法则

> 🎯 **同一个文件夹里做同一个大方向，同一个 Thread 里只推进一件具体的事。**

---

## 四、项目文件夹管理

### 4.1 推荐的文件夹结构

```
dev/
├── Learning/     # 学习资料
├── notes/        # 文章和笔记
├── Projects/     # 真实开发项目任务
├── sandbox/      # 沙盒（乱七八糟的东西）
└── tools/        # 通用脚本、可复用组件、小工具
```

### 4.2 真实案例

**飞书机器人项目**: 把公众号数据定时爬下来，存到多维表格里。

这说明：**Codex 并不只适合"纯代码项目"，也适合真实业务型任务。**

---

## 五、功能与配置项

### 5.1 定时任务

Codex 可以在特定日期干特定的事。

**真实场景**:
- 服务器托管（作者本人不懂服务器）
- 每天早上 9 点自动巡检服务器，检查报错
- 如果有报错，会自己解决并总结原因
- 再通过飞书机器人发给作者

---

## 六、与 ContextStack 的关联

**您的使用场景**:
- 已配置 Codex 国内接入（cc-switch + 中转 API）
- 已在使用 Claude Code / Trae 进行开发
- 有自媒体内容发布需求（结合 social-auto-upload）

**建议关注**:
- Codex 与 Claude Code 的能力差异和互补
- Thread 组织方式对多任务管理的启发
- 定时任务功能对自动化工作流的补充

---

## 参考链接

- OpenAI GPT-5.5 发布: https://openai.com/index/introducing-gpt-5-5/
- OpenAI API Docs: https://developers.openai.com/api/docs/models/gpt-5.5
- cc-switch GitHub: https://github.com/farion1231/cc-switch/releases/

---

**最后更新**: 2026-05-30
