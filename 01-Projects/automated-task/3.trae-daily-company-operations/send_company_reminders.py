"""
燕知行 · 公司运营提醒 — 每日 11:00 推送
读取公司社保公积金计划文档，自动计算到期提醒，提前 7 天推送飞书群。
"""
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from push_lark import send_interactive_card, load_secrets

# ==================== 配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today()
DATE_STR = TODAY.strftime("%Y年%m月%d日")
WEEKDAY = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][TODAY.weekday()]
ADVANCE_DAYS = 7  # 提前 7 天开始提醒
DEADLINE_END = TODAY + timedelta(days=ADVANCE_DAYS)

# 公司关键日期
COMPANY_REGISTER_DATE = date(2026, 7, 9)
# 阶段判断：2026年9月前为筹备期，之后为有员工运转期
EMPLOYEE_STAGE_START = date(2026, 10, 1)  # 预计10月完成入职三件套+首次发薪


# ==================== 状态判断 ====================

def get_current_stage() -> str:
    """判断当前公司运营阶段"""
    if TODAY < EMPLOYEE_STAGE_START:
        return "筹备期"
    return "有员工运转期"


def is_employee_stage() -> bool:
    return TODAY >= EMPLOYEE_STAGE_START


# ==================== 截止日期计算 ====================

def next_occurrence(target_day: int) -> date:
    """计算下一个目标日（如每月15日）的日期"""
    this_month = date(TODAY.year, TODAY.month, min(target_day, 28))
    if this_month >= TODAY:
        return this_month
    # 下个月
    if TODAY.month == 12:
        return date(TODAY.year + 1, 1, min(target_day, 28))
    return date(TODAY.year, TODAY.month + 1, min(target_day, 28))


def next_quarterly(months: list, target_day: int = 15) -> date:
    """计算下一个季度截止日"""
    candidates = []
    for m in months:
        for y in [TODAY.year, TODAY.year + 1]:
            d = date(y, m, min(target_day, 28))
            if d >= TODAY:
                candidates.append(d)
    return min(candidates) if candidates else None


def next_annual(month: int, day: int) -> date:
    """计算下一个年度截止日"""
    this_year = date(TODAY.year, month, min(day, 28))
    if this_year >= TODAY:
        return this_year
    return date(TODAY.year + 1, month, min(day, 28))


def in_window(dl: date) -> bool:
    """判断截止日期是否在提前提醒窗口内"""
    return TODAY <= dl <= DEADLINE_END


def days_until(dl: date) -> int:
    return (dl - TODAY).days


# ==================== 截止日期定义 ====================

