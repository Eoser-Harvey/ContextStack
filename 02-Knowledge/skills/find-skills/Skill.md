---
name: find-skills
description: |
  帮助用户从开放的 Agent Skills 生态（skills.sh）中发现和安装第三方 Skill。
  支持关键词模糊搜索数千个社区 Skill（前端、后端、DevOps、测试等），
  列出任意 Git 仓库中托管的 Skill，并安装到目标 Agent 中。
  提供可复现的 Git 安装、Agent 作用域控制和快速发现能力。
---

# Find Skills - 技能发现与安装工具

## 简介

Find Skills 帮助你快速定位和安装适合当前任务的 Skill，支持：

- 从已安装的 Skill 集合中检索和推荐最匹配的 Skill
- 根据任务描述推荐单个 Skill 或 Skill 组合链
- 列出所有已安装的 Skill，按类别分组展示

## 使用方式

### 1. 根据任务查找 Skill

```
我需要完成以下任务：[任务描述]

请从已安装的 skill 中帮我推荐：
- 最适合的单个 skill
- 如果需要组合使用，建议调用顺序
- 每个推荐的理由
```

### 2. 列出所有已安装的 Skill

```
列出当前已安装的所有 skill，按类别分组，注明每个 skill 的核心能力和典型使用场景。
```

## 当前项目已安装的 Skills

| 技能名称 | 核心能力 | 典型场景 |
|---------|---------|---------|
| **brainstorming** | 前置设计与需求分析 | 新功能开发、技术选型、项目规划 |
| **device-debugging** | 设备调试指南 | 硬件设备问题排查 |
| **karpathy-guidelines** | 简洁编码准则 | 代码编写、重构约束 |
| **network-packet-analysis** | 网络报文分析 | 网络问题排查、协议分析 |
| **pua-governance** | 高能动性治理 | 突破反复失败僵局、高质量交付 |
| **systematic-debugging** | 系统化调试 | Bug 根因分析、多组件故障定位 |
| **tsn-protocol** | TSN 协议分析 | TSN 网络问题排查 |
| **vscode-config-management** | VSCode 配置管理 | IDE 配置优化 |
| **writing-plans** | 实施计划生成 | 设计文档转可执行步骤 |

## 搜索推荐逻辑

根据任务类型自动匹配：

| 任务类型 | 推荐 Skill |
|---------|-----------|
| 新项目/新功能 | brainstorming → writing-plans |
| 调试/排错 | systematic-debugging → (可选) pua-governance |
| 代码编写/重构 | karpathy-guidelines |
| 网络问题 | network-packet-analysis |
| TSN 协议相关 | tsn-protocol |
| 设备调试 | device-debugging |
| IDE 配置 | vscode-config-management |
