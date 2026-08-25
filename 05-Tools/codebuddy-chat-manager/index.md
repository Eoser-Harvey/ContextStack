# codebuddy-chat-manager

CodeBuddy 聊天记录迁移工具：清单式索引 + 选择性迁移到新账户。

## 目录说明

- 日常只维护会话清单（chat-index.json / chat-index.md），不复制聊天数据本体
- 换账户时按清单选择会话，从源路径直接拷贝到目标账户（新/旧账户均可）并合并索引
- 详细用法与风险见 [README.md](README.md)

## 关键文件

| 文件              | 说明                               |
|:------------------|:-----------------------------------|
| chat-index.ps1    | 扫描生成会话清单（日常跑）         |
| chat-restore.ps1  | 选择性迁移会话到新账户（需要时跑） |
| chat-index.json   | 机器可读清单（脚本生成）           |
| chat-index.md     | 人类可读清单（脚本生成）           |

## 快速开始

```powershell
.\chat-index.ps1      # 更新清单
.\chat-restore.ps1    # 交互式迁移（先关闭 IDE）
```
