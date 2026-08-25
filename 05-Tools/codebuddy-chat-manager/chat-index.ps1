#requires -Version 5.1
<#
.SYNOPSIS
    扫描 CodeBuddy 本地聊天记录，生成会话清单（chat-index.json / chat-index.md）。
.DESCRIPTION
    只生成索引清单，不复制任何聊天记录本体。
    数据源: %LOCALAPPDATA%\CodeBuddyExtension\Data
.EXAMPLE
    .\chat-index.ps1
#>
[CmdletBinding()]
param(
    [string]$DataRoot = (Join-Path $env:LOCALAPPDATA 'CodeBuddyExtension\Data'),
    [string]$OutDir   = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

# 兼容旧版 PowerShell 5.1：某些执行方式下 $PSScriptRoot 为空（如 cmd 直接调用/任务计划）
# 用脚本自身的实际路径兜底（$MyInvocation），不要用 Get-Location（任务计划默认工作目录是 System32）
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $PSScriptRoot = (Get-Location).Path
}
if ([string]::IsNullOrEmpty($OutDir)) {
    $OutDir = $PSScriptRoot
}

# ---------- 工具函数 ----------
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

function ConvertFrom-WorkspaceDirName {
    param([string]$Name)
    try {
        $b64 = $Name.Replace('-', '+').Replace('_', '/')
        $mod = $b64.Length % 4
        if ($mod -ne 0) { $b64 += ('=' * (4 - $mod)) }
        $bytes = [Convert]::FromBase64String($b64)
        $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
        if ($text -match '^[A-Za-z]:[\\/]') { return $text }
    } catch { }
    return $Name
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

# ---------- 1. 扫描 ----------
if (-not (Test-Path $DataRoot)) { throw "数据目录不存在: $DataRoot" }

$items = New-Object System.Collections.ArrayList
$accountDirs = Get-ChildItem $DataRoot -Directory | Where-Object { $_.Name -notin @('default', 'Public') }

foreach ($account in $accountDirs) {
    foreach ($client in (Get-ChildItem $account.FullName -Directory -ErrorAction SilentlyContinue)) {
        if ($client.Name -eq 'genie-cache') { continue }
        foreach ($ws in (Get-ChildItem $client.FullName -Directory -ErrorAction SilentlyContinue)) {
            $historyDir = Join-Path $ws.FullName 'history'
            if (-not (Test-Path $historyDir)) { continue }
            foreach ($group in (Get-ChildItem $historyDir -Directory -ErrorAction SilentlyContinue)) {
                $idxFile = Join-Path $group.FullName 'index.json'
                if (-not (Test-Path $idxFile)) { continue }
                try {
                    $idx = Get-Content $idxFile -Raw -Encoding UTF8 | ConvertFrom-Json
                } catch {
                    Write-Warning "索引解析失败，已跳过: $idxFile"
                    continue
                }
                foreach ($conv in @($idx.conversations)) {
                    $convDir = Join-Path $group.FullName $conv.id
                    $msgDir  = Join-Path $convDir 'messages'
                    $msgCount = 0
                    $sizeBytes = 0L
                    if (Test-Path $msgDir) {
                        $files = Get-ChildItem $msgDir -Filter '*.json' -File -ErrorAction SilentlyContinue
                        $msgCount = @($files).Count
                        $sum = ($files | Measure-Object -Property Length -Sum).Sum
                        if ($sum) { $sizeBytes = [long]$sum }
                    }
                    $model = ''
                    if ($conv.modelMap) {
                        $model = ($conv.modelMap.PSObject.Properties | ForEach-Object { $_.Value }) -join ','
                    }
                    [void]$items.Add([ordered]@{
                        accountId      = $account.Name
                        client         = $client.Name
                        workspace      = (ConvertFrom-WorkspaceDirName $ws.Name)
                        workspaceDir   = $ws.Name
                        groupHash      = $group.Name
                        conversationId = [string]$conv.id
                        name           = $(if ($conv.name) { [string]$conv.name } else { '(未命名)' })
                        type           = [string]$conv.type
                        model          = $model
                        createdAt      = [string]$conv.createdAt
                        lastMessageAt  = [string]$conv.lastMessageAt
                        messageFiles   = $msgCount
                        sizeMB         = [math]::Round($sizeBytes / 1MB, 2)
                        sourcePath     = [string]$convDir
                    })
                }
            }
        }
    }
}

$sorted = @($items | Sort-Object { $_['lastMessageAt'] } -Descending)

# ---------- 2. 写 chat-index.json ----------
$ser = Get-JsonSerializer
$payload = [ordered]@{
    generatedAt   = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    dataRoot      = $DataRoot
    totalSessions = $sorted.Count
    conversations = (ConvertTo-PlainObject $sorted)
}
$jsonPath = Join-Path $OutDir 'chat-index.json'
Write-Utf8NoBom -Path $jsonPath -Content ($ser.Serialize($payload))

# ---------- 3. 写 chat-index.md ----------
$headers = @('#', '会话名称', '账户', '客户端', '工作区', '最后消息时间', '消息数', '大小MB')
$rows = New-Object System.Collections.ArrayList
$i = 0
foreach ($c in $sorted) {
    $i++
    $nm = ([string]$c['name']) -replace '\s+', ' ' -replace '\|', '\|'
    $t = [string]$c['lastMessageAt']
    if ($t.Length -ge 19) { $t = $t.Substring(0, 19).Replace('T', ' ') }
    [void]$rows.Add(@(
        "$i",
        (Split-TruncatedName $nm 34),
        ([string]$c['accountId']).Substring(0, 8),
        [string]$c['client'],
        (Split-TruncatedName ([string]$c['workspace']) 26),
        $t,
        "$($c['messageFiles'])",
        "$($c['sizeMB'])"
    ))
}

$widths = @(0, 0, 0, 0, 0, 0, 0, 0)
for ($c = 0; $c -lt $headers.Count; $c++) {
    $widths[$c] = Get-DisplayWidth $headers[$c]
    foreach ($r in $rows) {
        $w = Get-DisplayWidth $r[$c]
        if ($w -gt $widths[$c]) { $widths[$c] = $w }
    }
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('# CodeBuddy 会话清单')
[void]$sb.AppendLine('')
[void]$sb.AppendLine("- 生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$sb.AppendLine("- 数据源: ``$DataRoot``")
[void]$sb.AppendLine("- 会话总数: $($sorted.Count)")
[void]$sb.AppendLine("- 本文件由 ``chat-index.ps1`` 自动生成，请勿手改")
[void]$sb.AppendLine('')

$line = '|'
for ($c = 0; $c -lt $headers.Count; $c++) { $line += ' ' + (Format-Cell $headers[$c] $widths[$c]) + '|' }
[void]$sb.AppendLine($line)
$sep = '|'
for ($c = 0; $c -lt $headers.Count; $c++) { $sep += ':' + ('-' * ($widths[$c] + 1)) + '|' }
[void]$sb.AppendLine($sep)
foreach ($r in $rows) {
    $line = '|'
    for ($c = 0; $c -lt $headers.Count; $c++) { $line += ' ' + (Format-Cell $r[$c] $widths[$c]) + '|' }
    [void]$sb.AppendLine($line)
}

$mdPath = Join-Path $OutDir 'chat-index.md'
Write-Utf8NoBom -Path $mdPath -Content $sb.ToString()

# ---------- 4. 摘要 ----------
Write-Host ''
Write-Host "扫描完成: 共 $($sorted.Count) 个会话 (数据源: $DataRoot)"
Write-Host "  JSON: $jsonPath"
Write-Host "  MD  : $mdPath"
