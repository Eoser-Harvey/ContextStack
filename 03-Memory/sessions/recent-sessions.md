# 最近会话经验索引

> 每次对话前自动读取，加载最近经验
> 
> **规则**: 保留最近 10 次会话精华，按时间倒序

---

## 快速参考

| 日期 | 主题 | 关键经验 | 文件 |
|------|------|---------|------|
| 2026-08-31 | 社区采集推送工具链 + 面试准备 + LLM-Wiki范式研究 | 新建 community-collection-push 工具链(采集/画像/飞书推送/每日AI资讯)；面试框架(自我+Linux应用层+环形缓冲三追问+嵌入式C)；inbox暂存→范式提炼→入库；.gitignore忽略Office锁文件 | `session-20260831-auto-catchup.md` |
| 2026-08-29 | 修 auto_push Step2 exit0 漏推 bug + 公司设立/面试沉淀 | ⚠️"脚本exit0≠所有改动已推送"（8/25~8/28漏推投资改动近2天）；Step2改$aheadPushed标志不再早退；加$env:TEMP三级fallback；本地bare隔离测试法 | `session-20260829-auto-catchup.md` |
| 2026-08-28 | family-hub 投资系统月内更新（auto-catchup） | holdings 加仓/换仓/新建仓+三份报告同步；⚠️当日改了未提交致沉淀断档；投资更新闭环(数据源→历史→报告需同提交) | `session-20260828-auto-catchup.md` |
| 2026-08-25 | 天玑《我的一些阅读和学习方法~》入库 | 英语输入输出闭环/一目十行泛读/70-20-10精力分层；与用户学习体系对照（费曼/面试mock同源）；警示收藏式学习；文章入库SOP二次验证可Skill化 | `session-20260825-tianji-learning-methods.md` |
| 2026-08-24 | 贝版《一年只需出手两三次》投资方法论入库 + family-hub 挂载 | 提炼6组观点；与现有纪律对照表（识别"自己恐慌卖 vs 别人恐慌买"张力、CRCL集中度反例）；分层落位(inbox知识+REFERENCES挂载)；三级索引同步 | `session-20260824-bayfamily-invest-methodology.md` |
| 2026-08-23 | 框架深度重新学习（WorkBuddy 接入）+ 会话沉淀闭环 | 全量重读四层架构+v3.4 自检清单 8 项；确认"后续基于框架沟通"；双工作区记忆分工(.workbuddy vs 03-Memory)；沉淀本次 session | `session-20260823-framework-relarn.md` |
| 2026-08-22 | 投资系统账本全量更新 + 报告引擎3处修复 + "禁止推算"规则固化 | 合并账户(燕/韩伟币安)；CRCL整体均价$66.66；脚本修复(按资产+均价列/第九节接trade_log/第十节上期价)；华盛通成本推算被骂→固化"禁止推算不确定必问"(GLOBAL-RULES v3.4) | `session-20260822-investment-system-update.md` |
| 2026-08-22 | ContextStack 框架完整重新学习 + 常驻规则固化 + 会话沉淀补闭环 | 完整重读四层架构；固化"每次对话5条常驻规则"到记忆；补今天会话沉淀（上次2026-08-20那条实为审计，非学习） | `session-20260822-framework-relarn.md` |
| 2026-05-28 18:20 | Ruflo研究 + 会话沉淀机制设计 | 先研究再设计、分层落地、机制闭环、模板化思维 | `session-20260528-1820.md` |
| — | — | — | — |

> ⚠️ 2026-05-28 至 2026-08-20 之间 3 个月无会话归档，违反框架"每次对话后更新"规则。
> 主要原因：多数会话产出直接写入项目 STATE.md / 03-Memory/knowledge/framework-maintenance.md，
> 未单独沉淀为 session 文件。后续可考虑：重要里程碑会话双写（session 文件 + 项目 STATE）。

---

## 模式库（跨会话复用）

### 任务处理模式
- **研究类任务标准流程**: 阅读来源 → 提取核心 → 对比分析 → 落地建议 → 优先级排序
- **分层实施策略**: P0快速见效，P1-P4逐步建设

### 错误避免模式
- 避免初期理解偏差，先完整阅读再下结论
- 复杂脚本需预留优化空间

### 效率优化模式
- 机制设计必须闭环（沉淀+读取+应用）
- 模板化降低后续使用门槛
- 预置常用模式减少重复思考

---

## 完整会话记录

