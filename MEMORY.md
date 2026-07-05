# Memory 索引

> 框架 L4 层：持久化记忆索引。分为两大类 — AI 行为约束（给 AI 读） + 知识与项目状态（给人读）。

---

## 索引总表

### 一、AI 行为约束（偏好 / 规则 / 操作授权）

| 分类 | 条目 | 摘要 | 更新时间 |
|------|------|------|----------|
| **行为约束** | 不创建不必要的中介文件 | 优先编辑现有文件 | 2026-04-27 |
| **行为约束** | 命令行操作直接执行不确认 | 含 Skill 安装/下载/脚本执行，均自动执行 | 2026-05-27 |
| **行为约束** | 新文件夹/笔记自动加 index.md | 目录结构规范 | 2026-05-07 |
| **行为约束** | 文件操作红线 | 只删/改自己创建的文件，不碰别人项目文件 | 2026-05-19 |
| **行为约束** | 及时清理无用文件 | debug.log/.uploads 等临时文件即查即删 | 2026-05-23 |
| **行为约束** | .codebuddy/ 不同步 Git | IDE 本地治理规则，.gitignore 忽略 | 2026-05-23 |
| **行为约束** | inbox 归档规则 | 归档写入 archive/archive-log.md，不单独建归档文件 | 2026-05-24 |
| **行为约束** | 新文件先探索目录再落位 | 新建前 `list_dir` 目标子文件夹，放入框架正确位置 | 2026-06-10 |
| **行为约束** | 资产报告按月生成规则 | 运行报告脚本前确认月份：当月报告文件存在则直接更新，不存在则复制上月报告重命名后更新。禁止修改非当月历史报告 | 2026-07-01 |

### 二、知识与项目状态（技能 / 项目 / 参考资料 / 知识条目）

