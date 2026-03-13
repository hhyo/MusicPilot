"""Chart Fetchers"""
from .base import ChartData, ChartEntry, BaseChartFetcher
from .netease import NeteaseChartFetcher
from .qq_music import QQMusicChartFetcher

__all__ = [
    "ChartData",
    "ChartEntry",
    "BaseChartFetcher",
    "NeteaseChartFetcher",
    "QQMusicChartFetcher",
]