# TODO 总看板

> **用途**：跨项目统一待办管理，每天开工看这个。
> **规则**：项目 ACTIONS.md 保留详细上下文；本看板只放"要做什么" + 链接回源文件。做完打勾，AI 双向同步。
> **更新**：每次新增/完成时同步更新。

---

## P0（本周必须做）

### 🏢 燕知行公司（有硬期限，逾期影响摇号资格）

> 完整上下文 → [待办与风险管控](01-Projects/family-hub/company-setup/beijing-company-backlog-and-risks.md) ｜ 操作步骤 → [运营手册](01-Projects/family-hub/company-setup/1-beijing-company-ops-manual.md) ｜ 资金账 → [会计账簿](01-Projects/family-hub/company-setup/2-beijing-company-accounting-ledger.md)

- [ ] **9/15 前：补发 8 月工资 5,393.65 元**（对公→薛燕卡，备注 `2026年8月工资`；严禁现金、严禁凑整）
- [ ] **9/11-15：首次个税实报**（8 月属期，应补税额 **0**；**申报 ≠ 缴款，0 税也必须按期报送**）。🔴 扣缴端填报口径：养老 581.60 ／ **医疗 148.40** ／ 失业 36.35 ／ 公积金 840.00 ／ **专项附加扣除 0**（合计 1,606.35）
- [ ] **9/26 前：工商公示实缴 3 万**（gsxt.gov.cn，实缴后 20 日内）＋ 转账回单 / 出资证明归档 ＋ 印花税 7.50 元（营业账簿，2027-01 按年缴）
- [ ] **9/30 前：残疾人就业保障金申报**（0 残疾人也须申报；⚠️ 首年是否适用需先确认）

### Life OS 六模块系统（2026-09-06 起，神鱼框架落地）
- [ ] **inbox 建 index.md 内容地图**（87 篇归档按类别索引，LLM Wiki 落地第一步）→ [参考](02-Knowledge/inbox/LLM-Wiki-知识编译范式研究.md)
- [ ] **健康指标追踪表建表**（先录韩伟近两年体检数据 → 趋势，为 2026-10 蓝医保补买做准备）→ [详情](01-Projects/family-hub/health/)
- [ ] **周复盘模板**（每周日：本周决策/结果/下周3件事）→ [参考](02-Knowledge/inbox/个人成长系统方法论-12项习惯.md)

### 🎯 唯一主任务：端侧AI转型（理论 + 实践，9-7 ~ 9-20）

> 两条线并行，互为支撑：
> - **实践**：Day16 上板（F407 部署 + Parity + 实测延迟）→ 产出实物
> - **理论**：闭卷复述面试题库（训练侧 11 题 + 部署侧 12 题）→ 会讲原理
> 做完 = 有可写进简历的产出物 + 治好"知识复述"病。硬件从 N647 迁移到 F407（小模型不需要 NPU，反而证明跨平台能力）。

| # | 截止 | 动作 | 验收标准 |
|:-:|:-----|:-----|:---------|
| 0 | 9-7（今天） | 确认 F407 型号 + 找模型 .h 文件 | 硬件 + 文件清单 |
| 1 | 9-8~9-9 | 训练侧 11 题闭卷复述（不依赖硬件）+ 数据标注闭环 | 能闭卷讲 A1-A11 |
| 2 | 9-13（周六） | F407 上板 + Parity 自检 + DWT 实测延迟 | `PARITY_PASS` + 延迟数字 |
| 3 | 9-14（周日） | 部署侧不依赖实测的题（B3/B4/B6/B8）闭卷复述 | 能闭卷讲 |
| 4 | 9-15~20 | GitHub + 视频 + 用实测数据答完剩余题 | 可展示产出物 |

