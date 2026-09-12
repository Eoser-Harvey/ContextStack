# 家庭决策枢纽 — 项目规则 (L2)

## 项目概述
自动化追踪跨平台投资资产（香港券商美股、WEB3资产、A股券商等），
按月生成资产报告，按年生成年度汇总，记录历史最值和净资产趋势。

## 目录结构
```
01-Projects/family-hub/           # 项目工作台 (L2)
   WORKSPACE.md                   # 工作台入口
   STATE.md                       # 最新状态
   ACTIONS.md                     # 任务清单
   CONTEXT.md                     # 稳定上下文
   REFERENCES.md                  # 参考资料
   research/                      # 投资研究资料 (含敏感数据)
      portfolio/                  # 持仓追踪
         holdings.yaml            # 持仓数据
         portfolio_history.yaml   # 历史追踪
         reports/                 # 自动生成的报告

05-Tools/portfolio-tracker/       # 工具脚本 (可提交)
   generate_report.py             # 报告生成器
   requirements.txt               # 依赖
```

## 敏感数据红线
- 持仓数据 (`holdings.yaml`, `portfolio_history.yaml`, `reports/`)
  位于 `research/portfolio/`，已在 .gitignore 中忽略
- 工具脚本 (`generate_report.py`) 不含敏感数据，可安全提交

## 数据来源
- CryptoCompare API → BTC/ETH 价格
- Yahoo Finance → Stooq回退 → Sina财经回退 → 美股/港股/A股价格
- Manual → CRCL预IPO、TS平台时间代币

## 资产分类
| 分类 | 说明 | 价格来源 |
|------|------|---------|
| crypto | 加密货币(链上+交易所) | cryptocompare |
| us_stock_tokenized | 链上证券(CRCL) | manual |
| us_stock | 美股 | yahoo→stooq |
| hk_stock | 港股 | yahoo→stooq |
| a_stock | A股 | yahoo→stooq→sina |
| ts_time_token | TS时间代币 | manual |

## 成本类型
- `cost_is_total: true` → cost_basis 为总成本(直接使用)
- 默认 → cost_basis 为单价(乘以数量)
- `cost_unknown: true` → 成本待补充

## 文件同步规则

### ① 财务数字单源化（2026-09-12 起）
- **唯一真值源**：`company-setup/2-beijing-company-accounting-ledger.md` §零「参数与口径总表」
- 其他文档出现金额时**一律以账本为准**；不一致 → 改其他文档，**不改账本**
- **参数变更纪律**：改 §零 任一参数 → 必须检查下游 6 个文件：`beijing-company-backlog-and-risks.md` / `1-beijing-company-ops-manual.md` / `beijing-company-cost-model.md` / `archive/company-done-log.md` / `archive/个税纳税记录补救方案.md` / `archive/社保缴费核对与生育险待遇说明.md`

### ② company-setup 文件职责单一（2026-09-12 拆分，原 1025 行文档一分为三）

**主文档**（`company-setup/`，按使用顺序编号）：
| 文件 | 唯一职责 |
|------|----------|
| `1-beijing-company-ops-manual.md` | 操作步骤（月/季/年、报税、收款码、自记账） |
| `2-beijing-company-accounting-ledger.md` | 账务凭证 + **数字真值源** |
| `beijing-company-backlog-and-risks.md`（原 `beijing-company-social-insurance-plan.md`） | 决策 / 待办 / 风险 |
| `beijing-company-cost-model.md` | 费用测算 |

**归档**（`company-setup/archive/`，低频查阅）：
| 文件 | 唯一职责 |
|------|----------|
| `archive/company-done-log.md` | 已完成事项 |
| `archive/社保缴费核对与生育险待遇说明.md` | 社保逐项核对 + 生育险待遇 |
| `archive/个税纳税记录补救方案.md` | 2026 个税补救（执行至 2026-11 入库） |

> 🔴 **命名规则（2026-09-12）**：主文档用 `序号-` 前缀表示使用顺序（`1-` 操作 → `2-` 账本）；归档文件不带序号，统一放 `archive/`。
> ⚠️ **改名纪律（2026-09-12 血泪教训）**：文件名变更**必须同步更新全部引用**，至少包括 —— 本文件、`company-setup/index.md`、`TODO-DASHBOARD.md`、`research/index.md`、`company-setup/` 内各文档互链、`archive/` 归档文档的相对链接（注意多一层目录需加 `../`），以及 **`automated-task/3.trae-daily-company-operations/send_company_reminders.py` 的 `COMPANY_DOC_PATH`**（漏改 = 飞书每日推送直接失败，且失败是静默的）。

