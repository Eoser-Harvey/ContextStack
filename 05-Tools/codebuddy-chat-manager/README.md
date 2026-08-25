# CodeBuddy 聊天记录迁移工具（可复刻版）

> 设计原则：**不复制数据，只维护清单**。日常跑 `chat-index.ps1` 更新会话索引；
> 换账户后用 `chat-restore.ps1` 按清单选择性拷贝到新账户。
>
> 本 README 同时是「复刻规格说明」——拿到另一台电脑 / 另一个 AI 助手，照着本文能搭一套功能相同的工具。

---

## 一、工具文件清单

| 文件                     | 作用                                                 | 何时用         |
|:-------------------------|:-----------------------------------------------------|:---------------|
| `chat-index.ps1`         | 扫描 Data 目录，生成会话清单（json + md）            | 日常刷新清单   |
| `chat-restore.ps1`       | 按清单选择会话，迁移到目标账户（合并 index.json）    | 换账户迁移     |
| `chat-relocate.ps1`      | 把误落入独立工作区的会话归位到当前工作区             | 迁移后看不到时 |
| `setup_chat_index_task.bat` | 注册 Windows 定时任务（每日自动刷新清单）         | 一次性设置     |
| `chat-index.json`        | 机器可读清单（脚本生成，含完整源路径）               | 自动生成       |
| `chat-index.md`          | 人类可读清单（脚本生成，按最后消息倒序）             | 自动生成       |

---

## 二、数据源结构（逆向分析，复刻地基）

CodeBuddy 的会话数据存在本地，目录结构如下：

```
%LOCALAPPDATA%\CodeBuddyExtension\Data\
└── {账户UUID}\                          <- 每个登录过的账户一个目录
    └── {CodeBuddyIDE | VSCode}\         <- 客户端类型
        └── {工作区目录}\                 <- base64编码的路径 或 账户UUID
            └── history\{分组hash}\       <- 分组（同一项目/窗口的会话归一组）
                ├── index.json            <- 会话清单（名称/时间/模型）
                └── {会话ID}\
                    ├── index.json        <- 消息索引
                    └── messages\*.json   <- 消息本体（每条一个文件）
```

**关键结论**（复刻必懂）：
- **账户** 和 **工作区** 是两级隔离。会话属于「账户 → 客户端 → 工作区」，不在同一工作区就互相看不见。
- **工作区目录名有两种**：base64 编码的项目路径（如 `ZDovTXlGaWxl...` = `d:/MyFile/AI/...`），或账户 UUID（代表「默认工作区」）。
- **index.json 是会话索引**：`{ "conversations": [ {id, name, createdAt, lastMessageAt, modelMap...} ], "current": "当前会话id" }`。

---

## 三、使用场景

### 场景 1：日常刷新清单（无需关 IDE）

```powershell
cd 05-Tools\codebuddy-chat-manager
.\chat-index.ps1
```

只扫描、写 json/md，不动会话数据，随时可跑。

### 场景 2：换账户迁移（先关 IDE）

```powershell
# Step 1: 在 CodeBuddy 退出当前账户，登录目标账户（新账户会自动生成 UUID 目录）
# Step 2: 完全关闭 CodeBuddy IDE（脚本会检测进程并拦截）
# Step 3: 独立 PowerShell 窗口执行:
cd 05-Tools\codebuddy-chat-manager
.\chat-restore.ps1
# Step 4: 按提示选会话编号 → 选目标账户 → 确认
# Step 5: 重启 IDE，切到目标账户查看
```

**`chat-restore.ps1` 参数**：

| 参数           | 说明                                        |
|:---------------|:--------------------------------------------|
| `-Account`       | 只显示该账户的会话（UUID 前缀匹配）         |
| `-Select`        | 跳过交互直接选，如 `1,3,5-8` 或 `all`       |
| `-TargetAccount` | 目标账户 UUID，跳过交互                     |
| `-Rescan`        | 执行前重新扫描生成最新清单                  |
| `-DryRun`        | 只打印计划，不写入任何文件                  |
| `-Force`         | 跳过 IDE 进程检查与确认（全自动模式用）     |

### 场景 3：迁移后「看不到会话」（归位）

`chat-restore.ps1` 会**保留源工作区名**，导致会话落入独立的「源账户 UUID」工作区，在当前工作区看不到。

```powershell
# 先完全关闭 IDE，再执行归位（把会话从独立工作区挪到当前工作区）
.\chat-relocate.ps1
```

> 归位脚本是「按需定制」的：里面写死了源工作区、目标工作区、分组 hash。换机器复刻时，这三个值要按实际情况改。

### 场景 4：每天自动刷新清单（定时任务）

