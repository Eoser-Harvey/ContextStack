# 自动同步脚本 — 每日 22:00 执行
# 用法: Windows 任务计划程序 → 每日 22:00 → powershell -File "...\auto_push.ps1"
# 公司电脑版：使用当前 origin 协议（HTTPS），不强制切换 SSH

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoPath  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logFile   = Join-Path $scriptDir "auto_push.log"
$env:GIT_TERMINAL_PROMPT = 0
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $logFile -Value "=== $timestamp ==="

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Set-Location $repoPath

# === Step 0: SSH Config Setup ===============================================
function Initialize-SshConfig {
    $sshConfigPath = "$env:USERPROFILE\.ssh\config"
    $sshConfigEntry = @"

Host github-ssh
    Hostname ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519_contextstack
    StrictHostKeyChecking accept-new
    ConnectTimeout 10

"@

    try {
        $existing = if (Test-Path $sshConfigPath) { Get-Content $sshConfigPath -Raw } else { "" }
        if ($existing -notmatch 'Host github-ssh') {
            Add-Content -Path $sshConfigPath -Value $sshConfigEntry -Encoding ASCII -ErrorAction Stop
            Add-Content -Path $logFile -Value "Step 0: SSH config written to ~/.ssh/config"
        }
    } catch {
        Add-Content -Path $logFile -Value "Step 0: SSH config write error ($($_.Exception.Message))"
    }

    # Ensure origin is SSH
    $originUrl = git remote get-url origin 2>&1
    if ($originUrl -notmatch 'git@github-ssh') {
        git remote set-url origin git@github-ssh:Eoser-Harvey/ContextStack.git 2>&1 | Out-Null
        Add-Content -Path $logFile -Value "Step 0: origin set to SSH"
    }

    # Remove legacy origin-ssh if exists
    $remotes = git remote 2>&1
    if ($remotes -match 'origin-ssh') {
        git remote remove origin-ssh 2>&1 | Out-Null
        Add-Content -Path $logFile -Value "Step 0: legacy origin-ssh removed"
    }
}

# Initialize-SshConfig  ← 已注释：公司电脑用HTTPS不强制切SSH

# === Step 1: Pull (2 retries) ================================================
$maxRetries = 2
$retryDelays = @(10, 30)
$pullOk = $false

for ($i = 0; $i -lt $maxRetries; $i++) {
    if ($i -gt 0) {
        Add-Content -Path $logFile -Value "Step 1: SSH retry $i after $($retryDelays[$i-1])s..."
        Start-Sleep -Seconds $retryDelays[$i-1]
    }

    Add-Content -Path $logFile -Value "Step 1: git pull (SSH)..."
    $pullOutput = & git pull origin master 2>&1
    $ec = $LASTEXITCODE

    if ($ec -eq 0) {
        if ($pullOutput -match "Already up to date") {
            Add-Content -Path $logFile -Value "Pull: Already up to date."
        } else {
            Add-Content -Path $logFile -Value "Pull: $pullOutput"
        }
        $pullOk = $true
        break
    }
    Add-Content -Path $logFile -Value "Pull failed ($($i+1)/$maxRetries): $($pullOutput -replace '\n',' ')"

    # Refresh SSH config on failure
    Initialize-SshConfig
}

if (-not $pullOk) {
    Add-Content -Path $logFile -Value "PULL FAILED after $maxRetries attempts"
    Add-Content -Path $logFile -Value ""
    exit 1
}

# === Step 2: Push any already-committed changes first =========================
$commitsAhead = [int](& git rev-list --count origin/master..HEAD 2>&1)
if ($commitsAhead -gt 0) {
    Add-Content -Path $logFile -Value "Step 2: $commitsAhead committed but un-pushed, pushing..."
    try {
        $pushOutput = & git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Add-Content -Path $logFile -Value "Push OK: $pushOutput"
            Add-Content -Path $logFile -Value ""
            exit 0
        } else {
            Add-Content -Path $logFile -Value "Push of ahead commits FAILED: $($pushOutput -replace '\n',' ')"
        }
    } catch {
        Add-Content -Path $logFile -Value "Push of ahead commits FAILED: $_"
    }
}

# === Step 3: Check for local changes (uncommitted) =========================================
$status = git status --porcelain
if (-not $status) {
    Add-Content -Path $logFile -Value "No local changes to push."
    Add-Content -Path $logFile -Value ""
    exit 0
}

# === Step 4: Generate commit message =========================================
$files = @($status -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
$fileCount = $files.Count

$dirs = @($files | ForEach-Object {
    $path = $_ -replace '^\S+\s+', ''
    if ($path -match '^(.+?)/') { $matches[1] } else { '(root)' }
} | Sort-Object -Unique)

$exts = @($files | ForEach-Object {
    $path = $_ -replace '^\S+\s+', ''
    if ($path -match '\.(\w+)$') { ".$($matches[1])" } else { 'no-ext' }
} | Sort-Object -Unique)

$dirSummary = ($dirs | Select-Object -First 4) -join ", "
if ($dirs.Count -gt 4) { $dirSummary += ", ..." }
$extSummary = ($exts -join " ") -replace '^//', '/'
$commitMsg  = "auto: [$fileCount files] $dirSummary ($extSummary)"

git add -A
# 防止误删：取消暂存所有删除操作（多电脑同步场景下删除需手动确认）
$deletedFiles = & git diff --cached --diff-filter=D --name-only 2>&1
if ($deletedFiles) {
    foreach ($f in ($deletedFiles -split "`n" | Where-Object { $_ -ne "" })) {
        & git reset HEAD -- $f 2>&1 | Out-Null
    }
    Add-Content -Path $logFile -Value "Step 3: Skipped auto-commit of deleted files"
}
$commitOutput = & git commit -m "$commitMsg" 2>&1
if ($LASTEXITCODE -eq 0) {
    Add-Content -Path $logFile -Value "Commit OK: $commitMsg"
} else {
    Add-Content -Path $logFile -Value "Commit FAILED: $commitOutput"
    Add-Content -Path $logFile -Value ""
    exit 1
}

# === Step 5: Push (2 retries) ==========================================
$pushOk = $false

for ($i = 0; $i -lt $maxRetries; $i++) {
    if ($i -gt 0) {
        Add-Content -Path $logFile -Value "Step 4: retry $i after $($retryDelays[$i-1])s..."
        Start-Sleep -Seconds $retryDelays[$i-1]
    }

    try {
        $pushOutput = & git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Add-Content -Path $logFile -Value "Push OK: $pushOutput"
            Add-Content -Path $logFile -Value ""
            $pushOk = $true
            break
        } else {
            Add-Content -Path $logFile -Value "Push failed ($($i+1)/$maxRetries): $($pushOutput -replace '\n',' ')"
        }
    } catch {
        Add-Content -Path $logFile -Value "Push failed ($($i+1)/$maxRetries): $_"
    }
}

if ($pushOk) {
    exit 0
} else {
    Add-Content -Path $logFile -Value "PUSH FAILED after $maxRetries attempts"
    Add-Content -Path $logFile -Value ""
    exit 1
}
