


# Memory 索引

> 框架 L4 层：持久化记忆索引。分为两大类 — AI 行为约束（给 AI 读） + 知识与项目状态（给人读）。

---

## 索引总表

### 一、AI 行为约束（偏好 / 规则 / 操作授权）

| 分类       | 条目     | 摘要                                                                 | 更新时间   |
|:-----------|:---------|:--------------------------------------------------------------------|:-----------|
| **行为约束** | 操作授权（命令行直接执行） | 含Skill安装/脚本执行，权威见GLOBAL-RULES.md | 2026-05-27 |
| **行为约束** | 文件操作红线（只删自己文件） | 历史教训：2026-05-19误删btc server；2026-07-08违规擅移25 PDF。权威见GLOBAL-RULES.md | 2026-07-08 |
| **行为约束** | 修改用户文件必须明确授权 | 「看看/合理吗」=征求意见→给分析+方案→等明确「按这个改」再动（2026-07-06违规） | 2026-07-06 |
| **行为约束** | 索引/文档规范 | index.md必加/表格对齐/时间线倒序/inbox归档写archive-log。权威见GLOBAL-RULES.md | 2026-07-07 |
| **行为约束** | 新文件先探索目录再落位 | list_dir 放对位置（2026-06-10） | 2026-06-10 |
| **行为约束** | 批判性立场（铁律第5条） | 不偏向/每次先讲用户可改点，权威见GLOBAL-RULES.md | 2026-07-19 |
| **行为约束** | 学习讨论收尾纪律（费曼复述） | ≥3层后提醒复述+面试官考核（权威见GLOBAL-RULES.md） | 2026-07-29 |
| **行为约束** | 小修改不频繁推送 | 积累到量再统一推 | 2026-07-07 |
| **行为约束** | 会话沉淀闭环（强制无例外） | 对话结束前必须在03-Memory/sessions/生成session+更新recent-sessions.md/index.md，不依赖用户提醒（自检清单第7项，2026-08-22升级），权威见GLOBAL-RULES.md | 2026-08-22 |
| **行为约束** | TODO-DASHBOARD 双向同步 | 新增待办同步到看板/完成打勾同步回源文件；个人待办统一整合进看板（不再单独维护 personal/todo.md，2026-08-17 已删除），权威见GLOBAL-RULES.md | 2026-08-17 |

### 二、知识与项目状态（技能 / 项目 / 参考资料 / 知识条目）

