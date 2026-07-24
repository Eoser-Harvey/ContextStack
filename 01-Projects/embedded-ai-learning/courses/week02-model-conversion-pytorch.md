# Week 2：模型转换全流程与 TFLite 部署入门

> **主线（优先 TFLite）**：打通「训练框架 → TFLite → TFLM」全链路，优先走 **Keras/TF → TFLiteConverter → TFLM** 这条 TFLite 原生路径
> **与 W1 衔接**：W1 只读现成 `.tflite`；W2 自己造一个——理解"模型是怎么来的"，并为后续 int8 量化(W2.2)和实战项目(W4 MNIST)打地基
> **核心目标**：能手写 Keras 训一个小模型 → `TFLiteConverter` 转 TFLite → 用 Netron 看结构 → 跑通 TFLM 推理（PyTorch→ONNX 作为可选/延后模块，仅当你手上的模型是 PyTorch 时才需要）
> **学习策略**：部署岗的核心是"转换 + 落地"，不是训练。Keras 几行就能造模型并导出，优先吃透 TFLite 原生路径；PyTorch 训练可延后到真有 PyTorch 模型要部署时再学。

**状态**：🔄 进行中（已排，待学习）
**日期**：2026-07-22（排期）
**周期**：Week 2（覆盖计划 W2 Day1-Day5：模型转换 + Keras 主线 + 集成验证 + PyTorch 可选）

---

## 一、为什么需要"模型转换"？（理论）

W1 里 `.tflite` 是"天降"的。真实流程有**两条路径**，优先走路径 A：

```
路径 A（主线，优先 TFLite —— 最贴合你的目标）：
Keras/TF 训练 → SavedModel/.h5（含训练态：梯度/优化器/计算图）
        ↓ 导出（TFLiteConverter.from_keras_model）
TFLite / .tflite（推理专用 FlatBuffer，含算子+权重+元数据）
        ↓ 转换（xxd / generate_cc_arrays）
TFLM C 数组（model_data.h，烧进 MCU Flash）

路径 B（可选 / 延后 —— 仅当模型是 PyTorch 时）：
PyTorch 训练 → .pth（含训练态）
        ↓ 导出
ONNX（框架无关中间表示，开放标准）
        ↓ 转换（TFLiteConverter.from_onnx_model）
TFLite / .tflite → TFLM C 数组
```

**关键认知**：
- 训练框架的重量级格式**不适合部署**（含反向传播、动态图、Python 依赖）。
- **TFLite Converter** (`tf.lite.TFLiteConverter`) 是转换核心：做算子映射 + 常量折叠 + （可选的）量化。无论路径 A 还是 B，最终都汇聚到这里。
- **ONNX 只是 PyTorch 模型的"翻译桥"**，不是部署必经环节。路径 A 根本不需要 ONNX——这也正是"优先 TFLite"比"绕道 PyTorch"更直接的原因。
- TFLM 只认 FlatBuffer 版 `.tflite`，且只支持 TFLM 已实现的算子子集（呼应 W1 思考题 #3：没注册就报错）。

---

## 二、Keras/TF 主线：训练 → TFLite（必做）

> 目标不是成为 Keras 专家，而是能**造一个小模型、导出权重、转成 TFLite**。这是部署岗最直接需要的"造模型"能力——比 PyTorch 更贴 TFLite 生态。

> 🔑 **前置概念：前向 vs 反向（读 2.1 前必看）**
>
> 神经网络本质是一个函数：`y = f(x; W)`
> - `x` = 输入（语音 / 图像 / 传感器读数）
> - `W` = 训练好的权重（模型"学到的知识"，一串数字）
> - `y` = 输出（识别结果 / 预测值）
>
> **前向（Forward Pass）**：把 `x` 顺着网络一层层往下算（每层一次矩阵乘加），算出 `y`。部署时"输入进去、结果出来"的单向过程就是前向。
>
> **训练 vs 部署，只差三步**：`fit()` 内部是「前向 → 算 loss → 反向算梯度 → 优化器更新权重」循环多轮；**部署只保留第一步"前向"**，其余三步全部丢弃。
>
> | 阶段                | 训练时 | 部署时 | 为什么                         |
> |:--------------------|:------:|:------:|:-------------------------------|
> | ① 前向（算输出）     | ✅    | ✅    | 部署核心就是"用模型出结果"        |
> | ② 算 loss（比对错） | ✅    | ❌    | 真实输入没有标准答案可比对          |
> | ③ 反向（算梯度）     | ✅    | ❌    | 权重已固定，不再学习              |
> | ④ 优化器更新权重     | ✅    | ❌    | 不再训练，W 是烤死的常量          |
>
> **为什么部署只做前向**（4 点根因）：
> 1. **权重已固定**：训练阶段已把 W 学好，部署只是把 W 塞进设备"用"，不改动。
> 2. **无标签可比对**：部署吃真实世界数据，没有"正确答案"去算 loss。
> 3. **省资源**：反向需保存每层中间结果算梯度，极吃内存；MCU 资源紧张，砍掉反向+优化器大幅省内存与算力。
> 4. **TFLM 本体设计**：TensorFlow Lite Micro 是**推理引擎不是训练引擎**，只实现前向算子，没移植反向/训练能力。
>
> 一句话记：**前向 = 用模型，反向+优化器 = 造模型**。部署岗日常是"用"，但天花板在"不懂造"。