### ③ ⚠️ html 同步规则（**当前失效，待确认**）
- 原规则：`beijing-company-backlog-and-risks.md`（原 `beijing-company-social-insurance-plan.md`） ← 唯一编辑源；`.html` 由 `python 05-Tools/fileops/md2html.py <md>` 自动生成，禁止手动编辑
- **现状（2026-09-12 核查）**：`company-setup/` 下**已无 .html 文件**，该规则早已无人执行 → 属于"写了规则但没落地"的典型
- **待办**：确认是**废止**该规则，还是**恢复** html 生成流程

### ④ company-setup 每月数据维护 SOP（🔴 每月照做，不靠记性）

> **目的**：把 `1-beijing-company-ops-manual.md` 月度五步流程产生的每一个"实际数"，**当天**落到唯一登记点（账本 §0.5），并同步更新受影响文档 —— **避免需要数据时再去翻网站 / 银行流水**。
> **总原则**：**先有数据、后有记录**。只登记渠道给出的实际数，**绝不自算、不推算、不估数**（2026 年 8 月 `759.12` 返工即因此）。

**五步动作表（顺序不可颠倒）**

| 步 | 时点 | 渠道操作（用户做） | 记录 / 同步（落点） |
|:--:|:--|:--|:--|
| **①** | 每月最后一天 | 公积金自动托收 → 网厅确认是否成功 | 登记托收日 + 单位/个人额 → 账本 **§0.5** |
| **②** | 次月 10-25 日 | 电子税务局申报缴纳上月社保 | 登记缴费日 + 单位/个人额 → 账本 **§0.5**；补日记账 + 凭证 + 总账 → **§四 / §五 / §六** |
| **③** | 发薪前 | 扣缴端试算个税 | 编当月工资表（应发 − 个人社保 − 个人公积金 − 个税 = 实发）；登记试算额 → **§二 / §0.5** |
| **④** | 发薪日 | 对公 → 个人卡转账（备注 `X月工资`） | 登记转账日 + 实发 + 流水号 → **§0.5**；补凭证 + 日记账 + 余额 → **§五 / §四 / §0.4** |
| **⑤** | 次月 1-15 日 | 扣缴端正式申报（**≠ 缴款，0 税也要报**） | 登记申报日 + 应补税额 + **税款入库月** → **§0.5**；有税款时补缴税凭证 → **§五** |
| **⑥** | 每月末 | — | **月度自查**：§0.5 当月行是否填全？§0.4 余额是否与银行一致？总账 / 报表是否更新？→ **§六 / §七** |
| **⑦** | 每季首月 15 日前 | 电子税务局季报（增值税 + 企税 + 附加税，零申报 6 项） | 确认完成 + 更新报表 → **§七** |
| **⑧** | 数据变动时 | — | **参数变更纪律**：改账本 §零任一参数 → 检查下游 6 文件（见 §①） |

**AI 协作分工**
- **用户**：完成渠道操作（转账 / 申报 / 确认），**一句话告知事实**即可（如"9/10 社保已扣 2,707.44"）
- **AI**：算分录、更新账本、补凭证、校验恒等式、**填 §0.5 登记表**
- ⛔ **用户不自己改账本数字**（避免两边打架）；**AI 不得在用户确认前填任何"实际数"**

**触发词（最省事的用法）**
| 说这句 | AI 应做 |
|:--|:--|
| "公积金托收成功了" | 登记 §0.5 ①，补公积金凭证 |
| "社保扣款了 X 元" | 登记 §0.5 ②，补凭证 + 日记账 + 总账 |
| "X 月工资已发" | 登记 §0.5 ④，补工资凭证，更新 §0.4 余额 |
| "个税申报完成，应补 X 元" | 登记 §0.5 ⑤，有税款时补代扣代缴分录 |
| **"本月数据登记核对一下"** | 通读 §0.5，指出缺项，按渠道数补齐 |
| **"月度自查"** | 执行 ⑥，出结论（含"余额是否与银行一致"） |

> 📌 **月度自查是硬性动作，不是可选**：每月末（或次月发薪后）**由 AI 主动核对** §0.5 是否填全、各数是否互相闭合、§0.4 是否与银行一致，**不等用户开口**。
> 🔗 **相关位置**：操作步骤 → `1-beijing-company-ops-manual.md`；登记表 → `2-beijing-company-accounting-ledger.md` §0.5；记账协作 → 同文件 §八；待办 / 期限 → 根目录 `TODO-DASHBOARD.md`（P0「🏢 燕知行公司」）。