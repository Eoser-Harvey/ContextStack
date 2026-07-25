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

> 🔑 **前置概念：Converter 三个入口的原理（接上框）**
>
> **"转换"本质是同一流水线**：无论哪个入口，Converter 内部都走 `读取模型 → 得到一张 TF 计算图(tf.Graph) → 图变换(算子映射/常量折叠/死代码消除) → (可选)量化 float32→int8 → 序列化成 FlatBuffer(.tflite)`。**"跳过 ONNX"只是第 1 步的来源不同**，第 2-4 步完全一样。
>
> **为什么 Keras/SavedModel 不需要 ONNX**：Keras 模型底层就是 TensorFlow 的 `tf.Graph`；SavedModel 是 Keras/TF 的**磁盘标准格式**（`saved_model.pb` 计算图 + `variables/` 权重）。TFLite Converter 是 **TensorFlow 官方出品**，对这两种格式是"母语直读"——同团队、同框架、同一种内部表示，无需翻译。
> - `from_keras_model(model)`：直接拿**内存中** Keras 模型对象 → 内部降格/固化为 `tf.Graph` → 转 TFLite。
> - `from_saved_model(path)`：从**磁盘**读回 SavedModel → 反序列化为 `tf.Graph` → 转 TFLite。
>
> **对比：PyTorch 为什么必须 ONNX**：PyTorch 是另一套框架（Meta），内部表示与 TF 完全不同、Converter 不认。必须先经 **ONNX（开放神经网络交换格式，跨框架通用标准）**翻译成 Converter 能读的外语。即路径 B：PyTorch → ONNX（翻译桥）→ TFLite。**ONNX 是"跨框架翻译桥"：同框架不用翻译，跨框架必须翻译。**
>
> | 入口                | 输入               | 读取方式            | 是否需 ONNX | 内部动作                          |
> |:--------------------|:-------------------|:--------------------|:------------|:----------------------------------|
> | `from_keras_model`  | 内存中 Keras 模型对象 | 直接访问 Python 对象  | ❌         | Keras 模型降为 tf.Graph → 转 TFLite |
> | `from_saved_model`  | 磁盘 SavedModel 目录 | 从 .pb + variables/ | ❌         | 反序列化 SavedModel 为 tf.Graph     |
> | `from_onnx_model`   | 磁盘 .onnx 文件     | 解析 ONNX 格式       | ✅(本身即是) | ONNX 图映射成 TF 图 → 转 TFLite     |
>
> **工程提醒**：两个 API **终点完全相同**，只是入口不同（一个吃内存对象、一个吃磁盘文件）。部署流水线更推荐 `from_saved_model`——模型已落盘，不依赖当时的 Python 环境/对象状态。"跳过 ONNX"≠"永远不用学 PyTorch 路径"：真正要部署的开源模型多在 PyTorch 生态，ONNX 桥届时绕不掉。

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
>> 两种工具产物相同（都是 C 数组头文件）：`xxd` 是纯命令行工具（Windows 需装 Git for Windows）；`generate_cc_arrays` 是 TFLM 的 Python 脚本，底层也调 xxd，make 构建系统会自带 xxd。
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
>> 区别在于是否使用原生TF训练模型；一个是内存，一个是磁盘获取；TF直接可以转换成TFLite，不需要经过ONNX。
3. 转换时报"op not supported by TFLite"，有哪些解法？（3 种以上）

### 任务2：Netron + TFLM 集成
1. 在 Netron 里数出你模型的算子种类，它们是否都在 TFLM 的 `AddXxx()` 里有对应？
2. 把 `.tflite` 转成 C 数组后，烧进 MCU 还需要什么才能跑？（回顾 W1 六步）
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
> **任务1**：
①`fit()` = 前向(乘加)+算 loss+反向(算梯度)+优化器更新权重，循环多轮；部署只做前向，无需梯度/优化器。②`from_keras_model` 直接吃内存中模型对象，`from_saved_model` 吃磁盘 SavedModel 目录；两者都跳过 ONNX 是因为 Keras 原生就属于 TF 生态，Converter 能直接解析，不需中间标准桥。
③解法：a. `target_spec.supported_ops` 含对应 builtin 或 `SELECT_TF_OPS`；b. `allow_custom_ops=True` + 自己实现 TFLM 算子；c. 回训练端把不支持的算子替换成 TFLM 支持的等价结构再重导。
> **任务2**：
①逐一对照 TFLM `micro_mutable_op_resolver.h` 的 `AddXxx` 清单，缺哪个就 `Add` 哪个，否则 `Invoke` 前 Prepare 阶段报 "Didn't find op"（见 W1 思考题 #3）。
②还需：Arena 内存够、OpResolver 注册齐全、输入张量正确填充、输出张量读取（W1 六步）。
③a. 权重/输入未做同样的预处理（归一化）不一致；b. 量化参数(scale/zero_point)不匹配（若用了 int8）；c. 输入数据 layout/shape 与训练时不同；d. 算子版本/数值精度(float vs double)差异累积。
> **任务3**：
①ONNX 是开放中间标准，解耦 PyTorch 私有格式与 TF Converter；路径 A 的 Keras 本就是 TF 格式，Converter 直读无需中转。
②`dynamic_axes` 让 batch 维可变，否则导出图 batch 维被固定为 1，换 batch 大小会 shape 不匹配。
③查算子是否在 PyTorch→ONNX 支持列表；调 `opset_version`；自定义算子写 symbolic；或绕路用等价算子组合。
> **任务4**：
①常见原因：未量化（仍是 float32，比 int8 大 4×）；图含 TFLM 不支持算子被降级成更大的 TF 算子；metadata/签名信息膨胀——用 Netron 比对节点数与大小。
②本质相同——都是 FlatBuffer 推理图，TFLM 都认；区别只在"来源格式不同导致转换中间步骤不同"，最终 `.tflite` 结构等价。

