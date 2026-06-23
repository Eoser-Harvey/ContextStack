# 家里自动同步脚本 — 每日凌晨 3:00 执行
# 用法: Windows 任务计划程序 → 每日 3:00 → powershell -File "...\auto_push_home.ps1"
# 网络容错: 3次重试 + 指数退避 + VPN代理清理 + HTTPS→SSH回退

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoPath  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logFile   = Join-Path $scriptDir "auto_push_home.log"
$env:GIT_TERMINAL_PROMPT = 0
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $logFile -Value "=== $timestamp ==="

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Set-Location $repoPath

# === Step 0: Proxy Detection & Cleanup =======================================
$vpnProxy = $null
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
$env:http_proxy = $null
$env:https_proxy = $null
$env:ALL_PROXY  = $null
$env:all_proxy  = $null

$proxyPorts = @(7890, 10809, 1080)
foreach ($port in $proxyPorts) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $async = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
        if ($async.AsyncWaitHandle.WaitOne(1000)) {
            $tcp.EndConnect($async)
            $tcp.Close()
            $vpnProxy = "127.0.0.1:$port"
            Add-Content -Path $logFile -Value "Step 0: VPN proxy alive at $vpnProxy"
            $env:HTTPS_PROXY = "http://$vpnProxy"
            $env:HTTP_PROXY  = "http://$vpnProxy"
            break
        }
        $tcp.Close()
    } catch {}
}

try {
    $proxyReg = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyServer -ErrorAction SilentlyContinue
    if ($proxyReg.ProxyServer -match '^127\.0\.0\.1:\d+' -and -not $vpnProxy) {
        Add-Content -Path $logFile -Value "Step 0: Clearing dead VPN proxy residual ($($proxyReg.ProxyServer))"
        Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyServer -ErrorAction SilentlyContinue
    }
} catch {}

if ($vpnProxy) {
    Add-Content -Path $logFile -Value "Step 0: Will use VPN proxy for git"
} else {
    Add-Content -Path $logFile -Value "Step 0: No VPN proxy detected, using direct connection"
}

# === Step 0.5: SSH Fallback Setup ============================================
function Initialize-SshFallback {
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
            Add-Content -Path $logFile -Value "Step 0.5: SSH config written to ~/.ssh/config"
        }
    } catch {
        Add-Content -Path $logFile -Value "Step 0.5: SSH config write skipped ($($_.Exception.Message))"
    }

    $existingRemotes = git remote 2>&1
    if ($existingRemotes -notmatch 'origin-ssh') {
        git remote add origin-ssh git@github-ssh:Eoser-Harvey/ContextStack.git 2>&1 | Out-Null
        Add-Content -Path $logFile -Value "Step 0.5: origin-ssh remote added"
    }
}

function Test-SshReachable {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $async = $tcp.BeginConnect("ssh.github.com", 443, $null, $null)
        $result = $async.AsyncWaitHandle.WaitOne(2000)
        if ($result) { $tcp.EndConnect($async) }
        $tcp.Close()
        return $result
    } catch {
        return $false
    }
}

Initialize-SshFallback

