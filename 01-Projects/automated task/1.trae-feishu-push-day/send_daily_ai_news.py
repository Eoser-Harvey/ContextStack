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
NEWS_DATE = "2026年6月22日"
NEWS_WEEK = "6月第四周"

# ---- 新闻条目 ----
NEWS_ITEMS = [
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "具身智能赛道融资狂飙：上半年累计超460亿元，头部效应显著",
        "summary": "2026年上半年，国内具身智能赛道累计融资超460亿元，其中约330亿元（七成）流向仅20家头部企业，塔尖5家公司吞噬37%资金约171亿元。大晓机器人6月15日完成天使+轮融资，2026年上半年累计融资数亿美元，15家机构参投。",
        "source": "投资界 / 36氪",
    },
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "一周60亿热钱涌入具身智能：15家企业集中获投",
        "summary": "6月第二周，国内具身智能赛道15家相关企业在一周内斩获融资，披露总额超过60亿元人民币。资本密集押注脑机接口与具身智能交叉赛道，人形机器人产业基金规模已突破2000亿元。",
        "source": "36氪 / 投资界",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "AMD发布锐龙AI Halo：全球最小AI开发系统，本地跑2000亿参数大模型",
        "summary": "CES 2026大会上，AMD苏姿丰揭晓颠覆性产品——锐龙AI Halo(Ryzen AI Halo)，被官方定义为'全球最小AI开发系统'的迷你主机，彻底重构算力门槛，个人AI开发时代正式到来。",
        "source": "CES 2026 / AMD官方",
    },
    {
        "category": "\U0001f4e6 产品发布",
        "title": "阿里发布千问具身智能大模型Qwen-Robot系列，推动AI走向物理世界",
        "summary": "阿里巴巴发布千问具身智能大模型Qwen-Robot系列，专为机器人场景优化，支持多模态感知与物理世界交互，标志大模型正从虚拟对话向实体智能加速进化。",
        "source": "阿里官方 / 机器之心",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "Anthropic计划部署AMD Instinct MI450加速器，AMD再获关键客户突破",
        "summary": "Anthropic计划在下一代AI基础设施中部署AMD Instinct MI450加速器，这是AMD继OpenAI、Meta之后又一关键客户突破。MI450基于CDNA 5架构，计算性能达40 PFLOP（FP4）。",
        "source": "算力日报 / AMD",
    },
    {
        "category": "\U0001f52c 技术突破",
        "title": "2026年AI技术突破：具身智能产业化、大模型任务化、算力自主化三大主线",
        "summary": "2026年AI技术突破集中在具身智能产业化、大模型任务化、算力自主化及垂直领域深度渗透。AI正从虚拟对话工具进化成能理解、改造物理世界的智能伙伴，价值在工厂、医疗、出行等场景加速兑现。",
        "source": "Google DeepMind / 机器之心",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "工信部印发《'人工智能+信息通信'创新发展实施意见(2026-2028年)》",
        "summary": "6月10日，工信部印发《'人工智能+信息通信'创新发展实施意见(2026-2028年)》，推动人工智能与信息通信融合创新发展，明确将通用大模型、行业垂直大模型、自主AI智能体列为核心扶持赛道。",
        "source": "工信部 / 搜狐",
    },
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "科创板第五套标准扩围至AI大模型行业，'六小虎'或加速上市回流",
        "summary": "科创板第五套标准适用范围扩大至人工智能大模型行业，预计将吸引AI大模型'六小虎'上市或回流A股。政策一放一严，AI智能体开启2026超级主升赛道，配套研发补贴、算力倾斜、产学研协同举措落地。",
        "source": "人民财讯 / 新华网",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "中国集成电路规模冲刺2万亿，'十五五'开局迎来关键突破",
        "summary": "2026年'十五五'开局，中国集成电路产业迎来关键突破。半导体市场规模高速扩张，国产化率持续提升，AI算力需求拉动全产业链爆发。政策、资本、技术多重驱动下，万亿级市场红利释放。",
        "source": "证券时报 / 爱集微",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "车企竞速布局具身智能新赛道：自研芯片与大模型集中落地",
        "summary": "国内汽车产业迎来结构性变革，小鹏、蔚来、理想等车企集体放弃外购供应链模式，加码自研芯片与车载大模型。英伟达Blackwell、AMD新一代GPU、国产云端AI加速卡全部采用芯粒架构，国产先进封装产线实现批量供货。",
        "source": "四大证券报 / 科创板日报",
    },
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "第四届链博会开幕：自动驾驶、算力基建、AI等成核心议题",
        "summary": "6月22日，第四届中国国际供应链促进博览会在北京开幕，聚焦全球供应链合作。自动驾驶、新能源、算力基建、AI等多个领域成为核心议题，标志中国科技产业链正加速融入全球创新网络。",
        "source": "腾讯新闻 / 链博会官方",
    },
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "2026人形机器人产业创新大会召开，聚力协同创新加速产业化",
        "summary": "2026人形机器人产业创新大会近日召开，聚焦聚力协同创新。张江具身智能供应链大会同期开幕，80余家企业围绕人形机器人商业化落地、灵巧手产业化、精密减速器国产替代等议题深入探讨。",
        "source": "浦东发布 / 腾讯新闻",
    },
]

