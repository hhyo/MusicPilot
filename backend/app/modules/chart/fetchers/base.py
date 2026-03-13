"""Chart fetcher base classes"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class ChartEntry:
    """Single chart entry"""

    rank: int
    title: str
    artist: str
    album: str = ""
    duration: int = 0  # seconds
    cover_url: str = ""
    detail_url: str = ""


@dataclass
class ChartData:
    """Chart data container"""

    source: str
    chart_type: str
    updated_at: datetime
    entries: List[ChartEntry]
    total: int = 0
    description: str = ""


class BaseChartFetcher(ABC):
    """Base class for chart fetchers"""

    @abstractmethod
    async def fetch(self, chart_type: str, limit: int = 50) -> ChartData:
        """Fetch chart data"""
        pass

    @abstractmethod
    def get_supported_charts(self) -> List[str]:
        """Return list of supported chart types"""
        pass