# === Step 1: Pull with Retry + SSH Fallback ==================================
function Invoke-GitPull {
    $maxRetries = 3
    $retryDelays = @(10, 30, 60)

    $gitExtraArgs = @()
    if (-not $script:vpnProxy) {
        $gitExtraArgs = @("-c", "http.proxy=", "-c", "https.proxy=")
    }

    # Phase A: Try HTTPS
    for ($i = 0; $i -lt $maxRetries; $i++) {
        if ($i -gt 0) {
            Add-Content -Path $logFile -Value "Step 1: HTTPS retry $i after $($retryDelays[$i-1])s..."
            Start-Sleep -Seconds $retryDelays[$i-1]
        }

        if (-not (Test-GitHubReachable)) {
            Add-Content -Path $logFile -Value "Step 1: GitHub HTTPS unreachable (attempt $($i+1)/$maxRetries)"
            continue
        }

        Add-Content -Path $logFile -Value "Step 1: git pull (HTTPS)..."
        $pullOutput = & git @gitExtraArgs -c http.lowSpeedLimit=0 -c http.lowSpeedTime=60 pull origin master 2>&1
        $ec = $LASTEXITCODE

        if ($ec -eq 0) {
            if ($pullOutput -match "Already up to date") {
                Add-Content -Path $logFile -Value "Pull: Already up to date."
            } else {
                Add-Content -Path $logFile -Value "Pull: $pullOutput"
            }
            return $true
        }
        Add-Content -Path $logFile -Value "Pull HTTPS failed (attempt $($i+1)/$maxRetries): $($pullOutput -replace '\n',' ')"
    }

    # Phase B: Fallback to SSH over port 443
    if (Test-SshReachable) {
        Add-Content -Path $logFile -Value "Step 1: HTTPS exhausted, trying SSH over port 443..."

        for ($i = 0; $i -lt $maxRetries; $i++) {
            if ($i -gt 0) {
                Add-Content -Path $logFile -Value "Step 1: SSH retry $i after $($retryDelays[$i-1])s..."
                Start-Sleep -Seconds $retryDelays[$i-1]
            }

            Add-Content -Path $logFile -Value "Step 1: git pull (SSH)..."
            $pullOutput = & git pull origin-ssh master 2>&1
            $ec = $LASTEXITCODE

            if ($ec -eq 0) {
                if ($pullOutput -match "Already up to date") {
                    Add-Content -Path $logFile -Value "Pull (SSH): Already up to date."
                } else {
                    Add-Content -Path $logFile -Value "Pull (SSH): $pullOutput"
                }
                Add-Content -Path $logFile -Value "Step 1: SSH fallback SUCCESS"
                return $true
            }
            Add-Content -Path $logFile -Value "Pull SSH failed (attempt $($i+1)/$maxRetries): $($pullOutput -replace '\n',' ')"
        }
    } else {
        Add-Content -Path $logFile -Value "Step 1: SSH port 443 also unreachable, giving up"
    }

    Add-Content -Path $logFile -Value "PULL FAILED after exhausting HTTPS + SSH"
    Add-Content -Path $logFile -Value ""
    return $false
}

function Test-GitHubReachable {
    try {
        $response = Invoke-WebRequest -Uri "https://github.com" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

if (-not (Invoke-GitPull)) { exit 1 }

# === Step 2: Push any already-committed changes first =========================
$commitsAhead = [int](& git rev-list --count origin/master..HEAD 2>&1)
if ($commitsAhead -gt 0) {
    Add-Content -Path $logFile -Value "Step 2: $commitsAhead committed but un-pushed, pushing..."
    $gitExtraArgs = @()
    if (-not $script:vpnProxy) { $gitExtraArgs = @("-c", "http.proxy=", "-c", "https.proxy=") }
    try {
        $pushOutput = & git @gitExtraArgs -c http.lowSpeedLimit=0 -c http.lowSpeedTime=60 push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Add-Content -Path $logFile -Value "Push OK: $pushOutput"
            Add-Content -Path $logFile -Value ""
            exit 0
        }
        # HTTPS failed, try SSH
        if (Test-SshReachable) {
            $pushOutput = & git push origin-ssh master 2>&1
            if ($LASTEXITCODE -eq 0) {
                Add-Content -Path $logFile -Value "Push OK (SSH): $pushOutput"
                Add-Content -Path $logFile -Value ""
                exit 0
            }
        }
        Add-Content -Path $logFile -Value "Push of ahead commits FAILED: $($pushOutput -replace '\n',' ')"
    } catch {
        Add-Content -Path $logFile -Value "Push of ahead commits FAILED: $_"
    }
}

# === Step 3: Check for local changes (uncommitted) ============================
$status = git status --porcelain
if (-not $status) {
    Add-Content -Path $logFile -Value "No local changes to push."
    Add-Content -Path $logFile -Value ""
    exit 0
}

# === Step 3.5: Auto-cleanup temp test files ==================================
$tempCleaned = $false
Get-ChildItem $repoPath -File -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '^\.(test|verify|tmp|x)[.\-]' -and $_.Length -lt 500
} | ForEach-Object {
    Add-Content -Path $logFile -Value "Cleanup: removing temp file '$($_.Name)'"
    Remove-Item $_.FullName -Force
    $tempCleaned = $true
}
if ($tempCleaned) {
    $status = git status --porcelain
    if (-not $status) {
        Add-Content -Path $logFile -Value "Only temp files existed, cleaned. Nothing to push."
        Add-Content -Path $logFile -Value ""
        exit 0
    }
}

# === Step 4: Generate commit message =========================================
$rawFiles = @($status -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })

$groups = @{}

