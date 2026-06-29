#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profile Sync Script
每天0点执行：读取最新投资持仓和职业发展档案，更新到飞书推送系统的config.yaml中
静默完成，异常时记录日志
"""

import yaml
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = Path(r"E:\ProjectGroup\AI\ContextStack")
HOLDINGS_PATH = BASE_DIR / "01-Projects" / "family-investment" / "research" / "portfolio" / "holdings.yaml"
REPORTS_DIR = BASE_DIR / "01-Projects" / "family-investment" / "research" / "portfolio" / "reports"
CAREER_PATH = BASE_DIR / "02-Knowledge" / "career-development" / "career-strategy" / "个人职业发展分析-端侧AI企业定制攻略.md"
CONFIG_PATH = BASE_DIR / "02-Knowledge" / "skills" / "1.trae-feishu-push" / "config.yaml"
HOUR_ARCHIVE_DIR = BASE_DIR / "01-Projects" / "automated task" / "0.trae-feishu-push-hour" / "profile_archive"
DAY_ARCHIVE_DIR = BASE_DIR / "01-Projects" / "automated task" / "1.trae-feishu-push-day" / "profile_archive"
LOG_DIR = BASE_DIR / "01-Projects" / "automated task" / "logs"

# ============================================================
# 日志配置
# ============================================================
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"sync_profile_{datetime.now().strftime('%Y%m%d')}.log"

# 同时输出到文件和控制台
import logging
logger = logging.getLogger("sync_profile")
logger.setLevel(logging.INFO)

fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

# ============================================================
# 工具函数
# ============================================================
def read_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """读取YAML文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"读取YAML失败 [{path}]: {e}")
        return None

def write_yaml(path: Path, data: Dict[str, Any]) -> bool:
    """写入YAML文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"写入YAML失败 [{path}]: {e}")
        return False

def read_text(path: Path) -> str:
    """读取文本文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文本失败 [{path}]: {e}")
        return ""

def find_latest_report(directory: Path) -> Optional[Path]:
    """查找最新的月度报告文件"""
    try:
        pattern = re.compile(r'家庭资产报告-(\d{4})-(\d{2})\.md')
        candidates = []
        for f in directory.iterdir():
            if f.is_file():
                m = pattern.match(f.name)
                if m:
                    year, month = int(m.group(1)), int(m.group(2))
                    candidates.append((year, month, f))
        if not candidates:
            logger.warning(f"未找到月度报告文件: {directory}")
            return None
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        logger.info(f"找到最新月度报告: {candidates[0][2].name}")
        return candidates[0][2]
    except Exception as e:
        logger.error(f"查找最新报告失败: {e}")
        return None

def extract_markdown_table(text: str, table_name: str) -> List[Dict[str, str]]:
    """从Markdown文本中提取表格数据"""
    lines = text.split('\n')
    tables = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|') and '---' in line and ':' not in line.replace('-', '').replace('|', '').strip():
            # 找到分隔行，往前是表头
            if i > 0:
                header_line = lines[i-1].strip()
                headers = [h.strip() for h in header_line.split('|') if h.strip()]
                rows = []
                j = i + 1
                while j < len(lines):
                    row_line = lines[j].strip()
                    if not row_line.startswith('|'):
                        break
                    cells = [c.strip() for c in row_line.split('|')]
                    cells = [c for c in cells if c]
                    if len(cells) >= len(headers):
                        row = {}
                        for idx, h in enumerate(headers):
                            row[h] = cells[idx] if idx < len(cells) else ""
                        rows.append(row)
                    j += 1
                tables.append((headers, rows))
                i = j - 1
        i += 1
    return tables

def get_nested(data: Dict, *keys, default=None):
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

def calc_crcl_total(holdings_data: Dict) -> float:
    """计算CRCL总持仓"""
    total = 0.0
    for item in holdings_data.get('holdings', []):
        if item.get('symbol') == 'CRCL':
            total += float(item.get('quantity', 0))
    return total

