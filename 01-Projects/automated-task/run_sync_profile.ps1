# 每日0点个人画像同步任务包装脚本
# 用途: 调用 sync_profile_to_config.py 完成画像更新
# 调度: 通过 Windows 任务计划程序配置每天 00:00 执行

$scriptPath = Join-Path $PSScriptRoot "sync_profile_to_config.py"

# 切换到工作目录
$workspace = "E:\ProjectGroup\AI\ContextStack"
Set-Location $workspace

# 执行同步脚本
& python "$scriptPath"

# 退出码传递
exit $LASTEXITCODE
