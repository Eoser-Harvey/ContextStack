"""
AI分析模块 — 基于个人画像对推文生成投资/生活/家庭建议
"""
from typing import Optional, List, Dict


class ProfileAnalyzer:
    """个人画像分析器，生成针对性建议"""

    def __init__(self, profile):
        self.profile = profile

    # 有意义的推文关键词（匹配到才生成完整建议）
    MEANINGFUL_KEYWORDS = {
        "elonmusk": [
            "cursor", "burry", "ai", "compute", "grok", "spacex", "tesla",
            "robot", "agi", "singularity", "bitcoin", "crypto", "doge",
            "spcx", "stock", "share", "price", "model y", "tsla", "fsd",
            "starship", "mars", "orbit", "latency", "engineering",
            "10%", "odds", "important", "lesson", "build", "construct",
            "coding", "ai-native", "remote", "hospital", "save lives",
            "iran", "peace", "resource", "military", "multiplanetary",
            "censor", "审查", "protect the children", "prison", "politician",
            "250,000", "girls", "raped", "abused", "white girls",
            "$60b", "60b", "acquire", "cursor", "wealth", "inexplicable",
        ],
        "cz_binance": [
            "zoom out", "best performing", "short-term", "15 years",
            "might be late", "can't predict", "😂", "late",
            "iran", "macro", "tailwind", "oil", "fed", "rate cut",
            "$61k", "$67k", "trend", "narrative", "fundamental",
            "super cycle", "supercycle", "don't panic", "panic",
            "not return", "not dead", "not die",
            "btc", "bitcoin", "crypto", "regulat", "compliance",
            "build", "developer", "builder", "don't quit", "24 years",
        ],
        "realDonaldTrump": [
            "phase 2", "easier", "phase 1", "mou online",
            "never have a nuclear", "nuclear weapon",
            "fully open", "flowing", "greatest peace deal",
            "fake news", "paying", "iran will be paying",
            "gas", "0.47", "$0", "signing", "geneva", "ceremony",
            "g7", "summit", "france", "golden age", "respect",
            "iran", "peace deal", "hormuz",
            "tariff", "trade", "manufacturing",
            "crypto", "bitcoin", "fed", "rate", "stock",
            "now we build",
        ],
        "aleaborteddit": [
            "stock", "share", "market", "trade", "invest",
            "crcl", "nok", "mrvl", "dram", "spcx",
            "buy", "sell", "position", "portfolio", "earnings",
            "analysis", "technical", "fundamental", "valuation",
            "ai", "chip", "semi", "semiconductor", "etf",
        ],
        "qinbafrank": [
            "ai", "人工智能", "tech", "科技", "trend", "趋势",
            "macro", "宏观", "capital", "资本", "流动性", "liquidity",
            "cycle", "周期", "morgan stanley", "大摩", "report", "报告",
            "stock", "美股", "invest", "投资", "valuation",
            "crypto", "加密", "bitcoin", "btc", "ethereum",
            "semiconductor", "半导体", "chip", "芯片", "gpu",
            "fed", "美联储", "rate", "利率", "inflation", "通胀",
            "trade", "交易", "position", "仓位", "portfolio",
        ],
        "xiaomustock": [
            "stock", "股票", "market", "市场", "trade", "交易",
            "xiaomi", "小米", "mi", "lei jun", "雷军", "ev", "su7",
            "invest", "投资", "valuation", "估值", "earnings", "财报",
            "china", "中国", "a-share", "a股", "h-share", "港股",
            "tech", "科技", "semiconductor", "半导体", "chip",
            "ai", "人工智能", "smartphone", "手机", "iot",
        ],
        "xingpt": [
            "ai", "人工智能", "gpt", "llm", "大模型", "prompt",
            "agi", "machine learning", "deep learning", "neural",
            "tech", "科技", "startup", "创业", "innovation",
            "openai", "anthropic", "google", "meta",
            "coding", "编程", "software", "软件", "developer",
            "product", "产品", "growth", "增长", "trend",
        ],
        "hibtc37": [
            "btc", "bitcoin", "比特币", "crypto", "加密", "区块链",
            "eth", "ethereum", "以太坊", "defi", "web3",
            "mining", "挖矿", "hash", "哈希", "halving",
            "price", "价格", "market", "行情", "trade",
            "altcoin", "山寨", "wallet", "钱包", "exchange",
            "macro", "宏观", "fed", "美联储", "rate", "利率",
        ],
    }

    def analyze(self, tweets):
        """对所有推文生成分析建议"""
        for tweet in tweets:
            tweet["analysis"] = self._analyze_single(tweet)
        return tweets

    def _is_meaningful(self, username, text):
        """快速判断推文是否与用户的投资/科技/职业关注领域相关"""
        keywords = self.MEANINGFUL_KEYWORDS.get(username, [])
        return any(kw in text for kw in keywords)

    def _analyze_single(self, tweet):
        """分析单条推文并生成建议
        仅当推文内容匹配有意义关键词时，才生成完整建议(投资/职业/生活/家庭)。
        不匹配的推文只做简单摘要，避免信息过载。
        """
        username = tweet.get("username", "")
        content = tweet.get("content", "")
        translated = tweet.get("translated", "")
        text = (content + " " + translated).lower()

        if not self._is_meaningful(username, text):
            # 不匹配任何有意义关键词 → 只做摘要，不生成建议
            return {
                "summary": "该推文与你的投资/科技/职业关注领域关联度较低，仅供参考。"
            }

        # 匹配到有意义关键词 → 生成完整建议
        analysis = {
            "investment": self._investment_advice(username, content, translated),
            "career": self._career_advice(username, content, translated),
            "life": self._life_advice(username, content, translated),
            "family": self._family_advice(username, content, translated),
        }
        return analysis

    def _investment_advice(self, username, content, translated):
        """生成投资建议"""
        text = (content + " " + translated).lower()

        profile = self.profile
        assets = profile["assets"]
        liabilities = profile["liabilities"]

        # CZ相关 — 加密货币
        if username == "cz_binance":
            if any(kw in text for kw in ["zoom out", "best performing asset", "best performing", "short-term volatility", "15 years of green", "30 days of red", "long-term outperformance"]):
                return (
                    f"📈 **CZ的长期主义 — 比特币15年vs30天**\n"
                    f"CZ说'比特币是过去十年表现最好的资产，短期波动是长期超额收益的代价'。\n"
                    f"你的BTC持仓: {assets['crypto']['btc']}，" 
                    f"当前BTC约$66.5K。\n"
                    f"📌 核心逻辑:\n"
                    f"• CZ说的对：30天的红色不应让你忘记15年的绿色\n"
                    f"• ✅ 币安借贷已还清，但信用卡¥{liabilities['credit_card_invest']}仍需关注\n"
                    f"• MA120策略模式：BTC在MA120下方，定投暂存USDT待命\n"
                    f"📌 行动: 牛市回本后优先降杠杆，用自有资金做长期投资，" 
                    f"这样你才能真正做到CZ说的'zoom out'而不焦虑"
                )
            if any(kw in text for kw in ["might be late", "can't predict", "无法预测", "😂", "late"]):
                return (
                    f"😄 **CZ的幽默自嘲 — 超级周期预测的坦诚**\n"
                    f"CZ发推'可能会迟到…我无法预测任何事情 😂'——"
                    f"这是对他四个月前(2026年1月)预测超级周期的幽默回应。\n"
                    f"你的持仓: BTC {assets['crypto']['btc']}+ETH {assets['crypto']['eth']}，" 
                    f"币安USDT ${assets['crypto']['usdt']}。\n"
                    f"📌 核心教训: CZ自己都承认无法预测市场——"
                    f"你用信用卡¥{liabilities['credit_card_invest']}做投资，" 
                    f"预测性交易的风险很高。\n"
                    f"📌 行动: 不要试图'预测'超级周期何时来，" 
                    f"而是在确认趋势后（如BTC站稳$70K+）再逐步增加敞口。\n"
                    f"市场不会因为你预测对而奖励你，但会因为你在错误时机加杠杆而惩罚你。"
                )
            if any(kw in text for kw in ["iran", "伊朗", "macro", "宏观", "tailwind", "oil", "fed", "rate cut"]):
                return (
                    f"💰 **宏观利好链条已启动**\n"
                    f"CZ分析伊朗和平协议→油价下降→通胀缓解→美联储降息→BTC上涨。\n"
                    f"你的加密持仓: BTC ~{assets['crypto']['btc']}、ETH ~{assets['crypto']['eth']}，"
                    f"币安USDT ${assets['crypto']['usdt']}。\n"
                    f"📈 BTC从一周前$61K涨至$66.5K，宏观拐点信号明确。\n"
                    f"⚠️ 负债提醒: 信用卡¥{liabilities['credit_card_invest']}，" 
                    f"✅ 币安借贷已还清。如果确认降息周期启动，" 
                    f"BTC可能向$80K-$100K迈进，你的0.642 BTC将显著升值。\n"
                    f"📌 行动建议: USDT ${assets['crypto']['usdt']}可在BTC回调时分批建仓，" 
                    f"当前MA120模式：BTC在MA120下方暂存USDT，站回后买入。"
                )
            if any(kw in text for kw in ["$61k", "$67k", "zoom out", "trend", "narrative", "headline", "fundamental"]):
                return (
                    f"📊 **趋势vs噪音 — CZ的交易哲学**\n"
                    f"CZ说'趋势是朋友，叙事是敌人'——BTC从$61K→$66.5K仅用一周，"
                    f"当时恐慌抛售的人正在后悔。\n"
                    f"你的持仓: BTC {assets['crypto']['btc']}，" 
                    f"如果BTC回到$80K+，收益可观。\n"
                    f"📌 关键教训: 你的资产配置本质是'长期看多加密+科技'，" 
                    f"不要因短期波动频繁操作。CZ说的对——看基本面而非看标题。\n"
                    f"⚠️ 但也要注意: 你用了信用卡¥{liabilities['credit_card_invest']}，" 
                    f"杠杆不适合'不看盘'策略。牛市回本后优先降杠杆。"
                )
            if any(kw in text for kw in ["super cycle", "超级周期", "supercycle"]):
                return (
                    f"💰 **比特币超级周期信号**\n"
                    f"CZ承认超级周期可能延迟但仍坚持——这是个重要信号。\n"
                    f"你当前持仓: BTC ~{assets['crypto']['btc']}、ETH ~{assets['crypto']['eth']}，"
                    f"币安USDT ${assets['crypto']['usdt']}。\n"
                    f"⚠️ 风险提醒: 信用卡投资负债¥{liabilities['credit_card_invest']}，" 
                    f"✅ 币安借贷已还清。BTC若反弹至$100K+将显著改善你的资产负债表，" 
                    f"但信用卡杠杆仍需警惕。建议：当前MA120模式，BTC站回MA120后恢复定投买入。"
                )
            if any(kw in text for kw in ["don't panic", "不要恐慌", "panic", "not dead", "不会死", "not die"]):
                return (
                    f"🧘 **市场恐慌应对**\n"
                    f"CZ喊话'不要恐慌'——BTC近期从高点回落。\n"
                    f"你的加密资产: BTC {assets['crypto']['btc']} + ETH {assets['crypto']['eth']} + USDT ${assets['crypto']['usdt']}。\n"
                    f"当前策略: 币安有${assets['crypto']['usdt']}闲置资金，" 
                    f"可在市场恐慌时分批抄底BTC/ETH。\n"
                    f"✅ 币安借贷已还清，无强制平仓风险。MA120模式：BTC站回MA120后恢复买入。"
                )
            if any(kw in text for kw in ["not return", "不返回", "不重返", "passive shareholder"]):
                return (
                    f"📊 **币安管理层信号**\n"
                    f"CZ确认不重返币安CEO——这降低了监管不确定性，对BNB和币安生态是利好。\n"
                    f"你的加密资产大部分在币安(USDT ${assets['crypto']['usdt']})，"
                    f"币安稳定性直接影响你的资产安全。CZ作为被动股东+行业精神领袖继续发声是正面信号。"
                )
            if any(kw in text for kw in ["btc", "bitcoin", "比特币", "crypto", "加密"]):
                return (
                    f"💰 **加密货币信号**\n"
                    f"你当前持仓: BTC ~{assets['crypto']['btc']}、ETH ~{assets['crypto']['eth']}，"
                    f"币安USDT余额 ${assets['crypto']['usdt']}。\n"
                    f"⚠️ 注意: 信用卡投资负债¥{liabilities['credit_card_invest']}，" 
                    f"✅ 币安借贷已还清。CZ的言论需结合你的风险敞口审慎判断，" 
                    f"不建议因推文情绪加仓。"
                )
            if any(kw in text for kw in ["regulat", "监管", "compliance", "合规"]):
                return (
                    f"⚖️ **监管风险提示**\n"
                    f"你在币安有敞口(USDT ${assets['crypto']['usdt']})，" 
                    f"CZ对监管的评论需特别关注。"
                    f"✅ 借贷已还清，建议保持USDT适当流动性应对监管变化。"
                )
            return ""

        # 马斯克相关
        if username == "elonmusk":
            if any(kw in text for kw in ["cursor", "$60b", "60b", "acquire cursor", "ai-native", "coding", "knowledge work"]):
                return (
                    f"💻 **SpaceX 600亿美元收购Cursor — AI编程革命**\n"
                    f"SpaceX宣布以$600亿收购AI编程平台Cursor，打造AI原生软件开发。\n"
                    f"📌 投资启示:\n"
                    f"• SPCX(当前$173.42)用股票收购Cursor→稀释现有股东但换取AI编程赛道龙头\n"
                    f"• Cursor年收入约$2-3B，$60B估值=20-30x P/S，在AI赛道属合理偏高\n"
                    f"• 你的持仓(CRCL 626股+MRVL+NOK)不受直接影响，但利好AI编程生态链\n"
                    f"📌 职业启示: AI编程工具(Cursor/Copilot)正在改变软件开发——"
                    f"你的Python+嵌入式技能不会被替代，但需要学会用AI工具提效。\n"
                    f"学习Cursor/GitHub Copilot，让你的编码效率提升50%+。"
                )
            if any(kw in text for kw in ["burry", "short", "做空", "trillion", "doesn't worth", "bankrupt"]):
                return (
                    f"🎯 **大空头Burry炮轰SPCX — 马斯克霸气回怼**\n"
                    f"Michael Burry称SPCX不值$1万亿，马斯克回怼'他2018年也说特斯拉会破产'。\n"
                    f"📌 投资启示:\n"
                    f"• Burry做空次贷成名，但做空特斯拉失败了——历史可能重演\n"
                    f"• SPCX 3天涨29%→短期过热，但长期叙事(太空+AI)有支撑\n"
                    f"• 你的策略: SPCX不建议追高，等回调至$150以下再考虑\n"
                    f"📌 核心教训: 做空者质疑估值、做多者相信未来——"
                    f"你不需要站队，只需要管理好仓位。\n"
                    f"不要因为Burry说贵就恐慌，也不要因为马斯克说好就FOMO。"
                )
            if any(kw in text for kw in ["model y", "medical emergency", "chest pain", "remotely unlocked", "save lives", "remote", "hospital", "tesla app"]):
                return (
                    f"🚗 **Tesla远程救援 — 技术拯救生命**\n"
                    f"马斯克转发Model Y驾驶员胸痛发作时，其子远程解锁并将车导航至医院的真实故事。\n"
                    f"📌 投资启示:\n"
                    f"• TSLA(你已清仓): 这类真实故事比财报更能证明技术价值→长期品牌溢价\n"
                    f"• 远程控车+AI导航→端侧AI在汽车安全领域有巨大空间→你TFLM学习方向正确\n"
                    f"• 但短期TSLA股价更多受FSD进展和交付数据驱动，单一救援故事不构成交易信号\n"
                    f"📌 职业启示: 远程控车需要嵌入式实时系统+低延迟通信——"
                    f"正是你的TSN+嵌入式技能组合的应用场景"
                )
            if any(kw in text for kw in ["250,000", "girls", "raped", "abused", "rape", "lured", "white girls"]):
                return (
                    f"🔍 **马斯克聚焦英国强奸团伙丑闻**\n"
                    f"马斯克转发称'至少25万英国白人女孩被诱骗强奸虐待'——"
                    f"这是他对英国社会问题的持续施压，与反审查立场一脉相承。\n"
                    f"📌 投资启示:\n"
                    f"• 马斯克以此论证'审查掩盖真相'，强化其反体制叙事→对加密去中心化叙事有间接支撑\n"
                    f"• 但此类社会议题推文不直接涉及市场/科技→对持仓影响有限\n"
                    f"• 你持仓(BTC {assets['crypto']['btc']}+CRCL+MRVL+NOK)不受此话题直接驱动\n"
                    f"⚠️ 注意: 马斯克高强度输出中情绪化内容增多，" 
                    f"建议关注其中科技/AI/加密相关推文，社会议题类可降低权重"
                )
            if any(kw in text for kw in ["censor", "审查", "protect the children", "保护儿童", "imprison", "prison", "入狱", "politician", "政客"]):
                return (
                    f"🔍 **马斯克抨击审查制度**\n"
                    f"马斯克连发4条推文抨击审查制度和政客腐败，核心观点：\n"
                    f"• '政客关押人民是为了掩盖自己的罪行'\n"
                    f"• '审查总是以保护儿童为幌子'\n"
                    f"📌 投资启示：马斯克近期大量发声揭露体制问题，可能影响政治风向→监管环境。\n"
                    f"• 你的加密持仓(BTC {assets['crypto']['btc']}+ETH {assets['crypto']['eth']})，" 
                    f"对监管风向敏感，马斯克的反审查立场可能间接利好去中心化叙事\n"
                    f"• 但他4小时内连发33条推文的高强度输出，也可能引发短期市场波动\n"
                    f"⚠️ 注意：这是价值观层面的推文，对投资直接影响有限，不建议据此交易"
                )
            if any(kw in text for kw in ["spcx", "173", "stock", "share", "close", "bankrupt"]):
                return (
                    f"🚀 **SPCX $173.42 — 5天涨+29%**\n"
                    f"SpaceX上市后持续走高，从IPO价$135涨至$173.42。马斯克强调'真正价值在构建而非股价'。\n"
                    f"你的持仓影响:\n"
                    f"• 你关注端侧AI/机器人赛道，SPCX的'太空+AI'叙事与你技能方向高度契合\n"
                    f"📌 投资: SPCX已涨29%，不建议追高。关注回调至$150以下再考虑建仓。\n"
                    f"📌 职业: SpaceX的轨道算力(LEO 25ms延迟)与你端侧AI技能形成'天上+地下'互补——"
                    f"云端轨道算力做复杂推理，端侧设备做实时推理。你的技能不会过时。"
                )
            if any(kw in text for kw in ["iran", "peace", "伊朗", "和平", "military", "军事", "resource", "资源", "multiplanetary"]):
                return (
                    f"🕊️ **和平红利与太空投资**\n"
                    f"马斯克说'和平意味着更多资源用于太空探索和AI'——"
                    f"如果全球军事预算的10%转向太空，那将是每年$200B+的增量市场。\n"
                    f"你的投资组合(TSLA/机器人ETF/CRCL)都受益于全球和平+科技投资增加的大趋势。\n"
                    f"📌 地缘风险降温→全球风险偏好回升→利好你的多资产配置(加密+美股+A股+港股)。\n"
                    f"📌 长期视角: 你在端侧AI的学习方向，正是'和平时代的科技红利'赛道。"
                )
            if any(kw in text for kw in ["spacexai", "grok", "orbital compute", "轨道算力", "latency"]):
                return (
                    f"🛰️ **SpaceXAI轨道算力 — 颠覆性AI基础设施**\n"
                    f"马斯克宣布SpaceXAI将用LEO轨道集群运行Grok，延迟从150ms降至25ms。\n"
                    f"这对你的职业方向(端侧AI/TFLM)意义重大:\n"
                    f"• 轨道算力解决的是'云端AI'延迟问题，而端侧AI解决的是'设备端'延迟问题\n"
                    f"• 两者互补而非竞争：轨道算力做复杂推理，端侧做实时推理\n"
                    f"• 你在{profile['career']['company']}的嵌入式+TSN背景，正是'端侧+低延迟网络'的交叉点\n"
                    f"📌 投资角度：SPCX(已上市$161→关注回调)、算力产业链(NVDA/AVGO)受益于太空算力竞赛\n"
                    f"⚠️ 注意：马斯克的'2028轨道算力'时间线激进，短期SPCX可能因预期过高而波动"
                )
            if any(kw in text for kw in ["agi", "singularity", "2026", "奇点", "engineering math"]):
                return (
                    f"🤖 **AGI 2026 — 对你职业的深远影响**\n"
                    f"马斯克再次确认2026年实现AGI(通用人工智能)，强调这不是预测而是'工程计算'。\n"
                    f"你的端侧AI(TFLM)学习方向恰恰是AGI落地的关键一环：\n"
                    f"• AGI需要无处不在的推理能力→端侧推理芯片需求爆发\n"
                    f"• 你已有的嵌入式+TSN+驱动开发能力→AI边缘设备开发天然契合\n"
                    f"• 新华三(网络设备商)在AI推理服务器+边缘计算网关方向有布局机会\n"
                    f"📌 投资: 机器人ETF(已持4000股)+端侧AI芯片(ESP32-S3/NPU生态)值得持续关注\n"
                    f"📌 职业: 从现在到AGI落地，你有1-2年窗口完成从'传统嵌入式'到'AI嵌入式'的转型"
                )
            if any(kw in text for kw in ["starship", "mars", "星舰", "火星", "multiplanetary", "launch window"]):
                return (
                    f"🚀 **星舰火星计划 — 2026年底发射窗口**\n"
                    f"马斯克明确2026年底火星发射窗口，星舰是关键。\n"
                    f"SpaceX IPO(SPCX $161)后马斯克聚焦火星殖民，这对你持有TSLA(2.45股)有间接利好：\n"
                    f"• 马斯克精力分配：IPO后SpaceX资金充裕，可更专注星舰→TSLA管理压力减小\n"
                    f"• 航天产业链：SPCX的长期叙事是火星经济，短期关注每个发射窗口的股价催化\n"
                    f"📌 你投资组合中的TSLA+机器人ETF+加密→都属于'高风险高回报'配置，" 
                    f"与马斯克的'即使只有10%成功率也要试'理念一致，但需控制单赛道集中度"
                )
            if any(kw in text for kw in ["10%", "odds", "lesson", "成功机会", "important enough"]):
                return (
                    f"💡 **创业精神与投资心态**\n"
                    f"马斯克说SpaceX当初只有不到10%成功率，如今成为史上最大IPO($1.78万亿)。\n"
                    f"你的投资组合(加密+美股+A股)也属于'高风险高回报'策略，核心原则相通：\n"
                    f"• 关键不是你对了多少次，而是你对的时候赚了多少\n"
                    f"• 你BTC持仓~0.52、ETH~1.35，在加密领域已是'早期入场者'\n"
                    f"• CZ说'builders keep building'——你在端侧AI的持续学习也是一种'长期主义投资'\n"
                    f"📌 反思：你的杠杆(信用卡¥40W+币安借贷$13.4K)是否与'10%成功率'的哲学一致？"
                    f"建议在牛市回本后优先降杠杆，用利润而非负债做高风险投资"
                )
            if any(kw in text for kw in ["spacex", "ipo", "trillionaire", "万亿"]):
                return (
                    f"🚀 **SpaceX IPO历史性事件**\n"
                    f"SpaceX于6月12日纳斯达克上市(代码SPCX)，首日收盘$160.95(+19.2%)，马斯克成为全球首个万亿富翁。\n"
                    f"你持有TSLA 2.45股(燕蒙古WEB3)，马斯克商业帝国估值暴涨对TSLA有正向溢出效应。\n"
                    f"⚠️ 注意：马斯克5月28日推文披露Anthropic租约仅为180天短期，曾引发2万亿估值恐慌——"
                    f"这说明他的推文能剧烈影响股价。如考虑买入SPCX，建议等待回调。\n"
                    f"📌 长线视角：轨道数据中心+AI算力服务是SpaceX第二增长曲线，值得关注。"
                )
            if any(kw in text for kw in ["compute", "算力", "colossus", "anthropic", "lease", "租约"]):
                return (
                    f"💻 **AI算力即服务信号**\n"
                    f"马斯克明确SpaceX的AI算力租赁是180天短期合约（非多年长期），\n"
                    f"这说明AI算力市场仍在早期探索阶段，商业模式未定型。\n"
                    f"你的端侧AI方向(TFLM)恰恰是'去中心化算力'的趋势——端侧推理不需要云端算力，\n"
                    f"这与SpaceX'轨道数据中心'形成互补。投资角度：算力相关标的短期波动大，\n"
                    f"但你的技能方向长期受益于AI产业爆发。"
                )
            if any(kw in text for kw in ["ai", "人工智能", "grok", "xai", "robot", "机器人"]):
                return ""
            if any(kw in text for kw in ["tesla", "特斯拉", "tsla", "ev", "fsd"]):
                return ""
            if any(kw in text for kw in ["doge", "狗狗币", "crypto", "加密"]):
                return ""
            return ""

        # 特朗普相关
        if username == "realDonaldTrump":
            if any(kw in text for kw in ["phase 2", "第二阶段", "easier", "phase 1", "mou online", "easier than"]):
                return (
                    f"🏛️ **美伊协议进入第二阶段 — 确定性进一步增强**\n"
                    f"特朗普宣布美伊协议进入第二阶段，称'比第一阶段更容易'，6/19日内瓦正式签署。\n"
                    f"📌 核心信号:\n"
                    f"• 从'停战'到'和平建设'的转折→地缘风险进一步系统性下降\n"
                    f"• 霍尔木兹海峡19日前全面重开→全球石油运输恢复正常\n"
                    f"• 第二阶段涉及核计划技术讨论+财政援助+海峡开放细节\n"
                    f"📌 对你的投资影响:\n"
                    f"• 加密(BTC {assets['crypto']['btc']}+ETH {assets['crypto']['eth']}): 宏观利好确认，BTC $67K站稳\n"
                    f"• CRCL 626股: 地缘稳定→风险偏好回升→利好科技成长股\n"
                    f"• 币安USDT ${assets['crypto']['usdt']}: 可在6/19签署仪式前后逐步部署\n"
                    f"⚠️ 关注: 第二阶段谈判细节可能引发短期波动，" 
                    f"但中长期方向(降息+和平)对多资产组合有利。"
                )
            if any(kw in text for kw in ["never have a nuclear", "never", "nuclear weapon", "核武器", "fully open", "flowing", "greatest peace deal", "now we build"]):
                return (
                    f"☢️ **伊朗永久无核化 — 历史性地缘转折**\n"
                    f"特朗普宣布伊朗同意'永不拥有核武器'，霍尔木兹海峡全面通航。\n"
                    f"这是中东和平的结构性突破，对全球市场的意义远超短期油价波动:\n"
                    f"• 中东战争风险系统性下降→全球风险溢价降低→利好所有风险资产\n"
                    f"• 你的加密(BTC {assets['crypto']['btc']}+ETH {assets['crypto']['eth']})+" 
                    f"TSLA+机器人ETF+CRCL→全组合受益\n"
                    f"• 能源价格长期稳定→通胀预期下调→美联储降息空间增大\n"
                    f"📌 行动: 这是今年最大的宏观利好之一。" 
                    f"关注6/19日内瓦签署仪式后的市场反应，" 
                    f"币安USDT ${assets['crypto']['usdt']}可在确认降息趋势后逐步部署。" 
                    f"但注意'买预期卖事实'——签署后可能有短期获利了结。"
                )
            if any(kw in text for kw in ["fake news", "假新闻", "paying", "支付", "iran will be paying", "not us"]):
                return (
                    f"🏛️ **特朗普否认美国向伊朗支付 — 协议细节澄清**\n"
                    f"特朗普在G7峰会期间发帖否认'美国向伊朗支付巨额资金'的报道，" 
                    f"称'伊朗将付钱——不是我们'。\n"
                    f"背后信息：副总统Vance透露可能涉及海湾联盟资助的$3000亿投资基金，" 
                    f"前提是伊朗履行义务。\n"
                    f"📌 对你的投资影响:\n"
                    f"• 协议资金来源澄清→减少市场对'美国纳税人买单'的担忧→利好风险资产\n"
                    f"• 你的加密(BTC {assets['crypto']['btc']}+ETH {assets['crypto']['eth']})+" 
                    f"TSLA+机器人ETF，全部受益于地缘风险下降\n"
                    f"• 6/19日内瓦签署仪式仍是关键催化剂\n"
                    f"⚠️ 但'Fake News'言论本身就是市场波动源——关注协议具体条款的最终版本"
                )
            if any(kw in text for kw in ["gas", "油价", "0.47", "$0", "signing", "geneva", "日内瓦", "ceremony"]):
                return (
                    f"⛽ **油价下降$0.47 — 直接利好你的钱包**\n"
                    f"特朗普宣布伊朗协议公布后油价已降$0.47，6/19日内瓦签署仪式后可能进一步下行。\n"
                    f"对你的直接影响:\n"
                    f"• 生活成本: 油价降→交通/物流成本降→CPI降→生活压力减小\n"
                    f"• 房贷: 通胀缓解→美联储降息预期增强→你的商贷¥{liabilities['mortgage_commercial']}+公积金¥{liabilities['mortgage_fund']}月供有望下降\n"
                    f"• 投资: 降息利好风险资产→BTC/ETH/TSLA/机器人ETF全部受益\n"
                    f"📌 重点关注6/19日内瓦签署仪式——这是确定性催化剂，签署后市场可能迎来新一轮risk-on。\n"
                    f"📌 你币安USDT ${assets['crypto']['usdt']}可在签署仪式前布局，但注意'买预期卖事实'风险。"
                )
            if any(kw in text for kw in ["g7", "summit", "france", "法国", "golden age", "黄金时代", "respect"]):
                return (
                    f"🌍 **G7峰会圆满 — 美国外交格局重塑**\n"
                    f"特朗普宣布G7法国峰会成功，强调'世界再次尊重美国'。\n"
                    f"这背后意味着:\n"
                    f"• 美国主导的中东和平框架(伊朗协议)→地缘风险系统性下降\n"
                    f"• 关税政策可能在多边框架下调整→利好你的港股CRCL和中概股持仓\n"
                    f"• 新华三(你的雇主)作为国产网络设备商→国际环境缓和有利于出海业务\n"
                    f"📌 多资产策略: 地缘稳定+降息预期=风险资产黄金窗口，但也要警惕'利好出尽'。"
                )
            if any(kw in text for kw in ["iran", "伊朗", "peace deal", "和平协议", "hormuz"]):
                return (
                    f"🕊️ **伊朗和平协议 — 重大地缘利好**\n"
                    f"特朗普宣布伊朗和平协议完成，霍尔木兹海峡通航恢复。\n"
                    f"这对全球能源价格是重大利好：油价下行→通胀缓解→美联储可能降息→利好风险资产。\n"
                    f"你的持仓影响分析:\n"
                    f"• 加密: 降息预期利好BTC/ETH，你持仓{assets['crypto']['btc']}+{assets['crypto']['eth']}直接受益\n"
                    f"• 美股: TSLA和CRCL受益于利率下行预期\n"
                    f"• A股: 机器人ETF/小米受益于风险偏好回升\n"
                    f"• 港股: CRCL受益于地缘风险降温\n"
                    f"📌 行动建议: 关注6月24日美国独立250周年庆典前后政策窗口，"
                    f"币安USDT ${assets['crypto']['usdt']}可在确认降息趋势后逐步部署。"
                )
            if any(kw in text for kw in ["tariff", "关税", "trade", "贸易", "manufacturing"]):
                return ""
            if any(kw in text for kw in ["crypto", "bitcoin", "加密", "比特币"]):
                return ""
            if any(kw in text for kw in ["fed", "美联储", "rate", "利率", "stock", "股市"]):
                return ""
            return ""

        return ""

    def _career_advice(self, username, content, translated):
        """生成职业发展建议"""
        text = (content + " " + translated).lower()
        career = self.profile["career"]

        if username == "elonmusk":
            if any(kw in text for kw in ["cursor", "$60b", "60b", "acquire", "coding", "ai-native"]):
                return (
                    f"💼 **AI编程时代 — 嵌入式工程师的新工具**\n"
                    f"SpaceX $600亿收购Cursor标志着AI编程进入主流。\n"
                    f"你在{career['company']}做{career['role']}，{career['experience']}，" 
                    f"技能栈({', '.join(career['skills'])})不会被AI替代，" 
                    f"但会用AI工具的工程师会替代不会的。\n"
                    f"📌 行动: 学会用Cursor/Copilot辅助嵌入式开发，" 
                    f"把重复性编码交给AI，聚焦架构设计和系统优化——这才是PL的核心价值。"
                )
            if any(kw in text for kw in ["burry", "short", "做空", "doesn't worth", "never learn"]):
                return (
                    f"💼 **做空者的教训与职业韧性**\n"
                    f"马斯克回怼Burry'做空者从不学习'——2018年Burry做空特斯拉失败，" 
                    f"2026年又来质疑SPCX。\n"
                    f"你在{career['company']}做{career['role']}已{career['experience']}，" 
                    f"职场中也会遇到质疑你转型端侧AI的人——'嵌入式转AI太难了''你年龄大了'。\n"
                    f"📌 马斯克的逻辑: 不要回应质疑，用结果说话。TFLM学习+项目实践，" 
                    f"让时间和成果成为最好的回应。"
                )
            if any(kw in text for kw in ["model y", "medical emergency", "remotely", "save lives", "remote", "hospital"]):
                return (
                    f"💼 **嵌入式工程师的终极价值 — 技术拯救生命**\n"
                    f"Model Y远程救援案例证明：嵌入式实时系统+远程控制=关键时刻能救命。\n"
                    f"你在{career['company']}做{career['role']}，技能栈(嵌入式+TSN+驱动)正是这种'安全关键系统'的核心技术。\n"
                    f"📌 职业定位: 不要把自己看作'写驱动的'——"
                    f"你是在构建'关键时刻能救命的系统'。端侧AI(TFLM)加持后，"
                    f"你的技能从'被动响应'升级为'主动智能'——这正是行业需要的。"
                )
            if any(kw in text for kw in ["250,000", "girls", "raped", "abused", "white girls"]):
                return (
                    f"💼 **关注焦点管理 — 信息输入的纪律**\n"
                    f"马斯克推文覆盖科技/AI/政治/社会多领域，近24h发34条——"
                    f"你需要有选择地关注：科技和AI推文对你的职业有直接价值，" 
                    f"社会议题推文可作为背景了解但不应占据主要注意力。\n"
                    f"你在{career['company']}做{career['role']}，时间有限，" 
                    f"建议：每天30分钟信息摄入(科技+加密+宏观)，其余时间聚焦TFLM学习和项目实践。"
                )
            if any(kw in text for kw in ["censor", "审查", "protect the children", "保护儿童", "imprison", "prison", "politician", "政客"]):
                return (
                    f"💼 **马斯克的反体制立场与职业启示**\n"
                    f"马斯克连发4条推文抨击政客和审查制度——" 
                    f"这反映了一种'用技术改变规则'而非'遵守现有规则'的思维模式。\n"
                    f"你在{career['company']}做{career['role']}，" 
                    f"薪资{career['salary']}在嵌入式领域已属中上，" 
                    f"但瓶颈也在于'规则内发展'——PL岗位的天花板清晰可见。\n"
                    f"📌 职业突破点: 端侧AI(TFLM)是你'打破规则'的路径——" 
                    f"从传统嵌入式到AI嵌入式的跃迁，本质是从'遵守规则'到'创造新规则'。\n"
                    f"马斯克的逻辑：真正的变革来自'构建'而非'遵守'。"
                )
            if any(kw in text for kw in ["spcx", "173", "stock price", "build", "construct"]):
                return (
                    f"💼 **SPCX vs 你的职业选择**\n"
                    f"马斯克说'真正价值在构建而非股价'——对你也适用。\n"
                    f"你在{career['company']}做{career['role']}，{career['experience']}，" 
                    f"薪资{career['salary']}在嵌入式领域已是中上水平。\n"
                    f"但马斯克的逻辑是: 薪资是'股价'，能力才是'构建'。\n"
                    f"📌 TFLM学习+端侧AI实践=你在'构建'未来的竞争力，" 
                    f"即使短期薪资涨幅有限，长期你的交叉技能(嵌入式+AI+TSN)是稀缺资源。"
                )
            if any(kw in text for kw in ["iran", "peace", "resource", "资源", "military", "multiplanetary"]):
                return (
                    f"💼 **和平时代的科技红利**\n"
                    f"马斯克说'把军事预算的10%转向太空和AI'——虽然这是他的愿景，"
                    f"但反映了趋势：全球资源正从'对抗'转向'建设'。\n"
                    f"你在{career['company']}的嵌入式+TSN+网络设备技能，"
                    f"在'建设时代'（工业AIoT/智能工厂/自动驾驶基础设施）的需求远大于'对抗时代'。\n"
                    f"📌 职业策略: 和平环境→经济繁荣→企业增加技术投入→你的技能升值。"
                    f"持续深耕端侧AI，这是确定性最高的职业方向。"
                )
            if any(kw in text for kw in ["ai", "人工智能", "engineering", "工程", "compute", "算力", "orbital", "轨道", "grok", "spacexai"]):
                return (
                    f"💼 **AI算力趋势与你职业方向的契合**\n"
                    f"马斯克在推文中强调SpaceXAI将用轨道算力集群运行AI——"
                    f"AI算力正在成为基础设施级服务。\n"
                    f"你在{career['company']}做{career['role']}，有{career['experience']}，"
                    f"端侧AI(TFLM)是'去中心化算力'的重要方向——在设备端做推理不需要云端GPU。\n"
                    f"📌 职业策略: 端侧AI+嵌入式+TSN协议的组合在工业AIoT场景有稀缺性，"
                    f"建议持续深耕，这是大厂和创业公司都需要的交叉技能。\n"
                    f"轨道算力解决云端延迟，你解决端侧延迟——两条路线互补，你的技能不会过时。"
                )
            if any(kw in text for kw in ["agi", "奇点", "singularity", "engineering math"]):
                return (
                    f"💼 **AGI时代嵌入式工程师的定位**\n"
                    f"马斯克说AGI 2026是'工程计算'而非预测——这意味着AI芯片和边缘推理需求即将爆发。\n"
                    f"你作为{career['role']}在{career['company']}，有{career['experience']}，" 
                    f"技能栈({', '.join(career['skills'])})在AGI时代的定位：\n"
                    f"• AGI需要边缘推理→嵌入式AI芯片(NPU/TPU)需求爆发→你的TFLM技能直接对口\n"
                    f"• 新华三作为网络设备商→AI推理服务器+边缘网关→内部转型机会\n"
                    f"📌 建议：在未来6个月内完成TFLM基础学习+1个端侧AI实战项目(如ESP32-S3语音识别)，"
                    f"这将是你从'传统嵌入式'到'AI嵌入式'转型的关键里程碑。"
                )
            if any(kw in text for kw in ["spacex", "mars", "月球", "火星", "science fiction", "科幻", "starship", "星舰", "10%", "odds"]):
                return (
                    f"💼 **长期视野与职业定位**\n"
                    f"马斯克说'把科幻变为现实'——你作为嵌入式工程师，"
                    f"所做的底层驱动/协议开发恰恰是让科幻落地的关键技术层。\n"
                    f"你在{career['company']}的{career['experience']}，"
                    f"端侧AI(TFLM)是你从'传统嵌入式'到'智能嵌入式'的跃迁路径。\n"
                    f"📌 建议: 在TFLM学习同时，关注边缘计算+AI推理芯片(如ESP32-S3/NPU)的实战，"
                    f"这是硬件工程师在AI时代最值钱的能力。"
                )
            if any(kw in text for kw in ["hire", "招聘", "team", "团队"]):
                return ""
            if any(kw in text for kw in ["ai", "人工智能", "engineering", "工程"]):
                return ""

        if username == "cz_binance":
            if any(kw in text for kw in ["zoom out", "best performing", "15 years", "short-term"]):
                return (
                    f"💼 **职业长期主义 — Zoom Out你的职业轨迹**\n"
                    f"CZ说'不要让30天的红色让你忘记15年的绿色'——" 
                    f"这也适用于你的职业规划。\n"
                    f"你在{career['company']}已{career['experience']}，" 
                    f"短期来看PL岗位天花板明显，薪资{career['salary']}涨幅有限。" 
                    f"但zoom out看：嵌入式+AI+TSN的组合是稀缺技能，" 
                    f"你正在从一个'写驱动的嵌入式工程师'变成一个'懂AI的嵌入式架构师'。\n"
                    f"📌 15年视角: 你现在的TFLM学习+端侧AI项目积累，" 
                    f"不是在为下一次跳槽准备，而是在为未来10年的职业竞争力投资。"
                )
            if any(kw in text for kw in ["might be late", "can't predict", "无法预测", "😂"]):
                return (
                    f"💼 **接受不确定性 — CZ的智慧**\n"
                    f"CZ自嘲'我无法预测任何事'——作为币安创始人，" 
                    f"他公开承认预测的局限性，这是一种领导力。\n"
                    f"你在{career['company']}做{career['role']}已{career['experience']}，" 
                    f"职业规划同样面临不确定性：端侧AI什么时候爆发？" 
                    f"新华三内部是否有AI转型机会？什么时候跳槽？\n"
                    f"📌 CZ的哲学: 不做精确预测，但坚持'build'——" 
                    f"你坚持TFLM学习+项目实践，即使不确定时机，方向是正确的。\n"
                    f"预测不重要，持续'构建'才重要。"
                )
            if any(kw in text for kw in ["build", "构建", "developer", "开发", "builder", "don't quit", "不放弃", "24 years"]):
                return (
                    f"💼 **长期主义投资哲学**\n"
                    f"CZ借SpaceX IPO谈投资真谛：最好的投资是投给'不放弃的建造者'。" 
                    f"马斯克用了24年——大多数人2年就放弃了。\n"
                    f"对你的启示：你在{career['company']}已{career['experience']}，端侧AI(TFLM)是新的'24年旅程'的起点。\n"
                    f"• 加密投资同理：BTC从$0到$66K走了15年，中间无数次'死亡'\n"
                    f"• 你的持仓(BTC~0.642+ETH~1.35)已是长期主义实践\n"
                    f"📌 行动：减少短线交易，将精力聚焦于'建造'——TFLM学习+职业转型+家庭"
                )

        if username == "realDonaldTrump":
            if any(kw in text for kw in ["manufacturing", "制造", "tariff", "关税", "america"]):
                return ""

        return ""

    def _life_advice(self, username, content, translated):
        """生成生活建议"""
        text = (content + " " + translated).lower()
        profile = self.profile

        suggestions = []

        # 马斯克 — 工作与生活平衡
        if username == "elonmusk":
            if any(kw in text for kw in ["cursor", "$60b", "acquire", "coding", "ai-native"]):
                suggestions.append(
                    f"💻 **AI工具解放生产力**: SpaceX $600亿收购Cursor——"
                    f"AI编程工具正在改变所有工程师的工作方式。"
                    f"你在学习TFLM的同时，也建议花1-2小时体验Cursor/Copilot，"
                    f"用AI辅助写嵌入式代码——把重复劳动交给AI，把创造力留给自己。"
                )
            if any(kw in text for kw in ["burry", "short", "做空", "never learn"]):
                suggestions.append(
                    f"🧠 **质疑声中保持定力**: 马斯克回怼Burry'做空者从不学习'——"
                    f"生活中总会遇到质疑你的人。你在学TFLM转型端侧AI，"
                    f"可能有人说'嵌入式转AI太难'——不要理会。"
                    f"马斯克24年坚持才把SpaceX从10%成功率做到$2.66万亿。你的TFLM学习才刚开始。"
                )
            if any(kw in text for kw in ["model y", "medical emergency", "save lives", "remotely"]):
                suggestions.append(
                    f"❤️ **技术的人文价值**: 马斯克分享的Model Y远程救援故事提醒我们——"
                    f"技术的终极价值是守护生命。你每天做的嵌入式开发、驱动调试，"
                    f"看似枯燥，但可能在某个时刻成为别人的'救命按钮'。"
                    f"这种意义感值得你每天带着热情去工作，而不仅仅是'拿工资'。"
                )
            if any(kw in text for kw in ["censor", "审查", "protect the children", "prison", "政客", "politician"]):
                suggestions.append(
                    f"🔍 **信息素养提醒**: 马斯克33条推文中4条关于审查和政客——"
                    f"高信息密度时代，你关注加密+股市+科技+政治多领域信息，" 
                    f"容易信息过载。建议设定'信息摄入窗口'（如每天30分钟），" 
                    f"剩余时间聚焦TFLM学习和家庭。马斯克推文是信号，但不要让它成为噪音。"
                )
            if any(kw in text for kw in ["iran", "peace", "humanity", "人类", "resource", "资源"]):
                suggestions.append(
                    f"☮️ **和平红利与个人心态**: 马斯克说和平对人类有益——"
                    f"地缘冲突缓解不仅是投资利好，也是心理利好。"
                    f"减少每天对'战争/崩盘/危机'的焦虑，" 
                    f"把精力更多投入TFLM学习和家庭陪伴。市场好的时候多做事，市场差的时候多学习。"
                )
            if any(kw in text for kw in ["work", "工作", "sleep", "睡眠", "hardcore"]):
                suggestions.append(
                    f"🕐 **工作强度提醒**: 马斯克以极限工作著称，"
                    f"但你在{profile['career']['company']}已有{profile['career']['experience']}，"
                    f"注意劳逸结合。投资+工作+学习的三角需要合理分配精力。"
                )
            if any(kw in text for kw in ["future", "未来", "excited", "兴奋", "wake up", "醒来", "10%", "odds", "成功机会"]):
                suggestions.append(
                    f"🌟 **保持好奇心**: 马斯克说'必须有让你对未来兴奋的东西，让你每天早上醒来充满期待'。"
                    f"你现在同时推进TFLM学习+加密投资+职业发展，"
                    f"虽然压力大但方向正确。记住你选择端侧AI的初心——这是你从'写驱动'到'做AI'的跃迁。"
                )
            if any(kw in text for kw in ["agi", "奇点", "singularity", "engineering math"]):
                suggestions.append(
                    f"🤖 **AGI时代的个人定位**: 马斯克说AGI 2026是工程计算。"
                    f"这对你意味着：不要把AGI看成威胁，而是机会。"
                    f"你的嵌入式+TSN+驱动开发经验，结合TFLM学习，正是'物理世界AI化'需要的技能组合。"
                    f"保持学习节奏，不要焦虑——AGI需要硬件落地，而你是做硬件的人。"
                )

        # CZ — 极简与自律
        if username == "cz_binance":
            if any(kw in text for kw in ["zoom out", "best performing", "15 years of green", "30 days of red", "long-term"]):
                suggestions.append(
                    f"📊 **人生也需要Zoom Out**: CZ说比特币15年涨了10000倍，但中间经历了无数次30%+回撤——"
                    f"你的人生也一样。9年嵌入式经验、北京安家、家庭、投资组合，" 
                    f"这些都是'长期趋势向上'的资产。短期焦虑(薪资/房贷/孩子升学)是正常的波动，" 
                    f"但zoom out看，你在正确的轨道上。保持节奏，不要因为30天的困难否定15年的积累。"
                )
            if any(kw in text for kw in ["$61k", "$67k", "zoom out", "trend", "narrative", "headline", "fundamental"]):
                suggestions.append(
                    f"📊 **交易心理学**: CZ说'不要交易标题，交易基本面'——"
                    f"这对你的生活也适用。BTC $61K时恐慌的人现在踏空，"
                    f"你的0.52 BTC还在。生活中也一样：不要被短期噪音影响长期判断，"
                    f"无论是职业选择(TFLM学习)还是家庭决策(孩子教育)，都要'zoom out'看大趋势。"
                )
            if any(kw in text for kw in ["focus", "专注", "simple", "简单", "life", "生活", "builder", "构建者"]):
                suggestions.append(
                    f"🧘 **极简与聚焦**: CZ强调'builders keep building'——真正创造价值的人持续前行。"
                    f"你的资产配置已经比较多元，生活中也需要做减法——"
                    f"聚焦端侧AI学习+投资研究+家庭，减少无效信息摄入。"
                )
            if any(kw in text for kw in ["patient", "耐心", "stay patient", "fundamental"]):
                suggestions.append(
                    f"⏳ **长期主义**: CZ说'保持耐心，基本面没变'——这不仅适用于BTC投资，也适用于你的职业转型。"
                    f"从嵌入式到端侧AI的转型需要时间积累，不急于求成。"
                )

        # 特朗普 — 宏观心态
        if username == "realDonaldTrump":
            if any(kw in text for kw in ["win", "胜利", "fight", "战斗"]):
                suggestions.append(
                    f"💪 **心态建设**: 特朗普的战斗精神值得借鉴。"
                    f"你当前面临求职+投资+孩子升学多重压力，"
                    f"保持积极心态，每个阶段都有解法。"
                )
            if any(kw in text for kw in ["peace", "和平", "deal", "协议", "iran"]):
                suggestions.append(
                    f"☮️ **宏观稳定利好个人生活**: 伊朗和平协议意味着地缘风险下降，"
                    f"全球经济和市场情绪可能改善。这对你的多资产配置是系统性利好，"
                    f"可以减少每天盯盘的焦虑，把更多精力投入学习和家庭。"
                )

        return "\n".join(suggestions) if suggestions else ""

    def _family_advice(self, username, content, translated):
        """生成家庭建议"""
        text = (content + " " + translated).lower()
        family = self.profile["family"]
        liabilities = self.profile["liabilities"]

        suggestions = []

        # 通用家庭风险提示
        if username == "cz_binance" and any(kw in text for kw in ["risk", "风险", "safe", "安全", "panic", "恐慌", "crash", "崩盘"]):
            suggestions.append(
                f"👨‍👩‍👧 **家庭财务安全网**: BTC近期从高点回落，CZ喊话不要恐慌。"
                f"你当前投资负债: 信用卡¥{liabilities['credit_card_invest']}" 
                f"(✅ 币安借贷已还清)，"
                f"家庭备用金¥{self.profile['assets']['cash']}是安全垫。"
                f"⚠️ 关键原则: 确保在任何市场情况下，孩子教育资金和房贷不受影响。"
                f"投资账户和家庭账户必须严格隔离。"
            )

        if username == "realDonaldTrump" and any(kw in text for kw in ["economy", "经济", "job", "就业", "manufacturing", "制造"]):
            suggestions.append(
                f"👨‍👩‍👧 **家庭规划与政策环境**: 特朗普关税政策推动制造业回流，"
                f"对你的影响双面: ①新华三作为国产设备商可能受益于国产替代→职业稳定；"
                f"②{family['location']}生活成本高，孩子{family['children']}在京上学需规划升学路径。"
                f"保持现金流健康，投资账户与家庭账户严格隔离。"
            )

        if username == "realDonaldTrump" and any(kw in text for kw in ["gas", "油价", "$0", "signing", "geneva", "日内瓦"]):
            suggestions.append(
                f"👨‍👩‍👧 **油价下降的家庭实惠**: 特朗普宣布油价降$0.47——"
                f"按北京家庭每月加油200升算，每月省¥60-70。虽然金额不大，"
                f"但油价下行带动的物流成本下降，会逐步传导到日常消费。"
                f"更重要的是通胀缓解→降息预期→你的房贷(商贷¥{liabilities['mortgage_commercial']}+公积金¥{liabilities['mortgage_fund']})月供有望下调。"
                f"📌 关注6/19日内瓦签署仪式后的政策窗口期。"
            )
        if username == "realDonaldTrump" and any(kw in text for kw in ["never", "nuclear", "核武器", "fully open", "flowing"]):
            suggestions.append(
                f"👨‍👩‍👧 **伊朗无核化 — 为孩子创造一个更安全的世界**: 特朗普宣布伊朗永久无核化——"
                f"这可能是这一代最重要的地缘安全进展。对你家庭(北京，{family['children']}在京上学)意味着：" 
                f"①全球核扩散风险降低→长期和平环境→孩子成长在更稳定的世界；" 
                f"②中东稳定→能源价格可控→降低生活成本；" 
                f"③全球risk-on→你的投资组合回暖→家庭财务压力减小。" 
                f"这不仅是投资利好，更是给下一代的安全保障。"
            )
        if username == "realDonaldTrump" and any(kw in text for kw in ["peace", "和平", "iran", "伊朗"]):
            suggestions.append(
                f"👨‍👩‍👧 **和平红利与家庭**: 伊朗和平协议降低全球地缘风险，"
                f"对你的家庭意味着: ①油价下行→生活成本降低；②降息预期→房贷压力可能减轻(商贷¥{liabilities['mortgage_commercial']}+公积金¥{liabilities['mortgage_fund']})；"
                f"③市场情绪好转→投资组合回暖。建议趁市场好转时优先削减高息负债。"
            )

        if username == "elonmusk" and any(kw in text for kw in ["cursor", "$60b", "acquire", "coding", "ai-native"]):
            suggestions.append(
                f"👨‍👩‍👧 **AI时代的教育投资**: SpaceX $600亿收购Cursor——"
                f"AI编程将从'专业技能'变成'基础技能'。"
                f"你孩子(在京上学)未来面对的就业市场，AI编程可能和今天的Office一样基础。"
                f"建议：让孩子从小接触AI工具，培养'用AI解决问题'的思维，" 
                f"而非死记硬背。你在学TFLM的过程本身就是在给孩子做榜样。"
            )
        if username == "elonmusk" and any(kw in text for kw in ["burry", "short", "做空", "never learn"]):
            suggestions.append(
                f"👨‍👩‍👧 **教孩子面对质疑**: 马斯克说'做空者从不学习'——"
                f"这是很好的家庭教育素材。孩子在学校可能被质疑、被嘲笑——"
                f"告诉他们：像马斯克一样，不要回应噪音，专注做自己的事。" 
                f"真正的成功是对质疑最好的回应。"
            )
            suggestions.append(
                f"👨‍👩‍👧 **父与子的技术救援**: 故事中儿子远程操控父亲的Model Y送医——"
                f"这是技术连接亲情的完美案例。对你家庭的启示："
                f"①让孩子理解技术不是'玩手机'而是'改变世界的力量'；"
                f"②你学TFLM、做嵌入式开发——将来也许你写的代码也能在关键时刻保护家人；"
                f"③最好的家庭教育不是报班，是让孩子看到父母在持续学习和创造价值。"
            )
        if username == "elonmusk" and any(kw in text for kw in ["censor", "审查", "protect the children", "保护儿童", "prison", "政客"]):
            suggestions.append(
                f"👨‍👩‍👧 **信息环境的家庭教育**: 马斯克说'审查总是以保护儿童为幌子'——"
                f"在数字时代，你孩子(在京上学)面临的不是信息太少而是太多。" 
                f"真正的'保护'不是封锁信息，而是培养批判性思维——" 
                f"和孩子一起讨论'为什么有人要审查信息'，比直接屏蔽更有效。" 
                f"你在学习TFLM的过程，本身就是在给孩子示范'如何获取和筛选知识'。"
            )
        if username == "elonmusk" and any(kw in text for kw in ["future", "未来", "mars", "火星", "moon", "月球", "inspire", "starship", "星舰", "10%", "odds", "成功机会"]):
            suggestions.append(
                f"👨‍👩‍👧 **为孩子点燃好奇心**: 马斯克说'让科幻变为现实，为每个人创造激动人心的未来'——"
                f"在为孩子规划教育路径时（非京籍升学6条路径），"
                f"也要培养他们对科技的好奇心。你正在学的端侧AI，也许某天可以和孩子一起做个AI小项目，"
                f"这比任何培训班都更能激发学习动力。"
            )
        if username == "elonmusk" and any(kw in text for kw in ["agi", "奇点", "singularity"]):
            suggestions.append(
                f"👨‍👩‍👧 **AGI时代的孩子教育**: 马斯克预测AGI 2026年到来。"
                f"对你孩子(在京上学)的教育规划启示：未来的核心竞争力不是'记忆知识'而是'理解AI+创造性思维'。"
                f"建议在家庭日常中引入AI工具(ChatGPT/Grok)，让孩子从小接触，把AI变成'学习伙伴'而非'竞争对手'。"
                f"你学TFLM的过程本身就是在给孩子做榜样——终身学习是最好的教育。"
            )

        return "\n".join(suggestions) if suggestions else ""


def analyze_tweets(tweets, profile):
    """分析推文并添加建议"""
    analyzer = ProfileAnalyzer(profile)
    return analyzer.analyze(tweets)
