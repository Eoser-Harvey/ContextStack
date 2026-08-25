# CodeBuddy 聊天记录迁移工具

> 设计原则：**不复制数据，只维护清单**。日常跑 `chat-index.ps1` 更新会话索引；
> 换账户后用 `chat-restore.ps1` 按清单选择性拷贝到新账户。

## 文件说明

| 文件              | 作用                                       |
|:------------------|:-------------------------------------------|
| chat-index.ps1    | 扫描 Data 目录，生成会话清单（json + md）  |
| chat-restore.ps1  | 按清单选择会话，迁移到目标账户             |
| chat-index.json   | 机器可读清单（脚本生成，含完整源路径）     |
| chat-index.md     | 人类可读清单（脚本生成，按最后消息倒序）   |
| data-export/      | `-Export` 实体导出目录（不进 Git）         |

## 日常使用

### 1. 更新清单（无需关 IDE，随时可跑）

```powershell
cd 05-Tools\codebuddy-chat-manager
.\chat-index.ps1
```

### 2. 换账户迁移（换账户时用）

**前置认知**：
- 清单不是备份：会话数据一直在 C 盘原位，脚本从源路径**直接拷贝**到目标账户，无中间环节
- 目标账户不限于新账户：脚本列出 Data 下**所有**账户目录，旧账户也能作目标（导入按会话 id 合并，不覆盖已有会话）
- 退出前若无新增会话，**无需重跑** `chat-index.ps1`（清单已是最新）

**操作步骤**：
```powershell
# Step 1: 在 CodeBuddy 退出当前账户，登录目标账户（全新账户会自动生成新 UUID 目录）
# Step 2: 完全关闭 CodeBuddy IDE（脚本会检测进程并拦截）
# Step 3: 独立 PowerShell 窗口执行:
cd 05-Tools\codebuddy-chat-manager
.\chat-restore.ps1
# Step 4: 按提示操作:
#   a. 输入会话编号(如 1,3,5-8 / all / q 退出)
#   b. 选目标账户 —— 列表已按活跃排序，显示「会话数 / 最近消息」，看这两个字段认账户:
#      全新账户 = 会话数 0、最近消息「(无会话)」
#      旧账户   = 按会话数/最近消息对照你之前的使用记录
#   c. 确认执行
# Step 5: 重启 CodeBuddy IDE，切到目标账户，检查会话列表是否出现恢复的会话
```

## chat-restore.ps1 参数

| 参数            | 说明                                            |
|:----------------|:------------------------------------------------|
| -Account        | 只显示该账户的会话（UUID 前缀匹配）             |
| -Select         | 跳过交互直接选，如 `1,3,5-8` 或 `all`           |
| -TargetAccount  | 目标账户 UUID，跳过交互                         |
| -Export         | 迁移同时把会话实体导出到 data-export/ 留底      |
| -Rescan         | 执行前重新扫描生成最新清单                      |
| -DryRun         | 只打印计划，不写入任何文件                      |
| -Force          | 跳过 IDE 进程检查与执行确认（全自动模式用）     |

## 注意事项（必读）

1. **清单 ≠ 备份**：聊天数据只有 C 盘一份。旧账户目录被清理（重装系统 / 磁盘清理 / CodeBuddy 升级清数据）则清单失效。重要会话请用 `-Export` 留实体。
2. **恢复前必须关闭 IDE**：运行中的 IDE 退出时可能用内存状态覆写 `index.json`，导致恢复被抹掉。脚本默认会检测进程并拦截。
3. **目标账户需已存在于 Data 目录**：全新账户要先登录一次让 CodeBuddy 生成 UUID 目录；旧账户则无需额外操作。
4. 合并前脚本自动把目标 `index.json` 备份为 `.bak-时间戳`；合并按会话 id 去重，重复执行安全。
5. 存储结构来自逆向分析（2026-08 版本），CodeBuddy 大版本升级后若失效，需重新核对目录结构。

## 数据源结构（参考）

```
%LOCALAPPDATA%\CodeBuddyExtension\Data\
└── {账户UUID}\
    └── {CodeBuddyIDE|VSCode}\
        └── {工作区目录(base64编码路径 或 UUID)}\
            └── history\{分组hash}\
                ├── index.json            <- 会话清单（名称/时间/模型）
                └── {会话ID}\
                    ├── index.json        <- 消息索引
                    └── messages\*.json   <- 消息本体（每条一个文件）
```
