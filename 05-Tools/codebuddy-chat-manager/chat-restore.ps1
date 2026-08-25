#requires -Version 5.1
<#
.SYNOPSIS
    按清单选择性地把 CodeBuddy 会话迁移到目标账户。
.DESCRIPTION
    从 chat-index.json 读取会话清单，交互选择会话，
    复制会话文件夹到目标账户对应位置，并合并目标 index.json（自动先备份）。
    可选 -Export 在脚本目录 data-export\ 留一份实体备份。
    注意: 执行前请完全关闭 CodeBuddy IDE。
.EXAMPLE
    .\chat-restore.ps1
.EXAMPLE
    .\chat-restore.ps1 -Select 1,3-5 -TargetAccount xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx -DryRun
.EXAMPLE
    .\chat-restore.ps1 -Account 2a2e1d62 -Export
#>
[CmdletBinding()]
param(
    [string]$DataRoot      = (Join-Path $env:LOCALAPPDATA 'CodeBuddyExtension\Data'),
    [string]$IndexFile     = (Join-Path $PSScriptRoot 'chat-index.json'),
    [string]$Account,
    [string]$TargetAccount,
    [string]$Select,
    [switch]$Export,
    [switch]$Rescan,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# ---------- 工具函数（与 chat-index.ps1 相同，保持脚本独立可运行） ----------
function Get-DisplayWidth {
    param([string]$Text)
    if ($null -eq $Text) { return 0 }
    $w = 0
    foreach ($ch in $Text.ToCharArray()) {
        if ([int]$ch -ge 0x2E80) { $w += 2 } else { $w += 1 }
    }
    return $w
}

function Format-Cell {
    param([string]$Text, [int]$Width)
    $pad = $Width - (Get-DisplayWidth $Text)
    if ($pad -lt 0) { $pad = 0 }
    return $Text + (' ' * $pad)
}

function Split-TruncatedName {
    param([string]$Text, [int]$MaxWidth)
    if ((Get-DisplayWidth $Text) -le $MaxWidth) { return $Text }
    $sb = New-Object System.Text.StringBuilder
    $w = 0
    foreach ($ch in $Text.ToCharArray()) {
        $cw = 1
        if ([int]$ch -ge 0x2E80) { $cw = 2 }
        if (($w + $cw) -gt ($MaxWidth - 3)) { break }
        [void]$sb.Append($ch)
        $w += $cw
    }
    return ($sb.ToString() + '...')
}

function ConvertTo-PlainObject {
    param($InputObject)
    if ($null -eq $InputObject) { return $null }
    if ($InputObject -is [string]) { return ([string]$InputObject) }
    if ($InputObject -is [System.Collections.IDictionary]) {
        $d = [ordered]@{}
        foreach ($k in $InputObject.Keys) { $d[$k] = ConvertTo-PlainObject $InputObject[$k] }
        return $d
    }
    if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
        $list = New-Object System.Collections.ArrayList
        foreach ($i in $InputObject) { [void]$list.Add((ConvertTo-PlainObject $i)) }
        return $list
    }
    if ($InputObject -is [pscustomobject]) {
        $d = [ordered]@{}
        foreach ($p in $InputObject.PSObject.Properties) { $d[$p.Name] = ConvertTo-PlainObject $p.Value }
        return $d
    }
    return $InputObject
}

function Get-JsonSerializer {
    Add-Type -AssemblyName System.Web.Extensions
    $ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $ser.MaxJsonLength = [int]::MaxValue
    return $ser
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Read-JsonFile {
    param([string]$Path)
    $s = Get-JsonSerializer
    $raw = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    return $s.DeserializeObject($raw)
}

function Parse-Selection {
    param([string]$Text, [int]$Max)
    $result = @{}
    foreach ($part in ($Text -split ',')) {
        $p = $part.Trim()
        if ($p -match '^(\d+)$') {
            $n = [int]$Matches[1]
            if ($n -ge 1 -and $n -le $Max) { $result[$n] = $true }
        } elseif ($p -match '^(\d+)\s*-\s*(\d+)$') {
            $a = [int]$Matches[1]
            $b = [int]$Matches[2]
            if ($a -gt $b) { $tmp = $a; $a = $b; $b = $tmp }
            for ($n = $a; $n -le $b; $n++) {
                if ($n -ge 1 -and $n -le $Max) { $result[$n] = $true }
            }
        }
    }
    return @($result.Keys | Sort-Object)
}

# ---------- 0. IDE 运行检查 ----------
if (-not $DryRun -and -not $Force) {
    $procs = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'codebuddy|workbuddy' })
    if ($procs.Count -gt 0) {
        $names = ($procs | Select-Object -ExpandProperty ProcessName -Unique) -join ', '
        Write-Host ''
        Write-Host "检测到 CodeBuddy 相关进程正在运行: $names" -ForegroundColor Yellow
        Write-Host '恢复会写入目标账户的 index.json，IDE 退出时可能用内存状态覆写，导致恢复失效。'
        Write-Host '请先完全关闭 CodeBuddy IDE 再执行；已了解风险可加 -Force 跳过本检查。'
        exit 1
    }
}

