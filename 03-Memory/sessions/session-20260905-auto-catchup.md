# 会话经验模板

> 本次为 session-daily-catchup 自动化补齐（2026-09-05 当日活动沉淀）

---

## 元信息

- **会话日期**: 2026-09-05
- **对话主题**: sync_profile_archive.py 档案同步中枢大幅重写 + 信用卡主控表滞留多日后提交
- **处理文件数**: 1 commit / 2 files（`557b107`，auto 提交；工作区已 clean）
- **用户反馈**: 无（自动化补齐，无对话反馈）

---

## 做对了什么（保持）

1. **档案同步中枢 `sync_profile_archive.py` 持续演进并定型架构**：本次 +824/−464（共 1288 行变动），相比 09-01 的 968 行重构进一步扩展。架构已清晰：每日 0 点读取 `holdings.yaml` + 最新月报 + 职业档案 → 生成两份 `profile_archive`（小时推送 / 日报推送各一份）→ 下游 `analyzer.py` / `send_daily_ai_news.py` / `push_lark.py` 经 `profile_loader.load_latest_profile()` 动态加载，`config.yaml` 不再硬编码 profile 段；更新 archive 即全链路生效，无需改消费方代码。
2. **信用卡主控表.xlsx 滞留多日（09-01→09-05）终随本次 auto commit 落地**，消除长期未提交风险。

---

## 踩了什么坑（避免）

1. **`sync_profile_archive.py` 单文件 churn 极高**（09-01 改 968 行、09-05 又改 1288 行），说明该"中枢"职责仍在快速膨胀，有向"万能脚本"演化的反模式风险。建议把"生成归档 / 加载归档 / 异常日志"等子职责拆为独立模块，降低单文件体积与回归风险。
2. **信用卡主控表.xlsx 连续多日未提交**（09-01 起滞留至 09-05），再次暴露"改动当天不提交、靠 auto_push 兜底"的习惯问题（同 08-28 警示）。跨日累积成大 diff 也难 review。

---

## 下次怎么更快（优化）

1. **高 churn 中枢脚本改动后当次对话即提交**：避免跨多日累积成 1288 行大 diff，review 与回滚都困难。
2. **xlsx 等二进制改动当场提交**，不留工作区过夜。

---

## 可复用的模式

- **自动化推送"档案中枢"模式**：`sync_profile_archive.py` 每日 0 点生成 `profile_archive`（小时/日报两份）→ `profile_loader.load_latest_profile()` 动态加载 → `analyzer`/`send_daily_ai_news`/`push_lark` 消费；config 不硬编码 profile，更新 archive 即全链路生效。可作为其他定时数据管道的中枢范本。
- **auto_push 收口 vs 及时提交**：`auto_push_home.ps1` 会把跨日累积的未提交改动统一收口（08-29 已修 Step2 漏推 bug），但易掩盖"改动当天未提交"问题——重要改动仍应当次提交。

---

## 关联文件

- 产出（已提交，commit `557b107`）:
  - `01-Projects/automated-task/sync_profile_archive.py`（1288 行重写，档案同步中枢）
  - `01-Projects/family-hub/credit-card-management/信用卡主控表.xlsx`（滞留多日后提交）
- 参考:
  - `session-20260901-auto-catchup.md`（同文件 09-01 的 968 行重构先例）
  - `session-20260903-auto-catchup.md`（投资组合更新闭环；该中枢消费的 holdings/月报来源）

