# -*- coding: utf-8 -*-
"""
社区投资情报抓取推送 - 主入口脚本
功能：从 ChatLog 云端报告中心抓取核心群聊 + 额外群聊 AI 摘要报告，
      提取投资相关信息（热门代币/股票/项目/观点/洞察），生成飞书卡片推送到"社区投资情报"群。
调度：TRAE 自动化任务每日执行；报告每天 08:01 更新，仅当有新报告时推送（去重）。
"""
import json
import os
import re
import sys
import time
import datetime
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from push_lark import send_interactive_card, verify_message, load_secrets

# ==================== 配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "community_push_state.json")  # 去重状态（上次推送的报告+时间戳）

# 报告日期格式（文件名里 YYYYMMDD）
DATE_FMT = "%Y%m%d"


# ==================== 站点访问 ====================

def _load_site_secrets():
    """加载站点凭证 + 社区群 chat_id（从 .secrets.yaml，已 gitignore）"""
    import yaml
    with open(os.path.join(SCRIPT_DIR, ".secrets.yaml"), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    site = data.get("site", {})
    if not site.get("base_url") or not site.get("username") or not site.get("password"):
        raise RuntimeError(".secrets.yaml 缺少 site 配置")
    community_chat_id = (data.get("lark", {}) or {}).get("community_chat_id") or ""
    return {"site": site, "community_chat_id": community_chat_id}


def fetch_report_list(site):
    """获取 /api/reports 报告列表，返回 [{file, modified, size}]（按 modified 倒序）"""
    import requests
    url = site["base_url"] + "/api/reports"
    r = requests.get(url, auth=(site["username"], site["password"]), timeout=20)
    r.raise_for_status()
    data = r.json()
    data.sort(key=lambda x: x.get("modified", 0), reverse=True)
    return data


def fetch_report_html(site, filename):
    """抓取指定报告 HTML 文本"""
    import requests
    url = site["base_url"] + "/reports/" + filename
    r = requests.get(url, auth=(site["username"], site["password"]), timeout=20)
    r.raise_for_status()
    return r.text


def pick_latest_reports(report_list, today=None):
    """挑选最新一天的核心+额外报告。
    返回: {"core": {file, modified}, "additional": {file, modified}} 或 None
    若当天(today=YYYYMMDD)报告已存在则用当天，否则用列表里最新一天。
    """
    today = today or datetime.date.today().strftime(DATE_FMT)
    core = None
    additional = None
    latest_day = None
    for item in report_list:
        m = re.match(r"(core|additional)_groups_report_(\d{8})(?:_[\d]+)?\.html", item["file"])
        if not m:
            continue
        kind, day = m.group(1), m.group(2)
        if latest_day is None:
            latest_day = day  # 列表已按 modified 倒序，第一个即最新一天
        if day != latest_day:
            continue  # 只关心最新一天
        if kind == "core" and core is None:
            core = {"file": item["file"], "modified": item["modified"]}
        elif kind == "additional" and additional is None:
            additional = {"file": item["file"], "modified": item["modified"]}
        if core and additional:
            break
    if not core and not additional:
        return None
    return {"core": core, "additional": additional, "day": latest_day}


def is_new_report(picked, state):
    """判断是否为新报告：记录文件名 + modified，只要不同就算新"""
    core = picked.get("core") or {}
    add = picked.get("additional") or {}
    key = (core.get("file", ""), core.get("modified", 0),
           add.get("file", ""), add.get("modified", 0))
    if state.get("last_key") == list(key):
        return False
    return True


# ==================== HTML 解析 ====================
# 关注的 class -> 收集纯文本
CORE_GROUP_CLASSES = {"group-section"}        # 核心报告每群容器
CORE_SECTION_TITLES = {"ai-title"}            # 每群小节标题（热门代币/讨论项目/关键洞察）
CORE_ITEM_NAME = {"ai-item-name"}             # 条目名（BTC/RH链等）
CORE_ITEM_CONTEXT = {"ai-item-context"}       # 条目描述
CORE_INSIGHT = {"insight-item"}               # 洞察条目
CORE_GROUP_NAME = {"group-name"}
CORE_GROUP_OWNER = {"group-owner"}

ADD_GROUP_CLASSES = {"group-card"}            # 额外报告每群容器
ADD_SECTION_TITLES = {"section-title"}        # 每群小节标题（代币/股票/项目/观点/洞察...）
ADD_TAG = {"tag"}                             # 标签（含 title 属性=观点）
ADD_INSIGHTS = {"insights"}                   # 观点/洞察容器
ADD_SUMMARY = {"summary"}                     # 内容总结
ADD_SENTIMENT = {"sentiment"}                 # 情绪
ADD_GROUP_NAME = {"group-name"}
ADD_GROUP_STATS = {"group-stats"}


class _TextCollector(HTMLParser):
    """按 class 收集元素文本。进入目标 class 时开始收集，其结束标签时停止。"""
    def __init__(self, target_classes):
        super().__init__()
        self.targets = target_classes
        self.stack = []          # 元素 class 栈
        self.depth = 0           # 当前收集深度
        self.collecting = False
        self.buf = []
        self.results = []

    def _cls(self, attrs):
        for k, v in attrs:
            if k == "class":
                return set(v.split())
        return set()

    def handle_starttag(self, tag, attrs):
        cls = self._cls(attrs)
        if self.collecting:
            self.depth += 1
            return
        if cls & self.targets:
            self.collecting = True
            self.depth = 0
            self.buf = []

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if self.collecting:
            if self.depth > 0:
                self.depth -= 1
            else:
                text = "".join(self.buf)
                text = re.sub(r"\s+", " ", text).strip()
                self.results.append(text)
                self.collecting = False
                self.buf = []

    def handle_data(self, data):
        if self.collecting:
            self.buf.append(data)


def _collect(html, target_classes):
    p = _TextCollector(target_classes)
    p.feed(html)
    return p.results


def parse_core_report(html):
    """解析核心报告 -> [{group, owner, sections:{标题: [条目]}, insights:[...]}]"""
    groups = []
    # 按 group-section 分割
    pattern = re.compile(r'<div class="group-section">(.*?)(?=<div class="group-section">|$)', re.S)
    for m in pattern.finditer(html):
        block = m.group(1)
        names = _collect(block, CORE_GROUP_NAME)
        owners = _collect(block, CORE_GROUP_OWNER)
        group = {
            "name": names[0] if names else "",
            "owner": owners[0] if owners else "",
            "sections": {},   # 标题 -> 条目列表
        }
        # 每个小节
        sec_pattern = re.compile(r'<div class="ai-section">(.*?)(?=<div class="ai-section">|$)', re.S)
        for sm in sec_pattern.finditer(block):
            sec = sm.group(1)
            titles = _collect(sec, CORE_SECTION_TITLES)
            if not titles:
                continue
            title = titles[0]
            # 条目（ai-item）和洞察（insight-item）
            items = _collect(sec, CORE_ITEM_NAME | CORE_ITEM_CONTEXT | CORE_INSIGHT)
            # 单独取名称列表（带次数）和洞察列表
            names_list = _collect(sec, CORE_ITEM_NAME)
            contexts = _collect(sec, CORE_ITEM_CONTEXT)
            insights = _collect(sec, CORE_INSIGHT)
            entries = []
            for i, nm in enumerate(names_list):
                ctx = contexts[i] if i < len(contexts) else ""
                entries.append((nm, ctx))
            group["sections"][title] = {"items": entries, "insights": insights}
        if group["name"]:
            groups.append(group)
    return groups


def parse_additional_report(html):
    """解析额外报告 -> [{name, stats, sections:{标题:[文本]}}]"""
    groups = []
    pattern = re.compile(r'<div class="group-card">(.*?)(?=<div class="group-card">|$)', re.S)
    for m in pattern.finditer(html):
        block = m.group(1)
        names = _collect(block, ADD_GROUP_NAME)
        stats = _collect(block, ADD_GROUP_STATS)
        group = {
            "name": names[0] if names else "",
            "stats": stats[0] if stats else "",
            "sections": {},
        }
        sec_pattern = re.compile(r'<div class="analysis-section">(.*?)(?=<div class="analysis-section">|$)', re.S)
        for sm in sec_pattern.finditer(block):
            sec = sm.group(1)
            titles = _collect(sec, ADD_SECTION_TITLES)
            if not titles:
                continue
            title = titles[0]
            tags = _collect(sec, ADD_TAG)
            insights = _collect(sec, ADD_INSIGHTS)
            summaries = _collect(sec, ADD_SUMMARY)
            sentiments = _collect(sec, ADD_SENTIMENT)
            texts = []
            for t in tags:
                if t and "暂无" not in t:
                    texts.append(t)
            for t in insights:
                if t and "暂无" not in t:
                    texts.append(t)
            for t in summaries:
                if t and "暂无" not in t:
                    texts.append(t)
            for t in sentiments:
                if t and "暂无" not in t:
                    texts.append(t)
            # 去重保序
            seen = set()
            uniq = []
            for t in texts:
                if t not in seen:
                    seen.add(t)
                    uniq.append(t)
            group["sections"][title] = uniq
        if group["name"]:
            groups.append(group)
    return groups


# ==================== 构建卡片 ====================

# 只关注的投资相关小节标题（关键字匹配）
INVEST_SECTION_KEYWORDS = ["代币", "股票", "项目", "观点", "洞察", "内容", "情绪"]

CORE_IMPORTANT = ["🪙", "🚀", "💡"]  # 核心报告只取：热门代币/讨论项目/关键洞察


def _clean(s):
    """清理文本，规避飞书/命令行特殊字符（$ 与 |）"""
    s = s.replace("$", "＄").replace("|", "｜").replace("|", "｜")
    return s.strip()


def build_investment_blocks(core_groups, add_groups):
    """把解析结果过滤为投资相关条目，返回 [(群名, 摘要文本), ...] 已按重要性排序"""
    blocks = []

    # 1) 核心群聊：只保留有投资内容的小节（代币/项目/洞察），跳过"暂无"
    for g in core_groups:
        lines = []
        for title, sec in g["sections"].items():
            if not any(k in title for k in ["代币", "项目", "洞察"]):
                continue
            items = sec.get("items", [])
            insights = sec.get("insights", [])
            if items:
                # 组合成 "条目名(次数): 描述"
                for nm, ctx in items:
                    if ctx and "暂无" not in ctx and "无消息" not in ctx:
                        lines.append(f"{_clean(nm)}: {_clean(ctx)}")
            if insights:
                for ins in insights:
                    if ins and "暂无" not in ins and "无消息" not in ins and "无活跃" not in ins:
                        lines.append(_clean(ins))
        if lines:
            blocks.append((g["name"], "；".join(lines)))

    # 2) 额外群聊：只保留有投资内容的小节，跳过"暂无"
    for g in add_groups:
        lines = []
        for title, texts in g["sections"].items():
            if not any(k in title for k in ["代币", "股票", "项目", "观点", "洞察"]):
                continue
            for t in texts:
                if t and "暂无" not in t and "无消息" not in t and "无活跃" not in t:
                    lines.append(_clean(t))
        if lines:
            blocks.append((g["name"], "；".join(lines)))

    return blocks


def build_card_json(core_groups, add_groups, day, report_count=0):
    """构建飞书 interactive 卡片 JSON"""
    blocks = build_investment_blocks(core_groups, add_groups)
    date_display = f"{day[:4]}-{day[4:6]}-{day[6:8]}"

    elements = []

    # 概览
    overview = (f"核心群聊 {len(core_groups)} 个｜额外群聊 {len(add_groups)} 个｜"
                f"筛选出投资相关 {len(blocks)} 个群")
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": f"**📊 今日社区投资情报（{date_display}）**\n{overview}"},
    })
    elements.append({"tag": "hr"})

    if not blocks:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md",
                     "content": "今日各群暂无有效投资讨论（代币/股票/项目/洞察均无实质内容）。"},
        })
    else:
        for name, text in blocks:
            # 卡片单条长度限制，截断超长
            if len(text) > 400:
                text = text[:400] + "…"
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**{_clean(name)}**\n{text}"},
            })
            elements.append({"tag": "hr"})

    # 页脚
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"数据来源：ChatLog 云端报告中心 v3.1（{report_count} 份报告）｜每日 08:01 自动更新｜仅供参考，投资需谨慎",
        }],
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"社区投资情报 | {date_display}"},
            "template": "green",
        },
        "elements": elements,
    }
    return card