# ---------- 1. 清单准备 ----------
if ($Rescan -or -not (Test-Path $IndexFile)) {
    Write-Host '正在重新扫描生成清单...'
    & (Join-Path $PSScriptRoot 'chat-index.ps1') -DataRoot $DataRoot -OutDir $PSScriptRoot
    $IndexFile = Join-Path $PSScriptRoot 'chat-index.json'
}
if (-not (Test-Path $IndexFile)) { throw "清单文件不存在: $IndexFile" }

$ser = Get-JsonSerializer
$data = Read-JsonFile -Path $IndexFile
$convs = @($data['conversations'])

# 从清单统计每个账户的会话数与最近消息时间（用于目标账户识别，免记 UUID）
$acctCnt = @{}
$acctLatest = @{}
foreach ($c in $convs) {
    $aid = [string]$c['accountId']
    if (-not $acctCnt.ContainsKey($aid)) { $acctCnt[$aid] = 0; $acctLatest[$aid] = '' }
    $acctCnt[$aid] = $acctCnt[$aid] + 1
    $lm = [string]$c['lastMessageAt']
    if ($lm -and ($acctLatest[$aid] -eq '' -or $lm -gt $acctLatest[$aid])) { $acctLatest[$aid] = $lm }
}

Write-Host "清单生成于: $($data['generatedAt'])  共 $($convs.Count) 个会话"
if ($Account) {
    $convs = @($convs | Where-Object { [string]$_['accountId'] -like "$Account*" })
    Write-Host "按账户前缀 '$Account' 过滤后: $($convs.Count) 个"
}
if ($convs.Count -eq 0) { Write-Host '没有匹配的会话。'; exit 0 }

# ---------- 2. 会话列表 ----------
Write-Host ''
Write-Host '会话列表 (按最后消息时间倒序):'
$i = 0
foreach ($c in $convs) {
    $i++
    $nm = ([string]$c['name']) -replace '\s+', ' '
    $nm = Split-TruncatedName $nm 30
    $t = [string]$c['lastMessageAt']
    if ($t.Length -ge 19) { $t = $t.Substring(0, 19).Replace('T', ' ') }
    $acc = ([string]$c['accountId']).Substring(0, 8)
    $line = '  [{0,3}] {1}' -f $i, (Format-Cell $nm 30)
    $line += " 账户:$acc  $t  消息:$($c['messageFiles'])  $($c['sizeMB'])MB"
    Write-Host $line
}

# ---------- 3. 选择会话 ----------
if (-not $Select) {
    $Select = Read-Host '输入编号 (如 1,3,5-8 / all / q 退出)'
}
if ($Select -match '^(q|quit|exit)$') { Write-Host '已取消。'; exit 0 }
if ($Select.Trim().ToLower() -eq 'all') { $Select = "1-$($convs.Count)" }
$selIdx = @(Parse-Selection -Text $Select -Max $convs.Count)
if ($selIdx.Count -eq 0) { throw "未解析到有效编号: $Select" }

# ---------- 4. 选择目标账户 ----------
$accountDirs = @(Get-ChildItem $DataRoot -Directory | Where-Object { $_.Name -notin @('default', 'Public') } | Sort-Object LastWriteTime -Descending)
if (-not $TargetAccount) {
    Write-Host ''
    Write-Host '目标账户列表 (按最近活跃排序; 看「会话数 / 最近消息」认账户, 不用记 UUID):'
    $j = 0
    foreach ($a in $accountDirs) {
        $j++
        $aid = $a.Name
        $cnt = if ($acctCnt.ContainsKey($aid)) { $acctCnt[$aid] } else { 0 }
        $lat = '(无会话)'
        if ($acctLatest.ContainsKey($aid) -and $acctLatest[$aid]) {
            $lat = $acctLatest[$aid].Substring(0, [Math]::Min(19, $acctLatest[$aid].Length)).Replace('T', ' ')
        }
        Write-Host ('  [{0}] {1}' -f $j, $aid)
        Write-Host ("        会话数: {0,3}   最近消息: {1}" -f $cnt, $lat)
    }
    Write-Host '  提示: 刚登录/较新的账户通常会话数最少、目录写入时间最新'
    $pick = Read-Host '选择目标账户序号'
    if ($pick -notmatch '^\d+$') { throw '无效输入' }
    $pi = [int]$pick
    if ($pi -lt 1 -or $pi -gt $accountDirs.Count) { throw '序号超出范围' }
    $TargetAccount = $accountDirs[$pi - 1].Name
}
$targetRoot = Join-Path $DataRoot $TargetAccount
if (-not (Test-Path $targetRoot)) {
    throw "目标账户目录不存在: $targetRoot`n新账户需要先在 CodeBuddy 登录一次，生成目录后再执行。"
}

