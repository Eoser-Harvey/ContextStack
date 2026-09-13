# -*- coding: utf-8 -*-
"""
刷卡循环提醒（信用卡循环第一线提醒）

数据源：
  表1 · 主循环  +  表2 · 独立小循环
  → E:\\ProjectGroup\\AI\\ContextStack\\01-Projects\\family-hub\\credit-card-management\\信用卡管理方案.md  §7.3
  年费到期（附加段）
  → 同目录 卡片信息库.md

逻辑：
  匹配 今天 == 刷卡日(D0)   → "今日需刷卡"
  匹配 今天 == 到账日       → "今日资金到账"（金额取该行「还款金额」，并累加合计）
  两表均无刷卡且无到账 且 无30天内年费到期 → 静默结束，不推送

推送：PushPlus，template=html，title 前缀 🔁
用法：
  python 刷卡循环提醒.py            # 正常执行并推送
  python 刷卡循环提醒.py --dry      # 只打印，不推送（调试用）
"""
import sys
import io
import re
import os
import json
import argparse
import urllib.request
from datetime import datetime, date

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE_DIR, "信用卡管理方案.md")
CARD_DB_PATH = os.path.join(BASE_DIR, "卡片信息库.md")

PUSHPLUS_URL = "http://www.pushplus.plus/send"
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "6b280503d6df417f87556a366bc4ba61")

FEE_WARN_DAYS = 30          # 年费到期预警窗口（天）
GROUP_FONT_SIZE = 19        # 表1/表2 分组标题字号（px，比正文大一档）
FOOTER = "📱 原则：能D2就D2省费率，来不及才D1；刷出即蓄水，还后次日必刷，绝不当日还当日刷"


# ---------------------------------------------------------------- 解析工具
def _day_num(s):
    """'21日' / '**22日**' -> 21；失败 None"""
    m = re.match(r"(\d+)", str(s).replace("**", "").strip())
    return int(m.group(1)) if m else None


def _wan(s):
    """'4.6万' -> 4.6；失败 None（单位：万）"""
    m = re.match(r"([\d.]+)\s*万", str(s).replace("**", ""))
    return float(m.group(1)) if m else None


def _last_day_of(year, month):
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


