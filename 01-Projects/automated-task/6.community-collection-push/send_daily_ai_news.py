"""
每日AI+半导体+机器人新闻推送 - 主入口脚本
功能：整理当日AI/半导体/机器人热点新闻，生成飞书interactive卡片并推送到群聊
覆盖六大板块：融资并购 / 产品发布 / 技术突破 / 行业法规 / 半导体芯片 / 机器人具身智能
"""

import json
import sys
import os

# 确保能找到同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from push_lark import send_interactive_card, verify_message, load_secrets
from profile_loader import load_latest_profile

# ==================== 数据 ====================
NEWS_DATE = "2026年8月30日"
NEWS_WEEK = "8月第五周｜周日休市｜英伟达129亿美元收购Hugging Face(拟)+Stripe 70亿美元收购OpenRouter+OpenAI自研芯片Jalapeño首秀超越GB300+苹果AI眼镜N50定档2027+欧盟AI法案正式执行+英伟达Q2营收962亿美元(+106%)+CRCL跌至$87.14(-7.53%)+BTC $78.8K"

# ---- 新闻条目 ----
# 筛选2026年8月28日-30日 AI/半导体/机器人六大板块核心新闻
NEWS_ITEMS = [
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "英伟达拟129亿美元收购Hugging Face，AI开源生态巨震",
        "summary": "8月28日消息，英伟达据报已同意以约129亿美元（约867亿人民币）收购全球最大开源AI平台Hugging Face，估值约86倍年化1.5亿美元收入。交易尚未签署正式协议，仍有失败可能。若完成，英伟达将从芯片供应商延伸至AI开源生态分发领域，掌控全球最大模型托管平台，AI产业链\"卖算力vs卖模型\"格局进一步重塑。",
        "source": "36氪 / LineVestNews / 科创板日报",
    },
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "Stripe以超70亿美元收购AI模型聚合平台OpenRouter",
        "summary": "8月24日，支付巨头Stripe宣布以超70亿美元收购AI模型聚合平台OpenRouter，加速在AI应用层和Agent基础设施领域的布局。同周，AI芯片公司Etched完成7亿美元融资（估值210亿美元），AI行业并购持续升温，大厂加速整合AI基础设施能力。",
        "source": "WEEX / 新浪财经 / 36氪",
    },
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "AI云基础设施Lambda获10亿美元融资，购买GPU租赁给微软",
        "summary": "8月29日，AI云基础设施公司Lambda获得摩根大通约10亿美元短期私募债务，用于购买英伟达GPU并租赁给微软。此前Lambda已获15亿美元风投（估值54.3亿美元），另有30亿美元Pre-IPO轮融资传闻。交易结构显示市场对AI算力采购和云服务需求持续旺盛。",
        "source": "GuruFocus / AI-Market-Watch / 36氪",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "苹果首款AI智能眼镜N50定档2027年，轻量化无屏设计",
        "summary": "8月30日，据9to5mac报道，苹果首款消费级AI智能眼镜（内部代号N50）预计最早2027年面世。与Vision Pro不同，该眼镜为轻量化无屏设计，核心交互依赖摄像头、麦克风和扬声器，赋予Siri\"观察\"现实环境的能力。计划2027年6月WWDC向开发者公布，9月与iPhone 20周年纪念版同期发售，摄像头功能可能采用\"保留但禁止常规拍照录像\"的折中设计，所有影像数据本地处理。",
        "source": "环球网 / 9to5mac / 新浪科技",
    },
    {
        "category": "\U0001f4e6 产品发布",
        "title": "银河通用获千台人形机器人订单+超3亿美元融资，估值破200亿",
        "summary": "8月29日，银河通用宣布与沛克精密达成战略合作，将在工业精密制造领域部署超1000台人形智能机器人。公司同时完成新一轮超3亿美元融资，创单人形智能领域融资纪录，最新估值超200亿元。这是具身智能领域从\"炫技\"走向\"产线实干\"的又一标志性订单。",
        "source": "GMTeight / 36氪 / 新浪科技",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "OpenAI自研推理芯片Jalapeño首秀：每瓦吞吐量超英伟达GB300达1.5-1.9倍",
        "summary": "8月27日，OpenAI与博通合作开发的自研推理芯片Jalapeño首次公开测试性能数据：每瓦吞吐量较英伟达GB300提升约1.5-1.9倍，端到端延迟降低约3.4倍，最低延迟下Token生成速度约2.7-4.1倍。芯片功耗约700瓦，专为推理阶段设计，研发周期仅约9个月，计划2026年底投入使用。这标志着AI芯片生态竞争进入新阶段——\"卖模型\"的OpenAI也开始自研芯片。",
        "source": "36氪 / AIToolsRecap / TechCrunch",
    },
    {
        "category": "\U0001f52c 技术突破",
        "title": "英伟达Q2 FY2027财报：营收962亿美元同比增106%，AI需求持续爆发",
        "summary": "8月26日，英伟达发布Q2 FY2027财报：总营收962.21亿美元，同比增106%，环比增18%，净利润597亿美元。数据中心季度收入890亿美元，同比增长117%。英伟达预计FY2028营收增长约70%。同时，英伟达扩大与AWS合作，计划到2028年再部署200万颗GPU。AI算力需求持续推动全球基础设施扩张，未见放缓迹象。",
        "source": "NVIDIA官方博客 / 36氪 / 华尔街见闻",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "欧盟AI法案正式进入执行阶段：透明度规则生效，最高罚全球年收入3%",
        "summary": "自2026年8月2日起，欧盟AI法案正式进入执行阶段。欧盟委员会AI办公室获得对通用人工智能(GPAI)模型提供商的调查和处罚权，最高可处全球年收入3%或1500万欧元罚款。透明度规则要求聊天机器人等交互式AI系统明确告知用户\"正在与AI交互\"。高风险AI系统合规义务通过《数字双年法案》延期至2027年底。全球AI监管进入实操阶段。",
        "source": "Regulation-AI.eu / 新浪财经 / 36氪",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "Hot Chips 2026：英伟达Vera Rubin+AMD CDNA 5+Intel Diamond Rapids齐亮相",
        "summary": "8月26日Hot Chips 2026大会上，三大芯片巨头同台竞技：英伟达发布Vera Rubin平台，88核Arm Vera CPU（1.2TB/s内存带宽）+Rubin GPU（288GB HBM4/22TB/s带宽），专为Agentic AI设计；AMD展示CDNA 5架构Instinct MI455X，8颗2nm计算芯粒+432GB HBM4/23.3TB/s带宽；Intel展示Diamond Rapids服务器处理器，18A-P工艺+256性能核+650W TDP。AI芯片算力军备竞赛持续升级。",
        "source": "OCClub / TrendForce / 快科技",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "半导体涨价潮再起：卓胜微/国民技术MCU涨10-20%/ST年内第三次调价",
        "summary": "8月28日消息，新一轮芯片涨价潮来袭：卓胜微全系列RF产品9月1日起涨价；国民技术部分MCU产品涨价10%-20%；STMicroelectronics实施年内第三次价格调整（8月23日）；ADI将于9月13日启动第二轮涨价。AI计算需求抢夺成熟制程产能、供应链成本上升、供需持续紧张是主因，国产替代需求同步增长。",
        "source": "C114通信网 / 电子工程世界 / 集微网",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "长鑫存储LPDDR6量产首发小米18 Fold，追平国际大厂节奏",
        "summary": "8月29日，长鑫存储(CXMT)宣布LPDDR6内存已进入量产，将首发搭载于小米18 Fold折叠旗舰。雷军祝贺长鑫这一突破，称玄戒O3芯片首批支持CXMT LPDDR6。SK海力士和三星计划2026下半年量产LPDDR6，美光尚在样品阶段（预计2027年商用），长鑫的LPDDR6量产时间线与国际大厂基本同步，标志国产存储技术取得重大突破。",
        "source": "今日头条 / 中国电子报 / 集微网",
    },
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "优必选2026中报：营收12.7亿元翻倍，人形机器人销量同比增268%",
        "summary": "8月28日，优必选发布2026年中期业绩：总营收12.7亿元，同比增长104.2%；人形机器人销量16123台，同比增268.3%。全尺寸具身智能人形机器人收入5.9亿元，同比增1445%，实现921台销量全球第一，成为核心增长引擎。优必选从\"亏损烧钱\"到\"营收翻倍\"的转折，验证了人形机器人商业化路径的可行性。",
        "source": "新浪财经 / 证券时报 / 36氪",
    },
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "Figure AI启动10亿美元Index项目：全球征集人类训练数据",
        "summary": "8月30日，Figure AI宣布启动Index项目，计划投入超10亿美元，在全球108个国家和地区招募普通人上传真实场景任务视频，为人形机器人Helix模型提供物理世界训练数据。项目已支付超1500万美元报酬，用户可通过移动端App上传家务、办公、工厂作业等日常任务视频。这是迄今规模最大的人形机器人训练数据采集计划，标志着\"数据飞轮\"成为具身智能竞争新壁垒。",
        "source": "羊城晚报 / Figure AI官方 / 机器之心",
    },
]