def get_all_deadlines():
    """
    返回所有截止日期列表。
    每个元素: (截止日期, 名称, 描述, 紧急程度标签)
    紧急程度: 'critical'=今日到期, 'urgent'=1-2天, 'normal'=3-7天
    """
    deadlines = []

    # ===== 月度常规（筹备期 + 有员工期通用）=====
    dl = next_occurrence(15)
    if in_window(dl):
        deadlines.append((dl, "个税申报", "每月15日前完成上月工资薪金个税申报（自然人电子税务局扣缴端）。筹备期无员工做零申报，有员工后实报。"))

    # 对公账户余额核查（每月15日前）
    if in_window(dl):
        deadlines.append((dl, "对公账户余额核查", "确保对公账户余额充足，防止社保/公积金/个税自动扣款失败。断缴 = 5年摇号资格重算。"))

    # ===== 有员工阶段月度 =====
    if is_employee_stage():
        # 1-5日 工资核算
        dl_5 = next_occurrence(5)
        if in_window(dl_5):
            deadlines.append((dl_5, "工资与社保核算", "制作工资表：应发工资 - 个人社保 - 个人公积金 - 代扣个税 = 实发工资。核对当月社保/公积金缴费通知单。"))

        # 10-15日 发工资
        dl_10 = next_occurrence(10)
        if in_window(dl_10):
            deadlines.append((dl_10, "对公账户发工资", "批量代发：对公账户→个人卡，银行流水备注'X月工资'。严禁现金发薪。"))

        # 15日前 社保缴费
        if in_window(dl):
            deadlines.append((dl, "社保费缴纳", "税务系统自动扣款（三方协议）。总额=单位部分+个人代扣部分。断缴=5年重算，确保余额充足。"))

        # 公积金汇缴
        dl_20 = next_occurrence(20)
        if in_window(dl_20):
            deadlines.append((dl_20, "公积金汇缴", "公积金中心按委托收款协议自动扣款。总额=单位缴存+个人缴存。"))

        # 月末 账务处理
        dl_28 = next_occurrence(28)
        if in_window(dl_28):
            deadlines.append((dl_28, "月末账务处理", "计提当月工资、单位社保、单位公积金。登记发放/缴费/缴税会计分录。装订工资表+银行回单+缴费凭证+个税申报表。"))

    # ===== 季度申报（1/4/7/10月15日前）=====
    dl_q = next_quarterly([1, 4, 7, 10], 15)
    if dl_q and in_window(dl_q):
        q_num = ((dl_q.month - 1) // 3) + 1
        deadlines.append((dl_q, f"Q{q_num}季度申报", f"增值税(文化服务+商业)+企业所得税+城建税+教育费附加+地方教育附加。筹备期6项零申报，有员工后按实申报。"))

    # ===== 年度截止日 =====
    # 次年3月31日：企业所得税汇算
    dl_331 = next_annual(3, 31)
    if in_window(dl_331):
        deadlines.append((dl_331, "企业所得税年度汇算清缴", "上年度企业所得税多退少补。即使零收入也要申报。漏报罚款+影响信用。"))

    # 次年6月30日：工商年报
    dl_630 = next_annual(6, 30)
    if in_window(dl_630):
        deadlines.append((dl_630, "工商年报", "国家企业信用信息公示系统填报。逾期列入经营异常名录，影响法人征信。"))

    # 次年9月30日：残保金
    dl_930 = next_annual(9, 30)
    if in_window(dl_930):
        deadlines.append((dl_930, "残疾人就业保障金申报", "即使0残疾人也要申报。每年一次。"))

    # 有员工阶段年度
    if is_employee_stage():
        # 社保基数核定（6-7月）
        dl_base = next_annual(7, 1)
        if in_window(dl_base):
            deadlines.append((dl_base, "社保缴费基数年度核定", "按员工上年度月平均工资申报新一年度社保基数。北京每年公布上下限。"))

        # 公积金基数调整（7月31日）
        dl_gjj = next_annual(7, 31)
        if in_window(dl_gjj):
            deadlines.append((dl_gjj, "公积金年度基数调整（跨年清册核定）", "公积金年度=当年7月至次年6月。先完成6月汇缴再办基数申报，否则无法缴7月。"))

        # 个税综合所得汇算（3-5月）
        dl_tax = next_annual(5, 31)
        if in_window(dl_tax):
            deadlines.append((dl_tax, "个人所得税综合所得年度汇算", "员工个人通过个税APP办理，公司提供收入明细协助。"))

    # ===== 2026年特殊时间线（一次性事件）=====
    special_2026 = [
        (date(2026, 8, 15), "个税零申报（7月）", "7月工资薪金个税零申报。筹备期无员工，做零申报即可。"),
        (date(2026, 9, 15), "个税零申报（8月）", "8月工资薪金个税零申报。"),
        (date(2026, 10, 15), "入职三件套 + 个税零申报（9月）+ Q3季报", "签劳动合同→社保增员→公积金增员。个税零申报。Q3季报：增值税(2子目)+企税+城建税+教附+地教附，共6项零申报。"),
        (date(2026, 11, 15), "首次个税实报（10月工资）", "申报10月工资个税。爱人约30.58元/月，弟弟约15.58元/月，合计约46.16元/月。"),
        (date(2026, 12, 15), "个税实报（11月）+ 账务处理", "申报11月工资个税。月末完成账务处理：计提工资+单位社保公积金+银行手续费。"),
    ]
    for dl, name, desc in special_2026:
        if in_window(dl):
            deadlines.append((dl, name, desc))

    # 去重、排序
    seen = set()
    unique = []
    for dl, name, desc in deadlines:
        key = (dl, name)
        if key not in seen:
            seen.add(key)
            unique.append((dl, name, desc))
    unique.sort(key=lambda x: x[0])

    return unique


# ==================== 构建卡片 ====================

def build_card_json():
    """构建飞书 interactive 卡片"""
    stage = get_current_stage()
    deadlines = get_all_deadlines()

    elements = []

    # 头部信息
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**当前阶段**：{stage}  |  **公司注册日期**：2026-07-09  |  **行业**：文艺创作与表演",
        },
    })

    # 阶段提示
    if stage == "筹备期":
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    "📌 **筹备期核心任务**\n"
                    "• 每月15日前：个税零申报（自然人电子税务局扣缴端）\n"
                    "• 每季度末后15日内：季度零申报（增值税+企税+附加税）\n"
                    "• 当前无员工、无社保公积金缴费，零申报即可\n"
                    "• 首次季报：**2026年10月15日前**（Q3，共6项零申报）\n"
                    "• 首次个税实报：**2026年11月15日前**（申报10月工资）\n"
                    "• **Q4启动（10月）**：为法人发工资 + 缴纳社保公积金"
                ),
            },
        })
    else:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    "📌 **有员工运转期核心任务**\n"
                    "• 每月1-5日：工资核算\n"
                    "• 每月10-15日：发工资（对公账户→个人卡）\n"
                    "• 每月15日前：社保缴费 + 个税申报\n"
                    "• 每月中旬：公积金汇缴\n"
                    "• 每月月末：账务处理\n"
                    "• 每月总出账：约17,612元"
                ),
            },
        })

    elements.append({"tag": "hr"})

    # 到期提醒
    if not deadlines:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "✅ **未来7天内无到期事项，一切正常。**",
            },
        })
    else:
        # 按紧急程度分组
        critical = [(dl, n, d) for dl, n, d in deadlines if days_until(dl) == 0]
        urgent = [(dl, n, d) for dl, n, d in deadlines if 1 <= days_until(dl) <= 2]
        normal = [(dl, n, d) for dl, n, d in deadlines if days_until(dl) >= 3]

        if critical:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "🚨 **今日到期（必须处理）**",
                },
            })
            for dl, name, desc in critical:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{name}**\n{desc}",
                    },
                })
            elements.append({"tag": "hr"})

        if urgent:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "⚠️ **1-2天内到期**",
                },
            })
            for dl, name, desc in urgent:
                left = days_until(dl)
                day_word = "明天" if left == 1 else "后天"
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{name}**（{day_word}，{dl.strftime('%m月%d日')}前）\n{desc}",
                    },
                })
            elements.append({"tag": "hr"})

        if normal:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📅 **提前提醒（{ADVANCE_DAYS}天内）**",
                },
            })
            for dl, name, desc in normal:
                left = days_until(dl)
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{name}**（{left}天后，{dl.strftime('%m月%d日')}前）\n{desc}",
                    },
                })

    elements.append({"tag": "hr"})

    # 关键风险提示
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": (
                "⚠️ **关键风险提示**\n"
                "• **社保断缴 = 5年摇号资格重算**，每月15日前确保对公账户余额充足\n"
                "• **个税不能为零**（摇号不认），发薪后确保有个税扣缴记录\n"
                "• **工商年报漏报 = 经营异常名录**，每年6月30日前必须完成\n"
                "• **零申报不等于不申报**，无收入也必须按期申报"
            ),
        },
    })

    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"燕知行 · 公司运营提醒 | {DATE_STR} {WEEKDAY} | 每日 11:00 自动推送",
            }
        ],
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"燕知行 · 公司运营提醒 | {DATE_STR} {WEEKDAY}",
            },
            "template": "blue",
        },
        "elements": elements,
    }
    return card


