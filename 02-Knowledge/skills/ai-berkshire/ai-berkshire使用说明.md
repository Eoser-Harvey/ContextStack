# AI Berkshire 投资研究技能使用说明

## 技能概述

**AI Berkshire** 是一套专门为投资研究设计的AI Agent技能集合，提供完整的投资分析工作流，帮助投资者进行深度研究和决策支持。

## 技能集合

### 1. investment-research - 投资研究
**功能**：对特定公司或行业进行深度投资研究分析

**使用格式**：
- Claude Code: `/investment-research [公司/行业名称]`
- Codex: `使用 investment-research 研究 [公司/行业名称]`
- Codex（带Slash Prompts）: `/prompts:investment-research [公司/行业名称]`

**输出内容**：
- 公司基本面分析
- 行业竞争格局
- 财务数据解读
- 风险因素评估
- 投资建议总结

**示例**：
```
/investment-research 腾讯
/investment-research 新能源行业
```

### 2. investment-team - 投资团队分析
**功能**：分析投资团队或基金公司的背景、业绩、策略

**使用格式**：
- Claude Code: `/investment-team [团队/公司名称]`
- Codex: `使用 investment-team 分析 [团队/公司名称]`

**输出内容**：
- 团队背景和经验
- 历史投资业绩
- 投资策略和风格
- 管理规模和资金流向
- 团队稳定性评估

**示例**：
```
/investment-team 美团
/investment-team 高瓴资本
```

### 3. earnings-review - 财报回顾
**功能**：深入分析公司财报，提取关键信息和趋势

**使用格式**：
- Claude Code: `/earnings-review [公司名称] [财报期间]`
- Codex: `使用 earnings-review 分析 [公司名称] [财报期间]`

**参数说明**：
- `[公司名称]`：要分析的公司
- `[财报期间]`：可选，如 `2025Q4`、`2025年报`、`2026Q1`

**输出内容**：
- 关键财务指标分析
- 营收和利润增长趋势
- 现金流状况
- 资产负债表健康度
- 管理层讨论与分析摘要
- 未来展望和市场预期

**示例**：
```
/earnings-review 腾讯 2025Q4
/earnings-review PDD 2025年报
/earnings-review 茅台
```

### 4. industry-funnel - 行业漏斗分析
**功能**：对特定行业进行筛选和分层分析

**使用格式**：
- Claude Code: `/industry-funnel [行业名称]`
- Codex: `使用 industry-funnel 筛选 [行业名称]`

**输出内容**：
- 行业市场规模和增长趋势
- 产业链上下游分析
- 关键参与者和竞争格局
- 技术发展和创新趋势
- 政策和监管环境
- 投资机会和风险点

**示例**：
```
/industry-funnel AI算力
/industry-funnel 新能源汽车
/industry-funnel 医疗健康
```

### 5. portfolio-review - 投资组合回顾
**功能**：分析投资组合表现和优化建议

**使用格式**：
- Claude Code: `/portfolio-review [持仓配置]`
- Codex: `使用 portfolio-review 分析 [持仓配置]`

**参数说明**：
- `[持仓配置]`：持仓比例描述，如 `腾讯30%, 美团20%, 茅台20%, 现金30%`

**输出内容**：
- 资产配置分析
- 风险和收益评估
- 相关性分析
- 再平衡建议
- 压力测试结果
- 优化方案推荐

**示例**：
```
/portfolio-review 腾讯30%, 美团20%, 茅台20%, 现金30%
/portfolio-review 当前持仓
```

## 使用场景

### 场景1：个人投资者日常研究
**目标**：快速了解公司和行业基本面
**推荐技能**：`investment-research` + `earnings-review`
**工作流**：
1. 使用 `investment-research` 获取公司概况
2. 使用 `earnings-review` 分析最新财报
3. 结合两者做出投资决策

### 场景2：专业分析师深度研究
**目标**：生成完整的投资研究报告
**推荐技能**：全技能组合
**工作流**：
1. `industry-funnel` 分析行业趋势
2. `investment-research` 研究具体公司
3. `earnings-review` 分析财务数据
4. `portfolio-review` 评估投资组合
5. 综合所有分析生成报告

### 场景3：投资组合管理
**目标**：定期检视和优化投资组合
**推荐技能**：`portfolio-review` + `investment-team`
**工作流**：
1. `portfolio-review` 分析当前持仓
2. `investment-team` 评估管理团队
3. 根据分析结果调整配置

## 数据源集成

### 财务数据源
- 公司财报（年报、季报）
- 财务报表分析
- 财务比率计算
- 现金流分析

### 市场数据源
- 股价和交易数据
- 市值和估值指标
- 市场情绪指标
- 技术分析数据

### 行业数据源
- 行业研究报告
- 市场规模数据
- 竞争格局分析
- 政策监管信息

### 新闻舆情源
- 财经媒体报道
- 分析师研究报告
- 社交媒体情绪
- 公司公告和新闻

## 分析方法

