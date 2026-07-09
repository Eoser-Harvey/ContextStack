# 嵌入式AI工程师笔记 — 课程项目全流程（原理+实践+问答）

> 基于「AI+嵌入式」课程（Day1/5/8/11-15）+ TFLM 源码学习 + 8年工业嵌入式经验
> 项目载体：**STM32N647 + QMI8658A 六轴IMU 人体动作识别系统**（idle/walk/stairs 三分类）
> 目标：面试时能讲清全链路、答出深度、展示落地能力

---

## 一、项目一句话描述（简历用）

> 基于 STM32N647 + QMI8658A 六轴 IMU，独立完成人体动作识别（idle/walk/stairs 三分类）的**全链路落地**：数据采集→特征提取（时域11+频域13维）→模型设计（MLP Dense32+16+Softmax）→训练验证（Keras+EarlyStopping+混淆矩阵）→INT8量化→TFLM端侧部署，单帧推理<5ms，模型<20KB，测试准确率92%+。

---

## 二、端侧AI全流程（7环节 × 原理+实践+问答）

### 环节1：数据采集与清洗（Day11）

**原理**：
- 硬件：STM32N647 + QMI8658A（六轴 IMU：三轴线性加速度 + 三轴角速度）
- 采样率 50Hz，每帧含 lin_ax/ay/az（m/s²）+ gx/gy/gz（rad/s）
- 清洗流程：原始数据 → 去除 invalid 标记帧 → 去除 clipped（超出量程）帧 → 单位归一化（×1000 整数 → 浮点）→ 计算 acc_norm / gyro_norm 合成幅值

**实践要点**：
```python
# 关键：合成幅值 = sqrt(ax² + ay² + az²)，消除方向依赖
df["lin_acc_mag_mps2"] = np.sqrt(df["lin_ax_mps2"]**2 + df["lin_ay_mps2"]**2 + df["lin_az_mps2"]**2)
```

**面试问答**：
- Q: 为什么用合成幅值而不是单轴？
  A: 单轴数据依赖设备佩戴方向，合成幅值 `sqrt(ax²+ay²+az²)` 是方向无关的，模型泛化性更好。部署时也只需一个特征通道。
- Q: 采样率为什么选 50Hz？
  A: 人体动作频率集中在 0.5-5Hz，根据奈奎斯特定理 50Hz 采样可覆盖到 25Hz，远超需求；同时 50Hz 对 MCU 负载友好（20ms 一帧）。

---

### 环节2：特征提取与可视化（Day12）

**原理**：
- 滑动窗口切片：window_size=64（1.28s），step_size=32（50% 重叠）
- 每个窗口提取 **时域11特征 + 频域13特征**，8 路信号 × 24 特征 = **192 维特征向量**
- 时域特征：mean, max, min, variance, std, peak_to_peak, rms, skewness, kurtosis, slope, change_rate
- 频域特征：dominant_freq, spectral_centroid, low/mid/high_band_energy + ratio, harmonic_2/3_ratio

**实践代码核心**：
```python
# 时域：RMS = sqrt(mean(x²))，衡量信号能量
rms = float(np.sqrt(np.mean(x**2)))

# 频域：FFT + Hanning窗 → 主频 + 频带能量
spectrum = np.fft.rfft(x * np.hanning(len(x)))
freqs = np.fft.rfftfreq(len(x), d=1.0/sample_rate)
power = np.abs(spectrum)**2
dominant_freq = freqs[np.argmax(power[1:])+1]  # 跳过DC
```

**可视化输出**：时域波形图、FFT频谱图、特征分布箱线图、特征相关性热力图、PCA降维散点图

**面试问答**：
- Q: 为什么用滑动窗口而不是逐帧分类？
  A: 单帧数据没有时序上下文，无法区分"静止"和"走路的某一瞬间"。64点窗口（1.28s）覆盖一个完整动作周期，特征才有统计意义。
- Q: 窗口重叠50%有什么好处？
  A: 增加训练样本数量（约翻倍），同时相邻窗口有重叠数据，推理时过渡更平滑，减少边界误判。
