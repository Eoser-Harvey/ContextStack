"""
燕知行 · 公司运营提醒 — 每日 11:00 推送
读取公司社保公积金计划文档，自动计算到期提醒，提前 7 天推送飞书群。
"""
import json
import os
import re
import sys
from datetime import date, timedelta

import requests
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from push_lark import send_interactive_card, load_secrets

# ==================== 配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today()
DATE_STR = TODAY.strftime("%Y年%m月%d日")
WEEKDAY = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][TODAY.weekday()]
ADVANCE_DAYS = 7  # 提前 7 天开始提醒
DEADLINE_END = TODAY + timedelta(days=ADVANCE_DAYS)


# ==================== 公司配置动态加载 ====================

# 公司社保公积金计划文档（唯一数据源，用户每日更新）
COMPANY_DOC_PATH = os.path.normpath(os.path.join(
    SCRIPT_DIR, "..", "..", "family-hub", "company-setup",
    "beijing-company-social-insurance-plan.md"
))

# 内置默认值（所有回退路径最终兜底）
BUILTIN_DEFAULTS = {
    "company": {
        "name": "燕知行",
        "register_date": "2026-07-09",
        "industry": "文艺创作与表演",
    },
    "stage": {"current": ""},
    "special_events_2026": [],
    "policy_highlights": [
        "**小微企业税收优惠延续至2027年底**\n5%企业所得税低税负、六税两费减半、小规模月销10万免增值税等优惠明确延续。金税四期「以数治税」全面上线，需注意合规申报。",
        "**《增值税法》2026年1月1日起施行**\n财政部税务总局公告2026年第10号将小规模纳税人优惠锁定至2027年12月31日。月销售额≤10万、季销售额≤30万免征增值税。",
        "**社保补贴政策延续至2026年底**\n中小微企业招用2026届高校毕业生、失业半年以上人员等重点群体，可申领社保补贴。税务部门正严查社保足额缴纳。",
        "**人社新规7月实施**\n多项社保权益变化生效，包括养老保险全国统筹落地、社保费检查套用税收执法程序和标准。",
    ],
}


def _parse_date(date_str: str) -> date:
    """解析 YYYY-MM-DD 格式日期字符串"""
    parts = date_str.strip().split("-")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


def _parse_timeline_date(raw_date: str, fallback_month: int, fallback_year: int) -> date | None:
    """解析时间线表格中的日期格式：9/15前、8/30、月末 等"""
    if not raw_date or not fallback_month:
        return None
    raw_date = re.sub(r'前$', '', raw_date).strip()  # 去掉"前"后缀
    if "月末" in raw_date:
        if fallback_month == 12:
            return date(fallback_year, 12, 31)
        return date(fallback_year, fallback_month + 1, 1) - timedelta(days=1)
    m = re.match(r'(\d+)/(\d+)', raw_date)
    if m:
        return date(fallback_year, int(m.group(1)), int(m.group(2)))
    return None


def _parse_timeline_table(table_text: str, base_year: int = 2026) -> list:
    """
    解析时间线 Markdown 表格，提取事件列表。
    表格格式：| **8月** | 8/14 | 签劳动合同 | 待办 |
    """
    events = []
    current_month = None
    for line in table_text.strip().split("\n"):
        if ":--" in line or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        month_cell = re.sub(r'\*', '', cells[0]).strip()
        date_cell = re.sub(r'\*', '', cells[1]).strip() if len(cells) > 1 else ""
        desc_cell = re.sub(r'\*', '', cells[2]).strip() if len(cells) > 2 else ""

        month_match = re.match(r'(\d+)月', month_cell)
        if month_match:
            current_month = int(month_match.group(1))
        if not date_cell or not desc_cell:
            continue

        event_date = _parse_timeline_date(date_cell, current_month, base_year)
        if event_date is None:
            continue

        # 跳过已完成事件（含 ✅ 标记）
        if "✅" in desc_cell:
            continue

        # 清理描述
        desc_clean = re.sub(r'[✅⚠️🔶⭐]', '', desc_cell).strip()
        desc_clean = re.sub(r'[（(][^）)]*[）)]', '', desc_clean).strip()
        if not desc_clean or len(desc_clean) < 3:
            continue

        name = desc_clean[:40] if len(desc_clean) > 40 else desc_clean
        events.append({
            "date": event_date.strftime("%Y-%m-%d"),
            "name": name,
            "description": desc_clean,
        })
    return events


