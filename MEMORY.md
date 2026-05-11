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
- **状态**: 学习阶段（理论学习进行中）
- **项目路径**: `D:\MyFile\AI\ContextStack\workbench\projects\embedded-ai-learning\Source\tflite-micro-main`
- **技术栈**: TensorFlow Lite Micro, C/C++, 嵌入式开发
- **学习内容**:
  - TFLM架构和原理（任务3进度40%）
  - 嵌入式AI特点（任务2进度50%）
  - 内存管理机制（Tensor Arena、MicroAllocator）
  - 模型量化和部署（待开始）
- **当前进展**: 
  - 已完成嵌入式AI第一课，深入学习了TFLM内存管理架构
  - 掌握了Tensor Arena三个分区（Head/Temporary/Tail）的功能
  - 理解了离线内存规划的优势和实现原理
  - 基于ContextStack四层架构进行系统化学习
- **工作台**: `workbench/projects/embedded-ai-learning/embedded-ai-learning.md`
- **项目规则**: `workbench/projects/embedded-ai-learning/PROJECT-RULES.md`
- **备注**: 这是新的学习方向，结合之前嵌入式开发经验，采用ContextStack框架进行系统化知识积累

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

---

**最后更新**: 2026-05-11
**更新内容**: 添加Knowledge记忆部分，记录ContextStack四层架构框架知识，创建详细说明文件
