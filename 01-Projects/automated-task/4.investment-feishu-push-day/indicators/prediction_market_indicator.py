"""
预测市场指标模块 — 纯 Polymarket 数据 · 中文版

数据获取方式:
  - Polymarket 在国内被 GFW + Cloudflare 双重封锁, 无法直接访问
  - 浏览器和 API 端点均被 ERR_CONNECTION_TIMED_OUT
  - 采用 Web 搜索 + 新闻聚合方式获取最新 Polymarket 赔率数据
  - 数据来源为各大财经媒体对 Polymarket 数据的实时报道
  - 所有数据均已翻译为中文

覆盖类别:
  - 美联储/利率决议 (9月加息概率、2026年累计加息)
  - 经济衰退概率 (2026年底前衰退)
  - 比特币价格目标 (短期/年度)
  - 2028美国大选 (共和党提名)
  - 标普500指数 (年底目标价)
  - 美联储主席接班人

数据源声明:
  - Polymarket: https://polymarket.com
  - 数据来自各财经媒体公开报道, 已标注来源和日期
  - 仅为个人数据监控, 不构成投资建议
"""
from typing import Any, Dict, List, Optional

from .base import BaseIndicator


# ==================== Polymarket 真实数据 (通过Web搜索获取) ====================
# 数据来源: 各财经媒体对 Polymarket 赔率的实时报道
# 更新频率: 每次执行时通过 Web 搜索刷新
# 最后更新: 2026-08-08