| 分类 | 条目 | 摘要 | 关联项目 | 更新时间 |
|------|------|------|----------|----------|
| **User** | 技能和经验 | 网络设备/嵌入式/C/Python/TSN/驱动/TFLM | 全部 | 2026-04-27 |
| **User** | 完整职业画像（2026-06-12更新） | ~9年嵌入式经验：爱博精电6年+新华三3年。S级：自研RTOS/TSN六协议/DSP优化。详细分析：[[career-development/interview-project-summaries/interview-prep/职业画像与求职分析]] | career-development | 2026-06-12 |
| **User** | 习惯和偏好 | 简洁直接、自动化脚本、配置备份 | 全部 | 2026-04-27 |
| **User** | 路径和配置 | 项目关键路径映射 | 全部 | 2026-05-23 |
| **User** | 当前薪资 | 30K×16=53W/年，底线65-70W | 全部 | 2026-06-10 |
| **Project** | 嵌入式AI学习 | TFLM 源码驱动学习，Week 1 Day 1 完成 | 01-Projects/embedded-ai-learning | 2026-05-13 |
| **Project** | 网络设备调试 | 工业交换机问题排查（IE4120/IE4300/IE4500） | 01-Projects/network-device-debug | 2026-05-07 |
| **Project** | 腾讯云AI编程培训 | 培训资料归档 | 01-Projects/tencent-cloud-training | 2026-05-07 |
| **Project** | BTC温度仪表盘 | 加密货币市场可视化 | 01-Projects/btc-temperature-gauge | 2026-05-07 |
| **Project** | wechat-radar | AI驱动公众号智能日报，环境就绪 | 01-Projects/wechat-radar | 2026-06-10 |
| **Project** | family-hub | 家庭决策枢纽（投资/健康/社保/信用/AI） | 01-Projects/family-hub | 2026-07-06 |
| **Project** | 求职面试-今日宜休ISHO | 面试讨论中，已完成全面匹配度分析 | career-development | 2026-05-29 |
| **Project** | 个性化Agent开发 | 待规划：李笑来认知蒸馏Agent、健康Agent等 | 01-Projects/personal-agents | 2026-06-17 |
| **Reference** | S5120V8逻辑寄存器手册 | 硬件参考 | network-device-debug | — |
| **Reference** | Wireshark 抓包 | 网络分析工具 | network-device-debug | — |
| **Knowledge** | ContextStack四层架构 | 框架说明 | 全部 | 2026-04-29 |
| **Knowledge** | 框架审计报告 2026-06-10 | 全量审计：3严重+5中等+3轻微问题，附优先级行动清单 | 全部 | 2026-06-10 |
| **Knowledge** | 九号公司 FreeRTOS 面经 | 牛客网14题完整答案 | career-development | 2026-06-10 |
| **Knowledge** | note-organizer Skill | 智能笔记整理，5种类型识别 | 全部 | 2026-05-26 |
| **Knowledge** | 自主自我改进循环研究 | Hermes Agent四层记忆+三层飞轮 | 全部 | 2026-06-03 |
| **Knowledge** | CPO产业链投资标的精选 | 光模块/CPO深度研究 | 全部 | 2026-06-04 |
| **Knowledge** | 图解Skill—AI提效实战指南 | 宝玉《图解Skill》配套资源 | 全部 | 2026-06-05 |
| **Knowledge** | 人生投资自检清单20问 | 定期自检模板 | 全部 | 2026-06-05 |
| **Knowledge** | 非京籍孩子升学路径全解析 | 6条升学路子：积分落户/工居/回老家/国际学校/中职贯通/天津落户 | 全部 | 2026-06-05 |
| **Knowledge** | 面试经验总库 | 7家公司完整面试记录+教训+5条红线+赛道P0考点+提问策略 | career-development | 2026-06-10 |
| **Knowledge** | interview-prep Skill | 输入公司名自动生成8模块面试准备清单 | 全部 | 2026-06-10 |
| **Knowledge** | Academic Research Skills 深度分析 | Claude Code 学术研究Skill套件：32+Agent、完整性门、引用验证、反讨好机制 | 全部 | 2026-06-11 |
| **Knowledge** | OpenSquilla MetaSkill 分析 | Agent自组织技能新范式：动态发现+自动编排工作流，解决「组合灾难」 | 全部 | 2026-06-11 |
| **Knowledge** | ClawHunt Agent众包市场分析 | Agent任务众包平台：需求方挂任务→Agent竞标→法币结算。当前收入微薄，适合观察学习 | 全部 | 2026-06-16 |
| **Knowledge** | 八字紫微排盘Skill (bazi-ziwei) | AI八字+紫微斗数排盘：算法精准排盘+格局补层+综合印证+水墨风HTML海报 | 全部 | 2026-06-17 |
| **Knowledge** | 半导体材料国产替代投资机会 | 五大紧缺材料赛道：氮化镓/靶材/硅微粉/ABF板/光刻胶。英飞凌GaN被禁催化，江丰电子业绩已验证 | family-hub | 2026-06-17 |
| **Knowledge** | 小黑怪诞正文配图 Skill | Codex Skill：把中文文章的认知锚点变成16:9手绘怪诞配图。小黑IP+纯白背景+少量红橙蓝批注。适合知识型/方法论内容配图 | 全部 | 2026-06-20 |
| **Knowledge** | X推文自动化研究归档 | 闲鱼自动化/封号风险、全流程自动化可行性、24小时微信推送方案、飞书AI配置、信息源推荐。含7项待办 | 全部 | 2026-06-20 |

---

## 一、AI 行为约束

> 以下条目约束 AI 的编码和操作行为，跨 session 持久生效。

