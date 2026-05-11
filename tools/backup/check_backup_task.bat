@echo off
chcp 65001 >nul
echo ========================================
echo ContextStack 备份任务状态检查
echo ========================================
echo.
echo 检查时间: %DATE% %TIME%
echo.

echo [1] 检查任务计划程序中的备份任务...
schtasks /query /tn "ContextStack_Backup" /fo list
echo.

echo [2] 检查备份目录是否存在...
if exist "D:\MyFile\AI\ContextStack\backups_compressed\" (
    echo ✅ 备份目录存在: D:\MyFile\AI\ContextStack\backups_compressed\
    echo.
    echo [3] 列出最近的备份文件...
    powershell -Command "Get-ChildItem 'D:\MyFile\AI\ContextStack\backups_compressed' -Filter 'ContextStack_*.zip' | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name, LastWriteTime, @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}} -AutoSize"
) else (
    echo ❌ 备份目录不存在
    echo 提示: 备份任务将在今晚24:00首次运行
)

echo.
echo [4] 检查任务下次运行时间...
for /f "tokens=2 delims=:" %%a in ('schtasks /query /tn "ContextStack_Backup" /fo list ^| findstr "下次运行时间"') do (
    set "nextRun=%%a"
)
if defined nextRun (
    echo ✅ 下次运行时间: %nextRun%
) else (
    echo ❌ 无法获取下次运行时间
)

echo.
echo [5] 手动测试备份执行...
echo 是否要立即测试备份? (Y/N)
set /p testChoice=
if /i "%testChoice%"=="Y" (
    echo.
    echo 正在执行测试备份...
    powershell -ExecutionPolicy Bypass -File "compress_backup.ps1"
)

echo.
echo ========================================
echo 操作说明:
echo 1. 备份任务已配置为每天 24:00 自动运行
echo 2. 备份文件保存在: D:\MyFile\AI\ContextStack\backups_compressed\
echo 3. 备份格式: ContextStack_yyyy-MM-dd.zip
echo 4. 保留策略: 7天自动清理
echo ========================================
echo.
pause