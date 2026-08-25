#requires -Version 5.1
<#
.SYNOPSIS
    Relocate 4 conversations from workspace "5e856652" into current workspace "2a2e1d62".
.DESCRIPTION
    chat-restore.ps1 keeps the source workspace dir name, so imported sessions land
    in a separate "5e856652" workspace and are invisible in the current workspace.
    This script moves the 4 session folders into the current workspace and merges
    its index.json. Uses ConvertFrom-Json / ConvertTo-Json (no JavaScriptSerializer)
    to avoid the PSObject circular-reference serialization bug.
    IMPORTANT: close CodeBuddy IDE completely before running.
#>
$ErrorActionPreference = 'Stop'

$account = "2a2e1d62-de8b-4abb-87fe-af5f9a2ff441"
$group   = "25985284d3c02a370bb0b66e3fb1ece1"
$base    = "C:\Users\h31280\AppData\Local\CodeBuddyExtension\Data\$account\CodeBuddyIDE"
$dstWs   = "$base\2a2e1d62-de8b-4abb-87fe-af5f9a2ff441\history\$group"
$srcWs   = "$base\5e856652-1370-4b6e-993c-e2488f3569ed\history\$group"
$dstIdx  = "$dstWs\index.json"
$srcIdx  = "$srcWs\index.json"

function Read-Json([string]$p) {
    Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json
}
function Write-Json([string]$p, $obj) {
    $json = ConvertTo-Json -InputObject $obj -Depth 20
    [System.IO.File]::WriteAllText($p, $json, (New-Object System.Text.UTF8Encoding($false)))
}

if (-not (Test-Path $srcIdx)) { Write-Host "Source workspace not found, nothing to relocate: $srcIdx" -ForegroundColor Yellow; exit 0 }
if (-not (Test-Path $dstIdx)) { Write-Host "Target workspace index.json not found: $dstIdx" -ForegroundColor Red; exit 1 }

# 1. backup target index.json
$bak = "$dstIdx.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $dstIdx $bak -Force
Write-Host "Backed up -> $bak"

# 2. merge conversations (dedup by id)
$dst = Read-Json $dstIdx
$src = Read-Json $srcIdx
$merged = New-Object System.Collections.ArrayList
$seen = @{}
foreach ($c in @($dst.conversations)) { [void]$merged.Add($c); $seen[[string]$c.id] = $true }
$added = 0
foreach ($c in @($src.conversations)) {
    if (-not $seen.ContainsKey([string]$c.id)) { [void]$merged.Add($c); $seen[[string]$c.id] = $true; $added++ }
}
Write-Host "Merge: target=$($dst.conversations.Count) + added=$added = total=$($merged.Count)"

# 3. write back (current unchanged)
$new = [ordered]@{ conversations = @($merged.ToArray()); current = $dst.current }
Write-Json $dstIdx $new

# 4. move the 4 session folders
foreach ($c in @($src.conversations)) {
    $cid = [string]$c.id
    $s = "$srcWs\$cid"; $d = "$dstWs\$cid"
    if (Test-Path $s) {
        robocopy $s $d /E /MOVE /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
        Write-Host "Moved: $cid  exit=$LASTEXITCODE"
    } else {
        Write-Host "Skip (already moved): $cid"
    }
}

# 5. verify
$verify = Read-Json $dstIdx
Write-Host ""
Write-Host "Verify: target index.json now has $($verify.conversations.Count) conversations:"
foreach ($c in @($verify.conversations)) { Write-Host "  - $([string]$c.id)" }
Write-Host ""
Write-Host "DONE. Reopen CodeBuddy IDE and check the session list."
Write-Host "Rollback if needed: copy $bak back over $dstIdx"
