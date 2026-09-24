# -*- coding: utf-8 -*-
"""Update news items - temp script"""
import re

fp = r"E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\1.trae-feishu-push-day\send_daily_ai_news.py"

with open(fp, "r", encoding="utf-8") as f:
    txt = f.read()

# 1. Week line
txt = txt.replace('周二｜NVIDIA 129亿美元收购Hugging Face+OpenAI Presence企业AI Agent+特斯拉Optimus得州工厂+台积电涨10%+Humanoids Summit首尔', '周三｜硅基流动29亿融资+Anthropic Opus 5.5+高通2nm芯片+GPT-6 Sol/Luna+波士顿动力Atlas训练中心+台积电涨价+三星2nm试产+纽约RAISE法案')

# 2. Replace all news items from _add_news to def build_personalized_analysis
pat = r'_add_news\(.*?(?=\ndef build_personalized_analysis)'
new_items = []
# Financing
new_items.append(r'_add_news("\U0001f4b0 \u878d\u8d44/\u5e76\u8d2d", "硅基流动完成B+轮二期与C轮融资，2026年度累计股权融资近29亿元", "9月23日，AI能力提供商硅基流动完成B+轮二期与C轮融资，2026年以来累计股权融资近29亿元人民币。投资方包括中国互联网投资基金、国新基金、中国移动链长基金、东方资产国际等。资金将用于推理引擎、异构算力调度、模型与芯片适配等核心技术研发。", "新浪财经 / 新浪科技")')
new_items.append(r'_add_news("\U0001f4b0 \u878d\u8d44/\u5e76\u8d2d", "ADI 13.5亿美元收购Alif Semiconductor + Cognex 5亿美元收购Intel RealSense", "9月23日，模拟芯片巨头ADI宣布以全现金13.5亿美元收购AI边缘芯片公司Alif Semiconductor。同时，机器视觉公司Cognex拟以约5亿美元收购Intel拆出的RealSense立体深度相机业务。两笔交易分别表明边缘AI芯片和机器视觉仍是半导体并购热点方向。", "WLRK / 新浪财经 / 头条")')
# Products
new_items.append(r'_add_news("\U0001f4e6 \u4ea7\u54c1\u53d1\u5e03", "Anthropic发布Claude Opus 5.5，成本降低40%且更安全", "9月22日，Anthropic发布Claude Opus 5.5，运行成本较Opus 5下降40%，输出速度提升超30%。新模型在测试环境中突破边界的尝试次数较上代减少85%。API价格为每百万输入Token 4美元、输出20美元。这是Anthropic CEO呼吁\u2018放缓前沿AI发展\u2019后的首款新模型。", "凤凰网 / C114 / 新浪财经")')
new_items.append(r'_add_news("\U0001f4e6 \u4ea7\u54c1\u53d1\u5e03", "OpenAI推出GPT-6 Sol和Luna，价格下调50%加速下沉", "9月22日，OpenAI推出GPT-6 Sol和GPT-6 Luna，均基于GPT-6 Astra技术进展。Sol定位复杂专业工作、编码和智能体任务，Luna主打高频低成本使用。两款API价格较GPT-5.6促销价下调50%，已上线ChatGPT Work、Codex及API。距GPT-6 Astra发布不足三周。", "凤凰网 / 头条新闻")')
new_items.append(r'_add_news("\U0001f4e6 \u4ea7\u54c1\u53d1\u5e03", "高通发布骁龙8 Elite Gen 6：台积电2nm制程，端侧支持超300亿参数MoE模型", "9月22日，高通发布骁龙8 Elite Gen 6和Extreme Gen 6，采用台积电2纳米制程，最高主频达5GHz。Extreme版NPU性能提升35%，AI每瓦性能提升33%，支持端侧运行超300亿参数MoE模型，引入Adreno Neural Fusion技术。", "财联社 / 新浪科技")')
# Tech breakthroughs
new_items.append(r'_add_news("\U0001f52c \u6280\u672f\u7a81\u7834", "DeepSeek-V4.1-Flash：552B参数MoE非对称架构，KV缓存压缩至1/4", "9月23日，DeepSeek V4.1-Flash采用非对称Causal Encoder-Decoder架构，输入仅8B激活参数，输出仅16B激活参数。KV缓存HBM占用降至上代1/4，SSD存储占用降至1/8。性能超越V4-Pro，已上线API，开源MIT许可。", "DeepSeek API Docs / Hugging Face")')
new_items.append(r'_add_news("\U0001f52c \u6280\u672f\u7a81\u7834", "Google DeepMind发布Gemini 3.8 Flash和Flash Cyber专用模型", "9月23日，Google DeepMind发布Gemini 3.8 Flash系列。3.8 Flash在软件工程、Agent任务和多步推理方面显著超越3.7 Flash，价格与3.7持平。Flash Cyber专攻网络安全，在Chrome代码库的有效修复数量是基线模型的2.6倍。", "Google AI Blog / 智东西")')
# Regulation
new_items.append(r'_add_news("\u2696\ufe0f \u884c\u4e1a\u6cd5\u89c4", "纽约州RAISE法案强化前沿AI监管：要求注册备案与72小时安全事件报告", "9月21日，纽约州州长Kathy Hochul宣布依据RAISE法案，从11月起要求前沿AI开发者向州政府注册，自2027年1月起需在72小时内报告重大安全事件。同时评估\u2018AI安全开关\u2019等进一步措施。", "NY Governor / Infobae")')
new_items.append(r'_add_news("\u2696\ufe0f \u884c\u4e1a\u6cd5\u89c4", "中国发布《人工智能安全治理框架3.0》，全球3大辖区强制AI法律生效", "9月14日，全国网络安全标准化技术委员会发布《AI安全治理框架3.0》，优化调整技术应对和综合治理措施。截至2026年9月，欧盟AI法案、韩国AI框架法、越南AI法已全面生效，EU AI法禁止性规定将于2026年12月生效。", "头条新闻 / AI Risk Aware")')
# Semiconductor
new_items.append(r'_add_news("\U0001f50c \u534a\u5bfc\u4f53/\u82af\u7247", "台积电通知客户涨价5-10%，AMD全线产品Q4起涨价10%", "9月23日，台积电已向Nvidia、Apple、Qualcomm等主要客户通知晶圆涨价5%-10%，重点针对先进5nm以下制程。AMD随即宣布GPU、AI加速器、芯片组等全线产品Q4起涨价10%。Omdia将2026年全球半导体收入增长预测上调至94.1%，存储芯片将占半导体总收入50%以上。", "Ticker.report / Omdia / TrendForce")')
new_items.append(r'_add_news("\U0001f50c \u534a\u5bfc\u4f53/\u82af\u7247", "三星得州泰勒工厂2nm设施月底试产，预定产能已满", "9月23日，三星电子位于美国得州泰勒工厂的2nm设施将于9月底开始试产，当前预定产能已满。客户包括特斯拉(AI5芯片)、博通和Arm。初始产能约5万片晶圆/月，接近台积电8万片水平。存储芯片集体上涨：闪迪涨6%，美光涨5%。", "The CODEW / 电子工程专辑")')
# Robotics
new_items.append(r'_add_news("\U0001f916 \u673a\u5668\u4eba/\u5177\u8eab\u667a\u80fd", "波士顿动力在现代工厂开设Atlas机器人训练中心，人形机器人进入制造业实训", "9月21日，波士顿动力宣布在现代汽车美国亚特兰大工厂园区开设RMAC机器人训练中心。Atlas人形机器人将在真实工厂环境中学习汽车零部件排序、物流准备等任务，未来将扩展到组装、重物搬运等场景。现代计划将Atlas部署到全球工厂。", "Boston Dynamics / 新浪科技")')
new_items.append(r'_add_news("\U0001f916 \u673a\u5668\u4eba/\u5177\u8eab\u667a\u80fd", "具身智能2026H1融资总额达935亿元，多家机器人企业排队上市", "9月23日，IT桔子数据显示2026年上半年具身智能领域融资总额达935亿元人民币，约为去年同期的5倍。正在港交所排队上市的企业超500家，其中机器人及具身智能相关企业超50家。同时特斯拉Optimus得州工厂主体结构接近完工、中国宁波供应链审核推进中。", "IT桔子 / 新浪财经 / 智东西")')

new_block = '\n\n'.join(new_items)

# Replace between first _add_news and def build_personalized_analysis
start = txt.find('_add_news("')
end = txt.find('\ndef build_personalized_analysis()')
txt = txt[:start] + new_block + txt[end:]

# 3. Update trend commentary
old_trend = '2026年9月22日，周二，复盘今日(9月第四周)三大方向'
txt = txt.replace(old_trend, '2026年9月23日，周三，复盘今日(9月第四周)三大方向')

# Save
with open(fp, "w", encoding="utf-8") as f:
    f.write(txt)

print("Done!")
print(f"News items: {len(new_items)}")
print(f"Has '硅基流动': {'硅基流动' in txt}")
print(f"Has '波士顿动力': {'波士顿动力' in txt}")