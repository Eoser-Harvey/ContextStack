# Agent Skills 开源资源大全（GitHub 深度搜索）

> 搜索日期：2026-07-05
> 搜索范围：GitHub 上别人做好的开源 Skills 仓库
> 用途：参考、借鉴、直接安装到 CodeBuddy 使用
> 适用平台：CodeBuddy / Claude Code / Codex / Cursor / Gemini CLI 等

---

## 一、最值得收藏的"精选合集"仓库（Top 5）

按 Star 数和实用度排序，这5个是必看：

| # | 仓库 | ⭐ Stars | 特点 | 地址 |
|---|------|---------|------|------|
| 1 | **VoltAgent/awesome-agent-skills** | 27.4k | 人工精选 600+ skills，覆盖60+企业官方+6位专家贡献，跨平台兼容 | https://github.com/VoltAgent/awesome-agent-skills |
| 2 | **ComposioHQ/awesome-claude-skills** | 36.6k | 最全的 Claude Skills 列表，Claude Code 首选 | https://github.com/ComposioHQ/awesome-claude-skills |
| 3 | **hesreallyhim/awesome-claude-code** | 24.6k | Claude Code 综合资源（含 skills/agents/hooks） | https://github.com/hesreallyhim/awesome-claude-code |
| 4 | **sickn33/antigravity-awesome-skills** | 14.0k | 800+ 技能，Claude Code/Antigravity/Cursor 通用 | https://github.com/sickn33/antigravity-awesome-skills |
| 5 | **heilcheng/awesome-agent-skills** | 2.3k | 跨平台精选，质量较高 | https://github.com/heilcheng/awesome-agent-skills |

### 中文资源

| # | 仓库 | ⭐ Stars | 特点 | 地址 |
|---|------|---------|------|------|
| 6 | **libukai/awesome-agent-skills** | 2.0k | 跨平台 + 中文入门指南，对各平台 skills 目录路径讲解详细 | https://github.com/libukai/awesome-agent-skills |
| 7 | **clawdbot-ai/awesome-openclaw-skills-zh** | 635 | OpenClaw 中文技能库翻译版 | https://github.com/clawdbot-ai/awesome-openclaw-skills-zh |
| 8 | **Prat011/awesome-llm-skills** | 918 | 跨平台 LLM Skills 精选 | https://github.com/Prat011/awesome-llm-skills |

---

## 二、官方企业 Skills 仓库（权威源）

由各公司工程团队官方维护，质量有保证：

| # | 仓库 | ⭐ Stars | 维护方 | 主要内容 | 地址 |
|---|------|---------|--------|---------|------|
| 1 | **anthropics/skills** | 158k | Anthropic | 官方 Claude Skills：docx/pdf/pptx/xlsx/frontend-design/mcp-builder/skill-creator 等17个 | https://github.com/anthropics/skills |
| 2 | **openai/skills** | 9.3k | OpenAI | Codex 官方 Skills：cloudflare-deploy/imagegen/jupyter-notebook/game-development 等 | https://github.com/openai/skills |
| 3 | **vercel-labs/agent-skills** | 20.9k | Vercel | Next.js 最佳实践/缓存/升级等 | https://github.com/vercel-labs/agent-skills |
| 4 | **vercel-labs/skills** | 6.6k | Vercel | `npx skills` CLI 工具，一行命令安装管理 Skills | https://github.com/vercel-labs/skills |
| 5 | **Tencent/awesome-devbuddy** | 20 | 腾讯 | CodeBuddy 官方示例：6 agents + 3 commands + 1 skill (webapp-testing) | https://github.com/Tencent/awesome-devbuddy |
| 6 | **kepano/obsidian-skills** | 10.3k | Obsidian 创始人 | Obsidian 知识库操作 | https://github.com/kepano/obsidian-skills |

### CodeBuddy 官方 Skills 包

| # | 仓库 | 维护方 | 内容 | 地址 |
|---|------|--------|------|------|
| 7 | **codebuddy/codebuddy (skills目录)** | 腾讯 CodeBuddy | HTTP 导入式 skills.zip，含：docx/pdf/pptx/xlsx/doc-coauthoring/writing-clearly-and-concisely/internal-comms/remotion/brainstorming/writing-plans/executing-plans/summarize/daily-news-digest/file-organizer | https://cnb.cool/codebuddy/codebuddy/-/tree/master/skills |

