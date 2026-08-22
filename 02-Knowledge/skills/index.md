# Skills 库

> 可复用的 AI 助手技能模块，分为三类：ContextStack 自定义 Skills、CodeBuddy 内置 Skills、用户级安装 Skills。  
> 外部参考：[[codebuddy-builtin-skills-analysis|WorkBuddy Top 10 Skills 适配分析]]

---

## 一、ContextStack 自定义 Skills（18 个）

### 专业领域 Skills

| Skill | 说明 | 标签 |
|-------|------|------|
| [[device-debugging/index\|设备调试]] | 网络设备、嵌入式设备的分层调试 | `#debugging` `#network` `#embedded` |
| [[network-packet-analysis/index\|网络抓包分析]] | Wireshark 抓包与协议分析 | `#wireshark` `#packet-analysis` `#network` |
| [[tsn-protocol/index\|TSN协议]] | IEEE 802.1 TSN 协议栈 | `#tsn` `#network` `#protocol` |
| [[vscode-config-management/index\|VSCode配置管理]] | 配置备份、恢复与同步 | `#vscode` `#tool-config` `#backup` |
| [[interview-prep/interview-prep使用说明\|面试准备]] | 输入公司名，自动生成8模块面试准备清单 + 7家公司经验库 | `#interview` `#career` `#job-search` |
| [[wechat-push/x-tweets-wechat-push-方案说明\|微信推送方案]] | X推文→微信推送方案演进：WeChat MCP vs Server酱 vs Bun JSON-RPC | `#wechat` `#push` `#automation` `#json-rpc` |
| [[0.wechat-push/README\|X推文推送系统]] | 完整代码归档：抓取→翻译→分析→推送，Bun JSON-RPC 直连 | `#wechat` `#push` `#x-tweets` `#automation` |
| [[ai-berkshire/index\|AI Berkshire投资研究]] | 投资研究AI助手：公司研究/财报分析/行业筛选/组合回顾 | `#investment-research` `#financial-analysis` `#ai-assistant` |
| [[browser-automation/web-pack/index\|Web-Pack素材采集]] | 网页主题完整素材包采集，超越传统剪藏工具（已归入浏览器自动化目录） | `#web-crawling` `#knowledge-management` `#content-collection` |
| [[wechat-cli/index\|WeChat CLI本地查询]] | 命令行查询本地微信数据（聊天记录/联系人/群成员/统计/收藏/导出），AI Agent 友好 JSON 输出 | `#wechat` `#local-data` `#agent-tool` `#json` `#sqlcipher` |
| [[arm-cortex-microcontrollers/index\|ARM Cortex-M固件开发]] | ARM Cortex-M 固件专家知识库：内存屏障/DMA/中断/Hardfault/栈保护，覆盖 STM32/nRF52/Teensy/SAMD | `#embedded` `#cortex-m` `#firmware` `#driver` |
| [[tailored-resume-generator/index\|定制简历生成]] | 分析 JD 生成定制简历：ATS 优化/量化成果/差距分析/面试建议 | `#resume` `#job-search` `#ats` |

### AI 编码与治理 Skills（2026-05-13）

| Skill | 说明 | 类型 |
|-------|------|------|
| [[karpathy-guidelines/karpathy-guidelines使用说明\|Karpathy编码准则]] | 四原则约束AI编码 | `always` 自动生效 |
| [[brainstorming/brainstorming使用说明\|Brainstorming]] | 强制前置设计与需求分析 | `manual` `@skill://brainstorming` |
| [[writing-plans/writing-plans使用说明\|Writing Plans]] | 设计输出转零上下文可执行计划 | `manual` `@skill://writing-plans` |
| [[systematic-debugging/systematic-debugging使用说明\|Systematic Debugging]] | 四阶段系统化调试 + 架构质疑 | `manual` `@skill://systematic-debugging` |
| [[pua-governance/pua-governance使用说明\|PUA Governance]] | RCA/Musk五步法/Jobs减法 + 强制检查清单 | `manual` `@skill://pua-governance` |
| [[find-skills/Skill\|Find Skills]] | 技能发现与推荐 | `manual` `@skill://find-skills` |
| [[openspec/openspec使用说明\|OpenSpec]] | 规范驱动开发（SDD），npm 全局工具 | `npm` `openspec` `/opsx:propose` |

### 人物蒸馏 Skills（Persona Distillation）

| Skill | 说明 | 标签 |
|-------|------|------|
| [[laoxue/index\|老薛（奋斗的老薛）人物蒸馏]] | 财富成长+投资决策+贵人杠杆+守富+精力战略的心智模型与启发式 | `#persona` `#财富成长` `#贵人杠杆` `#守富` |

- 关联分析：[[laoxue/财富成长路径与关键决策\|老薛 0–100万 / 100–1000万 路径 + 对你千万级的借鉴]]

---

## 二、CodeBuddy 内置 Skills（6 个）