### 2.1 最小训练循环（Keras，模板）

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, losses, optimizers

model = keras.Sequential([
    layers.Dense(64, activation="relu", input_shape=(784,)),
    layers.Dense(10),
])
model.compile(optimizer=optimizers.Adam(1e-3),
              loss=losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=["accuracy"])

# x_train:[N,784]  y_train:[N]
model.fit(x_train, y_train, epochs=EPOCHS, validation_split=0.1)
model.save("mnist_model.h5")   # 或 keras.models.save_model
```

**对照 W1 思考题**：`model(x)` 前向 = W1 说的"推理=for循环做乘加"；`fit()` 内部的前向+反向+优化器更新是训练独有（部署时丢弃）。

### 2.2 转 TFLite（from_keras_model，主线核心）

```python
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_keras_model(model)  # 或 from_saved_model("mnist_model.h5")
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
# 可选量化（预演 W2.2）：converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()
open("model.tflite", "wb").write(tflite_model)
```

> 这是路径 A 的"灵魂一步"：一个 `from_keras_model` 就把训练态模型压成推理态 FlatBuffer，**不需要 ONNX、不需要 PyTorch**。

### 2.3（对照）如果用 TF SavedModel 入口

```python
converter = tf.lite.TFLiteConverter.from_saved_model("mnist_model")  # 同 from_keras_model 效果
```

---

## 三、用 Netron 看懂你的模型（实践）

- 安装：`pip install netron` 或下载桌面版；浏览器打开 `netron.app`。
- 打开 `model.tflite`：你会看到**节点图**——每个圆圈是算子（Reshape/Dense/Softmax），连线是张量流向。
- **练习**：对照 W1 的 `reference/fully_connected.h`，在 Netron 里找到 `FullyConnected`（Dense）节点，确认输入输出维度。这把"代码里的循环"和"图里的节点"对应起来。

> 呼应 W1 任务2 Q4：记事本看 `.tflite` 是乱码，Netron 才是正确的"阅读器"。

---

## 四、把自训模型跑进 TFLM（实践，衔接 W1）

1. 用 `xxd -i model.tflite > model_data.h` 生成 C 数组（或 TFLM 的 `generate_cc_arrays` 工具）。
2. 把 `model_data.h` 替换进 W1 的 `hello_world_test.cc` 同款工程（或 `examples/` 下的 minimal）。
3. `RegisterOps` 里按需 `AddFullyConnected()` / `AddSoftmax()` / `AddReshape()`。
4. `AllocateTensors` → `Invoke` → 打印输出，与 Python 端推理结果对比（误差应极小）。

**这是 W1「读现成模型」→ W2「造模型并验证」的闭环**，也是 W4 MNIST 实战的预演。

---

## 五、PyTorch → ONNX → TFLite（可选 / 延后模块）

> **标记：可选，可延后。** 仅当你手上的模型是 PyTorch 训练（现在多数开源模型如此）才需要。纯部署岗不必现在深学——等你真有 PyTorch 模型要落地时再回来学本节即可。下面给出最小可用脚本，不展开原理。

### 5.1 PyTorch 训练循环（轻量，仅参考）

```python
import torch, torch.nn as nn, torch.optim as optim

model = nn.Sequential(nn.Linear(784, 64), nn.ReLU(), nn.Linear(64, 10))
criterion, optimizer = nn.CrossEntropyLoss(), optim.Adam(model.parameters(), lr=1e-3)
for epoch in range(EPOCHS):
    for x, y in dataloader:
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
```

### 5.2 导出 ONNX

```python
dummy = torch.randn(1, 784)
torch.onnx.export(model, dummy, "model.onnx",
                  input_names=["input"], output_names=["output"],
                  dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}})
