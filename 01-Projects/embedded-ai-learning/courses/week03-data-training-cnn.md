# Week 3：模型训练实战 + 数据准备

> **日期**：2026-07-24（初建）
> **状态**：🔄 已排（待学习）
> **考核**：待完成
> **主线**：TFLM 源码阅读（conv.cc / pooling.cc / softmax.cc）
> **辅线**：CNN 架构、数据预处理、数据增强、训练技巧（围绕 TFLM 讲解）
> **源码根目录**：`source/tflite-micro-main/`
> **实践目标**：用 PyTorch 训练 CIFAR-10 CNN 模型（>70%），掌握数据工程全流程，为 Week 4 量化部署准备模型

---

## 一、CNN 在 TFLM 里的实现：三个核心算子

Week 1 我们拆解了全连接层（`FullyConnected`）——「两层 for 循环做矩阵乘加 + 激活」。CNN 比 FC 多两个关键操作：**卷积**和**池化**。下面逐一打开 TFLM 源码看实现。

### 1.1 卷积（Conv2D）—— 滑窗乘加

> 核心源码位置：`tensorflow/lite/micro/kernels/conv.cc`（调度层）→ 真实乘加循环在 `tensorflow/lite/kernels/internal/reference/conv.h`

**一句话**：卷积 = 一个 3×3（或 K×K）的「小窗口」在输入特征图上从头到尾滑动，每停一步做一次矩阵乘加，输出一个点。

```
输入特征图 H×W×C_in         卷积核 K_h×K_w×C_in×C_out     输出特征图 H×W×C_out
┌─────────────────┐         ┌───────────────────┐        ┌──────────────────┐
│ 1  2  3  4  5   │         │  w0 w1 w2 │ (×C_out)│        │  y0 y1 y2 y3 y4  │
│ 6  7  8  9  10  │    *    │  w3 w4 w5 │   组     │   =    │  y5 y6 y7 y8 y9  │
│ 11 12 13 14 15  │         │  w6 w7 w8 │         │        │  ...             │
│ 16 17 18 19 20  │         └───────────────────┘        └──────────────────┘
│ 21 22 23 24 25  │
└─────────────────┘
```

**TFLM 源码简化版（核心乘加循环）**：

```cpp
// tensorflow/lite/kernels/internal/reference/conv.h
// 核心三层 for 循环

for (int out_y = 0; out_y < output_height; out_y++) {
  for (int out_x = 0; out_x < output_width; out_x++) {
    for (int out_c = 0; out_c < output_depth; out_c++) {
      float total = bias[out_c];  // 从偏置开始
      // 对 3×3 窗口内每个位置做乘加
      for (int ky = 0; ky < kernel_height; ky++) {
        for (int kx = 0; kx < kernel_width; kx++) {
          for (int in_c = 0; in_c < input_depth; in_c++) {
            int in_y = out_y * stride + ky - padding;
            int in_x = out_x * stride + kx - padding;
            // 边界检查（padding 区域跳过）
            if (in_y >= 0 && in_y < input_height &&
                in_x >= 0 && in_x < input_width) {
              total += input[in_y][in_x][in_c] *
                       weights[ky][kx][in_c][out_c];
            }
          }
        }
      }
      output[out_y][out_x][out_c] = activation(total);
    }
  }
}
```

> **TFLM 真实调度路径**：`conv.cc` 的 `ConvEval()` 函数不直接做循环，而是按数据类型分发：
> ```cpp
> // conv.cc 中是调度器
> switch (input->type) {
>   case kTfLiteFloat32:  → reference_ops::Conv(...)   // 浮点卷积
>   case kTfLiteInt8:     → reference_integer_ops::ConvPerChannel(...) // INT8 量化卷积
> }
> ```
> 真正的乘加循环在 `reference/conv.h` 和 `reference/integer_ops/conv.h`（INT8版本）。这和 Week 1 全连接层的结构一模一样——**调度器 + 内核实现分离**。

### 1.2 池化（MaxPool2D / AveragePool2D）—— 降维

> 核心源码位置：`tensorflow/lite/micro/kernels/pooling.cc`

池化层的代码比卷积简单得多——没有权重，纯做「窗口内取最值/均值」。

