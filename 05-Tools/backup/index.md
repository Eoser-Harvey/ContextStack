# Git 自动同步工具

> 备份策略：Git = 本地 + GitHub 远程双重备份，不再使用本地压缩备份。

## 工具列表

| 脚本 | 用途 | 目标机器人 |
|------|------|------|
| [auto_push.ps1](./auto_push.ps1) | 单位自动同步：每日 22:00 先 pull 再 push | 单位电脑 |
| [auto_push_home.ps1](./auto_push_home.ps1) | 家里自动同步：每日 03:00 先 pull 再 push | 家里电脑 |
| [setup_git_task.bat](./setup_git_task.bat) | 设置 Windows 任务计划程序 | 助理安装 |
| [README-自动推送任务.md](./README-自动推送任务.md) | 设置指南和故障排出 | 参考资料 |

## 任务状态

| 任务 | 状态 | 上次运行 |
|------|------|----------|
| ContextStack_GitAutoPush（单位） | ✅ 就绪 | 每日 22:00 |
| 家里自动同步 | ✅ 已配置 | 每日 03:00 |

### 检查任务
```powershell
schtasks /query /tn "ContextStack_GitAutoPush"
```

### 重新设置（路径变更后）
以管理员身份运行 `setup_git_task.bat`

## 注意事项

- Git 提交前先 pull，避免冲突
- 两台机器的自动同步脚本间隔足够，不会冲突
- 不再使用本地压缩备份，Git 提供完整版本历史

---

**最后更新**: 2026-05-26
**工具版本**: v3.1（移除压缩备份，专注 Git 同步）