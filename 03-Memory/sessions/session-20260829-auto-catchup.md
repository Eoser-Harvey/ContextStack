# 会话经验模板

> 本次为 session-daily-catchup 自动化补齐（2026-08-29 当日活动沉淀）

---

## 元信息

- **会话日期**: 2026-08-29
- **对话主题**: 修复 `auto_push_home.ps1` Step 2 越早退出 bug + 当日多类知识沉淀（北京公司设立 / 千寻智能面试准备 / 目录重组）
- **处理文件数**: 10+（脚本 1、company-setup 5、company-h3c 重组 2、千寻面试 2 未提交）
- **用户反馈**: 正面（认可"用本地 bare 隔离测试"、认可根因分析）

---

## 做对了什么（保持）

1. **根因定位靠"日志结尾 + 源码"比对**：8/29 03:00 定时任务其实跑了，不是没跑；真正问题是 Step 2 push 成功后 `exit 0`，未提交改动被静默跳过。先看日志断点、再读对应源码，避免"任务没跑"的误判。
2. **用本地 bare 仓库隔离测试 bug 修复**：`git clone --bare` 建本地仓库 → 把 `origin`/`origin-ssh` 临时指向它 → 构造「ahead commit + 未提交改动」并存场景 → 跑脚本验证 → 测完 `git reset --mixed` 撤销测试 commit + 恢复 remote + 删测试文件。全程不污染 github，且能真实跑通端到端（Step 1→2→3→4→5）。
3. **修主 bug 时顺手修掉关联健壮性缺陷**：测试暴露 `$env:TEMP` 在非交互环境为空，导致写 commit message 失败（"Empty path name"）。加三级 fallback（`$env:TEMP`→`$env:TMP`→`$scriptDir`），一步到位。
4. **网络抖动与脚本 bug 分清**：一次推送失败是临时网络断（SSH 443 与 GitHub HTTPS 同时不可达），诊断 `Test-NetConnection` 确认网络恢复后重跑即成功，没有误改脚本。

---

## 踩了什么坑（避免）

1. **`auto_push_home.ps1` Step 2 的 `exit 0` 是潜伏 bug**：原逻辑 push 完"已提交未推送的 commit"后直接退出，导致「ahead commit + 未提交改动」并存时，**未提交改动被静默晾着**。8/25~8/28 连续多晚定时任务都"正常运行 exit 0"，但把投资数据改动漏推了近两天——"脚本 exit 0" 不等于 "所有改动都已推送"。
2. **脚本假设 `$env:TEMP` 一定存在**：非交互/服务环境可能为空，写临时文件直接抛 "Empty path name is not legal"。
3. **批量删除保护拦截**：删本地 bare 测试仓库（892 文件）被 Safe-Delete 批量阈值（>500）拒绝，需用户手动删，不能用命令绕。
4. **PowerShell `-Command` 里的 `$` 变量被环境吞掉**：调试时用 `-File` 直接跑脚本体更稳；`-Command` 字符串里的 `$_`/`$LASTEXITCODE` 等可能丢失。

---

## 下次怎么更快（优化）

1. **给自动推送脚本加"残留告警"**：push 完成后若 `git status --porcelain` 仍非空，主动写一条告警日志（甚至发通知）。这样"看起来跑成功实则漏推"的问题当天就能发现，不用等到两天后。
2. **重要数据改动当场 commit**：投资/公司设立等关键数据改动，当次对话里就提交，别完全依赖凌晨定时任务兜底。
3. **改脚本先讨论再动**：用户文件改动属于高影响操作，定位到根因并给出方案后再改，避免来回试错。

---

## 可复用的模式

- **定时任务"假成功"诊断法**：① 查日志确认任务是否真跑了；② 看日志结尾停在哪一步；③ 读对应源码找 early-return / 显式 `exit` / 条件分支遗漏。本例停在 Step 2 push OK 之后，源码对应 `if (Test-SshReachable) { push; exit 0 }`。
- **脚本修复的隔离测试 SOP**：本地 bare 仓库作临时 remote → 构造 bug 触发场景 → 真实运行验证 → reset/remote 恢复/删残留。比"dry-run 猜逻辑"可靠得多。
- **自动推送脚本健壮性清单**：① push 后不提前 exit，先确认无未提交改动；② 临时文件路径三级 fallback；③ 运行结尾校验 `git status` 是否为空并告警。
- **PowerShell 执行偏好**：跑整脚本用 `-File`；诊断用 `Test-NetConnection host -Port 443 -InformationLevel Quiet` 测连通性（避开 `$` 变量被吞）。

---

## 关联文件

- 产出（已提交）:
  - `05-Tools/backup/auto_push_home.ps1` — Step 2 `$aheadPushed` 标志重构 + `$env:TEMP` fallback（commit `0c188f9`）
  - `01-Projects/family-hub/company-setup/*` — 北京公司设立：社保方案(html/md 修订)、记账账本(新建 240 行)、完成日志、index（commit `6bc36c9`）
  - `02-Knowledge/career-development/company-h3c/*` — 原 `company/` 目录重命名为 `company-h3c/`（commit `12c2eab`）
- 未提交（工作区残留，待下次推送）:
  - `02-Knowledge/career-development/interview-project-summaries/01-company-interviews/千寻智能-MS准备清单.md` — 千寻智能 MS 面试准备（120 行大幅扩充）
  - `.../01-company-interviews/index.md` — 索引更新
- 参考: `05-Tools/backup/auto_push_home.log`（Step 2 bug 现场 + 修复后端到端验证日志）
