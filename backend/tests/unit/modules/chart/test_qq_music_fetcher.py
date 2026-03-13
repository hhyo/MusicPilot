"""QQ音乐榜单抓取器测试"""


import pytest

from app.modules.chart.fetchers.base import ChartData
from app.modules.chart.fetchers.qq_music import QQMusicChartFetcher


class TestQQMusicChartFetcher:
    """测试 QQ音乐榜单抓取器"""

    def test_supported_charts(self):
        """测试返回支持的榜单类型"""
        fetcher = QQMusicChartFetcher()
        charts = fetcher.get_supported_charts()

        assert "new_songs" in charts
        assert "hot_songs" in charts
        assert "soaring" in charts

    def test_chart_urls_mapping(self):
        """测试榜单 URL 映射"""
        fetcher = QQMusicChartFetcher()

        assert "new_songs" in fetcher.CHART_URLS
        assert "hot_songs" in fetcher.CHART_URLS
        assert "soaring" in fetcher.CHART_URLS

    @pytest.mark.asyncio
    async def test_fetch_new_songs_chart(self):
        """测试抓取新歌榜"""
        fetcher = QQMusicChartFetcher()
        data = await fetcher.fetch("new_songs", limit=5)

        assert isinstance(data, ChartData)
        assert data.source == "qq_music"
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
        fetcher = QQMusicChartFetcher()
        data = await fetcher.fetch("hot_songs", limit=3)

        assert data.source == "qq_music"
        assert data.chart_type == "hot_songs"
        assert len(data.entries) == 3

    @pytest.mark.asyncio
    async def test_fetch_invalid_chart_type(self):
        """测试无效的榜单类型"""
        fetcher = QQMusicChartFetcher()

        with pytest.raises(ValueError) as exc_info:
            await fetcher.fetch("invalid_chart", limit=10)

        assert "invalid_chart" in str(exc_info.value)