- Q: 时域和频域特征各有什么优势？
  A: 时域特征（RMS、peak_to_peak）反映信号强度和幅度，计算量小；频域特征（dominant_freq、band_energy）反映运动节奏和频率分布，区分 walk/stairs 更有效。两者互补。
- Q: 192维特征会不会太多？
  A: 对 MLP 来说 192 维输入可接受，但部署时可以用特征选择（相关性分析去冗余）或 PCA 降到 30-50 维，减少模型参数。

---

### 环节3：模型设计（Day13）

**原理**：
- 选型：**MLP（多层感知机）**，结构 `Dense(32, ReLU) → Dense(16, ReLU) → Dense(3, Softmax)`
- 为什么不用 CNN/LSTM？
  - CNN 适合空间结构数据（图像），特征已提取为 1D 向量后 MLP 更直接
  - LSTM 串行计算慢、内存大，且时序信息已在滑窗特征中提取
- 参数量：192×32+32 + 32×16+16 + 16×3+3 = 6176+528+51 = **6755 参数**
- INT8 量化后：~6.8KB Flash，TFLM 推理 <5ms

**面试问答**：
- Q: 为什么隐藏层用 32→16 递减？
  A: 递减结构是"信息瓶颈"设计，逐层压缩特征维度，强迫网络学习最本质的判别特征，同时控制参数量。32 和 16 是经过实验平衡精度和体量的选择。
- Q: 为什么用 ReLU 而不是 Sigmoid？
  A: ReLU 计算简单（max(0,x)）、梯度不饱和（避免梯度消失）、INT8 量化友好（零点对齐）。Sigmoid 在深层网络中梯度消失严重。
- Q: Softmax 输出三分类概率，部署时怎么用？
  A: TFLM 输出三个 logits，取 argmax 为预测类别。可加置信度阈值（如>0.7才输出），低于阈值走传统逻辑兜底。

---

### 环节4：模型训练与验证（Day14）

**原理**：
- 数据划分：**分层抽样** 70% 训练 / 15% 验证 / 15% 测试（保证每类比例一致）
- 归一化：Z-Score 标准化 `(x - mean) / std`，**mean/std 只用训练集计算**，部署时必须用同一组参数
- 优化器：Adam（lr=0.003, β1=0.9, β2=0.999）
- 损失函数：交叉熵 `sparse_categorical_crossentropy`
- 早停：patience=20，监控 val_loss，连续 20 轮无改善则停止
- 评估指标：Accuracy + Macro F1 + 混淆矩阵 + Precision/Recall

**实践代码核心**：
```python
# 分层抽样：每类按比例划分 train/val/test
for label_id in np.unique(y):
    indices = np.where(y == label_id)[0]
    rng.shuffle(indices)
    n_train = int(len(indices) * 0.70)
    n_val = int(len(indices) * 0.15)
    train_idx.extend(indices[:n_train])
    val_idx.extend(indices[n_train:n_train+n_val])
    test_idx.extend(indices[n_train+n_val:])

# 归一化：只从训练集计算
scaler_mean = x_train.mean(axis=0)
scaler_std = x_train.std(axis=0)
x_scaled = (x - scaler_mean) / scaler_std

# Keras 模型
model = keras.Sequential([
    keras.layers.Input(shape=(192,)),
    keras.layers.Dense(32, activation="relu"),
    keras.layers.Dense(16, activation="relu"),
    keras.layers.Dense(3, activation="softmax")
])
model.compile(optimizer=Adam(0.003), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
```

**面试问答**：
- Q: 为什么归一化参数只能用训练集？
  A: 如果用全量数据算 mean/std，测试集信息泄漏到训练过程，评估结果虚高。部署时必须用训练时的 mean/std，否则模型输入分布不匹配，推理结果错误。
- Q: EarlyStopping 的 patience=20 怎么选的？
  A: 太小（如5）可能过早停止，模型还没收敛；太大（如50）浪费时间且可能过拟合。20 是经验值，在 100 epoch 内通常能触发 1-2 次改善停滞。
