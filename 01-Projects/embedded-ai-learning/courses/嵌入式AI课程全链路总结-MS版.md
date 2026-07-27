# 嵌入式AI课程全链路总结（面试版）

> 课程：AI+嵌入式 千聊课程，Day3~Day16
> 项目：STM32N647 + QMI8658A 动作识别（idle/walk/stairs 三分类）
> 更新：2026-07-28 补充 Day16 根因分析报告与部署契约细节

---

## 一、一句话项目描述（简历用）

> 基于 STM32N647（Cortex-M55 + Neural-ART NPU）+ QMI8658A 六轴 IMU，独立完成人体动作识别全链路落地：**数据采集(40Hz) → 特征提取(56维时频域) → 模型设计(MLP) → 训练验证(时间块隔离) → 全INT8量化(6352B) → TFLM/X-CUBE-AI端侧部署**。测试准确率 92.95%，单帧推理 <5ms，含 Python↔C 一致性自检、OOD 检测、两窗EMA稳定判据。

---

## 二、硬件平台

| 组件 | 型号/规格 |
|------|----------|
| MCU | STM32N647（Cortex-M55 @800MHz，支持 Helium 向量扩展） |
| NPU | Neural-ART @1GHz（可选，CPU 版本无需额外权重文件） |
| IMU | QMI8658A 六轴（3轴加速度 + 3轴陀螺仪） |
| AI 框架 | TensorFlow Lite Micro + X-CUBE-AI v10.2 |
| IDE | STM32CubeIDE 1.19 + CubeMX 6.16 |

---

## 三、全链路 7 环节

### 环节1：数据采集与清洗（Day11）

**流程**：
```text
QMI8658A 原始寄存器 → 零偏估计(前100样本) → 低通滤波(α=0.25)
→ 重力跟踪(α=0.02) → ×1000取整 → 串口输出 → GUI采集 → *_clean.csv
```

**关键参数**：
- 采样率 40Hz（25ms 周期）
- 加速度单位 **g**（不是 m/s²）— 这是 Day16 审计发现的核心矛盾
- 陀螺仪单位 rad/s
- 静止时 `acc_norm/1000 ≈ 0.998`

**面试问答**：
- Q: 为什么用 40Hz 而不是 100Hz 或更高？
  A: 人体动作频率集中在 0.5-5Hz，奈奎斯特定理 40Hz 可覆盖 20Hz；更高采样率对 MCU 负载和功耗不友好，且不提升分类性能。

### 环节2：特征提取（Day12 + Day16 优化）

**滑动窗口**：64 点（1.6 秒），步长 16 点（0.4 秒，75% 重叠）

**最终模型（模型B）使用 56 维特征 = 40 维时域 + 16 维频域**：

| 类型 | 来源 | 特征数 | 关键特征 |
|------|------|-------|---------|
| 时域统计 | 5 通道 × 9 统计量 | 45 | RMS、峰峰值、过零率、绝对差分均值 |
| 时域协方差 | lin/gyro 各自 3 轴协方差 | 5 | 特征值、协方差比、均值向量模 |
| 相关系数 | lin_norm × gyro_norm | 1 | Pearson 相关系数 |
| **时域合计** | | **51→实际40** | |
| 频域 | 4 通道 × 4 统计量 | 16 | 主频、频谱重心、频谱熵、频带能量比 |
| **总计** | | **56** | |

**5 个基础通道**：`lin_norm`, `gyro_norm`, `acc_norm_centered`, `lin_delta_norm`, `gyro_delta_norm`
— 全部基于合成模长和差分模长，方向无关，提高泛化性。

**面试问答**：
- Q: 为什么 walk 和 stairs 只用时域特征区分不好？
  A: 两者的 RMS、峰峰值等时域统计量高度重叠。但频域不同：walk 主频约 2Hz（步频），stairs 主频约 1.5Hz 且频谱更分散。必须加频域特征才能分开。
- Q: 特征中 acc_norm_centered = acc_norm - 1 是什么目的？
  A: 静止时 acc_norm ≈ 1g，减 1 后静止特征 ≈ 0，运动时偏离 0，帮助模型区分静止和运动。

### 环节3：模型设计（Day13）

