@echo off
chcp 65001 >nul
echo ========================================
echo  微信 Bot 保活进程 - 开机自启配置
echo ========================================
echo.

set TASK_NAME=WeChatBot_KeepAlive
set SCRIPT_DIR=%~dp0
set PYTHON=%SCRIPT_DIR%..\..\..\..\..\..\AppData\Local\Programs\Python\Python39\python.exe

if not exist "%PYTHON%" set PYTHON=python

echo 创建计划任务: %TASK_NAME%
echo 脚本路径: %SCRIPT_DIR%keepalive.py
echo.

schtasks /Create /SC ONLOGON /TN "%TASK_NAME%" /TR "%PYTHON% %SCRIPT_DIR%keepalive.py" /F /RL HIGHEST /DELAY 0001:00

if %ERRORLEVEL%==0 (
    echo ✅ 开机自启配置成功！
    echo    任务名: %TASK_NAME%
    echo    触发: 用户登录后延迟1分钟启动
    echo.
    echo 启动保活进程...
    start /B %PYTHON% %SCRIPT_DIR%keepalive.py
    echo ✅ 保活进程已启动
) else (
    echo ❌ 配置失败，请以管理员身份运行
)

pause