---

## 三、CodeBuddy 专用社区仓库

直接兼容 CodeBuddy `.codebuddy/skills/` 格式的社区贡献：

| # | 仓库 | 内容 | 地址 |
|---|------|------|------|
| 1 | **libairu/codebuddy-skills** | frontend-best-practices / design-mcp / commit-push-staged / commit-skill | https://github.com/libairu/codebuddy-skills |

> ⚠️ CodeBuddy skills 与 Claude Code skills 格式高度兼容（都是 `SKILL.md` + YAML frontmatter），大部分 Claude skills 可直接复制到 `.codebuddy/skills/` 使用。

---

## 四、特色功能型 Skills（高 Star 独立 Skill）

适合直接拿来用或参考的高质量独立 Skill：

| # | 仓库 | ⭐ Stars | 功能 | 适配场景 | 地址 |
|---|------|---------|------|---------|------|
| 1 | **nextlevelbuilder/ui-ux-pro-max-skill** | 33.4k | UI/UX 设计智能，让 AI 写出专业级界面代码 | 前端开发 | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| 2 | **OthmanAdi/planning-with-files** | 14.3k | Manus 风格的持久化 Markdown 规划模式 | 项目管理 | https://github.com/OthmanAdi/planning-with-files |
| 3 | **forrestchang/andrej-karpathy-skills** | 6.7k | 复刻 Andrej Karpathy 的编程风格 | AI 编码规范 | https://github.com/forrestchang/andrej-karpathy-skills |
| 4 | **blader/humanizer** | 6.1k | 去除 AI 生成文本的痕迹 | 内容创作 | https://github.com/blader/humanizer |
| 5 | **K-Dense-AI/claude-scientific-skills** | 9.1k | 科学计算（生物信息学、药物发现、基因组学） | 科研 | https://github.com/K-Dense-AI/claude-scientific-skills |
| 6 | **coreyhaines31/marketingskills** | 8.7k | 营销技能包（CRO、文案、SEO、数据分析） | 营销 | https://github.com/coreyhaines31/marketingskills |

> 💡 **与你的关联**：你已经实现了 `karpathy-guidelines`（参考第3项）、`writing-plans`（参考第2项的规划思路）、`brainstorming`（CodeBuddy官方包也有同名）。可对比官方实现，吸收优点。

---

## 五、Skills 开发工具与基础设施

| # | 仓库 | ⭐ Stars | 功能 | 地址 |
|---|------|---------|------|------|
| 1 | **yusufkaraaslan/Skill_Seekers** | 9.7k | 将文档/GitHub仓库/PDF 自动转换为 Skills，支持冲突检测 | https://github.com/yusufkaraaslan/Skill_Seekers |
| 2 | **diet103/claude-code-infrastructure-showcase** | 9.0k | Skills 自动激活、Hooks 与 Agent 基础设施示例 | https://github.com/diet103/claude-code-infrastructure-showcase |
| 3 | **muratcankoylan/Agent-Skills-for-Context-Engineering** | 8.5k | 面向上下文工程的 Skills 集合 | https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering |
| 4 | **refly-ai/refly** | 6.6k | 第一个开源 Skills Builder，可视化工作流定义 Skills | https://github.com/refly-ai/refly |
| 5 | **ChrisWiles/claude-code-showcase** | 5.4k | Claude Code 项目配置示例（含 hooks/skills/agents） | https://github.com/ChrisWiles/claude-code-showcase |
| 6 | **affaan-m/everything-claude-code** | 49.4k | Claude Code 完整配置集合（agents/skills/hooks/commands） | https://github.com/affaan-m/everything-claude-code |

---

## 六、VoltAgent 仓库分类速查（600+ Skills 按来源）

> 这是目前最全的精选库，按企业/团队分类。以下只列技能数≥10的高质量源：

### 6.1 官方企业 Skills（≥10个技能的团队）