def calc_total_investment_value(holdings_data: Dict, usd_cny: float, hkd_cny: float) -> float:
    """估算投资资产总价值(CNY)"""
    total = 0.0
    for item in holdings_data.get('holdings', []):
        qty = float(item.get('quantity', 0))
        # 尝试获取价格
        price = 0
        if 'manual_price_usd' in item:
            price = float(item['manual_price_usd']) * usd_cny
        # 对于其他需要实时价格的，这里简化处理
        # 实际值应从月度报告中获取
        pass
    return total

# ============================================================
# 数据提取
# ============================================================
class ProfileExtractor:
    def __init__(self):
        self.holdings_data = None
        self.report_text = ""
        self.career_text = ""
        self.report_path = None
        self.changes = []  # 记录变更日志

    def load_sources(self) -> bool:
        """加载所有源文件"""
        # 1. 读取holdings.yaml
        self.holdings_data = read_yaml(HOLDINGS_PATH)
        if self.holdings_data is None:
            logger.error("无法加载holdings.yaml，中止")
            return False
        logger.info("已加载 holdings.yaml")

        # 2. 读取最新月度报告
        self.report_path = find_latest_report(REPORTS_DIR)
        if self.report_path:
            self.report_text = read_text(self.report_path)
            logger.info(f"已加载月度报告: {self.report_path.name}")
        else:
            logger.warning("未找到月度报告，将跳过报告数据")

        # 3. 读取职业发展档案
        self.career_text = read_text(CAREER_PATH)
        if self.career_text:
            logger.info("已加载职业发展档案")
        else:
            logger.warning("职业发展档案为空或读取失败")

        return True

    def extract_career(self) -> Dict[str, Any]:
        """从职业发展档案提取career信息"""
        career = {}
        text = self.career_text

        # 公司、角色、经验
        career['company'] = "新华三"
        career['role'] = "嵌入式开发工程师"

        # 从当前画像表格提取经验
        # 文档中: "总经验 | **~9年**（爱博精电 6年 + 新华三 3年）"
        exp_match = re.search(r'总经验\s*\|\s*([^\n|]+)', text)
        if exp_match:
            raw_exp = exp_match.group(1).strip().replace('**', '')
            career['experience'] = f"~3年嵌入式产品开发经验 (新华三), 爱博精电6年工业仪表/DSP基础"
        else:
            career['experience'] = "~3年嵌入式产品开发经验 (新华三), 爱博精电6年工业仪表/DSP基础"

        # 技能
        skills_match = re.search(r'技能栈\s*\|\s*([^\n|]+)', text)
        if skills_match:
            raw_skills = skills_match.group(1).strip()
            # 按逗号分割
            career['skills'] = [s.strip() for s in raw_skills.split('、') if s.strip()]
        else:
            career['skills'] = ["C语言", "Python", "自研RTOS", "TSN全协议栈(802.1Qbv/AS/Qci/Qbu/CB/Qcc)", "DSP汇编优化", "ARM架构", "驱动开发", "TFLM", "PL管理"]

        # 聚焦方向
        focus_match = re.search(r'行业聚焦\s*\|\s*([^\n|]+)', text)
        if focus_match:
            raw_focus = focus_match.group(1).strip().replace('**', '')
            career['focus'] = [f.strip() for f in raw_focus.split('、') if f.strip()]
        else:
            career['focus'] = ["端侧AI", "MCU/RTOS底层驱动", "嵌入式系统", "工业网络"]

        # 薪资
        salary_match = re.search(r'薪资预期.*?(\d+[\d\-W]+)', text)
        if salary_match:
            career['salary'] = f"当前30K×16, 目标{salary_match.group(1)}总包"
        else:
            career['salary'] = "当前30K×16, 目标50-70W总包"

        # 目标公司 - 从表格提取
        target_companies = []
        company_pattern = re.compile(r'\*\*(.*?)\*\*\s*\|')
        for line in text.split('\n'):
            if '|' in line and any(k in line for k in ['小米', '地平线', '寒武纪', '百度', '字节', '联想', '三一', '北汽', '滴滴']):
                m = company_pattern.search(line)
                if m:
                    company = m.group(1).strip()
                    if company and company not in target_companies:
                        target_companies.append(company)
        # 去重并排序，保留优先级
        priority = ["小米", "地平线", "寒武纪", "百度", "字节跳动", "联想", "滴滴", "三一重工", "北汽新能源"]
        sorted_targets = []
        for p in priority:
            for t in target_companies:
                if p in t and p not in sorted_targets:
                    sorted_targets.append(p)
        # 补充未匹配到的
        for p in priority:
            if p not in sorted_targets:
                sorted_targets.append(p)
        career['target_companies'] = sorted_targets[:6] if sorted_targets else ["小米", "地平线", "寒武纪", "百度", "字节跳动", "联想"]

        # 地点约束
        career['location_constraint'] = "北京海淀/昌平"

        # 求职状态
        js_match = re.search(r'求职周期\s*\|\s*([^\n|]+)', text)
        if js_match:
            raw_js = js_match.group(1).strip().replace('**', '').replace('，', ', ')
            career['job_search_status'] = ' '.join(raw_js.split())
        else:
            career['job_search_status'] = "已约1年, 面试过九号/ISHO/思朗"

        career['interview_method'] = "工程叙事四层结构: 本质→实践→踩坑→思考"

        return career

    def extract_assets(self) -> Dict[str, Any]:
        """从holdings.yaml和月度报告提取资产信息"""
        assets = {}
        h = self.holdings_data
        meta = h.get('meta', {})
        usd_cny = float(meta.get('usd_cny', 6.79))
        hkd_cny = float(meta.get('hkd_cny', 0.866))

        # crypto
        btc_qty = 0
        eth_status = "已清仓"
        usdt_balance = 0
        for item in h.get('holdings', []):
            if item.get('id') == 'btc_onchain':
                btc_qty = float(item.get('quantity', 0))
            if item.get('id') == 'eth_onchain':
                eth_status = f"{item.get('quantity', 0)} ETH"
        for c in h.get('cash', []):
            if 'USDT' in c.get('name', ''):
                usdt_balance = float(c.get('amount_usd', 0))

        assets['crypto'] = {
            'btc': f"{btc_qty:.4f} BTC (链上唯一持仓, 币安已清仓)",
            'eth': "已清仓 (2026-06-24)",
            'usdt': f"${usdt_balance:,.0f} (币安余额)"
        }

        # stocks
        crcl_total = 0.0
        mrvl_qty = 0.0
        bitgo_qty = 0.0
        ubt_qty = 0.0
        crcl_accounts = []
        for item in h.get('holdings', []):
            sym = item.get('symbol', '')
            qty = float(item.get('quantity', 0))
            name = item.get('name', '')
            storage = item.get('storage', '')
            if sym == 'CRCL':
                crcl_total += qty
                crcl_accounts.append(f"{storage}{qty:.2f}股")
            elif sym == 'MRVL':
                mrvl_qty = qty
            elif sym == 'BTGO':
                bitgo_qty = qty
            elif sym == '9880.HK':
                ubt_qty = qty

        us_stocks = []
        if crcl_total > 0:
            us_stocks.append(f"CRCL {crcl_total:.1f}股 (分散{len(crcl_accounts)}账户)")
        if mrvl_qty > 0:
            us_stocks.append(f"MRVL {mrvl_qty:.2f}股")
        if bitgo_qty > 0:
            us_stocks.append(f"BitGo {bitgo_qty:.0f}股")

        hk_stocks = []
        if ubt_qty > 0:
            hk_stocks.append(f"优必选 {ubt_qty:.0f}股")

        assets['stocks'] = {
            'us': us_stocks,
            'hk': hk_stocks
        }

        # TS tokens
        xiaoan_qty = 0
        wufan_qty = 0
        xiaoan_price = 0
        wufan_price = 0
        for item in h.get('holdings', []):
            if item.get('id') == 'ts_xiaoan':
                xiaoan_qty = float(item.get('quantity', 0))
                xiaoan_price = float(item.get('manual_price_usd', 0))
            elif item.get('id') == 'ts_wufan':
                wufan_qty = float(item.get('quantity', 0))
                wufan_price = float(item.get('manual_price_usd', 0))

        assets['ts_tokens'] = {
            'xiaoan': f"{xiaoan_qty:,.0f}秒 (≈¥{xiaoan_qty * xiaoan_price * usd_cny:,.0f})",
            'wufan': f"{wufan_qty:,.0f}秒 (≈¥{wufan_qty * wufan_price * usd_cny:,.0f})"
        }

        # real_estate
        real_estate = ""
        for item in h.get('fixed_assets', []):
            if '北京' in item.get('name', ''):
                val = item.get('value_cny', 0)
                real_estate = f"北京海淀住宅 ¥{val/10000:.0f}W (2025年底购入)"
        assets['real_estate'] = real_estate

        # cash
        cash_cny = 0
        cash_hkd = 0
        for c in h.get('cash', []):
            if '家庭备用金' in c.get('name', ''):
                cash_cny = float(c.get('amount_cny', 0))
            elif 'HK打新' in c.get('name', ''):
                cash_hkd = float(c.get('amount_hkd', 0))
        assets['cash'] = f"¥{cash_cny:,.0f} (家庭备用金) + HK${cash_hkd:,.0f} (打新资金) + ${usdt_balance:,.0f} (币安USDT)"

        # 从月度报告提取汇总数据
        total_assets_str = ""
        net_assets_str = ""
        investment_assets_str = ""
        if self.report_text:
            # 总资产
            ta_match = re.search(r'\*\*总资产\*\*\s*\|\s*\*\*([^*]+)\*\*', self.report_text)
            if ta_match:
                total_assets_str = ta_match.group(1).strip()
            # 净资产
            na_match = re.search(r'\*\*净资产\*\*\s*\|\s*\*\*([^*]+)\*\*', self.report_text)
            if na_match:
                net_assets_str = na_match.group(1).strip()
            # 投资合计
            ia_match = re.search(r'\*\*投资合计\*\*\s*\|\s*—\s*\|\s*—\s*\|\s*\*\*([^*]+)\*\*', self.report_text)
            if ia_match:
                investment_assets_str = ia_match.group(1).strip()

        assets['total_assets'] = f"{total_assets_str} (净资产 {net_assets_str})" if total_assets_str else ""
        assets['investment_assets'] = investment_assets_str

        # CRCL集中度 - 从月度报告投资明细表格提取CRCL市值并计算占比
        crcl_concentration_str = ""
        if self.report_text and investment_assets_str:
            # 提取所有CRCL行的市值(CNY)
            crcl_values = []
            for line in self.report_text.split('\n'):
                if 'Circle(' in line and '|' in line:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if len(cells) >= 4:
                        # 尝试提取市值列（通常是第4列，格式如 ¥166,114）
                        for cell in cells:
                            if cell.startswith('¥') and ',' in cell:
                                try:
                                    val = float(cell.replace('¥', '').replace(',', ''))
                                    crcl_values.append(val)
                                    break
                                except ValueError:
                                    continue
            if crcl_values and investment_assets_str:
                total_crcl_value = sum(crcl_values)
                try:
                    inv_total = float(investment_assets_str.replace('¥', '').replace(',', '').replace(' ', ''))
                    if inv_total > 0:
                        ratio = total_crcl_value / inv_total * 100
                        crcl_concentration_str = f"CRCL {crcl_total:.1f}股, 占投资约{ratio:.0f}% ⚠️ 高度集中"
                except ValueError:
                    pass
        if not crcl_concentration_str and crcl_total > 0:
            crcl_concentration_str = f"CRCL {crcl_total:.1f}股 ⚠️ 高度集中"
        assets['crcl_concentration'] = crcl_concentration_str

        return assets

    def extract_liabilities(self) -> Dict[str, str]:
        """从holdings.yaml提取负债信息"""
        liabilities = {}
        h = self.holdings_data
        for item in h.get('liabilities', []):
            name = item.get('name', '')
            if '信用卡' in name:
                liabilities['credit_card_invest'] = f"¥{item.get('amount_cny', 0):,.0f} (投资WEB3)"
            elif '币安' in name:
                liabilities['binance_loan'] = f"¥{item.get('amount_usd', 0):,.0f} (2026-06-05已全部还清)" if item.get('amount_usd', 0) == 0 else f"${item.get('amount_usd', 0):,.0f}"
            elif '商贷' in name:
                liabilities['mortgage_commercial'] = f"¥{item.get('amount_cny', 0):,.0f} (自住)"
            elif '公积金' in name:
                liabilities['mortgage_fund'] = f"¥{item.get('amount_cny', 0):,.0f} (自住)"
        return liabilities

    def extract_family(self) -> Dict[str, str]:
        """从职业发展档案提取家庭信息"""
        family = {}
        text = self.career_text
        family['location'] = "北京"
        family['hukou'] = "非京籍 (内蒙古)"
        family['children'] = "有孩子 (在京上学)"
        family['spouse'] = "已婚 (薛燕)"
        return family

    def extract_insurance(self) -> Dict[str, str]:
        """保险信息（当前无源文件，保持已有值或从config继承）"""
        # 保险信息不在源文件中，返回空让merge逻辑处理
        return {}

    def extract_recent_trades(self) -> List[str]:
        """从月度报告提取近期交易"""
        trades = []
        if not self.report_text:
            return trades

        # 查找"本期持仓变动"部分
        section_match = re.search(r'## 九、本期持仓变动\n\n(.*?)(?=##|\Z)', self.report_text, re.DOTALL)
        if section_match:
            section = section_match.group(1)
            for line in section.split('\n'):
                line = line.strip()
                if line.startswith('|') and not line.startswith('|---') and '标的' not in line:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if len(cells) >= 3:
                        symbol = cells[0]
                        change = cells[1]
                        note = cells[2] if len(cells) > 2 else ""
                        trades.append(f"{symbol}: {change} ({note})")

        # 也尝试从holdings.yaml注释中提取清仓记录
        holdings_text = read_text(HOLDINGS_PATH)
        for line in holdings_text.split('\n'):
            line = line.strip()
            if line.startswith('#') and ('清仓' in line or '买入' in line or '卖出' in line):
                # 提取注释中的交易信息
                clean = line.lstrip('# ').strip()
                if clean and clean not in trades:
                    trades.append(clean)

        # 去重并限制数量
        unique_trades = []
        seen = set()
        for t in trades:
            key = t[:50]
            if key not in seen:
                seen.add(key)
                unique_trades.append(t)
        return unique_trades[:15]

    def extract_risk_profile(self) -> str:
        """生成风险偏好描述"""
        crcl_total = calc_crcl_total(self.holdings_data)
        # 简化计算
        return f"高风险偏好 (加密货币+美股集中持仓, CRCL {crcl_total:.1f}股⚠️)"

    def extract_a8_plan(self) -> Dict[str, str]:
        """从月度报告或holdings提取A8计划信息"""
        a8 = {}
        a8['target'] = "1000万人民币 (2026-2028)"
        # BTC目标
        btc_qty = 0
        for item in self.holdings_data.get('holdings', []):
            if item.get('id') == 'btc_onchain':
                btc_qty = float(item.get('quantity', 0))
        a8['btc_target'] = f"2.32个 (当前{btc_qty:.3f}, 进度{btc_qty/2.32*100:.1f}%)"
        a8['strategy'] = "MA120趋势 + 月度定投¥16,700 + 港股打新"
        a8['current_mode'] = "BTC在MA120下方, 定投暂存USDT待命"
        return a8

    def build_new_profile(self) -> Dict[str, Any]:
        """构建新的profile字典"""
        profile = {}
        profile['name'] = "Harvey"
        profile['career'] = self.extract_career()
        profile['assets'] = self.extract_assets()
        profile['liabilities'] = self.extract_liabilities()
        profile['family'] = self.extract_family()
        profile['insurance'] = self.extract_insurance()
        profile['risk_profile'] = self.extract_risk_profile()
        profile['interests'] = ["加密货币", "端侧AI", "CPO产业链", "投资理财", "职业发展"]
        profile['a8_plan'] = self.extract_a8_plan()
        profile['recent_trades'] = self.extract_recent_trades()
        return profile

    def merge_profile(self, old_profile: Dict, new_profile: Dict) -> Tuple[Dict, List[str]]:
        """对比旧profile和新profile，仅更新变化的字段，返回合并后的profile和变更日志"""
        merged = {}
        changes = []

        for key in new_profile:
            old_val = old_profile.get(key)
            new_val = new_profile[key]

            if isinstance(new_val, dict):
                merged[key] = {}
                old_dict = old_val if isinstance(old_val, dict) else {}
                for sub_key, sub_new in new_val.items():
                    sub_old = old_dict.get(sub_key)
                    if sub_new != sub_old and sub_new:
                        merged[key][sub_key] = sub_new
                        old_repr = str(sub_old)[:60] if sub_old is not None else "(无)"
                        changes.append(f"[{key}.{sub_key}] {old_repr} → {str(sub_new)[:60]}")
                    elif sub_old is not None:
                        merged[key][sub_key] = sub_old
                    else:
                        merged[key][sub_key] = sub_new
                # 保留旧dict中存在但新dict中没有的键
                for sub_key in old_dict:
                    if sub_key not in merged[key]:
                        merged[key][sub_key] = old_dict[sub_key]
            elif isinstance(new_val, list):
                old_list = old_val if isinstance(old_val, list) else []
                if new_val != old_list:
                    merged[key] = new_val
                    changes.append(f"[{key}] 列表更新: {len(old_list)}项 → {len(new_val)}项")
                else:
                    merged[key] = old_list
            else:
                if new_val != old_val and new_val:
                    merged[key] = new_val
                    old_repr = str(old_val)[:60] if old_val is not None else "(无)"
                    changes.append(f"[{key}] {old_repr} → {str(new_val)[:60]}")
                elif old_val is not None:
                    merged[key] = old_val
                else:
                    merged[key] = new_val

        # 保留旧profile中存在但新profile中没有的顶级键
        for key in old_profile:
            if key not in merged:
                merged[key] = old_profile[key]

        return merged, changes

    def generate_archive(self, config_data: Dict, changes: List[str], archive_dir: Path) -> Optional[Path]:
        """生成归档文件"""
        try:
            archive_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime('%Y%m%d')
            archive_path = archive_dir / f"profile_{date_str}.md"

            profile = config_data.get('profile', {})
            assets = profile.get('assets', {})
            career = profile.get('career', {})
            family = profile.get('family', {})
            insurance = profile.get('insurance', {})
            liabilities = profile.get('liabilities', {})

            lines = []
            lines.append(f"---")
            lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
            lines.append(f"source: holdings.yaml + {self.report_path.name if self.report_path else '无报告'} + 职业发展档案")
            lines.append(f"---")
            lines.append("")
            lines.append(f"# 个人画像归档 ({datetime.now().strftime('%Y-%m-%d')})")
            lines.append("")

            # 1. 投资持仓概览
            lines.append("## 一、投资持仓概览")
            lines.append("")
            crypto = assets.get('crypto', {})
            if crypto:
                lines.append("### 加密货币")
                for k, v in crypto.items():
                    lines.append(f"- **{k.upper()}**: {v}")
                lines.append("")
            stocks = assets.get('stocks', {})
            if stocks:
                lines.append("### 股票")
                us = stocks.get('us', [])
                if us:
                    lines.append("**美股:**")
                    for s in us:
                        lines.append(f"- {s}")
                hk = stocks.get('hk', [])
                if hk:
                    lines.append("**港股:**")
                    for s in hk:
                        lines.append(f"- {s}")
                lines.append("")
            ts = assets.get('ts_tokens', {})
            if ts:
                lines.append("### TS时间代币")
                for k, v in ts.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")
            lines.append(f"- **总资产**: {assets.get('total_assets', 'N/A')}")
            lines.append(f"- **投资资产**: {assets.get('investment_assets', 'N/A')}")
            lines.append(f"- **房产**: {assets.get('real_estate', 'N/A')}")
            lines.append(f"- **现金**: {assets.get('cash', 'N/A')}")
            lines.append(f"- **风险集中度**: {assets.get('crcl_concentration', 'N/A')}")
            lines.append("")

            # 2. 职业发展画像
            lines.append("## 二、职业发展画像")
            lines.append("")
            lines.append(f"- **公司**: {career.get('company', 'N/A')}")
            lines.append(f"- **角色**: {career.get('role', 'N/A')}")
            lines.append(f"- **经验**: {career.get('experience', 'N/A')}")
            lines.append(f"- **技能**: {', '.join(career.get('skills', []))}")
            lines.append(f"- **聚焦**: {', '.join(career.get('focus', []))}")
            lines.append(f"- **薪资**: {career.get('salary', 'N/A')}")
            lines.append(f"- **目标公司**: {', '.join(career.get('target_companies', []))}")
            lines.append(f"- **地点约束**: {career.get('location_constraint', 'N/A')}")
            lines.append(f"- **求职状态**: {career.get('job_search_status', 'N/A')}")
            lines.append("")

            # 3. 家庭与保险
            lines.append("## 三、家庭与保险")
            lines.append("")
            lines.append(f"- **家庭所在地**: {family.get('location', 'N/A')}")
            lines.append(f"- **户口**: {family.get('hukou', 'N/A')}")
            lines.append(f"- **子女**: {family.get('children', 'N/A')}")
            lines.append(f"- **配偶**: {family.get('spouse', 'N/A')}")
            lines.append("")
            if insurance:
                lines.append("### 保险配置")
                for k, v in insurance.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")
            if liabilities:
                lines.append("### 负债")
                for k, v in liabilities.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")

            # 4. 本次更新变更记录
            lines.append("## 四、本次更新变更记录")
            lines.append("")
            if changes:
                for c in changes:
                    lines.append(f"- {c}")
            else:
                lines.append("- 无变更")
            lines.append("")

            content = "\n".join(lines)
            with open(archive_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"归档已生成: {archive_path}")
            return archive_path
        except Exception as e:
            logger.error(f"生成归档失败: {e}\n{traceback.format_exc()}")
            return None

