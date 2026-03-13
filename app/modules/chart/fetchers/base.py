"""Chart Fetcher 基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ChartEntry:
    """榜单条目"""
    rank: int
    title: str
    artist: str
    album: Optional[str] = None
    mbid: Optional[str] = None


@dataclass
class ChartData:
    """榜单数据"""
    source: str
    chart_type: str
    updated_at: datetime
    entries: List[ChartEntry]


class BaseChartFetcher(ABC):
    """榜单抓取器抽象基类"""
    
    @abstractmethod
    async def fetch(self, chart_type: str, limit: int = 50) -> ChartData:
        """抓取榜单数据"""
        pass
    
    @abstractmethod
    def get_supported_charts(self) -> List[str]:
        """返回支持的榜单类型"""
        pass