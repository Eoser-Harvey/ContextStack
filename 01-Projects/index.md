# 项目工作台

所有项目按独立子目录管理，每个项目包含标准化文件结构。

## 活跃项目

| 项目              | 状态     | 入口                                          |
|:------------------|:---------|:----------------------------------------------|
| [嵌入式AI学习](./embedded-ai-learning/)       | 学习阶段 | [WORKSPACE.md](./embedded-ai-learning/WORKSPACE.md)   |
| [网络设备调试](./network-device-debug/)        | 进行中   | [WORKSPACE.md](./network-device-debug/WORKSPACE.md)    |
| [腾讯云AI编程培训](./tencent-cloud-training/)  | 资料整理 | [WORKSPACE.md](./tencent-cloud-training/WORKSPACE.md) |
| [BTC温度仪表盘](./btc-temperature-gauge/)      | 基础完成 | [WORKSPACE.md](./btc-temperature-gauge/WORKSPACE.md) |
| [WeChat Radar](./wechat-radar/)                | 环境就绪 | [WORKSPACE.md](./wechat-radar/WORKSPACE.md)           |
| [家庭决策枢纽](./family-hub/)                  | 进行中（最活跃） | [WORKSPACE.md](./family-hub/WORKSPACE.md)             |
| [自动化任务实验](./automated-task/)            | 活跃     | [README-自动推送任务.md](./automated-task/README-自动推送任务.md) |
| [个人网站](./personal-website/)                | 活跃     | [index.html](./personal-website/index.html) |
| [个性化Agent](./personal-agents/)              | 待规划   | [index.md](./personal-agents/index.md) |
| [话题工作台](./topics/)                         | 活跃     | [index.md](./topics/index.md) |

> 注：求职面试归档位于 `02-Knowledge/career-development/`，不在本目录。

## 项目标准文件结构

每个项目至少包含以下文件：

| 文件               | 用途                           |
|:-------------------|:-------------------------------|
| **WORKSPACE.md**   | 工作台入口、项目信息、导航       |
| **STATE.md**       | 最新状态与进展 (✅⚠️📌❓)         |
| **ACTIONS.md**     | 任务清单与进度追踪               |
| **CONTEXT.md**     | 稳定背景、共识决策、前提约束       |
| **REFERENCES.md**  | 内部文档与外部资源链接            |
| **PROJECT-RULES.md** | 项目规则与行为约束             |

## 模板

新项目从 `04-Templates/project/` 复制标准文件模板。

## 任务型目录说明

- [topics/](./topics/) — 跨项目技术话题讨论暂存（PBR策略路由分析、TSN协议分析）
- [automated-task/](./automated-task/) — 自动化定时任务（飞书推送/TFLM日报/公司运营日报/推特抓取/AI三线卖出监控）
- [personal-agents/](./personal-agents/) — 个性化 Agent 开发待规划（李笑来认知蒸馏/健康 Agent）
- [personal-website/](./personal-website/) — 静态个人站点，文章发布与一键部署脚本

> 以上四类为任务/工具型目录，与上方"活跃项目"（标准六文件结构）不同，按需维护。

---

**最后更新**: 2026-08-20
