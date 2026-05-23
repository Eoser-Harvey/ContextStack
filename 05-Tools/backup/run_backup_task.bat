@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo ContextStack 定时备份任务执行器
echo ========================================
echo.
echo 此脚本由 Windows 任务计划程序在每天 00:00 自动调用
echo 执行实际的压缩备份操作
echo.
echo 开始时间: %DATE% %TIME%
echo.

set "SCRIPT_PATH=%~dp0compress_backup.ps1"
set "LOG_FILE=%~dp0backup_task.log"
set "ERROR_LOG=%~dp0backup_errors.log"

:: 创建日志目录（如果需要）
if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOG_DIR=%~dp0logs"

:: 生成带时间戳的日志文件名
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "datetime=%%I"
set "TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%"
set "DETAILED_LOG=%LOG_DIR%\backup_%TIMESTAMP%.log"

:: 记录开始时间
echo ======================================== >> "%LOG_FILE%"
echo [%DATE% %TIME%] 开始执行定时备份任务 >> "%LOG_FILE%"
echo [%DATE% %TIME%] 详细日志: %DETAILED_LOG% >> "%LOG_FILE%"

:: 执行备份脚本，同时输出到控制台和详细日志
echo 正在执行备份脚本: %SCRIPT_PATH%
echo 执行命令: powershell -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"
echo.

:: 执行备份，捕获输出
powershell -ExecutionPolicy Bypass -File "%SCRIPT_PATH%" > "%DETAILED_LOG%" 2>&1
set "EXIT_CODE=%errorlevel%"

:: 读取详细日志的最后几行
set "LOG_TAIL="
for /f "skip=1 delims=" %%A in ('type "%DETAILED_LOG%" ^| tail -10') do (
    set "LOG_TAIL=!LOG_TAIL!%%A\n"
)

:: 记录结果
echo 备份执行完成，退出代码: %EXIT_CODE%
echo.

if %EXIT_CODE% equ 0 (
    echo [%DATE% %TIME%] ✅ 备份任务执行成功 >> "%LOG_FILE%"
    echo ✅ 备份任务执行成功
    echo 成功日志片段:
    echo !LOG_TAIL!
) else (
    echo [%DATE% %TIME%] ❌ 备份任务执行失败 (错误代码: %EXIT_CODE%) >> "%LOG_FILE%"
    echo [%DATE% %TIME%] 错误详情: !LOG_TAIL! >> "%ERROR_LOG%"
    echo ❌ 备份任务执行失败 (错误代码: %EXIT_CODE%)
    echo 错误日志片段:
    echo !LOG_TAIL!
)

echo [%DATE% %TIME%] 备份任务结束 >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo.

:: 清理旧日志（保留最近30天）
forfiles /p "%LOG_DIR%" /m "backup_*.log" /d -30 /c "cmd /c del @path" >nul 2>&1
forfiles /p "%~dp0" /m "backup_task.log" /d -90 /c "cmd /c echo 清理旧日志: @path" >> "%LOG_FILE%" 2>&1

echo 结束时间: %DATE% %TIME%
echo 任务日志: %LOG_FILE%
echo 详细日志: %DETAILED_LOG%
echo 错误日志: %ERROR_LOG%
echo ========================================

:: 任务计划程序运行时不需要保持窗口打开
:: 此脚本应以静默方式运行
exit /b %EXIT_CODE%