- Q: 为什么看 Macro F1 而不只是 Accuracy？
  A: 三分类如果数据不平衡（如 idle 样本多），Accuracy 会被多数类拉高。Macro F1 对每个类别平等加权，更能反映少数类的识别效果。
- Q: 混淆矩阵怎么看？
  A: 对角线是正确分类，非对角线是误分类。如果 walk→stairs 误判多，说明这两个动作特征重叠大，需要增加区分性特征或加训练数据。

---

### 环节5：模型量化与转换（Day15/Day8）

**原理**：
- **PTQ（后训练量化）**：训练完成后，用校准数据集统计激活值范围，将 FP32 → INT8
- 量化公式：`真实值 = (整数值 - zero_point) × scale`
- 权重量化：直接统计权重的 min/max 计算 scale
- 激活量化：用 100 组代表性数据跑一遍推理，统计每层激活的真实范围
- TFLite 转换：`TFLiteConverter` + `representative_dataset` + `OPTIMIZE_FOR_SIZE`

**实践代码**：
```python
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset  # 100组校准数据
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8   # 输入也量化
converter.inference_output_type = tf.int8  # 输出也量化
quantized_model = converter.convert()
```

**量化效果**：模型体积 FP32 ~27KB → INT8 ~6.8KB（4×压缩），推理速度提升 5-8×

**面试问答**：
- Q: PTQ 和 QAT 的区别？什么时候用 QAT？
  A: PTQ 训练后量化，简单快速但精度损失可能 2-5%。QAT 训练中模拟量化误差，精度损失 <1% 但需改训练代码。先 PTQ 验证，掉点 >2% 才上 QAT。
- Q: 量化后精度掉了怎么办？（5步排查）
  A: ① 查校准集是否覆盖全部工况 → ② 查前后处理一致性（归一化参数匹配）→ ③ PTQ→QAT → ④ 混合精度（敏感层留 FP16）→ ⑤ 调整模型结构
- Q: 为什么必须全 INT8（权重+激活）？
  A: 只量化权重不量化激活，推理时仍需 float 运算，MCU 没有 FPU 或 FPU 慢，性能提升有限。全 INT8 才能完全利用 MCU 整数算力。

---

### 环节6：TFLM 端侧部署（Day5/Day1）

**原理 — TFLM 推理 6 步**：
```cpp
// ① 注册算子（编译期确定，零堆分配）
MicroMutableOpResolver<3> op_resolver;  // FC + ReLU + Softmax
op_resolver.AddFullyConnected();
op_resolver.AddSoftmax();
// ReLU 融合在 FC 里，不需单独注册

// ② 创建解释器
MicroInterpreter interpreter(model, op_resolver, tensor_arena, kTensorArenaSize);

// ③ 分配内存（静态预分配，无 malloc）
interpreter.AllocateTensors();

// ④ 设置输入（INT8 量化后的输入）
interpreter.input(0)->data.int8[0] = quantized_input;

// ⑤ 执行推理
interpreter.Invoke();

// ⑥ 读取输出
int8_t output = interpreter.output(0)->data.int8[0];
```

**关键设计哲学**：
| 设计 | 原因 | 嵌入式类比 |
|------|------|-----------|
| OpResolver\<N\> | 编译期确定算子，只链接用到的 | 条件编译 `#ifdef` |
| tensor_arena | 静态预分配，零堆碎片 | RTOS 任务栈 `uint8_t stack[512]` |
| Invoke() | 拓扑顺序执行，完全确定性 | 状态机顺序执行 |
| FlatBuffer 模型 | 零拷贝、零解析、直接映射内存 | const 数组查表 |

**面试问答**：
- Q: TFLM 为什么不用 malloc？
  A: MCU 无 MMU，malloc 会导致内存碎片，长时间运行后分配失败崩溃。tensor_arena 是一块静态数组，MicroAllocator 在内部管理，零碎片风险。
- Q: tensor_arena 多大？
  A: 取模型中**内存占用最大的一层**的输入+输出张量之和，加 20-30% 余量。MLP 小模型一般 10-20KB。可用 `RecordingMicroInterpreter` 精确测定。
