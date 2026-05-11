# ContextStack 工作台系统
> 通过工作台实现会话持久化和话题切换

## 概述

工作台系统是ContextStack协作架构的重要组成部分，能实现跨会话的上下文持久化和不同话题/项目之间的快速切换。

### 与四层架构的关系
工作台系统是四层架构的执行层，连接全局规则、项目规则、规范文档和持久化记忆，实现会话持久化和话题切换。

```
全局规则（常驻） <-> 项目规则（动态）
        ↓                      ↓
规范文档（按需加载）<-> 记忆（持续更新）
        ↓                      ↓
    工作台系统（会话持久化）
```

## 目录结构

```
workbench/
├─ README.md                    # 工作台系统说明
├─ workbench-guide.md          # 工作台使用指南
├─ templates/                  # 工作台模板
  ├─ project-template.md     # 项目工作台模板
  ├─ topic-template.md      # 话题工作台模板
  └─ task-template.md        # 任务工作台模板
├─ topics/                     # 话题工作台
  ├─ TSN-protocol-analysis.md
  ├─ code-review.md
  ├─ doc-organization.md
  └─ network-debug.md
├─ projects/                   # 项目工作台
  ├─ README.md
  ├─ embedded-ai-learning/   # 嵌入式AI学习项目
  ├─ network-device-debug/   # 网络设备调试项目
  └─ tencent-cloud-training/ # 腾讯云培训计划
└─ history/                    # 会话历史记录
    ├─ [时间戳]_[话题/项目].md
    └─ ...
```

## 工作台类型

### 项目工作台
- **目的**：跟踪长期项目
- **内容**：项目信息、任务、交付物、资源
- **示例**：`embedded-ai-learning.md`

### 话题工作台
- **目的**：跟踪特定话题
- **内容**：话题目标、讨论记录、参考资料、结论
- **示例**：`TSN-protocol-analysis.md`

### 任务工作台
- **目的**：跟踪具体任务执行
- **内容**：任务情况、进度、结果、下一步
- **示例**：`task-001.md`

## 切换命令

### 切换到项目
- `切换到[项目名称]` / `Switch to [Project Name]`
- `Switch to [Project Name]`

### 切换到话题
- `切换到[话题名称]` / `Switch to [Topic Name]`
- `Switch to [Topic Name]`

### 保存工作台
- `暂存[工作台名称]工作台` / `Save [Workbench Name] workbench`
- `Save [Workbench Name] workbench`

### 恢复工作台
- `恢复[工作台名称]工作台` / `Restore [Workbench Name] workbench`
- `Restore [Workbench Name] workbench`

### 结束会话
- `结束会话` → End session
- `End session`

## 相关资源

- 全局规则：`D:\MyFile\AI\ContextStack\GLOBAL-RULES.md`
- 记忆索引：`D:\MyFile\AI\ContextStack\MEMORY.md`
- 架构文档：`D:\MyFile\AI\ContextStack\ContextStack协作架构.md`
- 实施计划：`D:\MyFile\AI\ContextStack\ContextStack协作架构-落地计划.md`
- 交互协议：`D:\MyFile\AI\ContextStack\ContextStack协作架构-交互协议.md`

## 最佳实践
1. **切换前始终保存工作台**：使用 `Save [Workbench Name] workbench`
2. **更新版本控制**：在工作台中记录版本变化
3. **保持会话历史**：将重要会话保存到 history/ 目录
4. **使用模板**：从模板创建新工作台
5. **定期清理**：归档已完成的话题/项目

## 注意事项

- 工作台文件采用 Markdown 格式
- 每个工作台都有版本字段
- 使用一致的命名约定
- 定期备份重要工作台

---

**最后更新**: 2026-05-08  
**版本**：v1.1  
**变更**：修复编码乱码，将目录重命名为英文名称以提高工具兼容性