# ==================== 状态管理 ====================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== 主流程 ====================

def main():
    print("=" * 60)
    print("  社区投资情报抓取推送")
    print("=" * 60)

    # 0. 配置
    secrets = load_secrets()
    app_id, app_secret = secrets["app_id"], secrets["app_secret"]
    site_cfg = _load_site_secrets()
    site = site_cfg["site"]
    chat_id = site_cfg.get("community_chat_id") or secrets["chat_id"]
    if site_cfg.get("community_chat_id"):
        print(f"[INFO] 推送目标: 社区投资情报群 {chat_id}")

    # 1. 抓取报告列表
    print(f"\n[STEP 1] 抓取报告列表 {site['base_url']} ...")
    report_list = fetch_report_list(site)
    print(f"  报告总数: {len(report_list)}")

    # 2. 挑选最新报告
    picked = pick_latest_reports(report_list)
    if not picked:
        print("[WARN] 未找到 core/additional 报告，退出")
        sys.exit(1)
    day = picked["day"]
    print(f"  最新报告日: {day}")
    if picked["core"]:
        print(f"  core: {picked['core']['file']} (modified={picked['core']['modified']})")
    if picked["additional"]:
        print(f"  additional: {picked['additional']['file']} (modified={picked['additional']['modified']})")

    # 3. 去重检查
    state = load_state()
    if not is_new_report(picked, state):
        print("[INFO] 报告无更新（已推送过），本次跳过")
        sys.exit(0)

    # 4. 抓取两份报告正文
    print(f"\n[STEP 2] 抓取报告正文 ...")
    core_html = ""
    if picked["core"]:
        core_html = fetch_report_html(site, picked["core"]["file"])
        print(f"  core HTML: {len(core_html)} 字符")
    add_html = ""
    if picked["additional"]:
        add_html = fetch_report_html(site, picked["additional"]["file"])
        print(f"  additional HTML: {len(add_html)} 字符")

    # 5. 解析
    print(f"\n[STEP 3] 解析投资信息 ...")
    core_groups = parse_core_report(core_html) if core_html else []
    add_groups = parse_additional_report(add_html) if add_html else []
    print(f"  核心群聊解析: {len(core_groups)} 个")
    print(f"  额外群聊解析: {len(add_groups)} 个")
    blocks = build_investment_blocks(core_groups, add_groups)
    print(f"  投资相关筛选: {len(blocks)} 个群")
    for name, text in blocks[:10]:
        print(f"    - {name}: {text[:80]}")

    # 6. 构建卡片
    print(f"\n[STEP 4] 构建飞书卡片 ...")
    card = build_card_json(core_groups, add_groups, day, report_count=len(report_list))
    card_str = json.dumps(card, ensure_ascii=False, indent=2)
    print(f"  卡片 JSON: {len(card_str)} 字符")

    # 7. 推送
    print(f"\n[STEP 5] 推送消息到群 {chat_id} ...")
    try:
        message_id = send_interactive_card(chat_id, card, app_id=app_id, app_secret=app_secret)
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")
        sys.exit(1)

    # 8. 验证
    print(f"\n[STEP 6] 验证消息 ...")
    try:
        verify_message(message_id, app_id=app_id, app_secret=app_secret)
        print("  消息验证通过！")
    except Exception as e:
        print(f"[WARN] 验证消息时出现问题: {e}")

    # 9. 更新状态
    core = picked.get("core") or {}
    add = picked.get("additional") or {}
    state["last_key"] = [core.get("file", ""), core.get("modified", 0),
                         add.get("file", ""), add.get("modified", 0)]
    state["last_day"] = day
    state["last_push_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_state(state)
    print(f"\n  状态已更新: {state['last_push_time']}")

    print(f"\n{'=' * 60}")
    print(f"  推送完成！message_id: {message_id}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
