# 备份管理工具

系统备份、数据保护和版本管理的工具集合。

## 💾 工具列表

### Git 自动同步
- [[auto_push.ps1]] — **单位**自动同步：每日 22:00 先 pull 再 push
- [[auto_push_home.ps1]] — **家里**自动同步：每日 03:00 先 pull 再 push

### 核心备份工具
- [[compress_backup.ps1]] - **推荐** 压缩备份脚本 (方案B)
- [[daily_backup.ps1]] - 原始每日备份脚本 (文件夹复制)
- [[restore_from_backup.ps1]] - 备份恢复工具
- [[check_backup_task.bat]] - 备份任务状态检查
- [[test_compress_backup.bat]] - 压缩备份测试脚本
- [[run_backup_task.bat]] - 定时任务执行器 (系统使用)

## 🎯 适用场景

### 1. 定期备份
- 每日自动备份重要数据
- 保留指定天数的备份历史
- 自动清理过期备份

### 2. 数据保护
- 防止误删除或文件损坏
- 版本回退和恢复
- 跨设备数据同步

### 3. 灾难恢复
- 系统故障时的数据恢复
- 配置丢失时的快速恢复
- 迁移到新环境的准备

## 🚀 使用指南

### 🔄 自动备份 (已配置)
**系统已配置每日自动备份，无需手动操作**
- **时间**: 每天 24:00 (00:00)
- **方式**: Windows 任务计划程序
- **任务名**: `ContextStack_Backup`
- **状态**: ✅ 已启用，每天自动运行

### 手动执行备份
#### 压缩备份脚本 (推荐方案B)
```powershell
# 运行压缩备份
powershell -File compress_backup.ps1

# 带参数运行（指定备份目录和保留天数）
powershell -File compress_backup.ps1 -BackupRoot "D:\Backups" -RetentionDays 30

# 指定源目录
powershell -File compress_backup.ps1 -SourceDir "D:\MyFile\AI\ContextStack" -RetentionDays 14
```

### 原始每日备份脚本
```powershell
# 运行每日备份
powershell -File daily_backup.ps1

# 带参数运行（指定备份目录和保留天数）
powershell -File daily_backup.ps1 -BackupRoot "D:\Backups" -RetentionDays 30
```

### 参数说明
- `-BackupRoot`：备份根目录
  - 压缩备份默认：`D:\MyFile\AI\ContextStack_backups_compressed`
  - 原始备份默认：`D:\MyFile\AI\ContextStack\backups_daily`
- `-SourceDir`：源目录（默认：`D:\MyFile\AI\ContextStack`）
- `-RetentionDays`：保留天数（默认：7天）

## 📋 备份策略

### 1. 备份频率
- **每日备份**：核心数据和配置文件
- **每周备份**：完整数据备份
- **每月备份**：归档备份，长期保存

### 2. 保留策略
- 最近7天的每日备份
- 最近4周的每周备份
- 最近12个月的每月备份

### 3. 备份内容
- 配置文件（`.json`、`.yaml`、`.md`）
- 代码文件（`.py`、`.ps1`、`.bat`）
- 文档文件（`.txt`、`.md`、`.pdf`）
- 重要数据文件

### 4. 排除内容
- 临时文件（`.tmp`、`.log`）
- 缓存文件（`.cache`、`__pycache__`）
- 备份目录本身（避免递归）
- 大型二进制文件（选择性备份）

## 🔧 备份原理

### 压缩备份流程 (compress_backup.ps1)
```
1. 检查备份目录和 PowerShell 版本
2. 创建带日期的 ZIP 文件名 (ContextStack_yyyy-MM-dd.zip)
3. 复制文件到临时目录（排除备份文件）
4. 使用 Compress-Archive 压缩为 ZIP
5. 计算压缩率和节省空间
6. 清理过期备份（超过保留天数）
7. 生成详细备份摘要
```

### 原始备份流程 (daily_backup.ps1)
```
1. 检查备份目录是否存在
2. 创建带时间戳的备份目录
3. 使用 Robocopy 复制文件
4. 应用排除规则
5. 清理过期备份
6. 生成备份摘要
```

### 技术特点对比
| 特性 | 压缩备份 (方案B) | 原始备份 |
|------|-----------------|----------|
| **空间节省** | ✅ 高 (ZIP压缩) | ❌ 无压缩 |
| **恢复便利** | ✅ 直接解压 ZIP | ✅ 直接访问文件夹 |
| **备份速度** | ⚠️ 较慢（需压缩） | ✅ 快（直接复制） |
| **版本管理** | ✅ 清晰 (日期ZIP) | ✅ 清晰 (日期文件夹) |
| **增量支持** | ❌ 全量压缩 | ✅ Robocopy 增量 |
| **存储效率** | ✅ 高（节省60-80%） | ❌ 低（原始大小） |

## ⚠️ 注意事项

### 安全提示
- 备份目录应放在不同磁盘或设备
- 敏感数据加密备份
- 定期验证备份的完整性
- 测试恢复流程确保可用

### 性能考虑
- 备份时间窗口选择非高峰时段
- 网络备份注意带宽限制
- 大文件备份考虑增量策略
- 监控备份进度和资源使用

## 📊 备份监控

### 监控指标
- 备份成功/失败状态
- 备份大小和文件数量
- 备份耗时
- 存储空间使用情况

### 报警机制
- 备份失败通知
- 存储空间不足警告
- 备份时间异常提醒

## 🔗 相关链接

- [[tools/index|工具库索引]]
- [[tools/README|工具库详细说明]]
- [[encoding/index|编码处理工具]]
- [[02-Knowledge/system/tool-configurations/index|工具配置管理]]（VSCode备份）

## 🔄 扩展计划

### 已实现工具
- ✅ `compress_backup.ps1` - 压缩备份脚本 (方案B)
- ✅ `daily_backup.ps1` - 原始每日备份脚本

### 待开发工具
- `incremental_backup.ps1` - 增量备份脚本 (方案C)
- `backup_verification.py` - 备份验证工具
- `cloud_backup.py` - 云备份工具
- `backup_scheduler.py` - 备份调度器

### 功能增强
- 支持云存储备份（OneDrive、Google Drive）
- 备份加密（ZIP密码保护）
- 自动化恢复测试
- 备份报表生成
- 增量压缩备份（每日增量+每周全量）

---

**最后更新**: 2026-05-08  
**工具版本**: v2.0 (新增压缩备份)  
**维护者**: ContextStack 框架