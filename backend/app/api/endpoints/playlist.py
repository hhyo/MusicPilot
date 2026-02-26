"""
Playlist API 端点
播放列表相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.operations.playlist import PlaylistOper
from app.db.operations.track import TrackOper
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistWithTracksResponse,
    PlaylistListResponse,
    AddTrackRequest,
    BatchAddTracksRequest,
    ReorderTracksRequest,
)
from app.schemas.response import ResponseModel, PaginatedResponse


router = APIRouter()


def get_playlist_oper(db: AsyncSession = Depends(get_db)) -> PlaylistOper:
    """获取 Playlist 操作实例"""
    from app.db import db_manager
    return PlaylistOper(db_manager)


@router.get("/", response_model=PaginatedResponse[PlaylistListResponse])
async def get_playlists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """获取播放列表"""
    playlists = await playlist_oper.get_all(skip=skip, limit=limit)

    total = await playlist_oper.count()
    total_pages = (total + limit - 1) // limit
    page = skip // limit + 1

    playlist_list = [
        PlaylistListResponse(
            id=p.id,
            type=p.type,
            name=p.name,
            cover_url=p.cover_url,
            is_public=p.is_public,
            created_at=p.created_at,
        )
        for p in playlists
    ]

    return PaginatedResponse(
        data=playlist_list,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/smart", response_model=PaginatedResponse[PlaylistListResponse])
async def get_smart_playlists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """获取智能播放列表"""
    playlists = await playlist_oper.get_smart_playlists(skip=skip, limit=limit)

    total = await playlist_oper.count(type="smart")
    total_pages = (total + limit - 1) // limit
    page = skip // limit + 1

    playlist_list = [
        PlaylistListResponse(
            id=p.id,
            type=p.type,
            name=p.name,
            cover_url=p.cover_url,
            is_public=p.is_public,
            created_at=p.created_at,
        )
        for p in playlists
    ]

    return PaginatedResponse(
        data=playlist_list,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/{playlist_id}", response_model=ResponseModel[PlaylistWithTracksResponse])
async def get_playlist(
    playlist_id: int,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """获取播放列表详情（包含曲目）"""
    playlist = await playlist_oper.get_with_tracks(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    tracks = [
        {
            "id": t.id,
            "playlist_id": t.playlist_id,
            "track_id": t.track_id,
            "position": t.position,
            "added_at": t.added_at,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in playlist.tracks
    ]

    return ResponseModel(
        data=PlaylistWithTracksResponse(
            id=playlist.id,
            type=playlist.type,
            name=playlist.name,
            description=playlist.description,
            cover_url=playlist.cover_url,
            smart_query=playlist.smart_query,
            order=playlist.order,
            is_public=playlist.is_public,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
            tracks=tracks,
        )
    )


@router.post("/", response_model=ResponseModel[PlaylistResponse])
async def create_playlist(
    playlist: PlaylistCreate,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """创建播放列表"""
    created_playlist = await playlist_oper.create(**playlist.model_dump())
    return ResponseModel(
        message="播放列表创建成功",
        data=PlaylistResponse.model_validate(created_playlist),
    )


@router.put("/{playlist_id}", response_model=ResponseModel[PlaylistResponse])
async def update_playlist(
    playlist_id: int,
    playlist: PlaylistUpdate,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """更新播放列表"""
    updated_playlist = await playlist_oper.update(
        playlist_id, **{k: v for k, v in playlist.model_dump().items() if v is not None}
    )
    if not updated_playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    return ResponseModel(
        message="播放列表更新成功",
        data=PlaylistResponse.model_validate(updated_playlist),
    )


@router.delete("/{playlist_id}", response_model=ResponseModel[dict])
async def delete_playlist(
    playlist_id: int,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """删除播放列表"""
    success = await playlist_oper.delete(playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    return ResponseModel(message="播放列表删除成功", data={"id": playlist_id})


@router.post("/{playlist_id}/tracks", response_model=ResponseModel[dict])
async def add_track_to_playlist(
    playlist_id: int,
    request: AddTrackRequest,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """添加曲目到播放列表"""
    playlist = await playlist_oper.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    playlist_track = await playlist_oper.add_track(
        playlist_id, request.track_id, request.position
    )

    return ResponseModel(
        message="曲目添加成功",
        data={"playlist_id": playlist_id, "track_id": request.track_id, "position": playlist_track.position},
    )


@router.post("/{playlist_id}/tracks/batch", response_model=ResponseModel[dict])
async def batch_add_tracks_to_playlist(
    playlist_id: int,
    request: BatchAddTracksRequest,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """批量添加曲目到播放列表"""
    playlist = await playlist_oper.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    added_tracks = []
    for track_id in request.track_ids:
        playlist_track = await playlist_oper.add_track(playlist_id, track_id)
        added_tracks.append({"track_id": track_id, "position": playlist_track.position})

    return ResponseModel(
        message=f"成功添加 {len(added_tracks)} 首曲目",
        data={"playlist_id": playlist_id, "tracks": added_tracks},
    )


@router.delete("/{playlist_id}/tracks/{track_id}", response_model=ResponseModel[dict])
async def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """从播放列表移除曲目"""
    success = await playlist_oper.remove_track(playlist_id, track_id)
    if not success:
        raise HTTPException(status_code=404, detail="曲目不在播放列表中")

    return ResponseModel(
        message="曲目移除成功",
        data={"playlist_id": playlist_id, "track_id": track_id},
    )


@router.put("/{playlist_id}/tracks/reorder", response_model=ResponseModel[dict])
async def reorder_playlist_tracks(
    playlist_id: int,
    request: ReorderTracksRequest,
    playlist_oper: PlaylistOper = Depends(get_playlist_oper),
):
    """重新排序播放列表曲目"""
    success = await playlist_oper.reorder_tracks(playlist_id, request.track_ids)
    if not success:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    return ResponseModel(
        message="曲目排序成功",
        data={"playlist_id": playlist_id},
    )
