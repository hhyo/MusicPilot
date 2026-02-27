"""
封面图片 API
封面下载、缓存和管理
"""

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.log import logger
from app.db import get_db
from app.db.operations.album import AlbumOper
from app.schemas.response import ResponseModel

router = APIRouter()

# 封面缓存目录
COVER_CACHE_DIR = settings.cache_path / "covers"
COVER_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/{cover_id}", response_class=FileResponse)
async def get_cover(cover_id: str):
    """
    获取封面图片

    - **cover_id**: 封面 ID 或 MusicBrainz ID
    """
    cover_path = COVER_CACHE_DIR / f"{cover_id}.jpg"

    # 检查缓存
    if cover_path.exists():
        return FileResponse(path=str(cover_path), media_type="image/jpeg")

    # 从 MusicBrainz 下载
    try:
        import musicbrainzngs

        from app.core.config import settings

        musicbrainzngs.set_useragent(
            f"{settings.musicbrainz_app_name}/{settings.musicbrainz_app_version}",
            "https://github.com/hhyo/MusicPilot",
        )

        cover_url = musicbrainzngs.get_release_cover_url(cover_id)
        if not cover_url:
            raise HTTPException(status_code=404, detail="封面不存在")

        # 下载封面
        async with aiofiles.ClientSession() as session, session.get(cover_url) as response:
            if response.status != 200:
                raise HTTPException(status_code=404, detail="封面下载失败")

            content = await response.read()

        # 保存到缓存
        await aiofiles.write(cover_path, content)

        return FileResponse(path=str(cover_path), media_type="image/jpeg")

    except Exception as e:
        logger.error(f"获取封面失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取封面失败: {e}") from e


@router.post("/albums/{album_id}/cover", response_model=ResponseModel[dict])
async def download_album_cover(
    album_id: int,
    album_oper: AlbumOper = Depends(get_db),
):
    """
    下载专辑封面

    - **album_id**: 专辑 ID
    """
    album = await album_oper.get_by_id(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    # 如果已经有 MusicBrainz ID，直接使用
    if album.musicbrainz_id:
        # 触发封面获取（通过 GET /covers/{id}）
        return ResponseModel(
            data={
                "album_id": album_id,
                "cover_url": f"/api/v1/covers/{album.musicbrainz_id}",
                "status": "downloading",
            }
        )

    # 否则先查询 MusicBrainz
    try:
        import musicbrainzngs

        from app.core.config import settings

        musicbrainzngs.set_useragent(
            f"{settings.musicbrainz_app_name}/{settings.musicbrainz_app_version}",
            "https://github.com/hhyo/MusicPilot",
        )

        # 搜索专辑
        if album.title:
            result = musicbrainzngs.search_release_groups(album.title, limit=5)
            for rg in result.get("release-group-list", []):
                # 简单匹配标题
                if rg.get("title") == album.title:
                    mb_id = rg.get("id")
                    # 更新数据库
                    await album_oper.update(album_id, musicbrainz_id=mb_id)
                    return ResponseModel(
                        data={
                            "album_id": album_id,
                            "musicbrainz_id": mb_id,
                            "cover_url": f"/api/v1/covers/{mb_id}",
                            "status": "found",
                        }
                    )

        return ResponseModel(
            data={
                "album_id": album_id,
                "status": "not_found",
                "message": "未找到匹配的 MusicBrainz 专辑",
            }
        )

    except Exception as e:
        logger.error(f"查询专辑封面失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询专辑封面失败: {e}") from e


@router.post("/batch", response_model=ResponseModel[dict])
async def batch_download_covers(
    album_ids: list[int],
    album_oper: AlbumOper = Depends(get_db),
):
    """
    批量下载专辑封面

    - **album_ids**: 专辑 ID 列表
    """
    if not album_ids:
        raise HTTPException(status_code=400, detail="必须提供 album_ids")

    results = []

    for album_id in album_ids:
        try:
            # 复用单个下载逻辑
            album = await album_oper.get_by_id(album_id)
            if not album:
                results.append(
                    {
                        "album_id": album_id,
                        "status": "not_found",
                    }
                )
                continue

            cover_url = f"/api/v1/covers/{album.musicbrainz_id}" if album.musicbrainz_id else None

            if cover_url:
                results.append(
                    {
                        "album_id": album_id,
                        "cover_url": cover_url,
                        "status": "ready",
                    }
                )
            else:
                results.append(
                    {
                        "album_id": album_id,
                        "status": "no_musicbrainz_id",
                    }
                )

        except Exception as e:
            logger.error(f"处理专辑 {album_id} 失败: {e}")
            results.append(
                {
                    "album_id": album_id,
                    "status": "error",
                    "error": str(e),
                }
            )

    return ResponseModel(
        message=f"批量处理完成: {len([r for r in results if r['status'] == 'ready'])} 个封面就绪",
        data={
            "total": len(album_ids),
            "ready": len([r for r in results if r["status"] == "ready"]),
            "results": results,
        },
    )


@router.post("/custom/{album_id}", response_model=ResponseModel[dict])
async def upload_custom_cover(
    album_id: int,
    file: UploadFile = File(...),
    album_oper: AlbumOper = Depends(get_db),
):
    """
    上传自定义封面

    - **album_id**: 专辑 ID
    - **file**: 封面图片文件
    """
    album = await album_oper.get_by_id(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")

    # 生成封面 ID
    import time

    cover_id = f"custom_{album_id}_{int(time.time())}"

    # 保存文件
    cover_path = COVER_CACHE_DIR / f"{cover_id}.jpg"
    async with aiofiles.open(cover_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 更新数据库
    await album_oper.update(album_id, cover_id=cover_id)

    return ResponseModel(
        message="自定义封面上传成功",
        data={
            "album_id": album_id,
            "cover_id": cover_id,
            "cover_url": f"/api/v1/covers/{cover_id}",
        },
    )


@router.delete("/{album_id}/cover", response_model=ResponseModel[dict])
async def delete_cover(
    album_id: int,
    album_oper: AlbumOper = Depends(get_db),
):
    """
    删除专辑封面

    - **album_id**: 专辑 ID
    """
    album = await album_oper.get_by_id(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    # 删除文件
    if album.cover_id:
        cover_path = COVER_CACHE_DIR / f"{album.cover_id}.jpg"
        if cover_path.exists():
            try:
                await aiofiles.remove(cover_path)
            except Exception as e:
                logger.error(f"删除封面文件失败: {e}")

    # 清空数据库中的封面 ID
    await album_oper.update(album_id, cover_id=None)

    return ResponseModel(message="封面删除成功", data={"album_id": album_id})
