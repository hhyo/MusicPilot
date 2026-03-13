"""网易云音乐榜单抓取器测试"""


import pytest

from app.modules.chart.fetchers.base import ChartData
from app.modules.chart.fetchers.netease import NeteaseChartFetcher


class TestNeteaseChartFetcher:
    """测试网易云榜单抓取器"""

    def test_supported_charts(self):
        """测试返回支持的榜单类型"""
        fetcher = NeteaseChartFetcher()
        charts = fetcher.get_supported_charts()

        assert "new_songs" in charts
        assert "hot_songs" in charts
        assert "soaring" in charts

    def test_chart_ids_mapping(self):
        """测试榜单 ID 映射"""
        fetcher = NeteaseChartFetcher()

        assert fetcher.CHART_IDS["new_songs"] == 3779629
        assert fetcher.CHART_IDS["hot_songs"] == 3778678
        assert fetcher.CHART_IDS["soaring"] == 19723756

    @pytest.mark.asyncio
    async def test_fetch_new_songs_chart(self):
        """测试抓取新歌榜"""
        fetcher = NeteaseChartFetcher()
        data = await fetcher.fetch("new_songs", limit=5)

        assert isinstance(data, ChartData)
        assert data.source == "netease"
        assert data.chart_type == "new_songs"
        assert len(data.entries) == 5

        # 检查第一条数据
        first = data.entries[0]
        assert first.rank == 1
        assert first.title
        assert first.artist

    @pytest.mark.asyncio
    async def test_fetch_hot_songs_chart(self):
        """测试抓取热歌榜"""
        fetcher = NeteaseChartFetcher()
        data = await fetcher.fetch("hot_songs", limit=3)

        assert data.source == "netease"
        assert data.chart_type == "hot_songs"
        assert len(data.entries) == 3

    @pytest.mark.asyncio
    async def test_fetch_invalid_chart_type(self):
        """测试无效的榜单类型"""
        fetcher = NeteaseChartFetcher()

        with pytest.raises(ValueError) as exc_info:
            await fetcher.fetch("invalid_chart", limit=10)

        assert "invalid_chart" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_network_error(self):
        """测试网络错误处理"""
        # 这个测试需要模拟网络错误
        pass