def _parse_company_document(content: str) -> dict:
    """
    从公司社保公积金计划文档中提取最新运营状态。
    文档是唯一数据源，用户每日更新，脚本自动读取。
    """
    config = {
        "company": {"name": "燕知行", "register_date": "2026-07-09", "industry": "文艺创作与表演"},
        "stage": {"current": ""},
        "special_events_2026": [],
        "policy_highlights": BUILTIN_DEFAULTS["policy_highlights"],
        "doc_last_updated": "",
    }

    # 1. 文档更新时间
    m = re.search(r'最新整理时间:\s*(.+)', content)
    if m:
        config["doc_last_updated"] = m.group(1).strip()

    # 2. 当前状态文本
    m = re.search(r'当前状态:\s*(.+?)(?:\n|$)', content)
    status_text = m.group(1).strip() if m else ""

    # 3. 判断运营阶段（基于状态文本中的里程碑完成情况）
    has_shebao = "社保增员完成" in status_text
    has_gjj = "公积金增员完成" in status_text
    has_contract = "劳动合同" in status_text and "签订" in status_text

    if has_shebao and has_gjj:
        if has_contract:
            config["stage"]["current"] = "有员工运转期"
        else:
            config["stage"]["current"] = "入职过渡期"
    else:
        config["stage"]["current"] = "筹备期"

    # 4. 公司基本信息
    m = re.search(r'注册日期\s*\|\s*(\d{4}-\d{2}-\d{2})', content)
    if m:
        config["company"]["register_date"] = m.group(1)
    m = re.search(r'行业\s*\|\s*\*{0,2}(.+?)\*{0,2}\s*\|', content)
    if m:
        config["company"]["industry"] = m.group(1).strip()

    # 5. 解析时间线表格
    timeline_match = re.search(
        r'完整时间线（2026年8月-12月）.*?\n\n((?:\|.+\|.*\n)+)',
        content
    )
    if timeline_match:
        config["special_events_2026"] = _parse_timeline_table(timeline_match.group(1))

    return config


