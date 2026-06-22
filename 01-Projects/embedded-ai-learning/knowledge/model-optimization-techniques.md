# 模型优化技术与神经网络架构 — 端侧AI核心知识

> 创建时间：2026-06-10
> 定位：面试 + 实战必备，覆盖 3 个月精通计划中 Month 1 Week 4 的全部技术点

---

## 一、模型压缩三大技术

| 技术 | 核心思想 | 压缩率 | 精度损失 | 适用阶段 |
|:---:|------|:---:|:---:|---------|
| **量化** | 降低数值精度（FP32→INT8） | 4× | < 3% | 训练后/部署前 |
| **剪枝** | 删除不重要的权重/通道 | 2-10× | < 2% | 训练后/训练中 |
| **蒸馏** | 大模型教小模型 | 根据Teacher-Student比 | < 5% | 训练阶段 |

### 1.1 量化（Quantization）

#### 核心原理
```
将浮点数映射到整数，用整数运算替代浮点运算

对称量化：Q = round(R / scale)      scale = max(|R|) / 127
非对称量化：Q = round(R / scale) + zero_point
```

#### 两种方案对比

| 方案 | PTQ（后训练量化） | QAT（量化感知训练） |
|------|------------------|-------------------|
| **时机** | 训练完成后 | 训练过程中 |
| **精度** | 略低（损失 1-3%） | 更高（损失 < 1%） |
| **难度** | 低，一行 API | 高，需修改训练代码 |
| **适用** | 对精度不敏感的场景 | 精度敏感的场景 |
| **TFLM 支持** | ✅ `TFLiteConverter` | ✅ `tf.quantization` |

#### INT8 量化公式

```python
# PTQ in TensorFlow
converter = tf.lite.TFLiteConverter.from_saved_model(model_dir)
converter.optimizations = [tf.lite.Optimize.DEFAULT]  # INT8 PTQ
tflite_model = converter.convert()

# QAT in TensorFlow
import tensorflow_model_optimization as tfmot
qat_model = tfmot.quantization.keras.quantize_model(model)  # 插入 FakeQuant 层
# → 训练 → 转换
```

#### 嵌入式场景的量化注意

| 问题 | 表现 | 解决 |
|------|------|------|
| 权重/激活分布差异大 | 统一量化精度差 | 逐通道量化（Per-Channel） |
| INT8 累加溢出 | 中间结果超 INT8 范围 | Accumulator 用 INT32 |
| 量化参数不匹配 | PC 与 MCU 结果不一致 | 确认 scale/zero_point 一致 |

---

### 1.2 剪枝（Pruning）

#### 概念对比

| 类型 | 剪的是啥 | 优点 | 缺点 |
|------|---------|------|------|
| **非结构化剪枝** | 单个权重 → 置零 | 压缩率高 | **实际加速难**（稀疏矩阵运算硬件支持弱） |
| **结构化剪枝** | 整行/整列/整通道 | **可直接加速**（移除后矩阵变小） | 压缩率略低 |

#### 结构化剪枝 —— 通道剪枝

```
原始卷积层：C_in × C_out × K × K 个参数
通道剪枝后：C_in × (C_out - pruned) × K × K

剪掉的通道对应的输入/输出维度同时缩减
→ 计算量和内存线性减少
```

#### PyTorch 实操

```python
import torch.nn.utils.prune as prune

# 非结构化：对 Conv2d 的 weight 做 L1 剪枝 50%
prune.l1_unstructured(module, name="weight", amount=0.5)

# 结构化：按 L2 范数剪掉 30% 的通道
# 更推荐用 torch-pruning 等第三方库实现通道剪枝
```

#### 嵌入式场景的剪枝挑战

- 非结构化剪枝在 MCU 上**不直接加速**（没有稀疏矩阵硬件）
- TFLM **不支持稀疏格式的稀疏推理**
- → 端侧优先用 **结构化剪枝**，剪出更小的稠密模型

---

### 1.3 知识蒸馏（Knowledge Distillation）

#### Teacher-Student 框架

```
            ┌──────────────┐
            │  Teacher      │  ← 大模型（准确率高）
            │  (ResNet-50)  │
            └──────┬───────┘
                   │ Soft Labels (软标签)
                   ↓
            ┌──────────────┐
            │  Student      │  ← 小模型（目标：学到 Teacher 的"认知"）
            │  (MobileNet)  │
            └──────────────┘
```

