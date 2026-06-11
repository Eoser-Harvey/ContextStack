# 家庭投资追踪系统 — 项目规则 (L2)

## 项目概述
自动化追踪跨平台投资资产（香港券商美股、WEB3资产、A股券商等），
按月生成资产报告，按年生成年度汇总，记录历史最值和净资产趋势。

## 目录结构
```
01-Projects/family-investment/    # 项目工作台 (L2)
   WORKSPACE.md                   # 工作台入口
   STATE.md                       # 最新状态
   ACTIONS.md                     # 任务清单
   CONTEXT.md                     # 稳定上下文
   REFERENCES.md                  # 参考资料
   investment-research/           # 投资研究资料 (含敏感数据)
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
  位于 `investment-research/portfolio/`，已在 .gitignore 中忽略
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