# 项目工作台

此目录包含所有项目工作台。

## 项目列表

### 活跃项目

#### 1. 嵌入式AI学习 (Embedded AI Learning)
- **路径**：`embedded-ai-learning/`
- **状态**：活跃
- **描述**：学习TensorFlow Lite Micro (TFLM)进行嵌入式AI开发
- **关键文件**：
  - `embedded-ai-learning.md` - 主项目工作台
  - `3-month-mastery-plan.md` - 3个月精通学习计划
  - `3-month-mastery-plan-v1.0-20260429.md` - 历史版本
- **相关**：TFLM项目位于 `D:\MyFile\AI\TFLM\tflite-micro-main\tflite-micro-main`

#### 2. 网络设备调试 (Network Device Debugging)
- **路径**：`network-device-debug/`
- **状态**：活跃
- **描述**：网络设备调试问题和解决方案集合
- **关键文件**：
  - `network-device-debug.md` - 项目概述
  - `IE4120U-18TP-issue.md` - IE4120U-18TP终端问题
- **相关设备**：
  - IE4120U-18TP (18端口工业交换机)
  - IE4300U-10P (10端口工业交换机)
  - IE4500 (工业交换机)

### 待处理项目
#### 3. 腾讯云培训 (Tencent Cloud Training)
- **路径**：`tencent-cloud-training/`
- **状态**：待迁移
- **描述**：腾讯云AI编程培训材料
- **内容**：演示图片和材料

## 项目切换

### 命令
- `Switch to embedded-ai-learning` - 切换到嵌入式AI学习项目
- `Switch to network-device-debug` - 切换到网络设备调试项目
- `Switch to network-device-debug/IE4120U-18TP-issue` - 切换到特定问题

### 自动上下文加载
切换到项目时，自动加载以下上下文：
- **全局规则**：`D:\MyFile\AI\ContextStack\GLOBAL-RULES.md`
- **项目规则**：`{项目路径}/PROJECT-RULES.md`（如果存在）
- **相关文档**：来自 Obsidian/system/
- **记忆索引**：`D:\MyFile\AI\ContextStack\MEMORY.md`

## 项目结构模板

每个项目应遵循以下结构：
```
项目名称/
├─ 项目名称.md              # 主项目工作台
├─ 项目计划.md              # 项目计划（适用时）
├─ 项目计划-vX.X-YYYYMMDD.md # 历史版本
├─ issues/                      # 特定工作台（可选）
│  ├─ issue-1.md
│  └─ issue-2.md
└─ resources/                   # 项目资源（可选）
    ├─ documentation/
    ├─ tools/
    └─ references/
```

## 版本控制

所有项目文件应包含：
- **版本号**（例如 v1.0, v1.1）
- **版本历史**，包含日期和变更
- **最后更新**时间

### 版本编号
- **v1.0**：初始版本
- **v1.x**：小更新，改进
- **v2.0**：大更新，结构变更

## 命名约定

### 文件名
- 使用小写字母、数字和连字符
- 用连字符替换空格
- 使用描述性名称
- 示例：`embedded-ai-learning.md`, `3-month-mastery-plan.md`

### 目录名
- 使用小写字母、数字和连字符
- 用连字符替换空格
- 使用描述性名称
- 示例：`embedded-ai-learning`, `network-device-debug`

## 最佳实践
1. **切换前始终保存**：切换项目前保存当前工作台状态
2. **保持版本历史**：为所有重要文件维护版本控制
3. **使用模板**：从模板创建新项目
4. **定期更新**：定期更新项目状态和进度
5. **记录决策**：记录重要决策及其理由

## 相关资源

- **工作台README**：`../README.md`
- **全局规则**：`D:\MyFile\AI\ContextStack\GLOBAL-RULES.md`
- **记忆索引**：`D:\MyFile\AI\ContextStack\MEMORY.md`

## 迁移说明

此目录于2026-04-30从中文名称迁移到英文名称，以提高工具兼容性。
**旧结构**：
- `工作台/项目/嵌入式AI学习/` → `projects/embedded-ai-learning/`
- `工作台/项目/网络设备调试/` → `projects/network-device-debug/`

更多详情，参见 `D:\MyFile\AI\ContextStack\directory-migration-log.md`。

---

**最后更新**: 2026-04-30  
**版本**：v1.0  
**迁移状态**：进行中（约7%完成）