# ---- 投资与职业发展分析（从 profile_archive 动态生成） ----

def build_personalized_analysis():
    """基于最新个人档案，结合当日新闻生成个性化分析"""
    profile = load_latest_profile()
    if not profile:
        # 无档案时返回通用分析
        return _generic_analysis()

    career = profile.get("career", {})
    assets = profile.get("assets", {})
    crypto = assets.get("crypto", {})
    us_stocks = assets.get("stocks", {}).get("us", [])
    liabilities = profile.get("liabilities", {})
    family = profile.get("family", {})
    insurance = profile.get("insurance", {})

    btc_str = crypto.get("btc", "0.12980465")
    usdt_str = crypto.get("usdt", "$7,826.40")
    crcl_str = assets.get("crcl_concentration", "66.7%")
    cc_debt = liabilities.get("credit_card_invest", "\u00a5400,000")
    company = career.get("company", "新华三")
    role = career.get("role", "嵌入式开发工程师")
    salary = career.get("salary", "30K\u00d716")
    target_companies = career.get("target_companies", [])
    location = family.get("location", "北京")
    children = family.get("children", "有孩子")
    hanwei_ins = insurance.get("hanwei_zhongji", "达尔文50W")

    # 提取 CRCL 股数
    crcl_qty = "938.3"
    for s in us_stocks:
        if "CRCL" in s:
            m = __import__("re").search(r'([\d.]+)\s*\u80a1', s)
            if m:
                crcl_qty = m.group(1)

    # 提取 BTC 数量
    btc_qty = "0.1298"
    m = __import__("re").search(r'([\d.]+)\s*BTC', btc_str)
    if m:
        btc_qty = m.group(1)

    # 提取信用卡负债数字
    cc_short = "40W"
    m = __import__("re").search(r'\u00a5?([\d,]+)', cc_debt)
    if m:
        try:
            num = int(m.group(1).replace(",", ""))
            cc_short = f"{num//10000}W"
        except ValueError:
            cc_short = m.group(1)

    # 提取 DRAM 股数
    dram_qty = "57"
    for s in us_stocks:
        if "DRAM" in s:
            m = __import__("re").search(r'(\d+)\s*\u80a1', s)
            if m:
                dram_qty = m.group(1)

    # 提取 MRVL 股数
    mrvl_qty = "40.2"
    for s in us_stocks:
        if "\u8fc8\u5a01\u5c14" in s or "MRVL" in s:
            m = __import__("re").search(r'([\d.]+)\s*\u80a1', s)
            if m:
                mrvl_qty = m.group(1)

    investment = (
        "【AI方向】英伟达拟129亿美元收购Hugging Face(延伸AI开源生态)；"
        "Stripe 70亿美元收购OpenRouter(模型聚合平台)；"
        "OpenAI自研推理芯片Jalape\u00f1o首秀(每瓦吞吐量超GB300达1.5-1.9倍)；"
        "英伟达Q2营收962亿美元(+106%)；\n"
        "【半导体】Hot Chips 2026三大巨头同台(英伟达Vera Rubin/AMD CDNA 5群Intel Diamond Rapids)；"
        "芯片涨价潮再起(卓胜微/国民技术MCU+10-20%/ST年内第三次调价)；"
        "长鑫LPDDR6量产首发小米18 Fold(追平国际大厂节奏)。\n"
        "【机器人】优必选中报营收12.7亿翻倍，人形机器人销量+268%；"
        "Figure AI启动10亿美元Index项目(全球征集人类训练数据)；"
        "银河通用获千台机器人订单+超3亿美元融资。\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4cc 结合你的持仓({crcl_qty}股CRCL, {btc_qty}BTC, DRAM {dram_qty}股, MRVL {mrvl_qty}股)：\n"
        f"\u2022 CRCL {crcl_qty}股(集中度66.7%\u26a0\ufe0f) 8/28收盘$87.14(-7.53%)，较前日$94.24大幅回调。"
        f"Q2财报(8月5日盘前)后股价从$60+反弹至$94，但8/28单日暴跌7.5%显示市场对Circle估值仍有分歧。"
        f"CRCL集中度偏高仍是核心风险，不宜加仓，等待Q2财报后方向明朗\n"
        f"\u2022 DRAM {dram_qty}股：长鑫LPDDR6量产+国际大厂同步推进，但HBF新世代技术成本高于HBM(带宽仅60%)，"
        f"存储芯片涨价潮延续(MCU/RF全线调价)利好行业景气，短期持有观察\n"
        f"\u2022 MRVL {mrvl_qty}股：Hot Chips 2026上英伟达/AMD/Intel三巨头AI芯片军备竞赛升级，"
        f"MRVL定制ASIC和网络芯片受益于AI算力扩张，英伟达Q2营收962亿(+106%)验证AI需求持续爆发，"
        f"MRVL中长期受益逻辑不变，耐心等待企稳\n"
        f"\u2022 BTC 8/30报$78.8K，较24日$65.3K大幅反弹超20%！"
        f"英伟达Q2财报超预期+AI算力需求持续验证推动市场风险偏好回升，"
        f"BTC强势站上MA120上方，右侧信号强化。USDT$7,826可考虑逢回调分批建仓\n"
        f"\u2022 信用卡{cc_short}负债压力仍在，央行流动性宽松+AI产业链并购活跃提振市场情绪，"
        f"但CRCL单日暴跌7.5%警示单一持仓风险，需控制仓位防御为先"
    )

    career_text = (
        "【AI方向】英伟达拟129亿美元收购Hugging Face(延伸AI开源生态)；"
        "OpenAI自研推理芯片Jalape\u00f1o首秀(每瓦吞吐量超GB300达1.5-1.9倍)；"
        "英伟达Q2营收962亿美元(+106%)；\n"
        "【半导体方向】Hot Chips 2026三巨头同台(英伟达Vera Rubin/AMD CDNA 5/Intel Diamond Rapids)；"
        "芯片涨价潮再起(卓胜微/国民技术MCU+10-20%/ST年内第三次调价)；"
        "长鑫LPDDR6量产首发小米18 Fold。\n"
        "【机器人方向】优必选营收12.7亿翻倍，人形机器人销量+268%；"
        "Figure AI 10亿美元Index项目(全球征集人类训练数据)；"
        "银河通用获千台机器人订单+超3亿美元融资。\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4cc 结合你的职业({company}/{role}，{salary}，{location})：\n"
        f"\u2022 英伟达129亿美元收购Hugging Face+OpenAI自研芯片Jalape\u00f1o，"
        f"AI产业从\"卖模型\"向\"卖算力\"+开源生态延伸趋势明确，端侧AI推理芯片需求持续爆发。"
        f"你9年嵌入式经验(自研RTOS/TSN/DSP)在端侧AI芯片和机器人底层软件栈中具有独特价值\n"
        f"\u2022 优必选营收翻倍+银河通用千台订单+Figure AI 10亿美元数据计划，"
        f"具身智能从\"烧钱\"走向\"商业闭环\"加速，嵌入式边缘计算+多模态感知+精密控制是关键技能方向\n"
        f"\u2022 Hot Chips 2026三巨头AI芯片军备竞赛升级(AI芯片算力竞争白热化)，"
        f"建议关注目标公司(小米/地平线/寒武纪/百度/字节跳动/联想/石头科技/美团等)的端侧AI芯片和机器人相关岗位动态"
    )

    family_text = (
        "英伟达拟129亿美元收购Hugging Face+Stripe 70亿美元收购OpenRouter。"
        "OpenAI自研芯片Jalape\u00f1o首秀+英伟达Q2营收962亿美元(+106%)。"
        "Hot Chips 2026三巨头同台+芯片涨价潮再起+长鑫LPDDR6量产。"
        "欧盟AI法案正式执行(最高罚全球年收入3%)。\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4cc 结合你的家庭({location}，{children})：\n"
        f"\u2022 保险已配置{hanwei_ins}\u2705，定寿(目标200W)和配偶重疾(目标30-50W)仍待配置——"
        f"全球AI产业并购整合加速(英伟达+Hugging Face/Stripe+OpenRouter)，"
        f"产业链格局重塑带来职业机遇但也伴随不确定性，家庭抗风险能力需进一步强化\n"
        f"\u2022 家庭备用金\u00a5630,808严格隔离不动，CRCL 8/28收盘$87.14(-7.53%)大幅回调，"
        f"信用卡{cc_short}需优先偿还。BTC $78.8K快速反弹站上MA120，但CRCL集中度66.7%仍是核心风险\n"
        f"\u2022 Figure AI 10亿美元Index项目全球征集人类训练数据+优必选营收翻倍，"
        f"具身智能商业化加速，C端消费级机器人走向家庭场景趋势明确，"
        f"建议关注暑期AI学习工具，为孩子规划机器人/编程体验，培养AI时代核心竞争力"
    )

    return {"investment": investment, "career": career_text, "family": family_text}


