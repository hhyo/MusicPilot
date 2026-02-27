"""
Track API 端点
曲目相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.operations.track import TrackOper
from app.schemas.track import (
    TrackCreate,
    TrackUpdate,
    TrackResponse,
    TrackListResponse,
    TrackStreamInfo,
)
from app.schemas.response import ResponseModel, PaginatedResponse
from app.core.config import settings


router = APIRouter()


def get_track_oper(db: AsyncSession = Depends(get_db)) -> TrackOper:
    """获取 Track 操作实例"""
    from app.db import db_manager
    return TrackOper(db_manager)


@router.get("/", response_model=PaginatedResponse[TrackListResponse])
async def get_tracks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    track_oper: TrackOper = Depends(get_track_oper),
):
    """
    获取曲目列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数（最多 100）
    - **search**: 搜索关键词（按标题搜索）
    """
    if search:
        tracks = await track_oper.search_by_title(search, limit=limit)
    else:
        tracks = await track_oper.get_all(skip=skip, limit=limit)

    total = await track_oper.count()
    total_pages = (total + limit - 1) // limit
    page = skip // limit + 1

    track_list = [
        TrackListResponse(
            id=t.id,
            musicbrainz_id=t.musicbrainz_id,
            album_id=t.album_id,
            artist_id=t.artist_id,
            disc_number=t.disc_number,
            track_number=t.track_number,
            title=t.title,
            duration=t.duration,
            path=t.path,
            file_format=t.file_format,
            play_count=t.play_count,
        )
        for t in tracks
    ]

    return PaginatedResponse(
        data=track_list,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/recent", response_model=List[TrackListResponse])
async def get_recent_tracks(
    limit: int = Query(50, ge=1, le=100),
    track_oper: TrackOper = Depends(get_track_oper),
):
    """获取最近播放的曲目"""
    tracks = await track_oper.get_recently_played(limit=limit)

    return [
        TrackListResponse(
            id=t.id,
            musicbrainz_id=t.musicbrainz_id,
            album_id=t.album_id,
            artist_id=t.artist_id,
            disc_number=t.disc_number,
            track_number=t.track_number,
            title=t.title,
            duration=t.duration,
            path=t.path,
            file_format=t.file_format,
            play_count=t.play_count,
        )
        for t in tracks
    ]


@router.get("/{track_id}", response_model=ResponseModel[TrackResponse])
async def get_track(
    track_id: int,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """获取曲目详情"""
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    return ResponseModel(data=TrackResponse.model_validate(track))


@router.get("/{track_id}/stream", response_class=FileResponse)
async def stream_track(
    track_id: int,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """
    流式传输曲目

    支持 Range 请求（断点续传）
    """
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    if not track.path:
        raise HTTPException(status_code=404, detail="曲目文件不存在")

    from pathlib import Path
    file_path = Path(track.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="曲目文件不存在")

    # 使用 FileResponse 自动处理 Range 请求
    return FileResponse(
        path=str(file_path),
        media_type=f"audio/{track.file_format or 'mpeg'}",
        filename=f"{track.title}.{track.file_format or 'mp3'}",
    )


@router.get("/{track_id}/lyrics", response_model=ResponseModel[dict])
async def get_track_lyrics(
    track_id: int,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """获取曲目歌词"""
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    return ResponseModel(data={"lyrics": track.lyrics})


@router.put("/{track_id}", response_model=ResponseModel[TrackResponse])
async def update_track(
    track_id: int,
    track: TrackUpdate,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """更新曲目"""
    updated_track = await track_oper.update(
        track_id, **{k: v for k, v in track.model_dump().items() if v is not None}
    )
    if not updated_track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    return ResponseModel(
        message="曲目更新成功",
        data=TrackResponse.model_validate(updated_track),
    )


@router.post("/{track_id}/play", response_model=ResponseModel[dict])
async def play_track(
    track_id: int,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """记录曲目播放（增加播放次数）"""
    track = await track_oper.update_play_count(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    return ResponseModel(
        message="播放记录成功",
        data={"id": track_id, "play_count": track.play_count},
    )