#### 软标签 vs 硬标签

| 标签类型 | 形式 | 信息量 |
|---------|------|--------|
| 硬标签 | `[0, 0, 1, 0]` | 只知道"哪个正确" |
| 软标签 | `[0.01, 0.02, 0.85, 0.12]` | 还知道"哪些类相似" |

#### 蒸馏温度 T

```python
软标签 = softmax(Teacher_logits / T)   # T 越大 → 分布越"软" → 类别间关系越明显
Loss = α · CE(Student, Hard_label) + (1-α) · T² · KL(Student_soft, Teacher_soft)
```

| T 值 | 效果 |
|------|------|
| 1 | 几乎等于硬标签 |
| 2-5 | 适中，保留类别间关系 |
| 10-20 | 极软，适合发现大类结构 |

---

### 1.4 推理层优化（Inference Optimization）

| 技术 | 原理 | 收益 | TFLM 支持 |
|------|------|:---:|:---:|
| **算子融合** | Conv + BN + ReLU → 单个算子 | 减少内存读写 30-50% | ✅ 转换器自动做 |
| **常量折叠** | 将可预计算的常量提前算好 | 减少运行时计算 | ✅ |
| **内存复用** | 临时张量复用已释放的内存 | 减少峰值内存 20-40% | ✅ MicroAllocator |
| **Winograd** | 3×3 卷积用 Winograd 算法替换 | 加速 2× | ✅ CMSIS-NN 等 |
| **Loop Unrolling** | 编译器展开小循环 | 减少分支开销 | 编译器选项 |

---

## 二、神经网络架构

### 2.1 卷积神经网络（CNN）

#### 核心组件

```
Input (H×W×C)
    ↓
Conv2D (K×K kernel, 学习空间特征)
    ↓
BatchNorm (加速收敛、抑制梯度消失)
    ↓
ReLU/ReLU6 (激活函数，引入非线性)
    ↓
Pooling (Max/Avg，降维 + 扩大感受野)
    ↓
...重复...
    ↓
Flatten → Dense → Softmax (分类头)
```

#### CNN 在嵌入式上的关键参数

| 参数 | 含义 | 对 MCU 的影响 |
|------|------|-------------|
| `C_in × C_out × K × K` | 卷积层参数量 | 决定 Flash 占用 |
| `H × W × C` | 特征图大小 | 决定 SRAM 占用 |
| 卷积层数 | 模型深度 | 决定推理延迟 |

#### 1×1 卷积

```
作用：
├── 降维/升维（改变通道数，不改变空间尺寸）
├── 跨通道信息融合
└── 参数量极小（C_out × C_in）
```

---

### 2.2 深度可分离卷积（Depthwise Separable Convolution）

> MobileNet 的核心，也是 TFLM 默认支持的算子

```
标准卷积（3×3, C_in→C_out）：
  参数量 = C_in × C_out × 3 × 3

深度可分离卷积 = Depthwise + Pointwise：
  Depthwise: C_in × 1 × 3 × 3     ← 每个通道单独卷积
  Pointwise: C_in × C_out × 1 × 1 ← 1×1 卷积融合通道

参数量 ≈ 标准卷积的 1/C_out + 1/9  → 节省 ~8×
```

| 维度 | 标准卷积 | 深度可分离卷积 |
|------|:---:|:---:|
| 参数 | 多 | **少 7-8×** |
| 计算量 | 大 | **小 8-9×** |
| 精度 | 基准 | **略降 1-2%** |

---

### 2.3 循环神经网络（RNN）与 LSTM

#### RNN 的结构问题

```
h_t = f(W·x_t + U·h_{t-1})

问题：
├── 梯度消失/爆炸（连乘的导数趋近于 0 或 ∞）
└── 长期依赖捕获弱（越远的输入对当前影响越小）
```

#### LSTM 的门控机制

```
遗忘门 f_t：决定丢弃旧记忆的哪些部分
输入门 i_t：决定新信息哪些写入记忆
输出门 o_t：决定记忆哪些部分输出

核心：细胞状态 C_t 通过加法更新 → 梯度不会消失
```

#### 嵌入式场景适用性