```cpp
// 最大池化（MaxPool）核心逻辑
for (int out_y = 0; out_y < output_height; out_y++) {
  for (int out_x = 0; out_x < output_width; out_x++) {
    for (int c = 0; c < channels; c++) {
      float max_val = -INFINITY;
      for (int ky = 0; ky < pool_height; ky++) {
        for (int kx = 0; kx < pool_width; kx++) {
          float val = input[in_y + ky][in_x + kx][c];
          if (val > max_val) max_val = val;   // ← 就这一行逻辑
        }
      }
      output[out_y][out_x][c] = max_val;
    }
  }
}

// 平均池化（AveragePool）
// ... 同上，只是把 max_val 换成 sum / (pool_height * pool_width)
```

**池化的三个作用（对应 TFLM 部署时的影响）**：

| 作用 | 说明 | TFLM 部署影响 |
|------|------|-------------|
| **降维** | H、W 减半（如 2×2 pool stride=2），减少后续层计算量 | 中间激活张量缩小→**省 SRAM** |
| **平移不变性** | 小位移不影响池化结果 | 摄像头轻微抖动不改变输出分类 |
| **防过拟合** | 压缩特征，减少参数敏感性 | 模型更鲁棒、精度方差更小 |

> **嵌入式要点**：池化算子的计算量远小于卷积（$O(H×W×C)$ vs $O(H×W×K²×C_in×C_out)$），但**内存访存密度高**——遍历整个特征图只为取一次 max。在 MCU 上，池化往往不是瓶颈，瓶颈在卷积。

### 1.3 Softmax —— 输出概率

> 核心源码位置：`tensorflow/lite/micro/kernels/softmax.cc`

```cpp
// Softmax: 把 logits 转为概率分布（所有输出之和 = 1.0）
// softmax(x_i) = exp(x_i) / Σ exp(x_j)

float max_logit = find_max(logits);     // ① 先减最大值（防溢出）
float sum = 0.0;
for (int i = 0; i < num_classes; i++) {
  output[i] = exp(logits[i] - max_logit);  // ② exp
  sum += output[i];                         // ③ 累加
}
for (int i = 0; i < num_classes; i++) {
  output[i] /= sum;                         // ④ 归一化
}
```

> **嵌入式陷阱**：`exp()` 在 MCU 上没有硬件支持（Cortex-M4 以下无 FPU），TFLM 的 INT8 量化版 Softmax 会用**查表法（LUT）**替代 `exp()`，大幅加速。这也是为什么 Week 4 量化如此重要——整网 INT8 之后的 Softmax 也是用定点查表跑，省掉浮点 `exp()`。

### 1.4 CNN 与 FC 的计算量对比（嵌入式视角）

| 对比维度 | 全连接层（FC） | 卷积层（Conv2D） |
|----------|--------------|-----------------|
| **计算量** | $O(in×out)$ | $O(H×W×K²×C_in×C_out)$ |
| **参数量** | $in×out$（大） | $K²×C_in×C_out$（小） |
| **内存访问模式** | 顺序访问，cache 友好 | 滑窗访问，**内存跳跃** ← MCU 疼点 |
| **在 MCU 上** | 较快（矩阵乘法可 SIMD 加速） | 慢（需 im2col/patch 展开+矩阵乘法） |
| **典型使用** | 分类头（最后一层） | 特征提取（前若干层） |

> **关键认知**：CNN 的参数量比 FC 小很多（卷积核权重共享），但**计算量和内存访存量远大于 FC**。这就是为什么 Week 4 要学量化——INT8 化后 CNN 推理速度在 MCU 上能快 5~10 倍。

---

## 二、为什么 CNN 适合图像、1D CNN 适合时序？（架构选型复习）

> 衔接 Week 1 扩展思考题 Q4（架构选型决策表），这里从 TFLM 算子实现角度加深理解。

### 2.1 CNN 的「局部感知 + 权重共享」= 图像天然适配

```
图像特点                          CNN 如何利用
───────────────────────────────────────────────────
像素局部相关（相邻像素才有关）  →  卷积核只扫 local receptive field（3×3/5×5）
特征位置无关（猫在左上/右下都是猫）→  同一组权重扫全图（weight sharing）
特征层次化（边缘→纹理→部件→物体）→  多层堆叠逐层抽象（浅层抓边缘、深层抓语义）
```

### 2.2 1D CNN 为什么是工业时序最优解

> 扩展自 Week 1 Q4「1D CNN vs LSTM 对比表」

TFLM 里 1D CNN 本质上就是 Conv2D，只是 `kernel_height = 1`（只沿时间轴滑动）：

```cpp
// 1D CNN = Conv2D with kernel_height=1
// 输入: [batch, time_steps, channels]（TFLite 内部用 [1, 1, time, ch] 表示）
// 卷积核: [1, kernel_width, C_in, C_out]
// 输出: [1, 1, time', C_out]
```

