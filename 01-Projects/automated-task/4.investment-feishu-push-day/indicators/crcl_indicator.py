"""
CRCL (Circle) 指标模块
数据源: https://crcl.seanzhao.ai — 子琦 (@Seanzhao1105) 开发的 CRCL 数据看板

抓取方式:
  看板的所有数据内嵌在页面 HTML 的 JavaScript 变量 `CD` 中。
  本模块通过 requests 抓取页面 HTML，再用正则提取 `CD = {...}` 对象并解析为 JSON。

CD 数据结构关键字段:
  - d[]         : 交易日日期数组 (YYYY-MM-DD)
  - close[]     : 收盘价
  - ma120[]     : 120日均线
  - ma200[]     : 200日均线
  - rsi[]       : RSI 14 指标
  - psTTM[]     : P/S (TTM) 市值/过去4季营收
  - psProxy[]   : P/S 日频代理 (USDC×10Y×1.2)
  - usdcShare[] : USDC 稳定币市占率 (%)
  - usdtShare[] : USDT 稳定币市占率 (%)
  - uv[]        : USDC 供应量 (美元)
  - udelta[]    : USDC 每日净发行/净销毁 (美元)
  - quarters[]  : 季度财报数据
  - st[]        : 买入信号分 (0-130)
  - sb[]        : 信号分三层分解 [估值层, 恐慌层, 基本面层]
  - scoring     : 信号分区间定义
  - bt          : 回测数据
  - ath/low     : 历史高点/低点
  - ipoDate     : 上市日期
"""
import json
import re
import requests
from typing import Any, Dict, List

from .base import BaseIndicator