```

### 5.3 from_onnx_model 转 TFLite

```python
import tensorflow as tf
converter = tf.lite.TFLiteConverter.from_onnx_model("model.onnx")
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
tflite_model = converter.convert()
open("model.tflite", "wb").write(tflite_model)
```

> 注：PyTorch→ONNX→TFLite 是跨框架最稳路径，但对你"优先 TFLite"的目标属于**绕路**——路径 A（Keras 主线）才是首选。

---

## 六、提示问题（你的思考区）

> 仿 W1 格式：先自己答，再展开下方「参考/优化」对照。

### 任务1：Keras 训练 + TFLite 转换（主线，必做）
1. `model.fit()` 内部做了什么？为什么部署时这些步骤都不需要？
2. `from_keras_model` 和 `from_saved_model` 入口区别？为什么路径 A 不需要 ONNX？
3. 转换时报"op not supported by TFLite"，有哪些解法？（3 种以上）

### 任务2：Netron + TFLM 集成
1. 在 Netron 里数出你模型的算子种类，它们是否都在 TFLM 的 `AddXxx()` 里有对应？
2. 把 `.tflite` 转成 C 数组后，烧进 MCU 还需要什么才能跑？（回顾 W1 六步）
>> 分配内存？
3. 自训模型在 TFLM 上 `Invoke()` 输出和 Python 端差很多，可能原因？（至少列 3 条）
>> 训练和部署使用的算子不同；量化参数不一致；

### 任务3（可选 / 延后）：PyTorch→ONNX
1. 为什么路径 B 要经过 ONNX，而路径 A 不用？
2. `dynamic_axes` 的作用是什么？不设置会怎样？
3. ONNX 导出报错"unsupported operator"时，一般怎么排查？

### 任务4：TFLite Converter 通用
1. 为什么同一个模型，转出的 `.tflite` 有时比原模型还大？
2. 路径 A 和路径 B 最终产出的 `.tflite` 本质是否相同？区别在哪一步？

> **参考/优化（学习时展开）：**
> **任务1**：①`fit()` = 前向(乘加)+算 loss+反向(算梯度)+优化器更新权重，循环多轮；部署只做前向，无需梯度/优化器。②`from_keras_model` 直接吃内存中模型对象，`from_saved_model` 吃磁盘 SavedModel 目录；两者都跳过 ONNX 是因为 Keras 原生就属于 TF 生态，Converter 能直接解析，不需中间标准桥。③解法：a. `target_spec.supported_ops` 含对应 builtin 或 `SELECT_TF_OPS`；b. `allow_custom_ops=True` + 自己实现 TFLM 算子；c. 回训练端把不支持的算子替换成 TFLM 支持的等价结构再重导。
> **任务2**：①逐一对照 TFLM `micro_mutable_op_resolver.h` 的 `AddXxx` 清单，缺哪个就 `Add` 哪个，否则 `Invoke` 前 Prepare 阶段报 "Didn't find op"（见 W1 思考题 #3）。②还需：Arena 内存够、OpResolver 注册齐全、输入张量正确填充、输出张量读取（W1 六步）。③a. 权重/输入未做同样的预处理（归一化）不一致；b. 量化参数(scale/zero_point)不匹配（若用了 int8）；c. 输入数据 layout/shape 与训练时不同；d. 算子版本/数值精度(float vs double)差异累积。
> **任务3**：①ONNX 是开放中间标准，解耦 PyTorch 私有格式与 TF Converter；路径 A 的 Keras 本就是 TF 格式，Converter 直读无需中转。②`dynamic_axes` 让 batch 维可变，否则导出图 batch 维被固定为 1，换 batch 大小会 shape 不匹配。③查算子是否在 PyTorch→ONNX 支持列表；调 `opset_version`；自定义算子写 symbolic；或绕路用等价算子组合。
> **任务4**：①常见原因：未量化（仍是 float32，比 int8 大 4×）；图含 TFLM 不支持算子被降级成更大的 TF 算子；metadata/签名信息膨胀——用 Netron 比对节点数与大小。②本质相同——都是 FlatBuffer 推理图，TFLM 都认；区别只在"来源格式不同导致转换中间步骤不同"，最终 `.tflite` 结构等价。

---

## 七、课后习题（动手 + 笔答）

### 7.1 动手题（必做，走路径 A）
1. 用 Keras 写一个**拟合 sin(x)** 的小网络（1→16→1，约 2000 样本），训练 200 轮，把训练/验证 loss 曲线存图。
2. `from_keras_model` 转 TFLite → 用 Netron 打开，截图节点图贴到下方「实践结果区」。
3. 把 `.tflite` 转 C 数组，替换进 TFLM minimal 示例，`Invoke` 后打印输出，与 Python `model(x)` 对比（附误差）。

### 7.2 笔答题（选 3 题）
1. 画一张图说明 训练框架 → TFLite → TFLM 各阶段"丢掉/保留"了什么（路径 A）。
2. 解释 FlatBuffer 相比 JSON/Protobuf 在嵌入式端的 3 个优势。
3. 一个模型转 TFLite 后体积反而变大，列举 3 种可能原因。
4. 为什么嵌入式部署偏爱"静态图"而非"动态图"？

> （你的答案写在这里）

---

## 八、面试准备（Week 2 专题）

> W1 已建立"通用面试框架"（见 W1 文件末）。本节聚焦**模型转换/部署链路**高频题，与 W4 量化面试题衔接。

### 8.1 高频问答（先自答，再对照参考）

1. **把训练好的模型部署到 MCU，你走什么流程？**
   > 参考：优先 Keras/TF → `TFLiteConverter.from_keras_model` 转 TFLite → Netron 验证算子 → `xxd` 转 C 数组 → TFLM 注册算子+AllocateTensors+Invoke。若模型是 PyTorch，则先转 ONNX 再走 Converter（路径 B）。

2. **TFLite 和 ONNX Runtime 的区别？分别适合什么场景？**
   > 参考：TFLite/TFLM 面向移动/嵌入式（FlatBuffer、无 OS、小体积、支持 int8/int4 量化）；ONNX Runtime 面向服务端/桌面（多后端、GPU、灵活）。MCU 只能用 TFLM（Runtime 跑不了）。

3. **为什么模型转换会失败（op not supported）？怎么解决？**
   > 参考：见任务1 Q3 的三类解法（开 builtin/SELECT_TF_OPS、自定义 op、回训练端替换算子）。

4. **FlatBuffer 相比 JSON 在嵌入式有什么优势？（W1 已铺垫）**
   > 参考：①无需解析字符串，直接内存映射读取（零拷贝）；②体积更小（二进制+可选字段）；③schema 强类型、前向兼容；④可 `mmap` 进 Flash 直接跑，不需加载到 RAM。

5. **同一模型 Keras(.h5) 和 TFLite(.tflite) 体积谁大？为什么？**
   > 参考：通常 .h5 更大（含优化器状态、反向图、Python 结构）；.tflite 仅推理图+权重，且可量化到 int8 再缩 4×。但若未量化且含降级算子，tflite 也可能偏大。

### 8.2 简历话术（Week 2 可用）

> "我完整跑通过 Keras → TFLite 的模型转换链路，用 Netron 验证算子结构，最终把自训模型部署到 TFLM 跑通推理，输出与 Python 端一致。（补充：也了解 PyTorch→ONNX→TFLite 的跨框架路径。）"

### 8.3 深度追问（准备应对）
- 如果目标 MCU 不支持某算子（如 LayerNorm），你怎么在不改模型效果前提下绕过？
- int8 量化在哪个阶段做？转换时量化 vs 训练时量化（QAT）区别？（预演 W2.2）
- 如何用 `RecordingMicroInterpreter` 精确测出 arena 大小？

---

## 九、补充与扩展（可选）

- **工具**：`netron`（可视化）、`xxd`/`generate_cc_arrays`（转 C 数组）、`tensorflowjs_converter`（若涉及 Web）、`onnx-simplifier`（路径 B 导出后图化简）。
- **常见坑**：PyTorch 默认 NCHW、TFLite 常用 NHWC，路径 B 转完要在输入前做 `permute`；动态 shape 必须 `dynamic_axes`；ONNX opset 版本与转换端要匹配。路径 A（Keras）默认 NHWC，坑更少。
- **延伸阅读**：TFLM `examples/` 下每个示例都自带 `train_*.ipynb` 或 `convert_*.py`，是"训练→转换→部署"的最佳范本，建议读 `hello_world` 和 `mnist` 两个。
- **与 W4 衔接**：W2 的 sin 拟合 + MNIST 训练脚本，W4 直接拿去做"MCU 上跑 MNIST"实战，省去从头写训练代码。
- **PyTorch 何时学**：当你要部署的模型来源是 PyTorch（HuggingFace/论文复现/团队已有 .pth）时，再回头学第五节。否则先把 TFLite 原生部署吃透。

---

## 十、实践结果区

> 学完把产物贴这里：loss 曲线、Netron 截图、TFLM 输出对比表。

| 产物 | 路径/截图 | 备注 |
|------|-----------|------|
| sin 拟合训练脚本 | `week02_sin_train_keras.py` | 走路径 A |
| TFLite | `model.tflite` | 大小对比 |
| Netron 节点图 | （截图） | |
| TFLM 推理对比 | （输出 vs Python） | 最大误差 ___ |

---

## 十一、AI 助教反馈（完成后填写）

> 考核维度：理论理解 / 代码实践 / 习题完成度 / 面试表达
> 评分：___/10　评语：___