```text
输入(56) → Dense(32, ReLU) → Dense(16, ReLU) → Dense(3, Softmax)
参数量：56×32+32 + 32×16+16 + 16×3+3 = 1792+32 + 512+16 + 48+3
      = 1824 + 528 + 51 = 2403 参数
```

- 用 MLP 不用 CNN/LSTM：特征已经手工提取为 1D 向量，MLP 最直接且参数最少
- ReLU 原因：计算简单（max(0,x)），梯度不饱和，INT8 量化友好

### 环节4：模型训练与验证（Day14 + Day16 V2）

**Day16 的关键改进**（V2 消融实验）：

| 配置 | 主测试准确率 | Walk 准确率 | Stairs 准确率 | Walk尾段覆盖率 |
|------|:----------:|:----------:|:------------:|:------------:|
| 1×权重 | 92.14% | 86.52% | 92.13% | 53.66% |
| **2×权重(最终)** | **93.22%** | **90.78%** | **90.55%** | **75.61%** |
| 4×权重 | 89.70% | 82.27% | 89.76% | 73.17% |

- 数据按时间分三段（60% train / 20% val / 20% test），含 64 样本隔离带
- 上楼梯→走路过渡区（290768~297168ms）人工排除，不参与训练
- 尾段重标为 Walk，加 2×硬样本权重 → 最佳平衡点
- **没有使用随机打散 + 交叉验证** — 时间顺序划分更真实反映部署场景

**面试问答**：
- Q: 为什么不用随机划分而是时间顺序？
  A: 时间顺序划分更接近真实部署——训练用老数据，测试用新数据。随机划分会导致同一次采集的相邻窗口同时出现在训练和测试中，评估虚高。

### 环节5：全 INT8 量化（Day15/Day16）

```python
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = rep_dataset  # 训练集校准数据
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```

**INT8 参数**（deployment_contract.json）：
```json
{
  "input_scale": 0.046315137,
  "input_zero_point": -13,
  "output_scale": 0.00390625,
  "output_zero_point": -128
}
```
- 量化公式：`q = clamp(round_half_away_from_zero(normalized/scale + zp), -128, 127)`
- 模型大小：6352 字节（INT8） vs ~27KB（FP32），4.3× 压缩
- Keras ↔ TFLite INT8 逐样本一致率：**99.73%**

### 环节6：TFLM 端侧部署（Day5/Day1）

```cpp
// ① 注册算子（编译期确定，零堆分配）
MicroMutableOpResolver<3> op_resolver;
op_resolver.AddFullyConnected();  // ReLU 融合在 FC 里
op_resolver.AddSoftmax();

// ② 创建解释器
MicroInterpreter interpreter(model, op_resolver, tensor_arena, kTensorArenaSize);

// ③ 静态内存分配
interpreter.AllocateTensors();

// ④ 设置 INT8 输入
interpreter.input(0)->data.int8[i] = quantized_feature;

// ⑤ 执行推理
interpreter.Invoke();  // 拓扑顺序，完全确定性

// ⑥ 读取输出
int8_t* output = interpreter.output(0)->data.int8;
// 反量化：probability = (output[i] - (-128)) × 0.00390625
```

**关键设计哲学**：
| 设计 | 原因 |
|------|------|
| tensor_arena 静态预分配 | MCU 无 MMU，malloc 会导致内存碎片 |
| OpResolver\<N\> 模板 | 编译期确定算子集，只链接用到的 |
| FlatBuffer 格式 | 零拷贝、零解析、直接映射到内存 |

### 环节7：系统集成与工程化（Day16 重点）

**三级任务架构（FreeRTOS）**：
```
优先级 高：传感器采集（定时器触发，写环形缓冲区）
优先级 中：AI 推理（队列接收数据，TFLM Invoke()）
优先级 低：业务逻辑（串口上报、显示更新）
```

---

## 四、Day16 工程深度 — 5 个真实根因与修复（面试亮点）

这正是面试中能让你和纯算法候选人拉开差距的部分：

### Bug 1：板端清洗与训练不一致
- **问题**：Day16 曾加入"静止后重置重力"和"动态加速重力跟踪"
- **训练**：用的是固定 `alpha=0.02` 的重力低通
- **后果**：相同动作在训练和板端产生不同的线性加速度
- **修复**：恢复固定 α=0.25 低通 + α=0.02 重力跟踪，删除自适应重置