| 分类       | 条目                        | 摘要                                                                         | 关联项目         | 更新时间   |
|:-----------|:----------------------------|:----------------------------------------------------------------------------|:----------------|:-----------|
| **User**   | 技能和经验                  | 网络设备/嵌入式/C/Python/TSN/驱动/TFLM                                         | 全部            | 2026-04-27 |
| **User**   | 完整职业画像（2026-06-12更新） | ~9年嵌入式经验：爱博精电6年+新华三3年。S级：自研RTOS/TSN六协议/DSP优化。详细分析：[[career-development/interview-project-summaries/01-company-interviews/career-profile|职业画像与求职分析]] | career-development | 2026-06-12 |
| **User**   | 习惯和偏好                  | 简洁直接、自动化脚本、配置备份                                                   | 全部            | 2026-04-27 |
| **User**   | 路径和配置                  | 项目关键路径映射                                                               | 全部            | 2026-05-23 |
| **User**   | 当前薪资                    | 30K×16=53W/年，底线65-70W                                                      | 全部            | 2026-06-10 |
| **Project** | 嵌入式AI学习                | TFLM 源码驱动学习。Week 1 ✅已完成；Week 2/3 课程材料已建（待学）；总计 3 课文件，1833 个 TFLM 源码文件 | 01-Projects/embedded-ai-learning | 2026-07-24 |
| **Project** | 网络设备调试                | 工业交换机问题排查（IE4120/IE4300/IE4500）                                        | 01-Projects/network-device-debug | 2026-05-07 |
| **Project** | 腾讯云AI编程培训             | 培训资料归档                                                                   | 01-Projects/tencent-cloud-training | 2026-05-07 |
| **Project** | BTC温度仪表盘               | 加密货币市场可视化                                                              | 01-Projects/btc-temperature-gauge | 2026-05-07 |
| **Project** | wechat-radar                | AI驱动公众号智能日报，环境就绪                                                    | 01-Projects/wechat-radar | 2026-06-10 |
| **Project** | family-hub                 | 家庭决策枢纽（投资/健康/社保/信用/AI）                                            | 01-Projects/family-hub | 2026-07-06 |
| **Project** | 自动化任务实验              | TRAE 自动化工作流：飞书推送/嵌入式AI日报/公司运营日报/推特抓取                     | 01-Projects/automated-task | 2026-07-22 |
| **Project** | 个人网站                  | 静态个人站点：文章发布与一键部署脚本                                              | 01-Projects/personal-website | 2026-07-22 |
| **Project** | 话题工作台(topics)         | 特定技术话题讨论暂存（PBR策略路由分析/TSN协议分析）                               | 01-Projects/topics | 2026-07-22 |
| **Project** | 求职面试-今日宜休ISHO        | 面试讨论中，已完成全面匹配度分析                                                  | career-development | 2026-05-29 |
| **Project** | 求职面试-活跃推进           | 已面7家后仍在推进：盖洛普落地/简历改写/话术加才干句。核心弹药库 tech-interview-notes.md（44KB）+ career-strategy/（盖洛普测评+行动计划） | career-development | 2026-08-11 |
| **Project** | 个性化Agent开发              | 待规划：李笑来认知蒸馏Agent、健康Agent等                                           | 01-Projects/personal-agents | 2026-06-17 |
| **Reference** | S5120V8逻辑寄存器手册       | 硬件参考                                                                      | network-device-debug | —         |
| **Reference** | Wireshark 抓包             | 网络分析工具                                                                   | network-device-debug | —         |
| **Knowledge** | ContextStack四层架构        | 框架说明                                                                     | 全部            | 2026-04-29 |
| **Knowledge** | 框架审计报告 2026-06-10     | 全量审计：3严重+5中等+3轻微，附优先级行动清单                                    | 全部            | 2026-06-10 |
| 框架结构审计 2026-08-20     | 索引滞后修复/.gitignore 修订/AI 自检清单 v3.3/CodeBuddy vs 03-Memory 同步                                    | 全部            | 2026-08-20 |
| **Knowledge** | 九号公司 FreeRTOS 面经      | 牛客网14题完整答案                                                             | career-development | 2026-06-10 |
| **Knowledge** | note-organizer Skill        | 智能笔记整理，5种类型识别                                                        | 全部            | 2026-05-26 |
| **Knowledge** | 自主自我改进循环研究         | Hermes Agent四层记忆+三层飞轮                                                     | 全部            | 2026-06-03 |
| **Knowledge** | CPO产业链投资标的精选        | 光模块/CPO深度研究                                                              | 全部            | 2026-06-04 |
| **Knowledge** | 图解Skill—AI提效实战指南     | 宝玉《图解Skill》配套资源                                                         | 全部            | 2026-06-05 |
| **Knowledge** | 人生投资自检清单20问         | 定期自检模板                                                                   | 全部            | 2026-06-05 |
| **Knowledge** | 非京籍孩子升学路径全解析      | 6条升学路子：积分落户/工居/回老家/国际学校/中职贯通/天津落户                                | 全部            | 2026-06-05 |
| **Knowledge** | 面试经验总库               | 7家公司完整面试记录+教训+5条红线+赛道P0考点+提问策略                                   | career-development | 2026-06-10 |
| **Knowledge** | interview-prep Skill       | 输入公司名自动生成8模块面试准备清单                                                 | 全部            | 2026-06-10 |
| **Knowledge** | framework-maintenance      | 工具修复/框架演进决策/记忆系统分工（.workbuddy vs 03-Memory）                        | 全部            | 2026-07-31 |
| **Knowledge** | framework-structure-audit-2026-08-20 | 框架结构审计：索引滞后修复/.gitignore 修订/AI 自检清单/CodeBuddy vs 03-Memory 同步问题 | 全部 | 2026-08-20 |
| **Knowledge** | framework-audit-2026-06-10     | 全量审计：3严重+5中等+3轻微问题（2026-08-20 已从 knowledge/ 迁至 sessions/）                                    | 全部            | 2026-06-10 |
| **Knowledge** | Academic Research Skills 深度分析 | Claude Code 学术研究Skill套件：32+Agent、完整性门、引用验证、反讨好机制                      | 全部            | 2026-06-11 |
| **Knowledge** | OpenSquilla MetaSkill 分析   | Agent自组织技能新范式：动态发现+自动编排工作流，解决「组合灾难」                                  | 全部            | 2026-06-11 |
| **Knowledge** | ClawHunt Agent众包市场分析    | Agent任务众包平台：需求方挂任务→Agent竞标→法币结算。当前收入微薄，适合观察学习                      | 全部            | 2026-06-16 |
| **Knowledge** | 八字紫微排盘Skill (bazi-ziwei) | AI八字+紫微斗数排盘：算法精准排盘+格局补层+综合印证+水墨风HTML海报                           | 全部            | 2026-06-17 |
| **Knowledge** | 半导体材料国产替代投资机会     | 五大紧缺材料赛道：氮化镓/靶材/硅微粉/ABF板/光刻胶。英飞凌GaN被禁催化，江丰电子业绩已验证              | family-hub      | 2026-06-17 |
| **Knowledge** | 小黑怪诞正文配图 Skill       | Codex Skill：把中文文章的认知锚点变成16:9手绘怪诞配图。小黑IP+纯白背景+少量红橙蓝批注。适合知识型/方法论内容配图 | 全部 | 2026-06-20 |
| **Knowledge** | X推文自动化研究归档          | 闲鱼自动化/封号风险、全流程自动化可行性、24小时微信推送方案、飞书AI配置、信息源推荐。含7项待办        | 全部 | 2026-06-20 |
| **Knowledge** | AI Berkshire投资研究Skills    | 投资研究AI助手：公司研究/财报分析/行业筛选/组合回顾等5个核心技能                                 | 全部            | 2026-07-06 |
| **Knowledge** | Web-Pack素材采集Skill        | 网页主题完整素材包采集，超越传统剪藏工具，支持深度抓取和图片本地化                                  | 全部            | 2026-07-06 |
| **Knowledge** | 技术面试笔记（tech-interview-notes） | 面试技术弹药库：Tickless/PendSV/CNN算子/Dropout翻转补偿/启动流程等，TODO看板多项复述作业引用 | career-development | 2026-08-10 |
| **Knowledge** | 盖洛普测评与落地行动计划    | Harvey盖洛普优势测评 + 三主线落地（求职/投资/家庭）+ 才干检查清单 | career-development | 2026-08-11 |
| **Knowledge** | 贝版投资方法论《一年只需出手两三次》 | 承认无知/大部分Beta+小部分Alpha/等带血筹码/止损纪律/抄系统不抄代码；与 family-hub 纪律对照 | family-hub | 2026-08-24 |
| **Knowledge** | 天玑《我的一些阅读和学习方法~》 | 英语输入输出闭环/一目十行泛读(为精读服务)/70-20-10精力分层复习法；与用户学习体系对照 | 全部 | 2026-08-25 |
| **Knowledge** | lijigang Codex技能集研究 | Write Prompt作者，ljg-skills 7.3k star；技能工程化/认知方法论产品化/输出闭环；用户判定很牛后续学习 | 全部 | 2026-09-02 |

