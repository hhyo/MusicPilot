"""
订阅 API 端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.log import logger
from app.schemas.response import ResponseModel, PaginatedResponse
from app.schemas.subscribe import (
    SubscribeBase,
    SubscribeCreate,
    SubscribeUpdate,
    SubscribeResponse,
    SubscribeListResponse,
    SubscribeRelease,
    CheckSubscribeResponse,
)

from app.db.operations.subscribe import SubscribeOper
from app.db.operations.subscribe_history import SubscribeHistoryOper


router = APIRouter(prefix="/subscribes", tags=["订阅"])


# 订阅管理端点


@router.get("", response_model=SubscribeListResponse)
async def get_subscribes(
    type: Optional[str] = Query(None, description="订阅类型：artist, album"),
    state: Optional[str] = Query(None, description="状态：active, paused"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅列表

    - **type**: 订阅类型（可选）
    - **state**: 状态（可选）
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    subscribe_oper = SubscribeOper(db)

    # 构建查询条件
    filters = {}
    if type:
        filters["type"] = type
    if state:
        filters["state"] = state

    subscribes = await subscribe_oper.get_all(skip=skip, limit=limit, **filters)

    total = await subscribe_oper.count(**filters)

    return SubscribeListResponse(
        total=total,
        subscribes=[SubscribeResponse.model_validate(s) for s in subscribes],
    )


@router.post("", response_model=SubscribeResponse)
async def create_subscribe(
    subscribe_data: SubscribeCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建订阅

    - **type**: 订阅类型（artist, album）
    - **musicbrainz_id**: MusicBrainz ID
    - **name**: 名称
    - **description**: 描述（可选）
    - **auto_download**: 是否自动下载（默认 True）
    - **download_format**: 下载格式（可选）
    """
    subscribe_oper = SubscribeOper(db)

    # 检查是否已存在
    existing = await subscribe_oper.get_by_musicbrainz_id(subscribe_data.musicbrainz_id)
    if existing:
        raise HTTPException(status_code=400, detail="订阅已存在")

    subscribe = await subscribe_oper.create(**subscribe_data.model_dump())

    logger.info(f"创建订阅: {subscribe.name} ({subscribe.type})")

    return SubscribeResponse.model_validate(subscribe)


@router.get("/{subscribe_id}", response_model=SubscribeResponse)
async def get_subscribe(
    subscribe_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅详情

    - **subscribe_id**: 订阅 ID
    """
    subscribe_oper = SubscribeOper(db)
    subscribe = await subscribe_oper.get_by_id(subscribe_id)

    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    return SubscribeResponse.model_validate(subscribe)


@router.put("/{subscribe_id}", response_model=SubscribeResponse)
async def update_subscribe(
    subscribe_id: int,
    subscribe_data: SubscribeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新订阅

    - **subscribe_id**: 订阅 ID
    - **name**: 名称（可选）
    - **description**: 描述（可选）
    - **auto_download**: 是否自动下载（可选）
    - **download_format**: 下载格式（可选）
    - **state**: 状态（可选）
    """
    subscribe_oper = SubscribeOper(db)
    subscribe = await subscribe_oper.get_by_id(subscribe_id)

    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    update_data = subscribe_data.model_dump(exclude_unset=True)
    subscribe = await subscribe_oper.update(subscribe_id, **update_data)

    logger.info(f"更新订阅: {subscribe.name}")

    return SubscribeResponse.model_validate(subscribe)


@router.delete("/{subscribe_id}")
async def delete_subscribe(
    subscribe_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    删除订阅

    - **subscribe_id**: 订阅 ID
    """
    subscribe_oper = SubscribeOper(db)
    subscribe = await subscribe_oper.get_by_id(subscribe_id)

    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    await subscribe_oper.delete(subscribe_id)

    logger.info(f"删除订阅: {subscribe.name}")

    return ResponseModel(message="订阅已删除")


# 订阅检查端点


@router.post("/{subscribe_id}/check", response_model=CheckSubscribeResponse)
async def check_subscribe(
    subscribe_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    检查订阅更新

    - **subscribe_id**: 订阅 ID

    此端点会触发订阅更新检查，返回新发现的发布数量。
    """
    subscribe_oper = SubscribeOper(db)
    subscribe = await subscribe_oper.get_by_id(subscribe_id)

    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    # TODO: 调用 SubscribeChain 检查更新
    # chain = SubscribeChain(db_manager=db)
    # new_releases = await chain.check(subscribe_id)

    # 临时返回模拟数据
    new_releases = 0

    # 更新检查时间
    await subscribe_oper.update_check_time(subscribe_id)

    logger.info(f"检查订阅更新: {subscribe.name}, 新发布: {new_releases}")

    return CheckSubscribeResponse(
        subscribe_id=subscribe_id,
        new_releases=new_releases,
        message=f"发现 {new_releases} 个新发布" if new_releases > 0 else "没有新发布",
    )


@router.get("/{subscribe_id}/releases", response_model=List[SubscribeRelease])
async def get_subscribe_releases(
    subscribe_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅的发布历史

    - **subscribe_id**: 订阅 ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    subscribe_oper = SubscribeOper(db)
    subscribe = await subscribe_oper.get_by_id(subscribe_id)

    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    history_oper = SubscribeHistoryOper(db)
    histories = await history_oper.get_by_subscribe(subscribe_id, skip=skip, limit=limit)

    return [
        SubscribeRelease(
            id=h.id,
            musicbrainz_id=h.musicbrainz_id,
            title=h.title,
            release_date=h.release_date,
            release_type=h.release_type,
            downloaded=h.downloaded,
            download_status=h.download_status,
            file_path=h.file_path,
            created_at=h.created_at,
        )
        for h in histories
    ]


@router.get("/{subscribe_id}/stats")
async def get_subscribe_stats(
    subscribe_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅统计信息

    - **subscribe_id**: 订阅 ID
    """
    subscribe_oper = SubscribeOper(db)
    subscribe = await subscribe_oper.get_by_id(subscribe_id)

    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    history_oper = SubscribeHistoryOper(db)
    stats = await history_oper.get_stats(subscribe_id)

    return ResponseModel(data=stats)
