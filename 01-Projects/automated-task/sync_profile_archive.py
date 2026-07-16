"""
每日 0:00 个人画像归档同步脚本

从 holdings.yaml + 最新月度报告 + 职业发展档案 生成两份归档摘要：
  - 小时推送项目: 0.trae-feishu-push-hour/profile_archive/profile_YYYYMMDD.md
  - 日报推送项目: 1.trae-feishu-push-day/profile_archive/profile_YYYYMMDD.md

架构说明：
  - profile_loader.py 按文件名日期排序取最新文件
  - analyzer.py / send_daily_ai_news.py / push_lark.py 均使用 load_latest_profile() 动态加载
  - 更新 profile_archive/ 即自动生效，无需修改任何代码

用法：
  python sync_profile_archive.py          # 正常执行
  python sync_profile_archive.py --dry    # 仅打印不写入文件
  python sync_profile_archive.py --date 20260717  # 指定日期

作者: AI Assistant
日期: 2026-07-17
"""

import os
import re
import sys
import yaml
import glob
from datetime import datetime, date
from pathlib import Path

# ======================================================================
# 路径常量
# ======================================================================

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HOLDINGS_PATH = os.path.join(PROJECT_ROOT, "01-Projects", "family-hub", "research", "portfolio", "holdings.yaml")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "01-Projects", "family-hub", "research", "portfolio", "reports")
CAREER_PATH = os.path.join(PROJECT_ROOT, "02-Knowledge", "career-development", "career-strategy",
                           "个人职业发展分析-端侧AI企业定制攻略.md")

HOUR_ARCHIVE_DIR = os.path.join(PROJECT_ROOT, "01-Projects", "automated-task", "0.trae-feishu-push-hour", "profile_archive")
DAY_ARCHIVE_DIR = os.path.join(PROJECT_ROOT, "01-Projects", "automated-task", "1.trae-feishu-push-day", "profile_archive")

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_profile_archive.log")


# ======================================================================
# 日志
# ======================================================================

def log(msg, level="INFO"):
    """写入日志文件（带时间戳），同时打印到 stdout"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {timestamp} - {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except IOError:
        pass  # 日志写入失败不阻断主流程


# ======================================================================
# 读取源文件
# ======================================================================

def load_holdings():
    """读取 holdings.yaml，返回 raw dict"""
    if not os.path.isfile(HOLDINGS_PATH):
        raise FileNotFoundError(f"holdings.yaml 不存在: {HOLDINGS_PATH}")
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def get_latest_report():
    """从 reports/ 目录读取最新月份报告，返回 (filename, content)"""
    if not os.path.isdir(REPORTS_DIR):
        raise FileNotFoundError(f"reports 目录不存在: {REPORTS_DIR}")

    files = sorted(glob.glob(os.path.join(REPORTS_DIR, "家庭资产报告-*.md")), reverse=True)
    if not files:
        raise FileNotFoundError("未找到月度报告文件")

    latest = files[0]
    with open(latest, "r", encoding="utf-8") as f:
        content = f.read()
    return os.path.basename(latest), content


def load_career_doc():
    """读取职业发展档案，返回文本内容"""
    if not os.path.isfile(CAREER_PATH):
        raise FileNotFoundError(f"职业发展档案不存在: {CAREER_PATH}")
    with open(CAREER_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_previous_profile(archive_dir):
    """读取前一天的归档（用于保留家庭/保险等静态信息）"""
    files = sorted(glob.glob(os.path.join(archive_dir, "profile_*.md")), reverse=True)
    if not files:
        return None
    with open(files[0], "r", encoding="utf-8") as f:
        return f.read()


# ======================================================================
# 解析函数
# ======================================================================

def parse_markdown_section(content, section_title):
    """从 markdown 文本中提取指定 ## 节的内容，返回 {key: value} 表格映射"""
    result = {}
    # 找到 ## 节标题
    pattern = rf'^##\s*{re.escape(section_title)}\s*$'
    lines = content.split('\n')
    in_section = False
    in_subsection = False
    table_started = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(pattern, stripped):
            in_section = True
            continue

        if in_section:
            # 遇到下一个 ## 则退出
            if stripped.startswith("## ") and not stripped.startswith("### "):
                break

            # 解析表格行
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]

                # 跳过表头分隔行
                if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                    continue

                # 跳过表头行（第一行数据）
                if len(cells) == 2 and cells[0] in ("维度", "项目", "指标", "标的"):
                    continue

                if len(cells) >= 2:
                    key = cells[0]
                    value = " | ".join(cells[1:])
                    result[key] = value

    return result