---

## 一、AI 行为约束

> **权威源**：所有通用行为规则（铁律/安全红线/授权/文档规范/Git）以 `GLOBAL-RULES.md` 为唯一权威，本文件只留索引 + Memory 特有历史教训，不重复正文。

---

## 二、知识与项目状态

### User — 技能与偏好

#### 技能和经验
- 工作领域: 网络设备、嵌入式开发、TSN
- 编程语言: C语言、Python
- 工作经验: 网络设备开发调试、TSN时间敏感网络、驱动开发、协议栈开发

#### 习惯和偏好
- 沟通风格: 简洁直接
- 工作方式: 偏好自动化脚本
- 文档习惯: 重要配置备份和版本管理
- H3C 交换机风格举例（非华为/Cisco）

#### 路径和配置
- Skill保存路径: `02-Knowledge/skills/`
- VSCode配置路径: `05-Tools/vscode-config/`
- 项目路径: `01-Projects/`
- 知识库路径: `02-Knowledge/`
- 学习进度更新规则：必须等用户反馈学习完成后再更新

---

### Project — 活跃项目

#### 嵌入式AI学习
- 状态: 学习阶段（Week 1 ✅已完成，Week 2/3 课程材料已建待学）
- TFLM源码: `01-Projects/embedded-ai-learning/source/tflite-micro-main`（1833 个文件）
- 技术栈: TensorFlow Lite Micro, C/C++, 嵌入式开发, PyTorch（辅）
- 学习原则: TFLM为主,PyTorch为辅
- 课程进度: Week 1 ✅ (TFLM四组件+hello_world) | Week 2 🔄 (模型转换) | Week 3 🔄 (CNN+数据+训练) — 均待学习
- GitHub: https://github.com/Eoser-Harvey/ContextStack

#### 网络设备调试
- 状态: 进行中
- 涉及设备: IE4120U-18TP（已解决）、IE4300U-10P（已解决）、IE4500（进行中）

