# ContextStack 备份恢复脚本
# 功能: 从压缩备份 (ZIP) 或原始备份恢复文件
#
# 使用方式:
# powershell -File restore_from_backup.ps1 -BackupFile "backups_compressed\ContextStack_2025-05-08.zip"
# powershell -File restore_from_backup.ps1 -BackupDir "backups_daily\ContextStack_20250508" -RestoreTo "D:\Restore"

param(
    [string]$BackupFile,      # ZIP备份文件路径
    [string]$BackupDir,       # 原始备份目录路径
    [string]$RestoreTo = "D:\MyFile\AI\ContextStack_Restored",  # 恢复目标目录
    [switch]$ListBackups,     # 列出可用备份
    [switch]$Force            # 强制覆盖目标目录
)

# 函数: 日志记录
function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

# 函数: 列出可用备份
function List-AvailableBackups {
    Write-Log "可用的备份文件:" "Cyan"
    
    # 检查压缩备份目录
    $compressedBackupRoot = "D:\MyFile\AI\ContextStack\backups_compressed"
    if (Test-Path $compressedBackupRoot) {
        Write-Log "压缩备份 (ZIP):" "Yellow"
        $zipFiles = Get-ChildItem -Path $compressedBackupRoot -Filter "ContextStack_*.zip" | Sort-Object LastWriteTime -Descending
        if ($zipFiles.Count -eq 0) {
            Write-Log "  无压缩备份文件" "Gray"
        } else {
            foreach ($file in $zipFiles) {
                $sizeMB = [math]::Round($file.Length / 1MB, 2)
                $ageDays = [math]::Round(((Get-Date) - $file.LastWriteTime).TotalDays, 1)
                Write-Host "  - $($file.Name) ($sizeMB MB) [$ageDays 天前]"
            }
        }
    }
    
    # 检查原始备份目录
    $dailyBackupRoot = "D:\MyFile\AI\ContextStack\backups_daily"
    if (Test-Path $dailyBackupRoot) {
        Write-Log "原始备份 (文件夹):" "Yellow"
        $dirs = Get-ChildItem -Path $dailyBackupRoot -Directory -Filter "ContextStack_*" | Sort-Object LastWriteTime -Descending
        if ($dirs.Count -eq 0) {
            Write-Log "  无原始备份文件夹" "Gray"
        } else {
            foreach ($dir in $dirs) {
                $sizeMB = [math]::Round((Get-ChildItem -Path $dir.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
                $ageDays = [math]::Round(((Get-Date) - $dir.LastWriteTime).TotalDays, 1)
                Write-Host "  - $($dir.Name) ($sizeMB MB) [$ageDays 天前]"
            }
        }
    }
    
    Write-Log "使用示例:" "Green"
    Write-Host "  恢复最新压缩备份: powershell -File restore_from_backup.ps1 -BackupFile `"backups_compressed\ContextStack_2025-05-08.zip`""
    Write-Host "  恢复原始备份: powershell -File restore_from_backup.ps1 -BackupDir `"backups_daily\ContextStack_20250508`""
}

# 主程序
if ($ListBackups) {
    List-AvailableBackups
    exit 0
}

# 检查恢复目标目录
if (Test-Path $RestoreTo) {
    if ($Force) {
        Write-Log "强制模式: 将清空目标目录 $RestoreTo" "Yellow"
        Remove-Item -Path $RestoreTo -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        Write-Log "错误: 目标目录已存在: $RestoreTo" "Red"
        Write-Log "使用 -Force 参数覆盖，或指定不同的目标目录" "Yellow"
        exit 1
    }
}

# 创建目标目录
New-Item -ItemType Directory -Path $RestoreTo -Force | Out-Null
Write-Log "创建恢复目标目录: $RestoreTo" "Green"

# 处理压缩备份 (ZIP)
if ($BackupFile) {
    # 如果提供的是相对路径，转换为绝对路径
    if (-not [System.IO.Path]::IsPathRooted($BackupFile)) {
        $BackupFile = Join-Path (Get-Location) $BackupFile
    }
    
    if (-not (Test-Path $BackupFile)) {
        Write-Log "错误: 备份文件不存在: $BackupFile" "Red"
        exit 1
    }
    
    Write-Log "从压缩备份恢复: $BackupFile" "Cyan"
    Write-Log "目标目录: $RestoreTo" "Cyan"
    
    try {
        # 使用 Expand-Archive 解压
        Expand-Archive -Path $BackupFile -DestinationPath $RestoreTo -Force
        Write-Log "✅ 恢复完成" "Green"
        
        # 显示恢复的文件统计
        $fileCount = (Get-ChildItem -Path $RestoreTo -Recurse -File).Count
        $dirCount = (Get-ChildItem -Path $RestoreTo -Recurse -Directory).Count
        Write-Log "恢复统计: $fileCount 个文件, $dirCount 个目录" "Green"
    }
    catch {
        Write-Log "❌ 恢复失败: $($_.Exception.Message)" "Red"
        exit 1
    }
}
# 处理原始备份目录
elseif ($BackupDir) {
    # 如果提供的是相对路径，转换为绝对路径
    if (-not [System.IO.Path]::IsPathRooted($BackupDir)) {
        $BackupDir = Join-Path (Get-Location) $BackupDir
    }
    
    if (-not (Test-Path $BackupDir)) {
        Write-Log "错误: 备份目录不存在: $BackupDir" "Red"
        exit 1
    }
    
    Write-Log "从原始备份恢复: $BackupDir" "Cyan"
    Write-Log "目标目录: $RestoreTo" "Cyan"
    
    try {
        # 使用 Robocopy 复制
        $robocopyArgs = @(
            $BackupDir,
            $RestoreTo,
            "/E",          # 复制子目录
            "/COPY:DAT",   # 复制数据、属性、时间戳
            "/R:3",        # 失败时重试3次
            "/W:5",        # 重试等待5秒
            "/NP",         # 不显示进度
            "/NDL",        # 不显示目录列表
            "/NJH",        # 不显示作业头
            "/NJS"         # 不显示作业摘要
        )
        
        Write-Log "正在复制文件..." "Yellow"
        & robocopy @robocopyArgs
        
        if ($LASTEXITCODE -lt 8) {
            Write-Log "✅ 恢复完成" "Green"
            
            # 显示恢复的文件统计
            $fileCount = (Get-ChildItem -Path $RestoreTo -Recurse -File).Count
            $dirCount = (Get-ChildItem -Path $RestoreTo -Recurse -Directory).Count
            Write-Log "恢复统计: $fileCount 个文件, $dirCount 个目录" "Green"
        } else {
            Write-Log "⚠️ 恢复过程中出现错误 (robocopy 退出代码: $LASTEXITCODE)" "Yellow"
        }
    }
    catch {
        Write-Log "❌ 恢复失败: $($_.Exception.Message)" "Red"
        exit 1
    }
}
else {
    Write-Log "错误: 必须指定 -BackupFile 或 -BackupDir 参数" "Red"
    Write-Log "使用 -ListBackups 查看可用备份" "Yellow"
    Write-Log ""
    Write-Log "使用示例:" "Green"
    Write-Host "  列出备份: powershell -File restore_from_backup.ps1 -ListBackups"
    Write-Host "  恢复ZIP备份: powershell -File restore_from_backup.ps1 -BackupFile `"backups_compressed\ContextStack_2025-05-08.zip`""
    Write-Host "  恢复文件夹备份: powershell -File restore_from_backup.ps1 -BackupDir `"backups_daily\ContextStack_20250508`""
    Write-Host "  恢复到指定目录: powershell -File restore_from_backup.ps1 -BackupFile `"backups_compressed\ContextStack_2025-05-08.zip`" -RestoreTo `"D:\Restore`""
    exit 1
}

# 显示恢复位置
Write-Log "恢复完成!" "Green"
Write-Log "文件已恢复到: $RestoreTo" "Green"
Write-Log "可以在文件资源管理器中打开该目录查看恢复的文件。" "Yellow"