### Bug 2：模型概率被人为覆盖
- **问题**：C 代码把某些窗口硬改为 `Idle=100%`，按陀螺仪阈值交换 Walk 和 Stairs
- **后果**：屏幕显示的 100% 和 27.4% 不是模型的真实输出
- **修复**：三个类别概率原样输出，不再改成 100%，不再交换

### Bug 3：AI 初始化执行了两次
- **问题**：`MX_X_CUBE_AI_Init()` 同时出现在 CubeMX 自动代码区和用户区
- **后果**：模型句柄被重复创建，内存状态不确定
- **修复**：只保留一次调用

### Bug 4：模型 A（无频域）区分不了 walk 和 stairs
- **问题**：只用 40 维时域特征，两类动作的模长统计高度重叠
- **修复**：升级到模型 B（56 维），增加 16 维频域特征（主频、频谱重心、频带能量比）

### Bug 5：传感器单位不一致 — 9.807 倍矛盾（经典案例）
- **发现**：Day11 源码中用 `raw × 9.807 / sensitivity` 产出 m/s²
- **但实际 CSV** 中静止时 `acc_norm/1000 ≈ 0.998`，明确是 g
- **根因追溯**：GUI 采集工具只是原样保存串口文本，没有做 9.807 缩放；当时烧录的固件版本可能不是当前源码版本
- **裁决**（deployment_contract.json）：以实际 CSV 为数值权威，Day16 必须用 g
- **预防**：启动自检中串口显示 `DAY16_SAMP an=1000`（静止时），若显示 9807 则说明烧了错误的 m/s² 驱动，所有模型结果无效

### 面试时要讲的故事线：
> "部署阶段最难的往往不是模型本身，而是 Python ↔ C 的端到端一致性。我们碰到了 5 个真实 Bug——清洗算法不一致、概率被人为修改、AI 重复初始化、特征维度不匹配、传感器单位 9.807 倍偏移。每一个的根因定位和修复都比训练模型本身更有工程价值。"

---

## 五、部署契约（deployment_contract.json）— 端到端一致性的宪法

这是整个课程最有工程价值的设计模式。**Python 训练端和 C 部署端之间，用 JSON 定义了精确契约**：

```json
{
  "sampling": {
    "target_rate_hz": 40.0,
    "window_samples": 64,
    "hop_samples": 16,
    "deployment_requirement": "25ms 固定调度器，UART/LCD 不能定义采样周期"
  },
  "recorded_data_is_numeric_authority": {
    "acceleration_driver_unit_required": "g",
    "forbidden_conversion": "禁止在模型输入前乘 9.807"
  },
  "int8_formula": {
    "input_scale": 0.046315137,
    "input_zero_point": -13
  },
  "runtime_decision": {
    "probabilities": "不覆盖模型原始概率",
    "label_smoothing": "EMA α=0.45，最小概率 0.50，top2 最小差距 0.08",
    "out_of_distribution_guard": "clip>10 则维持上一个稳定标签"
  },
  "boot_self_test": {
    "expected_terminal_line": "[AI] PARITY_PASS,input_diff_gt1=0",
    "covered_chain": "清洗→56特征→clip→normalize→INT8输入→X-CUBE-AI输出"
  }
}
```

契约覆盖了：采样率、传感器单位、特征顺序、INT8 参数、输出处理策略、启动自检。任何一方修改，SHA256 会变，契约作废。

---

## 六、运行时安全机制

### 上电自检（Parity Check）
```
[AI] PARITY_PASS,input_diff_gt1=0   ← C 端和 Python 端输入一致
[AI] PARITY_FAIL                    ← 不一致，后续结果不可信
```
用 3 组固定窗口验证：清洗→特征→INT8 输入→模型输出，全程与 Python 比较。

### OOD 检测（Clip 计数）
正常输入窗口的 clip 数 0~3。超过 10 → 判定为分布外输入（如旋转、挥动、改变安装位置），维持上一个稳定标签，不输出不确定结果。

### 两窗 EMA 确认
```text
EMA α=0.45, 最小概率 0.50, top2 最小差距 0.08
需要连续 2 个窗口都满足条件才切换标签
```
防止单次噪声导致状态抖动。

---

## 七、最终性能指标

