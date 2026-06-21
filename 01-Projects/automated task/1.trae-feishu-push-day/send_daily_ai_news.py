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
from push_lark import send_interactive_card, verify_message

# ==================== 配置 ====================
CHAT_ID = "oc_9e92e8f883959df53547b20b259e174d"

# ==================== 数据 ====================
NEWS_DATE = "2026年6月21日"
NEWS_WEEK = "6月第三周"

# ---- 新闻条目 ----
NEWS_ITEMS = [
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "SpaceX拟600亿美元收购Cursor母公司Anysphere，创AI编程赛道最大并购",
        "summary": "6月16日，SpaceX宣布与AI编程工具Cursor母公司Anysphere签署最终合并协议，隐含股权价值约600亿美元，为全球AI编程赛道迄今最大单笔并购。交易预计Q3完成，马斯克将AI编程能力纳入xAI生态体系。",
        "source": "投资界 / 腾讯新闻",
    },
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "Robo.ai拟6000万美元收购QC Capital，布局AI硬科技孵化",
        "summary": "6月19日，纳斯达克上市公司Robo.ai宣布以6000万美元股权收购AI硬科技控股平台QC Capital 100%股权。QC Capital需在2026-2027年累计实现约24亿美元收入。Robo.ai持续扩展AI驱动的跨境并购与产业孵化版图。",
        "source": "美通社 / 全球TMT",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "WAIC 2026倒计时30天：超300款AI产品将全球首发",
        "summary": "6月17日，2026世界人工智能大会举行倒计时30天发布会。大会7月17-20日在上海举办，展览面积超10万平米，1100余家企业参展，超300款AI产品全球首发。升级版WAIC City Walk串联上海30余个AI应用场景，覆盖医疗、金融、教育等领域。",
        "source": "新华社 / 上海发布",
    },
    {
        "category": "\U0001f4e6 产品发布",
        "title": "赛豆科技发布AI原生出行品牌AIVA，主打\u201cAI定义汽车\u201d",
        "summary": "6月9日，赛豆科技发布AI原生出行品牌AIVA及Origin Concept概念车，提出\u201c先有AI，再有车\u201d颠覆性命题。同步官宣量产车型AIVA 01将搭载自研DriveAgent多模态驾驶系统，已获腾讯、比亚迪等战略投资。",
        "source": "36氪 / 界面新闻",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "Transformer之父Noam Shazeer离开Google加入OpenAI，AI人才战升级",
        "summary": "6月18日，Google DeepMind工程副总裁、Gemini联席负责人、Transformer原论文共同作者Noam Shazeer宣布离开谷歌加入OpenAI，担任架构研究负责人。此前谷歌以27亿美元估值收购其创立的Character.AI将其召回，如今再度流失。",
        "source": "The Verge / 机器之心",
    },
    {
        "category": "\U0001f52c 技术突破",
        "title": "Google DeepMind发布《从AGI到ASI》重磅报告，重新定义AI发展路径",
        "summary": "6月中旬，Google DeepMind发布57页长篇报告《从AGI到ASI》，对全球追逐AGI的热潮提出审慎判断。报告系统梳理了从通用人工智能到超级智能的技术鸿沟、安全挑战与时间表预估，引发学界与产业界广泛讨论。",
        "source": "Google DeepMind / 机器之心",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "七部门联合印发2026-2028行动方案：算力基础设施与AI智能体成核心主线",
        "summary": "6月18日，工信部、网信办等七部门联合印发《促进平台经济大中小企业协同发展行动方案(2026-2028年)》。首次将通用大模型、行业大模型、AI智能体并列定为目标，推动算力资源开放与互联互通，鼓励适配国产GPU和操作系统。",
        "source": "人民财讯 / 新华网",
    },
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "AI模型首次被列入出口管制清单，管制力度超EUV光刻机",
        "summary": "6月中旬，美国商务部将AI大模型权重参数列入出口管制物项清单，管制力度被认为超过对EUV光刻机的限制。此举对全球AI模型跨境合作、开源社区及云计算服务模式产生深远影响，OpenAI等多方发布合规评估报告。",
        "source": "CSIS / 财联社",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "美股半导体设备板块狂飙：7家公司年内股价翻倍，本周齐创新高",
        "summary": "6月20日《科创板日报》统计：美股总市值超百亿美元的9家半导体设备公司年内涨幅均超75%，其中应用材料、拉姆研究、科磊、MKS等7家实现翻倍，MKS涨幅达154.3%居首。花旗、瑞银同步上调设备股目标价，看好NAND与AI驱动需求。",
        "source": "科创板日报 / 瑞银",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "佰维存储子公司获长江存储入股，半导体\u201c垂直整合2.0\u201d加速",
        "summary": "6月，佰维存储自研存储芯片测试设备子公司成都态坦科技获长江存储产业基金战略入股，ATE测试机已在国内一线IDM厂商量产交付。赛微电子亦进军光刻机产业链，璞璘科技纳米压印光刻机量产成本仅为传统DUV方案的十分之一。",
        "source": "证券时报 / 爱集微",
    },
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "张江具身智能供应链大会开幕，80余家企业共探产业化路径",
        "summary": "6月16日，2026张江具身智能供应链大会在浦东开幕，聚焦具身智能产业生态。80余家企业围绕人形机器人商业化落地、灵巧手产业化、精密减速器国产替代等议题深入探讨，标志具身智能正从实验室加速走向供应链规模化。",
        "source": "腾讯新闻 / 浦东发布",
    },
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "具身智能赛道融资狂飙：千寻智能三个月吸金45亿元",
        "summary": "6月最新统计显示，千寻智能三个月内完成45亿元融资，星源智十个月累计融资超30亿元。脑机接口与具身智能交叉赛道获资本密集押注，人形机器人产业基金规模已突破2000亿元。产业链核心零部件国产替代进入兑现窗口。",
        "source": "36氪 / 投资界",
    },
]

