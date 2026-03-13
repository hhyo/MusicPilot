"""Chart Fetcher 基类测试"""
import pytest
from datetime import datetime
from app.modules.chart.fetchers.base import (
    BaseChartFetcher, ChartData, ChartEntry
)


class MockFetcher(BaseChartFetcher):
    """测试用的 Mock Fetcher"""
    
    async def fetch(self, chart_type: str, limit: int = 50) -> ChartData:
        return ChartData(
            source="mock",
            chart_type=chart_type,
            updated_at=datetime.now(),
            entries=[
                ChartEntry(rank=1, title="Test Song", artist="Test Artist")
            ]
        )
    
    def get_supported_charts(self) -> list:
        return ["test_chart"]


class TestChartEntry:
    """测试 ChartEntry 数据类"""
    
    def test_chart_entry_creation(self):
        """测试 ChartEntry 创建"""
        entry = ChartEntry(
            rank=1,
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            mbid="test-mbid-123"
        )
        
        assert entry.rank == 1
        assert entry.title == "Test Song"
        assert entry.artist == "Test Artist"
        assert entry.album == "Test Album"
        assert entry.mbid == "test-mbid-123"
    
    def test_chart_entry_optional_fields(self):
        """测试 ChartEntry 可选字段"""
        entry = ChartEntry(rank=1, title="Test", artist="Artist")
        
        assert entry.album is None
        assert entry.mbid is None


class TestChartData:
    """测试 ChartData 数据类"""
    
    def test_chart_data_creation(self):
        """测试 ChartData 创建"""
        entries = [ChartEntry(rank=1, title="Song", artist="Artist")]
        data = ChartData(
            source="netease",
            chart_type="new_songs",
            updated_at=datetime.now(),
            entries=entries
        )
        
        assert data.source == "netease"
        assert data.chart_type == "new_songs"
        assert len(data.entries) == 1


class TestBaseChartFetcher:
    """测试 BaseChartFetcher 抽象基类"""
    
    @pytest.mark.asyncio
    async def test_mock_fetcher_fetch(self):
        """测试 Mock Fetcher 能正确抓取数据"""
        fetcher = MockFetcher()
        data = await fetcher.fetch("test_chart", limit=10)
        
        assert data.source == "mock"
        assert data.chart_type == "test_chart"
        assert len(data.entries) == 1
        assert data.entries[0].rank == 1
        assert data.entries[0].title == "Test Song"
    
    def test_mock_fetcher_supported_charts(self):
        """测试 Mock Fetcher 返回支持的榜单"""
        fetcher = MockFetcher()
        charts = fetcher.get_supported_charts()
        
        assert "test_chart" in charts