# ==================== 主流程 ====================

def main():
    print("=" * 60)
    print(f"  燕知行 · 公司运营提醒 - {DATE_STR} ({WEEKDAY})")
    print(f"  当前阶段: {get_current_stage()}")
    print("=" * 60)

    # 0. 加载飞书凭证
    secrets = load_secrets()
    app_id = secrets["app_id"]
    app_secret = secrets["app_secret"]
    chat_id = secrets["chat_id"]

    # 1. 计算到期事项
    deadlines = get_all_deadlines()
    print(f"\n[INFO] 未来 {ADVANCE_DAYS} 天内到期事项: {len(deadlines)} 项")
    for dl, name, desc in deadlines:
        tag = "🚨" if days_until(dl) == 0 else "⚠️" if days_until(dl) <= 2 else "📅"
        print(f"  {tag} {name} ({dl.strftime('%Y-%m-%d')}，{days_until(dl)}天后)")

    # 2. 构建卡片
    print(f"\n[STEP 2] 构建 interactive 卡片 ...")
    card = build_card_json()
    card_str = json.dumps(card, ensure_ascii=False, indent=2)
    print(f"  卡片 JSON 长度: {len(card_str)} 字符")

    # 3. 发送到飞书
    print(f"\n[STEP 3] 推送飞书群聊 {chat_id} ...")
    try:
        message_id = send_interactive_card(chat_id, card, app_id=app_id, app_secret=app_secret)
        print(f"  推送完成！message_id: {message_id}")
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  完成！message_id: {message_id}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()