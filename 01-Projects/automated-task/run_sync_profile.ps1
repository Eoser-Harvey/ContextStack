# 每日0点个人画像归档同步任务包装脚本
# 用途: 调用 sync_profile_archive.py 生成 profile_archive 归档
#       新架构: config.yaml 不再硬编码 profile 段，所有分析实时从 archive 读取
# 调度: 通过 Windows 任务计划程序配置每天 00:00 执行

$scriptPath = Join-Path $PSScriptRoot "sync_profile_archive.py"

# 切换到工作目录
$workspace = "E:\ProjectGroup\AI\ContextStack"
Set-Location $workspace

# 执行同步脚本（静默模式，仅记录日志）
& python "$scriptPath"

# 退出码传递
exit $LASTEXITCODE
