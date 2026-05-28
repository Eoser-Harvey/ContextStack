# 保存会话经验脚本
# 对话结束时执行，生成会话经验文件

param(
    [string]$Topic = "未指定",
    [string]$KeyLearning = "",
    [string]$Mistakes = "",
    [string]$Optimizations = "",
    [string]$Patterns = "",
    [string]$RelatedFiles = ""
)

$sessionDir = "e:\ProjectGroup\AI\ContextStack\03-Memory\sessions"
$timestamp = Get-Date -Format "yyyyMMdd-HHmm"
$dateStr = Get-Date -Format "yyyy-MM-dd HH:mm"

# 生成会话文件
$sessionFile = "$sessionDir\session-$timestamp.md"
$template = @"# 会话经验: $Topic

> 日期: $dateStr

---

## 元信息

- **会话日期**: $dateStr
- **对话主题**: $Topic
- **处理文件数**: (待填写)
- **用户反馈**: (待填写)

---

## 做对了什么（保持）

$KeyLearning

## 踩了什么坑（避免）

$Mistakes

## 下次怎么更快（优化）

$Optimizations

## 可复用的模式

$Patterns

---

## 关联文件

$RelatedFiles
"@

$template | Out-File -FilePath $sessionFile -Encoding UTF8
Write-Host "会话经验已保存: $sessionFile" -ForegroundColor Green

# 更新 recent-sessions.md
$recentFile = "$sessionDir\recent-sessions.md"
if (Test-Path $recentFile) {
    $content = Get-Content $recentFile -Raw
    
    # 提取关键经验（第一行）
    $keyLine = ($KeyLearning -split "`n")[0].Trim()
    if (-not $keyLine) { $keyLine = "(详见文件)" }
    
    # 添加到快速参考表格
    $newRow = "| $dateStr | $Topic | $keyLine | ``session-$timestamp.md`` |"
    
    # 在表格后插入新行
    $lines = $content -split "`n"
    $tableEnd = $lines | Select-String "^\|.*\|$" | Select-Object -Last 1 | Select-Object -ExpandProperty LineNumber
    
    if ($tableEnd) {
        $newLines = @()
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $newLines += $lines[$i]
            if ($i -eq $tableEnd - 1 -and $lines[$i] -match "^\|.*\|.*\|.*\|.*\|$" -and $lines[$i] -notmatch "^-+$") {
                $newLines += $newRow
            }
        }
        $newLines | Out-File -FilePath $recentFile -Encoding UTF8
        Write-Host "已更新 recent-sessions.md" -ForegroundColor Green
    }
}

Write-Host "`n提示: 请完善 session-$timestamp.md 中的细节" -ForegroundColor Yellow
