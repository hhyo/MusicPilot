"""
Chart API 端点 - 榜单管理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.chart.chart_module import ChartModule

router = APIRouter(prefix="/chart", tags=["榜单管理"])
chart_module = ChartModule()


class ChartSource(BaseModel):
    id: str
    name: str


class ChartType(BaseModel):
    id: str
    name: str


class ChartEntry(BaseModel):
    rank: int
    title: str
    artist: str
    album: str | None = None
    duration: str | None = None
    cover_url: str | None = None


@router.get("/sources", response_model=list[ChartSource], summary="获取支持的榜单源")
async def get_chart_sources():
    """获取支持的榜单源列表"""
    sources = [
        ChartSource(id="netease", name="网易云音乐"),
        ChartSource(id="qq_music", name="QQ音乐"),
    ]
    return sources


@router.get("/{source}/types", response_model=list[ChartType], summary="获取榜单类型")
async def get_chart_types(source: str):
    """获取指定源支持的榜单类型"""
    types_map = {
        "netease": [
            ChartType(id="new_songs", name="新歌榜"),
            ChartType(id="hot_songs", name="热歌榜"),
            ChartType(id="soaring", name="飙升榜"),
        ],
        "qq_music": [
            ChartType(id="top", name="巅峰榜"),
            ChartType(id="new", name="新歌榜"),
        ],
    }
    return types_map.get(source, [])


@router.get("/{source}/{chart_type}", summary="获取榜单数据")
async def get_chart(source: str, chart_type: str, limit: int = 50):
    """获取榜单数据"""
    try:
        data = await chart_module.fetch_chart(source, chart_type, limit)
        return {
            "source": source,
            "chart_type": chart_type,
            "entries": [
                {
                    "rank": i + 1,
                    "title": entry.title,
                    "artist": entry.artist,
                    "album": entry.album,
                    "duration": entry.duration,
                    "cover_url": entry.cover_url,
                }
                for i, entry in enumerate(data.entries)
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取榜单数据失败: {str(e)}")