> 这些 Skills 随 CodeBuddy 预装，无需额外安装，通过 `@skill://skill-name` 或自然触发使用。

| Skill | 功能 | 安装名 |
|-------|------|--------|
| **agent-browser** | 浏览器自动化：打开网页、滚动、点击、截图、提取内容 | `@skill://agent-browser` |
| **playwright-cli** | 浏览器自动化：Playwright 内核，表单填充、复杂交互、测试 | `@skill://playwright-cli` |
| **BrowserSkill (bsk)** | 腾讯开源（MIT）：复用已登录真实浏览器，免重复登录（含 web-pack 素材采集） | [[browser-automation/index\|安装指南]] |
| **pdf** | PDF 读写：提取文本/表格、合并/拆分、加水印、OCR | `@skill://pdf` |
| **docx** | Word 文档：创建/读取/编辑 .docx，支持格式、目录、页眉页脚 | `@skill://docx` |
| **pptx** | PPT 演示：创建/读取/编辑 .pptx，支持模板、备注、批量操作 | `@skill://pptx` |
| **xlsx** | Excel 表格：创建/读取/编辑 .xlsx/.csv，公式、图表、数据清洗 | `@skill://xlsx` |
| **note-organizer** | 智能笔记整理：自动识别内容类型，结构化保存到 inbox（项目级 `#project`） | `@skill://note-organizer` |

> 另有 `web-search` / `web_fetch` 是 CodeBuddy **原生工具**（非 Skill），功能更强无需额外安装。  
> `self-improvement` 功能由 ContextStack 的 Memory 系统 + 工作台记忆机制替代。

---

## 三、用户级已安装 Skills（1 个）

> 安装在 `~/.codebuddy/skills/`，全局可用，不限于当前项目。

| Skill | 功能 | 来源 | 安装日期 |
|-------|------|------|----------|
| **obsidian** | Obsidian 知识库操作：搜索笔记、创建/编辑/移动笔记、管理 `[[wikilinks]]` 和标签 | SkillHub (steipete, 98K 下载) | 2026-05-27 |

---

## 统计

| 类别 | 数量 | 位置 |
|------|------|------|
| ContextStack 自定义 | 20 | `02-Knowledge/skills/` |
| CodeBuddy 内置 | 6 | CodeBuddy 预装 + `.codebuddy/skills/note-organizer/` |
| 用户级安装 | 1 | `~/.codebuddy/skills/obsidian/` |
| **合计** | **25** | — |

---

## 更新记录

| 日期 | 新增技能 | 来源 | 数量变化 |
|------|----------|------|----------|
| 2026-07-06 | [[ai-berkshire/index\|AI Berkshire 投资研究]]、[[browser-automation/web-pack/index\|Web-Pack 素材采集]] | 微信公众号「JackCui」投资研究文章、微信公众号「Ai学习的老章」原创 Skills 文章 | 14 → 16 |
| 2026-07-26 | [[wechat-cli/index\|WeChat CLI 本地查询]] | GitHub [huohuoer/wechat-cli](https://github.com/huohuoer/wechat-cli)，本地微信数据命令行查询工具 | 17 → 18 |
| 2026-08-21 | [[arm-cortex-microcontrollers/index\|ARM Cortex-M固件开发]]、[[tailored-resume-generator/index\|定制简历生成]] | GitHub [wshobson/agents](https://github.com/wshobson/agents)、[composio-community/awesome-codex-skills](https://github.com/composio-community/awesome-codex-skills) | 18 → 20 |

- **AI Berkshire**（投资研究）：5 个子技能（investment-research / investment-team / earnings-review / industry-funnel / portfolio-review）。源文：https://mp.weixin.qq.com/s/rN6gmls_hbTWVHHSDhN3-Q
- **Web-Pack**（网页素材采集，已归入 browser-automation）：深度采集 + 图片本地化 + 结构化输出。源文：https://mp.weixin.qq.com/s/U1nICI87xfBZ86Bh_Dj5kw

---

## 相关

- [[codebuddy-builtin-skills-analysis|WorkBuddy Top 10 Skills 适配分析]] — 10 个零成本 Skills 的 CodeBuddy 可行性分析
- [[awesome-agent-skills-resources|Agent Skills 开源资源大全]] — GitHub 深度搜索 76+ 仓库（2026-07-05），含全平台通用skills + 名人思维skills（巴菲特/马斯克/段永平/李笑来/芒格等48+名人）
- [[skills-building-best-practices|Skills 制作最佳实践（Anthropic 官方方法论）]] — 抽取自 Anthropic 官方博客，九条制作 Skills 的核心干货
- [[../system/methodology/index|调试方法论]] — Skills 的理论基础
- [[../system/tool-configurations/index|工具配置]] — 工具配置文档
- [[../../../.codebuddy/skills/note-organizer/SKILL|note-organizer SKILL.md]] — 智能笔记整理 Skill 源文件
