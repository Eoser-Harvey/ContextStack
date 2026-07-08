"""
个人画像加载模块 — 从 profile_archive 自动加载最新档案

原理：
  每个工作日自动同步个人画像到 profile_archive/profile_YYYYMMDD.md。
  本模块按文件名日期排序，取最新文件解析为分析器（analyzer.py）
  和推送模块（push_lark.py）所需的结构化 dict。

用法：
  from profile_loader import load_latest_profile
  profile = load_latest_profile()
  if profile:
      analyze_tweets(tweets, profile)
"""

import os
import glob
import re


ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile_archive")


# ======================================================================
# 文件发现
# ======================================================================

def get_latest_profile_path():
    """从 profile_archive/ 找到最新日期的 profile_YYYYMMDD.md"""
    if not os.path.isdir(ARCHIVE_DIR):
        print(f"[ERROR] profile_archive 目录不存在: {ARCHIVE_DIR}")
        return None

    pattern = os.path.join(ARCHIVE_DIR, "profile_*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        print(f"[ERROR] profile_archive 中未找到 profile_*.md 文件")
        return None

    print(f"[INFO] 加载个人档案: {os.path.basename(files[0])}")
    return files[0]


# ======================================================================
# Markdown 表格解析
# ======================================================================

def _parse_markdown_tables(lines):
    """
    将 markdown 解析为 {section: {subsection: {key: value}}} 结构

    表结构支持：
      - 2 列 key-value 表：  | key | value |
      - 4-5 列投资表：        | 标的 | 数量 | ... | 存放 |
      自动跳过表头分隔行（|---|）
    """
    result = {}         # {section: {subsection: {key: value}}}
    section = "root"    # 当前 ## 标题
    subsection = ""     # 当前 ### 标题

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测 ## 节标题
        if line.startswith("## ") and not line.startswith("###"):
            section = line[3:].strip()
            subsection = ""
            result[section] = {}
            i += 1
            continue

        # 检测 ### 子节标题
        if line.startswith("### "):
            subsection = line[4:].strip()
            if section not in result:
                result[section] = {}
            result[section][subsection] = {}
            i += 1
            continue

        # 检测表格行
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) < 2:
                i += 1
                continue

            # 跳过表头分隔行
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                i += 1
                continue

            # 2 列 → key-value
            if len(cells) == 2:
                key, value = cells[0], cells[1]
                if section not in result:
                    result[section] = {}
                if subsection:
                    if subsection not in result[section]:
                        result[section][subsection] = {}
                    result[section][subsection][key] = value
                else:
                    result[section][key] = value

            # 3+ 列 → 第一列是标的名称
            else:
                label = cells[0]
                full_desc = " | ".join(cells[1:])  # 多列拼接为描述
                if section not in result:
                    result[section] = {}
                if subsection:
                    if subsection not in result[section]:
                        result[section][subsection] = {}
                    result[section][subsection][label] = full_desc
                else:
                    result[section][label] = full_desc

        i += 1

    return result


# ======================================================================
# 结构化映射 — 将解析结果转换为 analyzer.py 所需的嵌套 dict
# ======================================================================

