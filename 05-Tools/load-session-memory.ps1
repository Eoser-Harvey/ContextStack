# 加载会话记忆脚本
# 每次对话开始时执行，读取最近会话经验

$sessionDir = "e:\ProjectGroup\AI\ContextStack\03-Memory\sessions"
$recentFile = "$sessionDir\recent-sessions.md"

Write-Host "=== 加载会话记忆 ===" -ForegroundColor Cyan

if (Test-Path $recentFile) {
    $content = Get-Content $recentFile -Raw
    
    # 提取快速参考表格
    if ($content -match "## 快速参考([\s\S]*?)##") {
        Write-Host "`n最近会话:" -ForegroundColor Yellow
        $matches[1].Trim() -split "`n" | Select-Object -First 15 | ForEach-Object {
            Write-Host $_
        }
    }
    
    # 提取模式库
    if ($content -match "## 模式库([\s\S]*?)##") {
        Write-Host "`n复用模式:" -ForegroundColor Yellow
        $matches[1].Trim() -split "`n" | Select-Object -First 20 | ForEach-Object {
            if ($_.Trim() -and $_ -notmatch "^-+$") {
                Write-Host $_
            }
        }
    }
} else {
    Write-Host "暂无会话记忆" -ForegroundColor Gray
}

Write-Host "`n=== 记忆加载完成 ===" -ForegroundColor Cyan