→ [面试题库](01-Projects/embedded-ai-learning/knowledge/edge-ai-fundamentals-gaps.md) + [详细计划](01-Projects/embedded-ai-learning/ACTIONS.md#day16-上板执行计划)

### 求职行动（盖洛普落地）
- [ ] **清理求职投递**：只保留机器人底层/汽车电子MCU/智能传感器固件/端侧AI部署 四类 → [详情](02-Knowledge/career-development/career-strategy/盖洛普测评落地行动计划.md#本周执行动作)
- [ ] **简历改写**：盖洛普才干翻译成工程叙事（审慎→5根因修复、纪律→部署契约、成就→全链路）→ 同上
- [ ] **面试话术加才干句**：「纪律+成就+审慎+公平 = 把事情做到极致」→ 同上

---

## P1（本月要做）

### 🏢 燕知行公司（10–11 月）
- [ ] **10/10：发 9 月工资 + Q3 绩效奖金 4,000 元**（🔴 **2026 年个税补救核心动作**，属期 2026-10 → 11 月入库）→ 转账 **9,388.22 元**，备注 `2026年9月工资+Q3绩效奖金`
- [ ] **10/15 前：Q3 季报**（增值税 2 子目 + 企业所得税 + 城建税 + 教育费附加 + 地方教育附加，共 6 项零申报）
- [ ] **11/1-15：个税实报（10 月属期，应补 ≈5.43 元）→ 2026 年税款入库 → 摇号年度记录成立** 🎯
- [ ] **弟弟入职准备**：合同 + 社保 + 公积金 + 发工资（⚠️ **北京社保卡须先办，无卡不操作**）；居住证先办登记卡（满 6 个月换证）
- [ ] **固化月 / 季 / 年操作清单 + 公司异常风险监控方案**（把运营流程从"人记"改为"系统提醒"）

### Life OS 六模块系统
- [ ] **定义 CRCL/MRVL/DRAM 卖出信号**（策略文档"待完善"挂太久，MA120 定不下来仓位就不该动）→ [详情](01-Projects/family-hub/research/investment-strategy.md)
- [ ] **归档流程升级**（raw 原文 + wiki 编译层两层 + 查询写回，分析结论不再死在聊天记录）→ [参考](02-Knowledge/inbox/LLM-Wiki-知识编译范式研究.md)
- [ ] **消费决策记录模板**（选品→比价→买入→用后反馈，每件5行，轻量化）→ [详情](01-Projects/family-hub/purchases/)
- [ ] **教育升学决策系统化**（非京籍6条升学路，放进人生导航）→ [参考](02-Knowledge/inbox/非京籍孩子升学路径全解析.md)

### 框架治理（2026-08-20 起）
- [ ] **AI 行为约束自检清单 Skill 化**：把 GLOBAL-RULES.md v3.3 的 6 项会话开始自检清单抽取为 `02-Knowledge/skills/ai-self-check/` Skill，配置为 always-applied（类似 karpathy-guidelines），让每次会话开始时自动注入到 system prompt，对抗"加载规则 ≠ 遵守规则"漏洞（已记录 4 次违规教训）。配套用户抽查机制兜底。→ [详情](GLOBAL-RULES.md#-ai-行为约束自检清单2026-08-20-新增)

### 嵌入式AI项目
- [ ] **UCI HAR 公开数据集交叉验证**（补"单人单天"数据短板）→ [详情](01-Projects/embedded-ai-learning/courses/嵌入式AI课程全链路总结-MS版.md#112-p1-级短板深挖必问)
- [ ] **低功耗方案设计**（40Hz 常开推理的功耗预算 + 动作唤醒占空比设计）→ 同上
- [ ] **鲁棒性验证**（跑 05_robustness_validation.py，补噪声衰减表）→ 同上

### 课程学习
- [ ] **Week 4：INT8 量化实战**（QAT/PTQ + 校准集 + 量化误差分析）→ [课程](01-Projects/embedded-ai-learning/courses/week04-quantization-deployment.md)
- [ ] **CIFAR-10 CNN 实战**（Week 3 §7 模板，跑通 PyTorch→TFLite 流程）→ [课程](01-Projects/embedded-ai-learning/courses/week03-data-training-cnn.md)

### 投资落地（盖洛普）
- [ ] **选宽基指数**（沪深300 或 中证500）→ [详情](02-Knowledge/career-development/career-strategy/盖洛普测评落地行动计划.md#二投资主线被动定投)
- [ ] **设每月固定日自动扣款** → 同上
- [ ] **写入 family-hub 投资模块** → 同上

### 家庭
- [ ] **爱人完成盖洛普测评** → 补充「配偶协同分析」→ [详情](02-Knowledge/career-development/career-strategy/Harvey盖洛普测评/Harvey盖洛普优势测评分析报告.md#七配偶协同分析可选)

### 保险（2026-06-13 起，来自原 personal/todo.md）
- [ ] **蓝医保 20 年百万医疗续保**（韩伟+薛燕，2025 年因指标异常被拒，体检指标改善后补买）。换保证续保须等 2026-10 之后：换新前先关掉旧续保功能，期间不能去医院检查/体检；薛燕甲状腺囊性结节单独做甲状腺 B 超复查即可，其余不用复查
- [ ] **年底评估薛燕妈咪换 10 年期百万医疗**（当前心医保 5 年期）。备选：超越保、太平洋普惠保（均保证续保 10 年），可让岳母试一下

---

## P2（有余力再做）

### Life OS 六模块系统
- [ ] **投研异常告警自动化**（btc-temperature-gauge 扩展：机器做侦察，人做判断）→ [详情](01-Projects/btc-temperature-gauge)
- [ ] **穿戴设备接入健康中枢**（二期，先跑通体检表再说）
- [ ] **wiki→文章输出管道**（wiki 页面直接生成公众号/网站文章）→ [详情](01-Projects/personal-website)

### 工具安装（2026-05/06 起，来自原 personal/todo.md）
- [ ] **飞书接入家里电脑**，手机远程控制 Trae（可参考腾讯飞书接入方案）
- [ ] **飞书接入家里电脑**，手机远程控制腾讯 IDE
- [ ] **Obsidian 官方 CLI 安装配置**：更新 Obsidian → 设置开启 CLI → 注册 PATH → 验证 `obsidian search`（需 Catalyst 许可证）
- [ ] **安装 OpenAI Codex 插件**

### 面试弹药库
- [ ] **算法追问 4 题准备**（MLP vs 1D-CNN / 为什么不用 LSTM / 手工特征 vs 端到端 / 加第四类跑步）→ [详情](01-Projects/embedded-ai-learning/courses/嵌入式AI课程全链路总结-MS版.md#114-算法选型高频追问弹药储备)
- [ ] **商业价值叙事段落**（产品化迁移场景 + 与 Oura/Apple Watch 差异定位）→ 同上
- [ ] **拍 30 秒演示视频**（设备实时输出动作标签）→ 同上
- [ ] **pytest 关键校验 + 一键复现 README** → 同上

### 复述作业（费曼纪律）
- [ ] **RTOS 三段链二次复述**（MSP/PSP 归位 + 实时层 + 三级方案重讲，目标 80 分）→ [话术](02-Knowledge/career-development/interview-project-summaries/02-interview-prep/narrative-training.md#-三段链复述话术2026-07-29-考核修正版背诵用)
- [ ] **启动流程四段链复述**（上电→四步曲→Boot五步曲→链接脚本）→ [话术](02-Knowledge/career-development/interview-project-summaries/02-interview-prep/narrative-training.md#-启动流程--boot-跳转复述话术2026-07-29-考核修正版背诵用)
- [ ] **三连案例复述**（单位/速率/固件版本，一个病根）→ [话术](01-Projects/embedded-ai-learning/courses/嵌入式AI笔记-课程项目全流程.md#q6-数据审计三连案例一个病根三连发作day16-真实素材)
- [ ] **11 钩子复述**（一句话描述 11 段各一句自己的话）→ [话术](01-Projects/embedded-ai-learning/courses/嵌入式AI笔记-课程项目全流程.md#-一句话描述逐段理解11-个面试钩子2026-07-28-补充)
- [ ] **Tickless 三道题消化**（竞态/分数累加器/唤醒补偿）→ [笔记](02-Knowledge/career-development/interview-project-summaries/tech-interview-notes.md#151-竞态条件详解2026-07-31-深挖)

---

## ✅ 已完成（近两周）

| 完成日期    | 事项                                                      | 来源                          |
|:------------|:----------------------------------------------------------|:------------------------------|
| 2026-08-11  | 盖洛普落地行动计划建立（三主线+才干检查清单）                  | 职业策略                       |
| 2026-08-11  | 56 维特征说明完善（5 通道推导链）                            | 嵌入式AI                       |
| 2026-08-10  | Dropout 翻转补偿 + 优化器 SGD vs Adam 笔记                  | tech-interview-notes §8.8-8.9 |
| 2026-08-06  | 数据增强五件套学习（工业时序）                                | Week3 §4                      |
| 2026-08-05  | 数据预处理+归一化学习                                        | Week3 §3                      |
| 2026-08-04  | CNN 核心算子与 TFLM 实现                                     | tech-interview-notes §8.7     |
| 2026-08-03  | BrowserSkill 安装 + 离线包打包 + 技能目录统一                 | browser-automation            |
| 2026-08-03  | 战略决策：做极致顶点不分散补短板                              | 职业策略记录9                  |
| 2026-07-31  | Tickless 低功耗框架讲完 + 三题答案入文档                      | tech-interview-notes §1.5     |
| 2026-07-30  | Week2 模型转换完成（xxd/TFLiteConverter/Netron）             | tech-interview-notes §8.4-8.6 |
| 2026-07-29  | auto_push.ps1 中文文件名 bug 修复                            | 工具维护                       |
| 2026-07-29  | 启动流程三节课完成 + 考核                                     | tech-interview-notes §9       |
| 2026-07-28  | PendSV/tick 六连问知识链完整                                  | narrative-training Q2 区       |
| 2026-07-28  | 数据口径全统一（56维/40Hz/2403参数/6352B）                    | 全流程+MS版                    |

---

**创建日期**：2026-08-11
**维护**：AI 在新增/完成待办时双向同步本看板与源文件