class CRCLIndicator(BaseIndicator):
    """CRCL (Circle) 投资指标"""

    DASHBOARD_URL = "https://crcl.seanzhao.ai"

    @property
    def name(self) -> str:
        return "CRCL (Circle)"

    @property
    def icon(self) -> str:
        return "\U0001f4b9"  # 💹

    # ==================== 数据抓取 ====================

    def fetch(self) -> Dict[str, Any]:
        """从 crcl.seanzhao.ai 抓取 CRCL 全量数据。

        Returns:
            包含最新交易日数据的字典。
        """
        print(f"[INFO] 抓取 CRCL 数据: {self.DASHBOARD_URL}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        resp = requests.get(self.DASHBOARD_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        html = resp.text
        print(f"[INFO] 页面 HTML 长度: {len(html)} 字符")

        # 提取 CD = {...} 对象
        # 页面内嵌 <script>var CD = {...}</script>
        cd_data = self._extract_cd_object(html)
        if cd_data is None:
            raise RuntimeError("无法从页面 HTML 中提取 CD 数据对象")

        # 解析为最新交易日的结构化数据
        result = self._parse_latest(cd_data)
        print(f"[INFO] CRCL 数据解析成功: 日期={result['date']}, 收盘=${result['close']:.2f}, 信号分={result['score']}")
        return result

    def _extract_cd_object(self, html: str) -> Dict[str, Any]:
        """从 HTML 中提取 `var CD = {...}` JavaScript 对象并解析为 dict。

        策略: 用正则定位 `var CD = ` 后的 JSON，然后逐步扩展花括号匹配完整对象。
        """
        # 定位起始位置
        marker = "var CD = "
        idx = html.find(marker)
        if idx == -1:
            # 尝试其他可能的写法
            marker = "CD = "
            idx = html.find(marker)
            if idx == -1:
                return None

        start = idx + len(marker)
        # 跳过可能的空白
        while start < len(html) and html[start] in " \t\r\n":
            start += 1

        if start >= len(html) or html[start] != "{":
            return None

        # 花括号匹配，考虑字符串内的花括号
        depth = 0
        in_string = False
        escape = False
        quote_char = None
        end = start

        for i in range(start, len(html)):
            ch = html[i]

            if escape:
                escape = False
                continue

            if ch == "\\":
                escape = True
                continue

            if in_string:
                if ch == quote_char:
                    in_string = False
                continue

            if ch in ('"', "'", "`"):
                in_string = True
                quote_char = ch
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        json_str = html[start:end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试清理一些 JS 特有的语法
            # 处理 null, true, false 已是 JSON 兼容
            # 处理可能的尾部逗号
            cleaned = re.sub(r",\s*([}\]])", r"\1", json_str)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                print(f"[ERROR] 解析 CD JSON 失败: {e}")
                return None

    def _parse_latest(self, cd: Dict[str, Any]) -> Dict[str, Any]:
        """从 CD 全量数据中提取最新交易日的结构化数据。"""
        d = cd["d"]
        n = len(d) - 1  # 最新交易日索引

        # USDC 7天/30天净变化
        uv = cd["uv"]
        udelta = cd["udelta"]
        usdc_now = uv[n]
        usdc_7d_ago = uv[n - 7] if n >= 7 else uv[0]
        usdc_30d_ago = uv[n - 30] if n >= 30 else uv[0]
        usdc_7d_change = usdc_now - usdc_7d_ago
        usdc_30d_change = usdc_now - usdc_30d_ago

        # 信号分三层分解
        sb = cd["sb"][n] if cd["sb"][n] else [0, 0, 0]
        score_valuation = sb[0] if len(sb) > 0 else 0  # 估值层 /80
        score_panic = sb[1] if len(sb) > 1 else 0       # 恐慌层 /20
        score_fundamental = sb[2] if len(sb) > 2 else 0 # 基本面层 /30

        # 信号分区间
        score = cd["st"][n] if cd["st"][n] else 0
        zone_name, zone_action = self._get_zone(score, cd.get("scoring", {}))

        # 距高点/低点
        close = cd["close"][n]
        ath = cd["ath"]
        low = cd["low"]
        from_ath_pct = (close - ath) / ath * 100
        from_low_pct = (close - low) / low * 100

        # MA 偏离
        ma120 = cd["ma120"][n]
        ma200 = cd["ma200"][n]
        vs_ma120_pct = ((close - ma120) / ma120 * 100) if ma120 else None
        vs_ma200_pct = ((close - ma200) / ma200 * 100) if ma200 else None

        # TTM 营收（最近4个已报告季度）
        quarters = cd.get("quarters", [])
        reported_qs = [q for q in quarters if q.get("reported") and q.get("total")]
        ttm_revenue = sum(q["total"] for q in reported_qs[-4:]) if len(reported_qs) >= 4 else None
        latest_q = reported_qs[-1] if reported_qs else None

        # 流通市值 = close * 隐含股数
        # 从页面提取的隐含股数（看板显示 248.6M 流通股）
        # 用 P/S(TTM) 反推: market_cap = psTTM * ttm_revenue
        ps_ttm = cd["psTTM"][n]
        market_cap = ps_ttm * ttm_revenue if ttm_revenue else None

        # Coinbase 分成后剩余 (TTM 储备收入的 ~63.1% 分给 Coinbase)
        ttm_reserve = sum(q.get("reserve", 0) for q in reported_qs[-4:]) if len(reported_qs) >= 4 else None
        coinbase_share = ttm_reserve * 0.631 if ttm_reserve else None
        net_after_coinbase = ttm_reserve - coinbase_share if ttm_reserve else None

        # EBITDA TTM
        ttm_ebitda = sum(q["ebitda"] for q in reported_qs[-4:] if q.get("ebitda")) if len(reported_qs) >= 4 else None

        return {
            "date": d[n],
            "close": close,
            "ma120": ma120,
            "ma200": ma200,
            "vs_ma120_pct": vs_ma120_pct,
            "vs_ma200_pct": vs_ma200_pct,
            "rsi": cd["rsi"][n],
            "ps_ttm": ps_ttm,
            "ps_proxy": cd["psProxy"][n],
            "usdc_supply": usdc_now,
            "usdc_7d_change": usdc_7d_change,
            "usdc_30d_change": usdc_30d_change,
            "usdc_share": cd["usdcShare"][n],
            "usdt_share": cd["usdtShare"][n],
            "score": score,
            "score_valuation": score_valuation,
            "score_panic": score_panic,
            "score_fundamental": score_fundamental,
            "zone_name": zone_name,
            "zone_action": zone_action,
            "ath": ath,
            "ath_date": cd["athDate"],
            "low": low,
            "low_date": cd["lowDate"],
            "from_ath_pct": from_ath_pct,
            "from_low_pct": from_low_pct,
            "ipo_date": cd["ipoDate"],
            "ttm_revenue": ttm_revenue,
            "latest_quarter": latest_q,
            "market_cap": market_cap,
            "ttm_reserve": ttm_reserve,
            "coinbase_share": coinbase_share,
            "net_after_coinbase": net_after_coinbase,
            "ttm_ebitda": ttm_ebitda,
            "quarters": reported_qs,
            "next_earnings": self._get_next_earnings(quarters),
            "backtest": cd.get("bt", {}),
        }

    def _get_zone(self, score: int, scoring: Dict) -> tuple:
        """根据信号分返回区间名称和操作建议。"""
        zones = scoring.get("zones", [])
        for zone in zones:
            if score >= zone["min"]:
                return zone["name"], zone["action"]
        return "观望", "不买,继续观察"

    def _get_next_earnings(self, quarters: List[Dict]) -> str:
        """找到下一个未发布的财报季度。"""
        for q in quarters:
            if not q.get("reported"):
                return q.get("q", "未知")
        return "未知"

    # ==================== 格式化工具 ====================

    @staticmethod
    def _fmt_money(val: float) -> str:
        """格式化美元金额: 1.23B / 456.7M / 12.3K"""
        if val is None:
            return "N/A"
        abs_val = abs(val)
        if abs_val >= 1e9:
            return f"${val/1e9:.2f}B"
        if abs_val >= 1e6:
            return f"${val/1e6:.1f}M"
        if abs_val >= 1e3:
            return f"${val/1e3:.1f}K"
        return f"${val:.2f}"

    @staticmethod
    def _fmt_pct(val: float, with_sign: bool = True) -> str:
        """格式化百分比"""
        if val is None:
            return "N/A"
        if with_sign and val > 0:
            return f"+{val:.2f}%"
        return f"{val:.2f}%"

    @staticmethod
    def _fmt_num(val: float, decimals: int = 2) -> str:
        if val is None:
            return "N/A"
        return f"{val:.{decimals}f}"

    # ==================== 卡片构建 ====================

    def build_section(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建 CRCL 指标的飞书卡片 elements。"""
        elements = []

        # ---- 板块标题 ----
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**{self.icon} CRCL (Circle) 指标监控**",
            },
        })

        # ---- 核心数据概览 ----
        close = data["close"]
        score = data["score"]
        zone = data["zone_name"]
        action = data["zone_action"]
        ps_ttm = data["ps_ttm"]
        rsi = data["rsi"]

        elements.append({
            "tag": "div",
            "fields": [
                {
                    "is_short": True,
                    "text": {"tag": "lark_md", "content": f"**收盘价**\n${close:.2f}"},
                },
                {
                    "is_short": True,
                    "text": {"tag": "lark_md", "content": f"**信号分**\n{score} · {zone}"},
                },
                {
                    "is_short": True,
                    "text": {"tag": "lark_md", "content": f"**P/S (TTM)**\n{ps_ttm:.2f}x"},
                },
                {
                    "is_short": True,
                    "text": {"tag": "lark_md", "content": f"**RSI 14**\n{rsi:.1f}"},
                },
            ],
        })

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"操作建议: {action}",
            },
        })

        elements.append({"tag": "hr"})

        # ---- 信号分三层分解 ----
        sv = data["score_valuation"]
        sp = data["score_panic"]
        sf = data["score_fundamental"]
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**信号分分解 (基础100 + 超频30 = 上限130)**\n"
                    f"\u2022 估值层: {sv}/80 (P/S 实时口径, 4.5x 以下进超频区)\n"
                    f"\u2022 恐慌层: {sp}/20 (RSI, ≤30 满分)\n"
                    f"\u2022 基本面层: {sf}/30 (USDC 90天趋势 + 市占率变化)"
                ),
            },
        })

        elements.append({"tag": "hr"})

        # ---- USDC 基本面 ----
        usdc_supply = data["usdc_supply"]
        usdc_7d = data["usdc_7d_change"]
        usdc_30d = data["usdc_30d_change"]
        usdc_share = data["usdc_share"]
        usdt_share = data["usdt_share"]

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**USDC 基本面**\n"
                    f"\u2022 供应量: {self._fmt_money(usdc_supply)}\n"
                    f"\u2022 7天净变化: {self._fmt_money(usdc_7d)} ({self._fmt_pct(usdc_7d/usdc_supply*100)})\n"
                    f"\u2022 30天净变化: {self._fmt_money(usdc_30d)} ({self._fmt_pct(usdc_30d/usdc_supply*100)})\n"
                    f"\u2022 市占率: USDC {usdc_share:.1f}% / USDT {usdt_share:.1f}%"
                ),
            },
        })

        elements.append({"tag": "hr"})

        # ---- 营收与估值 ----
        ttm_rev = data["ttm_revenue"]
        latest_q = data["latest_quarter"]
        market_cap = data["market_cap"]
        ttm_ebitda = data["ttm_ebitda"]
        coinbase = data["coinbase_share"]
        net_coinbase = data["net_after_coinbase"]
        next_earn = data["next_earnings"]

        rev_lines = "**营收与估值**\n"
        if ttm_rev:
            rev_lines += f"\u2022 TTM 总营收: {self._fmt_money(ttm_rev)}\n"
        if latest_q:
            qoq = latest_q.get("qoq")
            yoy = latest_q.get("yoy")
            qoq_str = self._fmt_pct(qoq) if qoq is not None else "N/A"
            yoy_str = self._fmt_pct(yoy) if yoy is not None else "N/A"
            rev_lines += f"\u2022 最新季度 {latest_q['q']}: {self._fmt_money(latest_q['total'])} (QoQ {qoq_str} / YoY {yoy_str})\n"
        if market_cap:
            rev_lines += f"\u2022 流通市值: {self._fmt_money(market_cap)}\n"
        if ttm_ebitda:
            ps_ebitda = market_cap / ttm_ebitda if market_cap and ttm_ebitda else None
            rev_lines += f"\u2022 市值/调整后EBITDA: {ps_ebitda:.1f}x (TTM EBITDA {self._fmt_money(ttm_ebitda)})\n"
        if coinbase is not None and net_coinbase is not None:
            rev_lines += f"\u2022 Coinbase 分成: {self._fmt_money(coinbase)} (分成后剩余 {self._fmt_money(net_coinbase)})\n"
        rev_lines += f"\u2022 下一份财报: {next_earn} (2026-08-05 已定档)"

        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": rev_lines.rstrip()},
        })

        elements.append({"tag": "hr"})

        # ---- 技术面 ----
        ma120 = data["ma120"]
        ma200 = data["ma200"]
        vs_ma120 = data["vs_ma120_pct"]
        vs_ma200 = data["vs_ma200_pct"]
        from_ath = data["from_ath_pct"]
        from_low = data["from_low_pct"]

        tech_lines = "**技术面**\n"
        tech_lines += f"\u2022 MA120: ${ma120:.2f}" if ma120 else "\u2022 MA120: N/A"
        if vs_ma120 is not None:
            tech_lines += f" (偏离 {self._fmt_pct(vs_ma120)})\n"
        else:
            tech_lines += "\n"
        tech_lines += f"\u2022 MA200: ${ma200:.2f}" if ma200 else "\u2022 MA200: N/A"
        if vs_ma200 is not None:
            tech_lines += f" (偏离 {self._fmt_pct(vs_ma200)})\n"
        else:
            tech_lines += "\n"
        tech_lines += f"\u2022 距历史新高: {self._fmt_pct(from_ath)} (ATH ${data['ath']:.2f} · {data['ath_date']})\n"
        tech_lines += f"\u2022 距上市低点: {self._fmt_pct(from_low)} (低点 ${data['low']:.2f} · {data['low_date']})"

        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": tech_lines},
        })

        elements.append({"tag": "hr"})

        # ---- 回测参考 ----
        bt = data.get("backtest", {})
        if bt:
            scored_days = bt.get("scoredDays", 0)
            baseline_cost = bt.get("baselineCost", 0)
            baseline_pct = bt.get("baselineVsNowPct", 0)
            thresholds = bt.get("thresholds", [])

            bt_lines = f"**回测参考 (可打分历史 {scored_days} 天)**\n"
            bt_lines += f"\u2022 同期每天都买成本: ${baseline_cost:.2f} (vs现价 {self._fmt_pct(baseline_pct)})\n"
            # 只展示关键阈值
            for th in thresholds:
                if th["th"] in (40, 55, 65):
                    if th["cost"]:
                        bt_lines += f"\u2022 ≥{th['th']}分才买: ${th['cost']:.2f} ({th['days']}天/{th['segments']}段, vs现价 {self._fmt_pct(th['vsNowPct'])})\n"
                    else:
                        bt_lines += f"\u2022 ≥{th['th']}分才买: 从未触发\n"
            bt_lines += "\u26a0\ufe0f 分数是纪律工具,不是预测。CRCL 上市仅一年,样本小,结论可能被修正。"

            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": bt_lines.rstrip()},
            })

        return elements

    # ==================== 摘要 ====================

    def get_summary(self, data: Dict[str, Any]) -> str:
        """返回 CRCL 指标的核心摘要，用于趋势点评。"""
        close = data["close"]
        score = data["score"]
        zone = data["zone_name"]
        ps_ttm = data["ps_ttm"]
        rsi = data["rsi"]
        usdc_7d = data["usdc_7d_change"]
        usdc_supply = data["usdc_supply"]
        from_ath = data["from_ath_pct"]
        next_earn = data["next_earnings"]

        usdc_trend = "净发行" if usdc_7d > 0 else "净销毁"

        return (
            f"CRCL ${close:.2f} (信号分{score}·{zone}, P/S {ps_ttm:.2f}x, RSI {rsi:.1f}), "
            f"距ATH {from_ath:.1f}%, USDC {self._fmt_money(usdc_supply)}({usdc_trend}), "
            f"下一财报{next_earn}(8/5)。"
        )
