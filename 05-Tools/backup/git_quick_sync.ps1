# 轻量 Git 同步 — 无长时间等待，适合交互触发
# 调用 auto_push_home.ps1 -Quick 被系统拦截时的替代方案
param([string]$LogFile = "auto_push_home.log")

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoPath  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logPath   = Join-Path $scriptDir $LogFile
$env:GIT_TERMINAL_PROMPT = 0

Set-Location $repoPath

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logPath -Value "=== $ts [quick-sync] ==="

# Step 1: Quick pull via SSH (skip HTTPS — this is what works at home)
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $async = $tcp.BeginConnect("ssh.github.com", 443, $null, $null)
    if ($async.AsyncWaitHandle.WaitOne(3000)) {
        $tcp.EndConnect($async)
        $tcp.Close()
        
        $pullResult = git pull origin-ssh master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Add-Content -Path $logPath -Value "Pull (SSH): $pullResult"
        } else {
            Add-Content -Path $logPath -Value "Pull SSH failed: $pullResult"
        }
    } else {
        $tcp.Close()
        Add-Content -Path $logPath -Value "SSH unreachable, skipping pull"
    }
} catch {
    Add-Content -Path $logPath -Value "SSH check failed: $_"
}

# Step 2: Check local changes
$status = git status --porcelain
if (-not $status) {
    Add-Content -Path $logPath -Value "No local changes."
    Add-Content -Path $logPath -Value ""
    Write-Output "OK: No local changes to sync."
    exit 0
}

# Step 3: Commit
$fileCount = ($status -split "`n" | Where-Object { $_.Trim() -ne "" }).Count
$commitMsg = "auto: [$fileCount files] quick-sync"
git add -A
git commit -m $commitMsg 2>&1 | Out-Null
Add-Content -Path $logPath -Value "Commit: $commitMsg"

# Step 4: Push via SSH
try {
    $pushResult = git push origin-ssh master 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Content -Path $logPath -Value "Push OK (SSH): $pushResult"
        Add-Content -Path $logPath -Value ""
        Write-Output "OK: Pushed $fileCount file(s) via SSH."
    } else {
        Add-Content -Path $logPath -Value "Push SSH failed: $pushResult"
        Write-Output "FAIL: Push failed."
    }
} catch {
    Add-Content -Path $logPath -Value "Push SSH error: $_"
    Write-Output "FAIL: Push error."
}
