# 家里自动同步脚本 — 每日凌晨 3:00 执行
# 用法: Windows 任务计划程序 → 每日 3:00 → powershell -File "...\auto_push_home.ps1"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoPath  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logFile   = Join-Path $scriptDir "auto_push_home.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $logFile -Value "=== $timestamp ==="

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Set-Location $repoPath

# === Step 1: Pull ============================================================
Add-Content -Path $logFile -Value "Step 1: git pull..."
$pullOutput = git pull origin master 2>&1

if ($LASTEXITCODE -ne 0) {
    Add-Content -Path $logFile -Value "PULL FAILED (conflict or error): $pullOutput"
    Add-Content -Path $logFile -Value ""
    exit 1
}

if ($pullOutput -match "Already up to date") {
    Add-Content -Path $logFile -Value "Pull: Already up to date."
} else {
    Add-Content -Path $logFile -Value "Pull: $pullOutput"
}

# === Step 2: Check for local changes =========================================
$status = git status --porcelain
if (-not $status) {
    Add-Content -Path $logFile -Value "No local changes to push."
    Add-Content -Path $logFile -Value ""
    exit 0
}

# === Step 3: Generate commit message =========================================
$files = @($status -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
$fileCount = $files.Count

$dirs   = @($files | ForEach-Object {
    $path = $_ -replace '^\S+\s+', ''
    if ($path -match '^(.+?)/') { $matches[1] } else { '(root)' }
} | Sort-Object -Unique)

$exts   = @($files | ForEach-Object {
    $path = $_ -replace '^\S+\s+', ''
    if ($path -match '\.(\w+)$') { ".$($matches[1])" } else { '(no-ext)' }
} | Sort-Object -Unique)

$dirSummary  = ($dirs | Select-Object -First 4) -join ", "
if ($dirs.Count -gt 4) { $dirSummary += ", ..." }
$extSummary  = ($exts -join " ") -replace '^//', '/'
$commitMsg   = "auto: [$fileCount files] $dirSummary ($extSummary)"

git add -A
git commit -m $commitMsg 2>&1 | Out-Null

# === Step 4: Push ============================================================
try {
    $pushOutput = git push origin master 2>&1
    Add-Content -Path $logFile -Value "Commit: $commitMsg"
    Add-Content -Path $logFile -Value "Push OK: $pushOutput"
} catch {
    Add-Content -Path $logFile -Value "Push FAILED: $_"
}

Add-Content -Path $logFile -Value ""