### 文件操作
- ⛔ **文件操作红线**：只删除/修改自己创建的文件，绝不碰别人项目文件夹下的任何文件（2026-05-19，教训：误删 btc-temperature-gauge 的 server.py/server.js）
- ⛔ 删除前必须确认归属：不确定来源的文件，宁可留着也不删
- **及时清理**：无用文件（debug.log/.uploads 等临时文件）即查即删（2026-05-23）
- **临时文件自动删除**：脚本执行过程中产生的临时文件（如 `_xxx_temp.py`、`_commit_msg.txt` 等），用完后直接 DeleteFile 删除，无需询问用户确认（2026-06-11）
- **新文件先探索目录结构**：新建前 `list_dir` 目标子文件夹，确保放入框架正确位置（2026-06-10）
- **资产报告按月生成**：运行 `_gen_report_v2.py` 前确认当前月份，只更新当月报告。当月报告文件不存在时先复制上月报告再更新，禁止修改历史月份报告（2026-07-01）

### 操作授权
- 命令行操作（文件夹编辑/重命名/删除等）直接执行，不需用户确认（2026-05-07/27）
- Skill 安装/下载/脚本执行均自动执行

### 文档规范
- 不创建不必要的中介文件，优先编辑现有文件（2026-04-27）
- 每创建新文件夹或笔记时，自动添加 index.md（2026-05-07）
- inbox 归档统一写入 archive/archive-log.md，不单独建归档文件（2026-05-24）

### Git 规范
- .codebuddy/ 不同步 Git，.gitignore 忽略（2026-05-23）
- 推送到远程统一使用 `05-Tools/backup/auto_push.ps1` 脚本；脚本失败时手动推送，但 commit message 遵循脚本格式 `auto: [N files] 目录摘要 (扩展名汇总)`（2026-06-11）

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
- 状态: 学习阶段
- TFLM源码: 本地 TFLM 源码目录
- 技术栈: TensorFlow Lite Micro, C/C++, 嵌入式开发
- 学习原则: TFLM为主，PyTorch为辅
- 当前进展: Week 1 Day 1 完成
- GitHub: https://github.com/Eoser-Harvey/ContextStack

#### 网络设备调试
- 状态: 进行中
- 涉及设备: IE4120U-18TP（已解决）、IE4300U-10P（已解决）、IE4500（进行中）

#### 腾讯云AI编程培训
- 状态: 培训资料整理阶段

#### 求职面试 — 九号公司
- 状态: 面经整理完成
- 文件: `02-Knowledge/career-development/interview-project-summaries/company-interviews/`
- 已有: 一面复盘、深度复盘、牛客面经14题答案

#### 求职面试 — 今日宜休 ISHO
- 状态: 面试讨论中
- 文件: `02-Knowledge/career-development/interview-project-summaries/company-interviews/isho-analysis.md`

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

| 条目 | 说明 | 位置 |
|------|------|------|
| ContextStack四层架构 | 框架完整说明 | `03-Memory/knowledge/contextstack-four-layer-framework.md` |
| 框架审计报告 2026-06-10 | 全量审计：3严重+5中等+3轻微 | `03-Memory/knowledge/framework-audit-2026-06-10.md` |
| 九号公司 FreeRTOS 面经 | 牛客网14题完整答案 | `career-development/interview-project-summaries/company-interviews/` |
| note-organizer Skill | 智能笔记整理，5种内容类型识别 | `.codebuddy/skills/note-organizer/` |
| 自主自我改进循环研究 | Hermes Agent四层记忆+三层飞轮 | `02-Knowledge/inbox/` |
| CPO产业链投资标的精选 | 光模块/CPO深度研究 | `02-Knowledge/inbox/` |
| 图解Skill—AI提效实战指南 | 宝玉《图解Skill》配套资源 | `02-Knowledge/skills/` |
| 人生投资自检清单20问 | 定期自检模板 | `02-Knowledge/inbox/` |
| 非京籍孩子升学路径全解析 | 6条升学路子完整解析 | `02-Knowledge/inbox/` |
| 面试经验总库 | 7家公司面试记录+教训+话术 | `02-Knowledge/skills/interview-prep/` |
| interview-prep Skill | 输入公司名自动生成8模块面试准备清单 | `02-Knowledge/skills/interview-prep/` |

---

> **维护规则**：AI 行为约束写入"一"区；项目状态/知识索引写入"二"区。两者都在本文件内，统一管理，便于迁移。