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
NEWS_DATE = "2026年6月28日"
NEWS_WEEK = "6月最后一周"

# ---- 新闻条目 ----
NEWS_ITEMS = [
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "智元机器人第15000台精灵G2量产下线，半年三次跨越刷新全球纪录",
        "summary": "6月28日，智元机器人宣布第15000台通用具身机器人精灵G2正式量产下线，现场交付至龙旗科技。从2025年12月第5000台到2026年6月第15000台仅用时半年，月产能从约364台跃升至约1666台。精灵G2搭载英伟达Jetson Thor芯片、19自由度灵巧手和3D触觉感知，标志工业级人形机器人从定制化走向标准化量产，数据飞轮正式启动。",
        "source": "财联社 / 科创板日报 / 界面新闻",
    },
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "京东刘强东：快递未来全部由机器人送，70万快递员将转岗修机器人",
        "summary": "京东集团创始人刘强东在2026年APEC工商领导人中国论坛上表示，快递终将实现全部机器人送货，未来不再需要快递员。京东内部已启动\"涅槃计划\"，拟将70万配送员工转岗至机器人维修、调度等新岗位，并推进全员再培训。机器人替代劳动力正从概念走向组织重构。",
        "source": "FT中文网 / 今日头条",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "央视财经实地报道：800G以上光模块出口暴涨百倍，国产占全球70%份额",
        "summary": "6月27日央视财经《朝闻天下》奔赴武汉光谷实地报道，华工科技旗下华工正源800G及以上高端光模块2026年开年至今出口同比暴涨超100倍，产线24小时三班倒仍无法覆盖订单。国产光模块占全球70%以上市场份额，中际旭创1.6T产品市占率50%-70%，头部企业订单排产至2028年，AI算力硬件出海成为外贸升级核心引擎。",
        "source": "央视财经 / 东方财富网",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "SK海力士与英伟达建立多年期合作，联合研发下一代AI内存",
        "summary": "SK海力士宣布与英伟达建立多年期技术合作伙伴关系，围绕全球AI工厂建设所需的下一代内存展开联合研发。存储芯片景气周期持续延续，二季度合约价预计环比仍有60%增幅。HBM作为AI算力核心存储瓶颈，正成为半导体产业链中确定性最高的增长赛道。",
        "source": "每周热点汇总 / 科技早报",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "OpenAI限制GPT-5.6初期发布，前沿模型进入国家安全审查阶段",
        "summary": "据Business Insider报道，OpenAI因美国政府要求将GPT-5.6系列先限量开放给经审核合作方。同时Anthropic的Mythos 5获部分模型限制豁免，可向关键基础设施机构有限开放，但更强的Fable 5仍冻结。前沿模型发布正进入\"国家安全审查+分阶段开放\"的新阶段，AI安全评测、模型合规、企业私有化部署将升温。",
        "source": "Business Insider / TechRadar",
    },
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "AI游戏初创General Intuition完成3.2亿美元A轮，资本重押AI原生应用层",
        "summary": "AI游戏初创公司General Intuition完成3.2亿美元A轮融资，表明资本并未只押注芯片和云，也开始重押\"AI原生娱乐/内容形态\"。同时TechCrunch报道称投资人对普通\"AI+SaaS包装\"更加谨慎，真正壁垒来自行业数据、流程闭环和结果交付，垂直行业Agent与结果型SaaS更受青睐。",
        "source": "Axios / TechCrunch",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "Anthropic指控阿里相关方蒸馏Claude，模型能力成知识产权博弈焦点",
        "summary": "据Reuters报道，Anthropic指控与阿里/Qwen相关操作者通过大量虚假账号提取Claude能力。同日论文《The Shift to Agentic AI: Evidence from Codex》发布，给出从问答式LLM向代理式AI迁移的实证证据。模型能力本身正在成为知识产权与国家竞争焦点，反蒸馏、API风控、模型水印、数据审计将成为大模型基础设施。",
        "source": "Reuters / arXiv",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "中国商务部等八部门发布\"AI+消费\"17项措施，推动AI进千家万户",
        "summary": "商务部等八部门发布《关于加快\"人工智能+消费\"发展的实施意见》，围绕商品消费、服务消费等五方面提出17项举措，明确布局人形机器人消费新赛道，推动AI手机、智能家居、智能网联汽车等终端普及。同期中国主要交易所调整指数增加AI和半导体公司权重，资本市场用指数机制强化\"硬科技主线\"。",
        "source": "财联社 / 财新 / 商务部",
    },
]

