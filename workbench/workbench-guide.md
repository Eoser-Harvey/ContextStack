# ContextStack 工作台使用指南
> 如何使用工作台系统实现会话持久化和话题切换？

## 概述

工作台系统使AI助手能通过持久化存储跨会话保持上下文，并在不同话题/项目之间快速切换。

## 快速开始

### 1. 创建新工作台

从模板复制：
- 项目工作台：`templates/project-template.md`
- 话题工作台：`templates/topic-template.md`
- 任务工作台：`templates/task-template.md`

### 2. 使用工作台
- **更新当前状态**：编辑工作台文件
- **跟踪进度**：更新任务列表和状态
- **记录决策**：添加笔记和理由
- **保存会话**：复制到 history/ 目录

### 3. 切换工作台

1. 保存当前工作台：`Save [Current] workbench`
2. 加载新工作台：`Switch to [New Topic]`
3. 更新上下文：AI加载新工作台状态

## 工作台结构

### 项目工作台

```markdown
## 项目信息
- 项目名称：
- 项目状态：
- 负责人： 
- 创建时间：
- 最后更新： 
- 当前状态： 

## 项目目标
项目的主要目标是什么？

## 任务列表
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3

## 进度跟踪
跟踪任务完成情况和状态

## 资源
文档、工具和链接

## 切换命令
- Switch to [项目名称]
- Save [项目名称] workbench
- Restore [项目名称] workbench
- End session

## 版本控制
- 当前版本：v1.0
- 版本历史：
  - v1.0 (YYYY-MM-DD)：初始版本
```

### 话题工作台

```markdown
## 话题信息
- 话题名称：
- 创建时间：
- 最后更新： 
- 当前状态： Active/Saved/Closed

## 话题目标
主要的讨论目标是什么？

## 讨论记录
记录重要讨论

## 结论
记录结论和决定

## 切换命令
- Switch to [话题名称]
- Save [话题名称] workbench
- End topic

## 版本控制
- 当前版本：v1.0
- 版本历史：
  - v1.0 (YYYY-MM-DD)：初始版本
```

## 最佳实践

### 1. 切换前始终保存
切换到新项目前，始终保存当前工作台状态。

### 2. 保持版本控制
使用版本号和更新历史跟踪变更。

### 3. 定期更新
定期更新工作台，记录进度和决定。

### 4. 使用会话历史
将重要会话保存到 history/ 目录。

### 5. 定期清理
归档已完成的话题/项目，保持工作台整洁。

## 常用命令

### 切换
- `Switch to [项目名称]`
- `Switch to embedded-ai-learning`

### 保存
- `Save [项目名称] workbench`
- `Save embedded-ai-learning workbench`

### 恢复
- `Restore [项目名称] workbench`
- `Restore embedded-ai-learning workbench`

### 结束
- `End session`

## 故障排除

### 工作台未找到
- 查看工作台文件是否存在
- 验证工作台名称是否正确

### 上下文未加载
- 查看工作台文件格式是否正确
- 验证工作台文件是否损坏

### 版本冲突
- 比较版本历史
- 如果需要，手动合并变更

## 示例

### 示例1：创建项目工作台

1. 复制 `templates/project-template.md` 到 `projects/我的项目.md`
2. 填写项目信息
3. 添加项目目标和任务
4. 开始跟踪

### 示例2：切换话题

1. 当前话题：`TSN-protocol-analysis`
2. 命令：`Save TSN-protocol-analysis workbench`
3. 命令：`Switch to embedded-ai-learning`
4. AI加载嵌入式AI学习上下文

### 示例3：结束会话

1. 命令：`Save [当前工作台] workbench`
2. 将会话复制到 `history/[时间戳].md`
3. 命令：`End session`

## 高级功能

### 自动上下文加载

切换到工作台时，AI自动加载：
- 全局规则：`D:\MyFile\AI\ContextStack\GLOBAL-RULES.md`
- 项目规则：`{项目路径}/PROJECT-RULES.md`（如果存在）
- 相关文档：来自 Obsidian/system/
- 记忆索引：`D:\MyFile\AI\ContextStack\MEMORY.md`

### 紧急情况

上下文冲突时：
1. 全局规则 > 项目规则 > 规范文档
2. 安全红线始终优先
3. 不确定时询问用户

工作台状态不一致时：
1. 工作台文件优先
2. 记忆仅为索引
3. 会话历史为参考

## 相关资源

- 工作台README：`workbench/README.md`
- 全局规则：`D:\MyFile\AI\ContextStack\GLOBAL-RULES.md`
- 交互协议：`D:\MyFile\AI\ContextStack\ContextStack协作架构-交互协议.md`

---

**最后更新**: 2026-04-30  
**版本**：v1.1  
**变更**：将目录重命名为英文名称以提高工具兼容性