- Q: 如果模型有 Conv2D 但没注册 AddConv2D() 会怎样？
  A: `AllocateTensors()` 阶段报 `kTfLiteError`，输出 `"Didn't find op for builtin opcode 'CONV_2D'"`。不会等到 Invoke() 才崩——这是 TFLM 的"初始化期检查"哲学。

---

### 环节7：系统集成（FreeRTOS + 传感器 + AI 推理）

**三级任务架构**：
```
任务优先级（高→低）：
  ① 传感器采集任务（最高）— 定时器/ADC中断触发，写环形缓冲区
  ② AI推理任务（中）     — 队列接收一帧数据，调用 TFLM Invoke()
  ③ 业务逻辑任务（低）   — 拿结果执行告警/串口上报/继电器控制
同步：队列 + 二值信号量
内存：tensor_arena 静态全局区，任务栈静态分配
```

**面试问答**：
- Q: AI 推理和 FreeRTOS 怎么结合保证实时性？
  A: 三级任务架构——采集最高优先级保证数据不丢；推理中优先级，计算密集型不被低优先级抢占；业务低优先级。推理中不做 malloc/串口打印/阻塞调用。tensor_arena 静态分配避免不确定延迟。
- Q: 推理耗时超标怎么办？
  A: ① 确认全 INT8（有没有算子回退浮点）→ ② 减少模型通道数/层数 → ③ 开 NPU 加速 → ④ 降低推理频次（跳帧）→ ⑤ 剪枝/蒸馏

---

## 三、高频面试问答速查

### A. 量化相关（100%会问）
| 问题 | 一句话答案 |
|------|-----------|
| INT8 量化原理 | FP32→INT8 线性映射，`真实值=(整数-zero_point)×scale` |
| PTQ vs QAT | PTQ 训练后量化快速但精度损失大；QAT 训练中模拟量化精度好但需改代码 |
| 量化掉点排查 | 校准集→前后处理一致性→QAT→混合精度→模型结构 |
| scale/zero_point | scale=浮点范围/255，zero_point=浮点0对应的整数 |

### B. TFLM 相关（90%会问）
| 问题 | 一句话答案 |
|------|-----------|
| tensor_arena | 静态预分配内存池，所有张量从中分配，零堆碎片 |
| OpResolver | 算子注册表，编译期确定，只链接用到的算子 |
| Invoke() | 按拓扑顺序逐个调用算子，完全确定性执行 |
| 模型格式 | FlatBuffer，零拷贝零解析，直接内存映射 |

### C. 模型设计相关（80%会问）
| 问题 | 一句话答案 |
|------|-----------|
| 为什么用 MLP 不用 CNN | 特征已提取为 1D 向量，MLP 更直接且参数少 |
| 为什么用 ReLU | 计算简单、梯度不饱和、量化友好 |
| 参数量估算 | FC: in×out+out；Conv: Cin×Cout×K×K+Cout |
| 能不能放进 MCU | Flash<50% ∧ SRAM<80% ∧ 延迟达标 ∧ 算子全支持 |

### D. 数据相关（70%会问）
| 问题 | 一句话答案 |
|------|-----------|
| 滑动窗口 | 64点(1.28s)覆盖一个动作周期，50%重叠增加样本 |
| 时域 vs 频域 | 时域反映强度(RMS)，频域反映节奏(dominant_freq)，互补 |
| 归一化 | Z-Score 只用训练集 mean/std，部署时必须一致 |
| 数据不平衡 | 分层抽样 + Macro F1 评估 + 数据增强 |

---

## 四、项目经验话术（简历包装+自我介绍）

### 简历项目描述（直接可用）
```
基于 STM32N647 + QMI8658A 的端侧人体动作识别系统  2026.05-2026.07
- 独立完成全链路：数据采集(50Hz六轴IMU) → 特征提取(192维时频特征) → 
  模型设计(MLP 6755参数) → 训练验证(Keras+EarlyStopping) → 
  INT8量化(4×压缩) → TFLM端侧部署
- 关键指标：模型 6.8KB(INT8)、单帧推理 <5ms、测试准确率 92%+、Macro F1 0.90+
- 技术亮点：tensor_arena 静态内存管理、FreeRTOS 三级任务调度、
  全 INT8 量化推理、输入侧边界钳位兜底
```

