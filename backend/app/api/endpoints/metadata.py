"""
元数据编辑 API
批量编辑和回写功能
"""

from fastapi import APIRouter, Depends, HTTPException

from app.chain.metadata import MetadataChain
from app.core.cache import AsyncFileCache
from app.core.config import settings
from app.core.event import EventManager
from app.core.log import logger
from app.core.module import ModuleManager
from app.core.plugin import PluginManager
from app.db import get_db
from app.db.operations.album import AlbumOper
from app.db.operations.artist import ArtistOper
from app.db.operations.track import TrackOper
from app.schemas.response import ResponseModel

router = APIRouter()


async def get_metadata_chain():
    """获取 MetadataChain 实例"""
    event_manager = EventManager()
    module_manager = ModuleManager()
    plugin_manager = PluginManager(event_manager)
    cache = AsyncFileCache(settings.cache_path, settings.cache_ttl)

    return MetadataChain(
        event_manager=event_manager,
        module_manager=module_manager,
        plugin_manager=plugin_manager,
        cache=cache,
    )


@router.patch("/artists/batch", response_model=ResponseModel[dict])
async def batch_update_artists(
    artist_ids: list[int],
    updates: dict,
    artist_oper: ArtistOper = Depends(get_db),
):
    """
    批量更新艺术家信息

    - **artist_ids**: 艺术家 ID 列表
    - **updates**: 要更新的字段（如: {"rating": 4.5, "tags": ["Rock"]}）
    """
    if not artist_ids:
        raise HTTPException(status_code=400, detail="必须提供 artist_ids")

    success_count = 0
    failed_count = 0
    failed_ids = []

    for artist_id in artist_ids:
        try:
            updated = await artist_oper.update(
                artist_id, **{k: v for k, v in updates.items() if v is not None}
            )
            if updated:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(artist_id)
        except Exception as e:
            failed_count += 1
            failed_ids.append(artist_id)
            logger.error(f"更新艺术家 {artist_id} 失败: {e}")

    return ResponseModel(
        message=f"批量更新完成: {success_count} 成功, {failed_count} 失败",
        data={
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
        },
    )


@router.patch("/albums/batch", response_model=ResponseModel[dict])
async def batch_update_albums(
    album_ids: list[int],
    updates: dict,
    album_oper: AlbumOper = Depends(get_db),
):
    """
    批量更新专辑信息

    - **album_ids**: 专辑 ID 列表
    - **updates**: 要更新的字段
    """
    if not album_ids:
        raise HTTPException(status_code=400, detail="必须提供 album_ids")

    success_count = 0
    failed_count = 0
    failed_ids = []

    for album_id in album_ids:
        try:
            updated = await album_oper.update(
                album_id, **{k: v for k, v in updates.items() if v is not None}
            )
            if updated:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(album_id)
        except Exception as e:
            failed_count += 1
            failed_ids.append(album_id)
            logger.error(f"更新专辑 {album_id} 失败: {e}")

    return ResponseModel(
        message=f"批量更新完成: {success_count} 成功, {failed_count} 失败",
        data={
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
        },
    )


@router.patch("/tracks/batch", response_model=ResponseModel[dict])
async def batch_update_tracks(
    track_ids: list[int],
    updates: dict,
    track_oper: TrackOper = Depends(get_db),
):
    """
    批量更新曲目信息

    - **track_ids**: 曲目 ID 列表
    - **updates**: 要更新的字段
    """
    if not track_ids:
        raise HTTPException(status_code=400, detail="必须提供 track_ids")

    success_count = 0
    failed_count = 0
    failed_ids = []

    for track_id in track_ids:
        try:
            updated = await track_oper.update(
                track_id, **{k: v for k, v in updates.items() if v is not None}
            )
            if updated:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(track_id)
        except Exception as e:
            failed_count += 1
            failed_ids.append(track_id)
            logger.error(f"更新曲目 {track_id} 失败: {e}")

    return ResponseModel(
        message=f"批量更新完成: {success_count} 成功, {failed_count} 失败",
        data={
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
        },
    )


@router.post("/tracks/{track_id}/rewrite", response_model=ResponseModel[dict])
async def rewrite_track_metadata(
    track_id: int,
    metadata_chain: MetadataChain = Depends(get_metadata_chain),
):
    """
    回写元数据到音频文件

    - **track_id**: 曲目 ID
    """
    try:
        success = await metadata_chain.rewrite_metadata(track_id)

        if success:
            return ResponseModel(message="元数据回写成功", data={"track_id": track_id})
        else:
            raise HTTPException(status_code=400, detail="元数据回写失败")

    except Exception as e:
        logger.error(f"回写元数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"回写元数据失败: {e}") from e


@router.post("/tracks/batch/rewrite", response_model=ResponseModel[dict])
async def batch_rewrite_tracks(
    track_ids: list[int],
    metadata_chain: MetadataChain = Depends(get_metadata_chain),
):
    """
    批量回写元数据

    - **track_ids**: 曲目 ID 列表
    """
    if not track_ids:
        raise HTTPException(status_code=400, detail="必须提供 track_ids")

    success_count = 0
    failed_count = 0
    failed_ids = []

    for track_id in track_ids:
        try:
            success = await metadata_chain.rewrite_metadata(track_id)
            if success:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(track_id)
        except Exception as e:
            failed_count += 1
            failed_ids.append(track_id)
            logger.error(f"回写曲目 {track_id} 元数据失败: {e}")

    return ResponseModel(
        message=f"批量回写完成: {success_count} 成功, {failed_count} 失败",
        data={
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
        },
    )


@router.get("/validate/{track_id}", response_model=ResponseModel[dict])
async def validate_track_metadata(
    track_id: int,
    track_oper: TrackOper = Depends(get_db),
):
    """
    验证曲目元数据完整性

    - **track_id**: 曲目 ID
    """
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    issues = []

    # 检查必需字段
    if not track.title:
        issues.append("缺少标题")
    if not track.artist_id:
        issues.append("缺少艺术家")
    if not track.path:
        issues.append("缺少文件路径")

    # 检查文件是否存在
    if track.path:
        from pathlib import Path

        if not Path(track.path).exists():
            issues.append("文件不存在")

    # 检查时长
    if not track.duration or track.duration == 0:
        issues.append("时长为空")

    return ResponseModel(
        data={
            "track_id": track_id,
            "is_valid": len(issues) == 0,
            "issues": issues,
        }
    )