| 场景 | 数据形状 | TFLM 实际跑什么 |
|------|---------|---------------|
| 2D 图像分类 | `[1, H, W, 3]` | Conv2D，kernel 在 H×W 上滑 |
| 1D 时序（振动/电流）| `[1, 1, T, 1]` | Conv2D with K_h=1，只沿 T 方向滑 |
| 1D 多通道（三轴加速度）| `[1, 1, T, 3]` | Conv2D with K_h=1，沿 T 滑、跨通道混合 |

> **嵌入式落地判断**：TFLM 里没有单独的 `Conv1D` 算子——所有 1D 卷积都用 `Conv2D` 实现。你在 `MicroMutableOpResolver` 里只需 `AddConv2D()`，不需要单独注册 1D 版本。

---

## 三、数据预处理：从传感器原始值到模型输入

> 这是嵌入式 AI 最容易踩坑的环节——预处理必须和训练时**严格一致**，否则模型输出错乱。

### 3.1 归一化（Normalization）—— 让数据落在激活函数的良好工作区

**为什么要归一化？** 以 ReLU 为例：

```
未归一化：ADC 原始值 0~4095
    ↓ 直接喂模型
    → 第1层输入极大 → 激活值饱和 → 梯度消失 → 训不动

归一化后：缩放到 [0, 1] 或 [-1, 1]
    ↓ 
    → 激活函数工作在线性/微饱和区 → 梯度稳定 → 正常训练
```

**三种主流归一化方式：**

| 方法 | 公式 | 适用场景 | TFLM 部署注意 |
|------|------|---------|-------------|
| **Min-Max** | $x' = \frac{x - min}{max - min}$ | 范围已知且稳定（传感器量程固定） | MCU 上只需减/乘，极快 |
| **Z-Score** | $x' = \frac{x - \mu}{\sigma}$ | 数据服从正态分布（图像常用 ImageNet 的 mean/std） | 需存 $\mu$、$\sigma$ 常量 |
| **固定范围** | $x' = x / 255.0$（图像） | 像素值 [0,255]→[0,1] | 最省事，只需除法 |

> **嵌入式落地原则**：部署时归一化参数（min/max 或 $\mu$/$\sigma$）必须**写死在代码常量里**，和训练时一字不差。工业传感器场景推荐 Min-Max——MCU 上「减 + 乘」两条指令，零开销。

### 3.2 One-Hot 编码 —— 分类标签的标准格式

```python
# 原始标签：数字 0~9
y = 3  # 第3类

# One-Hot 编码：长度为类别数的向量，只有对应位置为 1
y_onehot = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
                            ↑
                          第3类
```

**为什么用 One-Hot？** 交叉熵损失函数（`SparseCategoricalCrossentropy` 或 `CrossEntropyLoss`）需要这种格式计算概率分布之间的距离。TFLM 推理时输出也是 Softmax 概率向量，预测类别 = `argmax(output)`。

### 3.3 从原始数据到模型输入的完整流水线

```
传感器/文件 → Raw Data → 预处理 → 模型输入张量
             (uint16)   (归一化)   (float32 / int8)
             
示例：CIFAR-10 图像加载
┌──────────────────────────────────────────────────────┐
│ ① 加载 PNG/JPEG → uint8 [32, 32, 3]（0~255）        │
│ ② ToTensor → float32 [3, 32, 32]（0.0~1.0）        │
│ ③ 标准化 → Normalize(mean=[0.485,0.456,0.406],     │
│                       std=[0.229,0.224,0.225])      │
│ ④ batch 维度 → [1, 3, 32, 32] 送入模型             │
└──────────────────────────────────────────────────────┘
```

> **部署端代码一致性检查**（面试高频）：
> ```cpp
> // ❌ 错误：训练时用了 Min-Max 归一化到 [-1, 1]，部署时却除了 255
> float input = adc_value / 255.0f;
> 
> // ✅ 正确：训练用的什么，部署就一字不差地写什么
> // 训练时：x = (value - 0.0) / (4095.0 - 0.0)  →  [0, 1]
> float input = (float)adc_value / 4095.0f;
> ```

---

## 四、数据增强（Data Augmentation）—— 不花钱扩大数据集

> 核心思路：对训练样本做微小的、不影响类别的随机变换，让模型"见多识广"。

### 4.1 图像数据增强五件套

