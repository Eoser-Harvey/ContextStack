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

### 二、知识与项目状态（技能 / 项目 / 参考资料 / 知识条目）

| 分类 | 条目 | 摘要 | 关联项目 | 更新时间 |
|------|------|------|----------|----------|
| **User** | 技能和经验 | 网络设备/嵌入式/C/Python/TSN/驱动/TFLM | 全部 | 2026-04-27 |
| **User** | 习惯和偏好 | 简洁直接、自动化脚本、配置备份 | 全部 | 2026-04-27 |
| **User** | 路径和配置 | 项目关键路径映射 | 全部 | 2026-05-23 |
| **Project** | 嵌入式AI学习 | TFLM 源码驱动学习，Week 1 Day 1 完成 | 01-Projects/embedded-ai-learning | 2026-05-13 |
| **Project** | 网络设备调试 | 工业交换机问题排查（IE4120/IE4300/IE4500） | 01-Projects/network-device-debug | 2026-05-07 |
| **Project** | 腾讯云AI编程培训 | 培训资料归档 | 01-Projects/tencent-cloud-training | 2026-05-07 |
| **Project** | BTC温度仪表盘 | 加密货币市场可视化 | 01-Projects/btc-temperature-gauge | 2026-05-07 |
| **Project** | 求职面试-今日宜休ISHO | 面试讨论中，已完成全面匹配度分析 | career-development | 2026-05-29 |
| **Reference** | S5120V8逻辑寄存器手册 | 硬件参考 | network-device-debug | — |
| **Reference** | Wireshark 抓包 | 网络分析工具 | network-device-debug | — |
| **Knowledge** | ContextStack四层架构 | 框架说明 | 全部 | 2026-04-29 |
| **Knowledge** | 九号公司 FreeRTOS 面经 | 牛客网14题完整答案 | career-development | 2026-06-10 |
| **Knowledge** | note-organizer Skill | 智能笔记整理，5种类型识别 | 全部 | 2026-05-26 |
| **Knowledge** | 自主自我改进循环研究 | Hermes Agent四层记忆+三层飞轮 | 全部 | 2026-06-03 |
| **Knowledge** | CPO产业链投资标的精选 | 光模块/CPO深度研究 | 全部 | 2026-06-04 |
| **Knowledge** | 图解Skill—AI提效实战指南 | 宝玉《图解Skill》配套资源 | 全部 | 2026-06-05 |
| **Knowledge** | 人生投资自检清单20问 | 定期自检模板 | 全部 | 2026-06-05 |

---

## 一、AI 行为约束

> 以下条目约束 AI 的编码和操作行为，跨 session 持久生效。

### 文件操作
- ⛔ **文件操作红线**：只删除/修改自己创建的文件，绝不碰别人项目文件夹下的任何文件（2026-05-19，教训：误删 btc-temperature-gauge 的 server.py/server.js）
- ⛔ 删除前必须确认归属：不确定来源的文件，宁可留着也不删
- **及时清理**：无用文件（debug.log/.uploads 等临时文件）即查即删（2026-05-23）
- **新文件先探索目录结构**：新建前 `list_dir` 目标子文件夹，确保放入框架正确位置（2026-06-10）

### 操作授权
- 命令行操作（文件夹编辑/重命名/删除等）直接执行，不需用户确认（2026-05-07/27）
- Skill 安装/下载/脚本执行均自动执行

### 文档规范
- 不创建不必要的中介文件，优先编辑现有文件（2026-04-27）
- 每创建新文件夹或笔记时，自动添加 index.md（2026-05-07）
- inbox 归档统一写入 archive/archive-log.md，不单独建归档文件（2026-05-24）

### Git 规范
- .codebuddy/ 不同步 Git，.gitignore 忽略（2026-05-23）

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
- 文件: `02-Knowledge/career-development/interview-company-analysis/MS分析-北京今日宜休科技ISHO-20260529.md`

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
| 九号公司 FreeRTOS 面经 | 牛客网14题完整答案 | `career-development/interview-project-summaries/company-interviews/` |
| note-organizer Skill | 智能笔记整理，5种内容类型识别 | `.codebuddy/skills/note-organizer/` |
| 自主自我改进循环研究 | Hermes Agent四层记忆+三层飞轮 | `02-Knowledge/inbox/` |
| CPO产业链投资标的精选 | 光模块/CPO深度研究 | `02-Knowledge/investment-research/` |
| 图解Skill—AI提效实战指南 | 宝玉《图解Skill》配套资源 | `02-Knowledge/skills/` |
| 人生投资自检清单20问 | 定期自检模板 | `02-Knowledge/inbox/` |

---

> **维护规则**：AI 行为约束写入"一"区；项目状态/知识索引写入"二"区。两者都在本文件内，统一管理，便于迁移。
