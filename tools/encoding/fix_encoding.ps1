# 修复文件乱码字符
# 用法: powershell -ExecutionPolicy Bypass -File fix_encoding.ps1 [-FilePath "路径"]
#
# 此脚本用于修复因编码冲突导致的文件乱码问题。
# 常见乱码类型：UTF-8被Latin-1/CP1252错误解码后再保存导致的字符缺失/变形。

param(
    [string]$FilePath = ""
)

# 如果指定了文件路径，则修复该文件
if ($FilePath -ne "") {
    if (-not (Test-Path $FilePath)) {
        Write-Host "错误: 文件不存在 - $FilePath"
        exit 1
    }
    
    $content = Get-Content $FilePath -Raw -Encoding UTF8
    
    # 通用乱码修复映射表
    $replacements = @{
        "跾" = "路径"
        "盠" = "目标"
        "盽" = "目录"
        "盷" = "台"
        "圼" = "在"
        "臊" = "须"
        "竏" = "端口"
        "丼" = "演"
        "參" = "操作"
        "诓" = "错误"
        "版朎" = "版本控制"
        "持绛" = "持续更新"
    }
    
    foreach ($key in $replacements.Keys) {
        $content = $content -replace $key, $replacements[$key]
    }
    
    Set-Content $FilePath $content -Encoding UTF8
    Write-Host "文件修复完成: $FilePath"
    exit 0
}

# 如果没有指定文件，扫描整个 ContextStack 目录
Write-Host "扫描 ContextStack 目录中的乱码文件..."

$garbledPatterns = @(
    "跾", "盠", "盽", "盷", "圼", "臊", "竏", "丼", "參", "诓",
    "版朎", "持绛", "项盷", "盷作"
)

$foundFiles = @()

Get-ChildItem -Path "D:\MyFile\AI\ContextStack" -Recurse -Include "*.md","*.ps1","*.bat","*.py","*.txt" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($content) {
        foreach ($pattern in $garbledPatterns) {
            if ($content -match $pattern) {
                $foundFiles += $_.FullName
                break
            }
        }
    }
}

if ($foundFiles.Count -eq 0) {
    Write-Host "✅ 未发现乱码文件"
} else {
    Write-Host "❌ 发现 $($foundFiles.Count) 个乱码文件:"
    $foundFiles | ForEach-Object {
        Write-Host "  - $_"
    }
    Write-Host ""
    Write-Host "运行以下命令修复:"
    Write-Host "  powershell -File fix_encoding.ps1 -FilePath `<文件路径`>"
}
