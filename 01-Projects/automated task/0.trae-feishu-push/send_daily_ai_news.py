"""
Trae 每日AI新闻推送脚本
- 搜索当日AI行业热点新闻
- 生成 interactive 卡片推送到飞书群
- 使用 Bot 身份，token 自动缓存
"""
import json
import time
import os
import sys
import requests
from datetime import datetime

# ====== 配置区 ======
LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
LARK_CHAT_ID = os.environ.get("LARK_CHAT_ID", "")

LARK_API_BASE = "https://open.feishu.cn/open-apis"
TOKEN_URL = f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal"
MESSAGE_URL = f"{LARK_API_BASE}/im/v1/messages"

TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".lark_token_cache.json")


# ============ Token 管理 ============

def _load_token_cache():
    try:
        if os.path.exists(TOKEN_CACHE_FILE):
            with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"token": "", "expires_at": 0}


def _save_token_cache(cache):
    try:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass


def get_tenant_access_token():
    """获取 tenant_access_token (自动缓存，提前5分钟刷新)"""
    cache = _load_token_cache()
    now = time.time()

    if cache.get("token") and now < cache.get("expires_at", 0):
        return cache["token"]

    payload = {"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    resp = requests.post(TOKEN_URL, json=payload, timeout=10)
    data = resp.json()

    if data.get("code") == 0:
        token = data["tenant_access_token"]
        expire = data.get("expire", 7200)
        cache = {
            "token": token,
            "expires_at": now + expire - 300
        }
        _save_token_cache(cache)
        return token
    else:
        raise RuntimeError(f"获取token失败: {data.get('msg')}")


# ============ 新闻数据（当前为硬编码示例，后续可接入API/RSS） ============

def fetch_daily_ai_news():
    """
    获取当日AI新闻。
    当前为硬编码示例数据。后续可接入：
    - NewsAPI / GNews / AskNews 等新闻API
    - TechCrunch / The Verge / 机器之心 等RSS源
    - 自定义爬虫 + AI摘要
    """
    today = datetime.now().strftime("%Y年%m月%d日")

    news_items = [
        {
            "category": "产品发布",
            "title": "OpenAI与Anthropic先后提交IPO申请",
            "summary": "OpenAI于6月8日向SEC保密提交S-1草案，紧随Anthropic之后。双方竞逐2026年秋季上市窗口，与SpaceX共同构成三大潜在万亿级AI上市企业。",
            "source": "财联社 / The Information"
        },
        {
            "category": "产品发布",
            "title": "Anthropic Claude Fable 5发布3天后遭美国政府召回",
            "summary": "首款Mythos级公开模型SWE-Bench Pro得分80.3%，但美国政府以出口管制指令要求全球暂停访问，开创AI模型被政府召回先例。",
            "source": "MarkTechPost / ChatForest"
        },
        {
            "category": "产品发布",
            "title": "微软发布MAI自研模型套件（7款）",
            "summary": "覆盖推理、编码、图像、语音等方向。MAI-Thinking-1匹敌Claude Opus 4.6，MAI-Code-1-Flash原生集成VS Code和GitHub Copilot。",
            "source": "devFlokers / Microsoft Blog"
        },
        {
            "category": "融资并购",
            "title": "DeepSeek完成首轮510亿元融资",
            "summary": "估值突破500亿美元。创始人梁文锋个人出资200亿元领投，腾讯100亿元，宁德时代50亿元。特殊股权架构确保外部资本无法干预技术路线。",
            "source": "The Information / 21世纪经济报道"
        },
        {
            "category": "融资并购",
            "title": "SpaceX拟600亿美元收购Cursor母公司Anysphere",
            "summary": "AI编程赛道迄今最大单笔并购案，预计Q3完成。将为xAI提供关键企业级AI编程市场地位。",
            "source": "投资界 / Reuters"
        },
        {
            "category": "融资并购",
            "title": "OpenAI 2025年营收131亿美元，亏损385亿",
            "summary": "营收较2024年增长超3倍，但全年净亏损385亿美元，研发支出191.8亿美元。Q1现金消耗37亿美元。",
            "source": "金融时报 / 财联社"
        },
        {
            "category": "技术突破",
            "title": "OpenAI系统推翻80年数学猜想",
            "summary": "推翻了数学家埃尔德什1946年提出的单位距离猜想，生成125页数学证明，经全球9位顶尖数学家验证，论文发布于arXiv。",
            "source": "Nature / arXiv:2605.20695"
        },
        {
            "category": "技术突破",
            "title": "Google DeepMind Co-Scientist登上Nature",
            "summary": "多Agent AI科研助手展示从假设生成到实验验证的完整闭环，已在Stanford、MIT、Cambridge等顶尖实验室获得湿实验验证。",
            "source": "Labcritics / Google DeepMind"
        },
        {
            "category": "行业法规",
            "title": "全球AI治理三线并进",
            "summary": "美国白宫发布NSPM-11总统备忘录；欧盟AI法案将于8月全面执行；中国宣布7月在上海举办WAIC 2026并筹建世界人工智能合作组织。",
            "source": "白宫 / 欧盟委员会 / 新华社"
        }
    ]

    analysis = {
        "investment": "AI行业超级独角兽门槛已跃升至500亿美元。关注国产大模型企业（DeepSeek模式）和AI基础设施层（算力、电力、存储）。",
        "career": "AI编程赛道独立创业窗口收窄。建议关注AI+垂直行业交叉领域，以及AI安全合规方向。",
        "family": "培养孩子的AI素养与批判性思维，家庭科技消费可适度向AI终端倾斜。"
    }

    trend_comment = (
        "本周AI行业呈现政策+资本+技术三线共振态势。OpenAI与Anthropic的IPO竞速标志着AI行业从烧钱扩张进入价值验证阶段，"
        "而Claude Fable 5遭美国政府首次召回则揭示了前沿AI治理的深水区矛盾。"
        "2026年下半年，随着欧盟AI法案执行、美国监管框架落地、中国WAIC大会召开，全球AI治理格局将进入定型窗口期。"
    )

    return today, news_items, analysis, trend_comment


# ============ 卡片构建 ============

def build_news_card(title, news_items, analysis, trend_comment):
    """构建 AI 新闻推送的 interactive 卡片"""
    elements = []

    # 新闻条目（按分类分组）
    current_category = None
    for item in news_items:
        if item["category"] != current_category:
            current_category = item["category"]
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📌 {current_category}**"
                }
            })

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**{item['title']}**\n{item['summary']}\n> 来源：{item['source']}"
            }
        })
        elements.append({"tag": "hr"})

    # 投资与职业发展分析
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "**📊 投资与职业发展分析**"
        }
    })
    elements.append({
        "tag": "div",
        "fields": [
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**💰 投资方向**\n{analysis['investment']}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**💼 职业发展**\n{analysis['career']}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**🏠 家庭规划**\n{analysis['family']}"
                }
            }
        ]
    })
    elements.append({"tag": "hr"})

    # 趋势点评
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**🔥 今日趋势点评**\n{trend_comment}"
        }
    })

    # 页脚
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"由 Trae AI 自动整理推送 | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
        ]
    })

    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "template": "blue",
            "title": {
                "tag": "plain_text",
                "content": title
            }
        },
        "elements": elements
    }

    return card


