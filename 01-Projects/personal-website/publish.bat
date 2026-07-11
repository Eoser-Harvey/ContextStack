@echo off
chcp 65001 >nul
REM ============================================================
REM publish.bat — 一键发布文章到个人网站
REM
REM 使用方法:
REM   publish.bat <文章文件路径> <文章slug>
REM
REM 示例:
REM   publish.bat "D:\Downloads\我的投资复盘.html" "investment-review-2026-07"
REM   publish.bat article.md "embedded-ai-week1"
REM
REM 流程:
REM   1. add_article.py 生成文章页面 + 更新首页
REM   2. git add + commit + push
REM   3. Cloudflare Pages 自动部署（1-3分钟）
REM   4. 读者刷新页面即可看到新文章
REM ============================================================

setlocal

if "%~1"=="" (
    echo 用法: publish.bat ^<文章文件路径^> ^<文章slug^>
    echo 示例: publish.bat "D:\Downloads\文章.html" "my-article"
    exit /b 1
)

if "%~2"=="" (
    echo 用法: publish.bat ^<文章文件路径^> ^<文章slug^>
    exit /b 1
)

set ARTICLE_FILE=%~1
set ARTICLE_SLUG=%~2
set WEBSITE_DIR=%~dp0

echo ============================================
echo  发布文章: %ARTICLE_SLUG%
echo ============================================
echo.

REM Step 1: 生成文章页面
echo [1/3] 生成文章页面...
python "%WEBSITE_DIR%add_article.py" "%ARTICLE_FILE%" "%ARTICLE_SLUG%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: 文章生成失败！
    exit /b 1
)
echo.

REM Step 2: Git提交
echo [2/3] Git提交...
cd /d "%WEBSITE_DIR%"
git add -A
git commit -m "publish: %ARTICLE_SLUG%"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Git commit无变更或失败，继续推送...
)
echo.

REM Step 3: 推送
echo [3/3] 推送到远程...
git push origin main
if %ERRORLEVEL% neq 0 (
    echo WARNING: Git push失败，请检查网络或手动推送
    exit /b 1
)

echo.
echo ============================================
echo  发布成功！
echo ============================================
echo  文章页面: articles/%ARTICLE_SLUG%.html
echo  Cloudflare Pages将在1-3分钟内自动部署
echo  读者刷新 https://你的域名 即可看到新文章
echo ============================================

endlocal
