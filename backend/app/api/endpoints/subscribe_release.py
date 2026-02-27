"""
订阅发布记录 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DatabaseManager, db_manager
from app.db.operations.subscribe_release import SubscribeReleaseOper
from app.db.models.subscribe_release import SubscribeRelease
from app.schemas.subscribe_release import (
    SubscribeReleaseBase,
    SubscribeReleaseCreate,
    SubscribeReleaseUpdate,
    SubscribeReleaseResponse,
    SubscribeReleaseListResponse,
    SubscribeReleaseStatistics,
)
from app.schemas.response import ResponseModel
from app.core.log import logger

router = APIRouter(tags=["订阅发布记录"])


async def get_db():
    """获取数据库会话"""
    async with db_manager.get_session() as session:
        yield session


@router.get("/{subscribe_id}/releases", response_model=SubscribeReleaseListResponse, summary="获取订阅发布记录")
async def get_subscribe_releases(
    subscribe_id: int,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取订阅的发布记录

    - **subscribe_id**: 订阅ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **status**: 下载状态（可选：pending, downloading, completed, failed）
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)

    if status:
        releases = await oper.get_by_status(status, subscribe_id=subscribe_id, limit=limit)
        releases = releases[skip:skip + limit]
        total = len(releases)
    else:
        releases = await oper.get_by_subscribe_id(subscribe_id, limit=limit)
        total = await oper.count(subscribe_id=subscribe_id)

    return SubscribeReleaseListResponse(total=total, items=releases)


@router.get("/{subscribe_id}/releases/{release_id}", response_model=SubscribeReleaseResponse, summary="获取发布记录详情")
async def get_release(subscribe_id: int, release_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据ID获取发布记录详情
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)
    release = await oper.get_by_id(release_id)

    if not release or release.subscribe_id != subscribe_id:
        raise HTTPException(status_code=404, detail=f"发布记录 {release_id} 不存在")

    return release


@router.get("/{subscribe_id}/releases/statistics", response_model=SubscribeReleaseStatistics, summary="获取订阅发布统计")
async def get_release_statistics(subscribe_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取订阅的发布统计信息
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)
    stats = await oper.get_release_statistics(subscribe_id)
    return SubscribeReleaseStatistics(**stats)


@router.put("/{subscribe_id}/releases/{release_id}", response_model=SubscribeReleaseResponse, summary="更新发布记录")
async def update_release(
    subscribe_id: int,
    release_id: int,
    release: SubscribeReleaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新发布记录（主要用于更新下载状态）
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)

    # 验证发布记录属于该订阅
    existing = await oper.get_by_id(release_id)
    if not existing or existing.subscribe_id != subscribe_id:
        raise HTTPException(status_code=404, detail=f"发布记录 {release_id} 不存在")

    updated_release = await oper.update(
        release_id,
        **release.model_dump(exclude_unset=True)
    )

    logger.info(f"更新发布记录: {release_id}, 状态: {release.download_status}")
    return updated_release


@router.delete("/{subscribe_id}/releases/{release_id}", response_model=ResponseModel, summary="删除发布记录")
async def delete_release(subscribe_id: int, release_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除发布记录
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)

    # 验证发布记录属于该订阅
    existing = await oper.get_by_id(release_id)
    if not existing or existing.subscribe_id != subscribe_id:
        raise HTTPException(status_code=404, detail=f"发布记录 {release_id} 不存在")

    success = await oper.delete(release_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"发布记录 {release_id} 不存在")

    logger.info(f"删除发布记录: {release_id}")
    return ResponseModel(success=True, message="发布记录删除成功")


@router.get("/releases/downloading", response_model=list[SubscribeReleaseResponse], summary="获取正在下载的发布记录")
async def get_downloading_releases(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    获取所有正在下载的发布记录
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)
    releases = await oper.get_downloading()
    return releases[:limit]


@router.get("/releases/failed", response_model=list[SubscribeReleaseResponse], summary="获取下载失败的发布记录")
async def get_failed_releases(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    获取所有下载失败的发布记录
    """
    oper = SubscribeReleaseOper(SubscribeRelease, db_manager)
    releases = await oper.get_failed(limit=limit)
    return releases