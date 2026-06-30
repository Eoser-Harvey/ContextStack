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

# ==================== 数据 ====================
NEWS_DATE = "2026年6月30日"
NEWS_WEEK = "6月最后一周"

# ---- 新闻条目 ----
NEWS_ITEMS = [
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "Windsurf并购案72小时三国杀：Google 24亿美元抢人，Cognition接盘业务",
        "summary": "AI编码初创公司Windsurf在72小时内完成行业史上最复杂的并购拆分——Google以24亿美元签下人才许可协议，将CEO Varun Mohan等核心团队纳入DeepMind；随后Cognition（Devin开发商）收购剩余业务，包括IP、产品、品牌及8200万美元ARR。此案深刻揭示AI人才争夺已进入白热化阶段，顶级AI工程师成为比模型更稀缺的战略资源。",
        "source": "MefAI / 今日头条",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "OpenAI发布GPT-5.6 Sol预览版：编码与安全能力大幅跃升，配备史上最严安全栈",
        "summary": "6月26日，OpenAI正式预告GPT-5.6系列模型，旗舰版Sol在编程、生物学与网络安全领域刷新多项基准，配备迄今最先进的安全防护栈。同时发布Terra（平衡型）和Luna（低成本）两个版本，形成完整产品矩阵。OpenAI将能力、安全、价格和发布节奏重新绑定，模型发布更像基础设施准入测试而非单纯产品发布。",
        "source": "OpenAI / 今日头条",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "微软6月30日起取消Claude Code许可，数千工程师迁移至自研MAI模型",
        "summary": "微软宣布自6月30日起取消大部分内部Claude Code许可证，将数千名工程师迁移至GitHub Copilot CLI。此前微软在Build 2026上发布了7款自研MAI模型（含MAI Thinking 1），AI CEO Mustafa Suleyman明确表示Anthropic模型在企业规模下成本过高，每工程师月费超2000美元。此举标志着AI编码工具从\"模型绑定\"走向\"模型编排\"，大厂自研AI工具加速替代第三方方案。",
        "source": "TechWeb / Studio Global",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "国常会专题部署AI：加力推进超大规模智算集群建设，科创板第五套标准扩围至AI/半导体",
        "summary": "6月29日，李强主持国务院常务会议专题听取人工智能发展汇报，明确三大发力方向：加快关键技术攻关和超大规模智算集群建设、强化高质量数据供给、支持企业基础研究与前沿探索。同步将科创板第五套上市标准扩围至AI大模型、半导体硬科技未盈利企业，从融资端扶持前沿技术研发。这是国家级顶层加码AI的重磅定调，智算集群建设上升为硬性推进任务。",
        "source": "央视新闻 / 东方财富网",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "全球近20家半导体企业7月1日集体涨价，AI算力驱动景气度传导至上游",
        "summary": "7月1日起，全球近20家模拟及功率半导体企业同步启动新一轮涨价，包括英飞凌、德州仪器、扬杰科技、华润微等头部厂商，年内已呈现多批次阶梯式调价特征。AI算力集群功耗激增是核心驱动因素，高端AI芯片需求爆发导致上游功率器件、模拟芯片产能紧缺，不少厂商在手订单饱满、产能能见度已排至2027年。半导体行业正式进入AI超级周期驱动的全面景气阶段。",
        "source": "东方财富网 / 今日头条 / 财联社",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "工信部发布《高速光模块产业发展白皮书》：光模块定位AI算力/6G核心底层硬件",
        "summary": "6月26日，工信部正式发布《高速光模块产业发展白皮书》，明确高速光模块是AI算力、6G核心底层硬件，设定硬性国产替代目标：2028年高端200G EML光芯片自给率45%，配套磷化铟产业专项基金补贴扩产。叠加《\"人工智能+信息通信\"创新发展实施意见(2026-2028年)》落地，光模块产业迎来政策+需求双重黄金窗口期。",
        "source": "工信部 / 中华工商时报 / 东方财富网",
    },
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "智元机器人第15000台具身智能机器人精灵G2量产下线，交付龙旗科技工厂",
        "summary": "6月28日，智元机器人宣布第15000台通用具身智能机器人精灵G2正式量产下线，当天即交付电子设备制造企业龙旗科技，投入智能制造产线作业。自今年3月突破万台量产大关以来仅用时不足3个月，再度刷新全球具身智能机器人量产速度纪录。在具身智能上半年融资超460亿元的背景下，真正能拿出万台级量产数字的玩家屈指可数，智元率先跨过量产验证门槛。",
        "source": "IT之家 / 界面新闻 / 今日头条",
    },
]