# ============================================================
# 主流程
# ============================================================
def main():
    logger.info("=" * 50)
    logger.info("Profile Sync 任务开始")
    logger.info("=" * 50)

    extractor = ProfileExtractor()

    # 1. 加载源文件
    if not extractor.load_sources():
        logger.error("源文件加载失败，任务中止")
        return 1

    # 2. 读取现有config.yaml
    config_data = read_yaml(CONFIG_PATH)
    if config_data is None:
        logger.error(f"无法读取config.yaml，尝试创建新文件")
        config_data = {}

    old_profile = config_data.get('profile', {})

    # 3. 构建新profile
    new_profile = extractor.build_new_profile()

    # 4. 合并（仅更新变化的字段）
    merged_profile, changes = extractor.merge_profile(old_profile, new_profile)

    if changes:
        logger.info(f"检测到 {len(changes)} 处变更:")
        for c in changes:
            logger.info(f"  {c}")
    else:
        logger.info("未检测到变更")

    # 5. 更新config
    config_data['profile'] = merged_profile
    config_data['profile']['last_sync'] = datetime.now().isoformat()

    # 保留其他非profile配置
    if not write_yaml(CONFIG_PATH, config_data):
        logger.error("config.yaml 更新失败")
        return 1
    logger.info(f"config.yaml 已更新，last_sync={config_data['profile']['last_sync']}")

    # 6. 生成归档
    hour_path = extractor.generate_archive(config_data, changes, HOUR_ARCHIVE_DIR)
    day_path = extractor.generate_archive(config_data, changes, DAY_ARCHIVE_DIR)

    if hour_path and day_path:
        logger.info("归档生成完成")
    else:
        logger.warning("部分归档生成失败")

    logger.info("=" * 50)
    logger.info("Profile Sync 任务完成")
    logger.info("=" * 50)
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"未捕获的异常: {e}\n{traceback.format_exc()}")
        sys.exit(1)
