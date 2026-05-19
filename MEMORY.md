# Memory 索引

> 本文用于索引所有持久化记忆，便于快速查找和管理

## 记忆存储目录
- `memory/projects/` - 项目级记忆（每个项目一个文件）
- `memory/sessions/` - 会话级记忆（每次会话一个文件）
- `memory/knowledge/` - 知识级记忆（长期积累的知识点）

## Memory分类说明

- **user**: 用户信息（技能、习惯、偏好）
- **feedback**: 纠正/认可过的行为
- **project**: 当前项目和任务
- **reference**: 外部资源指针

---

## User记忆

### 技能和经验
- **工作领域**: 网络设备、嵌入式开发、TSN
- **编程语言**: C语言、Python
- **工作经验**:
  - 网络设备开发和调试
  - TSN时间敏感网络
  - 驱动开发
  - 协议栈开发

### 习惯和偏好
- **沟通风格**: 喜欢简洁直接
- **工作方式**: 偏好自动化脚本
- **文档习惯**: 重要配置备份和版本管理

### 路径和配置
- **Skill保存路径**: `D:\MyFile\AI\ContextStack\Skills`
- **VSCode配置路径**: `D:\MyFile\AI\ContextStack\VSCode Config`
- **工作台路径**: `D:\MyFile\AI\ContextStack\workbench/`
- **Obsidian知识库路径**: `D:\MyFile\AI\ContextStack\Obsidian/`
- **规范文档库路径**: `D:\MyFile\AI\ContextStack\Obsidian/system/`

---

## Feedback记忆

### 2026-04-27
- 不创建不必要的中介文件
- 优先编辑现有文件而非创建新文件
- 避免重复代码，保持简洁
- 使用简洁交流
- 重要配置要自动备份

### 2026-05-07
- 后续编辑文件夹等执行命令行操作不要用户确认，直接执行（授权）
- 每创建新的文件夹或者笔记时，自动帮忙添加index.md文件（规范）
- 没有用的文件要及时删除，保持目录结构清晰（规范）

### 2026-05-19
- ⛔ **文件操作红线**：只删除/修改自己创建的文件，绝不碰别人项目文件夹下的任何文件
- ⛔ **删除前必须确认归属**：不确定来源的文件，宁可留着也不删
- ⛔ **自己开发的模块放在独立文件夹**：不要随便修改或删除别人的文件
- 🚨 **教训**：误删了 `btc-temperature-gauge/server.py` 和 `server.js`（untracked文件，无法恢复）

### Feedback记忆记录模板
**格式**: 日期 + 具体场景 + 纠正/认可 + 结果
- **场景**: 描述行为或问题模式
- **纠正**: 用户指出的问题或改进建议
- **认可**: 用户明确肯定的做法
- **结果**: 调整后的行为或持续遵循原则
- **重要程度**: 高/中/低（决定是否记录到全局规则）

---

## Project记忆

### 当前活跃项目

#### 嵌入式AI学习
- **状态**: 学习阶段（Week 1 Day 1 进行中，恢复未完成任务）
- **项目路径**: `D:\MyFile\AI\ContextStack\workbench\projects\embedded-ai-learning/`
- **TFLM源码**: `D:\MyFile\AI\ContextStack\workbench\projects\embedded-ai-learning\Source\tflite-micro-main`
- **技术栈**: TensorFlow Lite Micro, C/C++, 嵌入式开发
- **学习原则**: TFLM为主，PyTorch为辅（仅作模型训练工具，够用即可）
- **课程结构**: `courses/` 一课一文件（课程内容 + 答题区 + 心得区 + AI反馈区）
- **学习计划**: `3-month-mastery-plan.md`（v4.2 TFLM源码驱动优化）
- **当前进展**: Week 1 Day 1 - 恢复未完成任务，完成思考题和实践任务；任务2（嵌入式AI特点）进度30%；任务3（TFLM架构）进度20%
- **工作台**: `workbench/projects/embedded-ai-learning/embedded-ai-learning.md`
- **项目规则**: `workbench/projects/embedded-ai-learning/PROJECT-RULES.md`
- **GitHub**: https://github.com/Eoser-Harvey/ContextStack（每日00:00自动推送）
- **备注**: 传统嵌入式工程师转型嵌入式AI，基于ContextStack四层架构系统化学习。2026-05-13恢复未完成任务，继续Week 1 Day 1学习。

