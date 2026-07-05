# Skills 库

> 可复用的 AI 助手技能模块，分为三类：ContextStack 自定义 Skills、CodeBuddy 内置 Skills、用户级安装 Skills。  
> 外部参考：[[codebuddy-builtin-skills-analysis|WorkBuddy Top 10 Skills 适配分析]]

---

## 一、ContextStack 自定义 Skills（13 个）

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

---

## 二、CodeBuddy 内置 Skills（6 个）

> 这些 Skills 随 CodeBuddy 预装，无需额外安装，通过 `@skill://skill-name` 或自然触发使用。

| Skill | 功能 | 安装名 |
|-------|------|--------|
| **agent-browser** | 浏览器自动化：打开网页、滚动、点击、截图、提取内容 | `@skill://agent-browser` |
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
| ContextStack 自定义 | 14 | `02-Knowledge/skills/` |
| CodeBuddy 内置 | 6 | CodeBuddy 预装 + `.codebuddy/skills/note-organizer/` |
| 用户级安装 | 1 | `~/.codebuddy/skills/obsidian/` |
| **合计** | **21** | — |

---

## 相关

- [[codebuddy-builtin-skills-analysis|WorkBuddy Top 10 Skills 适配分析]] — 10 个零成本 Skills 的 CodeBuddy 可行性分析
- [[awesome-agent-skills-resources|Agent Skills 开源资源大全]] — GitHub 深度搜索 76+ 仓库（2026-07-05），含全平台通用skills + 名人思维skills（巴菲特/马斯克/段永平/李笑来/芒格等48+名人）
- [[../system/methodology/index|调试方法论]] — Skills 的理论基础
- [[../system/tool-configurations/index|工具配置]] — 工具配置文档
- [[../../../.codebuddy/skills/note-organizer/SKILL|note-organizer SKILL.md]] — 智能笔记整理 Skill 源文件
