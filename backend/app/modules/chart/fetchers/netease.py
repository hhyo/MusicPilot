"""网易云音乐榜单抓取器"""

import httpx
from datetime import datetime
from typing import List
from .base import BaseChartFetcher, ChartData, ChartEntry


class NeteaseChartFetcher(BaseChartFetcher):
    """网易云音乐榜单抓取器"""

    API_BASE = "https://music.163.com/api"

    CHART_IDS = {
        "new_songs": 3779629,  # 新歌榜
        "hot_songs": 3778678,  # 热歌榜
        "soaring": 19723756,  # 飙升榜
    }

    async def fetch(self, chart_type: str, limit: int = 50) -> ChartData:
        """抓取指定榜单"""
        chart_id = self.CHART_IDS.get(chart_type)
        if not chart_id:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        url = f"{self.API_BASE}/playlist/detail?id={chart_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            data = response.json()

        code = data.get("code", -1)
        if code != 200:
            raise Exception(f"Failed to fetch chart: {data}")

        # API 返回 result 或 playlist
        playlist = data.get("result") or data.get("playlist", {})
        tracks = playlist.get("tracks", [])[:limit]

        entries = []
        for idx, track in enumerate(tracks):
            entries.append(
                ChartEntry(
                    rank=idx + 1,
                    title=track.get("name", ""),
                    artist=track.get("artists", [{}])[0].get("name", ""),
                    album=track.get("album", {}).get("name", ""),
                )
            )

        return ChartData(
            source="netease", chart_type=chart_type, updated_at=datetime.now(), entries=entries
        )

    def get_supported_charts(self) -> List[str]:
        """返回支持的榜单类型"""
        return list(self.CHART_IDS.keys())