| 来源团队 | 技能数 | 主要领域 |
|----------|--------|---------|
| **NVIDIA** | 155 | AI/ML 基础设施（17个产品） |
| **Microsoft** | 133 | Azure SDK 与 AI Foundry（6种语言） |
| **TestMu AI** | 44 | 测试自动化（Playwright/Cypress/Selenium等44框架） |
| **OpenAI** | 39 | 部署/文档/图像/Figma/安全 |
| **Paweł Huryn** | 65 | 产品管理全生命周期 |
| **Dean Peters** | 46 | 产品管理（发现/策略/执行/分析） |
| **Corey Haines** | 31 | SaaS 营销全套 |
| **Garry Tan** | 28 | 虚拟工程团队工作流 |
| **Trail of Bits** | 20 | 安全审计与智能合约安全 |
| **Flutter** | 20 | Flutter 跨平台开发 |
| **Venice.ai** | 19 | Venice API（聊天/图像/音频/视频） |
| **Anthropic** | 17 | Claude 官方（docx/pdf/pptx/xlsx/mcp-builder等） |
| **Google Workspace CLI** | 15 | Google Workspace 全套服务 |
| **Auth0** | 14 | 认证 SDK 全框架 |
| **fal.ai** | 14 | AI 图像/视频/音频生成 |
| **Apollo GraphQL** | 13 | GraphQL 客户端/服务器/联邦 |
| **Hugging Face** | 13 | ML 工作流（训练/评估/部署） |
| **WordPress** | 13 | WordPress 开发全套 |
| **Netlify** | 12 | 函数/边缘计算/存储/部署 |
| **Expo** | 12 | Expo 应用构建/部署/调试 |
| **Firebase** | 12 | Firebase 全套服务 |
| **Kim Barrett** | 12 | 直接响应广告 |
| **HashiCorp** | 11 | Terraform 提供者与模块 |
| **Brave** | 11 | Brave 搜索 API |
| **MiniMax** | 11 | 前端/全栈/移动开发 |
| **Cloudflare** | 8 | Workers/Pages/存储/AI |
| **Datadog Labs** | 8 | 可观测性（APM/日志/监控） |
| **GSAP** | 8 | GreenSock 动画全套 |
| **Browserbase** | 7 | 浏览器自动化 |
| **Binance** | 7 | Web3 交易与链上分析 |
| **Coinbase** | 9 | 钱包/支付/交易 |
| **Figma** | 7 | Figma 设计到代码 |
| **MongoDB** | 7 | MongoDB 连接/Schema/查询优化 |
| **Better Auth** | 7 | 认证集成最佳实践 |
| **Addy Osmani** | 6 | Web 质量（性能/可访问性/SEO） |
| **ClickHouse** | 6 | ClickHouse 最佳实践与部署 |
| **DuckDB** | 6 | 数据查询与文件读取 |
| **Google Labs (Stitch)** | 6 | 设计到代码转换 |
| **Google Gemini** | 4 | Gemini API 开发 |
| **Sanity** | 4 | CMS 最佳实践 |
| **Notion** | 4 | 知识捕获与会议准备 |
| **VoltAgent** | 4 | AI Agent 框架 |
| **Resend** | 5 | 邮件发送与模板 |
| **Firecrawl** | 5 | 网页搜索/抓取/提取 |
| **Stripe** | 2 | Stripe 集成与升级 |
| **Angular** | 2 | Angular 代码生成 |
| **Zero** | 2 | 工具发现与支付层 |
| **CodeRabbit** | 2 | AI 代码审查 |
| **Supabase** | 1 | PostgreSQL 最佳实践 |
| **Redis** | 1 | Redis 开发最佳实践 |
| **Composio** | 1 | 连接 1000+ 外部应用 |
| **Courier** | 1 | 多通道通知 |
| **CallStack** | 3 | React Native 性能优化 |
| **Neon** | 3 | Serverless Postgres |
| **Remotion** | 1 | React 编程式视频创作 |
| **Replicate** | 1 | AI 模型发现与运行 |
| **Typefully** | 1 | 社交媒体内容管理 |

---

## 七、对你最有价值的推荐（Top 10）

基于你的项目特征（嵌入式开发 + 投资追踪 + 自动化推送 + ContextStack 框架）：

