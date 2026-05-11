$repoPath = "D:\MyFile\AI\ContextStack"
$logFile = "D:\MyFile\AI\ContextStack\tools\backup\auto_push.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $logFile -Value "=== $timestamp ==="

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Set-Location $repoPath

$status = git status --porcelain
if (-not $status) {
    Add-Content -Path $logFile -Value "No changes to push."
    exit 0
}

git add -A
$commitMsg = "auto: daily sync - $timestamp"
git commit -m $commitMsg 2>&1 | Out-Null

try {
    $pushOutput = git push origin master 2>&1
    Add-Content -Path $logFile -Value "Push OK: $pushOutput"
} catch {
    Add-Content -Path $logFile -Value "Push FAILED: $_"
}

Add-Content -Path $logFile -Value ""