"""
飞书群推送模块 — 直接调用飞书 Open API (Bot 身份)
调用链: Python → HTTP POST → 飞书 Open API → 飞书群
"""
import json
import time
import os
import requests

# ====== 配置区 ======
LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
LARK_CHAT_ID = os.environ.get("LARK_CHAT_ID", "")

LARK_API_BASE = "https://open.feishu.cn/open-apis"
TOKEN_URL = f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal"
MESSAGE_URL = f"{LARK_API_BASE}/im/v1/messages"

# token 缓存文件（跨进程复用）
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".lark_token_cache.json")


def _load_token_cache():
    """从文件加载 token 缓存"""
    try:
        if os.path.exists(TOKEN_CACHE_FILE):
            with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"token": "", "expires_at": 0}


def _save_token_cache(cache):
    """保存 token 缓存到文件"""
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
            "expires_at": now + expire - 300  # 提前5分钟刷新
        }
        _save_token_cache(cache)
        return token
    else:
        raise RuntimeError(f"获取token失败: {data.get('msg')}")


def send_interactive_card_to_lark(card_data, chat_id=LARK_CHAT_ID):
    """发送 interactive 消息卡片到飞书群 (Bot 身份)"""
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


def build_news_card(title, news_items, analysis, trend_comment):
    """
    构建 AI 新闻推送的 interactive 卡片

    news_items: list of dict, each with keys:
        - category: str (如 "产品发布", "融资并购")
        - title: str
        - summary: str
        - source: str
    analysis: dict with keys:
        - investment: str
        - career: str
        - family: str
    trend_comment: str
    """
    elements = []

    # 1. 新闻条目（按分类分组）
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

    # 2. 投资与职业发展分析
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

    # 3. 趋势点评
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**🔥 今日趋势点评**\n{trend_comment}"
        }
    })

    # 4. 页脚
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": "由 Trae AI 自动整理推送"
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


# ====== 使用示例 ======
if __name__ == "__main__":
    # 示例数据
    news_items = [
        {
            "category": "产品发布",
            "title": "OpenAI 发布 GPT-5",
            "summary": "OpenAI 正式发布 GPT-5，性能大幅提升...",
            "source": "TechCrunch"
        },
        {
            "category": "产品发布",
            "title": "Google 更新 Gemini",
            "summary": "Gemini 2.0 发布，多模态能力增强...",
            "source": "The Verge"
        },
        {
            "category": "融资并购",
            "title": "某 AI 公司获 10 亿美元融资",
            "summary": "该公司专注于自动驾驶技术...",
            "source": "Reuters"
        }
    ]

    analysis = {
        "investment": "关注AI基础设施和垂直应用赛道",
        "career": "建议提升AI工程化能力",
        "family": "培养孩子的AI素养"
    }

    trend_comment = "本周AI行业呈现快速发展态势，各大厂商密集发布新产品..."

    card = build_news_card(
        title="Trae每日AI新闻推送 | 2026年6月20日",
        news_items=news_items,
        analysis=analysis,
        trend_comment=trend_comment
    )

    success, msg_id = send_interactive_card_to_lark(card)
    print(f"Success: {success}, msg_id: {msg_id}")
