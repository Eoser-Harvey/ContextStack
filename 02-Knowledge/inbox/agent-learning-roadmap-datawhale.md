# AI Agent 学习路线图 - Datawhale Agent Learning Hub

> 来源: [datawhalechina/Agent-Learning-Hub](https://github.com/datawhalechina/Agent-Learning-Hub)  
> 整理时间: 2026-05-24  
> 维护方: Datawhale 中国（开源学习组织）  
> 维护者: 陈思州

---

## 核心定位

不是资料堆砌，而是一份**可执行的 AI Agent 学习 todo list**。目标是把社区优秀分享、官方博客、论文、开源项目和真实工程经验，整理成系统化学习路径。

---

## 当前最值得投入的 5 个方向（按优先级）

| 优先级 | 方向 | 核心要点 |
|:------:|------|----------|
| 1 | **Claude Code / Codex-style coding agents** | 真实代码库、shell、文件编辑、测试、权限、上下文压缩 |
| 2 | **Agent harness engineering** | 工具协议、权限、状态、反馈、回放、CI、评测 |
| 3 | **OpenClaw / Hermes-style personal agents** | 长运行、本地优先、跨应用、记忆、skills、消息入口 |
| 4 | **Skills / MCP / A2A / ACP** | skills 能力复用、MCP 连接工具、A2A 连接 agent、ACP 连接宿主 |
| 5 | **Evaluation and safety** | 没有 eval、trace、权限边界的 agent 只能算 demo |

> ⚠️ **明确不建议重押**: 老式 crew/role-play 多 agent 框架（已泛化成模板）

---

## 8 阶段学习路径

### Stage 0: 理解 Agent 本质
- 区分 chatbot、workflow、agent、multi-agent
- 理解 agent 基本循环: observe → think → act → observe
- 明白什么时候不该用 agent
- **必读**: Anthropic《Building effective agents》、OpenAI《A practical guide to building agents》

### Stage 1: 构建最小 Agent Loop
- LLM API 对话、结构化 JSON 输出
- 定义工具函数、解析 tool call、执行工具
- 加最大步数、超时、错误处理
- **产出**: 50-150 行最小 agent

### Stage 2: 工具使用、RAG、记忆
- 检索增强生成: chunk、embed、retrieve、citations
- 搜索、数据库、文件、浏览器、代码执行接成工具
- 区分短期上下文、会话记忆、长期记忆
- **参考项目**: GPT Researcher、STORM、Khoj、mem0、Letta
- **产出**: 资料研究助手

### Stage 3: 研究现代 Agent Harness
选一个系统学深，重点不是 API 怎么调，而是如何组织工具、上下文、权限、状态、日志、子任务和反馈。

| 系统 | 适合学习 |
|------|----------|
| Claude Code | coding agent 产品化形态 |
| learn-claude-code | 从 0 复刻 harness |
| claw0 | 从 0 构建 gateway |
| hello-agents | 中文系统教程 |
| OpenClaw | 本地长运行 agent |
| LangGraph | 状态图编排 |

**产出**: 可调试的 agent harness demo

### Stage 4: 多 Agent 协调
- 理解 planner/executor/reviewer/critic/router 角色
- 用 supervisor 或 graph 管理，不是让 agent 随便聊天
- 定义职责边界、输入输出 schema、停止条件
- **产出**: research → write → review → revise 小型系统

### Stage 5: Skills、协议、能力封装
- **Skill vs Tool**: tool 是可调用接口，skill 是可复用流程知识
- **Skill vs Prompt**: prompt 是一次性指令，skill 是可发现、可版本化、可分发的能力包
- **Skill vs MCP**: MCP 接入外部工具，skill 告诉 agent 如何完成任务
- **关键协议**: MCP（连接工具）、A2A（连接 agent）、ACP（连接宿主应用）
- **产出**: 可复用 skill（如 code-review、research-report）

### Stage 6: 浏览器和 Computer-Use Agents
- Playwright / browser-use 网页观察和点击
- 安全限制: 不登录敏感账号、不越权
- 处理页面变化、弹窗、加载失败
- **产出**: 只操作公开网页的 browser agent

### Stage 7: 评测、可观测性、安全
- 固定测试集、记录成功率/失败原因/成本/延迟
- 看 trace，定位失败环节
- 危险工具加人工确认
- 了解 prompt injection、data exfiltration 风险
- **产出**: 至少 20 个任务的 agent eval 表格

### Stage 8: 发布真实 Agent
- 明确用户、任务、成功标准
- 日志、trace、错误重试、超时、成本上限
- 权限边界和人工确认机制
- 部署方式: CLI、Web app、Slack bot、GitHub Action
- **产出**: 别人能 clone 下来跑的 agent 项目

---

## 11 级项目阶梯 (Project Ladder)

| 等级 | 项目 | 能力 |
|:----:|------|------|
| 1 | Calculator Agent | 最小 tool call loop |
| 2 | Web Research Agent | 搜索、筛选、引用、总结 |
| 3 | PDF QA Agent | RAG、chunk、retrieval |
| 4 | Coding Review Agent | 读取 diff、风险排序 |
| 5 | Browser Agent | 页面观察、点击、提取 |
| 6 | Claude Code-like Nano Agent | shell、文件编辑、权限、session |
| 7 | OpenClaw-like Gateway | channel、routing、session、memory |
| 8 | Reusable Skill Pack | SKILL.md、脚本、模板、smoke test |
| 9 | Multi-Agent Writer | planner、writer、reviewer 协作 |
| 10 | Personal Agent | 记忆、skills、消息入口 |
| 11 | Production Harness | evals、trace、CI、runner |

---

## 与 ContextStack 框架的关联

| 本仓库概念 | ContextStack 对应 |
|-----------|-------------------|
| **Skills** | `Skills/` 目录 + 四层架构技能沉淀 |
| **Agent Harness** | `workbench/` 工作台系统（session、状态、记忆） |
| **MCP** | 四层 Context 加载机制（分层规则加载） |
| **Memory 分层** | `MEMORY.md` + `memory/`（短期/长期记忆） |
| **Project Ladder** | `workbench/projects/` 项目进阶路径 |
| **Evaluation** | Feedback 记忆（纠正/认可的行为记录） |

> 💡 **关键洞察**: ContextStack 四层架构本身就是 **Agent Harness** 的实现，与 Stage 3 研究方向高度契合！

---

## 对个人学习的建议

基于当前 **嵌入式AI学习** 项目，建议关注：

1. **Stage 2** → 学习 RAG、工具调用（与 TFLM 学习互补）
2. **Stage 3** → 研究 Claude Code harness 设计（与 ContextStack 对比）
3. **Stage 5** → Skills 机制（完善 `Skills/` 目录规范）
4. **Stage 7** → Evaluation（建立学习效果评估体系）

---

## 关键资源链接

### 必读官方文档
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [OpenAI: A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- [Claude Code Docs](https://code.claude.com/docs/en/overview)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### 推荐开源项目
- [hello-agents](https://github.com/datawhalechina/hello-agents) - 中文系统教程
- [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) - 复刻 Claude Code
- [OpenClaw](https://github.com/openclaw/openclaw) - 本地个人 agent
- [mem0](https://github.com/mem0ai/mem0) - 记忆层组件
- [browser-use](https://github.com/browser-use/browser-use) - 浏览器 agent

---

**归档信息**  
- 原材料: GitHub 仓库链接已保存  
- 处理状态: ✅ 已结构化整理  
- 存储位置: `02-Knowledge/system/agent-learning-roadmap-datawhale.md`