### 2026-08-31: 社区采集推送工具链 + 面试准备 + LLM-Wiki 知识范式研究（auto-catchup 补齐）
- **核心产出**: 当日 4 commits / 16 files，工作区已 clean。① 新建 `01-Projects/.../6.community-collection-push/` 工具链：`collect_community.py`(采集) / `profile_loader.py`(账号画像) / `push_lark.py`(飞书推送) / `send_daily_ai_news.py`(每日AI资讯调度)，配 `index.md`+`.gitignore`（经历 `63d957c` 初建、`0711674` 重排）；② 千寻智能 MS 清单增量补「自我介绍+Linux应用层能力+环形缓冲三追问」(+132行) + 新增 `embedded-c-algorithm-interview.md`(含SyncE/PTP时钟图)；③ `02-Knowledge/inbox/LLM-Wiki-知识编译范式研究.md`(137行)；④ `codebuddy-chat-manager/chat-index.{json,md}` 更新；⑤ 北京公司账务/社保 + 信用卡主控表更新。
- **关键决策**: 依"仅缺失且确有内容才创建"生成 auto-catchup；未覆盖任何正常 session。注意 `community-collection-push` 目录初建时未定清"采集/推送/调度"职责边界，导致 `0711674` 整体删除重排（先散后收）。
- **可复用**: 社区采集推送 SOP（采集→画像→飞书推送→每日资讯调度 + index/.gitignore）；面试准备框架（自我介绍/核心能力/高频追问/专项算法/项目配图）；知识摄入分层（inbox→范式提炼→入库）；.gitignore 忽略 Office 锁文件。

### 2026-08-29: 修 auto_push_home.ps1 Step2 越早退出 bug + 多类知识沉淀（auto-catchup 补齐）
- **核心产出**: 修复 `05-Tools/backup/auto_push_home.ps1` 定时推送脚本的潜伏 bug（Step 2 push 成功后 `exit 0`，导致「ahead commit + 未提交改动」并存时未提交改动被静默跳过，8/25~8/28 漏推投资改动近两天）；改用 `$aheadPushed` 标志变量使 push 后继续走 Step 3 提交未提交改动；顺带修 `$env:TEMP` 空值健壮性（三级 fallback）。当日另沉淀北京公司设立（社保方案/记账账本/完成日志）、`company/`→`company-h3c/` 目录重组。
- **关键决策**: 用本地 bare 仓库隔离测试 bug 修复（不污染 github），端到端验证 Step 1→2→3→4→5 全链路；区分"脚本 bug"与"临时网络抖动"（后者重跑即成功）。
- **可复用**: 定时任务"假成功"诊断法（日志结尾+源码找 early-return）；脚本修复隔离测试 SOP；自动推送脚本健壮性清单（push 后校验 `git status` 空告警 + 临时路径 fallback）。

### 2026-08-28: family-hub 投资系统月内更新（auto-catchup 补齐）
- **核心产出**: 补齐当日因"改工作区未提交"导致的会话沉淀断档。当日 modified 文件集中在 `01-Projects/family-hub/research/portfolio/`：holdings.yaml（last_updated 2026-08-28，含 CRCL 加仓、MRVL 清仓换仓至 MSTR/ONDO/UNI/SOXL、科创50ETF/HK创新药ETF 新建仓）、portfolio_history.yaml、月度/年度/A8 三份报告。
- **关键决策**: 依"仅缺失且确有内容才创建"原则生成 auto-catchup；未覆盖任何正常 session。
- **可复用**: 投资更新闭环（holdings→history→reports 三者必须同步且同一次 git 提交）；成本记录须写清加权均价过程。

### 2026-08-23: 框架深度重新学习（WorkBuddy 接入）+ 会话沉淀闭环
- **核心产出**: 全量重读四层架构（L1 v3.4 含 8 项自检清单 / L2 PROJECT-RULES 实例 / L3 规范文档 / L4 MEMORY 索引 + TODO 看板 + 工作台实例 + 最近会话）；确认用户"后续基于此框架沟通"；识别 08-22 后变更（v3.4 新增禁止推算项）
- **关键决策**: 记忆两层分工落地（AI 工作记忆→.workbuddy/memory，框架长期资产→03-Memory）；本会话为纯学习，沉淀价值在接入确认+状态快照
- **可复用**: 框架接入 SOP（L1→L4→工作台→会话→沉淀）；双工作区定位注意（WorkBuddy 工作区 vs ContextStack 根目录）

### 2026-08-22: ContextStack 框架完整重新学习 + 常驻规则固化 + 会话沉淀补闭环
- **核心产出**: 完整重读四层架构（L1-L4 核心文件 + 各层目录落地）；把"每次对话必须遵循的5条常驻规则"写入03-Memory；补今天这次会话沉淀
- **关键决策**: 修正 recent-sessions.md 误把 2026-08-20（实为框架审计）标成"框架学习"；新增 session-20260822 文件
- **可复用**: 框架审计/学习方法论（规则一致性 vs 实际执行检查）



<!-- 最近10次会话的摘要，每次对话后更新 -->

### 2026-08-20: ContextStack 框架完整学习 + 索引同步 + 自检清单设计
- **核心产出**: 完整学习框架四层架构，识别 5 处索引滞后并修复；提出 AI 行为约束自检清单方案
- **关键决策**: 增加「AI 自检清单」到 GLOBAL-RULES.md；.gitignore 改为精确忽略；创建 framework-structure-audit-2026-08-20.md 沉淀到 03-Memory
- **可复用**: 框架审计方法论（规则一致性 vs 实际执行检查）

### 2026-05-28 18:20: Ruflo研究 + 会话沉淀机制设计
- **核心产出**: 设计完整的会话经验沉淀+读取机制
- **关键决策**: 采用P0-P4优先级，从会话沉淀开始落地
- **可复用**: 研究→提炼→落地建议的标准流程

