@echo off
chcp 65001 >nul
echo ========================================
echo 压缩备份测试脚本
echo ========================================
echo.
echo 此脚本将测试 compress_backup.ps1 的功能
echo 注意: 这可能会创建实际的备份文件
echo.
echo 请选择测试模式:
echo 1. 快速测试 (显示命令，不实际执行)
echo 2. 实际测试 (运行压缩备份，创建备份文件)
echo 3. 带参数测试 (指定保留天数)
echo.
set /p choice="请选择 [1-3]: "

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto actual_test
if "%choice%"=="3" goto param_test
echo 无效选择
pause
exit /b 1

:quick_test
echo.
echo 快速测试模式 - 显示命令但不执行
echo.
echo 命令: powershell -File compress_backup.ps1
echo 参数说明:
echo   -BackupRoot: 备份根目录 (默认: D:\MyFile\AI\ContextStack\backups_compressed)
echo   -SourceDir: 源目录 (默认: D:\MyFile\AI\ContextStack)
echo   -RetentionDays: 保留天数 (默认: 7)
echo.
echo 要实际运行，请执行:
echo   powershell -File compress_backup.ps1
goto :eof

:actual_test
echo.
echo 实际测试模式 - 运行压缩备份
echo.
echo 正在运行 compress_backup.ps1...
powershell -ExecutionPolicy Bypass -File "compress_backup.ps1"
echo.
echo 测试完成!
echo 备份文件保存在: D:\MyFile\AI\ContextStack\backups_compressed\
echo.
pause
goto :eof

:param_test
echo.
echo 带参数测试模式
echo.
set /p retention="请输入保留天数 (默认7): "
if "%retention%"=="" set retention=7
echo.
echo 正在运行 compress_backup.ps1 -RetentionDays %retention%...
powershell -ExecutionPolicy Bypass -File "compress_backup.ps1" -RetentionDays %retention%
echo.
echo 测试完成!
echo 备份文件保存在: D:\MyFile\AI\ContextStack\backups_compressed\
echo 保留策略: %retention% 天
echo.
pause
goto :eof