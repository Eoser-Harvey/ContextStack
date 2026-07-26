"""
投资指标基类 — 所有指标模块继承此接口

设计原则:
  - 每个指标自包含数据抓取和卡片构建逻辑
  - fetch() 失败不应中断整个推送流程，由调用方捕获异常
  - build_section() 返回的 elements 直接拼入飞书卡片
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseIndicator(ABC):
    """投资指标抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """指标名称（用于日志和卡片标题）"""
        ...

    @property
    @abstractmethod
    def icon(self) -> str:
        """指标图标 emoji"""
        ...

    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """抓取原始数据，返回结构化字典。

        Returns:
            包含指标原始数据的字典，具体结构由子类定义。

        Raises:
            Exception: 抓取失败时抛出异常，由调用方捕获。
        """
        ...

    @abstractmethod
    def build_section(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据抓取的数据构建飞书卡片 elements。

        Args:
            data: fetch() 返回的数据字典

        Returns:
            飞书 interactive 卡片 elements 列表
        """
        ...

    @abstractmethod
    def get_summary(self, data: Dict[str, Any]) -> str:
        """返回该指标的核心摘要文本，用于趋势点评段落。

        Args:
            data: fetch() 返回的数据字典

        Returns:
            2-3 句话的摘要文本
        """
        ...