---

## 七、课后习题（动手 + 笔答）

### 7.1 动手题（必做，走路径 A）
1. （理解即可，不必从零写）运行现成的 sin(x) 训练脚本（1→16→1，约 2000 样本，训 200 轮），**读懂每步、拿到模型**；loss 曲线图存作对照。重心不在"写训练代码"。
2. `from_keras_model` 转 TFLite → 用 Netron 打开，截图节点图贴到下方「实践结果区」。
3. 把 `.tflite` 转 C 数组，替换进 TFLM minimal 示例，`Invoke` 后打印输出，与 Python `model(x)` 对比（附误差）。

> **优先级提示**：本动手题的重心是 **②转换 + ③TFLM 部署**，不是"写训练代码"。训练脚本只需读懂并跑通、拿到模型即可（理念见上：py 脚本非核心竞争力，**原理理解 + 部署实践才是硬道理**）。时间分配建议：① 理解 ≤10%，②③ 部署实战 ≥90%。

### 7.2 笔答题（选 3 题）
1. 画一张图说明 训练框架 → TFLite → TFLM 各阶段"丢掉/保留"了什么（路径 A）。
2. 解释 FlatBuffer 相比 JSON/Protobuf 在嵌入式端的 3 个优势。
3. 一个模型转 TFLite 后体积反而变大，列举 3 种可能原因。
4. 为什么嵌入式部署偏爱"静态图"而非"动态图"？

> （你的答案写在这里）

### 7.4 参考答案（AI 整理，供对照）

**① 训练框架 → TFLite → TFLM 各阶段"丢掉/保留"（路径 A）**

| 阶段 | 保留 | 丢掉 |
|:-----|:-----|:-----|
| 训练框架（Keras/TF） | 前向图、权重、反向、优化器、autograd、训练管线 | —（全有） |
| TFLite（转换后） | 前向计算图、权重（可量化 int8）、I/O 签名、metadata | 反向/梯度、优化器、autograd、训练循环、Python 运行时 |
| TFLM（部署端） | 前向算子实现、量化权重、C 数组、静态内存 arena | 动态 shape/控制流灵活性、未注册算子、Host OS/Python 依赖、动态分配 |

> 一句话：训练侧"全栈"，TFLite 砍到"只前向"，TFLM 再砍到"只认已注册前向算子 + 裸机可跑"。

**② FlatBuffer 相比 JSON/Protobuf 在嵌入式端的 3 个优势**

1. **零拷贝/零解析**：数据序列化后可直接内存映射（`mmap`）按偏移访问字段，不必整体反序列化成对象树。JSON 要全解析成对象、Protobuf 也要 decode——都吃 RAM 和 CPU，MCU 扛不住。
2. **体积极小 + 无反射依赖**：二进制紧凑，无 JSON 那种"每字段名重复存字符串"的开销；读取**不需要 schema/反射库**也能按已知偏移取部分字段 → 代码体积更小，适合 MCU。
3. **随机访问 + 向前兼容**：可只读取需要的子图/张量而不加载全部；新增字段向后兼容、不破坏旧解析逻辑 → OTA 升级模型时不必强制更新固件解析代码。

> 注：Protobuf 也二进制紧凑，但**必须反序列化成对象才能访问**且需代码生成/反射；FlatBuffer 的差异化优势正是"免解析 + 免反射"。

**③ 转 TFLite 后体积反而变大的 3 种可能原因**