# ---- 投资与职业发展分析 ----
ANALYSIS = {
    "investment": (
        "【AI算力】AMD MI450获Anthropic部署，锐龙AI Halo颠覆个人开发门槛，算力自主化与边缘AI是2026年最强主线。关注国产GPU适配、数据中心液冷、算力租赁标的。"
        "【半导体】中国集成电路规模冲刺2万亿，车企自研芯片与大模型集中落地，芯粒架构与先进封装国产替代加速，设备与材料环节最受益。"
        "【机器人】具身智能上半年融资460亿，头部集中效应显著。精密减速器、力矩传感器、灵巧手等核心零部件国产替代进入兑现窗口，产业链最确定性方向。"
    ),
    "career": (
        "【AI方向】Agent开发（多智能体协作、工具调用）、AI+行业（出行、医疗、制造）复合型岗位薪酬涨幅超50%。掌握LangChain/SwarmFlow等框架，具备大模型微调与部署能力者最抢手。"
        "【半导体方向】国产芯片设备、先进封装、算力架构设计人才需求激增，半导体设备工程师薪资涨幅领先传统IC设计30%以上。"
        "【机器人方向】具身智能'大脑(AI)+小脑(运控)+身体(本体)'三栖人才极度稀缺，机械/电子/算法交叉背景年薪普遍突破80万。"
    ),
    "family": (
        "AI内容标识新规全面落地，家长应引导孩子识别AI生成内容，培养数字媒体素养。"
        "人形机器人正从实验室走向家庭场景，建议关注青少年编程与机器人教育的早期培养，布局AI时代的核心素养正当时。"
    ),
}

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年6月22日，AI产业进入'政策+资本+技术'三浪叠加的质变时刻。"
    "①AI算力层面：AMD MI450获Anthropic部署，锐龙AI Halo让个人本地跑2000亿参数大模型成为可能，算力民主化浪潮加速，英伟达垄断格局面临实质性挑战；"
    "②半导体层面：中国集成电路规模冲刺2万亿，车企自研芯片与大模型集中落地，芯粒架构与先进封装成为国产替代核心突破口；"
    "③具身智能层面：上半年融资460亿，一周60亿热钱涌入，头部效应显著但产业化路径逐渐清晰。"
    "未来30天，WAIC 2026（7月17日）超300款AI新品首发将是关键观测节点，具身智能产业链亦将迎来密集催化。"
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
                "content": f"Trae每日AI+半导体+机器人新闻推送 | {NEWS_DATE} {NEWS_WEEK} | 数据来源：新华社、财联社、36氪、投资界、CSDN等公开媒体",
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
