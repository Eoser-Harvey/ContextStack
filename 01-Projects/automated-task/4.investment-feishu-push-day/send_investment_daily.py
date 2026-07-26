"""
每日投资指标推送 - 主入口脚本
功能：抓取多个投资指标数据，生成飞书 interactive 卡片并推送到群聊

当前覆盖指标:
  - CRCL (Circle): 买入信号分 / USDC 基本面 / 营收与估值 / 技术面 / 回测

架构设计:
  - indicators/ 包内实现可扩展的指标模块
  - 新增指标只需继承 BaseIndicator 并在 INDICATOR_REGISTRY 注册
  - 主脚本自动遍历所有注册指标，抓取数据并拼装卡片

数据源声明:
  - CRCL 数据来自 https://crcl.seanzhao.ai (作者: 子琦 @Seanzhao1105)
  - 仅为个人数据监控,不构成投资建议
"""
import json
import sys
import os
from datetime import datetime, timezone, timedelta

# 确保能找到同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from push_lark import send_interactive_card, verify_message, load_secrets
from indicators import INDICATOR_REGISTRY


def build_card_json() -> dict:
    """构建飞书 interactive 卡片 JSON。

    遍历所有注册指标，抓取数据并拼装卡片 elements。
    单个指标抓取失败不会中断整体流程，会在卡片中展示错误信息。
    """
    elements = []

    # ---- 卡片头部: 日期与概览 ----
    # 北京时间
    beijing_tz = timezone(timedelta(hours=8))
    now_beijing = datetime.now(beijing_tz)
    push_date = now_beijing.strftime("%Y年%m月%d日")
    push_time = now_beijing.strftime("%H:%M")

    # ---- 遍历所有指标 ----
    all_summaries = []
    indicator_count = 0
    failed_count = 0

    for IndicatorClass in INDICATOR_REGISTRY:
        indicator = IndicatorClass()
        print(f"\n[INFO] 处理指标: {indicator.name}")

        try:
            data = indicator.fetch()
            section_elements = indicator.build_section(data)
            elements.extend(section_elements)
            elements.append({"tag": "hr"})

            summary = indicator.get_summary(data)
            all_summaries.append(f"[{indicator.name}] {summary}")
            indicator_count += 1

        except Exception as e:
            print(f"[ERROR] 指标 {indicator.name} 抓取失败: {e}")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{indicator.icon} {indicator.name}**\n\u26a0\ufe0f 数据抓取失败: {e}",
                },
            })
            elements.append({"tag": "hr"})
            failed_count += 1

    # ---- 趋势点评 ----
    if all_summaries:
        trend_text = f"**今日投资指标速览 ({push_date})**\n\n"
        for s in all_summaries:
            trend_text += f"\u2022 {s}\n"
        trend_text += (
            f"\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\u26a0\ufe0f 以上数据来自第三方看板,仅为个人数据监控,不构成投资建议。"
            f"加密相关股票波动极大,请只用亏得起的钱做决定。"
        )
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": trend_text.rstrip()},
        })

    # ---- 页脚 ----
    elements.append({"tag": "hr"})
    data_sources = []
    for IndicatorClass in INDICATOR_REGISTRY:
        ind = IndicatorClass()
        if hasattr(ind, "DASHBOARD_URL"):
            data_sources.append(f"{ind.name}: {ind.DASHBOARD_URL}")
        else:
            data_sources.append(ind.name)

    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": (
                    f"Trae每日投资指标推送 | {push_date} {push_time} (北京时间) | "
                    f"指标数: {indicator_count}/{len(INDICATOR_REGISTRY)}"
                    + (f" (失败{failed_count})" if failed_count else "")
                    + f" | 数据来源: {', '.join(data_sources)}"
                ),
            }
        ],
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"投资指标日报 | {push_date}",
            },
            "template": "green",
        },
        "elements": elements,
    }

    return card


def main():
    print("=" * 60)
    print("  每日投资指标推送")
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
    print(f"  注册指标数: {len(INDICATOR_REGISTRY)}")

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
