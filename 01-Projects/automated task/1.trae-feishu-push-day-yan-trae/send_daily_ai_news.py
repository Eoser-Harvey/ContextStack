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
NEWS_DATE = "2026年6月24日"
NEWS_WEEK = "6月第四周"

# ---- 新闻条目 ----
NEWS_ITEMS = [
    # ========== 融资/并购 ==========
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "SpaceX以600亿美元全股票收购AI编程工具Cursor母公司Anysphere",
        "summary": "刚登陆纳斯达克、市值冲破2万亿美元的SpaceX，上市第四天即宣布以600亿美元全股票交易收购AI编程顶流Cursor母公司Anysphere，零现金支出。这是SpaceX首笔重大并购，标志其正式进军AI编程领域，补齐软件生态短板。",
        "source": "今日头条 / 腾讯新闻",
    },
    {
        "category": "\U0001f4b0 融资/并购",
        "title": "高通接近以40亿美元估值收购AI芯片初创公司Modular",
        "summary": "高通被曝接近以约40亿美元估值收购AI芯片初创公司Modular，进一步加码端侧AI算力布局。Modular专注于为边缘设备提供高效AI推理芯片方案，与高通骁龙平台形成战略协同。",
        "source": "华尔街见闻 / 搜狐科技",
    },
    # ========== 产品发布 ==========
    {
        "category": "\U0001f4e6 产品发布",
        "title": "字节跳动发布豆包大模型2.1 Pro：成本暴砍80%，编程追平Claude Opus 4.7",
        "summary": "火山引擎FORCE原动力大会推出豆包2.1 Pro旗舰版，代码交付、长程Agent任务及多模态理解能力达生产级质变。截至6月豆包模型token调用量同比增超10倍，成本降低80%，面向企业复杂研发场景全面开放。",
        "source": "贝壳财经 / 搜狐科技",
    },
    {
        "category": "\U0001f4e6 产品发布",
        "title": "英伟达发布Halos for Robotics：业界首个全栈物理AI安全系统",
        "summary": "英伟达推出Halos for Robotics安全系统，将自动驾驶安全架构扩展至机器人和具身智能领域，Agilebot率先接入。该系统覆盖感知、决策、执行全链路安全验证，为具身智能规模化落地提供安全底座。",
        "source": "科技早报 / 今日头条",
    },
    # ========== 技术突破 ==========
    {
        "category": "\U0001f52c 技术突破",
        "title": "中国\"灵晟\"超算问鼎全球TOP500，时隔9年再夺世界第一",
        "summary": "德国汉堡ISC2026大会发布全球超算TOP500榜单，国家超级计算深圳中心研制的\"灵晟\"以2.19 EFlops持续双精度浮点性能登顶，刷新世界算力新高度。这是全国产自主研制超算时隔9年再次排名全球第一。",
        "source": "中新网 / CNMO科技",
    },
    {
        "category": "\U0001f52c 技术突破",
        "title": "CPO量产未推迟，光模块上游磷化铟激光芯片成核心瓶颈",
        "summary": "据21财经从接近英伟达业内人士处印证，产业端并不存在CPO量产推迟。真正制约高速光通信的是上游磷化铟激光芯片，200G及以上速率EML激光器高度依赖海外供应，产线扩产周期漫长成最短板。",
        "source": "21财经 / 码农财经",
    },
    # ========== 行业法规 ==========
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "工信部加快编制智能网联新能源汽车\"十五五\"规划",
        "summary": "工信部明确将聚焦新一代动力电池、车用芯片、操作系统及自动驾驶技术攻关与产业化。规划将推动车规级芯片国产化替代加速，为半导体和AI产业打开万亿级车联网市场。",
        "source": "工信部 / 科技早报",
    },
    {
        "category": "\u2696\ufe0f 行业法规",
        "title": "刘国中调研江苏：培育发展脑机接口未来产业",
        "summary": "国务院副总理刘国中在江苏调研时强调，打造生物医药新兴支柱产业，培育发展脑机接口未来产业，深化多学科交叉融合，加快关键核心技术攻关。\"十五五\"规划已将脑机接口列为未来产业重点方向。",
        "source": "政府公开信息 / 搜狐财经",
    },
    # ========== 半导体/芯片 ==========
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "芯联集成签署200亿元增资协议，投向12英寸车规级芯片制造",
        "summary": "芯联集成签署增资协议，计划总投资约200亿元用于12英寸车规级数模混合芯片制造项目。同时兴森科技拟定增募资不超39亿元用于高阶mSAP基板智能制造，半导体国产替代进入资本密集投入期。",
        "source": "上市公司公告 / 东方财富网",
    },
    {
        "category": "\U0001f50c 半导体/芯片",
        "title": "凌川科技A+轮获数亿元融资：快手参投，全国产3D堆叠芯片已流片",
        "summary": "自研视频AI算力芯片企业凌川科技（灵川）完成A+轮数亿元融资，快手参投。其SL200累计出货近10万颗，全国产3D堆叠芯片已于4月流片。国产AI推理芯片在性能接近H200的同时进入快速放量阶段。",
        "source": "科技早报 / 投资界",
    },
    # ========== 机器人/具身智能 ==========
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "特斯拉Optimus德州工厂动工，规划年产能最高1000万台",
        "summary": "特斯拉得州超级工厂专属厂房钢结构落成，规划年产能最高1000万台Optimus人形机器人，同步布局下一代AI芯片晶圆厂，2027年夏启动大规模量产。供应商已开始备货，Optimus 3量产进入倒计时。",
        "source": "科技早报 / 华尔街见闻",
    },
    {
        "category": "\U0001f916 机器人/具身智能",
        "title": "日本公布物理AI专项投入10.5万亿日元，布局工业自动化与无人运输",
        "summary": "日本政府公布至2040年物理AI（具身感知决策操作）专项投入10.5万亿日元，重点布局工业自动化与无人运输领域，缓解劳动力萎缩。全球主要经济体正加速具身智能国家战略投入。",
        "source": "科技早报 / 日本经济产业省",
    },
]

