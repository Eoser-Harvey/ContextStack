# 单位自动同步脚本 — 每日 22:00 执行
# 用法: Windows 任务计划程序 → 每日 22:00 → powershell -File "...\auto_push.ps1"
# 网络容错: 3次重试 + 指数退避 + VPN代理清理

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoPath  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logFile   = Join-Path $scriptDir "auto_push.log"
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

# Check if VPN proxy is alive (common ports: 7890 Clash, 10809 V2Ray, 1080 SSR)
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

# Clean registry proxy residual if proxy is dead
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

function Test-GitHubReachable {
    try {
        $response = Invoke-WebRequest -Uri "https://github.com" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# === Step 1: Pull with Retry =================================================
function Invoke-GitPull {
    $maxRetries = 3
    $retryDelays = @(30, 60, 120)
    
    # Build git args: use proxy if VPN is alive, else disable
    $gitExtraArgs = @()
    if (-not $script:vpnProxy) {
        $gitExtraArgs = @("-c", "http.proxy=", "-c", "https.proxy=")
    }
    
    for ($i = 0; $i -lt $maxRetries; $i++) {
        if ($i -gt 0) {
            Add-Content -Path $logFile -Value "Step 1: Retry $i after $($retryDelays[$i-1])s..."
            Start-Sleep -Seconds $retryDelays[$i-1]
        }
        
        if (-not (Test-GitHubReachable)) {
            Add-Content -Path $logFile -Value "Step 1: GitHub unreachable (attempt $($i+1)/$maxRetries)"
            continue
        }
        
        Add-Content -Path $logFile -Value "Step 1: git pull..."
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
        
        Add-Content -Path $logFile -Value "Pull failed (attempt $($i+1)/$maxRetries): $pullOutput"
    }
    
    Add-Content -Path $logFile -Value "PULL FAILED after $maxRetries retries"
    Add-Content -Path $logFile -Value ""
    return $false
}

if (-not (Invoke-GitPull)) { exit 1 }

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

# === Step 4: Push with Retry =================================================
$maxPushRetries = 3
$pushRetryDelays = @(20, 60, 120)

# Build git args: use proxy if VPN is alive, else disable
$gitExtraArgs = @()
if (-not $script:vpnProxy) {
    $gitExtraArgs = @("-c", "http.proxy=", "-c", "https.proxy=")
}

for ($i = 0; $i -lt $maxPushRetries; $i++) {
    if ($i -gt 0) {
        Add-Content -Path $logFile -Value "Step 4: Retry $i after $($pushRetryDelays[$i-1])s..."
        Start-Sleep -Seconds $pushRetryDelays[$i-1]
    }
    
    if (-not (Test-GitHubReachable)) {
        Add-Content -Path $logFile -Value "Step 4: GitHub unreachable (attempt $($i+1)/$maxPushRetries)"
        continue
    }
    
    try {
        $pushOutput = & git @gitExtraArgs -c http.lowSpeedLimit=0 -c http.lowSpeedTime=60 push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Add-Content -Path $logFile -Value "Commit: $commitMsg"
            Add-Content -Path $logFile -Value "Push OK: $pushOutput"
            Add-Content -Path $logFile -Value ""
            exit 0
        } else {
            Add-Content -Path $logFile -Value "Push failed (attempt $($i+1)/$maxPushRetries): $pushOutput"
        }
    } catch {
        Add-Content -Path $logFile -Value "Push failed (attempt $($i+1)/$maxPushRetries): $_"
    }
}

Add-Content -Path $logFile -Value "PUSH FAILED after $maxPushRetries retries"
Add-Content -Path $logFile -Value ""
exit 1