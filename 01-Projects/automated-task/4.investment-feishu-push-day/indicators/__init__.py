"""
投资指标包 — 可扩展的多指标架构

每个指标模块需实现 BaseIndicator 接口:
  - fetch()        : 抓取原始数据
  - build_section(): 返回飞书卡片 elements 列表（该指标的展示区块）
  - get_summary()  : 返回该指标的核心摘要文本（用于趋势点评）

新增指标步骤:
  1. 在本目录下创建 xxx_indicator.py，定义继承 BaseIndicator 的类
  2. 在 __init__.py 的 INDICATOR_REGISTRY 中注册
  3. 主脚本会自动加载并执行
"""
from .base import BaseIndicator
from .crcl_indicator import CRCLIndicator

# 指标注册表 — 新增指标在此注册即可
# 顺序决定卡片中各指标的展示顺序
INDICATOR_REGISTRY = [
    CRCLIndicator,
]

__all__ = ["BaseIndicator", "CRCLIndicator", "INDICATOR_REGISTRY"]
