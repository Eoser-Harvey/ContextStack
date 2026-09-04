"""
每日个人画像归档同步脚本

每天0点执行：
1. 读取 holdings.yaml + 最新月度报告 + 职业发展档案
2. 生成两份 profile_archive 归档（小时推送/日报推送各一份）
3. 静默完成，异常时记录日志

架构说明：
- profile_loader.py 自动从 profile_archive/ 按文件名日期排序取最新文件
- analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile() 动态加载
- config.yaml 不再硬编码 profile 段，所有分析实时从 archive 读取
- 更新 profile_archive/ 即自动生效，无需修改任何代码

用法：
    python sync_profile_archive.py
"""

import os
import sys
import re
import glob
import logging
from datetime import datetime, date

# ======================================================================
# 路径配置
# ======================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HOLDINGS_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "..", "family-hub", "research", "portfolio", "holdings.yaml"))
REPORTS_DIR = os.path.normpath(
    os.path.join(BASE_DIR, "..", "family-hub", "research", "portfolio", "reports"))
CAREER_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "..", "..", "02-Knowledge", "career-development", "career-strategy",
                 "个人职业发展分析-端侧AI企业定制攻略.md"))

HOUR_ARCHIVE_DIR = os.path.normpath(
    os.path.join(BASE_DIR, "0.trae-feishu-push-hour", "profile_archive"))
DAY_ARCHIVE_DIR = os.path.normpath(
    os.path.join(BASE_DIR, "1.trae-feishu-push-day", "profile_archive"))

# ======================================================================
# 日志配置 — 仅异常时输出
# ======================================================================
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sync_profile_archive")


# ======================================================================
# 工具函数
# ======================================================================

def _read_file(path, encoding="utf-8"):
    """安全读取文件，失败返回 None"""
    if not os.path.isfile(path):
        logger.error(f"文件不存在: {path}")
        return None
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件失败 {path}: {e}")
        return None


def _parse_markdown_table_row(line):
    """解析一行 markdown 表格行，返回 cell 列表"""
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return None
    cells = [c.strip() for c in line.split("|")[1:-1]]
    if not cells:
        return None
    # 跳过表头分隔行
    if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
        return None
    return cells


def _parse_table_section(lines, start_idx):
    """
    从 lines[start_idx] 开始解析一个 markdown 表格区块。
    返回 (table_data, end_idx)，其中 table_data = [header, [row1, ...]]
    """
    i = start_idx
    # 跳过空行
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or not lines[i].strip().startswith("|"):
        return None, start_idx

    header = _parse_markdown_table_row(lines[i])
    if not header:
        return None, start_idx
    i += 1

    # 跳过分隔行
    if i < len(lines):
        sep = _parse_markdown_table_row(lines[i])
        if sep:
            i += 1

    rows = []
    while i < len(lines):
        cells = _parse_markdown_table_row(lines[i])
        if cells is None:
            break
        rows.append(cells)
        i += 1

    return {"header": header, "rows": rows}, i