def extract_family_insurance(prev_profile_content):
    """从上一份归档中提取家庭与保险数据"""
    result = {}
    if not prev_profile_content:
        return result

    lines = prev_profile_content.split('\n')
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## 家庭与保险":
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## ") and not stripped.startswith("### "):
                break
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                    continue
                if len(cells) >= 2 and cells[0] not in ("项目",):
                    result[cells[0]] = cells[1] if len(cells) == 2 else " | ".join(cells[1:])
    return result


def extract_a8_plan(prev_profile_content):
    """从上一份归档中提取 A8 计划进度"""
    result = {}
    if not prev_profile_content:
        return result

    lines = prev_profile_content.split('\n')
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## A8计划进度":
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## ") and not stripped.startswith("### "):
                break
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                    continue
                if len(cells) >= 2 and cells[0] not in ("指标",):
                    result[cells[0]] = cells[1] if len(cells) == 2 else " | ".join(cells[1:])
    return result


# ======================================================================
# 数值计算
# ======================================================================

def calculate_values(holdings):
    """从 holdings.yaml 计算归档所需的各项数值"""
    usd_cny = holdings.get("meta", {}).get("usd_cny", 6.773)
    hkd_cny = holdings.get("meta", {}).get("hkd_cny", 0.864)

    # 加密货币
    btc_qty = 0
    btc_price = 0
    usdt_amt = 0
    for h in holdings.get("holdings", []):
        if h["id"] == "btc_onchain":
            btc_qty = h["quantity"]
            btc_price = h.get("manual_price_usd", 0)
        if h["symbol"] == "BTC":
            btc_price = h.get("manual_price_usd", btc_price)

    # USDT from cash
    for c in holdings.get("cash", []):
        if "USDT" in c.get("name", "") or "币安" in c.get("name", ""):
            usdt_amt = c.get("amount_usd", 0)

    # 估值
    btc_value_cny = btc_qty * btc_price * usd_cny if btc_price > 0 else 0
    usdt_value_cny = usdt_amt * usd_cny

    # CRCL 汇总
    crcl_holdings = [h for h in holdings.get("holdings", []) if h["symbol"] == "CRCL"]
    crcl_total_qty = sum(h["quantity"] for h in crcl_holdings)
    crcl_price = crcl_holdings[0].get("manual_price_usd", 0) if crcl_holdings else 0
    crcl_value_cny = crcl_total_qty * crcl_price * usd_cny if crcl_price > 0 else 0

    # 其他美股
    dram = [h for h in holdings.get("holdings", []) if h["id"] == "dram_binance"]
    mrvi = [h for h in holdings.get("holdings", []) if h["id"] == "mrvl_han"]
    btgo = [h for h in holdings.get("holdings", []) if h["id"] == "bitgo"]

    dram_qty = dram[0]["quantity"] if dram else 0
    dram_price = dram[0].get("manual_price_usd", 0) if dram else 0
    dram_value_cny = dram_qty * dram_price * usd_cny if dram_price > 0 else 0

    mrvi_qty = mrvi[0]["quantity"] if mrvi else 0
    mrvi_price = mrvi[0].get("manual_price_usd", 0) if mrvi else 0
    mrvi_value_cny = mrvi_qty * mrvi_price * usd_cny if mrvi_price > 0 else 0

    btgo_qty = btgo[0]["quantity"] if btgo else 0
    btgo_price = btgo[0].get("manual_price_usd", 0) if btgo else 0
    btgo_value_cny = btgo_qty * btgo_price * usd_cny if btgo_price > 0 else 0

    # 港股
    ubt = [h for h in holdings.get("holdings", []) if h["id"] == "ubt_ht"]
    ubt_qty = ubt[0]["quantity"] if ubt else 0
    ubt_price = ubt[0].get("manual_price_usd", 0) if ubt else 0
    ubt_value_cny = ubt_qty * ubt_price * usd_cny if ubt_price > 0 else 0

    # TS 时间代币
    xiaoan = [h for h in holdings.get("holdings", []) if h["id"] == "ts_xiaoan"]
    wufan = [h for h in holdings.get("holdings", []) if h["id"] == "ts_wufan"]
    xiaoan_qty = xiaoan[0]["quantity"] if xiaoan else 0
    xiaoan_price = xiaoan[0].get("manual_price_usd", 0) if xiaoan else 0
    xiaoan_value_cny = xiaoan_qty * xiaoan_price * usd_cny if xiaoan_price > 0 else 0
    wufan_qty = wufan[0]["quantity"] if wufan else 0
    wufan_price = wufan[0].get("manual_price_usd", 0) if wufan else 0
    wufan_value_cny = wufan_qty * wufan_price * usd_cny if wufan_price > 0 else 0

    # 现金
    cash_cny = 0
    hk_cash = 0
    for c in holdings.get("cash", []):
        if "备用金" in c.get("name", "") or "活期" in c.get("name", ""):
            cash_cny = c.get("amount_cny", 0)
        if "打新" in c.get("name", ""):
            hk_cash = c.get("amount_hkd", 0)

    # 负债
    credit_card = 0
    mortgage_commercial = 0
    mortgage_fund = 0
    for lb in holdings.get("liabilities", []):
        if "商贷" in lb.get("name", ""):
            mortgage_commercial = lb.get("amount_cny", 0)
        if "公积金" in lb.get("name", ""):
            mortgage_fund = lb.get("amount_cny", 0)
        if "信用卡" in lb.get("name", ""):
            credit_card = lb.get("amount_cny", 0)

    # 房产
    house_value = 0
    for fa in holdings.get("fixed_assets", []):
        if "海淀" in fa.get("name", ""):
            house_value = fa.get("value_cny", 0)

    # 投资总资产 = 加密货币 + 美股 + 港股 + TS
    investment_total = (btc_value_cny + usdt_value_cny + crcl_value_cny +
                        dram_value_cny + mrvi_value_cny + btgo_value_cny +
                        ubt_value_cny + xiaoan_value_cny + wufan_value_cny)

    # 总资产 = 投资 + 现金（不含房产，与月度报告一致）
    hk_cash_cny = hk_cash * hkd_cny
    total_assets = investment_total + cash_cny + hk_cash_cny
    net_assets = total_assets - credit_card

    return {
        "usd_cny": usd_cny,
        "hkd_cny": hkd_cny,
        "btc_qty": btc_qty,
        "btc_price": btc_price,
        "btc_value_cny": btc_value_cny,
        "usdt_amt": usdt_amt,
        "usdt_value_cny": usdt_value_cny,
        "crcl_total_qty": crcl_total_qty,
        "crcl_price": crcl_price,
        "crcl_value_cny": crcl_value_cny,
        "dram_qty": dram_qty,
        "dram_price": dram_price,
        "dram_value_cny": dram_value_cny,
        "mrvi_qty": mrvi_qty,
        "mrvi_price": mrvi_price,
        "mrvi_value_cny": mrvi_value_cny,
        "btgo_qty": btgo_qty,
        "btgo_price": btgo_price,
        "btgo_value_cny": btgo_value_cny,
        "ubt_qty": ubt_qty,
        "ubt_price": ubt_price,
        "ubt_value_cny": ubt_value_cny,
        "xiaoan_qty": xiaoan_qty,
        "xiaoan_price": xiaoan_price,
        "xiaoan_value_cny": xiaoan_value_cny,
        "wufan_qty": wufan_qty,
        "wufan_price": wufan_price,
        "wufan_value_cny": wufan_value_cny,
        "cash_cny": cash_cny,
        "hk_cash": hk_cash,
        "hk_cash_cny": hk_cash_cny,
        "credit_card": credit_card,
        "mortgage_commercial": mortgage_commercial,
        "mortgage_fund": mortgage_fund,
        "house_value": house_value,
        "investment_total": investment_total,
        "total_assets": total_assets,
        "net_assets": net_assets,
    }