# ---------- 5. 确认 ----------
Write-Host ''
Write-Host "计划: 恢复 $($selIdx.Count) 个会话 -> 账户 $TargetAccount"
if ($Export) { Write-Host '      同时导出实体到 data-export\' }
if ($DryRun) { Write-Host '      [DryRun] 只打印计划，不写入任何文件' }
if (-not $DryRun -and -not $Force) {
    $confirm = Read-Host '确认执行? (y/N)'
    if ($confirm -notmatch '^(y|yes)$') { Write-Host '已取消。'; exit 0 }
}

# ---------- 6. 执行 ----------
$results = New-Object System.Collections.ArrayList
foreach ($n in $selIdx) {
    $c = $convs[$n - 1]
    $cid   = [string]$c['conversationId']
    $cname = [string]$c['name']
    $srcDir = [string]$c['sourcePath']
    $dstGroup   = Join-Path $targetRoot (Join-Path ([string]$c['client']) (Join-Path ([string]$c['workspaceDir']) (Join-Path 'history' ([string]$c['groupHash']))))
    $dstConvDir = Join-Path $dstGroup $cid
    $dstIndex   = Join-Path $dstGroup 'index.json'

    $status = 'OK'
    $note = ''
    try {
        if (-not (Test-Path $srcDir)) { throw "源目录不存在: $srcDir (清单可能已过时，请重跑 chat-index.ps1)" }

        if ($DryRun) {
            $status = 'DRYRUN'
            $note = "$srcDir`n           -> $dstConvDir"
        } else {
            # 6.1 目标目录
            New-Item -ItemType Directory -Force -Path $dstGroup | Out-Null

            # 6.2 从源 index.json 取会话条目（保留全部原字段）
            $srcIndex = Join-Path (Split-Path $srcDir -Parent) 'index.json'
            $srcData = Read-JsonFile -Path $srcIndex
            $srcEntry = $null
            foreach ($e in @($srcData['conversations'])) {
                if ([string]$e['id'] -eq $cid) { $srcEntry = $e; break }
            }
            if ($null -eq $srcEntry) { throw '源 index.json 中找不到该会话条目' }

            # 6.3 备份并合并目标 index.json
            if (Test-Path $dstIndex) {
                $bak = "$dstIndex.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                Copy-Item $dstIndex $bak -Force
                $dstData = Read-JsonFile -Path $dstIndex
            } else {
                $dstData = [ordered]@{ conversations = (New-Object System.Collections.ArrayList) }
            }
            $dstConvs = $dstData['conversations']
            if ($null -eq $dstConvs) {
                $dstConvs = New-Object System.Collections.ArrayList
                $dstData['conversations'] = $dstConvs
            }
            $existAt = -1
            for ($k = 0; $k -lt $dstConvs.Count; $k++) {
                if ([string]$dstConvs[$k]['id'] -eq $cid) { $existAt = $k; break }
            }
            if ($existAt -ge 0) { $dstConvs[$existAt] = $srcEntry } else { [void]$dstConvs.Add($srcEntry) }
            Write-Utf8NoBom -Path $dstIndex -Content ($ser.Serialize((ConvertTo-PlainObject $dstData)))

            # 6.4 复制会话文件夹
            $null = & robocopy "$srcDir" "$dstConvDir" /E /NFL /NDL /NJH /NJS /NP /R:1 /W:1
            if ($LASTEXITCODE -ge 8) { throw "robocopy 复制失败, 退出码 $LASTEXITCODE" }

            # 6.5 可选导出实体留底
            if ($Export) {
                $exportDir = Join-Path $PSScriptRoot (Join-Path 'data-export' (Join-Path ([string]$c['accountId']) (Join-Path ([string]$c['client']) (Join-Path ([string]$c['workspaceDir']) (Join-Path 'history' (Join-Path ([string]$c['groupHash']) $cid))))))
                $null = & robocopy "$srcDir" "$exportDir" /E /NFL /NDL /NJH /NJS /NP /R:1 /W:1
                if ($LASTEXITCODE -ge 8) { throw "导出失败, robocopy 退出码 $LASTEXITCODE" }
            }
            $note = "-> $dstConvDir"
        }
    } catch {
        $status = 'FAIL'
        $note = $_.Exception.Message
    }
    [void]$results.Add([ordered]@{ no = $n; name = $cname; id = $cid; status = $status; note = $note })
}

# ---------- 7. 汇总 ----------
Write-Host ''
Write-Host '执行结果:'
foreach ($r in $results) {
    $rname = ([string]$r['name']) -replace '\s+', ' '
    Write-Host ('  [{0,-6}] #{1} {2}' -f $r['status'], $r['no'], (Split-TruncatedName $rname 40))
    if ($r['note']) { Write-Host "           $($r['note'])" }
}
$okCount   = @($results | Where-Object { $_['status'] -eq 'OK' }).Count
$failCount = @($results | Where-Object { $_['status'] -eq 'FAIL' }).Count
Write-Host ''
Write-Host "合计: 成功 $okCount, 失败 $failCount, 共 $($results.Count)"
if (-not $DryRun -and $okCount -gt 0) {
    Write-Host ''
    Write-Host '下一步: 启动 CodeBuddy IDE，切到目标账户即可看到恢复的会话。'
    Write-Host '提示: 目标 index.json 已自动备份为 .bak-时间戳 文件，异常时可手动回滚。'
}
