# Week 1 Day 1：从 TFLM hello_world 理解神经网络

> **日期**：2026-05-09
> **状态**：进行中
> **主线**：TFLM 源码阅读
> **辅线**：DL 基础概念（围绕 TFLM 讲解）
> **源码根目录**：`Source/tflite-micro-main/`

---

## 一、TFLM 推理的 6 步流程

打开 `tensorflow/lite/micro/examples/hello_world/hello_world_test.cc`，找到 `LoadFloatModelAndPerformInference()` 函数（第 72 行），TFLM 使用模型的完整流程：

```cpp
// ① 注册算子 —— 告诉 TFLM "我需要哪些运算"
HelloWorldOpResolver op_resolver;
RegisterOps(op_resolver);   // 内部调用 op_resolver.AddFullyConnected()

// ② 创建解释器 —— 相当于初始化推理引擎
tflite::MicroInterpreter interpreter(model, op_resolver, tensor_arena,
                                     kTensorArenaSize);

// ③ 分配内存 —— 在 Tensor Arena 里给张量分配空间
interpreter.AllocateTensors();

// ④ 设置输入
interpreter.input(0)->data.f[0] = golden_inputs[i];

// ⑤ 执行推理 —— 这就是"跑模型"
interpreter.Invoke();

// ⑥ 读取输出
float y_pred = interpreter.output(0)->data.f[0];
```

> **注意**：文件中用了 `using HelloWorldOpResolver = tflite::MicroMutableOpResolver<1>;`（第 30 行）做了类型别名，本质就是 `MicroMutableOpResolver<1>`。

**嵌入式类比**：和 STM32 初始化外设流程一样 —— `Init → Config → Start → Read`

---

## 二、模型就是一个大数组

打开 `models/` 目录，模型以 `.tflite` 文件存储：
- `models/hello_world_float.tflite` — 浮点模型
- `models/hello_world_int8.tflite` — INT8 量化模型

在代码中通过 `GetModel()` 加载为 C 数据结构（`hello_world_test.cc` 第 73 行）：

```cpp
const tflite::Model* model =
    ::tflite::GetModel(g_hello_world_float_model_data);
```

`g_hello_world_float_model_data` 就是把 `.tflite` 文件转成的 `unsigned char` 数组（在 `hello_world_float_model_data.h` 中）。

hello_world 模型功能：**输入 x，输出 sin(x) 的近似值**

```
输入: x = 0.0, 1.0, 3.0, 5.0   （代码中 golden_inputs 数组）
        ↓
    [神经网络]   ← .tflite 文件里的权重数据
        ↓
输出: ≈ sin(x)                  （误差 < 0.05）
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

- [ ] 通读 `hello_world_test.cc`，找到 `LoadFloatModelAndPerformInference()` 函数，理解 6 步流程
- [ ] 打开 `models/` 目录，找到 `.tflite` 文件，感受"模型就是二进制数据"
- [ ] 打开 `tensorflow/lite/micro/kernels/fully_connected.cc`，找到矩阵乘法核心循环

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
| **using 类型别名** | `using A = B;` 给类型 B 起别名 A，等同于 `typedef B A;`，C++11 推荐写法 |

---

## ✍️ 思考题答题区

### 问题1：`MicroInterpreter` 的 `Invoke()` 做了什么？和 RTOS 任务调度有什么相似？

**思考提示：**
1. `Invoke()` 是如何调用算子（operators）的？是顺序执行还是有调度逻辑？
2. RTOS 任务调度器如何管理多个任务？`Invoke()` 管理多个算子有什么相似之处？
3. 嵌入式系统中为什么需要避免动态调度？`Invoke()` 的调用是静态确定的吗？

> （在此作答）

### 问题2：为什么 TFLM 需要 `tensor_arena`（预分配内存），而 PC 上的 TensorFlow 不需要？

**思考提示：**
1. 嵌入式设备的内存管理有什么特点？为什么不能频繁调用 `malloc/free`？
2. `tensor_arena` 是堆栈还是堆内存？预分配有什么好处？
3. PC 上的 TensorFlow 可以使用虚拟内存，嵌入式设备呢？
4. 内存碎片对嵌入式系统有什么影响？`tensor_arena` 如何避免这个问题？

> （在此作答）

### 问题3：`OpResolver` 是什么？如果模型有卷积层但没注册 `AddConv2D()`，会发生什么？

**思考提示：**
1. `OpResolver` 的作用是什么？为什么需要注册算子？
2. TFLM 如何知道模型需要哪些算子？是通过模型文件中的元数据吗？
3. 如果模型有卷积层但没注册 `AddConv2D()`，解释器会报什么错误？在哪个阶段报错？
4. 这种设计有什么好处？为什么不像 PC 版 TensorFlow 那样动态加载算子？

> （在此作答）

---

## 🔬 实践结果区

### 任务1：通读 `hello_world_test.cc`，找到 `LoadFloatModelAndPerformInference()`

**提示问题：**
1. 这 6 步分别对应嵌入式系统初始化的哪个阶段？
2. `tensor_arena` 是什么？为什么大小是 3000？
3. `golden_inputs` 数组的值是什么？模型在做什么数学运算？
4. `RegisterOps(op_resolver)` 内部调用了什么函数？为什么要注册算子？

> （记录你的理解和发现）

### 任务2：查看 `models/` 目录下的 `.tflite` 文件

**提示问题：**
1. 文件大小是多少？（浮点模型 vs INT8 量化模型）
2. 为什么模型文件可以直接嵌入到 C 代码中（通过 `#include "model_data.h"`）？
3. 这种“模型即数组”的方式对嵌入式部署有什么好处？
4. 尝试用文本编辑器打开 `.tflite` 文件，你看到了什么？