def _generic_analysis():
    """无个人档案时的通用分析兜底"""
    return {
        "investment": (
            "【AI算力】英伟达拟129亿美元收购Hugging Face+Stripe 70亿美元收购OpenRouter；"
            "OpenAI自研芯片Jalape\u00f1o首秀(每瓦吞吐量超GB300达1.5-1.9倍)；"
            "英伟达Q2营收962亿美元(+106%)；Lambda 10亿美元GPU融资。\n"
            "【半导体】Hot Chips 2026三巨头同台(英伟达Vera Rubin/AMD CDNA 5/Intel Diamond Rapids)；"
            "芯片涨价潮再起(卓胜微/国民技术MCU+10-20%/ST年内第三次调价)；"
            "长鑫LPDDR6量产首发小米18 Fold。\n"
            "【机器人】优必选营收12.7亿翻倍+银河通用千台订单+Figure AI 10亿美元Index项目。"
        ),
        "career": (
            "【AI方向】英伟达收购Hugging Face+OpenAI自研芯片+英伟达Q2营收962亿(+106%)。\n"
            "【半导体方向】Hot Chips 2026三大巨头同台+芯片涨价潮+长鑫LPDDR6量产。\n"
            "【机器人方向】优必选营收翻倍+Figure AI 10亿美元数据计划+银河通用千台订单。"
        ),
        "family": (
            "英伟达129亿美元收购Hugging Face+Stripe 70亿美元收购OpenRouter。"
            "OpenAI自研芯片Jalape\u00f1o首秀。"
            "欧盟AI法案正式执行。"
            "芯片涨价潮再起+长鑫LPDDR6量产。"
        ),
    }

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年8月30日，周日休市，回顾8月最后一周三大方向核心事件：\n"
    "一 AI方向：英伟达拟129亿美元收购Hugging Face(延伸至AI开源生态)、Stripe 70亿美元收购OpenRouter(模型聚合平台)——"
    "AI产业并购整合进入加速期，大厂从\"自研模型\"转向\"收购生态\"；"
    "OpenAI自研推理芯片Jalape\u00f1o首秀(每瓦吞吐量超GB300达1.5-1.9倍，研发仅9个月)，"
    "\"卖模型\"的OpenAI也开始自研芯片，AI芯片竞争格局进一步多元化；"
    "英伟达Q2营收962亿美元(+106%)，AI需求持续爆发未见放缓。\n"
    "二 半导体方向：Hot Chips 2026上英伟达Vera Rubin(88核Arm+288GB HBM4)、AMD CDNA 5(8颗2nm芯粒+432GB HBM4)、"
    "Intel Diamond Rapids(18A-P+256核)三巨头同台竞技，AI芯片算力军备竞赛全面升级；"
    "芯片涨价潮再起(卓胜微/国民技术MCU+10-20%/ST年内第三次调价)，"
    "AI计算需求抢夺成熟制程产能是主因；"
    "长鑫LPDDR6量产首发小米18 Fold，国产存储技术追平国际大厂节奏。\n"
    "三 机器人方向：优必选中报营收12.7亿翻倍(+104%)，人形机器人销量16123台(+268%)，"
    "全尺寸人形机器人收入5.9亿(+1445%)，从\"亏损烧钱\"到\"营收翻倍\"验证商业化路径可行性；"
    "Figure AI启动10亿美元Index项目，全球征集人类训练数据——\"数据飞轮\"成为具身智能竞争新壁垒；"
    "银河通用获千台机器人订单+超3亿美元融资，行业从\"炫技\"走向\"产线实干\"。\n"
    "最具系统性冲击的是英伟达拟129亿美元收购Hugging Face——"
    "这不仅是一笔巨额收购，更标志着AI产业链从\"卖芯片\"到\"占生态\"的战略升级。"
    "OpenAI自研芯片Jalape\u00f1o首秀(9个月研发周期)则意味着AI芯片\"去英伟达化\"趋势加速，"
    "长期利好端侧AI推理芯片和定制化ASIC方案。"
    "CRCL($87.14,-7.53%)单日暴跌，较前日$94.24大幅回调，"
    "集中度66.7%仍是核心风险，不建议加仓，等待企稳。"
    "BTC $78.8K较一周前$65.3K大幅反弹超20%，站上MA120，右侧信号强化，"
    "USDT$7,826可考虑逢回调分批建仓。"
    "AI产业并购整合加速+芯片军备竞赛升级+具身智能商业化验证，"
    "端侧AI推理芯片和C端消费级机器人是确定性方向，"
    "你9年嵌入式经验在端侧AI芯片和机器人底层软件栈中具有独特价值，建议关注目标公司相关岗位动态。"
)


