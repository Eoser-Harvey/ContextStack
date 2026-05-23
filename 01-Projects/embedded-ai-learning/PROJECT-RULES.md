# 嵌入式AI学习 - 项目规则

## 项目概述

### 基本信息
- **项目名称**: 嵌入式AI学习
- **项目类型**: 学习
- **技术栈**: TensorFlow Lite Micro (TFLM), C/C++, ARM Cortex-M, Python
- **负责人**: h31280
- **创建时间**: 2026-04-29
- **当前状态**: 学习阶段（第一阶段理论学习进行中）

### 项目目标
系统学习TensorFlow Lite Micro框架，掌握嵌入式AI模型部署全流程，包括模型量化、平台适配、性能优化等核心技能。

### 成功标准
- 理解TFLM核心架构和内存管理机制
- 能够独立完成模型量化和部署
- 掌握嵌入式AI性能优化方法
- 完成至少一个端到端的嵌入式AI项目

### 学习方法论（AI 助教必读）

**核心原则：TFLM 为主，PyTorch/DL 基础为辅。**

| 层级 | 内容 | 学习方式 |
|------|------|----------|
| **主线（必须）** | TFLM 源码阅读、示例运行、算子分析 | 直接操作本地 TFLM 源码 `./source/tflite-micro-main` |
| **辅线（够用就行）** | DL 基础概念（CNN、反向传播、损失函数等） | 围绕 TFLM 源码讲解，不另起 PyTorch 项目 |
| **工具（按需）** | PyTorch 训练、模型导出 .tflite | 仅在需要生成测试模型时使用，不展开教学 |

**AI 助教行为约束：**
1. ❌ **禁止**：要求用户安装 PyTorch 作为学习入口
2. ❌ **禁止**：以 PyTorch 代码作为课程主线
3. ✅ **正确做法**：从 TFLM 源码出发，通过读代码理解 DL 概念
4. ✅ **正确做法**：通用 DL 知识（CNN 原理、反向传播等）围绕 TFLM 的算子实现来讲解
5. ✅ **正确做法**：PyTorch 仅作为"模型训练工具"出现，且只在需要生成 .tflite 模型文件时才使用

**典型错误示例（禁止）：**
- "先装 PyTorch，跑一个 MNIST CNN 训练脚本" ← 这是 PyTorch 主线，不是 TFLM 主线

**正确示例：**
- "打开 TFLM 的 `fully_connected.cc`，看全连接层的矩阵乘法实现，这就是神经网络的核心计算"
- "打开 `conv.cc`，看卷积算子在 MCU 上是怎么实现的，对比一下 PC 上的 PyTorch Conv2d 有什么不同"

## 目录结构规范

### 项目代码路径
- **TFLM源码**: `./source/tflite-micro-main`
- **核心代码**: `tensorflow/lite/micro/`
- **示例代码**: `tensorflow/lite/micro/examples/`
- **工具脚本**: `tools/`, `python/`

### 工作台路径
- **工作台文件**: `./embedded-ai-learning.md`
- **学习计划**: `./3-month-mastery-plan.md`

## 代码规范

### 通用规范
- 遵循TFLM上游代码风格（Google C++ Style）
- 变量和函数命名: `snake_case`
- 常量命名: `UPPER_SNAKE_CASE`
- 类型命名: `PascalCase`
- 缩进: 2空格（遵循TFLM项目约定）

### 嵌入式约束
- 不使用动态内存分配（`malloc`/`free`）
- 优先使用栈分配和静态内存池
- 注意内存对齐要求
- 避免递归调用（栈溢出风险）

### 学习笔记规范
- 每个学习阶段完成后记录心得
- 实验代码添加详细注释
- 遇到的问题和解决方案必须记录

## 领域知识

### TFLM核心概念
- **Interpreter**: 模型解释器，负责模型加载和推理
- **MicroAllocator**: 内存分配器，管理tensor内存
- **MicroProfiler**: 性能分析器
- **OpResolver**: 算子注册和解析

### 模型量化
- 支持int8、int16、float16量化
- 量化感知训练 vs 训练后量化
- 量化精度损失评估

### 平台适配
- ARM Cortex-M系列（M0/M3/M4/M7）
- RISC-V架构
- DSP加速指令集

## 课程笔记规范

### 目录结构
```
courses/
├── index.md                          # 课程索引（自动维护）
├── week01-day01-tflm-hello-world.md  # 一课一文件（课程+答题+心得）
├── week01-day02-xxx.md
└── ...
```

### 命名规则
- 格式：`week{周}-day{天}-{主题}.md`
- 示例：`week01-day01-tflm-hello-world.md`

### 每课 MD 必须包含
- [ ] 日期和状态（进行中/已完成）
- [ ] 主线内容（TFLM 源码分析）
- [ ] 辅线内容（DL 概念，围绕 TFLM 讲解）
- [ ] 今日任务清单（checkbox 格式）
- [ ] 思考题
- [ ] 关键概念速查表
- [ ] ✍️ 思考题答题区（用户填写）
- [ ] 🔬 实践结果区（用户填写）
- [ ] 💭 学习心得区（用户填写）
- [ ] ❓ 待解决问题清单
- [ ] 🎯 AI 助教反馈区（AI 批改后填写）

### 一课一文件原则
```
3-month-mastery-plan.md          ← 学习计划（大纲，安排每天学什么）
courses/week01-day01-xxx.md      ← 一课一文件（课程内容 + 答题区 + 心得区 + AI反馈）
                                       ↑
                                  全部在一个文件里，不拆分
```

### AI 助教行为约束
- 每节课结束后，**必须**将课程内容写入对应的 `courses/weekXX-dayXX-xxx.md`
- 课程 MD 是积累型资产，后续可回顾复习
- 同步更新 `courses/index.md` 索引
- 用户提交答题后，在"AI 助教反馈"区批改
- **禁止**创建独立的 journal/ 目录，答题区在课程文件内

## 产品红线

- 不在生产设备上直接烧写未验证的模型
- 不修改TFLM核心解释器代码（学习阶段只读）
- 实验代码与生产代码严格分离
- 模型推理结果必须经过验证才能用于决策

## 相关资源

### 文档
- TFLM官方README: `tensorflow/lite/micro/README.md`
- TensorFlow Lite 官方文档: https://www.tensorflow.org/lite

### 工具
- GCC ARM Embedded工具链
- Keil MDK / IAR EWARM
- Renode 仿真平台

### 规范文档
- 技术调研框架: `02-Knowledge/system/research-frameworks/tech-research-framework.md`
- 调试方法论: `02-Knowledge/system/methodology/debug-methodology.md`

---

**版本**: v1.0
**创建时间**: 2026-05-07
**基于模板**: `02-Knowledge/system/templates/project-rules-template.md`