def _build_profile(raw):
    """将原始 {section: {key: value}} 映射为 analyzer.py 期望的嵌套结构"""
    p = {
        "name": "Harvey",
        "career": {
            "company": "新华三",
            "role": "",
            "experience": "",
            "skills": ["C语言", "ARM/DSP架构", "RTOS", "Linux", "Python", "TFLM"],
            "focus": [],
            "salary": "",
            "target_companies": [],
            "location_constraint": "北京海淀/昌平",
            "job_search_status": "",
            "interview_method": "工程叙事四层结构: 本质→实践→踩坑→思考",
        },
        "assets": {
            "crypto": {"btc": "", "eth": "", "usdt": ""},
            "stocks": {"us": [], "hk": []},
            "ts_tokens": {},
            "real_estate": "",
            "cash": "",
            "total_assets": "",
            "net_assets": "",
            "investment_assets": "",
            "crcl_concentration": "",
        },
        "liabilities": {
            "credit_card_invest": "",
            "binance_loan": "¥0 (2026-06-05已全部还清)",
            "mortgage_commercial": "",
            "mortgage_fund": "",
        },
        "family": {
            "location": "北京",
            "hukou": "",
            "children": "",
            "spouse": "",
        },
        "insurance": {
            "hanwei_zhongji": "",
            "hanwei_dingshou": "",
            "xueyan_zhongji": "",
        },
        "risk_profile": "",
        "interests": [],
        "a8_plan": {
            "target": "",
            "btc_target": "",
            "strategy": "",
            "current_mode": "",
        },
    }

    # --- 职业发展画像 ---
    career_table = raw.get("职业发展画像", {})
    kv_map_career = {
        "当前公司": ("career", "company", str),
        "当前角色": ("career", "role", str),
        "经验": ("career", "experience", str),
        "地点约束": ("career", "location_constraint", str),
        "当前薪资": ("career", "salary", str),
        "求职状态": ("career", "job_search_status", str),
        "面试方法论": ("career", "interview_method", str),
        "目标公司": ("career", "target_companies", "split"),
        "行业聚焦": ("career", "focus", "split"),
    }
    for md_key, (obj, attr, conv) in kv_map_career.items():
        val = career_table.get(md_key, "")
        if val:
            if conv == "split":
                p[obj][attr] = [s.strip() for s in val.replace("、", ",").split(",") if s.strip()]
            else:
                p[obj][attr] = val

    # 技能栈（合并 技能栈+核心能力 行）
    skills_raw = career_table.get("技能栈", "")
    core_raw = career_table.get("核心能力", "")
    combined_skills = set()
    for s in re.split(r"[,，、]", skills_raw):
        s = s.strip()
        if s:
            combined_skills.add(s)
    for s in re.split(r"[,，、]", core_raw):
        s = s.strip()
        if s:
            combined_skills.add(s)
    if combined_skills:
        p["career"]["skills"] = sorted(combined_skills, key=lambda x: (
            -1 if x in ("C语言", "Python", "RTOS", "Linux", "ARM/DSP架构", "TFLM") else 0
        ))

    # --- 投资持仓概览 ---
    invest = raw.get("投资持仓概览", {})

    def _clean_table_rows(table, skip_keys=("标的", "指标")):
        """过滤表头行，只返回数据行"""
        return {k: v for k, v in table.items() if k not in skip_keys}

    # 加密货币
    crypto_table = _clean_table_rows(invest.get("加密货币", {}))
    if "BTC(链上)" in crypto_table:
        btcinfo = crypto_table["BTC(链上)"]
        parts = [p.strip() for p in btcinfo.split("|")]
        btc_qty = parts[0] if parts else "0.1298"
        wallet = parts[-1] if len(parts) > 1 else "链上钱包"
        p["assets"]["crypto"]["btc"] = f"{btc_qty} BTC ({wallet})"
    if "USDT(币安)" in crypto_table:
        usdt_val = crypto_table["USDT(币安)"]
        m = re.search(r'\$?([\d,]+\.?\d*)', usdt_val)
        if m:
            p["assets"]["crypto"]["usdt"] = f"${m.group(1)}"
    if "ETH" in crypto_table:
        eth_val = crypto_table["ETH"]
        parts = [p.strip() for p in eth_val.split("|")]
        p["assets"]["crypto"]["eth"] = parts[-1] if len(parts) > 1 else eth_val

    # 美股 — 每行构建描述
    us_table = _clean_table_rows(invest.get("美股", {}))
    us_descs = []
    for label, desc in us_table.items():
        parts = [p.strip() for p in desc.split("|")]
        qty = parts[0] if parts else ""
        loc = parts[-1] if len(parts) > 1 else ""
        us_descs.append(f"{label} {qty}股 ({loc})")
    p["assets"]["stocks"]["us"] = us_descs

    # 港股
    hk_table = _clean_table_rows(invest.get("港股", {}))
    hk_descs = []
    for label, desc in hk_table.items():
        parts = [p.strip() for p in desc.split("|")]
        qty = parts[0] if parts else ""
        hk_descs.append(f"{label} {qty}股")
    if hk_descs:
        p["assets"]["stocks"]["hk"] = hk_descs

    # TS时间代币
    ts_table = _clean_table_rows(invest.get("TS时间代币", {}))
    for label, desc in ts_table.items():
        parts = [p.strip() for p in desc.split("|")]
        p["assets"]["ts_tokens"][label] = f"{parts[0]} ({parts[1]})" if len(parts) >= 2 else desc

    # 关键指标
    metrics = invest.get("关键指标", {})
    metric_map = {
        "总资产": ("assets", "total_assets"),
        "净资产": ("assets", "net_assets"),
        "投资总资产": ("assets", "investment_assets"),
        "家庭备用金": ("assets", "cash"),
        "信用卡负债": ("liabilities", "credit_card_invest"),
        "CRCL集中度": ("assets", "crcl_concentration"),
    }
    for md_key, (obj, attr) in metric_map.items():
        val = metrics.get(md_key, "")
        if val:
            p[obj][attr] = val

    # --- 家庭与保险 ---
    family_table = raw.get("家庭与保险", {})
    family_map = {
        "居住地": ("family", "location"),
        "户籍": ("family", "hukou"),
        "子女": ("family", "children"),
        "配偶": ("family", "spouse"),
        "房产": ("assets", "real_estate"),
        "hanwei_zhongji": ("insurance", "hanwei_zhongji"),
        "hanwei_dingshou": ("insurance", "hanwei_dingshou"),
        "xueyan_zhongji": ("insurance", "xueyan_zhongji"),
    }
    for md_key, (obj, attr) in family_map.items():
        val = family_table.get(md_key, "")
        if val:
            p[obj][attr] = val

    # --- A8计划进度 ---
    a8_table = raw.get("A8计划进度", {})
    a8_map = {
        "目标": ("a8_plan", "target"),
        "BTC目标": ("a8_plan", "btc_target"),
        "策略": ("a8_plan", "strategy"),
        "当前状态": ("a8_plan", "current_mode"),
    }
    for md_key, (obj, attr) in a8_map.items():
        val = a8_table.get(md_key, "")
        if val:
            p[obj][attr] = val

    # --- 衍生字段 ---
    # interests — 从 focus 和行业推断
    if p["career"]["focus"]:
        p["interests"] = ["加密货币", "端侧AI", "CPO产业链", "投资理财", "职业发展"]

    # risk_profile
    crcl_str = p["assets"].get("crcl_concentration", "")
    p["risk_profile"] = f"高风险偏好 (加密货币+美股集中持仓, CRCL占投资67.8%⚠️)"

    return p


# ======================================================================
# 公开接口
# ======================================================================

def load_latest_profile():
    """
    加载最新个人档案，返回分析器所需的嵌套 dict。

    Returns:
        dict | None — 失败时返回 None 并打印错误
    """
    path = get_latest_profile_path()
    if not path:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except IOError as e:
        print(f"[ERROR] 读取档案文件失败: {e}")
        return None

    lines = content.split("\n")
    raw = _parse_markdown_tables(lines)
    profile = _build_profile(raw)
    return profile


def load_latest_profile_or_exit():
    """
    同上，但加载失败时直接 exit(1)（适合自动化脚本使用）
    """
    profile = load_latest_profile()
    if profile is None:
        print("[FATAL] 无法加载个人档案，退出")
        print(f"       请检查 {ARCHIVE_DIR} 目录下是否存在 profile_YYYYMMDD.md")
        exit(1)
    return profile


# ======================================================================
# 独立测试
# ======================================================================

if __name__ == "__main__":
    profile = load_latest_profile()
    if profile:
        import json
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    else:
        print("[ERROR] 加载失败")