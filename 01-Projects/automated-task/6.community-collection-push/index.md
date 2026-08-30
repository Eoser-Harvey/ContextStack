# 6.community-collection-push — 社区投资情报推送

从 ChatLog 云端报告中心（`http://47.113.105.137:8080`）抓取核心群聊 + 额外群聊 AI 摘要报告，
提取投资相关信息（热门代币/股票/项目/观点/洞察），生成飞书卡片推送到"社区投资情报"群。

## 脚本

- `collect_community.py` — 主脚本：登录 → 抓报告列表 → 解析投资信息 → 构建卡片 → 推送
- `push_lark.py` — 飞书 interactive 卡片推送模块（复用）
- `profile_loader.py` — 个人画像加载模块（兼容复用）
- `.secrets.yaml` — 飞书凭证 + 网站凭证（.gitignore 排除，不入库）
- `community_push_state.json` — 去重状态（记录上次推送报告 + 时间戳，.gitignore 排除）

## 触发

TRAE 自动化任务（对应执行记忆 `.codebuddy/automations/`），每日定时运行：

```bash
python collect_community.py
```

报告每天 08:01 更新，脚本内置去重：仅当有新报告时推送，重复运行自动跳过。

## 推送目标

- 群：社区投资情报（chat_id 见 .secrets.yaml 的 `lark.community_chat_id`）
- 内容：仅投资相关（热门代币/股票/项目/观点/关键洞察），过滤"暂无/无消息"

## 验证记录

- 2026-08-31：本地端到端验证通过（抓取 638 报告 → 解析 22 核心 + 10 额外 → 筛选 18 投资群 → 推送成功，message_id 验证 OK）；去重重跑跳过验证通过。