| 架构 | 计算量 | 内存 | 适用 |
|------|:---:|:---:|------|
| LSTM | 高（4 个门×全连接） | 高（需要保留隐藏状态） | 关键词识别(KWS)、时序传感器 |
| GRU | 中（2 个门） | 中 | 同上，轻量替代 |
| Simple RNN | 低 | 低 | 精度差，几乎不用 |

---

### 2.4 轻量化网络架构

| 架构 | 年份 | 核心创新 | 参数量 | 嵌入式适配 |
|------|:---:|---------|:---:|:---:|
| **MobileNetV1** | 2017 | 深度可分离卷积 | ~4.2M | ✅ TFLM 官方示例 |
| **MobileNetV2** | 2018 | Inverted Residual + Linear Bottleneck | ~3.4M | ✅ 更高效的轻量方案 |
| **MobileNetV3** | 2019 | NAS + h-swish | ~5.4M | ✅ 搜索优化 |
| **ShuffleNetV2** | 2018 | Channel Shuffle | ~2.3M | ✅ |
| **SqueezeNet** | 2016 | Fire Module (1×1 压缩 + 扩张) | ~1.2M | ✅ 极致小 |
| **MCUNet** | 2020 | NAS + TinyEngine | **< 500KB** | ✅✅ MCU 专用 |

#### MobileNetV2 的 Inverted Residual

```
标准 Residual：宽→窄→宽（先压缩后扩张）
Inverted Residual：窄→宽→窄（先扩张后压缩）

原因：DW 卷积在低维空间表达能力弱
→ 先用 1×1 升维 → DW 卷积 → 1×1 降维
→ 6 倍扩张因子
```

#### 架构选型决策表

| 场景 | 推荐架构 | 理由 |
|------|---------|------|
| ESP32-S3 图像分类 | MobileNetV1 0.25× | 200KB 以内，延迟 < 50ms |
| STM32 关键词识别 | DS-CNN (深度可分离) | 语音特征 + 轻量 |
| 极致低功耗 | MCUNet | 专为 MCU 设计，< 64KB SRAM |
| 精度优先 | MobileNetV2 0.5× | 精度比 V1 高 2-3% |

---

## 三、实战组合拳：TFLM 部署优化 Checklist

```
□ 1. 训练阶段
   □ 用深度可分离卷积替代标准卷积
   □ 如果精度敏感 → QAT；否则 → PTQ
   □ 结构化剪枝减通道数（目标：50% 压缩）

□ 2. 转换阶段
   □ TFLiteConverter + optimizations=[DEFAULT]
   □ 确认 FlatBuffer 大小 < Flash 可用空间
   □ 用 Netron 可视化，确认算子全部在 TFLM 支持列表

□ 3. 部署阶段
   □ 用 MicroMutableOpResolver<N> 只注册用到的算子
   □ 用 RecordingMicroInterpreter 测定实际 arena 大小
   □ 用 CMSIS-NN 替换默认算子实现

□ 4. 验证阶段
   □ 对比 PC PyTorch 与 TFLM 推理结果（逐层）
   □ 测量延迟 + 内存峰值
   □ 录制"踩坑记录"（面试素材）
```

---

## 四、面试嘴替模板

| 问题 | 怎么说 |
|------|--------|
| "你怎么压缩模型？" | 「我的套路是三件套：量化（PTQ 优先）→ 结构化剪枝（50% 通道）→ 深度可分离卷积重构。三招下来模型从 4MB 压到 80KB」 |
| "为什么不用非结构化剪枝？" | 「MCU 没有稀疏矩阵硬件，非结构化剪枝不加速只压文件。嵌入式只做结构化剪枝」 |
| "PTQ 还是 QAT？" | 「精度敏感用 QAT（关键词识别差了 1% 就不识别了），精度不敏感用 PTQ。我会两个都跑一遍对比，选最优的」 |
| "深度可分离卷积为什么快？" | 「把标准卷积拆成空间+通道两步，参数量降到原来的 1/9，内存访问次数也同比例下降」 |

---

## 参考来源

- TFLM 官方文档：`tensorflow/lite/micro/`
- MobileNet 系列论文：Howard et al. (2017/2018/2019)
- Deep Compression: Han et al. (2016) — 量化+剪枝+霍夫曼编码三件套
- MCUNet: Lin et al. (2020) — MCU 专用架构搜索