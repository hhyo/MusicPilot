"""
订阅模块 - 榜单订阅功能
"""


from app.modules.chart.chart_module import ChartModule
from app.modules.chart.fetchers.base import ChartEntry


class SubscribeModule:
    """订阅模块（扩展支持榜单订阅）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.chart_module = ChartModule()
        self._downloaded_cache: set = set()

    async def process_subscription(self, subscription):
        """处理订阅（扩展支持榜单）"""
        if subscription.type == "chart":
            return await self.process_chart_subscription(subscription)
        else:
            # 原有逻辑 - 暂时返回 None
            return None

    async def process_chart_subscription(self, subscription) -> list[ChartEntry]:
        """处理榜单订阅 🆕 新增"""
        # 获取数据源
        source = subscription.source_type or "netease"
        chart_type = subscription.playlist_id or "new_songs"
        limit = 50  # 默认限制

        # 抓取榜单
        chart_data = await self.chart_module.fetch_chart(source, chart_type, limit)

        # 去重
        new_entries = self._filter_duplicates(chart_data.entries)

        # 自动下载
        if subscription.auto_download:
            for entry in new_entries:
                await self._download_entry(entry)

        return new_entries

    def _filter_duplicates(self, entries: list[ChartEntry]) -> list[ChartEntry]:
        """过滤已下载的歌曲 🆕 新增"""
        new_entries = []
        for entry in entries:
            key = f"{entry.title}-{entry.artist}"
            if key not in self._downloaded_cache:
                new_entries.append(entry)
                self._downloaded_cache.add(key)
        return new_entries

    async def _download_entry(self, entry: ChartEntry):
        """下载单首歌曲 🆕 新增"""
        # TODO: 调用搜索和下载模块
        pass

    def clear_cache(self):
        """清除下载缓存"""
        self._downloaded_cache.clear()

    def get_cached_count(self) -> int:
        """获取已缓存的歌曲数量"""
        return len(self._downloaded_cache)
