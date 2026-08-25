# codebuddy-chat-manager

CodeBuddy 聊天记录迁移工具：清单式索引 + 选择性迁移到新账户 + 工作区归位 + 定时刷新。

## 目录说明

- 日常只维护会话清单（chat-index.json / chat-index.md），不复制聊天数据本体
- 换账户时按清单选择会话，从源路径直接拷贝到目标账户（新/旧账户均可）并合并索引
- 迁移后若会话落在独立工作区，用 chat-relocate.ps1 归位到当前工作区
- 详细用法、数据源结构、踩坑经验见 [README.md](README.md)（含复刻指南）

## 关键文件

| 文件                      | 说明                                        |
|:--------------------------|:--------------------------------------------|
| chat-index.ps1            | 扫描生成会话清单（日常跑 / 定时跑）         |
| chat-restore.ps1          | 选择性迁移会话到目标账户（换账户时跑）      |
| chat-relocate.ps1         | 归位误落独立工作区的会话（迁移后看不到时跑）|
| setup_chat_index_task.bat | 注册每日自动刷新清单的 Windows 定时任务     |
| chat-index.json           | 机器可读清单（脚本生成）                    |
| chat-index.md             | 人类可读清单（脚本生成）                    |

## 快速开始

```powershell
.\chat-index.ps1          # 更新清单
.\chat-restore.ps1        # 交互式迁移（先关闭 IDE）
.\chat-relocate.ps1       # 归位会话到当前工作区（先关闭 IDE）
setup_chat_index_task.bat # 注册每日定时刷新（管理员运行）
```