# ---- 投资与职业发展分析 ----
ANALYSIS = {
    "investment": (
        "【AI算力】国常会专题部署AI+超大规模智算集群建设，政策力度空前。全球近20家半导体企业7月1日集体涨价，AI算力需求正从下游传导至上游全产业链。工信部光模块白皮书明确国产替代目标2028年光芯片自给率45%，光模块/光芯片赛道确定性极强。Windsurf 24亿美元并购案+微软弃Claude转向自研，AI编码工具赛道估值逻辑从\"模型领先\"转向\"生态整合\"。"
        "【半导体】7月1日近20家厂商集体涨价是标志性事件，功率半导体接棒存储芯片成AI时代新增长引擎。扬杰科技、华润微等订单排至2027年，行业景气度明确。光模块白皮书催化磷化铟(InP)、EML光芯片等上游材料国产替代加速，科创板第五套标准扩围为半导体硬科技未盈利企业打开融资通道，国产替代+政策红利双主线并行。"
        "【机器人】智元15000台量产下线标志具身智能从\"讲故事\"进入\"拼量产\"阶段。上半年融资288起超460亿元但投资逻辑已转向量产验证，有万台级交付能力的头部企业享受估值溢价。关注优必选等具身智能标的，以及智元供应链上的MCU/传感器/驱动国产替代机会。"
    ),
    "career": (
        "【AI方向】微软砍Claude Code转向自研MAI+GitHub Copilot CLI，释放明确信号：AI编码工具正在从\"用模型\"进化到\"编排模型\"。嵌入式开发者应关注AI辅助编程工具链（Copilot/Trae等）的深度使用，将Agent工作流集成到嵌入式开发流程中。国常会加码智算集群建设，AI基础设施工程师（算力调度、集群运维）需求激增。"
        "【半导体方向】光模块白皮书+磷化铟专项基金补贴扩产，光芯片设计、封装测试、光电共封装(CPO)成为新稀缺岗位。近20家半导体厂商集体涨价意味着行业进入扩张周期，国产替代芯片设计、模拟IC、功率器件方向人才需求旺盛。具备嵌入式+通信双重背景者，转型光通信/6G交叉领域优势明显。"
        "【机器人方向】智元15000台量产证明具身智能已跨越\"能不能造\"进入\"能不能批量造\"阶段。量产阶段最缺的不是AI算法人才，而是嵌入式底层工程师——MCU实时控制、RTOS调度、电机驱动、传感器融合。9年嵌入式经验可直接迁移至机器人运动控制，职业转型路径清晰且薪酬天花板更高，建议重点关注智元、优必选等头部企业招聘动态。"
    ),
    "family": (
        "【消费决策】半导体7月1日集体涨价将传导至消费电子终端价格，手机、电脑、家电可能迎来新一轮涨价。建议家庭大件消费（如换手机、买家电）在涨价传导前尽早决策。北京AI产业集聚+智算集群建设推高电力需求，夏季用电高峰叠加算力功耗，家庭电费支出可能上升，关注节能家电与智能用电管理方案。"
        "【育儿教育】GPT-5.6 Sol编程能力大幅升级+微软用AI替代Claude Code，AI编码能力正以月为单位迭代。建议引导孩子学习AI编程助手使用（如Trae/Copilot），培养\"人机协作编程\"能力而非单纯学语法。国常会加码AI人才培养，北京中小学AI教育投入将持续加大，可关注海淀/朝阳AI特色课程与竞赛机会。"
        "【家庭健康】夏季高温+AI算力数据中心高能耗，北京空气质量与用电负荷双重承压。建议家庭配备空气净化器+智能温控设备，关注光伏储能等绿色家居方案享受政策补贴。智元机器人15000台量产下线，家用服务机器人从\"玩具\"走向\"工具\"，未来2-3年家庭机器人消费选择将大幅丰富，可前瞻关注教育机器人、家务机器人等品类。"
    ),
}

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年6月30日，上半年收官日，AI、半导体、机器人三大赛道在政策、产业、资本层面同时迎来重磅催化。"
    "①AI方向：国常会专题加码智算集群建设+OpenAI GPT-5.6 Sol编码能力跃升+微软弃Claude转向自研MAI，三重信号叠加标志着AI正从\"模型竞赛\"进入\"基础设施+工程落地\"新阶段。"
    "②半导体方向：7月1日全球近20家厂商集体涨价是AI超级周期全面传导至上游的标志性事件，工信部光模块白皮书同步打开国产替代新空间，半导体产业链全面开花。"
    "③机器人方向：智元15000台量产下线证明具身智能已跨过量产验证门槛，从\"讲故事\"到\"拼量产\"的淘汰赛正式开启，有交付能力的头部企业将享估值溢价。"
    "2026年上半年收官，三大赛道均以\"政策加码+产业突破+资本涌入\"三重共振收尾，下半年AI算力基础设施、半导体国产替代、具身智能量产落地仍是最确定的三条主线。"
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

    # ---- 分割线 + 分析 ----
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "**\U0001f4ca 投资与职业发展分析**",
        },
    })

    # 三栏 fields 布局
    elements.append({
        "tag": "div",
        "fields": [
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**\U0001f4b9 投资方向**\n{ANALYSIS['investment']}",
                },
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**\U0001f4bc 职业发展**\n{ANALYSIS['career']}",
                },
            },
            {
                "is_short": False,
                "text": {
                    "tag": "lark_md",
                    "content": f"**\U0001f3e0 家庭规划**\n{ANALYSIS['family']}",
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
                "content": f"Trae每日AI+半导体+机器人新闻推送 ｜ {NEWS_DATE} {NEWS_WEEK} ｜ 数据来源：央视财经、财联社、Business Insider、Axios、Reuters、东方财富网等公开媒体",
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
