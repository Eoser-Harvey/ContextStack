@echo off
:: Register daily scheduled task to refresh CodeBuddy chat-index.md
:: Runs chat-index.ps1 every day at 22:30 (after auto_push at 22:00)
:: Right-click and "Run as Administrator" to register.

set TASK=ContextStack_ChatIndex
set SCRIPT=d:\MyFile\AI\ContextStack\05-Tools\codebuddy-chat-manager\chat-index.ps1

schtasks /create /f /tn "%TASK%" /tr "powershell.exe -ExecutionPolicy Bypass -File ""%SCRIPT%""" /sc daily /st 22:30 /rl highest

if %errorlevel% equ 0 (
    echo.
    echo [OK] Task "%TASK%" registered successfully.
    echo It will run chat-index.ps1 daily at 22:30 to refresh chat-index.md.
    echo.
    echo To verify:   schtasks /query /tn "%TASK%" /v /fo LIST
    echo To remove:   schtasks /delete /tn "%TASK%" /f
) else (
    echo.
    echo [FAIL] Registration failed - run this file as Administrator.
)
echo.
pause
