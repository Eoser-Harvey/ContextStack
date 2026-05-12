# Week 1 Day 1：从 TFLM hello_world 理解神经网络

> **日期**：2026-05-09
> **状态**：进行中
> **主线**：TFLM 源码阅读
> **辅线**：DL 基础概念（围绕 TFLM 讲解）

---

## 一、TFLM 推理的 6 步流程

打开 `tensorflow/lite/micro/examples/hello_world/hello_world_test.cc`，TFLM 使用模型的完整流程：

```cpp
// ① 注册算子 —— 告诉 TFLM "我需要哪些运算"
auto resolver = MicroMutableOpResolver<1>();
resolver.AddFullyConnected();

// ② 创建解释器 —— 相当于初始化推理引擎
MicroInterpreter interpreter(model, resolver, tensor_arena, arena_size);

// ③ 分配内存 —— 在 Tensor Arena 里给张量分配空间
interpreter.AllocateTensors();

// ④ 设置输入
TfLiteTensor* input = interpreter.input(0);
input->data.f[0] = 0.5f;   // 填入你的数据

// ⑤ 执行推理 —— 这就是"跑模型"
interpreter.Invoke();

// ⑥ 读取输出
TfLiteTensor* output = interpreter.output(0);
float result = output->data.f[0];
```

**嵌入式类比**：和 STM32 初始化外设流程一样 —— `Init → Config → Start → Read`

---

## 二、模型就是一个大数组

打开 `tensorflow/lite/micro/examples/hello_world/model.cc`，模型被存成 `unsigned char` 数组。

hello_world 模型功能：**输入 x，输出 sin(x) 的近似值**

```
输入: x = 0.5
        ↓
    [神经网络]   ← model.cc 里的字节数组
        ↓
输出: ≈ sin(0.5) ≈ 0.479
```

**关键理解**：不是用 `sin()` 函数算的，而是通过大量"神经元"的乘加运算逼近出来的。这就是神经网络的本质 —— **用简单数学运算逼近任意复杂函数**。

---

## 三、一个神经元在 TFLM 里的实现

打开 `tensorflow/lite/micro/kernels/fully_connected.cc`，核心计算：

```cpp
// 全连接层 = 矩阵乘法 + 偏置 + 激活函数
// output = activation(input × weights + bias)

for (int i = 0; i < output_dim; i++) {
    float total = bias[i];           // 从偏置开始
    for (int j = 0; j < input_dim; j++) {
        total += input[j] * weights[i * input_dim + j];  // 加权求和
    }
    output[i] = activation(total);   // 过激活函数
}
```

**两层 for 循环，和普通矩阵运算没有区别。**

---

## 四、训练 vs 推理

| | 训练（Training） | 推理（Inference） |
|---|---|---|
| **做什么** | 调整权重 w 和偏置 b | 用固定的 w、b 计算结果 |
| **在哪里跑** | PC/服务器（PyTorch/TF） | MCU（TFLM） |
| **需要什么** | 大量数据 + GPU | 模型文件 + TFLM 运行时 |
| **你的角色** | 不需要深入 | **这是你的主战场** |

**TFLM 只做推理，不做训练。**

---

## 今日任务

- [ ] 通读 `hello_world_test.cc`，理解 6 步流程
- [ ] 找到 `model.cc`，感受"模型就是大数组"
- [ ] 打开 `fully_connected.cc`，找到矩阵乘法核心循环

## 思考题

1. `MicroInterpreter` 的 `Invoke()` 做了什么？和 RTOS 任务调度有什么相似？
2. 为什么 TFLM 需要 `tensor_arena`（预分配内存），而 PC 上的 TensorFlow 不需要？
3. `OpResolver` 是什么？如果模型有卷积层但没注册 `AddConv2D()`，会发生什么？

---

## 关键概念速查

| 概念 | 一句话解释 |
|------|-----------|
| **MicroInterpreter** | TFLM 的总调度器，管理模型加载和推理执行 |
| **Tensor Arena** | 预分配的静态内存池，所有张量从这里分配 |
| **OpResolver** | 算子注册表，告诉解释器"我会哪些运算" |
| **Invoke()** | 执行一次完整的前向推理 |
| **全连接层** | 矩阵乘法 + 偏置 + 激活函数 |

---

## ✍️ 思考题答题区

### 问题1：`MicroInterpreter` 的 `Invoke()` 做了什么？和 RTOS 任务调度有什么相似？

> （在此作答）

### 问题2：为什么 TFLM 需要 `tensor_arena`（预分配内存），而 PC 上的 TensorFlow 不需要？

> （在此作答）

### 问题3：`OpResolver` 是什么？如果模型有卷积层但没注册 `AddConv2D()`，会发生什么？

> （在此作答）

---

## 🔬 实践结果区

### 任务1：通读 `hello_world_test.cc`

> （记录你的理解和发现）

### 任务2：查看 `model.cc`

> （记录你的感受）

### 任务3：分析 `fully_connected.cc`

> （记录核心代码片段和理解）

---

## 💭 学习心得

> （记录今天的收获、困惑、感悟）

---

## ❓ 待解决问题

- [ ] 
- [ ] 

---

## 🎯 AI 助教反馈

> （AI 批改后填写）