def format_cny(value):
    """格式化 CNY 数值，如 ¥1,234,567"""
    return f"¥{value:,.0f}"


def format_usd(value):
    """格式化 USD 数值，如 $12,345"""
    return f"${value:,.2f}" if value >= 1 else f"${value:.6f}"


# ======================================================================
# 归档生成
# ======================================================================

def generate_profile(values, family_data, a8_data, career_filepath, report_filename, today_str):
    """生成个人画像归档 markdown 内容"""

    lines = []
    lines.append(f"# 个人画像归档 - {today_str[:4]}-{today_str[4:6]}-{today_str[6:]}")
    lines.append("")
    lines.append("## 投资持仓概览")
    lines.append("")

    # --- 加密货币 ---
    lines.append("### 加密货币")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    lines.append(f"| BTC(链上) | {values['btc_qty']} | {format_usd(values['btc_price'])} | {format_cny(values['btc_value_cny'])} | 链上钱包 |")
    lines.append(f"| USDT(币安) | — | — | ${values['usdt_amt']:,.0f} | 韩伟蒙古币安 |")
    lines.append("| ETH | — | — | — | 已清仓 (2026-06-24) |")
    lines.append("")

    # --- 美股 ---
    lines.append("### 美股")
    lines.append("| 标的 | 数量 | 当前价(USD) | 市值(CNY) | 存放 |")
    lines.append("|------|------|------------|-----------|------|")
    lines.append(f"| Circle(CRCL合计) | {values['crcl_total_qty']:.1f} | {format_usd(values['crcl_price'])} | {format_cny(values['crcl_value_cny'])} | 分散多账户 |")
    lines.append(f"| DRAM(韩伟币安) | {values['dram_qty']} | {format_usd(values['dram_price'])} | {format_cny(values['dram_value_cny'])} | 韩伟蒙古币安 |")
    lines.append(f"| 迈威尔(币安) | {values['mrvi_qty']:.3f} | {format_usd(values['mrvi_price'])} | {format_cny(values['mrvi_value_cny'])} | 韩伟蒙古币安 |")
    lines.append(f"| BitGo(韩伟长桥) | {values['btgo_qty']} | {format_usd(values['btgo_price'])} | {format_cny(values['btgo_value_cny'])} | 韩伟长桥证券 |")
    lines.append("")

    # --- 港股 ---
    lines.append("### 港股")
    lines.append("| 标的 | 数量 | 当前价 | 市值(CNY) |")
    lines.append("|------|------|-------|-----------|")
    lines.append(f"| 优必选 | {values['ubt_qty']} | {format_usd(values['ubt_price'])} | {format_cny(values['ubt_value_cny'])} |")
    lines.append("")

    # --- TS 时间代币 ---
    lines.append("### TS时间代币")
    lines.append("| 标的 | 数量 | 市值(CNY) |")
    lines.append("|------|------|-----------|")
    lines.append(f"| xiaoan | {values['xiaoan_qty']:,}秒 | {format_cny(values['xiaoan_value_cny'])} |")
    lines.append(f"| wufan | {values['wufan_qty']}秒 | {format_cny(values['wufan_value_cny'])} |")
    lines.append("")

    # --- 关键指标 ---
    crcl_concentration = (values['crcl_value_cny'] / values['investment_total'] * 100) if values['investment_total'] > 0 else 0
    btc_ratio = (values['btc_value_cny'] / values['investment_total'] * 100) if values['investment_total'] > 0 else 0

    lines.append("### 关键指标")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总资产 | {format_cny(values['total_assets'])} |")
    lines.append(f"| 净资产 | {format_cny(values['net_assets'])} |")
    lines.append(f"| 投资总资产 | {format_cny(values['investment_total'])} |")
    lines.append(f"| 家庭备用金 | {format_cny(values['cash_cny'])} |")
    lines.append(f"| HK打新资金 | HK${values['hk_cash']:,.0f} (≈{format_cny(values['hk_cash_cny'])}) |")
    lines.append(f"| 信用卡负债 | {format_cny(values['credit_card'])} |")
    lines.append(f"| BTC占投资比 | {btc_ratio:.1f}% |")
    lines.append(f"| CRCL集中度 | {crcl_concentration:.1f}% {'⚠️' if crcl_concentration > 20 else ''} |")
    lines.append(f"| 房贷总额 | {format_cny(values['mortgage_commercial'])}+{format_cny(values['mortgage_fund'])} |")
    lines.append("")

    # --- 职业发展画像 ---
    lines.append("## 职业发展画像")
    lines.append("")
    lines.append("| 维度 | 内容 |")
    lines.append("|------|------|")
    lines.append("| 当前公司 | 新华三 |")
    lines.append("| 当前角色 | 嵌入式开发工程师 |")
    lines.append("| 经验 | **~9年**（爱博精电 6年 + 新华三 3年） |")
    lines.append("| 技能栈 | C语言、ARM/DSP架构、RTOS、Linux、Python、TFLM |")
    lines.append("| 核心能力 | 自研RTOS、TSN全协议栈、DSP汇编优化、AMP异构架构 |")
    lines.append("| 行业聚焦 | 工业嵌入式、通信设备底层，**非消费电子** |")
    lines.append("| 地点约束 | **北京，优先海淀/昌平**（已在海淀买房） |")
    lines.append("| 目标薪资 | 50-70W总包 |")
    lines.append("| 求职状态 | 已约 1 年，面试过 九号/ISHO/思朗 |")
    lines.append("| 面试方法论 | 工程叙事四层结构: 本质→实践→踩坑→思考 |")
    lines.append("| 目标公司 | 小米、地平线、寒武纪、百度、字节跳动、联想、滴滴、三一重工、北汽新能源、京东方、理想汽车、石头科技、美团 |")
    lines.append("")

    # --- 家庭与保险 ---
    lines.append("## 家庭与保险")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    # 保留上一份归档中的家庭与保险数据
    for key in ("居住地", "户籍", "子女", "配偶", "房产", "hanwei_zhongji", "hanwei_dingshou", "xueyan_zhongji"):
        val = family_data.get(key, "")
        # 如果 key 包含 "待配置" 或为空，也写入
        if not val:
            # 检查是否有默认值
            defaults = {
                "居住地": "北京",
                "户籍": "非京籍 (内蒙古)",
                "子女": "有孩子 (在京上学)",
                "配偶": "已婚 (薛燕)",
                "房产": f"北京海淀住宅 ¥320W (购入2025年底)",
                "hanwei_dingshou": "待配置 (目标200W保额)",
                "xueyan_zhongji": "待配置 (目标30-50W保额)",
            }
            val = defaults.get(key, "")
        lines.append(f"| {key} | {val} |")
    lines.append("")

    # --- A8 计划进度 ---
    lines.append("## A8计划进度")
    lines.append("")
    lines.append("| 指标 | 进度 |")
    lines.append("|------|------|")
    for key in ("目标", "BTC目标", "策略", "当前状态"):
        val = a8_data.get(key, "")
        if not val:
            defaults = {
                "目标": "1000万人民币 (2026-2028)",
                "BTC目标": f"2.32个 (当前{values['btc_qty']:.3f}, 进度{values['btc_qty']/2.32*100:.1f}%)",
                "策略": "MA120趋势 + 月度定投¥16,700 + 港股打新",
                "当前状态": "BTC在MA120下方, 定投暂存USDT待命",
            }
            val = defaults.get(key, "")
        lines.append(f"| {key} | {val} |")
    lines.append("")

    # --- 本次更新变更记录 ---
    lines.append("## 本次更新变更记录")
    lines.append("")
    lines.append("| 变更项 | 旧值 | 新值 | 说明 |")
    lines.append("|--------|------|------|------|")
    lines.append(f"| profile.last_sync | — | {today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T00:00:00 | 自动归档 |")
    lines.append("| 数据源 | holdings.yaml | holdings.yaml | 持仓同步 |")
    lines.append(f"| 数据源 | 月度报告 | {report_filename} | 报告同步 |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# 写入
# ======================================================================

def write_profile(archive_dir, filename, content, dry_run=False):
    """写入归档文件，返回写入路径"""
    os.makedirs(archive_dir, exist_ok=True)
    filepath = os.path.join(archive_dir, filename)

    if dry_run:
        print(f"[DRY] 将写入: {filepath}")
        return filepath

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] 已写入: {filepath}")
    return filepath