| # | Skill | 来源 | 推荐理由 | 地址 |
|---|-------|------|---------|------|
| 1 | **webapp-testing** | Tencent | Playwright Web 测试，9个渐进式示例，中文文档，CodeBuddy 原生格式 | https://github.com/Tencent/awesome-devbuddy |
| 2 | **skill-creator** | Anthropic | 官方技能创建指南，比你的 find-skills 更系统 | https://github.com/anthropics/skills |
| 3 | **mcp-builder** | Anthropic | 创建 MCP 服务器集成外部 API，扩展 CodeBuddy 能力 | https://github.com/anthropics/skills |
| 4 | **planning-with-files** | OthmanAdi | Manus 风格持久化规划，可增强你的 writing-plans | https://github.com/OthmanAdi/planning-with-files |
| 5 | **andrej-karpathy-skills** | forrestchang | 对比你的 karpathy-guidelines，吸收官方实现优点 | https://github.com/forrestchang/andrej-karpathy-skills |
| 6 | **Skill_Seekers** | yusufkaraaslan | 文档/仓库自动转 Skills，快速沉淀知识 | https://github.com/yusufkaraaslan/Skill_Seekers |
| 7 | **frontend-best-practices** | libairu | CodeBuddy 原生格式，前端最佳实践 | https://github.com/libairu/codebuddy-skills |
| 8 | **daily-news-digest** | CodeBuddy官方 | 每日资讯 Skill，可参考用于你的 AI 新闻推送 | https://cnb.cool/codebuddy/codebuddy/-/tree/master/skills |
| 9 | **file-organizer** | CodeBuddy官方 | 文件整理 Skill，可参考用于 inbox 归档自动化 | https://cnb.cool/codebuddy/codebuddy/-/tree/master/skills |
| 10 | **internal-comms** | Anthropic | 状态报告/新闻稿/FAQ 撰写，可用于家庭资产报告 | https://github.com/anthropics/skills |

---

## 八、安装方法（CodeBuddy）

### 方法1：直接复制（最简单）

```bash
# 1. 克隆目标仓库
git clone https://github.com/anthropics/skills.git /tmp/anthropic-skills

# 2. 复制需要的 skill 到项目级或用户级
# 项目级（仅当前项目可用）
cp -r /tmp/anthropic-skills/skills/mcp-builder .codebuddy/skills/

# 用户级（全局可用）
cp -r /tmp/anthropic-skills/skills/mcp-builder ~/.codebuddy/skills/

# 3. 重启 CodeBuddy 即可使用
```

### 方法2：npx skills CLI（Vercel 工具）

```bash
# 安装 Vercel 的 skills CLI
npm install -g skills

# 一行命令安装 skill
npx skills install anthropics/mcp-builder
```

### 方法3：CodeBuddy 插件市场（仅限 Claude Code 源）

```bash
# 在 Claude Code 中（非 CodeBuddy）
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
```

### 兼容性说明

| 平台 | Skills 目录 | 格式 | 与 CodeBuddy 兼容性 |
|------|-----------|------|-------------------|
| **CodeBuddy** | `.codebuddy/skills/` 或 `~/.codebuddy/skills/` | `SKILL.md` + YAML frontmatter | ✅ 原生 |
| **Claude Code** | `.claude/skills/` 或 `~/.claude/skills/` | `SKILL.md` + YAML frontmatter | ✅ 直接复制可用 |
| **Codex** | `.codex/skills/` | `SKILL.md` + YAML frontmatter | ✅ 直接复制可用 |
| **Cursor** | `.cursor/skills/` | `SKILL.md` + YAML frontmatter | ✅ 直接复制可用 |
| **Gemini CLI** | `.gemini/skills/` | `SKILL.md` + YAML frontmatter | ✅ 直接复制可用 |

> **关键结论**：所有主流平台的 Skills 格式统一为 `SKILL.md` + YAML frontmatter，可跨平台直接复制使用。只需把目标 skill 文件夹放到 `.codebuddy/skills/` 即可。

---

## 九、Skill 标准格式参考

```yaml
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Claude/CodeBuddy 将遵循的指令内容]

## Examples
- Example usage 1

## Guidelines
- Guideline 1
```

**必需字段**：
- `name`：唯一标识符（小写，连字符分隔）
- `description`：完整描述功能和使用场景（决定 AI 何时触发该 Skill）

**可选打包资源**：
```
skill-name/
├── SKILL.md          # 必需
├── scripts/          # 可执行代码（Python/Bash等）
├── references/       # 按需加载的参考文档
└── assets/           # 模板、图标、字体等
```

---

## 十、参考文章