# ---- 投资与职业发展分析 ----
ANALYSIS = {
    "investment": (
        "【AI算力】OpenAI限制GPT-5.6发布意味着前沿模型进入监管分级，国产大模型窗口期扩大。美股AI交易降温促使资本重新评估投入回报周期，但AI基础设施需求仍强，HBM、存储、散热、电力仍是主线。"
        "【半导体】央视财经证实800G光模块出口暴涨百倍，国产光模块占全球70%份额是算力链中国产话语权最强环节，中际旭创、华工科技订单排至2028年。SK海力士与英伟达联手研发下一代AI内存，存储芯片二季度合约价环比增60%，景气周期延续。"
        "【机器人】智元15000台下线标志量产拐点，数据飞轮启动，关注优必选等具身智能标的。京东70万快递员转岗信号推动服务机器人商业化预期升温，A股指数增加AI半导体权重将带来长期资金流入。"
    ),
    "career": (
        "【AI方向】论文实证Agentic AI迁移趋势，从问答式LLM向代理式AI转型已成定局。端侧AI/MCU开发者应关注Agent工作流编排、模型蒸馏防护与端侧推理优化，掌握多模态大模型工程化能力者薪酬溢价显著。"
        "【半导体方向】800G/1.6T高速光模块设计、HBM封装工艺、AI内存研发成为人才争夺焦点。国产光模块全产业链自研能力（如华工科技单波200G硅光芯片）突破带来芯片设计岗位需求，具备光通信与半导体交叉经验者稀缺度上升。"
        "【机器人方向】智元精灵G2搭载Jetson Thor+19自由度灵巧手，具身智能数据治理、真机数据采集、机器人调度系统成为新赛道。嵌入式开发者在MCU/RTOS/驱动层面的经验可直接迁移至机器人底层控制与实时通信，职业转型路径清晰。"
    ),
    "family": (
        "【消费决策】\"AI+消费\"17项措施推动AI家电、智能家居、人形机器人进入家庭场景，关注AI家电以旧换新补贴政策与AI手机换机潮，近期购置智能终端可享政策红利。"
        "【育儿教育】AI游戏融资3.2亿美元说明AI原生娱乐形态兴起，青少年可适度接触AI创作工具培养AI素养。京东配送机器人替代趋势提醒关注物流行业就业变化，可前瞻引导孩子关注机器人维修/调度等新兴职业技能方向。"
        "【家庭健康】极端热浪席卷欧洲、中国空调海外抢购现象提示关注家庭温控设备升级。AI+消费政策覆盖智能网联汽车，北京家庭购车可关注搭载AI辅助驾驶的新能源车型补贴动态。"
    ),
}

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年6月28日，AI、半导体、机器人三大赛道同步迎来标志性事件。"
    "①机器人方向：智元第15000台精灵G2量产下线，半年三次跨越标志中国人形机器人从概念验证迈入大规模商用，数据飞轮正式启动；京东70万快递员转岗信号推动服务机器人从概念走向组织重构。"
    "②半导体方向：央视财经证实800G光模块出口暴涨百倍，国产光模块占全球70%份额成为算力链最强环节，SK海力士与英伟达联手研发下一代AI内存延续存储景气周期。"
    "③AI方向：OpenAI限制GPT-5.6发布、Anthropic指控阿里蒸馏Claude，前沿模型进入国家安全审查与知识产权博弈新阶段，中国\"AI+消费\"17项措施推动AI从模型研发转向消费场景落地。"
    "全球科技产业进入\"监管分级+硬件出海+具身商用\"三重叠加新周期。"
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
