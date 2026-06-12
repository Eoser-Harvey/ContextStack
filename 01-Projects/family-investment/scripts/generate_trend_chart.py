#!/usr/bin/env python3
"""
从月度资产报告提取数据，生成资产趋势折线图。
数据源: research/portfolio/reports/家庭资产报告-YYYY-MM.md
输出:   research/portfolio/reports/images/asset-trend-2026.png
"""
import re
import os
import sys
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# 解决中文字体问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / 'research' / 'portfolio' / 'reports'
OUTPUT_DIR = REPORTS_DIR / 'images'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 需要从表格中提取的资产类别（按报告中的名称）
ASSET_KEYS = ['加密货币', '美股(链上)', '美股', '港股', 'A股',
              'TS时间代币', '现金固收', '总资产', '净资产']


def parse_report(filepath):
    """解析单份月度报告的资产总览表格，返回 {date: {类别: 金额}}"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取日期（从 yaml frontmatter 或标题）
    date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
    if not date_match:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
    if not date_match:
        return None, None
    date_str = date_match.group(1)

    # 定位"一、资产总览"表格
    # 表格格式: | 类别 | 金额(CNY) | 占比 |
    # 提取含有 ¥ 符号的行
    result = {}
    in_section = False
    for line in content.split('\n'):
        # 定位到资产总览章节
        if '一、资产总览' in line or '资产总览' in line:
            in_section = True
            continue
        # 遇到下一个章节则退出
        if in_section and re.match(r'^##\s', line):
            break
        if not in_section:
            continue
        # 解析表格行: | 类别 | ¥xxx | xx% |
        match = re.match(r'\|\s*(.+?)\s*\|\s*¥?([\d,]+(?:\.\d+)?)\s*\|', line)
        if match:
            name = match.group(1).strip()
            amount = float(match.group(2).replace(',', ''))
            result[name] = amount

    return date_str[:7], result  # 返回 2026-05 格式


def main():
    # 收集所有报告数据
    all_dates = []
    all_data = {}  # {类别: [按月份排列的金额列表]}

    for filepath in sorted(REPORTS_DIR.glob('家庭资产报告-*.md')):
        month, data = parse_report(filepath)
        if month is None:
            continue
        print(f'  ✓ {month} ({filepath.name})')
        all_dates.append(month)
        for key in ASSET_KEYS:
            if key not in all_data:
                all_data[key] = []
            all_data[key].append(data.get(key))

    if len(all_dates) < 2:
        print('  ⚠️ 至少需要 2 期报告才能绘制趋势图')
        sys.exit(0)

    # 绘图
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = {
        '加密货币': '#F7931A', '美股(链上)': '#2196F3', '美股': '#1565C0',
        '港股': '#E53935', 'A股': '#D32F2F', 'TS时间代币': '#7B1FA2',
        '现金固收': '#4CAF50', '总资产': '#757575', '净资产': '#000000'
    }

    for key in ASSET_KEYS:
        if key not in all_data or len(all_data[key]) < 2:
            continue
        vals = all_data[key]
        # 过滤 None（该月不存在此类别）
        plot_dates = [d for d, v in zip(all_dates, vals) if v is not None]
        plot_vals = [v for v in vals if v is not None]
        if len(plot_vals) < 2:
            continue

        color = colors.get(key, '#999999')
        lw = 2.5 if key == '净资产' else 1.8
        style = '-' if key == '净资产' else '-'
        alpha = 1.0 if key in ('净资产', '总资产', '现金固收', '加密货币') else 0.7

        ax.plot(plot_dates, plot_vals, style, linewidth=lw,
                color=color, label=key, alpha=alpha, marker='o', markersize=5)

        # 在数据点上标注具体金额
        if key in ('净资产', '总资产', '现金固收', '加密货币'):
            for x, y in zip(plot_dates, plot_vals):
                offset = 15 if key == '净资产' else 10
                ax.annotate(f'{y/10000:.1f}万', (x, y),
                            textcoords='offset points', xytext=(0, offset),
                            fontsize=7, color=color, ha='center', alpha=0.85)

    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('资产值 (CNY)', fontsize=12)
    ax.set_title('家庭资产月度趋势 (2026)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f'{x/10000:.0f}万' if x >= 10000 else f'{x:.0f}'))

    plt.tight_layout()
    output_path = OUTPUT_DIR / 'asset-trend-2026.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'\n  ✅ 趋势图已保存: {output_path}')


if __name__ == '__main__':
    print('正在生成资产趋势图...')
    main()
