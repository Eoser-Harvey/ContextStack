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

## 目录结构规范

### 项目代码路径
- **TFLM源码**: `D:\MyFile\AI\TFLM\tflite-micro-main\tflite-micro-main`
- **核心代码**: `tensorflow/lite/micro/`
- **示例代码**: `tensorflow/lite/micro/examples/`
- **工具脚本**: `tools/`, `python/`

### 工作台路径
- **工作台文件**: `D:\MyFile\AI\ContextStack\workbench\projects\embedded-ai-learning\embedded-ai-learning.md`
- **学习计划**: `D:\MyFile\AI\ContextStack\workbench\projects\embedded-ai-learning\3-month-mastery-plan.md`

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
- 技术调研框架: `Obsidian/system/research-frameworks/tech-research-framework.md`
- 调试方法论: `Obsidian/system/methodology/debug-methodology.md`

---

**版本**: v1.0
**创建时间**: 2026-05-07
**基于模板**: `Obsidian/system/templates/project-rules-template.md`
