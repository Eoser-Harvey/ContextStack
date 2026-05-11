@echo off
chcp 65001 >nul

:: VSCode配置手动备份脚本
:: 功能: 手动触发一次配置备份

echo ========================================
echo VSCode配置手动备份
echo ========================================
echo.

set "BackupDir=D:\My File\AI\ContextStack\VSCode Config"
set "BackupScript=%BackupDir%\backup_vscode_config.bat"

if not exist "%BackupScript%" (
    echo 错误: 备份脚本不存在: %BackupScript%
    pause
    exit /b 1
)

echo 正在执行配置备份...
echo.

call "%BackupScript%"

echo.
echo 按任意键退出...
pause >nul