| 方法 | 操作 | 效果 | CIFAR-10 代码 |
|------|------|------|-------------|
| **随机水平翻转** | 左右镜像 | 猫朝左/朝右都认识 | `transforms.RandomHorizontalFlip()` |
| **随机裁剪+填充** | 裁一部分再缩回原大小 | 物体不在正中间也能识别 | `transforms.RandomCrop(32, padding=4)` |
| **颜色抖动** | 亮度/对比度/饱和度微调 | 适应不同光照 | `transforms.ColorJitter(brightness=0.2, contrast=0.2)` |
| **随机旋转** | 旋转 ±15°~30° | 物体倾斜也能认 | `transforms.RandomRotation(15)` |
| **标准化（必须）** | 减均值除标准差 | 统一量纲到模型友好区间 | `transforms.Normalize(mean, std)` |

**PyTorch 数据流水线（CIFAR-10 模板）**：

```python
import torchvision.transforms as transforms

# 训练集：数据增强 + 标准化
train_transform = transforms.Compose([
    transforms.RandomCrop(32, padding=4),        # 随机裁切
    transforms.RandomHorizontalFlip(),            # 随机水平翻转
    transforms.ColorJitter(brightness=0.2,        # 颜色抖动
                           contrast=0.2),
    transforms.ToTensor(),                        # uint8 → float32 [0,1]
    transforms.Normalize((0.4914, 0.4822, 0.4465),  # CIFAR-10 均值
                         (0.2023, 0.1994, 0.2010))  # CIFAR-10 标准差
])

# 验证/测试集：只做标准化，不做增强
val_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465),
                         (0.2023, 0.1994, 0.2010))
])
```

### 4.2 工业时序场景的数据增强（嵌入式 AI 特有）

图像增强是标配，**工业传感器增强才是嵌入式 AI 的差异化技能**：

| 方法 | 操作 | 模拟的现场工况 |
|------|------|-------------|
| **加高斯噪声** | `signal + np.random.normal(0, sigma)` | 电磁干扰、电源纹波 |
| **时间拉伸/压缩** | `np.interp` 插值 | 电机转速波动 |
| **幅值缩放** | `signal * random(0.8, 1.2)` | 负载变化 |
| **基线漂移** | `signal + slow_drift(t)` | 温度漂移、传感器老化 |
| **随机裁切** | 从长序列中随机取窗口 | 采集起始时刻随机 |

```python
# 工业时序增强模板
def augment_vibration(segment):
    """对振动信号做工业现场数据增强"""
    # ① 高斯噪声（模拟电磁干扰）
    noise_level = np.random.uniform(0, 0.05)
    segment += np.random.normal(0, noise_level, segment.shape)
    
    # ② 幅值缩放（模拟负载变化）
    scale = np.random.uniform(0.85, 1.15)
    segment *= scale
    
    # ③ 时间拉伸（模拟转速波动）
    if np.random.rand() > 0.5:
        factor = np.random.uniform(0.9, 1.1)
        new_len = int(len(segment) * factor)
        segment = np.interp(np.linspace(0, len(segment)-1, len(segment)),
                            np.linspace(0, len(segment)-1, new_len),
                            segment)
    
    return segment
```

> **面试加分话术**：「工业数据增强不是从论文抄的，是到了现场发现实际工况和训练数据差太远——电磁干扰、负载波动、温度漂移——必须针对性地加这些模拟噪声做增强，否则模型部署后精度直接掉 10%+。这和 CV 的随机裁剪/翻转是同一个思路，但是到了嵌入式工业现场才知道具体加什么。」

---

## 五、训练技巧三件套：学习率调度 / Early Stopping / Dropout

### 5.1 学习率调度（LR Scheduler）—— 先大步跑、后小步调

```
Epoch  1-50： lr = 0.1    ← 梯度大，快速收敛
Epoch 51-80： lr = 0.01   ← 逐步减小，精细调整
Epoch 81-100：lr = 0.001  ← 微调，避免跳过最优解
```

**三种常见调度器：**

| 调度器 | 做法 | PyTorch 代码 | 适用场景 |
|--------|------|-------------|---------|
| **StepLR** | 每 N 个 epoch 乘一个衰减因子 | `StepLR(optimizer, step_size=30, gamma=0.1)` | 通用，简单有效 |
| **CosineAnnealingLR** | 余弦曲线从大到小 | `CosineAnnealingLR(optimizer, T_max=100)` | 精度敏感型任务 |
| **ReduceLROnPlateau** | 验证 loss 不降时自动衰减 | `ReduceLROnPlateau(optimizer, patience=5)` | 不确定训练多久时用 |