> （记录你的感受）

### 任务3：分析 `tensorflow/lite/micro/kernels/fully_connected.cc`

**提示问题：**
1. 找到 `FullyConnectedEval` 函数，看看它是如何实现 `output = activation(input × weights + bias)` 的
2. 注意代码中的 `#ifdef` 分支，TFLM 如何支持浮点、INT8、INT4 等不同数据类型的？
3. 为什么嵌入式实现要避免动态内存分配（`malloc`）？
4. 全连接层的两层 for 循环的时间复杂度是多少？对于嵌入式设备这意味着什么？

> （记录核心代码片段和理解）

---

## 💭 学习心得

> **日期**：2026-05-22
> **主题**：神经网络的本质理解——从 hello_world 的 `sin(x)` 逼近说起
> 
> ### 核心洞见
> 今天通过 `week01-day01-tflm-hello-world.md` 第 68 行的提示，深入理解了神经网络的本质：
> 
> **"用简单数学运算逼近任意复杂函数"** 这句话在 TFLM 的 `hello_world` 示例中得到了完美体现：
> 
> 1. **数学本质**：神经网络不依赖 `sin()` 的数学公式，而是通过大量神经元的乘加运算（`y = activation(w·x + b)`）来逼近 `sin(x)` 函数。
> 2. **TFLM 实现**：在 `tensorflow/lite/micro/kernels/fully_connected.cc` 中，就是两层 for 循环的矩阵乘加运算：
>    ```cpp
>    total += input[j] * weights[i * input_dim + j];  // 乘加运算
>    output[i] = activation(total);                   // 非线性激活
>    ```
> 3. **嵌入式优势**：这种纯乘加运算非常适合 MCU：
>    - 可量化（int8 替代 float32）
>    - 可预分配内存（`tensor_arena`）
>    - 确定性延迟（无动态内存分配）
> 
> ### 与嵌入式开发的类比
> - **PID 控制器**：用公式 `error = target - actual` 控制
> - **神经网络**：用 `y = w·x + b` 的堆叠逼近复杂函数
> - **共同点**：都是"输入 → 计算 → 输出"的数据流，适合嵌入式实时处理
> 
> ### 关键验证
> 在 `hello_world_test.cc` 中：
> - 输入 `x = [0.0, 1.0, 3.0, 5.0]`
> - 输出 `≈ [sin(0), sin(1), sin(3), sin(5)]`
> - 误差 `< 0.05`，完全满足嵌入式应用要求
> 
> ### 困惑与下一步
> - **困惑**：如果没有非线性激活函数，神经网络还能逼近 `sin(x)` 吗？（待查 `activation.cc`）
> - **下一步**：深入分析 `tensor_arena` 的内存分配策略，理解为什么是 3000 字节
> 
> > *"神经网络的魔力不在于复杂的算法，而在于简单运算的大量组合。"*

---

## ❓ 待解决问题

- [ ] 
- [ ] 

---

## 🎯 AI 助教反馈

> （AI 批改后填写）