def build_card_json() -> dict:
    """构建飞书 interactive 卡片 JSON"""
    elements = []

    # ---- 新闻列表（按分类分组） ----
    current_category = None
    for i, news in enumerate(NEWS_ITEMS):
        # 分类标题
        if news["category"] != current_category:
            if current_category is not None:
                elements.append({"tag": "hr"})
            current_category = news["category"]
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{news['category']}**",
                },
            })

        # 新闻条目
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**{i + 1}. {news['title']}**\n{news['summary']}\n\U0001f4ce 来源：{news['source']}",
            },
        })

    # ---- 分割线 + 个性化分析（从 profile_archive 动态加载） ----
    analysis = build_personalized_analysis()

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "**\U0001f4ca 投资与职业发展分析**",
        },
    })
    elements.append({
        "tag": "div",
        "fields": [
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**\U0001f4b9 投资方向**\n{analysis['investment']}",
                },
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**\U0001f4bc 职业发展**\n{analysis['career']}",
                },
            },
            {
                "is_short": False,
                "text": {
                    "tag": "lark_md",
                    "content": f"**\U0001f3e0 家庭规划**\n{analysis['family']}",
                },
            },
        ],
    })

    # ---- 趋势点评 ----
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**\U0001f4c8 今日趋势点评**\n{TREND_COMMENTARY}",
        },
    })

    # ---- 页脚 ----
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"Trae每日AI+半导体+机器人新闻推送 | {NEWS_DATE} {NEWS_WEEK} | 数据来源：AI科技速览、科创板日报、财联社、新浪财经、环球网财经、同花顺iFinD、东方财富网、头条新闻、搜狐科技、36氪、TrendForce等",
            }
        ],
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"AI+半导体+机器人日报 | {NEWS_DATE}",
            },
            "template": "blue",
        },
        "elements": elements,
    }

    return card


