# ContextStack 压缩备份脚本 (方案B)
# 功能: 直接压缩整个 ContextStack 目录为 ZIP 文件，文件名包含日期，保留7天备份
#
# 使用方式:
# powershell -File compress_backup.ps1
# powershell -File compress_backup.ps1 -BackupRoot "D:\Backups" -RetentionDays 30

param(
    [string]$BackupRoot = "D:\MyFile\AI\ContextStack_backups_compressed",
    [string]$SourceDir = "D:\MyFile\AI\ContextStack",
    [int]$RetentionDays = 7
)

# 函数: 日志记录
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

# 1. 检查 PowerShell 版本（需要 5.0+ 支持 Compress-Archive）
$psVersion = $PSVersionTable.PSVersion.Major
if ($psVersion -lt 5) {
    Write-Log "错误: 需要 PowerShell 5.0 或更高版本 (当前: $psVersion)"
    exit 1
}

# 2. 创建备份根目录
if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Write-Log "创建备份根目录: $BackupRoot"
}

# 3. 生成备份文件名（包含日期）
$backupDate = Get-Date -Format "yyyy-MM-dd"
$zipFileName = "ContextStack_$backupDate.zip"
$zipFilePath = Join-Path $BackupRoot $zipFileName

# 4. 检查今天的备份是否已存在
if (Test-Path $zipFilePath) {
    Write-Log "今天的备份已存在: $zipFilePath，跳过备份"
    exit 0
}

# 5. 检查源目录是否存在
if (-not (Test-Path $SourceDir)) {
    Write-Log "错误: 源目录不存在: $SourceDir"
    exit 1
}

Write-Log "开始压缩备份: $SourceDir → $zipFilePath"

# 6. 定义排除模式（避免递归备份备份目录）
$excludePatterns = @(
    "backups_daily",
    "backups_compressed",
    "backup_archive",
    "*.backup*",
    "*.tmp",
    "*.log",
    "*.zip"
)

# 7. 创建临时目录用于准备备份文件
$tempDir = Join-Path $env:TEMP "ContextStack_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Write-Log "创建临时目录: $tempDir"