> **嵌入式建模经验**：小模型（<500K 参数）通常 50~100 轮就收敛，不需要太复杂的调度策略。**StepLR 够用，余弦更稳**。

### 5.2 Early Stopping —— 别让模型背答案

```
训练 loss ↘       验证 loss ↘  → 模型在学习（正在变好）
训练 loss ↘       验证 loss ↗  → 开始背训练集了（过拟合！停下！）
                                    ↑
                                Early Stopping 触发点
```

```python
# Early Stopping 实现
best_val_loss = float('inf')
patience_counter = 0
PATIENCE = 10  # 容忍 10 个 epoch 不改善

for epoch in range(MAX_EPOCHS):
    train_loss = train_one_epoch(model, train_loader)
    val_loss = validate(model, val_loader)
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        torch.save(model.state_dict(), "best_model.pth")  # 保存最佳模型
    else:
        patience_counter += 1
        if patience_counter >= PATIENCE:
            print(f"Early Stopping at epoch {epoch}")
            break
```

### 5.3 Dropout —— 训练时随机关神经元，推理时全开

```
训练时：          推理时：
  ●  ○  ●          ●  ●  ●
  ○  ●  ●    →     ●  ●  ●     （所有神经元都工作）
  ●  ●  ○          ●  ●  ●
  (p=0.3 drop)     (全连接)
```

**核心原理**：每次前向传播随机关掉一部分神经元（p=0.3 意味 30% 被置 0），迫使网络不能依赖任何单个神经元——必须让多个神经元**协同工作**，增强了泛化能力。

```python
# PyTorch 中的 Dropout
model = nn.Sequential(
    nn.Conv2d(3, 32, 3, padding=1),
    nn.ReLU(),
    nn.Dropout2d(0.2),     # Conv 层后的 Dropout（drop 整个通道）
    nn.MaxPool2d(2),
    nn.Conv2d(32, 64, 3, padding=1),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Flatten(),
    nn.Linear(64*8*8, 256),
    nn.ReLU(),
    nn.Dropout(0.5),        # FC 层后的 Dropout（drop 单个神经元）
    nn.Linear(256, 10)
)
```

> **TFLM 部署视角**：Dropout 在推理时**自动剥离**——转 TFLite 后模型图里没有 Dropout 节点。这是 TFLite Converter 的标准优化（推理时不需要 dropout，会做常量折叠）。所以你会在 Netron 里看到 `.tflite` 里没有 Dropout，不是 bug。

---

## 六、优化器选型：SGD vs Adam

| 维度 | SGD（随机梯度下降） | Adam（自适应矩估计） |
|------|-------------------|---------------------|
| **学习率** | 固定，需手动调 | 自适应，每个参数有自己的学习率 |
| **收敛速度** | 慢（需更多 epoch） | 快（动量 + 自适应） |
| **泛化能力** | **通常更好**（更简单=更泛化） | 可能过拟合（参数太灵活） |
| **调参难度** | 需调 lr + momentum | 默认参数通常就够 |
| **内存占用** | 低 | 高（存两套矩估计） |
| **嵌入式场景推荐** | ✅ 追求最终精度 | ✅ 快速原型/没时间调参 |

```python
# PyTorch 代码对比
# SGD：经典，泛化好
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=5e-4)

# Adam：省心，收敛快
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
```

> **实践经验**：CIFAR-10 用 **SGD + momentum** 通常比 Adam 最终精度高 1~2%，但需要多跑 ~50 epoch。时间紧用 Adam，追求精度用 SGD。

---

## 七、CIFAR-10 CNN 实战模板

### 7.1 标准 CNN 模型（参数约 80K，适合 MCU 部署）

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class CIFAR10_CNN(nn.Module):
    """轻量 CNN：CIFAR-10 目标 >70% 准确率，约 80K 参数"""
    def __init__(self, num_classes=10):
        super().__init__()
        # Block 1：32×32×3 → 32×32×32 → 16×16×32
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        
        # Block 2：16×16×32 → 16×16×64 → 8×8×64
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        
        # Block 3：8×8×64 → 8×8×128 → 4×4×128
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3   = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        
        # 分类头：4×4×128 = 2048 → 256 → 10
        self.fc1 = nn.Linear(128 * 4 * 4, 256)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, num_classes)
    
    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        x = torch.flatten(x, 1)           # [B, 128, 4, 4] → [B, 2048]
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x
```

**算子清单（对照 TFLM 注册）**：

| 层 | PyTorch 算子 | TFLM 注册 |
|----|------------|----------|
| conv1/2/3 | `nn.Conv2d` | `AddConv2D()` |
| bn1/2/3 | `nn.BatchNorm2d` | **不需要注册**（TFLite 转换时折叠进 Conv 权重） |
| pool1/2/3 | `MaxPool2d` | `AddMaxPool2D()` |
| fc1/fc2 | `nn.Linear` | `AddFullyConnected()` |
| 激活 | `F.relu` | ReLU 通常融合在 Conv/FC 算子内，不需要单独注册 |

> **TFLM 算子数**：这个 CIFAR-10 CNN 实际只需要 `MicroMutableOpResolver<3>`（Conv2D + MaxPool2D + FullyConnected），BatchNorm 和 ReLU 在转换时被折叠/融合了。

### 7.2 完整训练脚本模板

```python
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader
import torchvision, torchvision.transforms as transforms