def main():
    print("=" * 60)
    print(f"  每日AI+半导体+机器人新闻推送 - {NEWS_DATE}")
    print("=" * 60)

    # 0. 加载飞书凭证
    secrets = load_secrets()
    app_id = secrets["app_id"]
    app_secret = secrets["app_secret"]
    chat_id = secrets["chat_id"]

    # 1. 构建卡片
    print(f"\n[STEP 1] 构建 interactive 卡片 ...")
    card = build_card_json()
    card_str = json.dumps(card, ensure_ascii=False, indent=2)
    print(f"  卡片 JSON 长度: {len(card_str)} 字符")
    print(f"  新闻条目数: {len(NEWS_ITEMS)}")

    # 2. 发送消息
    print(f"\n[STEP 2] 发送消息到群聊 {chat_id} ...")
    try:
        message_id = send_interactive_card(chat_id, card, app_id=app_id, app_secret=app_secret)
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")
        sys.exit(1)

    # 3. 验证消息
    print(f"\n[STEP 3] 验证消息完整性 ...")
    try:
        verify_message(message_id, app_id=app_id, app_secret=app_secret)
        print(f"  消息验证通过！")
    except Exception as e:
        print(f"[WARN] 验证消息时出现问题: {e}")

    print(f"\n{'=' * 60}")
    print(f"  推送完成！message_id: {message_id}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()