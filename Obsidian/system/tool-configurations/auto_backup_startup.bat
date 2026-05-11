@echo off
chcp 65001 >nul

:: VSCode配置自动备份启动脚本
:: 功能: 启动后台监控脚本,自动备份VSCode配置变化

echo ========================================
echo VSCode配置自动备份启动器
echo ========================================
echo.

set "BackupDir=D:\My File\AI\ContextStack\VSCode Config"
set "WatchScript=%BackupDir%\watch_and_backup.ps1"

:: 检查脚本是否存在
if not exist "%WatchScript%" (
    echo 错误: 监控脚本不存在: %WatchScript%
    pause
    exit /b 1
)

echo 正在启动VSCode配置监控...
echo 监控脚本: %WatchScript%
echo.
echo 提示: 监控将在后台运行,VSCode配置修改后会自动备份
echo       按 Ctrl+C 可以停止监控
echo.

:: 以隐藏窗口方式启动PowerShell监控脚本
start powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%WatchScript%"

if %errorlevel% equ 0 (
    echo ✓ 监控已启动 (后台运行)
    echo.
    echo 如需停止监控,请在任务管理器中结束 PowerShell 进程
) else (
    echo ✗ 监控启动失败
    pause
    exit /b 1
)

echo.
timeout /t 3 /nobreak >nul
