# 2026-08-28 当日会话纪要（auto-catchup）

> 由 session-daily-catchup 自动化补齐：当天有工作区变更、无 git 提交、无正常 session 文件，故自动生成。

---

## 元信息

- **会话日期**: 2026-08-28 23:30（自动补齐）
- **对话主题**: family-hub 投资系统月内数据更新（持仓/历史/报告）
- **处理文件数**: 5（工作区 modified，未提交）
- **用户反馈**: 无（自动化静默生成）

---

## 做对了什么（保持）

1. 持仓数据源 `holdings.yaml` 保持 `last_updated` 时间戳（2026-08-28）与 `usd_cny/hkd_cny` 汇率同步更新，便于追因。
2. 账户合并（燕/韩伟币安）与加权均价逻辑在备注中完整留存成本计算过程，符合"成本只以用户给的为准、禁止推算"规则。
3. 清仓/换仓（MRVL、ETH、新增 DRAM/MSTR/ONDO/UNI/SOXL、科创50/HK创新药ETF 新建仓）均写进 holdings 备注，数据链路可追溯。

## 踩了什么坑（避免）

1. ⚠️ 当天变更**只改工作区、未 git 提交**，导致会话沉淀断档——这是本 catchup 文件存在的原因。
2. 报告类（月度/年度/A8计划）与 holdings 同步修改，但无提交记录，若换设备/恢复易丢失当日进度。

## 下次怎么更快（优化）

1. 投资数据更新类改动，应在同一会话内走 `auto_push_home.ps1` 提交，避免"改了不推"积累。
2. 月内多次小改可合并为一次提交（框架策略：小修改积累后再统一推送）。

## 可复用的模式

- **投资更新闭环**: holdings.yaml（数据源）→ portfolio_history.yaml（历史）→ reports/*.md（月/年/A8 三份报告）三者必须同步，且每次变更需 `git commit + push`。
- **成本记录纪律**: 加仓/换仓必须在 `note` 写清"原持仓@均价 + 加仓@价 → 现持仓@加权均价"，杜绝事后反推。

---

## 关联文件

- 产出（当日 modified，未提交）:
  - `01-Projects/family-hub/research/portfolio/holdings.yaml`
  - `01-Projects/family-hub/research/portfolio/portfolio_history.yaml`
  - `01-Projects/family-hub/research/portfolio/reports/家庭资产报告-2026-08.md`
  - `01-Projects/family-hub/research/portfolio/reports/家庭资产年度报告-2026.md`
  - `01-Projects/family-hub/research/portfolio/reports/Crypto-A8计划-2026至2028.md`
- 参考:
  - `03-Memory/sessions/session-20260822-investment-system-update.md`（账户合并/均价计算规则）
  - GLOBAL-RULES.md「禁止推算」铁律