### 自我介绍模板（30秒版）
> 我有8年工业嵌入式经验（驱动/RTOS/TSN），最近完成了基于 STM32 的端侧 AI 项目——从 IMU 数据采集到 TFLM 部署的全链路。我的定位是**懂AI的嵌入式落地工程师**，核心价值是把 AI 模型真正放进 MCU、满足实时性和可靠性要求、能稳定跑在现场。

### 和纯算法工程师的差异化
> 纯算法工程师做的是实验室 Demo，我做的是能量产的落地方案——懂硬件约束（Flash/SRAM/NPU）、懂实时性（FreeRTOS 任务调度）、懂现场可靠性（EMC抗干扰、边界兜底），一个人打通从模型到固件的全链路。

---

## 五、容易追问的深度问题

### Q1: 神经网络在训练范围外输出错乱怎么办？
**核心**：神经网络是"分段插值器"，天生不具备外推能力。
**工程方案**：
1. 训练数据覆盖全部工作范围（含边界/异常工况）
2. 输入侧判断：超范围数据不走 AI 模型，走传统阈值逻辑
3. 输出侧钳位：限制输出在合理物理范围
4. 输出层去掉激活函数，保留线性趋势

### Q2: 工业现场电磁干扰怎么保证 AI 鲁棒性？
**四层防御**：
1. 硬件：EMC 滤波 + 信号隔离 + PCB 屏蔽
2. 数据：训练加噪声增强 + 部署时前置校验过滤
3. 模型：MAE/Huber 损失替代 MSE + 1D CNN 抓局部特征
4. 部署：结果防抖（连续3次异常才告警）+ 传统阈值双重校验

### Q3: 工业时序为什么用 1D CNN 不用 LSTM？
1. NPU 加速：1D CNN 并行计算 10× 快于 LSTM 串行
2. 内存：CNN 张量可复用缓冲区，LSTM 需保存隐藏状态
3. 精度：短窗口（100-200点）CNN 抓局部突变更精准，LSTM 长序列优势发挥不出

### Q4: 传统阈值算法 vs AI 算法，什么时候必须用 AI？
- 传统阈值：规则人写死，只处理简单/线性/已知模式
- AI：规则从数据学，能处理复杂/非线性/多特征耦合
- **必须用 AI 的三类场景**：复杂故障特征（轴承早期故障）、多特征耦合（电流+电压+温度）、早期预警（劣化趋势识别）

---

## 六、课程知识地图（面试前速览）

```
Day1  TFLM 6步推理 → OpResolver → tensor_arena → hello_world sin(x)
Day5  TFLM核心结构 → MicroInterpreter → MicroAllocator → FlatBuffer
Day8  模型训练与量化 → PTQ/QAT → scale/zero_point → 校准集
Day11 数据采集与清洗 → IMU六轴 → 50Hz采样 → invalid/clipped过滤
Day12 特征提取 → 滑窗64/32 → 时域11+频域13 → FFT → 192维
Day13 模型设计 → MLP Dense32+16+Softmax → 6755参数 → ReLU
Day14 训练验证 → Adam+交叉熵 → EarlyStopping → 混淆矩阵 → Macro F1
Day15 量化转换 → TFLiteConverter → INT8 → 6.8KB → 部署
```

---

## 关联

- [[week01-day01-tflm-hello-world]] — Day1 详细笔记（825行，含 TFLM 源码深度分析 + 17道面试题）
- [[../3-month-mastery-plan]] — 3个月学习计划
- 原始课程材料：本目录下 Day5/8/11-15 的 PPT/PDF/Python 文件

---

**创建日期**: 2026-07-09
**覆盖范围**: Day1/5/8/11-15 全部课程 + TFLM 源码 + 8年工业嵌入式经验
**使用方式**: 面试前通读 → 重点记每环节的"面试问答" → 简历项目描述直接复用
