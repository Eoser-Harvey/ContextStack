# ContextStack 四层架构框架（精简指针）

> **本文件已精简为指针**：四层架构的完整定义、层间交互协议、工作台系统、CEO 协作模式、文件组织规范，均以 `FRAMEWORK-README.md`（框架根目录）为**唯一文档权威**。
> 此处仅保留速览，避免与 `FRAMEWORK-README.md` 内容重复漂移。

## 一图速览
- **L1 全局规则** `GLOBAL-RULES.md`：定义「我是谁」——角色/沟通风格/铁律/红线/授权；启动常驻、最高优先级、不可覆盖
- **L2 项目规则** `PROJECT-RULES.md`：定义「哪个项目」——规范/领域/目录/红线；切换工作台时动态加载，受 L1 约束
- **L3 规范文档** `02-Knowledge/system/`：定义「如何做」——方法论/SOP/模板；按需读取，不常驻
- **L4 持久 Memory** `MEMORY.md` + `03-Memory/`：记录「在做什么」——user/feedback/project/reference；持续更新、跨 session

## 冲突优先级
全局规则 > 项目规则 > 规范文档；安全红线始终优先。

## 协作模式
用户(Boss) > AI(CEO) > 执行任务。

> 完整内容见 `FRAMEWORK-README.md`；本文件不再维护副本。
