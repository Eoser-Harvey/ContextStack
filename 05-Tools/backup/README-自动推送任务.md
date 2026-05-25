# Git自动推送任务设置指南

## 背景
由于ContextStack框架升级，Git自动推送脚本的路径发生了变化：
- **旧路径**: `tools/backup/auto_push.ps1`
- **新路径**: `05-Tools/backup/auto_push.ps1`

## 解决方案
已创建批处理文件用于重新设置Windows任务计划程序任务：

### 文件位置
- `05-Tools/backup/setup_git_task.bat` - 自动设置脚本
- `05-Tools/backup/auto_push.ps1` - Git自动推送脚本（单位电脑版，22:00执行）
- `05-Tools/backup/auto_push_home.ps1` - Git自动推送脚本（家里电脑版，3:00执行）

### 使用方法
1. **以管理员身份运行** `setup_git_task.bat`
2. 脚本会自动：
   - 检查并删除现有任务（如果存在）
   - 创建新任务 `ContextStack_GitAutoPush`
   - 设置为每日22:00执行
   - 使用当前用户权限

### 任务详情
- **任务名称**: `ContextStack_GitAutoPush`
- **执行时间**: 每日22:00
- **执行命令**: `powershell.exe -ExecutionPolicy Bypass -File "./05-Tools/backup/auto_push.ps1"`
- **日志文件**: `05-Tools/backup/auto_push.log`

## 手动检查任务状态
```cmd
REM 查看任务详情
schtasks /query /tn ContextStack_GitAutoPush /fo LIST

REM 运行任务测试
schtasks /run /tn ContextStack_GitAutoPush

REM 删除任务（如果需要）
schtasks /delete /tn ContextStack_GitAutoPush /f
```

## 注意事项
1. **需要管理员权限**：设置任务计划需要管理员权限
2. **脚本路径正确性**：确保路径 `./05-Tools/backup/auto_push.ps1` 存在
3. **Git配置**：确保Git已正确配置用户名和邮箱
4. **网络连接**：推送需要网络连接

## 故障排除
如果任务创建失败：
1. 以管理员身份运行批处理文件
2. 检查脚本文件是否存在
3. 检查Git是否已安装并配置
4. 手动使用以下命令创建：
   ```cmd
   schtasks /create /tn ContextStack_GitAutoPush /tr "powershell.exe -ExecutionPolicy Bypass -File \"./05-Tools/backup/auto_push.ps1\"" /sc DAILY /st 22:00 /ru "%USERNAME%" /rl HIGHEST /f
   ```

## 更新历史
- 2026-05-23: 适配框架v3.0目录结构，创建重新设置工具