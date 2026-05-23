# VSCode配置监控和自动备份脚本
# 功能: 监控VSCode配置文件变化,自动触发备份

param(
    [int]$Interval = 5  # 检查间隔（秒）
)

$ErrorActionPreference = "Continue"

# 配置路径
$VscodeSettings = "C:\Users\h31280\AppData\Roaming\Code\User\settings.json"
$BackupDir = Join-Path $PSScriptRoot "..\..\..\05-Tools\vscode-config"
$HistoryDir = Join-Path $BackupDir "history"
$BackupScript = Join-Path $BackupDir "backup_vscode_config.bat"

# 创建历史目录
if (-not (Test-Path $HistoryDir)) {
    New-Item -ItemType Directory -Path $HistoryDir -Force | Out-Null
    Write-Host "创建历史目录: $HistoryDir" -ForegroundColor Green
}

# 检查源文件
if (-not (Test-Path $VscodeSettings)) {
    Write-Host "错误: VSCode配置文件不存在: $VscodeSettings" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 获取初始文件的哈希值
$lastHash = (Get-FileHash $VscodeSettings -Algorithm SHA256).Hash
Write-Host "开始监控VSCode配置文件..." -ForegroundColor Cyan
Write-Host "配置文件: $VscodeSettings" -ForegroundColor Cyan
Write-Host "检查间隔: $Interval 秒" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止监控" -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds $Interval

        if (-not (Test-Path $VscodeSettings)) {
            Write-Host "警告: 配置文件已被删除" -ForegroundColor Yellow
            continue
        }

        # 获取当前文件的哈希值
        $currentHash = (Get-FileHash $VscodeSettings -Algorithm SHA256).Hash

        # 比较哈希值
        if ($currentHash -ne $lastHash) {
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] 检测到配置文件变化,开始备份..." -ForegroundColor Yellow

            # 调用备份脚本
            $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$BackupScript`"" -NoNewWindow -Wait -PassThru

            if ($process.ExitCode -eq 0) {
                Write-Host "[$timestamp] 备份成功" -ForegroundColor Green
            } else {
                Write-Host "[$timestamp] 备份失败 (错误代码: $($process.ExitCode))" -ForegroundColor Red
            }

            # 更新哈希值
            $lastHash = $currentHash
            Write-Host ""
        }
    }
}
catch {
    Write-Host "监控脚本出错: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "按回车键退出"
}
