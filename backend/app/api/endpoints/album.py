"""
Album API 端点
专辑相关 API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.operations.album import AlbumOper
from app.db.operations.track import TrackOper
from app.schemas.album import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumListResponse,
)
from app.schemas.track import TrackListResponse
from app.schemas.response import ResponseModel, PaginatedResponse


router = APIRouter()


def get_album_oper(db: AsyncSession = Depends(get_db)) -> AlbumOper:
    """获取 Album 操作实例"""
    from app.db import db_manager
    return AlbumOper(db_manager)


def get_track_oper(db: AsyncSession = Depends(get_db)) -> TrackOper:
    """获取 Track 操作实例"""
    from app.db import db_manager
    return TrackOper(db_manager)


@router.get("/", response_model=PaginatedResponse[AlbumListResponse])
async def get_albums(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """
    获取专辑列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数（最多 100）
    - **search**: 搜索关键词（按标题搜索）
    """
    if search:
        albums = await album_oper.search_by_title(search, limit=limit)
    else:
        albums = await album_oper.get_all(skip=skip, limit=limit)

    total = await album_oper.count()
    total_pages = (total + limit - 1) // limit
    page = skip // limit + 1

    album_list = [
        AlbumListResponse(
            id=a.id,
            musicbrainz_id=a.musicbrainz_id,
            artist_id=a.artist_id,
            title=a.title,
            release_date=a.release_date,
            release_type=a.release_type,
            cover_url=a.cover_url,
            genres=a.genres,
            rating=a.rating,
            track_count=a.track_count,
            total_duration=a.total_duration,
        )
        for a in albums
    ]

    return PaginatedResponse(
        data=album_list,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/recent", response_model=List[AlbumListResponse])
async def get_recent_albums(
    limit: int = Query(50, ge=1, le=100),
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """获取最近的专辑"""
    albums = await album_oper.get_recent(limit=limit)

    return [
        AlbumListResponse(
            id=a.id,
            musicbrainz_id=a.musicbrainz_id,
            artist_id=a.artist_id,
            title=a.title,
            release_date=a.release_date,
            release_type=a.release_type,
            cover_url=a.cover_url,
            genres=a.genres,
            rating=a.rating,
            track_count=a.track_count,
            total_duration=a.total_duration,
        )
        for a in albums
    ]


@router.get("/top", response_model=List[AlbumListResponse])
async def get_top_albums(
    limit: int = Query(50, ge=1, le=100),
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """获取评分最高的专辑"""
    albums = await album_oper.get_top_rated(limit=limit)

    return [
        AlbumListResponse(
            id=a.id,
            musicbrainz_id=a.musicbrainz_id,
            artist_id=a.artist_id,
            title=a.title,
            release_date=a.release_date,
            release_type=a.release_type,
            cover_url=a.cover_url,
            genres=a.genres,
            rating=a.rating,
            track_count=a.track_count,
            total_duration=a.total_duration,
        )
        for a in albums
    ]


@router.get("/{album_id}", response_model=ResponseModel[AlbumResponse])
async def get_album(
    album_id: int,
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """获取专辑详情"""
    album = await album_oper.get_by_id(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    return ResponseModel(data=AlbumResponse.model_validate(album))


@router.get("/{album_id}/tracks", response_model=ResponseModel[List[TrackListResponse]])
async def get_album_tracks(
    album_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    track_oper: TrackOper = Depends(get_track_oper),
):
    """获取专辑的曲目列表"""
    tracks = await track_oper.get_by_album_id(album_id, skip=skip, limit=limit)

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

    return ResponseModel(data=track_list)


@router.get("/{album_id}/cover", response_class=FileResponse)
async def get_album_cover(
    album_id: int,
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """获取专辑封面"""
    album = await album_oper.get_by_id(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    if not album.cover_url:
        # 返回默认封面
        raise HTTPException(status_code=404, detail="专辑封面不存在")

    from pathlib import Path
    file_path = Path(album.cover_url)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="封面文件不存在")

    return FileResponse(path=str(file_path))


@router.post("/", response_model=ResponseModel[AlbumResponse])
async def create_album(
    album: AlbumCreate,
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """创建专辑"""
    created_album = await album_oper.create(**album.model_dump())
    return ResponseModel(
        message="专辑创建成功",
        data=AlbumResponse.model_validate(created_album),
    )


@router.put("/{album_id}", response_model=ResponseModel[AlbumResponse])
async def update_album(
    album_id: int,
    album: AlbumUpdate,
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """更新专辑"""
    updated_album = await album_oper.update(
        album_id, **{k: v for k, v in album.model_dump().items() if v is not None}
    )
    if not updated_album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    return ResponseModel(
        message="专辑更新成功",
        data=AlbumResponse.model_validate(updated_album),
    )


@router.delete("/{album_id}", response_model=ResponseModel[dict])
async def delete_album(
    album_id: int,
    album_oper: AlbumOper = Depends(get_album_oper),
):
    """删除专辑"""
    success = await album_oper.delete(album_id)
    if not success:
        raise HTTPException(status_code=404, detail="专辑不存在")

    return ResponseModel(message="专辑删除成功", data={"id": album_id})