### 基本面分析
- **财务分析**：盈利能力、偿债能力、运营效率
- **业务分析**：商业模式、竞争优势、增长潜力
- **管理分析**：管理层能力、公司治理、战略执行

### 技术分析
- **价格趋势**：支撑阻力、趋势线、形态分析
- **技术指标**：移动平均线、RSI、MACD、布林带
- **成交量分析**：量价关系、资金流向

### 量化分析
- **风险评估**：波动率、VaR、最大回撤
- **组合优化**：马科维茨模型、Black-Litterman模型
- **绩效评估**：夏普比率、索提诺比率、Alpha/Beta

### 定性分析
- **行业前景**：增长动力、竞争格局、进入壁垒
- **公司治理**：管理层质量、股东结构、企业文化
- **风险因素**：经营风险、市场风险、政策风险

## 输出格式

### 标准报告结构
1. **执行摘要**：关键发现和建议
2. **公司概况**：基本信息和业务描述
3. **财务分析**：财务数据和比率分析
4. **行业分析**：行业趋势和竞争格局
5. **风险评估**：主要风险因素和应对措施
6. **估值分析**：估值方法和目标价格
7. **投资建议**：买入/持有/卖出建议

### 可视化输出
- **财务图表**：收入增长、利润率趋势
- **行业图表**：市场规模、市场份额
- **组合图表**：资产配置、风险收益分布
- **时间序列**：价格走势、技术指标

## 配置选项

### 数据源配置
```yaml
# 财务数据源
financial_data:
  provider: "wind"  # 或 "bloomberg", "yahoo_finance"
  api_key: "YOUR_API_KEY"
  
# 市场数据源
market_data:
  provider: "tushare"  # 或 "akshare", "baostock"
  api_key: "YOUR_API_KEY"
  
# 新闻数据源
news_data:
  provider: "jisuapi"  # 或 "tencent_news", "sina_finance"
  api_key: "YOUR_API_KEY"
```

### 分析参数
```yaml
# 分析深度
analysis_depth: "standard"  # "quick", "standard", "deep"

# 报告语言
language: "zh-CN"  # "en-US", "zh-CN"

# 输出格式
output_format: "markdown"  # "html", "pdf", "excel"

# 图表设置
charts:
  enabled: true
  style: "professional"  # "simple", "professional", "interactive"
```

### 个性化设置
```yaml
# 投资偏好
investment_style: "growth"  # "value", "growth", "balanced"
risk_tolerance: "moderate"  # "conservative", "moderate", "aggressive"
time_horizon: "long_term"  # "short_term", "medium_term", "long_term"

# 关注领域
sectors:
  - "technology"
  - "healthcare"
  - "consumer"
  - "financials"

# 排除列表
exclusions:
  companies: ["*ST", "退市"]
  industries: ["赌博", "烟草"]
```

## 最佳实践

### 研究流程
1. **明确目标**：确定研究目的和范围
2. **收集数据**：使用相应技能获取基础数据
3. **分析评估**：结合多种分析方法
4. **得出结论**：基于分析结果形成观点
5. **跟踪更新**：定期更新研究和分析

### 风险控制
1. **多元化验证**：使用多个技能交叉验证
2. **数据质量**：关注数据来源的可靠性
3. **模型局限**：理解AI分析的局限性
4. **人工复核**：重要决策需要人工复核

### 持续学习
1. **技能更新**：关注技能版本的更新
2. **市场变化**：适应市场环境和规则变化
3. **反馈改进**：根据使用反馈优化分析方法
4. **知识积累**：建立个人投资研究知识库

## 注意事项

### 使用限制
1. **数据时效性**：金融数据具有时效性
2. **模型准确性**：AI分析可能存在误差
3. **市场风险**：投资存在固有风险
4. **合规要求**：遵守相关法律法规

### 免责声明
- 本技能提供的分析仅供参考，不构成投资建议
- 投资决策需结合个人风险承受能力
- 市场有风险，投资需谨慎
- 技能开发者不承担任何投资损失责任

## 故障排除

### 常见问题
1. **数据获取失败**：检查网络连接和API配置
2. **分析结果异常**：验证输入参数和数据质量
3. **性能问题**：调整分析深度和复杂度
4. **格式错误**：检查输出格式设置

### 技术支持
- **文档参考**：查阅官方文档和示例
- **社区支持**：参与用户社区讨论
- **问题反馈**：通过GitHub Issues提交问题
- **版本更新**：定期检查技能更新

## 版本历史

### v1.0 (2026-06-29)
- 初始版本发布
- 包含5个核心投资研究技能
- 支持多种AI平台调用

### 未来计划
- 增加更多分析模型和指标
- 支持更多数据源集成
- 增强可视化和报告功能
- 提供API接口和SDK

---

**标签**：`#investment-research` `#financial-analysis` `#ai-assistant` `#portfolio-management` `#automation`

**作者**：JackCui
**原文链接**：https://mp.weixin.qq.com/s/rN6gmls_hbTWVHHSDhN3-Q
**收录日期**：2026-07-06