foreach ($line in $rawFiles) {
    if ($line -match '^(.{1,2})\s+(.+)$') {
        $stFlag = $matches[1].Trim()
        $filePath = $matches[2]
        if ($filePath -match '"([^"]+)"') { $filePath = $matches[1] }

        if ($stFlag -match '^\?')  { $action = 'add' }
        elseif ($stFlag -match 'D') { $action = 'delete' }
        else                        { $action = 'modify' }

        $topDir = if ($filePath -match '^([^/\\]+)[/\\]') { $matches[1] } else { '(root)' }
        $key = "$action|$topDir"
        if (-not $groups.ContainsKey($key)) { $groups[$key] = 0 }
        $groups[$key]++
    }
}

$parts = @()
foreach ($key in ($groups.Keys | Sort-Object)) {
    $action, $dir = $key -split '\|'
    $count = $groups[$key]
    $parts += "$action $dir ($count)"
}

$commitMsg = if ($parts.Count -gt 0) { "auto: " + ($parts -join ", ") } else { "auto: changes" }

git add -A
$commitOutput = & git commit -m $commitMsg 2>&1
if ($LASTEXITCODE -eq 0) {
    Add-Content -Path $logFile -Value "Commit OK: $commitMsg"
} else {
    Add-Content -Path $logFile -Value "Commit FAILED: $commitOutput"
    Add-Content -Path $logFile -Value ""
    exit 1
}

# === Step 5: Push with Retry + SSH Fallback ==================================
$maxPushRetries = 3
$pushRetryDelays = @(10, 30, 60)

$gitExtraArgs = @()
if (-not $script:vpnProxy) {
    $gitExtraArgs = @("-c", "http.proxy=", "-c", "https.proxy=")
}

# Phase A: Try HTTPS
$httpsPushed = $false
for ($i = 0; $i -lt $maxPushRetries; $i++) {
    if ($i -gt 0) {
        Add-Content -Path $logFile -Value "Step 5: HTTPS retry $i after $($pushRetryDelays[$i-1])s..."
        Start-Sleep -Seconds $pushRetryDelays[$i-1]
    }

    if (-not (Test-GitHubReachable)) {
        Add-Content -Path $logFile -Value "Step 5: GitHub HTTPS unreachable (attempt $($i+1)/$maxPushRetries)"
        continue
    }

    try {
        $pushOutput = & git @gitExtraArgs -c http.lowSpeedLimit=0 -c http.lowSpeedTime=60 push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Add-Content -Path $logFile -Value "Commit: $commitMsg"
            Add-Content -Path $logFile -Value "Push OK (HTTPS): $pushOutput"
            Add-Content -Path $logFile -Value ""
            $httpsPushed = $true
            break
        } else {
            Add-Content -Path $logFile -Value "Push HTTPS failed (attempt $($i+1)/$maxPushRetries): $($pushOutput -replace '\n',' ')"
        }
    } catch {
        Add-Content -Path $logFile -Value "Push HTTPS failed (attempt $($i+1)/$maxPushRetries): $_"
    }
}

if (-not $httpsPushed) {
    # Phase B: Fallback to SSH over port 443
    if (Test-SshReachable) {
        Add-Content -Path $logFile -Value "Step 5: HTTPS exhausted, trying SSH over port 443..."

        for ($i = 0; $i -lt $maxPushRetries; $i++) {
            if ($i -gt 0) {
                Add-Content -Path $logFile -Value "Step 5: SSH retry $i after $($pushRetryDelays[$i-1])s..."
                Start-Sleep -Seconds $pushRetryDelays[$i-1]
            }

            try {
                $pushOutput = & git push origin-ssh master 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Add-Content -Path $logFile -Value "Commit: $commitMsg"
                    Add-Content -Path $logFile -Value "Push OK (SSH): $pushOutput"
                    git fetch origin-ssh master:refs/remotes/origin/master 2>&1 | Out-Null
                    Add-Content -Path $logFile -Value ""
                    $httpsPushed = $true
                    break
                } else {
                    Add-Content -Path $logFile -Value "Push SSH failed (attempt $($i+1)/$maxPushRetries): $($pushOutput -replace '\n',' ')"
                }
            } catch {
                Add-Content -Path $logFile -Value "Push SSH failed (attempt $($i+1)/$maxPushRetries): $_"
            }
        }
    } else {
        Add-Content -Path $logFile -Value "Step 5: SSH port 443 also unreachable, giving up"
    }
}

if ($httpsPushed) {
    exit 0
} else {
    Add-Content -Path $logFile -Value "PUSH FAILED after exhausting HTTPS + SSH"
    Add-Content -Path $logFile -Value ""
    exit 1
}