# 嵌入式AI学习 — 状态追踪

> 仅记录最新动态，稳定背景信息放在 CONTEXT.md

---

## 2026-07-24

### 📌 Week 3 课程材料已建（待学习）
- 课程文件 `courses/week03-data-training-cnn.md`（~830 行，v1.0）
- 内容覆盖：CNN 三算子源码剖析（conv/pooling/softmax）、数据预处理与归一化、数据增强（图像 5 件套 + 工业时序特有）、训练三件套（LR调度/EarlyStopping/Dropout）、SGD vs Adam、CIFAR-10 完整训练模板
- 含 4 道思考题 + 2 道扩展思考题（ESP32-S3 容量检验 / 1D CNN 深度选型）+ TFLM 部署准备 Checklist
- Week 4 衔接预告：INT8 量化 + 剪枝 + 蒸馏 + ESP32-S3 全链路部署
- ⚠️ **Rule 4 触发**：项目状态变更，已同步更新 STATE / MEMORY.md / ACTIONS / index.md

---

## 2026-07-22

### ✅ Week 1 完成 + 🔄 Week 2 已排
- Week 1（TFLM 四组件架构 + hello_world 源码剖析）已完成；课程文件 `week01-day01-tflm-hello-world.md` 状态→已完成，AI 助教考核 ≈7/10
- 思考题（4 题）+ 任务 1-3 参考版已补全，文件自洽；关键认知：层=算子、推理=for 循环乘加、OpResolver 缺算子报 `Didn't find op`、arena 静态分配
- Week 2 文档已建：`courses/week02-model-conversion-pytorch.md`（PyTorch→ONNX→TFLite→TFLM 全链路 + Netron，含理论/代码/习题/面试/补充）
- 下一步：执行 Week 2（自训 sin 模型→转换→Netron→跑通 TFLM）

---

## 2026-07-21

### 🔄 重启（响应"不能停滞不前"）
- 现状：自 6/24 完成损失函数后，一个月零更新；TFLM 核心架构（四组件）尚未真正读源码
- 决策：回到 Month 1 主线，按"两周落地节奏"推进，并注入"边学边发"新方向
- 两周节奏（带日期+发文）已归档至 `3-month-mastery-plan.md` 的「🗓️ 两周落地节奏」章节

### 📌 下一步
- Week 1 补完：TFLM 四组件架构 + hello_world 源码剖析（Day 2-5）
- Week 2：PyTorch 训 MNIST → 转换 .pth→.onnx→.tflite → 集成 TFLM 跑通
- 每周产出 1 篇一手实战文（公众号/掘金）
- ⚠️ 修正：ACTIONS 中 1.1「理解TFLM核心架构」原标 ✅，实际仅完成基本概念，已改回 🔄进行中

---

## 2026-06-24

### ✅ 已完成
- 学习损失函数：核心定义（量化差距）、三大作用（量化/引导/偏向）、训练闭环五步
- 掌握嵌入式AI场景损失函数选型：分类用BCE/Sparse CE，回归用MSE/MAE/Huber
- 归档豆包学习记录到 `knowledge/loss-function-embedded-ai.md`

### 📌 下一步
- 理论学习：TFLM 核心架构（模型加载、Arena分配、算子注册）
- 理论学习：内存管理机制

---

## 2026-05-11

### ✅ 已完成
- 理解 TFLM 基本概念（什么是 TFLM、为什么需要它）
- 创建详细学习计划和阶段划分
- 确定学习模式：TFLM 主线、PyTorch/DL 辅线

### ⚠️ 阻塞点
- 暂无

### 📌 下一步
- 理论学习：TFLM 核心架构
- 理论学习：内存管理机制
- 理论学习：算子实现

### ❓ 待确认
- 暂无