# ---- 投资与职业发展分析 ----
ANALYSIS = {
    "investment": (
        "【AI算力】七部门新政锁定算力为主赛道，WAIC 2026超300款新品待发，算力基础设施与AI智能体是未来三年最强政策主线，关注算力租赁、数据中心液冷、国产GPU适配标的。"
        "【半导体】美股设备股年内翻倍揭示趋势：AI投资正从芯片向上游设备扩散。国内垂直整合2.0（佰维+长江存储）路径值得关注，先进封装与测试设备国产替代加速，SEMI预测2026全球设备市场1680亿美元。"
        "【机器人】具身智能单赛道融资已超2000亿元，千寻智能三个月吸金45亿元信号明确。人形机器人产业链正经历\u201c资本涌入\u2192量产验证\u2192供应链成熟\u201d三阶段，精密减速器、力矩传感器等核心零部件是最确定性投资方向。"
    ),
    "career": (
        "【AI方向】Transformer之父Noam Shazeer入局OpenAI，顶级人才争夺白热化。Agent开发（多智能体协作、工具调用）、AI+行业（出行、医疗、金融）复合型岗位薪酬涨幅超50%，建议掌握LangChain/SwarmFlow等框架。"
        "【半导体方向】国产芯片设备、先进封装、算力架构设计人才需求激增，半导体设备工程师薪资涨幅领先传统IC设计30%以上。垂直整合模式下\u201c工艺+装备\u201d交叉人才最吃香。"
        "【机器人方向】具身智能\u201c大脑（AI）+小脑（运控）+身体（本体）\u201d三栖人才极度稀缺，机械/电子/算法交叉背景年薪普遍突破80万，供应链大会密集召开释放大量产业岗位信号。"
    ),
    "family": (
        "AI内容标识新规全面落地，家长应引导孩子识别AI生成内容，培养数字媒体素养。"
        "人形机器人正从实验室走向家庭场景，建议关注青少年编程与机器人教育的早期培养，2026年暑期机器人夏令营报名量同比增长300%，布局AI时代的核心素养正当时。"
    ),
}

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年6月第三周，AI产业进入\u201c三浪叠加\u201d的质变时刻。"
    "\u2460AI人才层面：Noam Shazeer从谷歌跳槽OpenAI，27亿美元估值也未能留住Transformer之父，顶级人才的天平正加速向OpenAI倾斜，全球AI人才争夺战进入\u201c亿元年薪\u201d时代；"
    "\u2461半导体层面：美股设备股集体翻倍创历史新高，国内垂直整合2.0模式加速（佰维+长江存储），SEMI Q1全球设备出货365.5亿美元创新高——AI投资正从芯片向上游设备全链条扩散；"
    "\u2462具身智能层面：千寻智能三个月融资45亿元，张江供应链大会80余家企业聚首，脑机接口与机器人交叉赛道资本密集涌入。"
    "未来30天，WAIC 2026（7月17日）超300款AI新品首发和英伟达线上年度技术大会（6月24日）将是两大关键观测节点，机器人产业链亦将迎来密集催化周。"
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
            "content": f"**\U0001f4c8 今日趋势点评**\n{''.join(TREND_COMMENTARY)}",
        },
    })

    # ---- 页脚 ----
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"Trae每日AI+半导体+机器人新闻推送 | {NEWS_DATE} {NEWS_WEEK} | 数据来源：新华社、财联社、东方财富、CSDN、Reuters等公开媒体",
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

    # 1. 构建卡片
    print(f"\n[STEP 1] 构建 interactive 卡片 ...")
    card = build_card_json()
    card_str = json.dumps(card, ensure_ascii=False, indent=2)
    print(f"  卡片 JSON 长度: {len(card_str)} 字符")
    print(f"  新闻条目数: {len(NEWS_ITEMS)}")

    # 2. 发送消息
    print(f"\n[STEP 2] 发送消息到群聊 {CHAT_ID} ...")
    try:
        message_id = send_interactive_card(CHAT_ID, card)
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")
        sys.exit(1)

    # 3. 验证消息
    print(f"\n[STEP 3] 验证消息完整性 ...")
    try:
        verify_message(message_id)
        print(f"  消息验证通过！")
    except Exception as e:
        print(f"[WARN] 验证消息时出现问题: {e}")

    print(f"\n{'=' * 60}")
    print(f"  推送完成！message_id: {message_id}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