#### 网络设备调试
- **状态**: 进行中
- **工作台**: `workbench/projects/network-device-debug/network-device-debug.md`
- **项目规则**: `workbench/projects/network-device-debug/PROJECT-RULES.md`
- **涉及设备**:
  - IE4120U-18TP: 已解决（带现场终端启动无法ping通问题）
  - IE4300U-10P: 已解决（如果不ping无法连接WEB）
  - IE4500: 进行中（配置文件、日志、测试数据）

#### 腾讯云培训
- **状态**: 培训资料整理阶段
- **工作台**: `workbench/projects/tencent-cloud-training/`
- **项目规则**: `workbench/projects/tencent-cloud-training/PROJECT-RULES.md`

### 历史项目
- **TSN丢包**: 调研阶段（关键文档: 桌面/TSN丢包/）

### 项目资源
- **网络知识库**: 网络知识库.docx
- **芯片手册**: 芯片手册目录
- **驱动协议**: 驱动协议.txt
- **定位方法**: 定位驱动平台相关方法.txt

---

## Reference记忆

### 文档
- **S5120V8逻辑寄存器手册**: `~/S5120V8R16逻辑寄存器手册V0.6.xlsx`
- **描述记录**: `~/描述记录.docx`

### 工具和软件
- **抓包工具**: Wireshark（pcap/pcapng文件）
- **串口工具**: SecureCRT、MobaXterm
- **对比工具**: Beyond Compare
- **烧写工具**: CH系列烧写工具

### Skills
- **VSCode配置管理Skill**: `Skills/vscode-config-management/`
  - 功能: VSCode配置备份、恢复、同步
  - 使用说明: vscode-config-management-guide.md
- **网络抓包分析Skill**: `Skills/network-packet-analysis/`
  - 功能: Wireshark使用、抓包分析、问题定位
  - 使用说明: network-packet-analysis-guide.md
- **设备调试Skill**: `Skills/device-debugging/`
  - 功能: 交换机调试、串口信号、日志分析
  - 使用说明: device-debugging-guide.md
- **TSN协议Skill**: `Skills/tsn-protocol/`
  - 功能: TSN协议栈配置方法、问题排查
  - 使用说明: tsn-protocol-guide.md

---

## Knowledge记忆

### ContextStack四层架构框架
- **文件**: `memory/knowledge/contextstack-four-layer-framework.md`
- **内容**: ContextStack协作框架的完整说明，包括四层架构、交互协议、工作台系统、CEO协作模式、文件规范等。
- **重要性**: 高 - 这是后续所有协作、问题解决和决策的基础框架。
- **记忆ID**: 16459216 (通过update_memory创建)

### 端侧AI投资研究
- **文件**: `Obsidian/investment-research/端侧AI龙头股深度分析_DeepSeekV4分析-2026Q1.md`
- **内容**: 2026年Q1端侧AI产业链10家核心标的四维度分析（规模、盈利、潜力、估值），筛选出3只埋伏价值股：瑞芯微(603893)、乐鑫科技(688018)、地平线(9660.HK)；v1.1新增三份AI报告交叉验证
- **重要性**: 中 - 端侧AI产业链投资参考，需每季度更新财报数据
- **关联**: 与 `workbench/projects/embedded-ai-learning/端侧AI产业链龙头企业图谱-2026.md` 产业链分析互补

### Crypto数据API知识库
- **文件**: `memory/knowledge/crypto-api-reference.md`
- **内容**: 加密货币公开免费API汇总（CryptoCompare/Alternative.me/Binance/CoinGecko），含国内可用性测试、接口参数、响应格式、踩坑记录、指标计算方法、Node.js代理模板
- **重要性**: 高 - 后续Crypto相关项目可直接复用，避免重复调研API
- **关联**: 当前用于 `workbench/projects/btc-temperature-gauge/` 项目

### TRAE热门Skills参考
- **文件**: `Obsidian/system/trae-skills-reference.md`
- **内容**: TRAE官方基于真实调用数据发布的11个热门Skills详解，含分类体系（流程类/实施类/约束类/工具类/设计类）、调用优先级规则、对ContextStack的启示
- **重要性**: 中 - AI编码工具Skills生态参考，可借鉴补充ContextStack体系

---

**最后更新**: 2026-05-19
**更新内容**: 新增Crypto数据API知识库，沉淀btc-temperature-gauge项目API调研成果