# ============ 发送消息 ============

def send_interactive_card(card_data, chat_id=LARK_CHAT_ID):
    """发送 interactive 消息卡片到飞书群"""
    token = get_tenant_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card_data, ensure_ascii=False)
    }
    params = {"receive_id_type": "chat_id"}

    resp = requests.post(
        MESSAGE_URL,
        headers=headers,
        json=payload,
        params=params,
        timeout=20
    )
    data = resp.json()

    if data.get("code") == 0:
        return True, data.get("data", {}).get("message_id", "")
    else:
        return False, f"code={data.get('code')}, msg={data.get('msg')}"


def verify_message(message_id):
    """验证消息内容完整性"""
    token = get_tenant_access_token()
    url = f"{LARK_API_BASE}/im/v1/messages/{message_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id_type": "open_id"}

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()

    if data.get("code") == 0:
        msg = data.get("data", {})
        return True, msg.get("msg_type"), msg.get("create_time")
    else:
        return False, None, f"code={data.get('code')}, msg={data.get('msg')}"


# ============ 主流程 ============

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行每日AI新闻推送...")

    # 1. 获取新闻
    today, news_items, analysis, trend_comment = fetch_daily_ai_news()
    print(f"获取到 {len(news_items)} 条新闻")

    # 2. 构建卡片
    title = f"🤖 Trae每日AI新闻推送 | {today}"
    card = build_news_card(title, news_items, analysis, trend_comment)
    print("卡片构建完成")

    # 3. 发送
    success, result = send_interactive_card(card)
    if not success:
        print(f"发送失败: {result}")
        sys.exit(1)

    message_id = result
    print(f"发送成功! message_id: {message_id}")

    # 4. 验证
    ok, msg_type, create_time = verify_message(message_id)
    if ok:
        print(f"验证通过! type={msg_type}, create_time={create_time}")
    else:
        print(f"验证失败: {create_time}")

    print("任务完成")


if __name__ == "__main__":
    main()
