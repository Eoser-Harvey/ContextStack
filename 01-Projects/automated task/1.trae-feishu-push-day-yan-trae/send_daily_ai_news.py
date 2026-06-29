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
NEWS_DATE = "2026年6月29日"
NEWS_WEEK = "6月最后一周"

# ---- 新闻条目 ----
NEWS_ITEMS = [
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "DeepSeek完成约500亿元首轮融资估值超500亿美元，全员扩编一倍",
        "summary": "6月25日，DeepSeek完成首轮外部融资约500亿元（约74亿美元），估值突破500亿美元，成为中国AI行业迄今规模最大单轮融资。同日发布成立以来最大规模招聘公告，计划将全部门人员规模至少扩充一倍，覆盖从底层算力到前沿Agent产品的完整技术链条，开放33+岗位，不到一天收到超万份简历。资本正用真金白银投票中国AGI赛道。",
        "source": "天眼查 / 36氪 / 今日头条",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "功率半导体再启涨价潮：AI算力集群功耗激增驱动，扬杰科技全系列涨10-15%",
        "summary": "6月29日，功率半导体行业再掀涨价潮。扬杰科技、宏微科技、华润微、士兰微等国内厂商年内已密集完成两轮调价，海外英飞凌、意法半导体同步跟进。AI算力集群功耗激增是核心驱动因素，功率半导体正式接棒存储芯片成为AI时代新增长引擎。多位业内人士判断本轮涨价周期仍将持续，部分厂商订单排至2027年。",
        "source": "东方财富网 / 今日头条",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "玻璃基板大规模导入AI芯片封装，英特尔量产台积电三星加速，上游材料变局",
        "summary": "6月29日AI科技早报确认，玻璃基板开始大规模导入AI芯片封装，解决传统有机基板散热与布线瓶颈。英特尔已实现量产，台积电、三星加速产线建设。2026年推理算力占比首次突破66%，英伟达Vera Rubin芯片下半年出货性能提升3.3倍，上游材料变革成为算力硬件关键增量赛道。同时磷化铟(InP)板块二季度持续走强，量价齐升。",
        "source": "AI科技早报 / 四大证券报",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "微软推出Scout企业级Autopilot Agent，AI助手从Copilot进化为Autopilot",
        "summary": "6月29日，微软正式推出Scout，一款始终在线的企业级Autopilot Agent，能独立监控、决策和执行任务，无需人类持续盯着看。从Copilot（副驾驶）到Autopilot（自动驾驶），AI助手正从辅助工具进化为可独立运行的AI员工。同期诺基亚与英伟达达成10亿美元战略合作，联合开发AI原生6G网络，将AI处理器集成至5G设备，边缘计算+AI通信融合加速。",
        "source": "AI科技日报 / 新浪财经",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "谷歌对Meta实施Gemini算力限购，硅谷算力争夺战白热化",
        "summary": "6月29日《金融时报》独家报道，谷歌自3月起正式向Meta下达Gemini算力上限通知，对Meta调用Gemini大模型接口设置每周封顶额度，即便加价也无法追加资源。谷歌云一季度营收突破200亿美元但积压订单庞大，优先保障自研业务算力供给。Meta被迫下发算力节约通知，多款AI产品上线计划延后。算力资源正从商品变为战略武器。",
        "source": "Financial Times / AI科技早报",
    },
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "无界动力完成超2亿美元天使轮融资，具身智能上半年融资288起超460亿元",
        "summary": "6月26日，北京通用具身智能机器人公司无界动力宣布完成超2亿美元天使轮融资，京东关联基金、红杉、高瓴等头部机构持续加注，Pre-A轮近2亿美元也接近完成。IT桔子统计显示，2026年上半年国内具身智能及机器人领域共发生288起融资事件，涉及226家企业，披露融资额超460亿元。投资逻辑已从\"看团队\"转向\"看量产验证\"，行业进入淘汰赛阶段。",
        "source": "36氪 / IT桔子 / 今日头条",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "美国首次在AI模型发布前介入用户准入审批，苏州发布\"AI+\"行动方案目标4000亿",
        "summary": "6月29日，美国政府在OpenAI GPT-5.6发布前宣布将审批用户准入资格，这是美国首次将出口管制思路搬至AI领域。同日苏州市发布\"人工智能+\"行动方案，目标2026年底集聚AI企业超3500家、核心产业营收超4000亿元。首届全球太空算力大会在北京开幕，配套50亿产业资金，发布天地一体化算力路线图。中国城市AI产业政策竞争进入白热化阶段。",
        "source": "AI科技日报 / 财联社 / 苏州市政府",
    },
]

