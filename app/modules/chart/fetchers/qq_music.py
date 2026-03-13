"""QQ 音乐榜单抓取器"""
from datetime import datetime
from typing import List
from .base import ChartData, ChartEntry, BaseChartFetcher


class QQMusicChartFetcher(BaseChartFetcher):
    """QQ 音乐榜单抓取器"""
    
    SUPPORTED_CHARTS = {
        "new_songs": "new",
        "hot_songs": "hot",
        "top500": "top",
    }
    
    def get_supported_charts(self) -> List[str]:
        """返回支持的榜单类型"""
        return list(self.SUPPORTED_CHARTS.keys())
    
    async def fetch(self, chart_type: str, limit: int = 50) -> ChartData:
        """抓取 QQ 音乐榜单"""
        if chart_type not in self.SUPPORTED_CHARTS:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # 模拟数据 - 实际应调用 QQ 音乐 API
        entries = [
            ChartEntry(
                rank=i + 1,
                title=f"QQ音乐测试歌曲{i + 1}",
                artist=f"QQ艺术家{i + 1}",
                album=f"QQ专辑{i + 1}",
            )
            for i in range(min(limit, 10))
        ]
        
        return ChartData(
            source="qq_music",
            chart_type=chart_type,
            updated_at=datetime.now(),
            entries=entries[:limit],
        )