try {
    # 8. 使用 Robocopy 复制文件到临时目录（应用排除规则）
    $robocopyArgs = @(
        $SourceDir,
        $tempDir,
        "/E",          # 复制子目录，包括空目录
        "/COPY:DAT",   # 复制数据、属性、时间戳
        "/R:3",        # 失败时重试3次
        "/W:5",        # 重试等待5秒
        "/NP",         # 不显示进度
        "/NDL",        # 不显示目录列表
        "/NJH",        # 不显示作业头
        "/NJS"         # 不显示作业摘要
    )
    
    # 添加排除模式
    foreach ($pattern in $excludePatterns) {
        $robocopyArgs += "/XD"
        $robocopyArgs += $pattern
    }
    
    # 排除特定文件扩展名
    $robocopyArgs += "/XF"
    $robocopyArgs += "*.tmp"
    $robocopyArgs += "*.log"
    $robocopyArgs += "*.backup*"
    
    Write-Log "正在复制文件到临时目录..."
    & robocopy @robocopyArgs
    
    if ($LASTEXITCODE -ge 8) {
        Write-Log "警告: 文件复制过程中出现错误 (robocopy 退出代码: $LASTEXITCODE)"
    }
    
    # 9. 计算源目录大小（用于日志）
    $sourceSize = (Get-ChildItem -Path $SourceDir -Recurse -File | Measure-Object -Property Length -Sum | Select-Object -ExpandProperty Sum)
    $sourceSizeMB = [math]::Round($sourceSize / 1MB, 2)
    Write-Log "源目录大小: $sourceSizeMB MB ($sourceSize 字节)"
    
    # 10. 压缩临时目录
    Write-Log "正在压缩文件..."
    $compressStartTime = Get-Date
    
    try {
        # 使用 Compress-Archive 创建 ZIP
        Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFilePath -CompressionLevel Optimal -Force
        $compressSuccess = $true
    }
    catch {
        Write-Log "压缩失败: $($_.Exception.Message)"
        $compressSuccess = $false
    }
    
    $compressEndTime = Get-Date
    $compressDuration = [math]::Round(($compressEndTime - $compressStartTime).TotalSeconds, 2)
    
    if ($compressSuccess) {
        # 11. 计算压缩后大小
        $zipSize = (Get-Item $zipFilePath).Length
        $zipSizeMB = [math]::Round($zipSize / 1MB, 2)
        $compressionRatio = [math]::Round(($sourceSize - $zipSize) / $sourceSize * 100, 1)
        
        Write-Log "压缩完成: $zipSizeMB MB ($zipSize 字节)"
        Write-Log "压缩率: $compressionRatio% (节省 $([math]::Round(($sourceSize - $zipSize) / 1MB, 2)) MB)"
        Write-Log "压缩耗时: $compressDuration 秒"
        
        # 12. 创建备份摘要文件
        $summaryFile = Join-Path $BackupRoot "backup_summary_$backupDate.txt"
        @"
ContextStack 压缩备份摘要
=========================
备份日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
源目录: $SourceDir
备份文件: $zipFileName
源目录大小: $sourceSizeMB MB ($sourceSize 字节)
压缩后大小: $zipSizeMB MB ($zipSize 字节)
压缩率: $compressionRatio%
压缩耗时: $compressDuration 秒
保留策略: $RetentionDays 天
排除内容: 备份目录、临时文件(*.tmp, *.log)、备份文件(*.backup*)

备份文件列表:
-------------
$(Get-ChildItem -Path $BackupRoot -Filter "ContextStack_*.zip" | Sort-Object LastWriteTime -Descending | ForEach-Object { "  - $($_.Name) ($([math]::Round($_.Length / 1MB, 2)) MB) [$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))]" })
"@ | Out-File -FilePath $summaryFile -Encoding UTF8
        
        Write-Log "备份摘要保存到: $summaryFile"
    }
}
finally {
    # 13. 清理临时目录
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "已清理临时目录: $tempDir"
    }
}

# 14. 清理旧备份（超过 RetentionDays 天）
if ($compressSuccess) {
    Write-Log "清理超过 $RetentionDays 天的旧备份..."
    $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $backupFiles = Get-ChildItem -Path $BackupRoot -Filter "ContextStack_*.zip"
    $summaryFiles = Get-ChildItem -Path $BackupRoot -Filter "backup_summary_*.txt"
    
    $deletedCount = 0
    foreach ($file in $backupFiles) {
        if ($file.LastWriteTime -lt $cutoffDate) {
            Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
            Write-Log "删除旧备份文件: $($file.Name)"
            $deletedCount++
        }
    }
    
    foreach ($file in $summaryFiles) {
        # 从文件名中提取日期
        if ($file.Name -match 'backup_summary_(\d{4}-\d{2}-\d{2})\.txt') {
            $fileDate = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd', $null)
            if ($fileDate -lt $cutoffDate) {
                Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
                Write-Log "删除旧备份摘要: $($file.Name)"
            }
        }
    }
    
    if ($deletedCount -gt 0) {
        Write-Log "已清理 $deletedCount 个旧备份文件"
    }
}

# 15. 最终状态
if ($compressSuccess) {
    Write-Log "✅ 压缩备份完成: $zipFilePath"
    Write-Log "备份文件列表:"
    Get-ChildItem -Path $BackupRoot -Filter "ContextStack_*.zip" | Sort-Object LastWriteTime | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        $ageDays = [math]::Round(((Get-Date) - $_.LastWriteTime).TotalDays, 1)
        Write-Host "  - $($_.Name) ($sizeMB MB) [$ageDays 天前]"
    }
} else {
    Write-Log "❌ 压缩备份失败"
    exit 1
}
