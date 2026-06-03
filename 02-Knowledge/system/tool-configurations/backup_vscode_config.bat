@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: VSCode配置自动备份脚本
:: 功能: 将VSCode配置备份到指定目录,并按日期创建历史版本

:: 配置路径
set "VScodeSettings=C:\Users\h31280\AppData\Roaming\Code\User\settings.json"
set "BackupDir=%~dp0..\..\..\05-Tools\vscode-config"
set "HistoryDir=%BackupDir%\history"

:: 获取当前日期和时间
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "datetime=%%I"
set "YEAR=%datetime:~0,4%"
set "MONTH=%datetime:~4,2%"
set "DAY=%datetime:~6,2%"
set "HOUR=%datetime:~8,2%"
set "MINUTE=%datetime:~10,2%"
set "SECOND=%datetime:~12,2%"

set "TIMESTAMP=%YEAR%-%MONTH%-%DAY%_%HOUR%-%MINUTE%-%SECOND%"

:: 创建历史目录
if not exist "%HistoryDir%" (
    mkdir "%HistoryDir%"
    echo 创建历史目录: %HistoryDir%
)

:: 检查源文件是否存在
if not exist "%VScodeSettings%" (
    echo 错误: VSCode配置文件不存在: %VScodeSettings%
    pause
    exit /b 1
)

:: 备份到历史目录
set "HistoryFile=%HistoryDir%\settings_%TIMESTAMP%.json"
copy "%VScodeSettings%" "%HistoryFile%" >nul
if %errorlevel% equ 0 (
    echo ✓ 备份成功: %HistoryFile%
) else (
    echo ✗ 备份失败
    pause
    exit /b 1
)

:: 同步到主配置目录
copy "%VScodeSettings%" "%BackupDir%\settings.json" >nul
if %errorlevel% equ 0 (
    echo ✓ 同步成功: %BackupDir%\settings.json
) else (
    echo ✗ 同步失败
    pause
    exit /b 1
)

:: 清理30天前的历史备份（保留最近30天）
set /a "KeepDays=30"
for /f "skip=%KeepDays% delims=" %%F in ('dir /b /o-d "%HistoryDir%\settings_*.json"') do (
    del "%HistoryDir%\%%F" >nul 2>&1
    echo 删除旧备份: %%F
)

echo.
echo ========================================
echo VSCode配置备份完成
echo 时间戳: %TIMESTAMP%
echo ========================================
echo.

:: 等待3秒后自动关闭
timeout /t 3 /nobreak >nul