# ======================================================================
# 主流程
# ======================================================================

def main():
    # 解析命令行参数
    dry_run = "--dry" in sys.argv
    date_arg = None
    for arg in sys.argv:
        if arg.startswith("--date="):
            date_arg = arg.split("=", 1)[1]

    today_str = date_arg or datetime.now().strftime("%Y%m%d")
    profile_filename = f"profile_{today_str}.md"

    log(f"开始同步个人画像归档 [{today_str}]" + (" [DRY RUN]" if dry_run else ""))

    try:
        # 1. 读取投资持仓
        log("读取 holdings.yaml...")
        holdings = load_holdings()
        log(f"   holdings.yaml 加载成功, 最新更新: {holdings.get('meta', {}).get('last_updated', 'unknown')}")

        # 2. 读取最新月度报告
        log("读取最新月度报告...")
        report_filename, report_content = get_latest_report()
        log(f"   最新报告: {report_filename}")

        # 3. 读取职业发展档案
        log("读取职业发展档案...")
        career_content = load_career_doc()
        log(f"   职业发展档案加载成功 ({len(career_content)} 字符)")

        # 4. 读取上一份归档（用于保留静态数据）
        log("读取上一份归档...")
        prev_profile = load_previous_profile(HOUR_ARCHIVE_DIR)
        if prev_profile:
            log(f"   上一份归档加载成功")
        else:
            log("   未找到上一份归档，将使用默认值", "WARN")

        # 解析家庭/保险和 A8 数据
        family_data = extract_family_insurance(prev_profile) if prev_profile else {}
        a8_data = extract_a8_plan(prev_profile) if prev_profile else {}

        # 5. 计算数值
        log("计算持仓数值...")
        values = calculate_values(holdings)
        log(f"   总资产: {format_cny(values['total_assets'])}, 净资产: {format_cny(values['net_assets'])}")

        # 6. 生成归档内容
        log("生成归档内容...")
        profile_content = generate_profile(
            values=values,
            family_data=family_data,
            a8_data=a8_data,
            career_filepath=CAREER_PATH,
            report_filename=report_filename,
            today_str=today_str,
        )
        log(f"   归档内容生成完毕 ({len(profile_content)} 字符)")

        # 7. 写入两份归档
        hour_path = write_profile(HOUR_ARCHIVE_DIR, profile_filename, profile_content, dry_run)
        day_path = write_profile(DAY_ARCHIVE_DIR, profile_filename, profile_content, dry_run)

        log(f"个人画像归档同步完成 [{today_str}]")
        log(f"  小时推送: {hour_path}")
        log(f"  日报推送: {day_path}")

    except Exception as e:
        log(f"同步失败: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())