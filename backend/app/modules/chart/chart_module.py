"""
Chart Module - 榜单模块
"""


from app.modules.chart.fetchers.base import ChartData
from app.modules.chart.fetchers.netease import NeteaseChartFetcher
from app.modules.chart.fetchers.qq_music import QQMusicChartFetcher


class ChartModule:
    """Chart Module - 榜单模块 🆕 新增"""

    _instance = None

    # 榜单 fetcher 映射
    FETCHERS = {
        "netease": NeteaseChartFetcher,
        "qq_music": QQMusicChartFetcher,
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._fetchers = {}

    def get_fetcher(self, source: str):
        """获取榜单 fetcher"""
        if source not in self._fetchers:
            fetcher_class = self.FETCHERS.get(source)
            if fetcher_class:
                self._fetchers[source] = fetcher_class()
            else:
                raise ValueError(f"Unknown chart source: {source}")
        return self._fetchers[source]

    async def fetch_chart(
        self, source: str = "netease", chart_type: str = "new_songs", limit: int = 50
    ) -> ChartData:
        """
        抓取榜单数据

        Args:
            source: 数据源 (netease, qq_music)
            chart_type: 榜单类型
            limit: 返回数量限制

        Returns:
            ChartData: 榜单数据
        """
        fetcher = self.get_fetcher(source)
        return await fetcher.fetch(chart_type=chart_type, limit=limit)

    def get_supported_sources(self) -> list[str]:
        """获取支持的数据源"""
        return list(self.FETCHERS.keys())

    def get_supported_charts(self, source: str) -> list[str]:
        """获取支持的榜单类型"""
        fetcher = self.get_fetcher(source)
        return fetcher.get_supported_charts()