# ---- 投资与职业发展分析 ----
ANALYSIS = {
    "investment": (
        "【AI算力】豆包2.1 Pro成本暴砍80%标志国产大模型进入性价比决胜阶段，推理侧国产芯片（凌川、华为昇腾）迎来放量窗口。"
        "【半导体】芯联集成200亿车规级芯片项目、兴森科技39亿高阶基板定增，国产替代从设计向制造/封测/材料全链条渗透。"
        "【机器人】特斯拉Optimus千台级产能规划落地，日本10.5万亿日元物理AI投入，具身智能从概念验证迈向规模化产业投资。"
    ),
    "career": (
        "【AI方向】Agentic Coding成为强共识，豆包2.1 Pro编程追平Claude标志国产模型能力质变。AI应用开发、模型微调、Agent架构师岗位需求激增，掌握多模态大模型工程化能力者薪酬溢价显著。"
        "【半导体方向】车规级芯片、高阶封装基板、光模块上游激光芯片成为人才争夺焦点，具备12英寸晶圆厂工艺经验者稀缺度上升。"
        "【机器人方向】物理AI安全系统、具身智能真机数据治理成为新赛道，机械/电子/算法交叉背景人才持续抢手。"
    ),
    "family": (
        "AI编程工具普及加速\"人人能编程\"时代到来，建议青少年尽早接触AI辅助编程与逻辑思维训练。"
        "脑机接口纳入\"十五五\"未来产业，关注相关前沿科普与交叉学科教育机会，为下一代布局前沿科技认知。"
    ),
}

# ---- 今日趋势点评 ----
TREND_COMMENTARY = (
    "2026年6月24日，AI、半导体、机器人三大赛道同步迎来标志性事件。"
    "①AI方向：SpaceX 600亿美元收购Cursor、豆包2.1 Pro成本暴砍80%，Agentic Coding从共识走向巨头卡位战，国产大模型性价比优势开始兑现；"
    "②半导体方向：灵晟超算时隔9年登顶TOP500彰显国产算力自主可控突破，芯联集成200亿车规级项目标志半导体国产替代进入资本密集期；"
    "③机器人方向：特斯拉Optimus千台级产能规划与日本10.5万亿日元物理AI投入共振，具身智能正从实验室走向工厂和社会的规模化部署。"
    "全球科技产业进入\"算力自主+Agent普及+具身落地\"三重叠加的新周期。"
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
                "content": f"Trae每日AI+半导体+机器人新闻推送 | {NEWS_DATE} {NEWS_WEEK} | 数据来源：今日头条、华尔街见闻、东方财富网、36氪、中新网等公开媒体",
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
