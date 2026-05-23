@echo off
echo ========================================
echo ContextStack Git自动推送任务设置工具
echo ========================================
echo.
echo 注意: 此操作需要管理员权限
echo.
echo 正在检查现有任务...

REM 检查是否有现有任务
schtasks /query /tn ContextStack_GitAutoPush >nul 2>&1
if %errorlevel% equ 0 (
    echo 发现现有任务: ContextStack_GitAutoPush
    echo 正在删除现有任务...
    schtasks /delete /tn ContextStack_GitAutoPush /f
    if %errorlevel% neq 0 (
        echo 错误: 无法删除现有任务
        echo 请以管理员身份运行此脚本
        pause
        exit /b 1
    )
    echo 现有任务已删除
) else (
    echo 未发现现有任务
)

echo.
echo 正在创建新任务...
echo 任务名称: ContextStack_GitAutoPush
echo 执行时间: 每日 22:00
echo 脚本路径: D:\MyFile\AI\ContextStack\05-Tools\backup\auto_push.ps1
echo.

REM 尝试创建任务（使用当前用户）
schtasks /create /tn ContextStack_GitAutoPush /tr "powershell.exe -ExecutionPolicy Bypass -File \"D:\MyFile\AI\ContextStack\05-Tools\backup\auto_push.ps1\"" /sc DAILY /st 22:00 /ru "%USERNAME%" /rl HIGHEST /f

if %errorlevel% equ 0 (
    echo.
    echo [成功] Git自动推送任务已创建!
    echo.
    echo 任务详情:
    schtasks /query /tn ContextStack_GitAutoPush /fo LIST | findstr /i "TaskName: NextRunTime: LastRunTime:"
) else (
    echo.
    echo [错误] 任务创建失败，可能原因:
    echo 1. 需要管理员权限
    echo 2. 脚本文件不存在
    echo 3. 系统权限不足
    echo.
    echo 请尝试:
    echo 1. 以管理员身份运行此脚本
    echo 2. 手动检查脚本文件路径: D:\MyFile\AI\ContextStack\05-Tools\backup\auto_push.ps1
)

echo.
pause