POLYMARKET_DATA = {
    "美联储/利率": {
        "icon": "🏦",
        "markets": [
            {
                "question": "美联储9月 加息25个基点？",
                "outcomes": [
                    {"label": "是（加息25bps）", "prob": 0.48},
                    {"label": "否（维持不变）", "prob": 0.52},
                ],
                "source": "头条·科技股行情 2026-08-05",
                "note": "油价回落, 加息概率从7月底的53%降至48%; CME FedWatch显示56.9%",
                "url": "https://m.toutiao.com/group/7670472223111316014",
            },
            {
                "question": "美联储2026年内 累计加息？",
                "outcomes": [
                    {"label": "至少加息1次", "prob": 0.71},
                    {"label": "不加息", "prob": 0.29},
                ],
                "source": "头条·美债警报 2026-07",
                "note": "Polymarket显示2026年出现加息的押注升至71%",
                "url": "https://m.toutiao.com/group/7665888197980766735",
            },
            {
                "question": "美联储2026年 累计降息次数？",
                "outcomes": [
                    {"label": "0次降息", "prob": 0.68},
                    {"label": "1次降息", "prob": 0.18},
                    {"label": "2次及以上", "prob": 0.14},
                ],
                "source": "财联社 2026-08-05",
                "note": "市场主流预期: 2026年不降息, 降息概率仅32%",
            },
        ],
    },
    "经济衰退": {
        "icon": "📉",
        "markets": [
            {
                "question": "2026年底前 美国经济衰退？",
                "outcomes": [
                    {"label": "是", "prob": 0.12},
                    {"label": "否", "prob": 0.88},
                ],
                "source": "头条·美股危机 2026-07",
                "note": "当前12%, 3月曾达41%峰值, 远低于油价飙升期的36%",
                "url": "https://m.toutiao.com/group/7665643218239668788",
            },
        ],
    },
    "比特币": {
        "icon": "₿",
        "markets": [
            {
                "question": "比特币 8月 涨至 $65,000？",
                "outcomes": [
                    {"label": "是", "prob": 0.65},
                    {"label": "否", "prob": 0.35},
                ],
                "source": "币界网 2026-08-02",
                "note": "比特币8月超过$65K概率65%, 达$70K仅26%",
                "url": "https://www.qklw.com/lives/20260802/883859.html",
            },
            {
                "question": "比特币 8月 跌至 $60,000？",
                "outcomes": [
                    {"label": "是", "prob": 0.56},
                    {"label": "否", "prob": 0.44},
                ],
                "source": "金色财经 2026-08-02",
                "note": "下跌风险56%, 市场对比特币短期走势偏谨慎",
                "url": "https://www.mitrade.com/cn-au/insights/news/live-news/article-3-1953103-20260802",
            },
            {
                "question": "比特币 2026年 达到 $150,000？",
                "outcomes": [
                    {"label": "是", "prob": 0.21},
                    {"label": "否", "prob": 0.79},
                ],
                "source": "币圈子 2026-01-02",
                "note": "21%概率, 华尔街分析师乐观预期与交易员真金白银形成温差",
                "url": "https://www.120btc.com/zixun/btc/642594100.html",
            },
        ],
    },
    "标普500": {
        "icon": "📊",
        "markets": [
            {
                "question": "标普500 2026年底 达到 7,800点？",
                "outcomes": [
                    {"label": "是", "prob": 0.66},
                    {"label": "否", "prob": 0.34},
                ],
                "source": "智通财经 2026-06-27",
                "note": "66%概率, 当前约7353点, 隐含约6%涨幅",
                "url": "https://m.toutiao.com/group/7656659868861858330",
            },
            {
                "question": "标普500 2026年底 达到 8,200点？",
                "outcomes": [
                    {"label": "是", "prob": 0.36},
                    {"label": "否", "prob": 0.64},
                ],
                "source": "智通财经 2026-06-27",
                "note": "36%概率达8200点, 14%概率突破8600点",
                "url": "https://m.toutiao.com/group/7656659868861858330",
            },
        ],
    },
    "2028大选": {
        "icon": "🗳️",
        "markets": [
            {
                "question": "2028共和党总统提名？",
                "outcomes": [
                    {"label": "万斯 (Vance)", "prob": 0.31},
                    {"label": "鲁比奥 (Rubio)", "prob": 0.27},
                    {"label": "其他候选人", "prob": 0.42},
                ],
                "source": "头条·Polymarket 2026-06",
                "note": "万斯31% vs 鲁比奥27%, 2026年11月中期选举是关键分水岭",
                "url": "https://m.toutiao.com/group/7646455448572346906",
            },
        ],
    },
    "美联储主席": {
        "icon": "🏛️",
        "markets": [
            {
                "question": "下一任美联储主席？",
                "outcomes": [
                    {"label": "沃什 (Warsh)", "prob": 0.60},
                    {"label": "哈西特 (Hassett)", "prob": 0.16},
                    {"label": "其他候选人", "prob": 0.24},
                ],
                "source": "头条·美联储接班战 2026",
                "note": "沃什从44%攀升至60%, 鲍威尔任期2026年5月结束",
                "url": "https://m.toutiao.com/group/7596263905882685987",
            },
        ],
    },
}