#### 腾讯云AI编程培训
- 状态: 培训资料整理阶段

#### 求职面试 — 九号公司
- 状态: 面经整理完成
- 文件: `02-Knowledge/career-development/interview-project-summaries/01-company-interviews/`
- 已有: 一面复盘、深度复盘、牛客网14题答案

#### 求职面试 — 今日宜休 ISHO
- 状态: 面试讨论中
- 文件: `02-Knowledge/career-development/interview-project-summaries/01-company-interviews/isho-analysis.md`

#### 求职面试 — 已面7家公司
- 状态: 全部结束（蚂蚁/加速进化/昉擎/西门子/思朗/宜休/九号），经验已归档
- 文件: `02-Knowledge/skills/interview-prep/面试经验库.md`
- 教训汇总: C底层/启动汇编/英语口语/不问裁员/岗位优先项/笔试编程题

#### wechat-radar
- 状态: 环境就绪
- 描述: AI 驱动微信公众号智能日报
- 文件: `01-Projects/wechat-radar/`

#### family-hub
- 状态: 进行中
- 描述: 家庭决策枢纽 — 投资追踪/健康管理/社保规划/信用管理/AI第二曲线
- 文件: `01-Projects/family-hub/`

#### 自动化任务实验 (automated-task)
- 状态: 活跃
- 描述: TRAE 自动化工作流集合 — 飞书定时推送、嵌入式AI日报、公司运营日报、推特 feed 抓取
- 文件: `01-Projects/automated-task/`

#### 个人网站 (personal-website)
- 状态: 活跃
- 描述: 静态个人站点，文章发布与一键部署
- 文件: `01-Projects/personal-website/`

#### 话题工作台 (topics)
- 状态: 活跃
- 描述: 特定技术话题讨论暂存（PBR 策略路由分析、TSN 协议分析）
- 文件: `01-Projects/topics/`

---

### Reference — 参考资料

#### 文档
- S5120V8逻辑寄存器手册
- 网络知识库.docx、芯片手册目录、驱动协议.txt

#### 工具
- 抓包: Wireshark
- 串口: SecureCRT、MobaXterm
- 对比: Beyond Compare

---

### Knowledge — 知识条目

| 条目                     | 说明                                               | 位置                                                                          |
|:-------------------------|:---------------------------------------------------|:------------------------------------------------------------------------------|
| ContextStack四层架构      | 框架完整说明                                        | `03-Memory/knowledge/contextstack-four-layer-framework.md`                   |
| 框架审计报告 2026-06-10   | 全量审计：3严重+5中等+3轻微（已迁至 sessions/）        | `03-Memory/sessions/session-20260610-framework-audit.md`                          |
| 框架结构审计 2026-08-20   | 索引滞后修复/.gitignore 修订/AI 自检清单 v3.3         | `03-Memory/sessions/session-20260820-framework-audit.md`                          |
| 九号公司 FreeRTOS 面经   | 牛客网14题完整答案                                   | `02-Knowledge/career-development/interview-project-summaries/01-company-interviews/ninebot-questions.md` |
| note-organizer Skill     | 智能笔记整理，5种内容类型识别                         | `.codebuddy/skills/note-organizer/`                                            |
| 自主自我改进循环研究      | Hermes Agent四层记忆+三层飞轮                          | `02-Knowledge/inbox/autonomous-self-improving-loops-research.md`              |
| CPO产业链投资标的精选     | 光模块/CPO深度研究                                    | `02-Knowledge/inbox/cpo-industry-investment-guide.md`                         |
| 图解Skill—AI提效实战指南  | 宝玉《图解Skill》配套资源                              | `02-Knowledge/inbox/illustrated-agent-skills-book.md`                         |
| 人生投资自检清单20问      | 定期自检模板                                         | `02-Knowledge/inbox/life-philosophy-20-questions.md`                          |
| 非京籍孩子升学路径全解析   | 6条升学路子完整解析                                    | `02-Knowledge/inbox/non-beijing-resident-education-paths.md`                 |
| 面试经验总库             | 7家公司面试记录+教训+话术                               | `02-Knowledge/skills/interview-prep/面试经验库.md`                            |
| interview-prep Skill    | 输入公司名自动生成8模块面试准备清单                       | `02-Knowledge/skills/interview-prep/`                                         |
| Crypto API 参考手册       | 主流加密货币交易所API使用指南                            | `03-Memory/knowledge/crypto-api-reference.md`                                |

---

> **维护规则**：AI 行为约束写入"一"区；项目状态/知识索引写入"二"区。两者都在本文件内，统一管理，便于迁移。