- [Agent Skills 生态全景：GitHub 上最受欢迎的 49 个技能相关仓库深度盘点](https://juejin.cn/post/7609151073307443251) — 掘金，2026-02-23
- [万字长文详解 CodeBuddy Skills：AI 编程进入"写技能"时代](https://cs.cloud.tencent.com/workbench) — 腾讯官方
- [Skills: 让 AI 变身你的专属领域专家](https://blog.csdn.net/caoxiaoye/article/details/156466066) — CSDN
- [Agent Skills 开发者指南：8 个最值得关注的开源仓](https://www.shengwang.cn/blog/blogdetail/202605-github-skills/) — 2026-05-22

---

## 十一、名人思维 Skills（Persona Distillation）

> 核心理念：不是角色扮演，而是提取"心智模型 + 决策启发式 + 表达DNA"，让 AI 用名人的视角帮你拆解问题

### 11.1 顶级框架与合集（Top 5）

| # | 仓库 | ⭐ Stars | 内容 | 地址 |
|---|------|---------|------|------|
| 1 | **alchaincyf/nuwa-skill（女娲）** | 26.9k | 名人思维蒸馏框架，已生成16个名人skill，5层认知提取+三重验证+自动进化 | https://github.com/alchaincyf/nuwa-skill |
| 2 | **xbtlin/ai-berkshire** | 10.1k | 巴菲特+芒格+段永平+李录四大师价值投资框架，19个skill，多Agent对抗分析 | https://github.com/xbtlin/ai-berkshire |
| 3 | **titanwings/colleague-skill（同事.skill）** | 9.6k | 引爆 persona distillation 运动的OG项目，支持微信/飞书/钉钉多源 | https://github.com/titanwings/colleague-skill |
| 4 | **sdamkkk/awesome-distill-skills** | — | 最全的名人persona skill精选清单，50+项目分类整理 | https://github.com/sdamkkk/awesome-distill-skills |
| 5 | **wemamawe/ai-persona-skills** | 1 | 14位中国科技领袖+硅谷大佬思维skill，中/英/法三语支持 | https://github.com/wemamawe/ai-persona-skills |

### 11.2 nuwa-skill（女娲）蒸馏的16个名人 Skill

> 仓库：https://github.com/alchaincyf/nuwa-skill  ⭐26.9k
> 作者：花叔（Huashu）
> 方法论：6路并行研究 → 5层认知提取（表达DNA→思维模型→决策启发式→反模式→诚实边界）→ 三重验证 → darwin-skill自动进化
> 每个 skill 包含 3-7个心智模型 + 5-10条决策启发式

| # | 名人 | 领域 | 保真度 | 安装命令 |
|---|------|------|--------|---------|
| 1 | 🔥 **Paul Graham** | 创业/写作/产品/人生哲学 | 97 | `npx skills add alchaincyf/paul-graham-skill` |
| 2 | 🔥 **张一鸣** | 产品/组织/全球化/人才 | 93 | `npx skills add alchaincyf/zhang-yiming-skill` |
| 3 | 🔥 **Andrej Karpathy** | AI/工程/教育/开源 | 97 | `npx skills add alchaincyf/karpathy-skill` |
| 4 | 🔥 **Ilya Sutskever** | AI安全/scaling/研究品味 | 94 | `npx skills add alchaincyf/ilya-sutskever-skill` |
| 5 | 🔥 **MrBeast** | 内容创造/YouTube方法论 | 97 | `npx skills add alchaincyf/mrbeast-skill` |
| 6 | 🔥 **特朗普** | 谈判/权力/传播/行为预判 | 95 | `npx skills add alchaincyf/trump-skill` |
| 7 | ⭐ **乔布斯** | 产品/设计/战略 | 97 | `npx skills add alchaincyf/steve-jobs-skill` |
| 8 | **马斯克** | 工程/成本/第一性原理 | 89 | `npx skills add alchaincyf/elon-musk-skill` |
| 9 | **芒格** | 投资/多元思维/逆向思考 | 96 | `npx skills add alchaincyf/munger-skill` |
| 10 | **费曼** | 学习/教学/科学思维 | 96 | `npx skills add alchaincyf/feynman-skill` |
| 11 | **纳瓦尔 (Naval)** | 财富/杠杆/人生哲学 | 97 | `npx skills add alchaincyf/naval-skill` |
| 12 | **塔勒布 (Taleb)** | 风险/反脆弱/不确定性 | 97 | `npx skills add alchaincyf/taleb-skill` |
| 13 | **张雪峰** | 教育选择/职业规划/阶层流动 | 97 | `npx skills add alchaincyf/zhangxuefeng-skill` ⭐6.5k |
| 14 | **孙宇晨** | 营销/注意力经济/叙事操控 | 91 | 复制 `examples/sun-yuchen-perspective/` |
| 15 | **X导师（主题Skill）** | X/Twitter运营全栈（6位创作者） | 96 | `npx skills add alchaincyf/x-mentor-skill` |
| 16 | 🧬 **达尔文.SKILL** | 让所有Skill持续进化（8维度评估+棘轮机制） | — | `npx skills add alchaincyf/darwin-skill` |

### 11.3 投资大师 Skills

#### AI Berkshire — 四大师价值投资框架 ⭐10.1k

> 仓库：https://github.com/xbtlin/ai-berkshire
> 核心设计：四位大师**互相挑战**，而非简单分工

| 大师 | 核心视角 | 职责 |
|------|---------|------|
| **段永平** | "对的生意"——商业模式本质 | 生意本质判断，是其余三个视角的共同起点 |
| **巴菲特** | 护城河、安全边际、管理层 | 财务估值与竞争优势评估 |
| **芒格** | 逆向思考、风险清单、偏误自查 | 强制思考失败场景与盲点 |
| **李录** | 文明趋势、范式转移、产业价值 | 长期确定性与文明级别趋势判断 |

**19个 Skill 列表**：

| 类别 | Skill | 用途 |
|------|-------|------|
| 深度研究 | `/investment-research` | 四大师综合深度分析（七模块） |
| 深度研究 | `/investment-team` | 多Agent并行投研团队 |
| 深度研究 | `/management-deep-dive` | 管理层纵深研究 |
| 深度研究 | `/private-company-research` | 未上市公司深度研究（如SpaceX） |
| 深度研究 | `/deep-company-series` | 8篇长文系列拆一家公司 |
| 财报分析 | `/earnings-review` | 财报精读（一手资料） |
| 财报分析 | `/earnings-team` | 财报精读团队 |
| 行业筛选 | `/industry-research` | 产业链全景扫描 |
| 行业筛选 | `/industry-funnel` | 行业漏斗筛选 |
| 行业筛选 | `/quality-screen` | 去劣筛选（7条硬指标） |
| 行业筛选 | `/bottleneck-hunter` | 供应链瓶颈猎手 |
| 行业筛选 | `/investment-checklist` | 巴菲特买入前Checklist |
| 持仓管理 | `/portfolio-review` | 组合管理与优化 |
| 持仓管理 | `/thesis-tracker` | 投资论文追踪 |
| 持仓管理 | `/thesis-drift` | 投资论文漂移检测 |
| 持仓管理 | `/news-pulse` | 股价异动10分钟快速归因 |
| 思维工具 | `/dyp-ask` | 段永平问答（商业/投资/人生） |
| 思维工具 | `/financial-data` | 财务数据获取与交叉验证 |
| 思维工具 | `/wechat-article` | 微信公众号文章三Agent协作 |

**安装**：
```bash
git clone https://github.com/xbtlin/ai-berkshire.git
cd ai-berkshire
# Windows
.\scripts\install-claude-commands.bat
# macOS/Linux
./scripts/install-claude-commands.sh
```

#### 其他投资大师独立 Skill

| 名人 | 仓库 | ⭐ Stars | 特点 | 地址 |
|------|------|---------|------|------|
| **段永平** | anneheartrecord/duanyongping-perspective | — | 基于雪球原帖+巴菲特午餐+浙大演讲，5个核心心智模型 | https://github.com/anneheartrecord/duanyongping-perspective |
| **段永平** | Panmax/duanyongping-skill | — | 「本分」哲学+价值投资+克制经营，"中国巴菲特"视角 | https://github.com/Panmax/duanyongping-skill |
| **李笑来** | jazzqi/li-xiaolai-skill | — | 认知优先+价值逻辑+长期主义+负面清单决策 | https://github.com/jazzqi/li-xiaolai-skill |
| **索罗斯** | Panmax/soros-skill | — | 反身性理论+金融哲学+开放社会，识别泡沫 | https://github.com/Panmax/soros-skill |
| **雷军** | Panmax/leijun-skill | — | 定价/创业/产品简化/与大公司竞争 | https://github.com/Panmax/leijun-skill |
| **雷军** | JasperHye/leijun-skill | — | 雷军思维模式的另一种蒸馏视角 | https://github.com/JasperHye/leijun-skill |
| **雷军** | ansuelele/leijun-works | — | 基于雷军已发表作品的文学导向方法 | https://github.com/ansuelele/leijun-works |

#### 投资大师合集项目

| 项目 | 仓库 | ⭐ Stars | 收录名人 | 特点 |
|------|------|---------|---------|------|
| **wisdom-council（智者议会）** | linxumoney/wisdom-council | — | 巴菲特/芒格/稻盛和夫/彼得林奇/纳瓦尔/达利欧/Peter Thiel | 7位思想家同时辩论，主持人总结分歧 |
| **skill-from-masters** | GBSOSS/skill-from-masters | 1.4k | 乔布斯/贝索斯/芒格/Chris Voss | 聚焦方法论，3层搜索+交叉验证+反模式 |
| **investment-master-mindset** | — | — | 巴菲特/索罗斯等8位投资大师 | 基于nuwa-skill方法论蒸馏 |
| **AI Hedge Fund** | virattt/ai-hedge-fund | 51k | 12位传奇投资人Agent | 巴菲特/芒格/格雷厄姆/达利欧/索罗斯/彼得林奇等 |

### 11.4 中国科技领袖 Skills

> 仓库：https://github.com/wemamawe/ai-persona-skills
> 特点：中/英/法三语支持，每个skill含5个思维模型+8条决策启发式+表达基因+时间线+价值观矛盾+诚实局限

#### README正式收录（11位）

| # | 名人 | 领域 | 思维特点 |
|---|------|------|---------|
| 1 | **马云 Jack Ma** | 互联网/电商 | 逆向哲学 · 故事基因 |
| 2 | **雷军 Lei Jun** | 硬件/电动车 | 趋势感知 · 完美主义 · 回归心态 |
| 3 | **刘强东 Richard Liu** | 电商/供应链 | 兄弟文化 · 自建物流 |
| 4 | **张一鸣 Zhang Yiming** | 内容/算法/全球化 | 延迟满足 · 上下文而非控制 |
| 5 | **任正非 Ren Zhengfei** | 电信/硬科技 | 灰度管理 · 活下来为先 |
| 6 | **黄峥 Colin Huang** | 电商/农业科技 | 本分哲学 · Costco + Disney 模式 |
| 7 | **程维 Cheng Wei** | 出行/自动驾驶 | 战争思维 · 补贴驱动网络效应 |
| 8 | **王兴 Wang Xing** | 本地服务/外卖 | 无边界理论 · 无限游戏 |
| 9 | **张勇 Daniel Zhang** | 电商/零售/组织 | 双十一发明者 · 数据飞轮 |
| 10 | **乔布斯 Steve Jobs** | 消费科技/设计 | 现实扭曲力场 · 科技 × 人文 |
| 11 | **马斯克 Elon Musk** | 太空/电动车/AI | 第一性原理 · 算法思维 · 多星球使命 |

#### 文件夹中额外收录（3位）

| # | 名人 | 领域 |
|---|------|------|
| 12 | **贝索斯 Jeff Bezos** | 电商/云计算 |
| 13 | **段永平 Duanyongping** | 价值投资 |
| 14 | **黄仁勋 Jensen Huang** | GPU/AI芯片 |

### 11.5 通用蒸馏框架（可蒸馏任意人物）

| 项目 | 仓库 | ⭐ Stars | 特点 |
|------|------|---------|------|
| **nuwa-skill（女娲）** | alchaincyf/nuwa-skill | 26.9k | 5层认知提取+6路并行研究+三重验证+自动进化 |
| **colleague-skill（同事.skill）** | titanwings/colleague-skill | 9.6k | OG项目，支持微信/飞书/钉钉/邮件多源 |
| **ex-skill（前任.skill）** | therealXiaomanChu/ex-skill | 3.3k | 6层人格提取，含伦理声明 |
| **anyone-skill** | acnlabs/anyone-skill | — | 最严谨框架，L1-L4证据分级，12+数据源 |
| **immortal-skill（永生.skill）** | agenmod/immortal-skill | — | 7阶段数字永生，7维数字孪生 |
| **bazi-persona-skill（八字人格）** | cantian-ai/bazi-persona-skill | — | 零数据冷启动，仅需姓名+生日，基于八字命理 |

### 11.6 对投资场景的推荐（Top 5）

基于持仓（MRVL/GOOGL/CRCL/BTC）和家庭投资追踪需求：

| # | 推荐 | 来源 | 推荐理由 |
|---|------|------|---------|
| 1 | **ai-berkshire** | xbtlin | ⭐10.1k，四大师对抗分析，直接用于美股投资决策，有 `/investment-checklist` `/portfolio-review` `/news-pulse` 等skill |
| 2 | **段永平.skill** | anneheartrecord | 持仓风格（长期持有+不追涨杀跌）与段永平哲学高度契合 |
| 3 | **芒格.skill** | alchaincyf | 逆向思考+偏误自查，配合三条卖出线方法论，避免确认偏误 |
| 4 | **李笑来.skill** | jazzqi | BTC持仓+定投策略与李笑来的长期主义+负面清单决策高度匹配 |
| 5 | **塔勒布.skill** | alchaincyf | 反脆弱思维，负债管理（信用卡+币安借贷）需要反脆弱视角 |

### 11.7 名人 Skill 标准结构

```
famous-person-skill/
├── SKILL.md              # 必需：核心指令
│   ├── YAML frontmatter  # name + description
│   ├── 角色扮演规则       # 激活/退出触发器
│   ├── 身份卡片          # 背景、现状
│   ├── 思维模型 ×5       # 每个含一句话总结+3证据点+应用+局限
│   ├── 决策启发式 ×8     # 经验法则+真实案例
│   ├── 表达基因          # 语调、词汇、节奏、幽默风格
│   ├── 时间线            # 关键人生事件+对思维的影响
│   ├── 价值观与矛盾      # 诚实记录，非美化
│   ├── 诚实局限          # 该Skill无法可靠模拟的内容
│   └── 关键语录          # 经验证来源
├── references/           # 可选：调研素材、原始访谈
└── assets/              # 可选：模板、示例
```

**女娲（nuwa-skill）五层认知提取模型**：

| 层次 | 说明 | 示例（芒格） |
|------|------|------------|
| 怎么说话 | 表达DNA——语气、节奏、用词偏好 | "反过来想，总是反过来想" |
| 怎么想 | 心智模型、认知框架 | 多元思维模型、逆向思考 |
| 怎么判断 | 决策启发式 | "我能怎么避免失败？" |
| 什么不做 | 反模式、价值观底线 | 不投资看不懂的生意 |
| 知道局限 | 诚实边界 | 无法预测短期市场 |

### 11.8 名人 Skills 参考文章

- [Distilling Persons into Agents: Person-as-Skill Survey](https://davidlxu.github.io/posts/2026/04/distilling-persons-into-agents/) — 2026-04-05
- [从"赛博前任"到"数字老板"：GitHub 爆火的 Person.Skill 背后的趋势](https://cloud.tencent.com/developer/article/2655883) — 腾讯云，2026-04-16
- [疯狂的 Skill：GitHub 爆火「同事.skill」背后的深度解析](https://blog.csdn.net/u014354882/article/details/159850002) — CSDN，2026-04-05
- [nuwa-skill 18K Star：16 个思维 Skill 全拆解](https://www.theaiera.cn/blogs/nuwa-skill-16-skills-overview) — 2026-05-10
- [AI Berkshire：把四位价值投资大师的对抗塞进 Claude Code](https://txtmix.com/posts/tech/xbtlin-ai-berkshire-multi-agent-value-investing-guide/) — 2026-06-25
- [AI"蒸馏"投资大师思维：开源项目构建可调用数字智囊团](https://www.houdao.com/d/9648) — 2026-04-22

---

## 统计汇总

| 类别 | 仓库数 | 总 Stars |
|------|--------|---------|
| 精选合集 | 8 | 105k+ |
| 官方企业 | 7 | 230k+ |
| CodeBuddy 专用 | 1 | — |
| 特色功能型 | 6 | 78k+ |
| 开发工具 | 6 | 88k+ |
| 名人思维 Skills | 48+ | 100k+ |
| **合计** | **76+** | **600k+** |

---

> 更新日志：
> - 2026-07-05 初版：GitHub 深度搜索，归档28+仓库，含CodeBuddy/Claude/Codex/Cursor全平台资源
> - 2026-07-05 更新：新增第十一章"名人思维 Skills"，归档48+名人skill项目（巴菲特/马斯克/段永平/李笑来/芒格/纳瓦尔等），合并为单一文档