| 指标 | 值 |
|------|:---:|
| 最终模型 | 模型B（56维时域+频域） |
| INT8 大小 | 6352 字节 |
| 测试准确率 | 92.95% |
| Macro-F1 | 93.51% |
| idle F1 | 100.00% |
| walk F1 | 91.10% |
| stairs F1 | 90.20% |
| Keras→TFLite 一致率 | 99.73% |
| ELF text | 93880 字节 |
| ELF bss | 2060532 字节（大部分为显示帧缓冲） |

---

## 八、已知限制（面试诚实说明加分项）

1. **三类数据各只有一段连续录制**，不是跨天/跨人/跨握持方式采集
2. **Walk 尾段参与了训练**，79.27% 覆盖率 ≠ 独立泛化准确率
3. **没有"未知动作"类别**，所有输出都被强制归入三分类之一
4. **时间块验证不是跨人员验证**，正式部署前需要独立盲测数据

> 面试时承认这些限制比假装模型完美更能体现工程成熟度。

---

## 九、高频面试问答速查

### 量化相关
| 问题 | 答案 |
|------|------|
| INT8 量化原理 | `真实值 = (整数值 - zero_point) × scale` |
| PTQ vs QAT | PTQ 训练后量化快速但可能掉点 2-5%；QAT 训练中模拟量化精度好但需改训练代码 |
| 量化掉点怎么排查 | ①校准集覆盖率 ②前后处理一致性 ③PTQ→QAT ④混合精度 |
| 为什么全 INT8 | 只量化权重不量化激活仍需 float 运算，MCU 无 FPU 则性能提升有限 |

### TFLM 相关
| 问题 | 答案 |
|------|------|
| tensor_arena | 静态预分配内存池，零堆碎片 |
| 为什么不用 malloc | MCU 无 MMU，malloc 导致内存碎片，长时间运行后崩溃 |
| FlatBuffer 优势 | 零拷贝、零解析、直接内存映射 |

### 工程落地相关
| 问题 | 答案 |
|------|------|
| Python↔C 一致性怎么保证 | 部署契约 JSON + 启动 PARITY 自检 + SHA256 版本锁定 |
| OOD 输入怎么处理 | clip 计数 >10 判定分布外，维持上一个稳定标签 |
| 传感器单位不一致怎么发现 | 训练数据审计：CSV 中静止 acc_norm≈998 而代码注释说 m/s²，9.807 倍矛盾 |
| 模型推理不稳定怎么调试 | 先看 PARITY_PASS/FAIL，再看原始概率（不能被后处理覆盖），最后看 DAY16_SAMP |

---

## 十、课程知识地图

```
Day3-5   基础入门：TFLite模型 → Demo工程 → TFLM核心架构（理论为主）
Day6-9   端到端Demo：Add算子AI vs No-AI → 正弦波数据→训练→量化→部署 → 性能评估
Day11    数据采集：真实QMI8658A IMU，串口采集，清洗管线，GUI工具
Day12    特征工程：滑窗64/32，时域9统计量+协方差，频域FFT+频谱特征
Day13    模型设计：MLP Dense32+16+Softmax，2403参数
Day14    训练验证：时间顺序划分，2×硬样本权重，Macro F1评估
Day15    量化转换：全INT8转换，校准集，TFLite验证
Day16 ★  终极部署：5个根因修复，4套部署方案(MCU无频域/MCU含频域/NPU含频域/No-AI基线)，
          8个Python Pipeline脚本，部署契约JSON，Parity自检，OOD检测
```

---

## 关联

- [[嵌入式AI笔记-课程项目全流程]] — Day1/5/8/11-15 详细笔记（含 17 道面试题）
- [[week01-day01-tflm-hello-world]] — TFLM 源码深度分析
- 原始材料：`E:\ProjectGroup\AI\EmbeddedAI\购买课程1-嵌入式AI\嵌入式AI\千聊课程\`
- Day16 关键文件：
  - `STM32动作识别端到端根因与修复报告.md` — 5个Bug的完整分析
  - `Day11到Day16真实数据流审计报告.md` — 9.807倍矛盾追溯
  - `Day16_最终模型设计与验证报告.md` — 模型A/B对比
  - `V2_动作切换与重训练结论.md` — 硬样本权重消融实验
  - `deployment_contract.json` — Python↔C部署契约
