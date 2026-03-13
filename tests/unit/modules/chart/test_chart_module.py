"""Chart Module 主类测试"""

import pytest
from datetime import datetime
from app.modules.chart.chart_module import ChartModule
from app.modules.chart.fetchers.base import ChartData, ChartEntry


class TestChartModule:
    """测试 ChartModule"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        module1 = ChartModule()
        module2 = ChartModule()

        assert module1 is module2

    def test_get_supported_sources(self):
        """测试获取支持的榜单源"""
        module = ChartModule()
        sources = module.get_supported_sources()

        assert "netease" in sources
        assert "qq_music" in sources

    @pytest.mark.asyncio
    async def test_fetch_netease_chart(self):
        """测试抓取网易云榜单"""
        module = ChartModule()
        data = await module.fetch_chart("netease", "new_songs", limit=3)

        assert isinstance(data, ChartData)
        assert data.source == "netease"
        assert len(data.entries) == 3

    @pytest.mark.asyncio
    async def test_fetch_qq_music_chart(self):
        """测试抓取 QQ音乐榜单"""
        module = ChartModule()
        data = await module.fetch_chart("qq_music", "new_songs", limit=3)

        assert isinstance(data, ChartData)
        assert data.source == "qq_music"
        assert len(data.entries) == 3

    @pytest.mark.asyncio
    async def test_fetch_unsupported_source(self):
        """测试不支持的榜单源"""
        module = ChartModule()

        with pytest.raises(ValueError) as exc_info:
            await module.fetch_chart("unsupported", "new_songs", limit=10)

        assert "unsupported" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_invalid_chart_type(self):
        """测试无效的榜单类型"""
        module = ChartModule()

        with pytest.raises(ValueError):
            await module.fetch_chart("netease", "invalid_type", limit=10)
