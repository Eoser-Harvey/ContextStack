# 会话经验模板

> 本次为 session-daily-catchup 自动化补齐（2026-09-03 当日活动沉淀）

---

## 元信息

- **会话日期**: 2026-09-03
- **对话主题**: family-hub 9月投资组合更新 + 报告引擎增强 + 新增每日飞书推送工具
- **处理文件数**: 7 files（5 modified + 2 untracked）；**当日 git 无 commit，全部改动停留工作区**
- **用户反馈**: 无（自动化补齐，无对话反馈）

---

## 做对了什么（保持）

1. **投资更新闭环保持同步**：`holdings.yaml`(持仓) + `portfolio_history.yaml`(历史) + 三份报告（`家庭资产报告-2026-09.md`新建 / `家庭资产年度报告-2026.md`修订 / `Crypto-A8计划-2026至2028.md`修订) 同批更新，未出现"只改持仓不更报告"的脱节。
2. **报告引擎脚本化**：`05-Tools/portfolio-tracker/_gen_report_v2.py`(+29行) 增强，支撑新报告字段/口径，降低手工改 yaml 与报告不一致风险。
3. **自动化推送形成"双档"**：在既有 `0.trae-feishu-push-hour/`(小时级) 之外，新增 `1.trae-feishu-push-day/_gen_script.py`(日级)；目录前缀 `0.`/`1.` 天然表达执行顺序，可作为定时任务命名约定。

---

## 踩了什么坑（避免）

1. **当日全部改动未 git 提交**：工作区 `git status` 仍有 5 modified + 2 untracked，依赖凌晨 `auto_push` 兜底。虽 Step2 漏推 bug 已于 08-29 修复，但"改了工作区过夜未提交"本身仍是 08-28 同源风险——若推送因故失败，改动仍会晾着。
2. （本日内容由工作区变更推断，对话中是否另有踩坑无法从纯变更判断，不臆造。）

---

## 下次怎么更快（优化）

1. **投资更新当次对话即提交**：月报/持仓更新完当场 `git commit`，不依赖定时任务兜底（08-28 已记，此处强化重复警示）。
2. **报告一律走 `_gen_report_v2.py` 生成**：新增字段只改脚本不手工改报告，避免 holdings 与报告数字对不上。

---

## 可复用的模式

- **投资更新闭环**：`holdings` → `portfolio_history` → `reports`(月报/年报/A8计划) 同一次更新且同一次 git 提交；新增月份即新建 `家庭资产报告-YYYY-MM.md`。
- **自动化定时推送双档命名**：`0.trae-feishu-push-hour/`(小时) + `1.trae-feishu-push-day/`(日)，前缀 `0.`/`1.` 表达顺序。
- **报告引擎脚本化**：`05-Tools/portfolio-tracker/_gen_report_v2.py` 单一入口生成全部报告，口径集中维护。

---

## 关联文件

- 未提交（工作区残留，待下次推送）:
  - `01-Projects/family-hub/research/portfolio/holdings.yaml`（持仓更新，4行）
  - `01-Projects/family-hub/research/portfolio/portfolio_history.yaml`（历史追加，18行）
  - `01-Projects/family-hub/research/portfolio/reports/家庭资产报告-2026-09.md`（**新建** 9月月报）
  - `01-Projects/family-hub/research/portfolio/reports/家庭资产年度报告-2026.md`（年报修订，29行）
  - `01-Projects/family-hub/research/portfolio/reports/Crypto-A8计划-2026至2028.md`（A8计划修订，8行）
  - `05-Tools/portfolio-tracker/_gen_report_v2.py`（报告引擎增强，29行）
  - `01-Projects/automated-task/1.trae-feishu-push-day/_gen_script.py`（**新建** 每日推送脚本）
- 参考: `session-20260828-auto-catchup.md`（同属"改了未提交"沉淀断档，闭环须同提交）

