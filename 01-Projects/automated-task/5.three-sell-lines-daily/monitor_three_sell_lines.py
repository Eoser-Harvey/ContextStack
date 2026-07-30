"""
三条卖出线每日自动监控脚本 v5
- 线1 (Capex): 监控 MSFT/GOOGL/META/AMZN/NVDA/MRVL 股价 + Capex新闻 + 投资建议
- 线2 (ARR): 监控 OpenAI/Anthropic ARR新闻 + 投资建议
- 线3 (替代赛道): 美股板块ETF资金流向 + 行业轮动信号
- 新闻翻译: 英文新闻自动翻译为中文
- 投资建议: 基于方法论场景A/B/C，止盈止损 + 上车信号

用法: python monitor_three_sell_lines.py
输出: 飞书推送（本地不留缓存，推送后自动删除）
"""

import requests, json, re, sys, time, os, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Windows UTF-8 兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 飞书推送模块（从参考项目复制，未修改）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from push_lark import send_interactive_card, load_secrets
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False
    print("[WARN] push_lark.py 未找到，跳过飞书推送")

BASE = Path(__file__).parent
REPORTS_DIR = BASE / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
out_file = REPORTS_DIR / f"three-sell-lines-daily-{today_str}.md"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ============================================================
# 零、新闻翻译引擎（本地规则翻译）
# ============================================================

TRANSLATION_CACHE_FILE = BASE / ".translation_cache.json"