def load_company_config() -> dict:
    """
    每日运行时自动获取最新公司运营状态。
    优先级：公司社保公积金计划文档 > company_config.yaml > 内置默认值
    """
    # 优先1：从公司社保公积金计划文档解析（真正的数据源）
    if os.path.exists(COMPANY_DOC_PATH):
        try:
            with open(COMPANY_DOC_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            config = _parse_company_document(content)
            updated = config.get("doc_last_updated", "未知")
            stage = config["stage"]["current"]
            events_count = len(config.get("special_events_2026", []))
            print(f"[INFO] 从公司社保公积金计划文档解析配置（每日自动读取最新）")
            print(f"       文档更新时间: {updated}")
            print(f"       当前阶段: {stage}")
            print(f"       时间线事件: {events_count} 条")
            return config
        except Exception as e:
            print(f"[WARN] 文档解析失败: {e}，尝试回退")

    # 优先2：从 company_config.yaml 读取
    config_path = os.path.join(SCRIPT_DIR, "company_config.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            print("[INFO] 从 company_config.yaml 加载公司配置")
            for section in BUILTIN_DEFAULTS:
                if section not in config or config[section] is None:
                    config[section] = BUILTIN_DEFAULTS[section]
            return config
        except Exception as e:
            print(f"[WARN] 读取 company_config.yaml 失败: {e}")

    # 优先3：内置默认值
    print("[INFO] 使用内置默认配置")
    return BUILTIN_DEFAULTS


# 加载配置（每次运行自动读取最新）
COMPANY_CONFIG = load_company_config()
COMPANY_REGISTER_DATE = _parse_date(COMPANY_CONFIG["company"]["register_date"])


# ==================== 状态判断 ====================

def get_current_stage() -> str:
    """判断当前公司运营阶段（从文档状态行自动判定）"""
    stage_cfg = COMPANY_CONFIG.get("stage", {})
    direct_stage = stage_cfg.get("current", "")
    if direct_stage in ("筹备期", "入职过渡期", "有员工运转期"):
        return direct_stage
    return "筹备期"


def is_employee_stage() -> bool:
    """入职过渡期及之后视为有员工阶段"""
    stage = get_current_stage()
    return stage in ("入职过渡期", "有员工运转期")


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


# ==================== 政策新闻 ====================

def fetch_policy_news() -> list:
    """
    从多个可靠 API 获取公司相关政策新闻，严格按标题关键词匹配。
    每个源最多取 1 条，确保来源多样性。
    返回 [(标题, 摘要, 来源, 链接), ...] 列表，最多 4 条。
    """
    import html
    import xml.etree.ElementTree as ET

    news_items = []
    seen_titles = set()
    source_count = {}  # 每源最多取 1 条

    # 严格政策关键词 —— 必须出现在【标题】中才算匹配
    title_keywords = [
        # 税务
        "减税", "降费", "税收优惠", "税率", "关税", "免税",
        "增值税", "企业所得税", "个税", "税务",
        # 社保/公积金
        "社保", "公积金", "养老金", "医保",
        # 扶持/补贴
        "补贴", "扶持", "纾困", "奖补", "专项资金",
        # 营商/准入
        "营商环境", "市场准入", "证照分离", "放管服",
        # 企业类型
        "小微企业", "中小微", "民营企业", "个体工商户",
        # 文化
        "文化产业", "文化事业",
        # 知识产权
        "知识产权", "专利", "商标",
        # 监管/法规
        "市场监管", "反垄断", "数据安全", "个人信息保护",
        # 政府动作
        "国务院常务", "政策发布", "政策解读", "新规",
        "财政部", "税务总局", "人社部", "发改委", "工信部",
        # 其他
        "最低工资", "工伤", "失业保险", "生育保险",
    ]

    # 国内政策优先关键词（命中则排序靠前）
    domestic_keywords = [
        "国务院", "财政部", "税务总局", "人社部", "发改委", "工信部",
        "小微企业", "中小微", "民营企业", "个体工商户",
        "减税", "降费", "社保", "公积金", "补贴", "扶持",
        "营商环境", "市场准入", "放管服", "文化产业",
        "增值税", "个税", "企业所得税",
        "最低工资", "知识产权", "市场监管",
    ]

    # 排除关键词 —— 标题含这些词则跳过
    exclude_keywords = [
        "IPO", "港股", "A股", "减持", "增持", "配售",
        "财报", "股价", "涨跌", "涨停", "跌停", "盘前",
        "游资", "龙虎榜", "招股", "上市", "退市",
        "基金净值", "理财", "私募", "公募",
        "评级", "目标价", "买入", "卖出",
        # 国际新闻排除（用户要国内政策）
        "特朗普", "美联储", "欧盟", "英国", "法国",
        "德国", "日本", "韩国", "俄罗斯", "乌克兰",
        "北约", "中东", "印度", "巴西",
        "美国经济", "美股", "日经", "欧股",
        "美国", "国际观察", "国际",
    ]

    fetch_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def _is_policy_relevant(title: str) -> bool:
        """严格判断标题是否与公司政策相关"""
        if not title or len(title) < 5:
            return False
        for ex in exclude_keywords:
            if ex in title:
                return False
        for kw in title_keywords:
            if kw in title:
                return True
        return False

    def _is_domestic(title: str) -> bool:
        """判断是否为国内政策新闻"""
        return any(kw in title for kw in domestic_keywords)

    def _clean_summary(raw_desc: str, max_len: int = 300) -> str:
        """清理 HTML 并截断摘要"""
        clean = re.sub(r'<[^>]+>', '', raw_desc or "")
        clean = html.unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if len(clean) > max_len:
            return clean[:max_len] + "…"
        return clean

    def _add_item(title, raw_desc, source_name, link):
        """去重 + 每源限 1 条 + 加入列表"""
        dedup = title[:15]
        if dedup in seen_titles:
            return
        # 每源最多取 1 条
        if source_count.get(source_name, 0) >= 1:
            return
        seen_titles.add(dedup)
        source_count[source_name] = source_count.get(source_name, 0) + 1
        summary = _clean_summary(raw_desc)
        is_dom = _is_domestic(title)
        # 国内政策优先排序：(is_domestic, source_count) → 国内排前
        news_items.append((title, summary, source_name, link, is_dom))

    # ============================================================
    # 源 1: 36氪 RSS
    # ============================================================
    try:
        resp = requests.get("https://36kr.com/feed", headers=fetch_headers, timeout=10)
        resp.encoding = "utf-8"
        if resp.text.startswith("<?xml"):
            root = ET.fromstring(resp.text)
            items = root.findall(".//item")
            print(f"  [INFO] 36氪 RSS 获取到 {len(items)} 条")
            for item in items:
                title = item.findtext("title", "").strip()
                desc = item.findtext("description", "") or ""
                link = item.findtext("link", "").strip() or item.findtext("guid", "")
                if _is_policy_relevant(title):
                    _add_item(title, desc, "36氪", link)
        else:
            print(f"  [WARN] 36氪 RSS 返回非 XML 格式")
    except Exception as e:
        print(f"  [WARN] 36氪 RSS 失败: {e}")

    # ============================================================
    # 源 2: 新浪财经宏观 API
    # ============================================================
    try:
        resp = requests.get(
            "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=30",
            headers=fetch_headers, timeout=10
        )
        data = resp.json()
        items = data.get("result", {}).get("data", [])
        print(f"  [INFO] 新浪财经 API 获取到 {len(items)} 条")
        for item in items:
            title = item.get("title", "").strip()
            intro = item.get("intro", "") or ""
            link = item.get("url", "")
            if _is_policy_relevant(title):
                _add_item(title, intro, "新浪财经", link)
    except Exception as e:
        print(f"  [WARN] 新浪财经 API 失败: {e}")

    # ============================================================
    # 源 3: 新浪国内 API
    # ============================================================
    try:
        resp = requests.get(
            "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2517&num=30",
            headers=fetch_headers, timeout=10
        )
        data = resp.json()
        items = data.get("result", {}).get("data", [])
        print(f"  [INFO] 新浪国内 API 获取到 {len(items)} 条")
        for item in items:
            title = item.get("title", "").strip()
            intro = item.get("intro", "") or ""
            link = item.get("url", "")
            if _is_policy_relevant(title):
                _add_item(title, intro, "新浪国内", link)
    except Exception as e:
        print(f"  [WARN] 新浪国内 API 失败: {e}")

    # ============================================================
    # 源 4: 人民网 RSS —— 已移除（RSS 内容过时，多为数月前旧闻）
    # ============================================================

    # 国内政策优先排序
    news_items.sort(key=lambda x: (not x[4],))  # is_dom=True 排前

    print(f"  [INFO] 政策新闻匹配到 {len(news_items)} 条（国内优先）")
    # 返回时去掉 is_dom 标记
    return [(t, s, src, l) for t, s, src, l, _ in news_items[:4]]


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

    # ===== 2026年特殊时间线（从 company_config.yaml 动态加载）=====
    special_events = COMPANY_CONFIG.get("special_events_2026", [])
    for evt in special_events:
        dl = _parse_date(evt["date"])
        if in_window(dl):
            deadlines.append((dl, evt["name"], evt["description"]))

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
    company_name = COMPANY_CONFIG["company"]["name"]
    company_reg = COMPANY_CONFIG["company"]["register_date"]
    company_industry = COMPANY_CONFIG["company"]["industry"]
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**当前阶段**：{stage}  |  **公司注册日期**：{company_reg}  |  **行业**：{company_industry}",
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
    elif stage == "入职过渡期":
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    "📌 **入职过渡期核心任务**\n"
                    "• 社保增员 ✅ 公积金增员 ✅ 个税增员 ✅\n"
                    "• 签劳动合同（预计8月14日）\n"
                    "• 首次发工资缴社保（8月底，实发约5,560元）\n"
                    "• 首次个税实报：**9月15日前**（申报8月工资，约17.30元）\n"
                    "• 首次社保/公积金缴费：**9月15日前**\n"
                    "• Q3季报：**10月15日前**（6项零申报）"
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

    # ===== 政策新闻 =====
    news_items = fetch_policy_news()
    if news_items:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "📰 **今日政策要闻**",
            },
        })
        for title, summary, source, link in news_items:
            # 每条新闻独立 div，完整展示标题+摘要+来源
            content_parts = [f"**{title}**"]
            if summary:
                content_parts.append(summary)
            if source:
                content_parts.append(f"[{source}]")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(content_parts),
                },
            })
        elements.append({"tag": "hr"})
    else:
        # 无国内政策新闻时，展示近期政策要点（基于当前有效政策）
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "📰 **近期政策要点**（今日暂无最新政策新闻，以下为当前有效政策提醒）",
            },
        })
        policy_highlights = COMPANY_CONFIG.get("policy_highlights", [])
        for highlight in policy_highlights:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": highlight,
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