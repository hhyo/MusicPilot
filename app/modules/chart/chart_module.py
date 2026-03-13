"""Chart Module 主类"""

from typing import List
from .fetchers.netease import NeteaseChartFetcher
from .fetchers.qq_music import QQMusicChartFetcher
from .fetchers.base import ChartData


class ChartModule:
    """榜单模块 - 管理各平台榜单抓取"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._init_fetchers()
        self._initialized = True

    def _init_fetchers(self):
        """初始化抓取器"""
        self.fetchers = {
            "netease": NeteaseChartFetcher(),
            "qq_music": QQMusicChartFetcher(),
        }

    async def fetch_chart(self, source: str, chart_type: str, limit: int = 50) -> ChartData:
        """抓取指定榜单"""
        fetcher = self.fetchers.get(source)
        if not fetcher:
            raise ValueError(f"Unsupported chart source: {source}")

        return await fetcher.fetch(chart_type, limit)

    def get_supported_sources(self) -> List[str]:
        """获取支持的榜单源"""
        return list(self.fetchers.keys())