# ---------------------------------------------------------------- 两张循环表
def parse_tables(path):
    """
    解析 §7.3「首尾循环衔接表1」与「首尾循环衔接表2」。
    返回 {'表1': [...], '表2': [...]}，每条：
      card / repay_day / amount / brush_day / arrive_day / tier / use_for
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到 {path}")

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    groups = {"表1": [], "表2": []}
    current, header_done = None, False

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if "首尾循环衔接表1" in line:
            current, header_done = "表1", False
            continue
        if "首尾循环衔接表2" in line:
            current, header_done = "表2", False
            continue
        if current is None:
            continue
        if not stripped.startswith("|"):
            if stripped:
                current = None          # 表格结束
            continue

        cells = [c.strip().replace("**", "").replace("　", "")
                 for c in stripped.strip("|").split("|")]
        if any("刷卡日" in c for c in cells):
            header_done = True
            continue
        if not header_done:
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if len(cells) < 7:
            continue
        card = cells[0].strip()
        if not card or card in ("卡", "银行"):
            continue
        groups[current].append({
            "card": card,
            "repay_day": cells[1].strip(),
            "repay_day_num": _day_num(cells[1]),
            "amount": cells[2].strip(),
            "brush_day": _day_num(cells[3]),
            "arrive_day": _day_num(cells[4]),
            "tier": cells[5].strip(),
            "use_for": cells[6].strip(),
        })
    return groups


# ---------------------------------------------------------------- 年费到期
def parse_annual_fees(path, today):
    """
    扫描 卡片信息库.md 的「年费」「收取日」行，提取 "M月D日/M月D号"。
    返回 [(卡名, 到期日date, 剩余天数), ...]，剩余天数 <= FEE_WARN_DAYS。
    只取卡片自述里写明日期的卡；"每年2月""年底前""消费N笔免"这类无确定日期的跳过。
    """
    if not os.path.exists(path):
        print(f"  [年费] 跳过：找不到 {path}")
        return []

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    hits, card = [], None
    pat = re.compile(r"(\d{1,2})月(\d{1,2})[日号]")

    for raw in lines:
        line = raw.rstrip("\n")
        if line.startswith("### "):
            card = re.sub(r"^###\s*", "", line).split("（")[0].strip()
            continue
        m = re.match(r"^\|\s*(年费|收取日)\s*\|(.+?)\|", line)
        if not m or not card:
            continue
        for mm, dd in pat.findall(m.group(2)):
            mm, dd = int(mm), int(dd)
            # 下一次到期日（未过当年则当年）
            try:
                due = date(today.year, mm, dd)
            except ValueError:
                continue
            if due < today:
                due = date(today.year + 1, mm, dd)
            days = (due - today).days
            if days <= FEE_WARN_DAYS:
                hits.append((card, due, days))
    hits.sort(key=lambda x: x[2])
    return hits


# ---------------------------------------------------------------- 文案拼装
def _matches(day, today):
    """day 是否落在今天。小月规则：还款日 31 日逢小月按当月最后一天处理"""
    if day is None:
        return False
    last = _last_day_of(today.year, today.month)
    return day == today.day or (day > last and today.day == last)


def build_group(title, recs, today):
    """
    按历史推送格式生成单张表的分段 HTML。
    三段：💳今日需还款（还款日==今天）→ 🔔今日需刷卡（刷卡日==今天）→ 💰今日资金到账（到账日==今天）
    返回 (html, 有还款, 有刷卡, 有到账)
    """
    repay = [r for r in recs if _matches(r["repay_day_num"], today)]
    brush = [r for r in recs if _matches(r["brush_day"], today)]
    arrive = [r for r in recs if _matches(r["arrive_day"], today)]

    out = [f'<b><span style="font-size:{GROUP_FONT_SIZE}px;">{title}</span></b><br>']

    # ---- 今日需还款 ----
    out.append("<b>💳 今日需还款：</b><br>")
    if repay:
        total_repay = 0.0
        for r in repay:
            out.append(f"&nbsp;&nbsp;💳 <b>{r['card']}</b> {r['amount']}<br>")
            v = _wan(r["amount"])
            if v:
                total_repay += v
        if total_repay > 0:
            out.append(f"<br>💳 今日还款合计：<b>{total_repay:.2f}万</b>")
    else:
        out.append("&nbsp;&nbsp;今日无需还款")
    out.append("<br><br>")

    # ---- 今日需刷卡 ----
    out.append("<b>🔔 今日需刷卡：</b><br>")
    if brush:
        for r in brush:
            arrive_day = r["arrive_day"]
            if arrive_day and r["brush_day"] and arrive_day < r["brush_day"]:
                arrive_day = _last_day_of(today.year, today.month)     # 跨月顺延
            out.append(f"&nbsp;&nbsp;💳 <b>{r['card']}</b> 刷 {r['amount']}"
                       f"（{r['tier']}，{arrive_day}到账）<br>")
    else:
        out.append("&nbsp;&nbsp;今日无需刷卡")
    out.append("<br><br>")

    # ---- 今日资金到账 ----
    out.append("<b>💰 今日资金到账：</b><br>")
    total = 0.0
    if arrive:
        for r in arrive:
            out.append(f"&nbsp;&nbsp;💰 <b>{r['card']}</b> {r['amount']}（{r['tier']}）"
                       f"→ {r['use_for']}<br>")
            v = _wan(r["amount"])
            if v:
                total += v
    else:
        out.append("&nbsp;&nbsp;今日无资金到账")
    if total > 0:
        out.append(f"<br>💰 今日到账合计：<b>{total:.2f}万</b>")
    out.append("<br><br>")

    return "".join(out), bool(repay), bool(brush), bool(arrive)


def build_message(today, groups, fees):
    today_str = today.strftime("%Y年%m月%d日")
    blocks, flags = [], []
    for key, label in (("表1", "🔷 表1 · 主循环"),
                       ("表2", "🔶 表2 · 独立小循环")):
        html, has_repay, has_brush, has_arrive = build_group(label, groups[key], today)
        blocks.append(html)
        flags += [has_repay, has_brush, has_arrive]

    if not any(flags) and not fees:
        return None, None

    parts = [f"<b>📅 刷卡循环提醒 | {today_str}</b><br><br>"]
    parts.append(blocks[0])
    parts.append(blocks[1])
    if fees:
        parts.append("<b>🎫 年费到期预警（30天内）：</b><br>")
        for card, due, days in fees:
            parts.append(f"&nbsp;&nbsp;🎫 <b>{card}</b> {due.strftime('%m月%d日')}"
                         f"（{days}天后）<br>")
        parts.append("<br>")
    parts.append(FOOTER)

    return f"🔁 刷卡循环提醒 - {today_str}", "\n".join(parts)


# ---------------------------------------------------------------- 推送
def send_pushplus(title, content):
    data = {"token": PUSHPLUS_TOKEN, "title": title, "content": content, "template": "html"}
    req = urllib.request.Request(
        PUSHPLUS_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=20)
    return resp.read().decode("utf-8")


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只打印，不推送")
    args = ap.parse_args()

    today = datetime.now()
    print(f"[{today}] 刷卡循环提醒启动")

    groups = parse_tables(DOC_PATH)
    print(f"  解析: 表1 {len(groups['表1'])} 条 | 表2 {len(groups['表2'])} 条")

    fees = parse_annual_fees(CARD_DB_PATH, today.date())
    print(f"  年费30天内到期: {len(fees)} 张")

    title, content = build_message(today, groups, fees)
    if not title:
        print(f"  今天({today.day}日)两表均无刷卡/到账、也无年费到期 → 静默结束，不推送。")
        return

    print("  ---- 推送预览 ----")
    print("  " + title)
    plain = re.sub(r"<[^>]+>", "", content.replace("<br>", "\n  ")).replace("&nbsp;", " ")
    print("  " + plain)
    print("  ------------------")

    if args.dry:
        print("  [dry-run] 未发送")
        return
    print("  " + send_pushplus(title, content))


if __name__ == "__main__":
    main()
