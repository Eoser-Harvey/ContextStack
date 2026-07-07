---
title: CodeBuddy 编辑器多标签修复
created: 2026-07-06
tags:
  - CodeBuddy
  - 编辑器配置
  - 多标签
  - Troubleshooting
---

# CodeBuddy 编辑器多标签修复

## 问题

CodeBuddy 默认行为：**打开新文件时，自动关闭上一个文件的页签**。无法同时保留多个打开的 Markdown 文件页签供切换。

## 根因诊断

1. **工作区 `.vscode/settings.json` 无效**：在项目根目录设置 `"workbench.editor.enablePreview": false` 无效，CodeBuddy 的编辑器内核**不读取工作区级别的这些开关**。
2. **JSON 注释导致解析失败**（已排除）：`//` 注释在 VS Code 中合法（JSONC），但某些解析器拒绝 → 导致整个文件被静默忽略。最终改为纯 JSON 排除此怀疑。
3. **真正生效位置：用户级全局配置** → `C:\Users\<用户名>\AppData\Roaming\CodeBuddy CN\User\settings.json`。

## 解决方案

在用户级全局配置 `CodeBuddy CN/User/settings.json` 中添加以下三项：

```json
"workbench.editor.enablePreview": false,
"workbench.editor.enablePreviewFromQuickOpen": false,
"workbench.editor.showTabs": "multiple"
```

| 设置 | 作用 |
|------|------|
| `enablePreview: false` | 单击文件打开**永久页签**（不再替换上一个） |
| `enablePreviewFromQuickOpen: false` | Ctrl+P 快速打开也开永久页签 |
| `showTabs: "multiple"` | 允许多个标签同时显示 |

设置后 **`Ctrl+Shift+P` → `Reload Window`** 重载生效。

## 关键教训

- **CodeBuddy ≠ VS Code**：编辑器行为设置的生效级别不同。工作区 `.vscode/settings.json` 中的 `workbench.editor.*` 相关设置被 CodeBuddy 内核忽略，必须写到**用户级全局配置**才生效。
- **工作区 `.vscode/settings.json`** 仍保留这些设置作为**参考文档**（纯 JSON，无注释），方便以后迁移到其他编辑器。
- 其他 VS Code 常规设置（`editor.fontSize`、`workbench.colorTheme` 等）是否受同样限制尚待验证。建议后续遇到类似「改工作区不生效」问题时，优先尝试用户级配置。
