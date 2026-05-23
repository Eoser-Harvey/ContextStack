# 嵌入式AI学习 — 稳定上下文

> 已达成共识的前提、约束、背景信息。变更频率低，沉淀后可长期复用。

## 项目定位
系统学习 TensorFlow Lite Micro 框架，掌握嵌入式 AI 模型部署全流程：模型量化、平台适配、性能优化。

## 已共识的决策

### 学习方法论：TFLM 主线，PyTorch/DL 为辅

| 层级 | 内容 | 学习方式 |
|------|------|----------|
| **主线（必须）** | TFLM 源码阅读、示例运行、算子分析 | 直接操作本地 TFLM 源码 |
| **辅线（够用即可）** | DL 基础概念（CNN、反向传播、损失函数等） | 围绕 TFLM 源码讲解，不另起 PyTorch 项目 |
| **工具（按需）** | PyTorch 训练、模型导出 .tflite | 仅在需要生成测试模型时使用 |

### AI 助教行为约束
1. ❌ 禁止要求用户安装 PyTorch 作为学习入口
2. ❌ 禁止以 PyTorch 代码作为课程主线
3. ✅ 从 TFLM 源码出发，通过读代码理解 DL 概念
4. ✅ 通用 DL 知识围绕 TFLM 算子实现讲解
5. ✅ PyTorch 仅在生成 .tflite 模型文件时使用

## 前提约束
- 硬件平台：ARM Cortex-M、RISC-V
- 工具链：GCC、LLVM
- 相关领域：深度学习基础、C/C++ 编程

## 系统环境 / 依赖
- TFLM 源码：`./source/tflite-micro-main`
- 核心代码：`tensorflow/lite/micro/`
- 示例代码：`tensorflow/lite/micro/examples/`