# 5.three-sell-lines-daily — 三条卖出线每日监控

自动生成三条卖出线每日监控报告并推送到飞书。

## 脚本

- `monitor_three_sell_lines.py` — 主监控脚本：线1(Capex股价+新闻)、线2(ARR收入新闻)、线3(板块ETF轮动)
- `push_lark.py` — 飞书 interactive 卡片推送模块
- `holdings.yaml` — 持仓数据源
- `.secrets.yaml` — 飞书 Bot 凭证（.gitignore 排除）
- `reports/` — 生成的每日报告

## 触发

自动化任务 `ai-7`，每日 9:00 自动运行：

```bash
python monitor_three_sell_lines.py
```
