# 端侧 AI Week 1-2 执行清单（训练端）

> 目标（2 周末达成）：训出 1D CNN 异常检测模型 → INT8 量化 → 转 C 数组（model.h），并能一句话答「数据怎么标注」
> 配套：[[./edge-ai-job-track-plan|端侧 AI 主线规划]]
> 每天 1h + 周末 3h，卡超 3 天就问

---

## Day 0：环境（1-2h，一次到位）

```
Miniconda → 建环境 → 装：pytorch、numpy、matplotlib、pandas、tensorflow(转换用)、onnx、netron
验证：python -c "import torch; print(torch.__version__)"
```

---

## 数据集（三选一，推荐第 1 个）

| 数据集 | 说明 | 推荐度 |
|:--|:--|:--|
| **CWRU 轴承数据集**（凯斯西储大学） | 轴承振动时序，标签清晰（正常/内圈/外圈/滚动体故障），1D CNN 故障分类最成熟的公开集 | ⭐首选，现成标注好 |
| IMS / NASA 轴承数据集（辛辛那提） | 轴承全寿命振动，适合异常/退化检测 | 备选 |
| 自己模拟电流信号 | 用你电力背景造「正常 + 谐波异常」电流波形 | 进阶（差异化最强但要自己造，先别） |

> 第一版先用 CWRU 跑通全流程，别一上来就自己造数据——**先跑通，再差异化**。

---

## ⭐ 滑窗标注方法（这是回答千寻「数据怎么标注」的关键）

时序信号没有现成图片标签，**标注 = 滑窗切片 + 按段给标签**：

```
原始长时序信号（如 12000 点/段，一类故障一段）
  │
  ├─ 滑窗切片：窗口 = 1024 点，步长 = 512（50% 重叠）
  │     → 每片成为一个「样本」(1, 1024)
  │
  ├─ 标签：该片来自哪一类信号，就标哪一类
  │     例：来自「内圈故障」段的所有切片 → 标签 1
  │
  └─ 归一化：每个通道做 z-score（减均值除标准差），或 min-max 到 [-1,1]
        → 消除量纲，让模型学「形状」而非「幅值」
```

**面试话术**：「时序信号的标注不是一张张打，是先把长信号用滑窗切成固定长度的样本，每个样本继承它所属信号段的类别标签；再做归一化消除量纲。我还会用数据增强（加噪/平移）扩充样本。」——这一句话就回答了千寻。

---

## 每天任务（Day 1-14）

| 天 | 做什么 | 产出 |
|:--|:--|:--|
| 1-2 | 下载 CWRU，写数据加载 + 滑窗切片 + 归一化，画 3 段信号对比（正常 vs 故障） | 数据管线 .py，可视化图 |
| 3-4 | 搭 1D CNN（代码骨架见下），训练，画 loss/acc 曲线 | 能训练的模型 |
| 5-6 | 调参（lr/epoch/batch）到验证集精度 >90%，Netron 看结构 | 精度 >90% 的 .pth |
| 7 | **阶段自检**：能讲「滑窗标注 + 1D CNN 各层作用」 | 能口述 |
| 8-9 | INT8 PTQ 量化（representative_dataset 校准），对比量化前后精度 | model_int8.tflite |
| 10-11 | tflite → C 数组（xxd -i），生成 model.h；记录模型大小 | model.h + 大小数据 |
| 12-14 | 整理训练/量化笔记；预研 TFLM 集成接口（DebugLog/MicroPrintf/arena），为 Week 3-4 部署铺路 | 笔记 + 接口清单 |

---

## 代码骨架 1：1D CNN 训练（PyTorch）

```python
import torch
import torch.nn as nn

class CNN1D(nn.Module):
    def __init__(self, num_classes=4):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool1d(2),   # 1024→512
            nn.Conv1d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool1d(2),  # 512→256
            nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),                                       # 256→1
        )
        self.classifier = nn.Linear(64, num_classes)

    def forward(self, x):           # x: (B, 1, 1024)
        x = self.features(x).squeeze(-1)   # (B, 64)
        return self.classifier(x)

# 训练循环（要点）：
# model = CNN1D(num_classes=4)
# opt = torch.optim.Adam(model.parameters(), lr=1e-3)
# loss_fn = nn.CrossEntropyLoss()          # 多分类用稀疏交叉熵
# for epoch in range(30):
#     for xb, yb in train_loader:           # xb:(B,1,1024), yb:(B,)
#         opt.zero_grad(); loss = loss_fn(model(xb), yb)
#         loss.backward(); opt.step()
# 每 epoch 在验证集算 accuracy，保存最优 .pth
```

## 代码骨架 2：INT8 PTQ 量化（TFLite）

```python
import tensorflow as tf, numpy as np
# 先把 .pth 转 SavedModel 或 ONNX 再转（Week 2 已学的转换链）
converter = tf.lite.TFLiteConverter.from_saved_model('saved_model')
converter.optimizations = [tf.lite.Optimize.DEFAULT]

def representative_dataset():                 # 校准集：用训练集采样 100-200 条
    for i in range(200):
        yield [X_train[i:i+1].astype(np.float32)]

converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
tflite_model = converter.convert()
open('model_int8.tflite', 'wb').write(tflite_model)
# 对比：FP32 vs INT8 的模型大小、精度损失
```

## 代码骨架 3：转 C 数组

```bash
xxd -i model_int8.tflite > model_data.cc      # 生成 C 数组
# 或 python 生成 model.h：
#   data = open('model_int8.tflite','rb').read()
#   写成 const unsigned char model_tflite[] = {...}; const int model_tflite_len = ...;
```

---

## Week 2 末完成标准（自检，全过才算完）

- [ ] 能一句话答「数据怎么标注」（滑窗切片 + 继承标签 + 归一化 + 增强）
- [ ] 1D CNN 在 CWRU 验证集精度 >90%
- [ ] 能画出并讲清 1D CNN 三层各做什么（卷积=滤波器提特征、池化=降采样、全连接=分类）
- [ ] INT8 量化后精度损失 <2%，模型缩小 ~4 倍
- [ ] 有 model.h（C 数组）+ 模型大小数据
- [ ] 训练/量化笔记整理完，能当面试素材

**达标后进入 Week 3-4（TFLM 部署到 F407）。不达标就在对应天重学，别带病推进。**

---

**最后更新**: 2026-09-24
