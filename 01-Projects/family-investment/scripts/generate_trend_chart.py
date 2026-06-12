#!/usr/bin/env python3
"""
从月度资产报告提取数据，生成资产趋势图（汇总图 + 每类资产单独子图）。
数据源: research/portfolio/reports/家庭资产报告-YYYY-MM.md
输出:   research/portfolio/reports/images/
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / 'research' / 'portfolio' / 'reports'
OUTPUT_DIR = REPORTS_DIR / 'images'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ASSET_KEYS = ['加密货币', '美股(链上)', '美股', '港股', 'A股',
              'TS时间代币', '现金固收', '总资产', '净资产']

COLORS = {
    '加密货币': '#F7931A', '美股(链上)': '#2196F3', '美股': '#1565C0',
    '港股': '#E53935', 'A股': '#D32F2F', 'TS时间代币': '#7B1FA2',
    '现金固收': '#4CAF50', '总资产': '#757575', '净资产': '#000000'
}


def parse_report(filepath):
    """解析单份月度报告的资产总览表格"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
    if not date_match:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
    if not date_match:
        return None, None
    date_str = date_match.group(1)

    result = {}
    in_section = False
    for line in content.split('\n'):
        if '一、资产总览' in line or '资产总览' in line:
            in_section = True
            continue
        if in_section and re.match(r'^##\s', line):
            break
        if not in_section:
            continue
        match = re.match(r'\|\s*(.+?)\s*\|\s*¥?([\d,]+(?:\.\d+)?)\s*\|', line)
        if match:
            name = match.group(1).strip()
            amount = float(match.group(2).replace(',', ''))
            result[name] = amount

    return date_str[:7], result


def _get_valid_series(all_dates, all_data, key):
    """返回 (dates, values) 过滤掉 None"""
    vals = all_data.get(key, [])
    dates = [d for d, v in zip(all_dates, vals) if v is not None]
    values = [v for v in vals if v is not None]
    return dates, values


def _annotate_points(ax, dates, values, color, fmt='{:.1f}万'):
    """在数据点上标注金额"""
    for x, y in zip(dates, values):
        text = fmt.format(y / 10000) if y >= 10000 else fmt.format(y)
        # 垂直偏移：根据数据密度动态调整
        offset = 12
        ax.annotate(text, (x, y),
                    textcoords='offset points', xytext=(0, offset),
                    fontsize=7, color=color, ha='center', alpha=0.85,
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='none', alpha=0.7))


# ── 汇总图 ──
def make_summary_chart(all_dates, all_data):
    fig, ax = plt.subplots(figsize=(14, 7))

    for key in ASSET_KEYS:
        dates, vals = _get_valid_series(all_dates, all_data, key)
        if len(vals) < 2:
            continue
        color = COLORS.get(key, '#999')
        lw = 2.5 if key == '净资产' else 1.8
        ax.plot(dates, vals, '-', linewidth=lw, color=color,
                label=key, alpha=1.0, marker='o', markersize=5)

        # 所有资产都标注金额
        _annotate_points(ax, dates, vals, color)

    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('资产值 (CNY)', fontsize=12)
    ax.set_title('家庭资产月度趋势汇总 (2026)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f'{x/10000:.0f}万' if x >= 10000 else f'{x:.0f}'))

    plt.tight_layout()
    path = OUTPUT_DIR / 'asset-trend-2026.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 汇总图: {path}')


# ── 单独子图 ──
def make_individual_charts(all_dates, all_data):
    """每个资产类别一张独立图"""
    for key in ASSET_KEYS:
        dates, vals = _get_valid_series(all_dates, all_data, key)
        if len(vals) < 2:
            continue

        fig, ax = plt.subplots(figsize=(8, 4.5))
        color = COLORS.get(key, '#999')

        ax.plot(dates, vals, '-', linewidth=2.5, color=color,
                marker='o', markersize=8)

        _annotate_points(ax, dates, vals, color)

        ax.set_xlabel('月份', fontsize=11)
        ax.set_ylabel('资产值 (CNY)', fontsize=11)
        ax.set_title(f'{key} 月度趋势', fontsize=13, fontweight='bold', color=color)
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f'{x/10000:.0f}万' if x >= 10000 else f'{x:.0f}'))

        plt.tight_layout()
        safe_name = key.replace('(', '').replace(')', '')
        path = OUTPUT_DIR / f'asset-trend-{safe_name}.png'
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f'  ✅ {key}: {path.name}')


def main():
    all_dates = []
    all_data = {}

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
        print('  ⚠️ 至少需要 2 期报告')
        sys.exit(0)

    print(f'\n  共 {len(all_dates)} 期报告: {all_dates[0]} ~ {all_dates[-1]}')

    print('\n─ 汇总图 ─')
    make_summary_chart(all_dates, all_data)

    print('\n─ 单独资产图 ─')
    make_individual_charts(all_dates, all_data)

    print('\n  🎉 全部图表生成完毕')


if __name__ == '__main__':
    print('正在生成资产趋势图...\n')
    main()
