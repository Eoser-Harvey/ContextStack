# Windows C 盘清理实战记录（2026-09-10）

> 触发：C 盘仅剩 12-14 GB，严重不足。用 SpaceSniffer + PowerShell 实测定位，结合豆包确认 AMD EeuDumps 专项，完成清理。
> 目的：沉淀**可复用的诊断方法 + 真实空间分布 + 分级清理清单**，下次 C 盘告警直接照此流程，不再从零探索。

---

## 一、诊断方法（可复用，先测再删）

### 1.1 总览（PowerShell，秒出）

```powershell
Get-PSDrive C | ForEach-Object { 'Used {0:N2} GB / Free {1:N2} GB' -f (($_.Used)/1GB), (($_.Free)/1GB) }
```

### 1.2 定位大户（只读，逐步打印防超时）

> 教训：PowerShell 内联 `$` 变量会被外层双引号吃掉导致 ParserError——**写临时 .ps1 文件执行，别用内联 -Command**。临时脚本用完即删。

```powershell
# 1) 根目录一级大小排行（含 pagefile/hiberfil 文件）
Get-ChildItem C:\ -Force | ForEach-Object {
  if ($_.PSIsContainer) {
    $s=(Get-ChildItem $_.FullName -Recurse -Force -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum
    '{0,-30} {1,8:N2} GB' -f $_.Name,($s/1GB)
  } else { '{0,-30} {1,8:N2} GB' -f $_.Name,($_.Length/1GB) }
}

# 2) 指定目录内部 Top 排行（下钻用）
function TopSub($root,$top=12){
  Get-ChildItem $root -Directory -Force -EA SilentlyContinue | ForEach-Object {
    $s=(Get-ChildItem $_.FullName -Recurse -Force -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum
    [PSCustomObject]@{Name=$_.Name;SizeGB=[math]::Round($s/1GB,2)}
  } | Sort-Object SizeGB -Desc | Select-Object -First $top | Format-Table -AutoSize
}
```

> 💡 实际重灾区永远是这几个，直接下钻省时间：`C:\Users\<user>\AppData\Roaming\Tencent`（微信系）、`AppData\Local\Google\Chrome`、`AppData\Local\Temp`、IDE 缓存（Trae/TRAE SOLO CN/bitbrowser）、`Windows\Installer`、`Windows\WinSxS`。

---

## 二、2026-09-10 实测空间分布（233GB 盘，参考基线）

| 目录 | 大小 | 性质 |
|:--|--:|:--|
| C:\Windows | 72.62 GB | Installer 28.2 + WinSxS 23.5 + System32 10.4（系统核心，勿手删） |
| C:\Users\harve | 57.21 GB | AppData 占 49.8（Roaming 腾讯 8.3 + TRAE 系 + 浏览器） |
| C:\Program Files (x86) | 25.66 GB | VS / SDK / Windows Kits / Lenovo |
| C:\Program Files | 8.40 GB | dotnet 4.2 + WSL + AMD |
| C:\ProgramData | 4.86 GB | Lenovo 1.7 + Adobe + SogouInput 0.66 |
| pagefile/hiberfil | — | swapfile 0.25 GB（无 hiberfil） |

**真实大头结论**：Windows 72GB（系统）+ Users 57GB（AppData 是主战场）+ Program Files 34GB。**用户侧可释放空间基本全在 AppData**，系统目录别碰。

---

## 三、分级清理清单

### Tier 1｜纯缓存垃圾（零风险，直接清，约 8-12 GB）

| 项 | 实测 | 处理 |
|:--|--:|:--|
| `%LOCALAPPDATA%\Temp` | 0.95 GB | 直接删内容 |
| npm-cache / Yarn / pnpm / pip / go-build | ~1.3 GB | `npm cache clean --force` 等，或迁移 D 盘 |
| `ms-playwright`（浏览器二进制） | 1.85 GB | 不用 Playwright 就删；用则迁 D |
| `Downloaded Installations` | 2.33 GB | 安装器残留，可清 |
| Chrome/Edge/bitbrowser 浏览器缓存 | 3-6 GB | 浏览器内"清除浏览数据" |
| SogouInput 缓存/日志 | 0.66 GB | 输入法设置内清理 |

### Tier 2｜大块但需确认（30-50 GB 潜在）

| 项 | 实测 | 决策点 |
|:--|--:|:--|
| `Roaming\Tencent`（xwechat 3.8 / WXWork 3.0 / WeChat 1.0 / WeMeet 0.44） | 8.27 GB | ⚠️ 微信聊天文件，确认云端备份后可清缓存 |
| TRAE SOLO CN 5.23 + Trae CN 0.98 + bitbrowser 4.17 | ~10 GB | AI IDE 历史缓存，确认可清 |
| Chrome User Data（多 Profile：Profile4 2.6 / Profile1 1.7 / ProfileTPL 1.7） | 6.5 GB | 旧 profile 确认不用再删 |
| Lenovo（Program Files 2.3 + ProgramData 1.7） | ~4 GB | 预装恢复工具，可留 |

### Tier 3｜治本：迁移到 D 盘（释放后不再回填）

- Chrome User Data / 微信文件与缓存：应用内设置改存储路径到 D
- npm/pip 缓存：`npm config set cache D:\npm-cache` / `pip config set global.cache-dir D:\.pip-cache`
- ms-playwright：`PLAYWRIGHT_BROWSERS_PATH=D:\pw-browsers`

### 🔴 系统目录红线（绝不手删）

- `Windows\Installer` 28GB / `Windows\WinSxS` 23GB：只能用 `cleanmgr`（磁盘清理）或 DISM 组件清理，**手动删除会让系统更新/卸载全坏**
- 关闭休眠 `powercfg /h off`（笔记本慎用，牺牲快速唤醒）
- `vssadmin` / `diskpart` / System Volume Information：不碰

---

## 四、专项：AMD EeuDumps 目录（2026-09-10 豆包确认）

### 这是什么

`C:\Windows\System32\AMD\EeuDumps` —— **AMD 芯片组/显卡驱动 bug** 造成的**错误转储高频写入**目录（相关已知问题，非病毒）。部分 AMD 平台会持续向该目录写 dump，导致 C 盘被悄悄吃满。

### 判定与清理

- 目录存在且持续增长 → 确认是 AMD EeuDumps 问题
- 处理：**清空目录内容可安全回收空间**（属诊断日志，非系统必需）
- 参考工具/讨论：GitHub `tGecko/AMD-EeuDumps`（含缓解脚本）、RadeonSoftwareSlimmer discussion #140
- 若反复快速涨回 → 更新 AMD 芯片组驱动 / 按社区方案禁用该写入行为

### 实测结果（本次）

- 清理后：EeuDumps 存在但 **0 GB**（已清空）；C 盘 Free 从 12.25 → **14.46 GB**（回收部分空间；大头仍需 Tier 1-3 处理）

---

## 五、流程复盘（下次照抄）

1. 总览 Free → 2. 根目录排行 → 3. AppData 下钻（腾讯/浏览器/IDE 缓存）→ 4. 系统目录仅 cleanmgr → 5. 专项目录单独确认（如 EeuDumps）→ 6. 优先迁移、其次删除、绝不手删系统目录
2. 每删一项前**只读测量大小**，删后验证空间确实回收
3. 临时测量脚本用完即删，不留在系统任何目录

---

## 关联

- C 盘清理 Skill：`e:\ProjectGroup\AI\ContextStack\.codebuddy\skills\c-drive-cleaner`（CleanSight，含 scanners/cleaners/migrators，可跑 analyze.ps1 自动报告）

---

**最后更新**: 2026-09-10