def _load_translation_cache():
    if TRANSLATION_CACHE_FILE.exists():
        try:
            return json.loads(TRANSLATION_CACHE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def _save_translation_cache(cache):
    TRANSLATION_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

# 金融术语映射表（英→中）— v2 大幅扩展，按长度降序排序确保长短语优先匹配
FINANCE_TERMS = {
    # ========== 完整标题句式（整句匹配，最高优先级）==========
    "Big Tech is paying for the AI boom, and chipmakers are cashing in: Chart of the Day": "科技巨头为AI繁荣买单，芯片制造商从中获利：今日图表",
    "Crypto Industry Steps Up Quantum Security Efforts as Encryption Risks Accelerate": "加密行业加速量子安全布局，加密风险加剧",
    "Goldman Sachs Says Optical Networking Is AI's Next Trillion-Dollar Opportunity": "高盛称光网络是AI的下一个万亿机会",
    "Memory Stock Surge Sets Stage for SK Hynix's U.S. Trading Debut": "存储股飙升为SK海力士美国交易首秀铺路",
    "\"Most Profound Impact Will Be in Life Sciences.\" Does This Bet on a Biotech Stock Prove He Means It?": "「最深远影响将在生命科学领域」，这笔生物科技投资能证明他此言不虚吗？",
    "ETF Showdown Traditional Energy Meets Clean Energy. Which ETF Is the Better Buy?": "ETF对决：传统能源vs清洁能源，哪个更值得买入？",

    # ========== 公司/机构（中文名 + 股票代码）==========
    "Marvell Technology": "迈威尔科技(MRVL)",
    "Taiwan Semiconductor Manufacturing": "台积电(TSM)",
    "Taiwan Semiconductor": "台积电(TSM)",
    "JPMorgan Chase": "摩根大通",
    "Morgan Stanley": "摩根士丹利",
    "Bank of America": "美国银行",
    "Citigroup": "花旗集团",
    "Wells Fargo": "富国银行",
    "Goldman Sachs": "高盛",
    "Deutsche Bank": "德意志银行",
    "UBS Group": "瑞银集团",
    "HSBC Holdings": "汇丰控股",
    "Barclays": "巴克莱",
    "Credit Suisse": "瑞士信贷",
    "Mizuho Securities": "瑞穗证券",
    "Nomura Holdings": "野村控股",
    "Jefferies": "杰富瑞",
    "Piper Sandler": "派珀桑德勒",
    "Wolfe Research": "沃尔夫研究",
    "Susquehanna": "萨斯奎哈纳",
    "Bernstein": "伯恩斯坦",
    "Monness Crespi": "蒙尼斯·克里斯皮",
    "Needham": "尼德汉姆",
    "Rosenblatt": "罗森布拉特",
    "Cantor Fitzgerald": "康托菲茨杰拉德",
    "Loop Capital": "卢普资本",
    "MoffettNathanson": "莫菲特纳桑森",
    "TD Cowen": "TD考恩",
    "Truist Securities": "信托证券",
    "Evercore ISI": "艾弗考尔ISI",
    "Raymond James": "雷蒙德詹姆斯",
    "Baird": "贝尔德",
    "KeyBanc": "基班克",
    "Stifel": "斯蒂费尔",
    "RBC Capital": "加拿大皇家银行资本",
    "BMO Capital": "蒙特利尔银行资本",
    "Oppenheimer": "奥本海默",
    "Wedbush": "韦德布什",
    "New Street Research": "新街研究",
    "Melius Research": "梅利乌斯研究",
    "William Blair": "威廉布莱尔",
    "Tigress Financial": "泰格雷斯金融",
    "Northland Capital": "诺斯兰资本",
    "DA Davidson": "DA戴维森",
    "Craig-Hallum": "克雷格-哈勒姆",
    "Roth MKM": "罗斯MKM",
    "H.C. Wainwright": "HC温赖特",
    "Berkshire Hathaway": "伯克希尔哈撒韦",
    "SoftBank Group": "软银集团",
    "Samsung Electronics": "三星电子",
    "SK Hynix": "SK海力士",
    "Micron Technology": "美光科技(MU)",
    "Western Digital": "西部数据",
    "Seagate Technology": "希捷科技",
    "Applied Materials": "应用材料(AMAT)",
    "Lam Research": "泛林研究(LRCX)",
    "KLA Corporation": "科磊(KLAC)",
    "ASML Holding": "阿斯麦(ASML)",
    "Tokyo Electron": "东京电子",
    "Synopsys": "新思科技(SNPS)",
    "Cadence Design": "楷登电子(CDNS)",
    "ARM Holdings": "安谋控股(ARM)",
    "Analog Devices": "亚德诺半导体(ADI)",
    "Texas Instruments": "德州仪器(TXN)",
    "Qualcomm": "高通(QCOM)",
    "Intel Corporation": "英特尔(INTC)",
    "Super Micro Computer": "超微电脑(SMCI)",
    "Arista Networks": "阿里斯塔网络(ANET)",
    "Palantir Technologies": "帕兰提尔(PLTR)",
    "CrowdStrike": "CrowdStrike(CRWD)",
    "Snowflake": "Snowflake(SNOW)",
    "Datadog": "Datadog(DDOG)",
    "MongoDB": "MongoDB(MDB)",
    "Cloudflare": "Cloudflare(NET)",
    "ServiceNow": "ServiceNow(NOW)",
    "Salesforce": "赛富时(CRM)",
    "Oracle": "甲骨文(ORCL)",
    "SAP": "思爱普(SAP)",
    "Workday": "Workday(WDAY)",
    "Atlassian": "Atlassian(TEAM)",
    "Adobe": "奥多比(ADBE)",
    "Cisco Systems": "思科(CSCO)",
    "Juniper Networks": "瞻博网络(JNPR)",
    "Ciena Corporation": "希纳(CIEN)",
    "Infinera": "英飞朗(INFN)",
    "Coherent Corp": "相干公司(COHR)",
    "Fabrinet": "法布里内特(FN)",
    "Celestica": "天弘(CLS)",
    "Vertiv Holdings": "维谛技术(VRT)",
    "Modine Manufacturing": "莫丁制造(MOD)",
    "Generac Holdings": "杰纳拉克(GNRC)",
    "Vistra Corp": "维斯特拉(VST)",
    "Constellation Energy": "星座能源(CEG)",
    "Talen Energy": "塔伦能源(TLN)",
    "GE Vernova": "通用电气韦尔诺瓦(GEV)",
    "NuScale Power": "纽斯凯尔电力(SMR)",
    "Oklo Inc": "Oklo(OKLO)",
    "Marvell": "迈威尔(MRVL)",
    "Broadcom": "博通(AVGO)",
    "Alphabet": "谷歌母公司Alphabet",
    "Nvidia": "英伟达(NVDA)",
    "Lumentum": "鲁门特姆(LITE)",
    "Roundhill": "圆山投资",

    # ========== 动作/事件（分析师行为 + 市场行为）==========
    "Reiterates Outperform Rating": "重申跑赢大盘评级",
    "Reiterates Buy Rating": "重申买入评级",
    "Reiterates Overweight Rating": "重申超配评级",
    "Reiterates Market Perform": "重申与大盘持平",
    "Reiterates Neutral Rating": "重申中性评级",
    "Maintains Outperform Rating": "维持跑赢大盘评级",
    "Maintains Overweight Rating": "维持超配评级",
    "Maintains Buy Rating": "维持买入评级",
    "Maintains Hold Rating": "维持持有评级",
    "Maintains Sell Rating": "维持卖出评级",
    "Maintains Market Perform": "维持与大盘持平",
    "Initiates Coverage With Buy": "首次覆盖给予买入评级",
    "Initiates Coverage With Outperform": "首次覆盖给予跑赢大盘评级",
    "Initiates Coverage With Overweight": "首次覆盖给予超配评级",
    "Initiates Coverage With Hold": "首次覆盖给予持有评级",
    "Initiates Coverage With Sell": "首次覆盖给予卖出评级",
    "Initiates Coverage With Neutral": "首次覆盖给予中性评级",
    "Initiates With Buy": "首次覆盖给予买入",
    "Initiates With Outperform": "首次覆盖给予跑赢大盘",
    "Initiates Coverage On": "首次覆盖",
    "Raises Price Target to": "目标价上调至",
    "Raises Price Target From": "目标价上调",
    "Raises PT From": "目标价上调",
    "Raises PT to": "目标价上调至",
    "Lowers Price Target to": "目标价下调至",
    "Lowers Price Target From": "目标价下调",
    "Lowers PT From": "目标价下调",
    "Lowers PT to": "目标价下调至",
    "Raises Price Target": "上调目标价",
    "Lowers Price Target": "下调目标价",
    "Raises PT": "上调目标价",
    "Lowers PT": "下调目标价",
    "Upgrades to Buy": "上调评级至买入",
    "Upgrades to Outperform": "上调评级至跑赢大盘",
    "Upgrades to Overweight": "上调评级至增持",
    "Upgrades to Strong Buy": "上调评级至强烈买入",
    "Downgrades to Hold": "下调评级至持有",
    "Downgrades to Sell": "下调评级至卖出",
    "Downgrades to Underperform": "下调评级至跑输大盘",
    "Downgrades to Underweight": "下调评级至减持",
    "Downgrades to Market Perform": "下调评级至与大盘持平",
    "Upgrades": "上调评级",
    "Downgrades": "下调评级",
    "Strong Buy": "强烈买入",
    "Outperform": "跑赢大盘",
    "Underperform": "跑输大盘",
    "Market Perform": "与大盘持平",
    "Overweight": "超配",
    "Underweight": "低配",
    "Sell-Off": "抛售",
    "Pullback": "回调",
    "Plunge": "暴跌",
    "Beat Expectations": "超预期",
    "Missed Expectations": "不及预期",
    "Beat Estimates": "超预期",
    "Missed Estimates": "不及预期",
    "Top Line Beat": "营收超预期",
    "Bottom Line Beat": "利润超预期",
    "Powering": "驱动",
    "Cashing In": "获利套现",
    "Line Up to Challenge": "排队挑战",
    "Line Up to": "排队",
    "Sets Stage for": "为...铺路",
    "Steps Up Quantum Security Efforts": "加速量子安全布局",
    "as Encryption Risks Accelerate": "因加密风险加剧",
    "Surge Sets Stage for": "飙升为...铺路",
    "U.S. Trading Debut": "美国上市首秀",
    "Trading Debut": "交易首秀",
    "Steps Up": "加速推进",
    "as Risks Accelerate": "随着风险加剧",
    "Nears $34B": "逼近340亿美元",

    # ========== 指标/术语 ==========
    "Capital Expenditure": "资本支出(CapEx)",
    "Annual Recurring Revenue": "年度经常性收入(ARR)",
    "Free Cash Flow": "自由现金流",
    "Gross Margin": "毛利率",
    "Operating Margin": "营业利润率",
    "Price-to-Earnings": "市盈率",
    "Enterprise Value": "企业价值",
    "Market Cap": "市值",
    "Dividend Yield": "股息率",
    "Earnings Per Share": "每股收益(EPS)",
    "Revenue Growth": "营收增长",
    "Earnings Growth": "盈利增长",
    "P/E Ratio": "市盈率",
    "Price Target": "目标价",
    "Market Capitalization": "市值",
    "Total Addressable Market": "总可寻址市场(TAM)",
    "Return on Equity": "净资产收益率(ROE)",
    "Return on Invested Capital": "投资资本回报率(ROIC)",
    "Debt-to-Equity": "负债权益比",
    "YTD": "年内至今",
    "AUM": "管理资产规模(AUM)",
    "TAM": "总可寻址市场",
    "Bookings": "订单额",
    "Backlog": "积压订单",
    "Pipeline": "项目储备",
    "Churn Rate": "流失率",
    "Net Retention": "净留存率",

    # ========== 产品/行业/赛道 ==========
    "Semiconductor": "半导体",
    "Data Center": "数据中心",
    "Artificial Intelligence": "人工智能(AI)",
    "Machine Learning": "机器学习",
    "Generative AI": "生成式AI",
    "Large Language Model": "大语言模型(LLM)",
    "Graphic Processing Unit": "图形处理器(GPU)",
    "Central Processing Unit": "中央处理器(CPU)",
    "Tensor Processing Unit": "张量处理器(TPU)",
    "Application-Specific Integrated Circuit": "专用集成电路(ASIC)",
    "High Bandwidth Memory": "高带宽内存(HBM)",
    "Double Data Rate": "双倍数据速率(DDR)",
    "Solid State Drive": "固态硬盘(SSD)",
    "Hard Disk Drive": "机械硬盘(HDD)",
    "Optical Networking": "光网络",
    "Active Electrical Cables": "有源电缆(AEC)",
    "Co-Packaged Optics": "共封装光学(CPO)",
    "Quantum Computing": "量子计算",
    "Quantum Security": "量子安全",
    "Self-Driving": "自动驾驶",
    "Autonomous Vehicle": "自动驾驶汽车",
    "Electric Vehicle": "电动车",
    "Renewable Energy": "可再生能源",
    "Nuclear Energy": "核能",
    "Clean Energy": "清洁能源",
    "Cloud Computing": "云计算",
    "Edge Computing": "边缘计算",
    "Cyber Security": "网络安全",
    "Encryption": "加密",
    "Blockchain": "区块链",
    "GPU": "GPU",
    "CPU": "CPU",
    "ASIC": "ASIC芯片",
    "HBM": "高带宽内存",
    "DDR5": "DDR5内存",
    "DRAM": "DRAM存储",
    "NAND": "NAND闪存",
    "SSD": "固态硬盘",

    # ========== 场景/情绪 ==========
    "Bullish": "看涨",
    "Bearish": "看跌",
    "Volatility": "波动率",
    "Momentum": "动能",
    "Correction": "回调修正",
    "Rebound": "反弹",
    "Rally": "上涨",
    "Surge": "飙升",
    "Crash": "崩盘",
    "Under the Radar": "低调的",
    "Runaway": "暴涨的",
    "Boom": "繁荣/爆发",
    "Frenzy": "狂热",
    "Meltdown": "熔断/暴跌",
    "Rout": "溃败",

    # ========== 财报/季度 ==========
    "Fiscal Year": "财年",
    "Fourth Quarter": "第四季度",
    "Third Quarter": "第三季度",
    "Second Quarter": "第二季度",
    "First Quarter": "第一季度",
    "Q4 Earnings": "Q4财报",
    "Q3 Earnings": "Q3财报",
    "Q2 Earnings": "Q2财报",
    "Q1 Earnings": "Q1财报",
    "Quarterly Results": "季度业绩",
    "Annual Results": "年度业绩",
    "Earnings Call": "财报电话会",
    "Earnings Report": "财报报告",
    "Earnings Season": "财报季",
    "Pre-Earnings": "财报前",
    "Post-Earnings": "财报后",
    "Earnings Preview": "财报前瞻",
    "Earnings Recap": "财报回顾",
    "Guidance": "业绩指引",
    "Forward Guidance": "前瞻指引",
    "Revenue Guidance": "营收指引",
    "Profit Guidance": "利润指引",
    "Consensus Estimate": "市场一致预期",
    "Top and Bottom Line": "营收和利润",
    "Revenue": "营收",
    "Profit": "利润",
    "Outlook": "展望",
    "Forecast": "预测",

    # ========== 常见句式/短语 ==========
    "Still Have A Lot More Upside": "仍有较大上行空间",
    "Trades at a Discount": "折价交易",
    "Next Trillion-Dollar Opportunity": "下一个万亿美元机会",
    "May Be the Biggest Winner": "可能是最大赢家",
    "Only One Will Match The": "只有一家能匹配",
    "Here Is What a $10,000 Investment Could Return": "看看$10,000投资能获得多少回报",
    "Top Stock Picks for 2026": "2026年首选股票",
    "Best Stocks to Buy Now": "当前最佳买入标的",
    "Why It's Time to Buy": "为什么现在是买入时机",
    "Why It's Time to Sell": "为什么现在是卖出时机",
    "Should You Buy the Dip": "是否应该逢低买入",
    "Should You Buy": "是否应该买入",
    "Is It Too Late to Buy": "是否已错过买入时机",
    "Here's Why Shares Are Moving Today": "股价今日波动原因",
    "Here's Why Shares Popped Today": "股价今日大涨原因",
    "Here's Why Shares Fell Today": "股价今日下跌原因",
    "Here's What Analysts Are Saying": "以下是分析师观点",
    "Here's What to Expect": "以下是预期",
    "Here's What You Need to Know": "以下是你需要了解的",
    "What Wall Street Is Saying": "华尔街怎么看",
    "What Analysts Are Saying": "分析师怎么看",
    "Street Says Buy": "华尔街建议买入",
    "Is a Strong Buy": "是强力买入标的",
    "Is a Buy Right Now": "当下是否值得买入",
    "Is It a Buy": "是否值得买入",
    "Got $10,000?": "手上有$10,000？",
    "How Much": "押注了多少",
    "Are You Really Betting On": "你到底在押注什么",
    "Reveals Why He Still Likes": "透露为何仍看好",
    "Possible Reasons Why": "可能的原因",
    "Chart of the Day": "今日图表",
    "ETF Inflows Top": "ETF资金流入突破",
    "at the Halfway Point of": "在...年中节点",
    "Is the Memory Rally Still Alive After": "存储芯片反弹在...后是否仍在",
    "New Memory ETFs": "新存储ETF",
    "Under the Radar AI Chip Stocks": "低调的AI芯片股",
    "Thoughts on": "对...的看法",
    "Why It May": "为何它可能",
    "Driving": "推动",
    "Despite": "尽管",
    "Peak Levels": "历史高点",
    "Buy More": "继续买入",
    "Investors": "投资者",
    "Analyst": "分析师",
    "Wall Street": "华尔街",
    "Chipmakers": "芯片制造商",
    "League Tables": "排行榜",
    "Paying for the": "为...买单",
    "Big Tech is paying for the": "科技巨头正在为",
    "and chipmakers are cashing in": "买单，芯片制造商从中获利",

    # ========== 翻译引擎通用词（放在最后，短词优先度低）==========
    # 注意：这些是辅助替换，解决半翻译残留
    " Says ": "称",
    "Says ": "称",
    " Is ": "",
    "Are the Best Ways to Play the Revival.": "是布局复苏的最佳选择。",
    "The Nuclear Energy Comeback Is Real. These 3 Energy ": "核能复苏是真的。这3只能源",
    "Dow Jones Futures: Watch ": "道指期货：关注",
    "As Market Sets Up; Big ": "市场蓄势待发；重磅",
    "Why Today's Small ": "为什么今天微小的",
    "Could Become Tomorrow's Retirement Engine": "可能成为明天的退休引擎",
    "Here Are": "以下是",
    "Here Is What a": "看看",
    "Here Is What": "看看",
    "Investment Could Return": "投资可能获得多少回报",
    "Energy Stocks ": "能源股",
    "Will Be Worth This In": "估值将达到",
    "Price Prediction: ": "股价预测：",
    "Sector Update: ": "板块快讯：",
    "Advance Late Afternoon": "午后走高",
    "Prediction: ": "预测：",
    "Nvidia CEO Jensen Huang Said ": "英伟达CEO黄仁勋称",
    "Is Bullish on ": "看涨",
    "Bullish on ": "看涨",
    "Taiwan Semiconductor's": "台积电的",
    "Will Soar on July 17": "将在7月17日飙升",
    "Got $10,000? Broadcom vs Marvell: Only One Will Match The AI Hype": "手上有$10,000？博通vs迈威尔：只有一家能匹配AI热潮",
    "5 Under the Radar AI Chip Stocks Powering the Data Center Boom": "5只低调AI芯片股推动数据中心繁荣",
    "Goldman Sachs Says Optical Networking Is AI's Next Trillion-Dollar Opportunity. Lumentum May Be the Biggest Winner": "高盛称光网络是AI的下一个万亿机会，Lumentum或是最大赢家",
    "ETF League Tables: Roundhill AUM Nears $34B": "ETF排行榜：Roundhill管理资产规模逼近340亿美元",
    "New Memory ETFs Line Up to Challenge Runaway DRAM": "新存储ETF排队挑战暴涨的DRAM",
    "Runaway DRAM": "暴涨的DRAM",
}

# 正则句式翻译模式（处理：主体 + 动词 + 宾语 的标准财经标题结构）
FINANCE_PATTERNS = [
    # "XXX Stock Surges/Plunges/Rallies After YYY"
    (re.compile(r'(.+?)\s+(?:Stock|Shares|Share Price)\s+(Surge|Plunge|Rally|Jump|Drop|Fall|Sink|Climb|Tumble|Soar|Slide|Slip)\s*(?:After|On|Following|As|Amid)?\s*(.*)', re.I),
     lambda m: f"{m.group(1)}股价{m.group(2)}，因{m.group(3) if m.group(3) else '市场波动'}"),
    # "XXX Surges/Plunges/Rallies After YYY"
    (re.compile(r'^(.+?)\s+(Surges|Plunges|Rallies|Jumps|Drops|Falls|Sinks|Climbs|Tumbles|Soars|Slides|Slips)\s*(?:After|On|Following|As|Amid)?\s*(.*)', re.I),
     lambda m: f"{m.group(1)}{m.group(2)}，因{m.group(3) if m.group(3) else '市场波动'}"),
    # "Why XXX Stock Is Falling/Surging/Rallying Today"
    (re.compile(r'Why\s+(.+?)\s+(?:Stock|Shares)?\s*(?:Is|Are)\s+(Falling|Surging|Rallying|Dropping|Jumping|Sliding)\s*(Today|Now|Monday|Tuesday|Wednesday|Thursday|Friday)?', re.I),
     lambda m: f"为何{m.group(1)}今日{m.group(2)}"),
    # "XXX Reports Q2 Earnings, Revenue Beat/Miss"
    (re.compile(r'(.+?)\s+Reports?\s+(Q[1-4]|Fourth|Third|Second|First)\s*(Quarter)?\s*(Earnings|Results)', re.I),
     lambda m: f"{m.group(1)}发布{m.group(2)}季度财报"),
    # "XXX Beats/Misses Q2 Estimates"
    (re.compile(r'(.+?)\s+(Beats?|Misses?)\s+(Q[1-4]|Fourth|Third|Second|First)\s*(Quarter)?\s*(Estimates?|Expectations?)', re.I),
     lambda m: f"{m.group(1)}{m.group(2)}了{m.group(3)}季度预期"),
    # "XXX Raises/Lowers Full-Year Guidance"
    (re.compile(r'(.+?)\s+(Raises?|Lowers?|Cuts?|Boosts?)\s+(Full-Year|FY\d*|Annual|Quarterly|Q[1-4])\s+(Guidance|Outlook|Forecast|Revenue|Profit)', re.I),
     lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{m.group(4)}"),
    # "Is XXX Stock a Buy/Sell/Hold Before Earnings?"
    (re.compile(r'Is\s+(.+?)\s+(?:Stock|Shares?)\s+a\s+(Buy|Sell|Hold)\s*(?:Before|Ahead of|After)\s*(Earnings|Q[1-4])?', re.I),
     lambda m: f"{m.group(1)}在{m.group(3) or '当前'}是否值得{m.group(2)}"),
    # "XXX Stock: Buy, Sell, or Hold?"
    (re.compile(r'(.+?)\s+(?:Stock|Shares?):\s*(Buy|Sell|Hold)\s*(?:,|or)?\s*(Buy|Sell|Hold)?\s*,?\s*(Buy|Sell|Hold)?\?', re.I),
     lambda m: f"{m.group(1)}：买入、卖出还是持有？"),
    # "XXX Announces YYY" / "XXX Unveils YYY"
    (re.compile(r'(.+?)\s+(Announces?|Unveils?|Launches?|Reveals?|Introduces?)\s+(.+)', re.I),
     lambda m: f"{m.group(1)}{m.group(2)}：{m.group(3)}"),
    # "XXX Gets/Receives Upgrade/Downgrade from YYY"
    (re.compile(r'(.+?)\s+(?:Gets?|Receives?|Sees?)\s+(?:an?\s+)?(Upgrade|Downgrade|Price Target)\s*(?:from|by)?\s*(.+)?', re.I),
     lambda m: f"{m.group(1)}获{m.group(3) or '分析师'}{m.group(2)}"),
    # "XXX PT Raised/Lowered/Cut at YYY"
    (re.compile(r'(.+?)\s+(?:PT|Price Target)\s+(Raised|Lowered|Cut|Boosted|Increased|Slashed)\s*(?:at|by)?\s*(.+)?', re.I),
     lambda m: f"{m.group(3) or '分析师'}{m.group(2)}了{m.group(1)}目标价"),
    # "Here's Why It's (Not) Too Late to Buy XXX"
    (re.compile(r"Here.s\s+Why\s+(?:It.s|It\s+Is)\s+(?:Not\s+)?Too\s+Late\s+to\s+Buy\s+(.+)", re.I),
     lambda m: f"为什么现在买入{m.group(1)}仍为时不晚"),
    # "What XXX's Q2 Earnings Mean for YYY"
    (re.compile(r"What\s+(.+?)(?:'s)?\s+(Q[1-4]|Fourth|Third|Second|First)\s*(?:Quarter)?\s*Earnings\s*(?:Mean|Say)\s*(?:for|about)\s*(.+)", re.I),
     lambda m: f"{m.group(1)}{m.group(2)}季度财报对{m.group(3)}意味着什么"),
    # "XXX Is Down/Up X%: Should You Buy?"
    (re.compile(r'(.+?)\s+(?:Is|Stock\s+Is)\s+(Down|Up)\s+(\d+[\.,]?\d*%?)\s*(?:Should|Is\s+It)', re.I),
     lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}，是否应该买入？"),
    # "XXX vs YYY: Which Is the Better Buy?"
    (re.compile(r'(.+?)\s+vs\.?\s+(.+?):\s*Which\s+(?:Is|Stock\s+Is)\s*(?:the\s+)?Better\s+Buy\??', re.I),
     lambda m: f"{m.group(1)} vs {m.group(2)}：哪个更值得买入？"),
]

def translate_en_to_zh(text):
    """翻译英文标题到中文：先查缓存 → 正则句式匹配 → 术语映射 → 后处理"""
    if not text:
        return text
    if not any(c.isascii() and c.isalpha() for c in text):
        return text

    cache = _load_translation_cache()
    cache_key = hashlib.md5(text.encode()).hexdigest()
    if cache_key in cache:
        return cache[cache_key]

    result = text

    # 第1步：正则句式匹配（优先尝试完整句式翻译）
    for pattern, replacer in FINANCE_PATTERNS:
        m = pattern.search(result)
        if m:
            try:
                result = replacer(m)
                # 句式匹配成功后，继续用术语映射处理剩余英文
                break
            except:
                pass

    # 第2步：术语映射（按长度降序，长术语优先）
    sorted_terms = sorted(FINANCE_TERMS.items(), key=lambda x: len(x[0]), reverse=True)
    for en_term, zh_term in sorted_terms:
        result = result.replace(en_term, zh_term)

    # 第3步：后处理 — 清理残留
    # 去掉多余空格
    result = re.sub(r'\s+', ' ', result).strip()
    # 处理残留的 "Stock" / "Shares" 单词（如果前面已经是中文公司名）
    result = re.sub(r'股票\s+股票', '股票', result)
    result = re.sub(r'股票\s*(飙升|下跌|上涨|暴跌|大涨)', r'\1', result)
    result = re.sub(r'(?<=[\u4e00-\u9fff])\s+(Stock|Shares|Share)', '', result)
    result = re.sub(r'\s+(股票|股价)', '', result)
    # 处理 "称XXX" 后面多余空格
    result = re.sub(r'称\s+', '称', result)
    # 处理句首句尾空白
    result = result.strip()

    if result != text and any('\u4e00' <= c <= '\u9fff' for c in result):
        cache[cache_key] = result
        _save_translation_cache(cache)
        return result

    return text

def translate_news_items(items):
    """批量翻译新闻条目的 title"""
    for item in items:
        if item.get("title") and "(" not in item["title"][:1]:  # 跳过占位文本
            item["title_zh"] = translate_en_to_zh(item["title"])
        else:
            item["title_zh"] = item.get("title", "")
    return items

# ============================================================
# 一、线1 — Capex监控：拉取关键公司股价
# ============================================================

def fetch_sina_stock(symbol):
    """新浪实时股价 — 美股gb_格式"""
    try:
        r = requests.get(f"https://hq.sinajs.cn/list={symbol}", timeout=10,
                         headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = "gbk"
        if '"' in r.text:
            parts = r.text.split('"')[1].split(",")
            if len(parts) > 2 and parts[1]:
                price = float(parts[1])
                change_amt = float(parts[2]) if parts[2] else 0
                prev_close = price - change_amt
                pct = (change_amt / prev_close * 100) if prev_close != 0 else 0
                return price, pct, prev_close
    except Exception as e:
        print(f"  [股价] {symbol} 获取失败: {e}")
    return None, None, None

capex_tickers = {
    "MSFT": "gb_msft", "GOOGL": "gb_googl",
    "AMZN": "gb_amzn", "META": "gb_meta",
    "MRVL": "gb_mrvl", "NVDA": "gb_nvda"
}

# 持仓映射（从 holdings.yaml 同步）
# GOOGL 币安已于 2026-07-07 清仓，DRAM 币安已加仓至 57 股均价 $66.85
holdings_map = {
    "MRVL": {"shares": 29.192, "value_cny": 59098, "cost_usd": 287.74, "note": "AI芯片/数据中心互连(币安)", "line": "线1"},
    "DRAM": {"shares": 57, "value_cny": 18570, "cost_usd": 66.85, "note": "AI服务器存储(币安)", "line": "线1"},
}

capex_data = {}
capex_pct = {}
capex_price = {}
print("【线1】抓取股价...")
for name, sym in capex_tickers.items():
    price, pct, prev_close = fetch_sina_stock(sym)
    if price is not None:
        sign = "+" if pct >= 0 else ""
        capex_data[name] = f"${price:.2f} ({sign}{pct:.2f}%)"
        capex_pct[name] = pct
        capex_price[name] = price
        print(f"  {name}: ${price:.2f} ({sign}{pct:.2f}%)")
    else:
        capex_data[name] = "N/A"
        capex_pct[name] = 0
        capex_price[name] = None

# ============================================================
# 二、新闻抓取函数
# ============================================================

def fetch_yahoo_finance_rss(ticker, limit=5):
    """Yahoo Finance 个股 RSS — 含 description 摘要"""
    items = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        if r.ok:
            items_block = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
            for block in items_block[:limit]:
                title_m = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', block, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
                date_m = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
                desc_m = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
                title = ""
                if title_m:
                    title = (title_m.group(1) or title_m.group(2) or "").strip()
                link = link_m.group(1).strip() if link_m else ""
                pub_date = date_m.group(1).strip() if date_m else ""
                # 抓取摘要（去掉HTML标签，截取前200字符）
                desc = ""
                if desc_m:
                    raw_desc = desc_m.group(1).strip()
                    raw_desc = re.sub(r'<[^>]+>', '', raw_desc)  # 去HTML标签
                    raw_desc = re.sub(r'&[a-z]+;', ' ', raw_desc)  # 去HTML实体
                    desc = raw_desc[:200].strip()
                if title:
                    items.append({
                        "title": title,
                        "link": link, "source": "Yahoo Finance",
                        "date": pub_date, "ticker": ticker,
                        "desc": desc
                    })
    except Exception as e:
        print(f"  [Yahoo RSS] {ticker} 失败: {e}")
    return items

def fetch_bing_news(query, limit=5):
    """Bing News RSS"""
    items = []
    try:
        url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        if r.ok:
            items_block = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
            for block in items_block[:limit*2]:
                title_m = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
                date_m = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
                title = title_m.group(1).strip() if title_m else ""
                if not title:
                    continue
                if title in ["搜索 - Microsoft 必应", "Bing 新闻", "Microsoft 必应"]:
                    continue
                if "必应" in title or "bing.com" in title.lower():
                    continue
                link = link_m.group(1).strip() if link_m else ""
                pub_date = date_m.group(1).strip() if date_m else ""
                items.append({
                    "title": title,
                    "link": link, "source": "Bing News",
                    "date": pub_date, "query": query
                })
    except Exception as e:
        print(f"  [Bing News] '{query}' 失败: {e}")
    return items

def deduplicate(items, key="title"):
    """去重：完全匹配 + 子串包含（阈值60%）"""
    seen = []
    result = []
    for item in items:
        title = item.get(key, "").lower().strip()
        if not title or len(title) < 15:
            continue  # 跳过过短标题
        is_dup = False
        for s in seen:
            # 完全匹配 或 子串包含度>60%
            if title == s:
                is_dup = True
                break
            if len(title) > 30 and len(s) > 30:
                shorter = title if len(title) < len(s) else s
                longer = s if len(title) < len(s) else title
                if shorter in longer:
                    is_dup = True
                    break
        if not is_dup:
            seen.append(title)
            result.append(item)
    return result

# 低质量新闻标题模式（负向过滤）
LOW_QUALITY_PATTERNS = [
    r'(?:Is|Are)\s+(?:It|They)\s+(?:Too\s+Late|Time)\s+to\s+(?:Buy|Sell|Invest)',  # 泛泛的"是否太晚买入"
    r'Here.s\s+Why\s+\w+\s+(?:Stock\s+)?(?:Is|Are)\s+(?:Moving|Falling|Rising|Up|Down)\s+Today',  # 每日涨跌解释（内容空洞）
    r'What.s\s+(?:Going\s+On|Happening)\s+With',  # "XX怎么回事"（clickbait）
    r'Should\s+You\s+(?:Buy|Sell)\s+\w+\s+(?:Stock|Shares)\s+(?:Right\s+)?Now',  # 泛泛买入建议
    r'(?:Better\s+Buy|Better\s+Stock)\s*(?::|,)\s*\w+\s+vs',  # 泛A vs B对比
    r'Top\s+\d+\s+(?:Stocks?|Picks?|Investment)',  # "Top N Stock" 列表文
    r'Best\s+\w+\s+(?:Stocks?|to\s+Buy)',  # "Best X Stocks"
    r'(?:A|The)\s+\d+\s+(?:Best|Top)\s+\w+\s+(?:Stocks?|Picks?)',  # 列表类标题
    r'Prediction:\s+.+\s+(?:Will|Could|Might|May)\s+(?:Surge|Soar|Skyrocket|Plunge|Crash)',  # 预测性标题
    r'\$\d+,?\d*\s+Investment\s+(?:Could|Would|Might)\s+(?:Become|Be\s+Worth|Turn\s+Into)',  # "$X investment could become..."
    r"Here.s\s+How\s+Much\s+(?:\$?\d+)?\s*(?:You|An?\s+Investor)",  # "Here's how much..."
    r'(?:If\s+)?You\s+(?:Invested|Bought)\s+\$?\d+',  # "If you invested $X"
    r'(?:Missed\s+the\s+Boat|Too\s+Late\s+to\s+Buy)',  # FOMO标题
    r'(?:Billionaire|Millionaire)\s+(?:Investor\s+)?Says',  # 亿万富翁说...
    r'\d+\s+(?:Reasons?|Things?)\s+(?:Why|You|To)',  # "5 Reasons Why..."
    r'(?:Bubble|Crash|Meltdown)\s+(?:Is\s+)?(?:Coming|Near|Imminent|Here)',  # 崩溃/泡沫恐慌文
]

def score_news_quality(item, tier1_keywords, tier2_keywords=None):
    """
    新闻质量评分（0-10分）
    - tier1: 必须关键词，命中1个+3分，命中2个+5分
    - tier2: 加分关键词，每个+1分（上限3分）
    - 标题长度: 30-80字符 +1分, >80字符 +2分（太短或太长扣分）
    - 来源加分: Yahoo Finance +1分
    - 负向过滤: 命中低质量模式 -5分
    - 有description摘要 +1分
    """
    if tier2_keywords is None:
        tier2_keywords = []

    title = item.get("title", "").strip()
    title_lower = title.lower()
    score = 0

    # 1) 标题长度评分
    tlen = len(title)
    if tlen < 20:
        score -= 3  # 太短，可能是碎片/垃圾
    elif tlen < 30:
        score -= 1
    elif 30 <= tlen <= 100:
        score += 1
    else:
        score += 0  # 超长标题不加分

    # 2) 负向过滤
    for pattern in LOW_QUALITY_PATTERNS:
        if re.search(pattern, title, re.I):
            score -= 4
            break

    # 3) Tier1 必须关键词
    t1_hits = sum(1 for kw in tier1_keywords if kw.lower() in title_lower)
    if t1_hits >= 2:
        score += 5
    elif t1_hits >= 1:
        score += 3
    else:
        score -= 2  # 关键主题词一个都没命中

    # 4) Tier2 加分关键词
    if tier2_keywords:
        t2_hits = sum(1 for kw in tier2_keywords if kw.lower() in title_lower)
        score += min(t2_hits, 3)

    # 5) 有摘要 +1
    if item.get("desc", "").strip():
        score += 1

    # 6) 来源加分
    source = item.get("source", "")
    if "yahoo" in source.lower():
        score += 0  # Yahoo中性，不加不扣

    return score

def filter_quality(items, min_score=3, max_items=15):
    """按质量分排序，取Top N"""
    scored = [(score_news_quality(item, [], []), item) for item in items]
    # 先计算临时分用于粗筛，保留>0的
    scored = [(s, item) for s, item in scored if s > -3]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:max_items]]

def filter_by_keywords(items, keywords, limit=5):
    """简单关键词过滤（保留兼容，但主逻辑用 score_news_quality）"""
    filtered = []
    for item in items:
        title_lower = item["title"].lower()
        if any(kw.lower() in title_lower for kw in keywords):
            filtered.append(item)
    return filtered[:limit]

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%m-%d")
    except:
        return date_str[:16] if date_str else ""

# ============================================================
# 三、线1 — Capex 新闻（Yahoo RSS + Bing聚合，质量评分筛选）
# ============================================================

print("\n【线1】抓取Capex相关新闻...")
is_earnings_season = datetime(2026, 7, 22) <= today <= datetime(2026, 8, 5)
is_monday = today.weekday() == 0

# Tier1 必须关键词：高价值信号词（财报/评级/目标价/CapEx/指引）
CAPEX_TIER1 = ['earnings', 'revenue', 'guidance', 'upgrade', 'downgrade', 'price target',
               'capex', 'capital expenditure', 'data center', 'gpu', 'chip', 'semiconductor',
               'ai spend', 'outlook', 'forecast', 'beat', 'miss', 'profit']
# Tier2 加分关键词：主题相关但不强制
CAPEX_TIER2 = ['cloud', 'nvidia', 'amd', 'broadcom', 'mrvl', 'marvell', 'dram',
               'microsoft', 'google', 'amazon', 'meta', 'analyst', 'bullish', 'bearish',
               'growth', 'hbm', 'memory', 'server', 'optical', 'networking']

# 数据源1：Yahoo RSS（多ticker聚合）
capex_ticker_list = ["MRVL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "SMH", "AVGO", "AMD", "DRAM"]
if is_earnings_season or is_monday:
    capex_ticker_list.extend(["INTC", "ARM", "TSM", "MU"])

capex_news = []
for ticker in capex_ticker_list:
    yahoo_items = fetch_yahoo_finance_rss(ticker, limit=4)
    capex_news.extend(yahoo_items)

# 数据源2：Bing News 补充（搜索芯片/AI/CapEx相关）
try:
    bing_queries = ["AI chip capex", "data center spending", "semiconductor earnings"]
    for q in bing_queries:
        bing_items = fetch_bing_news(q, limit=3)
        for item in bing_items:
            item["source"] = "Bing News"
        capex_news.extend(bing_items)
except Exception as e:
    print(f"  [Bing News] 补充搜索失败: {e}")

# 质量评分筛选（使用tier1/tier2关键词）
scored_capex = []
for item in capex_news:
    s = score_news_quality(item, CAPEX_TIER1, CAPEX_TIER2)
    # Capex新闻要求更严：至少命中tier1或分>2
    title_lower = item.get("title", "").lower()
    t1_hit = any(kw.lower() in title_lower for kw in CAPEX_TIER1)
    if s >= 2 or t1_hit:
        scored_capex.append((s, item))

# 按分数排序取Top N，财报季取更多
scored_capex.sort(key=lambda x: x[0], reverse=True)
top_n = 15 if is_earnings_season or is_monday else 12
capex_news = [item for _, item in scored_capex[:top_n]]
capex_news = deduplicate(capex_news)[:top_n]

if not capex_news:
    capex_news.append({"title": "(今日无重大Capex相关新闻)", "source": "", "link": "", "date": ""})
else:
    print(f"  Capex新闻评分范围: {scored_capex[0][0] if scored_capex else 0} ~ {scored_capex[-1][0] if scored_capex else 0}")

# 翻译
capex_news = translate_news_items(capex_news)

# ============================================================
# 四、线2 — ARR 新闻（严格筛选：必须命中ARR/OpenAI/Anthropic核心关键词）
# ============================================================

print("\n【线2】抓取ARR新闻...")

# Tier1 ARR核心关键词：必须命中至少1个（严格）
ARR_TIER1 = ['openai', 'anthropic', 'chatgpt', 'claude', 'copilot', 'gemini',
             'llm', 'large language model', 'ai model', 'annual recurring revenue',
             'arr ', 'subscription revenue', 'recurring revenue']
# Tier2 加分关键词：AI商业变现相关
ARR_TIER2 = ['revenue', 'growth', 'enterprise', 'business', 'pricing', 'monetization',
             'adoption', 'api', 'enterprise ai', 'ai agent', 'agentic']

arr_news = []

# 数据源1：Yahoo RSS（从AI产业链ticker中筛选）
arr_ticker_list = ["MSFT", "GOOGL", "META", "NVDA", "AMZN", "AVGO", "AMD", "TSM"]
for ticker in arr_ticker_list:
    yahoo_items = fetch_yahoo_finance_rss(ticker, limit=5)
    arr_news.extend(yahoo_items)

# 数据源2：Bing News 直接搜索 OpenAI/Anthropic/ARR
try:
    for q in ["OpenAI revenue ARR", "Anthropic Claude enterprise", "ChatGPT subscription"]:
        bing_items = fetch_bing_news(q, limit=3)
        for item in bing_items:
            item["source"] = "Bing News"
        arr_news.extend(bing_items)
except Exception as e:
    print(f"  [Bing News] ARR搜索失败: {e}")

# 严格质量评分：必须命中ARR_TIER1
scored_arr = []
for item in arr_news:
    title_lower = item.get("title", "").lower()
    t1_hit = any(kw.lower() in title_lower for kw in ARR_TIER1)
    if not t1_hit:
        continue  # 核心关键词不命中直接跳过
    s = score_news_quality(item, ARR_TIER1, ARR_TIER2)
    if s >= 1:
        scored_arr.append((s, item))

scored_arr.sort(key=lambda x: x[0], reverse=True)
arr_news = [item for _, item in scored_arr[:8]]
arr_news = deduplicate(arr_news)[:6]

# Fallback：如果严格筛选后为空，用AI+revenue宽松筛选
if not arr_news:
    print("  [ARR] 严格筛选无结果，使用宽松fallback...")
    arr_fallback = []
    for ticker in ["MSFT", "NVDA", "GOOGL", "AMZN", "META"]:
        yahoo_items = fetch_yahoo_finance_rss(ticker, limit=3)
        arr_fallback.extend(yahoo_items)
    fallback_tier1 = ['openai', 'anthropic', 'chatgpt', 'claude', 'ai model', 'ai ',
                       'artificial intelligence', 'llm', 'gemini', 'copilot']
    fallback_tier2 = ['revenue', 'growth', 'enterprise', 'earnings', 'subscription']
    scored_fb = []
    for item in arr_fallback:
        s = score_news_quality(item, fallback_tier1, fallback_tier2)
        if s >= 1:
            scored_fb.append((s, item))
    scored_fb.sort(key=lambda x: x[0], reverse=True)
    arr_news = [item for _, item in scored_fb[:5]]

if not arr_news:
    arr_news.append({"title": "(今日无ARR更新新闻，ARR增速为季度数据，下次关键节点9月底)", "source": "", "link": "", "date": ""})
else:
    print(f"  ARR新闻评分范围: {scored_arr[0][0] if scored_arr else 'N/A'} ~ {scored_arr[-1][0] if scored_arr else 'N/A'}")

arr_news = translate_news_items(arr_news)

# ============================================================
# 五、线3 — 美股板块ETF资金流向 + 替代赛道扫描
# ============================================================

print("\n【线3】抓取美股板块数据...")
alt_news = []
alt_data = {}

# 5.1 美股主要板块ETF（新浪）
sector_etfs = {
    "QQQ": ("gb_qqq", "纳斯达克100"),
    "SPY": ("gb_spy", "标普500"),
    "XLK": ("gb_xlk", "科技板块"),
    "XLY": ("gb_xly", "可选消费"),
    "XLF": ("gb_xlf", "金融板块"),
    "XLE": ("gb_xle", "能源板块"),
}

for name, (sym, label) in sector_etfs.items():
    price, pct, _ = fetch_sina_stock(sym)
    if price is not None:
        alt_data[name] = {"price": price, "pct": pct, "label": label}
        print(f"  {name} ({label}): ${price:.2f} ({pct:+.2f}%)")
    else:
        alt_data[name] = {"price": None, "pct": 0, "label": label}

# 5.2 板块轮动信号
# 判断: 科技(QQQ+XLK) vs 其他板块的相对强弱
tech_pct = (alt_data.get("QQQ", {}).get("pct", 0) + alt_data.get("XLK", {}).get("pct", 0)) / 2
other_pct = (alt_data.get("XLY", {}).get("pct", 0) + alt_data.get("XLF", {}).get("pct", 0) + alt_data.get("XLE", {}).get("pct", 0)) / 3

if tech_pct > other_pct + 0.5:
    rotation_signal = "🟢 资金仍在科技/AI主线，无轮动信号"
elif tech_pct < other_pct - 0.5:
    rotation_signal = "🟡 资金从科技流向传统板块，关注轮动风险"
elif tech_pct < other_pct - 1.0:
    rotation_signal = "🔴 科技板块明显跑输，替代赛道信号加强"
else:
    rotation_signal = "⚪ 板块无明显分化，中性"

# 5.3 替代赛道新闻（从板块ETF相关ticker获取）
# 用 SPY/QQQ/XLF 相关关键词的 ticker 来获取板块轮动新闻
alt_news.extend(fetch_yahoo_finance_rss("SPY", limit=3))
alt_news.extend(fetch_yahoo_finance_rss("XLE", limit=2))
alt_news = filter_by_keywords(alt_news,
    ['sector', 'rotation', 'energy', 'financial', 'consumer', 'value', 'growth', 'defensive', 'cyclical'], limit=5)
alt_news = deduplicate(alt_news)[:5]
if not alt_news:
    alt_news.append({"title": "(今日无替代赛道信号)", "source": "", "link": "", "date": ""})

alt_news = translate_news_items(alt_news)

# ============================================================
# 六、暴跌股专项搜索
# ============================================================

print("\n【暴跌股专项搜索】...")
special_news = []
alert_tickers = []
for ticker, pct in capex_pct.items():
    if ticker in holdings_map and pct <= -3:
        alert_tickers.append(ticker)
        print(f"  ⚠️ {ticker} 跌 {pct:.1f}%，专项搜索利空新闻...")
        ticker_news = fetch_yahoo_finance_rss(ticker, limit=8)
        ticker_news = deduplicate(ticker_news)[:5]
        for n in ticker_news:
            n["alert_for"] = ticker
        special_news.extend(ticker_news)

special_news = translate_news_items(special_news)

# ============================================================
# 七、告警生成
# ============================================================

alerts = []
for name, pct in capex_pct.items():
    if pct <= -5:
        alerts.append({
            "level": "🚨", "ticker": name, "pct": pct,
            "msg": f"{name} 单日暴跌 {pct:.1f}%，需要立即关注！"
        })
    elif pct <= -3:
        alerts.append({
            "level": "⚠️", "ticker": name, "pct": pct,
            "msg": f"{name} 单日跌 {pct:.1f}%，关注是否CapEx相关负面"
        })

if not alerts:
    alerts.append({"level": "✅", "ticker": "", "pct": 0, "msg": "无异常波动"})

# ============================================================
# 八、投资建议引擎
# ============================================================

print("\n【投资建议引擎】计算中...")
days_to_earnings = (datetime(2026, 7, 22) - today).days

# 8.1 持仓盈亏计算
position_advice = []
for ticker, h in holdings_map.items():
    current_price = capex_price.get(ticker)
    if current_price is None:
        continue

    cost = h["cost_usd"]
    shares = h["shares"]
    pnl_pct = (current_price - cost) / cost * 100
    pnl_usd = (current_price - cost) * shares
    pnl_cny = pnl_usd * 6.796

    # 从最高点回撤（用新浪前一交易日收盘价作为近似）
    if pnl_pct >= 0:
        pnl_status = f"🟢 盈利 {pnl_pct:+.1f}%"
    elif pnl_pct >= -10:
        pnl_status = f"🟡 亏损 {pnl_pct:.1f}%"
    else:
        pnl_status = f"🔴 亏损 {pnl_pct:.1f}%"

    # 止损建议
    stop_loss_advice = ""
    if pnl_pct <= -15:
        stop_loss_advice = "🔴 触发止损线(-15%)，建议立即清仓"
    elif pnl_pct <= -10:
        stop_loss_advice = "⚠️ 接近止损线(-15%)，设置条件单"
    elif pnl_pct <= -5:
        stop_loss_advice = "🟡 浮亏扩大中，密切关注"

    # 止盈建议
    if pnl_pct >= 30:
        stop_loss_advice = "💰 盈利超30%，建议设置移动止盈(最高点回撤15%)"
    elif pnl_pct >= 20:
        stop_loss_advice = "📈 盈利超20%，可考虑部分止盈锁定利润"
    elif pnl_pct >= 10:
        stop_loss_advice = "✅ 盈利中，继续持有"

    position_advice.append({
        "ticker": ticker,
        "name": h["note"],
        "shares": shares,
        "cost": cost,
        "current": current_price,
        "pnl_pct": pnl_pct,
        "pnl_cny": pnl_cny,
        "status": pnl_status,
        "stop_loss": stop_loss_advice,
        "line": h["line"],
    })

# 8.2 线1建议（Capex）
line1_advice = ""
if is_earnings_season:
    line1_advice = "🔴 财报季进行中！每日追踪MSFT/GOOGL/META/AMZN Capex数据，等数据到手再做决策"
elif days_to_earnings <= 7:
    line1_advice = f"🟡 距Q2财报季仅{days_to_earnings}天！密切关注MRVL/DRAM/GOOGL持仓，季报前不做新操作"
else:
    line1_advice = f"🟢 距Q2财报季还有{days_to_earnings}天，Capex信号待季报发布后更新。当前仅监控股价波动"

# 检查MRVL是否触发减仓信号
mrvl_pct = capex_pct.get("MRVL", 0)
if mrvl_pct <= -5:
    line1_advice += "\n🔴 MRVL单日跌超5%，对照方法论：若连续3日跌幅>3%且无利好消息→减仓50%"

# 8.3 线2建议（ARR）
has_arr_news = any("无ARR" not in n.get("title", "") for n in arr_news)
if has_arr_news:
    line2_advice = "🟡 今日有ARR相关新闻，关注OpenAI/Anthropic收入增速是否放缓"
else:
    line2_advice = "🟢 今日无ARR重大更新。ARR增速为季度数据，下次关键节点9月底"

# 8.4 线3建议（替代赛道）
line3_advice = rotation_signal
if tech_pct > 0.5:
    line3_advice += "\n✅ AI/科技仍是主线，暂无替代赛道切换必要"
elif tech_pct < -1.0:
    line3_advice += "\n⚠️ 科技板块跑输，建议审视CRCL是否需要部分调仓"

# 8.5 综合操作清单
action_items = []

# CRCL超配检查
action_items.append("📋 CRCL占投资71.3%严重超配，建议减至50%以下（P1本月）")

# BitGo
action_items.append("📋 BitGo亏损69.6%，建议清仓认赔（P0立即）")

# MRVL止损
if mrvl_pct <= -3:
    action_items.append(f"⚠️ MRVL今日跌{mrvl_pct:.1f}%，设移动止盈：跌破$268(-10%)自动卖出")

# 还信用卡
action_items.append("📋 信用卡循环¥400,000需偿还，优先卖非核心仓(BitGo→优必选→TS→CRCL)")

# 财报季提醒
if days_to_earnings <= 7:
    action_items.append(f"🔔 {days_to_earnings}天后Q2财报季，提前准备Capex监控表格")

# ============================================================
# 九、生成日报
# ============================================================

print("\n生成日报...")
lines = []
lines.append("---")
lines.append(f"date: {today_str}")
lines.append("type: three-sell-lines-daily")
lines.append(f"earnings_season: {is_earnings_season}")
lines.append(f"version: v4")
lines.append("---")
lines.append("")
lines.append(f"# 三条卖出线 — 每日监控 ({today_str})")
lines.append("")
lines.append(f"> 自动生成 · {today.strftime('%H:%M')} · v4（含投资建议+新闻摘要）")
lines.append("")

# ── 线1 股价 ──
lines.append("## 线1：Capex 股价（代理指标）")
lines.append("")
lines.append("| 公司 | 股价 | 涨跌 | 关联持仓 |")
lines.append("|------|------|------|---------|")
holdings_label = {
    "MRVL": "29.192股 ¥59,098",
    "NVDA": "— (行业风向标)",
}
for name in ["MSFT", "GOOGL", "AMZN", "META", "MRVL", "NVDA"]:
    val = capex_data.get(name, "N/A")
    pct = capex_pct.get(name, 0)
    price_display = val.split(" (")[0] if val != "N/A" else "N/A"
    icon = "🔴" if pct <= -3 else ("🟡" if pct <= -1 else "")
    pct_display = f"{icon} {pct:+.2f}%" if val != "N/A" else "—"
    label = holdings_label.get(name, "—")
    lines.append(f"| {name} | {price_display} | {pct_display} | {label} |")
lines.append("")

# ── 线1 新闻 ──
lines.append("### 📰 Capex / 持仓股新闻")
lines.append("")
for n in capex_news:
    title = n["title"]
    title_zh = n.get("title_zh", "")
    desc = n.get("desc", "")
    source = n.get("source", "")
    ticker_tag = n.get("ticker", "")
    link = n.get("link", "")
    date_display = format_date(n.get("date", ""))
    date_part = f" | {date_display}" if date_display else ""
    source_part = f" · {source}" if source else ""
    ticker_part = f" [{ticker_tag}]" if ticker_tag else ""
    if link:
        lines.append(f"- [{title}]({link}){ticker_part}{source_part}{date_part}")
    else:
        lines.append(f"- {title}{ticker_part}{source_part}{date_part}")
    if title_zh and title_zh != title:
        lines.append(f"  > 📝 {title_zh}")
    if desc:
        lines.append(f"  > 📄 {desc}")
lines.append("")

# ── 暴跌专项 ──
if special_news:
    lines.append("### 🎯 暴跌股专项新闻")
    lines.append("")
    for n in special_news:
        title = n["title"]
        title_zh = n.get("title_zh", "")
        source = n.get("source", "")
        link = n.get("link", "")
        alert_for = n.get("alert_for", "")
        tag = f"**[{alert_for}]** " if alert_for else ""
        source_part = f" · {source}" if source else ""
        if link:
            lines.append(f"- {tag}[{title}]({link}){source_part}")
        else:
            lines.append(f"- {tag}{title}{source_part}")
        if title_zh and title_zh != title:
            lines.append(f"  > 📝 {title_zh}")
    lines.append("")

# ── 线2 ──
lines.append("## 线2：ARR 新闻（OpenAI / Anthropic）")
lines.append("")
for n in arr_news:
    title = n["title"]
    title_zh = n.get("title_zh", "")
    desc = n.get("desc", "")
    source = n.get("source", "")
    link = n.get("link", "")
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}")
    else:
        lines.append(f"- {title}{source_part}")
    if title_zh and title_zh != title:
        lines.append(f"  > 📝 {title_zh}")
    if desc:
        lines.append(f"  > 📄 {desc}")
lines.append("")

# ── 线3 ──
lines.append("## 线3：替代赛道 — 美股板块ETF")
lines.append("")
lines.append("| 板块 | 价格 | 涨跌 |")
lines.append("|------|------|------|")
for name in ["QQQ", "SPY", "XLK", "XLY", "XLF", "XLE"]:
    d = alt_data.get(name, {})
    price = f"${d['price']:.2f}" if d.get("price") else "N/A"
    pct = f"{d['pct']:+.2f}%" if d.get("price") else "—"
    lines.append(f"| {name} ({d.get('label', '')}) | {price} | {pct} |")
lines.append("")
lines.append(f"**板块轮动信号**: {rotation_signal}")
lines.append("")

lines.append("### 📰 替代赛道新闻")
lines.append("")
for n in alt_news:
    title = n["title"]
    title_zh = n.get("title_zh", "")
    desc = n.get("desc", "")
    source = n.get("source", "")
    link = n.get("link", "")
    source_part = f" · {source}" if source else ""
    if link:
        lines.append(f"- [{title}]({link}){source_part}")
    else:
        lines.append(f"- {title}{source_part}")
    if title_zh and title_zh != title:
        lines.append(f"  > 📝 {title_zh}")
    if desc:
        lines.append(f"  > 📄 {desc}")
lines.append("")

# ── 告警 ──
lines.append("## ⚡ 今日告警")
lines.append("")
for a in alerts:
    lines.append(f"- {a['level']} {a['msg']}")
lines.append("")

# ── 投资建议 ──
lines.append("## 💡 投资建议")
lines.append("")

lines.append("### 持仓盈亏速览")
lines.append("")
lines.append("| 标的 | 成本 | 现价 | 盈亏% | 盈亏¥ | 建议 |")
lines.append("|------|------|------|-------|-------|------|")
for pa in position_advice:
    lines.append(f"| {pa['ticker']}({pa['name']}) | ${pa['cost']:.2f} | ${pa['current']:.2f} | {pa['pnl_pct']:+.1f}% | ¥{pa['pnl_cny']:+,.0f} | {pa['stop_loss']} |")
lines.append("")

lines.append(f"### 线1（Capex）: {line1_advice}")
lines.append("")
lines.append(f"### 线2（ARR）: {line2_advice}")
lines.append("")
lines.append(f"### 线3（替代赛道）: {line3_advice}")
lines.append("")

lines.append("### 📋 综合操作清单")
lines.append("")
for item in action_items:
    lines.append(f"- {item}")
lines.append("")

# ── 状态 ──
if days_to_earnings > 0:
    lines.append(f"> 📅 距Q2财报季（7月22日）还有 **{days_to_earnings}** 天，股价为早期预警，非卖出信号")
else:
    lines.append("> 🔴 已进入Q2财报季！请每日关注Capex新闻")
lines.append("")
lines.append("---")
lines.append("相关文档：[[ai-stock-three-sell-lines-methodology]]")
lines.append("> 数据源：新浪财经（股价+ETF）+ Yahoo Finance RSS（多ticker聚合+摘要）+ 本地术语翻译")

# 写入
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ 日报已生成: {out_file.name}")
print(f"   股价: {len(capex_data)}只 | Capex新闻: {len(capex_news)}条 | 暴跌专项: {len(special_news)}条")
print(f"   ARR新闻: {len(arr_news)}条 | 替代赛道: {len(alt_news)}条 | 板块ETF: {len(alt_data)}个")
print(f"   告警: {len(alerts)}条 | 持仓建议: {len(position_advice)}个")

if days_to_earnings in [7, 3, 1, 0]:
    print(f"\n{'='*50}")
    print(f"🔔 提醒：距Q2财报季还有 {days_to_earnings} 天！")
    print(f"   请关注 MSFT/GOOGL/META/AMZN Capex数据")
    print(f"{'='*50}")

if alert_tickers:
    print(f"\n{'='*50}")
    print(f"🚨 持仓股告警: {', '.join(alert_tickers)}")
    print(f"{'='*50}")


# ============================================================
# 十、飞书推送（interactive卡片）
# ============================================================

def build_lark_card():
    """构建飞书 interactive 卡片 JSON — 三线完整 + 中文翻译 + 投资建议"""
    elements = []

    # --- 线1 股价表 ---
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "**📊 线1：Capex 股价**"}
    })
    table_lines = ["| 公司 | 股价 | 涨跌 | 持仓 |", "|---|---|---|---|"]
    for name in ["MSFT", "GOOGL", "AMZN", "META", "MRVL", "NVDA"]:
        val = capex_data.get(name, "N/A")
        pct = capex_pct.get(name, 0)
        price_display = val.split(" (")[0] if val != "N/A" else "N/A"
        icon = "🔴" if pct <= -3 else ("🟡" if pct <= -1 else "")
        pct_str = f"{icon}{pct:+.2f}%" if val != "N/A" else "—"
        label_map = {"MRVL": "29.2股 ¥5.9万", "NVDA": "风向标"}
        table_lines.append(f"| {name} | {price_display} | {pct_str} | {label_map.get(name, '—')} |")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(table_lines)}
    })

    # --- 线1 新闻（前5条，中文翻译优先） ---
    elements.append({"tag": "hr"})
    news_lines = ["**📰 持仓股新闻**"]
    for n in capex_news[:5]:
        title_en = n["title"]
        title_zh = n.get("title_zh", "")
        # 飞书卡片优先展示中文翻译，如果翻译不完整则显示英文
        if title_zh and title_zh != title_en and len(title_zh) > 5:
            display_title = title_zh
        else:
            display_title = title_en
        source = n.get("source", "")
        news_lines.append(f"- {display_title} · {source}" if source else f"- {display_title}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(news_lines)}
    })

    # --- 线2 ARR ---
    elements.append({"tag": "hr"})
    arr_lines = ["**📈 线2：ARR（OpenAI/Anthropic）**"]
    for n in arr_news[:5]:
        title_en = n["title"]
        title_zh = n.get("title_zh", "")
        if title_zh and title_zh != title_en and len(title_zh) > 5:
            display_title = title_zh
        else:
            display_title = title_en
        arr_lines.append(f"- {display_title}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(arr_lines)}
    })

    # --- 线3 板块ETF ---
    elements.append({"tag": "hr"})
    etf_lines = ["**🔄 线3：美股板块ETF**"]
    etf_table = ["| 板块 | 涨跌 |", "|---|---|"]
    for name in ["QQQ", "SPY", "XLK", "XLY", "XLF", "XLE"]:
        d = alt_data.get(name, {})
        pct = d.get("pct", 0)
        icon = "🔴" if pct <= -1 else ("🟢" if pct >= 0 else "🟡")
        etf_table.append(f"| {name}({d.get('label', '')}) | {icon} {pct:+.2f}% |")
    etf_lines.append("\n".join(etf_table))
    etf_lines.append(rotation_signal)
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(etf_lines)}
    })

    # --- 告警 ---
    elements.append({"tag": "hr"})
    alert_lines = ["**⚡ 今日告警**"]
    for a in alerts:
        alert_lines.append(f"- {a['level']} {a['msg']}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(alert_lines)}
    })

    # --- 投资建议 ---
    elements.append({"tag": "hr"})
    advice_lines = ["**💡 投资建议**"]
    advice_lines.append(f"线1: {line1_advice}")
    advice_lines.append(f"线2: {line2_advice}")
    advice_lines.append(f"线3: {rotation_signal}")
    # 关键操作
    for pa in position_advice:
        if "清仓" in pa["stop_loss"] or "止损" in pa["stop_loss"]:
            advice_lines.append(f"⚠️ {pa['ticker']}: {pa['stop_loss']}")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": "\n".join(advice_lines)}
    })

    # --- 页脚 ---
    elements.append({"tag": "hr"})
    footer = f"📅 距Q2财报季还有 {days_to_earnings} 天 | v4 | 新浪+Yahoo RSS聚合"
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": footer}]
    })

    # 卡片颜色
    has_red = any(a["level"] == "🚨" for a in alerts)
    has_yellow = any(a["level"] == "⚠️" for a in alerts)
    header_color = "red" if has_red else ("yellow" if has_yellow else "blue")
    header_title = f"🔴 三条卖出线 | {today_str}" if has_red else (f"🟡 三条卖出线 | {today_str}" if has_yellow else f"三条卖出线 | {today_str}")

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": header_title},
            "template": header_color,
        },
        "elements": elements,
    }


# 飞书推送
if LARK_AVAILABLE:
    print("\n【飞书推送】发送 interactive 卡片...")
    try:
        secrets = load_secrets()
        card = build_lark_card()
        card_str = json.dumps(card, ensure_ascii=False)
        print(f"  卡片 JSON 长度: {len(card_str)} 字符")
        message_id = send_interactive_card(
            secrets["chat_id"], card,
            app_id=secrets["app_id"], app_secret=secrets["app_secret"]
        )
        print(f"  ✅ 飞书推送成功！message_id: {message_id}")
        # 推送成功后删除本地日报，不留缓存
        try:
            out_file.unlink()
            print(f"  🗑️ 本地日报已删除: {out_file.name}")
        except Exception as e:
            print(f"  ⚠️ 删除本地日报失败: {e}")
    except Exception as e:
        print(f"  ❌ 飞书推送失败: {e}")
else:
    print("\n【飞书推送】跳过（push_lark.py 不可用）")