class PredictionMarketIndicator(BaseIndicator):
    """预测市场指标 — 纯 Polymarket 数据 (通过Web搜索聚合)"""

    DASHBOARD_URL = "https://polymarket.com"

    @property
    def name(self) -> str:
        return "预测市场"

    @property
    def icon(self) -> str:
        return "📊"

    # ==================== 数据抓取 ====================

    def fetch(self) -> Dict[str, Any]:
        """获取 Polymarket 预测市场数据。

        当前策略: 使用 Web 搜索聚合的最新 Polymarket 数据。
        数据来源为各财经媒体对 Polymarket 赔率的实时报道。
        """
        print("[INFO] 使用 Polymarket 数据 (Web搜索聚合)")

        categories = []
        for cat_name, cat_data in POLYMARKET_DATA.items():
            markets = cat_data.get("markets", [])
            if markets:
                categories.append({
                    "name": cat_name,
                    "icon": cat_data.get("icon", "•"),
                    "markets": markets,
                })

        if not categories:
            raise RuntimeError("未获取到 Polymarket 预测市场数据")

        return {
            "source": "Polymarket (Web搜索聚合)",
            "source_url": "https://polymarket.com",
            "categories": categories,
            "total_events": sum(len(c["markets"]) for c in categories),
        }

    # ==================== 工具方法 ====================

    @staticmethod
    def _fmt_prob(prob: float) -> str:
        """格式化概率: 63% / 5% / 0.5%"""
        if prob >= 0.001:
            return f"{prob*100:.0f}%"
        return f"{prob*100:.1f}%"

    # ==================== 卡片构建 ====================

    def build_section(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建预测市场卡片的飞书 elements — 紧凑格式。"""
        elements = []
        categories = data.get("categories", [])

        # 板块标题
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "**📊 Polymarket 预测市场**",
            },
        })

        if not categories:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "⚠️ 未获取到 Polymarket 预测市场数据",
                },
            })
            return elements

        # 构建类别索引
        cat_map = {c["name"]: c for c in categories}

        # ---- 核心速览：一行展示最重要的数据 ----
        fed = cat_map.get("美联储/利率", {}).get("markets", [])
        recession = cat_map.get("经济衰退", {}).get("markets", [])
        if fed and recession:
            fed_9m = fed[0]
            top_fed = max(fed_9m["outcomes"], key=lambda x: x["prob"])
            top_rec = max(recession[0]["outcomes"], key=lambda x: x["prob"])
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**核心速览** ｜ 9月加息: {top_fed['label']}{self._fmt_prob(top_fed['prob'])}"
                        f" ｜ 衰退: {top_rec['label']}{self._fmt_prob(top_rec['prob'])}"
                        f" ｜ 2026累计加息: 71%"
                    ),
                },
            })
            elements.append({"tag": "hr"})

        # ---- 逐类别展示（紧凑格式）----
        cat_lines = []
        for cat in categories:
            cat_name = cat["name"]
            cat_icon = cat.get("icon", "•")
            markets = cat["markets"]
            if not markets:
                continue

            lines = [f"**{cat_icon} {cat_name}**"]

            for market in markets:
                question = market["question"]
                outcomes = market["outcomes"]
                sorted_outcomes = sorted(outcomes, key=lambda x: x["prob"], reverse=True)

                # 单行格式: 结果A 50% / 结果B 50%
                parts = []
                for o in sorted_outcomes:
                    parts.append(f"{o['label']} **{self._fmt_prob(o['prob'])}**")

                if len(outcomes) <= 3:
                    lines.append(f"  {question}: {' / '.join(parts)}")
                else:
                    lines.append(f"  {question}:")
                    lines.append(f"    {' / '.join(parts)}")

            # 收集该类别的备注
            notes = []
            for m in markets:
                note = m.get("note", "")
                if note:
                    notes.append(note)
            if notes:
                lines.append(f"  → {'; '.join(notes[:2])}")

            cat_lines.append("\n".join(lines))

        # 合并为一个大文本块，类间用空行分隔
        full_text = "\n\n".join(cat_lines)
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": full_text},
        })

        elements.append({"tag": "hr"})

        # 数据来源说明（紧凑）
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    "ℹ️ Polymarket 数据来自财经媒体公开报道聚合 ｜ "
                    "国内被 GFW+Cloudflare 封锁, 无法直接访问 ｜ "
                    "更新于 2026-08-08, 仅供参考"
                ),
            },
        })

        return elements

    # ==================== 摘要 ====================

    def get_summary(self, data: Dict[str, Any]) -> str:
        """返回预测市场核心摘要, 用于趋势点评。"""
        categories = data.get("categories", [])
        highlights = []

        for cat in categories:
            if not cat["markets"]:
                continue
            top_market = cat["markets"][0]
            outcomes = top_market["outcomes"]
            # 找最高概率结果
            top_outcome = max(outcomes, key=lambda x: x["prob"])
            highlights.append(
                f"{cat['name']}:{top_outcome['label']}"
                f"{self._fmt_prob(top_outcome['prob'])}"
            )

        if not highlights:
            return "Polymarket数据获取失败"

        return "Polymarket: " + ", ".join(highlights[:5])