def _find_latest_report():
    """在 reports 目录中按文件名日期排序取最新月度报告"""
    if not os.path.isdir(REPORTS_DIR):
        logger.error(f"报告目录不存在: {REPORTS_DIR}")
        return None

    # 匹配 家庭资产报告-YYYY-MM.md
    pattern = os.path.join(REPORTS_DIR, "家庭资产报告-*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        logger.error(f"未找到月度报告")
        return None
    return files[0]


def _find_previous_profile(archive_dir, today_str):
    """在 archive_dir 中找到上一个日期的 profile 文件"""
    if not os.path.isdir(archive_dir):
        return None
    pattern = os.path.join(archive_dir, "profile_*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    for f in files:
        basename = os.path.basename(f)
        m = re.match(r"profile_(\d{8})\.md", basename)
        if m and m.group(1) < today_str:
            return f
    return None


# ======================================================================
# 数据提取
# ======================================================================

def extract_report_data(report_path):
    """从月度报告中提取投资数据"""
    content = _read_file(report_path)
    if not content:
        return None

    lines = content.split("\n")
    data = {
        "date": "",
        "total_assets": "",
        "net_assets": "",
        "investment_assets": "",
        "cash_family": "",
        "cash_hk": "",
        "cash_usdt": "",
        "cash_hst": "",
        "credit_card_debt": "",
        "mortgage": "",
        "btc_qty": "0.12980465",
        "btc_price": "",
        "btc_market_value": "",
        "milady_price": "",
        "milady_value": "",
        "crcl_price": "",
        "crcl_total_value": "",
        "crcl_concentration": "",
        "crypto_items": [],
        "us_stock_items": [],
        "hk_stock_items": [],
        "a_stock_items": [],
        "ts_token_items": [],
        "btc_status": "",
        "crcl_status": "",
    }

    # 解析报告日期
    for line in lines:
        m = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", line)
        if m:
            data["date"] = m.group(1)
            break

    # 解析各章节
    current_section = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()

        # 资产总览表
        if current_section == "一、资产总览" and stripped.startswith("|"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) == 3:
                    label, amount, _ = cells
                    label_clean = label.replace("**", "").strip()
                    if label_clean == "总资产":
                        data["total_assets"] = amount
                    elif label_clean == "净资产":
                        data["net_assets"] = amount
                    elif label_clean == "投资总资产":
                        data["investment_assets"] = amount
                    elif label_clean == "现金固收":
                        data["cash_family"] = amount

        # 投资资产明细表
        if current_section.startswith("二、投资资产明细"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 9:
                name = cells[0]
                qty = cells[1]
                price = cells[2]
                mkt_val = cells[3]
                storage = cells[8] if len(cells) > 8 else cells[-1]

                if "比特币" in name:
                    data["btc_qty"] = qty
                    data["btc_price"] = price
                    data["btc_market_value"] = mkt_val
                elif "Milady" in name:
                    data["milady_price"] = price
                    data["milady_value"] = mkt_val
                elif "ONDO" in name or "Uniswap" in name:
                    data["crypto_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "CRCL" in name or "Circle" in name:
                    continue  # 单独处理
                elif "DRAM" in name:
                    data["us_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "MicroStrategy" in name:
                    data["us_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "半导体" in name:
                    data["us_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "BitGo" in name:
                    data["us_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "优必选" in name:
                    data["hk_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "小米" in name:
                    data["hk_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "科创50" in name:
                    data["a_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "创新药" in name:
                    data["a_stock_items"].append({
                        "name": name, "qty": qty, "price": price,
                        "mkt_val": mkt_val, "storage": storage
                    })
                elif "小安" in name:
                    data["ts_token_items"].append({
                        "name": name, "qty": qty, "mkt_val": mkt_val
                    })
                elif "午饭" in name:
                    data["ts_token_items"].append({
                        "name": name, "qty": qty, "mkt_val": mkt_val
                    })

        # 按资产统计表 — 提取 CRCL 合计
        if current_section.startswith("三、按资产统计"):
            cells = _parse_markdown_table_row(stripped)
            if cells and cells[0] == "Circle(CRCL)":
                data["crcl_total_value"] = cells[3]
                m = re.search(r"(\d+\.?\d*)%", cells[4] if len(cells) > 4 else "")
                if m:
                    data["crcl_concentration"] = f"{m.group(1)}% ⚠️"

        # 负债表
        if current_section.startswith("四、负债") or current_section == "四、负债":
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                if "信用卡" in cells[0]:
                    data["credit_card_debt"] = cells[1]

        # 现金及固收表
        if current_section.startswith("五、现金及固收"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                if "家庭备用金" in cells[0]:
                    data["cash_family"] = cells[1]
                if "HK打新" in cells[0]:
                    data["cash_hk"] = cells[1]
                if "USDT" in cells[0]:
                    data["cash_usdt"] = cells[1]
                if "华盛通" in cells[0]:
                    data["cash_hst"] = cells[1]

        # 房贷
        if current_section.startswith("七、房贷"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                if "商贷" in cells[0]:
                    m = re.search(r"¥?([\d,]+)", cells[1])
                    if m:
                        data["mortgage"] = data.get("mortgage", "") + f"商贷¥{m.group(1)}"
                if "公积金" in cells[0]:
                    m = re.search(r"¥?([\d,]+)", cells[1])
                    if m:
                        data["mortgage"] = data.get("mortgage", "") + (", " if data.get("mortgage") else "") + f"公积金¥{m.group(1)}"

        # 外部信号看板 — 提取 CRCL 和 BTC 状态
        if current_section.startswith("十一、外部信号"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                if cells[0] == "买卖建议":
                    if "CRCL" in data.get("crcl_status", "") or "CRCL" in current_section:
                        data["crcl_status"] = cells[1]
                    elif "BTC" in data.get("btc_status", "") or "BTC" in current_section:
                        data["btc_status"] = cells[1]

    # 解析 CRCL 看板中的买卖建议
    # 从外部信号看板 section 找 CRCL 和 BTC 的买卖建议
    crcl_found = False
    btc_found = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("### CRCL"):
            crcl_found = True
            btc_found = False
            continue
        if stripped.startswith("### BTC"):
            btc_found = True
            crcl_found = False
            continue
        if stripped.startswith("###"):
            crcl_found = False
            btc_found = False

        if crcl_found and stripped.startswith("|"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                if cells[0] == "买卖建议":
                    data["crcl_status"] = cells[1]
                elif cells[0] == "MA120":
                    data["crcl_ma120"] = cells[1]
                elif cells[0] == "当前价":
                    if not data.get("crcl_price"):
                        data["crcl_price"] = cells[1]

        if btc_found and stripped.startswith("|"):
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                if cells[0] == "买卖建议":
                    data["btc_status"] = cells[1]
                elif cells[0] == "MA120":
                    data["btc_ma120"] = cells[1]
                elif cells[0] == "当前价":
                    if not data.get("btc_price"):
                        data["btc_price"] = cells[1]

    return data


def extract_career_data(career_path):
    """从职业发展档案中提取结构化数据"""
    content = _read_file(career_path)
    if not content:
        return None

    data = {
        "company": "新华三",
        "role": "嵌入式开发工程师",
        "experience": "**~9年**（爱博精电 6年 + 新华三 3年）",
        "skills": "C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM",
        "core_abilities": "自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构",
        "focus": "工业嵌入式、通信设备底层，**非消费电子**",
        "location": "**北京，优先海淀/昌平**（已在海淀买房）",
        "target_salary": "50-70W总包",
        "job_search_status": "已约 1 年，面试过 九号/ISHO/思朗",
        "interview_method": "工程叙事四层结构: 本质→实践→踩坑→思考",
        "target_companies": "小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团",
        "family_location": "北京",
        "hukou": "非京籍 (内蒙古)",
        "children": "有孩子 (在京上学)",
        "spouse": "已婚 (薛燕)",
        "real_estate": "北京海淀住宅 ¥320W (购入2025年底)",
        "mortgage_commercial": "¥400,000",
        "mortgage_fund": "¥1,400,000",
        "hanwei_zhongji": "达尔文50W (¥6,960/年, 2026-06-15生效)",
        "hanwei_dingshou": "待配置 (目标200W保额)",
        "xueyan_zhongji": "待配置 (目标30-50W保额)",
    }

    lines = content.split("\n")

    # 从当前画像表提取数据
    in_profile_table = False
    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "| 维度 | 现状 |":
            in_profile_table = True
            continue
        if stripped.startswith("|---"):
            continue

        if in_profile_table:
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                key = cells[0]
                val = cells[1]
                if key == "总经验":
                    data["experience"] = val
                elif key == "S级能力":
                    data["core_abilities"] = val
                elif key == "技能栈":
                    data["skills"] = val
                elif key == "行业聚焦":
                    data["focus"] = val
                elif key == "地点约束":
                    data["location"] = val
                elif key == "职业路径":
                    pass
            elif not stripped.startswith("|"):
                in_profile_table = False

    # 薪资预期
    for line in lines:
        m = re.search(r'建议范围\s*\*\*¥?([\d,]+)\s*[-~]\s*¥?([\d,]+)W?\*', line)
        if m:
            data["target_salary"] = f"{m.group(1)}-{m.group(2)}W总包"

    # 目标公司
    for i, line in enumerate(lines):
        if "目标公司" in line and "修正版" in line:
            # 读取表格中列出的公司
            for j in range(i, min(i + 30, len(lines))):
                cells = _parse_markdown_table_row(lines[j])
                if cells and len(cells) >= 2:
                    company = cells[0].strip()
                    if company and company not in ("公司", "赛道", "备注"):
                        # 简单过滤有效的公司名
                        if not any(c in company for c in ("|", "---", "公司", "赛道", "为什么")):
                            pass

    return data


# ======================================================================
# 变更记录生成
# ======================================================================

def _parse_previous_profile(prev_path):
    """解析前一天的 profile 归档，提取关键指标做对比"""
    content = _read_file(prev_path)
    if not content:
        return None

    lines = content.split("\n")
    prev = {
        "total_assets": None,
        "net_assets": None,
        "investment_assets": None,
        "crcl_price": None,
        "crcl_concentration": None,
        "btc_price": None,
        "data_source": None,
        "career_file": None,
        "last_sync": None,
        "btc_market_value": None,
        "crcl_total_value": None,
    }

    in_metrics = False
    for line in lines:
        stripped = line.strip()
        if stripped == "### 关键指标":
            in_metrics = True
            continue
        if stripped.startswith("## ") and in_metrics:
            in_metrics = False

        if in_metrics:
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 2:
                key, val = cells[0], cells[1]
                if key == "总资产":
                    prev["total_assets"] = val
                elif key == "净资产":
                    prev["net_assets"] = val
                elif key == "投资总资产":
                    prev["investment_assets"] = val
                elif key == "CRCL集中度":
                    prev["crcl_concentration"] = val
                elif key == "BTC占投资比":
                    pass

        # 从美股表中提取 CRCL 价格
        cells = _parse_markdown_table_row(stripped)
        if cells and len(cells) >= 3 and "Circle(CRCL合计)" in cells[0]:
            prev["crcl_price"] = cells[2]
            prev["crcl_total_value"] = cells[3]
        if cells and len(cells) >= 3 and "比特币" in cells[0]:
            prev["btc_price"] = cells[2]
            prev["btc_market_value"] = cells[3]

    # 从变更记录中提取数据源
    in_changelog = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## 本次更新变更记录":
            in_changelog = True
            continue
        if stripped.startswith("## ") and in_changelog:
            break
        if in_changelog:
            cells = _parse_markdown_table_row(stripped)
            if cells and len(cells) >= 4:
                if cells[0] == "数据源" and "月度报告" in cells[2]:
                    prev["data_source"] = cells[3]
                elif cells[0] == "职业档案":
                    prev["career_file"] = cells[3]
                elif cells[0] == "profile.last_sync":
                    if cells[3] and "每日" in cells[3]:
                        prev["last_sync"] = cells[3].split(" ")[0] if " " in cells[3] else cells[3]

    return prev


def _compute_changes(prev_data, current_data, today_str, report_path):
    """计算变更记录"""
    changes = []
    report_name = os.path.basename(report_path)

    # 基础同步记录
    prev_sync = prev_data.get("last_sync") if prev_data else None
    changes.append(("profile.last_sync", prev_sync or "N/A", today_str, "每日自动归档"))

    # 总资产变动
    if prev_data and prev_data["total_assets"] and current_data.get("total_assets"):
        old_val = prev_data["total_assets"]
        new_val = current_data["total_assets"]

        # 尝试计算差值
        old_num = _extract_number(old_val)
        new_num = _extract_number(new_val)
        if old_num and new_num:
            diff = new_num - old_num
            pct = (diff / old_num * 100) if old_num else 0
            changes.append(("总资产", old_val, new_val,
                           f"{'+'if diff>=0 else ''}{diff:,.0f} ({'+'if pct>=0 else ''}{pct:.1f}%)"))
        else:
            changes.append(("总资产", old_val, new_val, "更新"))

    # 净资产变动
    if prev_data and prev_data["net_assets"] and current_data.get("net_assets"):
        old_val = prev_data["net_assets"]
        new_val = current_data["net_assets"]
        old_num = _extract_number(old_val)
        new_num = _extract_number(new_val)
        if old_num and new_num:
            diff = new_num - old_num
            pct = (diff / old_num * 100) if old_num else 0
            changes.append(("净资产", old_val, new_val,
                           f"{'+'if diff>=0 else ''}{diff:,.0f} ({'+'if pct>=0 else ''}{pct:.1f}%)"))
        else:
            changes.append(("净资产", old_val, new_val, "更新"))

    # 投资总资产变动
    if prev_data and prev_data.get("investment_assets") and current_data.get("investment_assets"):
        changes.append(("投资总资产", prev_data["investment_assets"],
                       current_data["investment_assets"], "更新"))

    # CRCL 价格变动
    if prev_data and prev_data.get("crcl_price") and current_data.get("crcl_price"):
        old_p = prev_data["crcl_price"]
        new_p = current_data["crcl_price"]
        old_num = _extract_number(old_p)
        new_num = _extract_number(new_p)
        if old_num and new_num:
            diff = new_num - old_num
            pct = (diff / old_num * 100) if old_num else 0
            changes.append(("CRCL价格", old_p, new_p,
                           f"{'+'if diff>=0 else ''}{pct:.1f}%"))
        else:
            changes.append(("CRCL价格", old_p, new_p, "更新"))

    # CRCL 集中度变动
    if prev_data and prev_data.get("crcl_concentration") and current_data.get("crcl_concentration"):
        old_c = prev_data["crcl_concentration"]
        new_c = current_data["crcl_concentration"]
        old_num = _extract_number(old_c)
        new_num = _extract_number(new_c)
        if old_num is not None and new_num is not None:
            if new_num > old_num:
                direction = "上升⚠️"
            elif new_num < old_num:
                direction = "下降"
            else:
                direction = "持平"
        else:
            direction = "更新"
        changes.append(("CRCL占比", old_c, new_c, f"集中度{direction}"))

    # BTC 价格变动
    if prev_data and prev_data.get("btc_price") and current_data.get("btc_price"):
        old_p = prev_data["btc_price"]
        new_p = current_data["btc_price"]
        old_num = _extract_number(old_p)
        new_num = _extract_number(new_p)
        if old_num and new_num:
            diff = new_num - old_num
            pct = (diff / old_num * 100) if old_num else 0
            changes.append(("BTC价格", old_p, new_p,
                           f"{'+'if diff>=0 else ''}{pct:.1f}%"))
        else:
            changes.append(("BTC价格", old_p, new_p, "更新"))

    # 数据源
    changes.append(("数据源", prev_data.get("data_source", "N/A") if prev_data else "N/A",
                   report_name, f"更新至{report_name}"))

    # 职业档案
    changes.append(("职业档案",
                   prev_data.get("career_file", "个人职业发展分析-端侧AI企业定制攻略.md") if prev_data else "N/A",
                   "个人职业发展分析-端侧AI企业定制攻略.md", "无变更"))

    return changes


def _extract_number(s):
    """从字符串中提取数值（如 '¥1,334,174' → 1334174.0）"""
    if not s:
        return None
    s = s.replace("**", "").replace("¥", "").replace("$", "").replace("HK$", "")
    s = s.replace(",", "").replace("%", "").strip()
    # 移除 emoji 和其他非数字字符（保留 . 和 -）
    s = re.sub(r'[^\d.\-]', '', s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ======================================================================
# 归档生成
# ======================================================================

def generate_profile(today, report_data, career_data, changes):
    """生成完整 profile markdown 内容"""
    today_str = today.strftime("%Y-%m-%d")
    today_compact = today.strftime("%Y%m%d")

    lines = []
    lines.append(f"# 个人画像归档 - {today_str}")
    lines.append("")

    # =========================================================
    # 投资持仓概览
    # =========================================================
    lines.append("## 投资持仓概览")
    lines.append("")

    # 加密货币
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    btc_name = "比特币(链上)"
    btc_qty = report_data.get("btc_qty", "0.12980465")
    btc_price = report_data.get("btc_price", "-")
    btc_val = report_data.get("btc_market_value", "-")
    lines.append(f"| {btc_name} | {btc_qty} | {btc_price} | {btc_val} | 链上钱包 |")

    milady_price = report_data.get("milady_price", "-")
    milady_val = report_data.get("milady_value", "-")
    lines.append(f"| Milady NFT(链上) | 1个 | {milady_price} | {milady_val} | 链上钱包 |")

    for item in report_data.get("crypto_items", []):
        lines.append(f"| {item['name']} | {item['qty']} | {item['price']} | {item['mkt_val']} | {item['storage']} |")
    lines.append("")

    # 美股
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")

    crcl_total_val = report_data.get("crcl_total_value", "-")
    crcl_price = report_data.get("crcl_price", "-")
    lines.append(f"| Circle(CRCL合计) | 1,008.5 | {crcl_price} | {crcl_total_val} | 分散多账户 |")

    for item in report_data.get("us_stock_items", []):
        lines.append(f"| {item['name']} | {item['qty']} | {item['price']} | {item['mkt_val']} | {item['storage']} |")
    lines.append("")

    # 港股
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")
    for item in report_data.get("hk_stock_items", []):
        lines.append(f"| {item['name']} | {item['qty']} | {item['price']} | {item['mkt_val']} | {item['storage']} |")
    lines.append("")

    # A股
    lines.append("### A股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) | 存放 |")
    lines.append("|------|------|-------|-----------|------|")
    for item in report_data.get("a_stock_items", []):
        lines.append(f"| {item['name']} | {item['qty']} | {item['price']} | {item['mkt_val']} | {item['storage']} |")
    lines.append("")

    # TS时间代币
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")
    for item in report_data.get("ts_token_items", []):
        lines.append(f"| {item['name']} | {item['qty']} | {item['mkt_val']} |")
    lines.append("")

    # 关键指标
    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总资产 | {report_data.get('total_assets', '-')} |")
    lines.append(f"| 净资产 | {report_data.get('net_assets', '-')} |")
    lines.append(f"| 投资总资产 | {report_data.get('investment_assets', '-')} |")
    lines.append(f"| 家庭备用金 | {report_data.get('cash_family', '-')} |")
    lines.append(f"| HK打新资金 | {report_data.get('cash_hk', '-')} |")
    lines.append(f"| USDT余额 | {report_data.get('cash_usdt', '-')} |")
    lines.append(f"| 华盛通现金 | {report_data.get('cash_hst', '-')} |")
    lines.append(f"| 信用卡负债 | {report_data.get('credit_card_debt', '-')} |")
    # BTC占比
    btc_val_num = _extract_number(btc_val)
    invest_val_num = _extract_number(report_data.get("investment_assets", "0"))
    if btc_val_num and invest_val_num and invest_val_num > 0:
        btc_pct = btc_val_num / invest_val_num * 100
        lines.append(f"| BTC占投资比 | {btc_pct:.1f}% |")
    else:
        lines.append(f"| BTC占投资比 | - |")
    # CRCL占比
    crcl_conc = report_data.get("crcl_concentration", "70.7% ⚠️")
    lines.append(f"| CRCL集中度 | {crcl_conc} |")
    lines.append(f"| 房贷总额 | ¥400,000+¥1,400,000 |")
    lines.append("")

    # =========================================================
    # 职业发展画像
    # =========================================================
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 当前公司 | {career_data.get('company', '新华三')} |")
    lines.append(f"| 当前角色 | {career_data.get('role', '嵌入式开发工程师')} |")
    lines.append(f"| 经验 | {career_data.get('experience', '**~9年**（爱博精电 6年 + 新华三 3年）')} |")
    lines.append(f"| 技能栈 | {career_data.get('skills', 'C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM')} |")
    lines.append(f"| 核心能力 | {career_data.get('core_abilities', '自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构')} |")
    lines.append(f"| 行业聚焦 | {career_data.get('focus', '工业嵌入式、通信设备底层，**非消费电子**')} |")
    lines.append(f"| 地点约束 | {career_data.get('location', '**北京，优先海淀/昌平**（已在海淀买房）')} |")
    lines.append(f"| 目标薪资 | {career_data.get('target_salary', '50-70W总包')} |")
    lines.append(f"| 求职状态 | {career_data.get('job_search_status', '已约 1 年，面试过 九号/ISHO/思朗')} |")
    lines.append(f"| 面试方法论 | {career_data.get('interview_method', '工程叙事四层结构: 本质→实践→踩坑→思考')} |")
    lines.append(f"| 目标公司 | {career_data.get('target_companies', '小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团')} |")
    lines.append("")

    # =========================================================
    # 家庭与保险
    # =========================================================
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 居住地 | {career_data.get('family_location', '北京')} |")
    lines.append(f"| 户籍 | {career_data.get('hukou', '非京籍 (内蒙古)')} |")
    lines.append(f"| 子女 | {career_data.get('children', '有孩子 (在京上学)')} |")
    lines.append(f"| 配偶 | {career_data.get('spouse', '已婚 (薛燕)')} |")
    lines.append(f"| 房产 | {career_data.get('real_estate', '北京海淀住宅 ¥320W (购入2025年底)')} |")
    lines.append(f"| 房贷商贷 | ¥400,000 |")
    lines.append(f"| 房贷公积金 | ¥1,400,000 |")
    lines.append(f"| hanwei_zhongji | {career_data.get('hanwei_zhongji', '达尔文50W (¥6,960/年, 2026-06-15生效)')} |")
    lines.append(f"| hanwei_dingshou | {career_data.get('hanwei_dingshou', '待配置 (目标200W保额)')} |")
    lines.append(f"| xueyan_zhongji | {career_data.get('xueyan_zhongji', '待配置 (目标30-50W保额)')} |")
    lines.append("")

    # =========================================================
    # A8计划进度
    # =========================================================
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")

    net_assets_str = report_data.get("net_assets", "¥1,334,174")
    net_assets_num = _extract_number(net_assets_str) or 1334174
    a8_pct = net_assets_num / 10000000 * 100
    lines.append(f"| 目标 | 1000万人民币 (2026-2028) |")
    lines.append(f"| 当前净资产 | {net_assets_str} ({a8_pct:.1f}%) |")

    btc_qty_num = _extract_number(btc_qty) or 0.12980465
    btc_progress = btc_qty_num / 2.32 * 100
    lines.append(f"| BTC目标 | 2.32个 (当前{btc_qty_num:.3f}, 进度{btc_progress:.1f}%) |")
    crcl_conc_pct = _extract_number(report_data.get("crcl_concentration", "70.7%"))
    lines.append(f"| CRCL自持 | 1008股 (目标占比≤20%, 当前{crcl_conc_pct:.1f}%⚠️) |")
    lines.append("| 策略 | MA120趋势 + 月度定投¥16,700 + 港股打新 |")

    # A8 当前状态
    crcl_status = report_data.get("crcl_status", "")
    btc_status = report_data.get("btc_status", "")
    crcl_price_val = report_data.get("crcl_price", "")
    crcl_ma120 = report_data.get("crcl_ma120", "")
    btc_price_val = report_data.get("btc_price", "")
    btc_ma120 = report_data.get("btc_ma120", "")

    status_parts = []
    if crcl_price_val and crcl_ma120:
        cp = _extract_number(crcl_price_val)
        cm = _extract_number(crcl_ma120)
        if cp and cm:
            if cp >= cm:
                status_parts.append(f"CRCL站上MA120(${cm:,.2f}), 已触发启动条件")
            else:
                status_parts.append(f"CRCL在MA120(${cm:,.2f})下方, 等待突破")
        if "观望" in crcl_status or "不买" in crcl_status:
            status_parts.append("看板建议观望")

    if btc_price_val and btc_ma120:
        bp = _extract_number(btc_price_val)
        bm = _extract_number(btc_ma120)
        if bp and bm:
            if bp >= bm:
                status_parts.append(f"BTC在MA120(${bm:,.0f})上方")
            else:
                status_parts.append(f"BTC在MA120(${bm:,.0f})下方")
        if "底部" in btc_status:
            status_parts.append("看板触发底部信号")

    if status_parts:
        lines.append(f"| 当前状态 | {'; '.join(status_parts)} |")
    else:
        lines.append("| 当前状态 | - |")
    lines.append("")

    # =========================================================
    # 本次更新变更记录
    # =========================================================
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    for change in changes:
        # 确保每个值最多一行，避免表格格式错乱
        old_val = str(change[1]).replace("\n", " ")
        new_val = str(change[2]).replace("\n", " ")
        desc = str(change[3]).replace("\n", " ")
        lines.append(f"| {change[0]} | {old_val} | {new_val} | {desc} |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# 主流程
# ======================================================================

def main():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_compact = today.strftime("%Y%m%d")

    # 1. 读取最新月度报告
    report_path = _find_latest_report()
    if not report_path:
        logger.error("无法找到最新月度报告，退出")
        sys.exit(1)
    logger.info(f"数据源: {os.path.basename(report_path)}")

    report_data = extract_report_data(report_path)
    if not report_data:
        logger.error("无法解析月度报告，退出")
        sys.exit(1)

    # 2. 读取职业发展档案
    career_data = extract_career_data(CAREER_PATH)
    if not career_data:
        logger.warning("职业发展档案读取失败，使用默认值")
        career_data = {}

    # 3. 读取上一天的 profile 做对比
    # 优先从小时目录读取
    prev_data = _parse_previous_profile(
        _find_previous_profile(HOUR_ARCHIVE_DIR, today_compact))
    if not prev_data:
        prev_data = _parse_previous_profile(
            _find_previous_profile(DAY_ARCHIVE_DIR, today_compact))

    # 4. 计算变更记录
    changes = _compute_changes(prev_data, report_data, today_str, report_path)

    # 5. 生成归档内容
    profile_content = generate_profile(today, report_data, career_data, changes)

    # 6. 写入两份归档
    hour_path = os.path.join(HOUR_ARCHIVE_DIR, f"profile_{today_compact}.md")
    day_path = os.path.join(DAY_ARCHIVE_DIR, f"profile_{today_compact}.md")

    for d in [HOUR_ARCHIVE_DIR, DAY_ARCHIVE_DIR]:
        os.makedirs(d, exist_ok=True)

    for path, label in [(hour_path, "小时推送"), (day_path, "日报推送")]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(profile_content)
            logger.info(f"已写入 {label} 归档: {os.path.basename(path)}")
        except Exception as e:
            logger.error(f"写入 {label} 归档失败 {path}: {e}")

    logger.info("归档同步完成")


if __name__ == "__main__":
    main()