```powershell
# 右键「以管理员身份运行」，注册每日 22:30 自动刷新
.\setup_chat_index_task.bat
```

注册后任务名为 `ContextStack_ChatIndex`，错开 git 推送（22:00）。

---

## 四、账户 UUID 识别方法（复刻必学）

会话数据异步落盘，**目录时间戳不可靠**。识别「当前账户」用这个方法：

```powershell
# 找最近 1-2 天实际写入的文件，路径里第一个 UUID 就是当前活跃账户
Get-ChildItem "$env:LOCALAPPDATA\CodeBuddyExtension\Data" -Recurse -File |
  Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-2) } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 5 FullName, LastWriteTime
```

刚发过消息的账户，其 `history\...\messages\*.json` 时间戳最新。

---

## 五、踩坑经验（复刻时最值钱的部分）

| # | 坑 | 现象 | 正确做法 |
|:-:|:---|:-----|:---------|
| 1 | **中文脚本在 PowerShell 5.1 乱码** | 脚本含中文 Write-Host/注释，GBK 读取无 BOM 文件把引号搞坏，报语法错误 | 新脚本用纯英文；或用编辑器存成带 BOM 的 UTF-8 |
| 2 | **`$PSScriptRoot` 为空** | cmd 直接调用 / 任务计划运行时，`Join-Path $PSScriptRoot ...` 报"参数为空字符串" | 加兜底：`Split-Path -Parent $MyInvocation.MyCommand.Path`（**不要用 `Get-Location`**，任务计划工作目录是 System32） |
| 3 | **JavaScriptSerializer 序列化 PSObject 循环引用** | `Serialize` 报 "circular reference ... PSParameterizedProperty" | 写回改用原生 `ConvertTo-Json`；读保留 `DeserializeObject`（返回 Dictionary，字典访问语法不变） |
| 4 | **单元素 ArrayList 被 PowerShell 展开** | 会话只有 1 个时，`conversations` 序列化成对象 `{}` 而非数组 `[]` | `ConvertTo-PlainObject` 里 `return ,$list` 阻止展开；或直接用 `ConvertTo-Json` |
| 5 | **会话落错工作区** | 迁移后当前工作区看不到导入的会话 | 理解「账户→工作区」两级隔离，用 `chat-relocate.ps1` 归位 |
| 6 | **IDE 运行中改 index.json 被覆写** | 改了 index.json，IDE 退出后用内存状态覆盖 | 改 index.json 前必须完全关闭 IDE |

**坑 3 + 坑 4 的完整解法**（复刻核心）：
- 读：`JavaScriptSerializer.DeserializeObject()` → 返回纯 .NET Dictionary/ArrayList，**无 PSObject 问题**，用 `$data['conversations']` 字典语法访问
- 写：先用 `ConvertTo-PlainObject` 把对象递归转成 `[ordered]@{}` + `ArrayList`（`return ,$list` 阻止展开），再用 `ConvertTo-Json -Depth 20` 序列化

---

## 六、复刻指南（其他 AI 照着做一套）

1. **确认数据源**：`dir %LOCALAPPDATA%\CodeBuddyExtension\Data` 看目录结构是否与「二、数据源结构」一致（版本不同可能变）。
2. **写 chat-index**：遍历 `Data\{账户}\{客户端}\{工作区}\history\{分组}\index.json`，解析 `conversations` 数组，统计消息文件数/大小，输出 json + md 清单。
3. **写 chat-restore**：读清单 → 选会话 → 选目标账户 → 复制会话文件夹 + 合并目标 index.json（先备份 `.bak-时间戳`，按 `id` 去重）。
4. **写 chat-relocate**：把会话文件夹从源工作区 `robocopy /MOVE` 到当前工作区，合并 index.json（写死三个值：源工作区、目标工作区、分组 hash）。
5. **写 setup bat**：`schtasks /create /sc daily /st 22:30` 注册定时刷新。
6. **全程遵守「五、踩坑经验」**，尤其：脚本纯英文、`$PSScriptRoot` 兜底、写回用 `ConvertTo-Json`。

---

## 七、注意事项

1. **清单 ≠ 备份**：聊天数据只有 C 盘一份，旧账户目录被清理（重装/磁盘清理/CodeBuddy 升级）则清单失效。
2. **恢复/归位前必须关 IDE**：否则 index.json 会被内存状态覆写。
3. **目标账户需已存在于 Data 目录**：新账户先登录一次生成 UUID 目录。
4. 存储结构来自 2026-08 版本逆向分析，CodeBuddy 大版本升级后若失效，需重新核对。

---

**最后更新**：2026-08-25
**工具版本**：v2.0（新增 chat-relocate + 定时任务 + 修复序列化循环引用 + 修复 $PSScriptRoot）