# ── 数据准备 ──────────────────────
train_transform = transforms.Compose([
    transforms.RandomCrop(32, padding=4),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465),
                         (0.2023, 0.1994, 0.2010))
])

trainset = torchvision.datasets.CIFAR10(
    root='./data', train=True, download=True, transform=train_transform)
trainloader = DataLoader(trainset, batch_size=128, shuffle=True)

testset = torchvision.datasets.CIFAR10(
    root='./data', train=False, download=True,
    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465),
                             (0.2023, 0.1994, 0.2010))
    ]))
testloader = DataLoader(testset, batch_size=128, shuffle=False)

# ── 模型 / 损失 / 优化器 ──────────
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CIFAR10_CNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=5e-4)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)

# ── 训练循环 ──────────────────────
EPOCHS = 100
best_acc = 0.0

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    for inputs, labels in trainloader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    
    scheduler.step()
    
    # 验证
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for inputs, labels in testloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    acc = 100. * correct / total
    if acc > best_acc:
        best_acc = acc
        torch.save(model.state_dict(), "best_cifar10_cnn.pth")
    
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1:3d}/{EPOCHS} | Loss: {running_loss:.3f} | Acc: {acc:.2f}%")

print(f"\nBest Accuracy: {best_acc:.2f}%")
```

---

## 关键概念速查

| 概念 | 一句话解释 |
|------|-----------|
| **Conv2D** | 滑窗做乘加，提取局部特征；TFLM 里=调度器+内核循环分离 |
| **MaxPool2D** | 窗口内取最大，降维+平移不变性 |
| **Softmax** | 把 logits 转为 [0,1] 概率分布，和为 1 |
| **BatchNorm** | 标准化每层输入，加速收敛；TFLite 转换时**折叠进权重** |
| **Dropout** | 训练时随机关神经元防过拟合；推理时**自动剥离** |
| **归一化** | 数据缩放到模型友好区间，部署时必须和训练一致 |
| **数据增强** | 微调训练样本增加多样性，图像=翻转/裁切，工业=加噪声/漂移 |
| **1D CNN** | Conv2D with K_h=1，沿时间轴卷积，TFLM 无需单独算子 |
| **Early Stopping** | 验证 loss 不再下降时停训，防过拟合 |
| **SGD vs Adam** | SGD 泛化好但慢，Adam 收敛快但可能过拟合 |
| **StepLR** | 每隔 N epoch 学习率 ×衰减因子，最简单有效的调度策略 |

---

## 今日任务

- [ ] 读懂 Conv2D 的三层 for 循环（`reference/conv.h`），理解为什么是 $O(H×W×K²×C_in×C_out)$
- [ ] 在 Netron 中打开一个 CNN 的 `.tflite`，数出用了哪几种算子，确认 BatchNorm 和 Dropout 是否已经消失
- [ ] 从 TFLM 源码 `pooling.cc` 中定位 MaxPool 和 AveragePool 的核心循环
- [ ] 运行 CIFAR-10 训练脚本，达到准确率 > 70%
- [ ] 实现完整数据预处理流水线（含数据增强）
- [ ] 对比 SGD 和 Adam 在 CIFAR-10 上的收敛曲线和最终精度
- [ ] 整理一份「模型训练 Checklist」（见下方模板）

---

## 思考题

### 问题1：BatchNorm 在 TFLite 转换后为什么消失了？这对 TFLM 部署有什么好处？

**思考提示：**
1. BatchNorm 的计算公式是什么？转换到推理模式后和训练模式有什么不同？
2. 为什么可以把 BN 的参数「折叠」进前一层的卷积权重里？
3. 这对 MCU 内存和推理速度有什么好处？

### 问题2：为什么 Dropout 只在训练时用，推理时不需要？TFLM 里有没有 Dropout 算子？

**思考提示：**
1. Dropout 的数学本质是什么？推理时如果还随机关闭神经元会怎样？
2. 打开 TFLM 的 `micro_mutable_op_resolver.h`，能找到 `AddDropout()` 吗？

### 问题3：工业振动传感器做 CNN 分类，数据增强应该加什么？和图像数据增强有什么本质区别？

**思考提示：**
1. 振动信号和图像信号的物理含义有什么不同？
2. 工业现场的干扰源有哪些？（电磁、负载、温度……）
3. 图像翻转不影响「这是一只猫」，振动翻转意味着什么？

### 问题4：Early Stopping 和固定 Epoch 训练，在嵌入式 AI 场景下应该选哪个？为什么？

**思考提示：**
1. 嵌入式 AI 项目中，训练在 PC 端完成，部署在 MCU 上。Early Stopping 影响了什么？
2. 你的目标是"找一个在 MCU 上表现最好的模型"，而不是"找一个在验证集上最好的模型"——这两者可能不同吗？

---

## ✍️ 思考题答题区

### 问题1：BatchNorm 为什么在 TFLite 里消失了？

> （你的答案写在这里）

### 问题2：Dropout 推理时为何不需要？

> （你的答案写在这里）

### 问题3：工业振动数据增强 vs 图像数据增强

> （你的答案写在这里）

### 问题4：Early Stopping vs 固定 Epoch

> （你的答案写在这里）

---

## 🔬 实践结果区

### 任务1：CIFAR-10 CNN 训练结果

| 指标 | 数值 |
|------|------|
| 模型名称 / 参数量 | |
| 优化器 | SGD / Adam（勾选） |
| 学习率调度 | |
| 数据增强 | |
| 训练 Epoch 数 | |
| 最终训练准确率 | |
| 最终测试准确率 | |
| 最佳模型文件名 | |

### 任务2：SGD vs Adam 对比

| 指标 | SGD | Adam |
|------|-----|------|
| 收敛所需 Epoch | | |
| 最终测试准确率 | | |
| Loss 曲线特征 | | |
| 结论 | | |

### 任务3：模型训练 Checklist

> 整理你学到的关键检查项，可以用下方模板，也可自己写一份。

```
☐ 数据预处理：训练和验证用的 transform 是否一致？
☐ 数据增强：是否只在训练集做增强、验证集不做？
☐ BatchNorm：训练时 model.train()、验证时 model.eval() 是否切换？
☐ Dropout：同上，model.eval() 会自动关闭 Dropout
☐ 学习率：初始值是否合理（SGD:0.01, Adam:0.001）？
☐ 优化器：weight_decay 是否设置（1e-4~5e-4）？
☐ 模型保存：是否保存最佳的 best_model.pth（而不是最后一轮）？
☐ 算子兼容：最终模型的所有算子是否都在 TFLM 支持列表中？
☐ 预处理一致性：训练时的 Normalize(mean, std) 是否已记录、部署时是否会一字不差地用？
☐ BatchNorm 折叠：转 TFLite 时是否确认 BN 已折叠（Netron 里看不到 BN 节点）？
```

### 任务4：Netron 模型对比

> （截图对比：训练版模型 vs TFLite 转换后模型，标注消失了哪些节点）

---

## 💭 学习心得

> **日期**：
> **主题**：
>
> ### 核心洞见
> 
> （记录你今天最深刻的理解）
>
> ### 与嵌入式开发的类比
> 
> （把 CNN/数据增强/训练技巧和你已有的嵌入式经验关联起来）
>
> ### 困惑与下一步
> 
> （今天没搞清楚的点 + 接下来想深入的方向）

---

## ❓ 待解决问题

- [ ] 
- [ ] 

---

## 🎯 AI 助教反馈（完成后填写）

> （AI 批改后填写）
> 打分：___/10
> 评语：

---

## 🧠 扩展思考题

### 问题5：CIFAR-10 模型（~80K 参数）能否放进 ESP32-S3 的 Flash 和 SRAM？

用 Week 1 Q5 的「硬约束检查表」逐项核对：

| 检查项 | 计算方法 | 数值 |
|--------|---------|------|
| ① 模型大小（Flash） | 80K 参数 × 1(INT8) = 80KB | 80KB / 8MB Flash → **1%** ✅ |
| ② 推理峰值 SRAM | 最大层：Conv3 输入 4×4×128 + 输出 4×4×128 ≈ 4KB | < 512KB SRAM ✅ |
| ③ 算子支持 | Conv2D / MaxPool2D / FC | TFLM 全支持 ✅ |
| ④ 推理延迟 | INT8 + NPU：~100K MAC / 240MHz | < 5ms ✅ |

> **结论**：CIFAR-10 80K 参数 CNN 在 ESP32-S3 上完全跑得动，瓶颈不在模型大小而在精度——Week 4 量化后部署。

### 问题6：工业时序场景的 1D CNN，为什么不需要像 CV 一样用很深的网络？

```
CV（ImageNet）：    1D CNN（工业时序）：
224×224×3 输入      1×T×1 输入（T=100-200）
1000 类输出          2-5 类输出
深度 50-150 层       深度 3-5 层
参数量 10M+          参数量 5-30K
────────────────────────────────
原因：
① 输入信息量差 1000 倍（224²×3 vs 200×1）
② 类别数差 200-500 倍
③ 工业信号的特征比自然图像简单得多
   — 图像需要「边缘→纹理→部件→物体」层层抽象
   — 振动信号「均值/峰值/RMS/频率」一两层 CNN 就能抓到
