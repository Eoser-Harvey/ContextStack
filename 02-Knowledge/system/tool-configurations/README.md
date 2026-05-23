---
title: VSCode 全局配置备份
tags:
  - tool-config
  - vscode
  - backup
summary: VSCode全局配置文件备份与同步方案，支持自动监控、历史版本管理和一键恢复
created: 2026-04-27
updated: 2026-05-07
---

# VSCode 全局配置备份

## 说明

此目录用于备份VSCode的全局配置文件，确保配置的安全和可恢复性。

## 文件说明

### settings.json
- **路径**: `05-Tools/vscode-config/settings.json`
- **原始路径**: `C:/Users/h31280/AppData/Roaming/Code/User/settings.json`
- **功能**: VSCode全局用户配置
- **包含内容**:
  - 编辑器设置（字体、字号、行高等）
  - 主题配置（分区域配色方案）
  - C/C++扩展设置
  - 终端配置
  - 护眼优化设置

## 同步规则

**重要**: VSCode配置修改后会自动同步到这个目录。

### 自动备份系统
- **自动监控**: 系统会自动监控VSCode配置文件变化
- **自动备份**: 配置修改后自动按时间戳创建历史版本
- **历史保留**: 保留最近30天的备份历史
- **自动清理**: 自动删除30天前的旧备份

### 脚本文件
- `auto_backup_startup.bat` - 启动自动备份监控系统
- `watch_and_backup.ps1` - 监控脚本（后台运行）
- `backup_vscode_config.bat` - 备份执行脚本
- `manual_backup.bat` - 手动触发备份

### 使用方法
1. **启动自动监控**:
   - 双击运行 `auto_backup_startup.bat`
   - 脚本会在后台运行，监控配置变化
   - 配置修改后会自动备份到 `history/` 目录

2. **手动备份**:
   - 双击运行 `manual_backup.bat`
   - 立即执行一次配置备份

3. **停止监控**:
   - 在任务管理器中结束PowerShell进程

## 配置特性

### 当前配置包含
- 分区域配色方案（代码区白色、终端暖灰色、侧边栏浅灰色等）
- 护眼优化（字体大小16px、行高1.6、合适的字间距）
- C/C++ IntelliSense配置
- 终端配色优化（暖灰色背景，不刺眼）
- 编辑器光标动画优化
- 源代码格式化设置

### 颜色方案
| 区域 | 背景色 | 说明 |
|------|---------|------|
| 代码编辑区 | #FAFAFA | 米白色护眼 |
| 终端/控制台 | #2D2D30 | 暖灰色 |
| 底部面板 | #2D2D30 | 暖灰色 |
| 左侧活动栏 | #2D2D2D | 深灰色 |
| 侧边栏 | #F3F3F3 | 浅灰色 |
| 状态栏 | #007ACC | 蓝色 |

## 使用方法

### 恢复配置（如果VSCode配置丢失）：
复制 `05-Tools/vscode-config/settings.json` 到 VSCode 用户配置目录。

## 配置历史

### 2026-04-27
- 添加自动备份系统
- 创建监控脚本，自动检测配置变化
- 按时间戳保存历史版本到 `history/` 目录
- 自动清理30天前的旧备份
- 添加手动备份功能

### 2026-04-26
- 初始配置
- 设置分区域配色方案
- 代码区白色护眼主题
- 终端暖灰色（#2D2D30）避免过暗
- C/C++ IntelliSense配置
- 护眼字体优化（14px、行高1.6）
- 调整编辑器字体大小至16px（增大字号）

## 注意事项

1. **自动备份**: 启动 `auto_backup_startup.bat` 后，系统会自动监控和备份配置
2. **历史管理**: 历史备份保存在 `history/` 目录，按时间戳命名
3. **备份保留**: 自动保留最近30天的备份，旧版本自动清理
4. **跨机器使用**: 此配置可以复制到其他Windows机器使用
5. **版本管理**: 建议使用Git管理此目录，记录配置变更历史

## 目录结构

```
05-Tools\vscode-config\
├── settings.json              # 当前配置文件
├── README.md                  # 说明文档
├── auto_backup_startup.bat    # 自动备份启动器
├── watch_and_backup.ps1       # 监控脚本
├── backup_vscode_config.bat   # 备份执行脚本
├── manual_backup.bat          # 手动备份脚本
└── history/                   # 历史备份目录
    ├── settings_2026-04-27_14-30-15.json
    ├── settings_2026-04-27_15-22-33.json
    └── ...
```

## 相关笔记
- [[VSCode配置管理 Skill]] — VSCode 配置管理的 Skill 封装

## 相关资源

- VSCode配置文档: https://code.visualstudio.com/docs/getstarted/settings
- 配置模板位置: `D:/Ai/Skills/Code Skill/VS 工程构建/template/`
- 配置工具: `D:/Ai/Tools/`