1. **未量化**：默认仍是 float32（4 字节）。若对比基准是训练时的 float16/混合精度、或已压缩的 checkpoint/量化 onnx，未量化 tflite 反而大（约 4× int8）。
2. **算子降级膨胀**：TFLM 不支持的算子被 fallback 成更大的通用 TF 算子或拆成多个基础算子（如复杂激活/自定义层展开），节点数与常量成倍膨胀。
3. **未融合/冗余保留**：BatchNorm 未折叠进 Conv（多一套参数）、保留 metadata/signature_defs/控制流中间张量、或转换优化被关掉导致死代码/常量未折叠。用 Netron 比对节点数与大小即可定位。

**④ 为什么嵌入式部署偏爱"静态图"而非"动态图"**

1. **内存可预测**：静态图结构在转换期就固定，编译期已知每层 I/O 张量大小 → TFLM 用静态 arena 一次性分配，总 RAM 可确定，不会运行时爆栈/碎片。动态图需运行时建图+动态分配，MCU 资源紧张承受不起。
2. **可离线优化 + 可部署**：静态图能做算子融合、常量折叠、量化校准；动态图（PyTorch eager）每步解释执行、依赖 autograd 与 Python，无法在裸 MCU 跑、耗时也不可预测。
3. **无重运行时依赖**：静态图序列化后只需轻量解释器（TFLM），不依赖 Python/autograd/动态调度；动态图框架太重，跑不了。
4. **确定性时延**：静态执行路径固定，实时性可控——工业/控制场景的关键诉求。

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
   >
   > 注：**降级算子 ≠ 未使用算子**。降级算子指模型**已用到**、但 TFLM 无高效原生实现，被拆细或退化为 Flex/Select 的算子，会撑大体积甚至导致裸机跑不了；未使用的算子会被转换器剪掉（死代码消除），根本不进 `.tflite`，与"变大"无关。

### 8.2 简历话术（Week 2 可用）

> "我完整跑通过 Keras → TFLite 的模型转换链路，用 Netron 验证算子结构，最终把自训模型部署到 TFLM 跑通推理，输出与 Python 端一致。（补充：也了解 PyTorch→ONNX→TFLite 的跨框架路径。）"

### 8.3 深度追问（准备应对）
- 如果目标 MCU 不支持某算子（如 LayerNorm），你怎么在不改模型效果前提下绕过？
- int8 量化在哪个阶段做？转换时量化 vs 训练时量化（QAT）区别？（预演 W2.2）
- 如何用 `RecordingMicroInterpreter` 精确测出 arena 大小？

> **深度追问参考答：**
> **① 绕过不支持的算子（如 LayerNorm），不改效果：**
> - 等价子图替换：在导出/转换端把该算子重写成 TFLM 支持的**基础算子组合**（如 LayerNorm 可拆成 Mean/Sub/Div/Scale），属等价变换、数值一致。
> - 自定义算子（custom op）：用 C 实现该算子并注册进 `MicroMutableOpResolver`（`allow_custom_ops=True`），效果一致；量化场景须自己保证 int8 内核精度。
> - ❌ 避免 Flex/Select fallback：需链接完整 TF 运行时，裸 MCU 基本跑不了，非真解。
> - 注：若训练时把 LayerNorm 换成 BatchNorm（可折叠进前层），属"改结构"，仅在确认效果近似时才用；违背"不改效果"前提时需谨慎。
>
> **② int8 量化阶段 + PTQ vs QAT：**
> - **阶段**：量化在**转换阶段**由 `TFLiteConverter` 固化。PTQ 全程在转换时；QAT 的"伪量化"在**训练时**插入，但最终 int8 固化仍在转换时。
> - **PTQ（训练后量化）**：float32 模型直接转换时量化，需**校准集**跑一遍收集激活分布定 scale/zero-point。优：简单快、不动训练。缺：小模型/激活范围大时精度损失明显。
> - **QAT（量化感知训练）**：训练时插伪量化节点，让模型"提前适应"量化噪声，转换时固化为真 int8。优：精度保持远好于 PTQ（int8/int4 必备）。缺：需重训/微调、流程复杂。
> - 策略：**先 PTQ，不达标再 QAT**（预演 W4 量化实战）。
>
> **③ `RecordingMicroInterpreter` 测 arena：**
> 1. 开一个**故意偏大**的 `tensor_arena` 缓冲（如数十 KB）。
> 2. 用 `tflite::RecordingMicroInterpreter` 替代 `MicroInterpreter` 构造（同套 op resolver / arena / profiler）。
> 3. 调 `AllocateTensors()`。
> 4. 取 `interpreter.GetTensorArenaUsedBytes()` → 即该模型**真实峰值占用**；部署时把 arena 设为该值（留余量）。
> 5. 意义：避免拍脑袋定 arena 导致溢出（OOM）或浪费 RAM；可纳入 CI 自动测。

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