④ 数据量差 3-4 个数量级（ImageNet 120 万张 vs 工业现场可能只有几千条）
   — 深网络 + 小数据 = 严重过拟合
```

---

## 📊 模型训练 Checklist（完整版）

> 训练脚本每次启动前逐项核对。这份 Checklist 覆盖从数据到部署的全链路。

### 数据准备
- [ ] 训练集和验证集已正确划分（没有数据泄露）
- [ ] 训练集应用了数据增强，验证集只做了标准化
- [ ] 数据增强的参数与任务匹配（图像：翻转/裁切；时序：加噪/缩放）
- [ ] 归一化参数（mean/std 或 min/max）已记录，将用于部署端

### 模型设计
- [ ] 输入尺寸与数据实际尺寸一致
- [ ] 输出类别数与任务一致
- [ ] 模型的所有算子都在 TFLM 支持列表中（对照 `micro_mutable_op_resolver.h`）
- [ ] 参数量在目标 MCU Flash 容量内（INT8 量化后 = 参数量 × 1 Byte）

### 训练配置
- [ ] 损失函数与任务类型匹配（分类→CrossEntropy，回归→MSE/MAE）
- [ ] 优化器学习率初始值合理（SGD:0.01，Adam:0.001）
- [ ] 使用了学习率衰减策略（StepLR 或 CosineAnnealing）
- [ ] BatchNorm 层在训练时 model.train()、验证时 model.eval()
- [ ] Dropout 在训练时开启（model.train()），验证时自动关闭
- [ ] 权重衰减（weight_decay）已设置（1e-4 ~ 5e-4）

### 验证与保存
- [ ] 每个 epoch 或每 N 个 epoch 做一次验证
- [ ] 保存的是**验证集表现最好**的模型（不是最后一轮的）
- [ ] 记录了最佳模型对应的 epoch 和准确率

### TFLM 部署准备（Week 4 衔接）
- [ ] 用 Netron 确认 BatchNorm 已被折叠、Dropout 已剥离
- [ ] 统计了模型实际使用的算子种类数（确定 `MicroMutableOpResolver<N>` 的 N）
- [ ] 预估了 tensor arena 大小（取最大层输入+输出 × 1.3 安全系数）
- [ ] 归一化参数已存档，将硬编码到 MCU 预处理代码中

---

## 🎯 Week 4 衔接预告

> Week 3 训练好的 CIFAR-10 模型，Week 4 将走完以下流程：
> 1. **INT8 后训练量化（PTQ）**：模型体积缩小 4×，推理加速 5~10×
> 2. **量化精度验证**：对比量化前后精度损失，控制在 3% 以内
> 3. **模型剪枝**：结构化剪枝砍掉 50% 通道，再微调恢复精度
> 4. **知识蒸馏**：大模型教小模型，压缩模型同时保精度
> 5. **TFLM 部署到 ESP32-S3**：完整跑通「采集→推理→输出」全链路
>
> Week 3 的模型就是 Week 4 的「原材料」——CIFAR-10 CNN 训练得越好，Week 4 量化后的精度底线越高。

---

**文件版本**：v1.0
**创建时间**：2026-07-24
**基于计划**：`3-month-mastery-plan.md` Week 3
**下一课**：`week04-quantization-pruning-distillation.md`（Week 4 模型量化+剪枝+蒸馏+部署）
