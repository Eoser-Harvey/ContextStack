# Memory 索引

> 表格化快速索引，详细信息见下方分类节。

## 索引总表

| 分类 | 文件 / 条目 | 摘要 | 关联项目 | 更新时间 |
|------|------------|------|----------|----------|
| **User** | 技能和经验 | 网络设备/嵌入式/C/Python/TSN/驱动 | 全部 | 2026-04-27 |
| **User** | 习惯和偏好 | 简洁直接、自动化脚本、配置备份 | 全部 | 2026-04-27 |
| **User** | 路径和配置 | 项目关键路径映射 | 全部 | 2026-05-23 |
| **Feedback** | 不创建不必要的中介文件 | 优先编辑现有文件 | 全部 | 2026-04-27 |
| **Feedback** | 操作直接执行不确认 | 所有命令行操作（含 Skill 安装/下载/脚本执行）均自动执行，不需确认 | 全部 | 2026-05-27 |
| **Feedback** | 新文件自动加 index.md | 目录结构规范 | 全部 | 2026-05-07 |
| **Feedback** | 文件操作红线 | 不碰别人项目文件 | 全部 | 2026-05-19 |
| **Feedback** | 及时清理无用文件 | debug.log/.uploads等临时文件即查即删 | 全部 | 2026-05-23 |
| **Feedback** | .codebuddy/ 不同步 | IDE本地治理规则，.gitignore忽略 | 全部 | 2026-05-23 |
| **Feedback** | inbox归档规则 | 归档统一写入 archive/archive-log.md（按分类分节），不单独建归档文件 | 全部 | 2026-05-24 |
| **Project** | 嵌入式AI学习 | TFLM 源码驱动学习 | 01-Projects/embedded-ai-learning | 2026-05-13 |
| **Project** | 网络设备调试 | 工业交换机问题排查 | 01-Projects/network-device-debug | 2026-05-07 |
| **Project** | 腾讯云AI编程培训 | 培训资料归档 | 01-Projects/tencent-cloud-training | 2026-05-07 |
| **Project** | BTC温度仪表盘 | 加密货币市场可视化 | 01-Projects/btc-temperature-gauge | 2026-05-07 |
| **Project** | 求职面试-今日宜休ISHO | 面试讨论中，已完成全面匹配度分析 | 02-Knowledge/career-development | 2026-05-29 |
| **Reference** | S5120V8逻辑寄存器手册 | 硬件参考 | network-device-debug | — |
| **Reference** | Wireshark 抓包 | 网络分析工具 | network-device-debug | — |
| **Knowledge** | ContextStack四层架构 | 框架说明 | 全部 | 2026-04-29 |
| **Knowledge** | 自主自我改进循环研究 | Agent自我进化：Hermes Agent四层记忆+三层飞轮、Self-Improving Coding Agents | 全部 | 2026-06-03 |

---

## User记忆

### 技能和经验
- 工作领域: 网络设备、嵌入式开发、TSN
- 编程语言: C语言、Python
- 工作经验: 网络设备开发调试、TSN时间敏感网络、驱动开发、协议栈开发

### 习惯和偏好
- 沟通风格: 简洁直接
- 工作方式: 偏好自动化脚本
- 文档习惯: 重要配置备份和版本管理

### 路径和配置
- Skill保存路径: `02-Knowledge/skills/`
- VSCode配置路径: `05-Tools/vscode-config/`
- 项目路径: `01-Projects/`
- 知识库路径: `02-Knowledge/`

---

## Feedback记忆

### 2026-05-19
- ⛔ 文件操作红线：只删除/修改自己创建的文件，绝不碰别人项目文件夹下的任何文件
- ⛔ 删除前必须确认归属：不确定来源的文件，宁可留着也不删
- ⛔ 自己开发的模块放在独立文件夹：不要随便修改或删除别人的文件
- 🚨 教训：误删了 `btc-temperature-gauge/server.py` 和 `server.js`（untracked文件，无法恢复）

### 2026-05-07
- 后续编辑文件夹等执行命令行操作不要用户确认，直接执行（授权）
- 每创建新的文件夹或者笔记时，自动帮忙添加index.md文件（规范）
- 没有用的文件要及时删除，保持目录结构清晰（规范）

### 2026-04-27
- 不创建不必要的中介文件
- 优先编辑现有文件而非创建新文件
- 避免重复代码，保持简洁
- 使用简洁交流
- 重要配置要自动备份

---

## Project记忆

### 当前活跃项目

#### 嵌入式AI学习
- 状态: 学习阶段
- TFLM源码: `本地 TFLM 源码目录`
- 技术栈: TensorFlow Lite Micro, C/C++, 嵌入式开发
- 学习原则: TFLM为主，PyTorch为辅
- 课程结构: `courses/` 一课一文件
- 学习计划: `3-month-mastery-plan.md`
- 当前进展: Week 1 Day 1 完成
- GitHub: https://github.com/Eoser-Harvey/ContextStack

#### 网络设备调试
- 状态: 进行中
- 涉及设备: IE4120U-18TP（已解决）、IE4300U-10P（已解决）、IE4500（进行中）

#### 腾讯云AI编程培训
- 状态: 培训资料整理阶段

---

## Reference记忆

### 文档
- S5120V8逻辑寄存器手册
- 描述记录
- 网络知识库.docx、芯片手册目录、驱动协议.txt

### 工具
- 抓包: Wireshark
- 串口: SecureCRT、MobaXterm
- 对比: Beyond Compare

---

## Knowledge记忆

### ContextStack四层架构框架
- 文件: `03-Memory/knowledge/contextstack-four-layer-framework.md`
- 内容: ContextStack协作框架的完整说明