# ---- 投资与职业发展分析 ----
ANALYSIS = {
    "investment": (
        "【AI算力】DeepSeek融资500亿估值500亿美元，中国AGI赛道资本热度不减。但谷歌对Meta限购算力揭示算力资源正从商品变为战略武器，英伟达Vera Rubin下半年出货性能提升3.3倍，推理算力占比破66%，算力基础设施投资确定性仍高。"
        "【半导体】功率半导体年内两轮涨价，AI算力集群功耗激增是核心驱动，扬杰科技、华润微等订单排至2027年。玻璃基板导入AI芯片封装开启上游材料变局，英特尔量产台积电三星加速，磷化铟(InP)板块二季度量价齐升。半导体产业链从存储到功率到材料全面开花。"
        "【机器人】无界动力天使轮超2亿美元，上半年具身智能融资288起超460亿元，但投资逻辑已转向量产验证。关注优必选等具身智能标的，以及即将港股IPO的普渡机器人。具身智能赛道进入淘汰赛，有量产能力的头部企业将享受估值溢价。"
    ),
    "career": (
        "【AI方向】微软Scout从Copilot到Autopilot标志着Agent开发成为AI工程师核心技能。DeepSeek全员扩编一倍、33+岗位覆盖底层算力到Agent产品，端侧AI/MCU开发者应关注Agent工作流编排、模型推理优化与边缘部署三大方向，多模态Agent工程化能力薪酬溢价显著。"
        "【半导体方向】功率半导体涨价潮带动国产替代芯片设计、封装工艺人才需求激增。玻璃基板封装、磷化铟(InP)材料、CPO光电共封装成为新稀缺岗位。诺基亚×英伟达6G合作催生通信+AI交叉人才，具备嵌入式+通信双重背景者转型优势明显。"
        "【机器人方向】无界动力等具身智能公司密集融资扩招，机器人底层控制（MCU/RTOS/驱动）、传感器融合、实时通信岗位需求旺盛。嵌入式开发者9年经验可直接迁移至机器人运动控制与实时系统，职业转型路径清晰且薪酬天花板更高。"
    ),
    "family": (
        "【消费决策】功率半导体涨价+AI算力功耗激增，家庭电费支出可能上升，关注节能家电升级与智能家居能耗管理方案。苏州AI行动方案目标4000亿、北京太空算力大会50亿产业资金，一线城市AI产业集聚推高周边生活成本，建议提前规划家庭支出节奏。"
        "【育儿教育】DeepSeek扩招万人投递、微软Autopilot Agent上岗，AI替代效应加速。建议引导孩子学习AI工具使用（如AI编程助手、创作工具），培养AI素养而非单纯应试。Agent开发方向是未来5年高薪赛道，可前瞻规划孩子STEM教育路径。"
        "【家庭健康】AI算力数据中心高能耗引发全球300+地区新建限制，能源转型加速。北京家庭可关注光伏储能、智能温控等绿色家居方案，享受政策补贴同时降低长期用电成本。诺基亚×英伟达6G合作预示下一代通信网络将更深度融入家庭生活，关注智能家居互联标准演进。"
    ),
}

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年6月29日，AI、半导体、机器人三大赛道呈现\"资本热、算力紧、量产实\"的三重特征。"
    "①AI方向：DeepSeek融资500亿估值500亿美元+全员扩编，中国AGI资本热度不减；但谷歌对Meta限购算力揭示算力正从商品变为战略武器，微软Scout从Copilot迈向Autopilot标志Agent时代正式开启。"
    "②半导体方向：功率半导体年内两轮涨价+玻璃基板导入AI芯片封装，半导体产业链从存储到功率到材料全面开花，国产替代+上游材料变革双主线并行。"
    "③机器人方向：无界动力天使轮超2亿美元+上半年融资288起超460亿元，具身智能投资逻辑从\"看团队\"转向\"看量产\"，行业进入淘汰赛阶段。"
    "全球科技产业进入\"算力博弈+政策竞速+量产淘汰\"三重叠加新周期。"
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
