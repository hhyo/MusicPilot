"""
订阅 API 端点
"""

from fastapi import APIRouter, HTTPException, Query

from app.chain.subscribe import SubscribeChain
from app.db import db_manager
from app.db.models.subscribe import Subscribe
from app.db.operations.subscribe import SubscribeOper
from app.schemas.subscribe import (
    SubscribeCreate,
    SubscribeListResponse,
    SubscribeResponse,
    SubscribeUpdate,
)

router = APIRouter()

subscribe_oper = SubscribeOper(Subscribe, db_manager)
subscribe_chain = SubscribeChain()


@router.get("", response_model=SubscribeListResponse)
async def list_subscribes(
    type: str | None = Query(None, description="订阅类型"),
    state: str | None = Query(None, description="状态"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    获取订阅列表
    """
    subscribes = await subscribe_oper.list(skip=skip, limit=limit)

    # 过滤
    if type:
        subscribes = [s for s in subscribes if s.type == type]
    if state:
        subscribes = [s for s in subscribes if s.state == state]

    return SubscribeListResponse(
        items=[SubscribeResponse.from_orm(s) for s in subscribes],
        total=len(subscribes),
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{subscribe_id}", response_model=SubscribeResponse)
async def get_subscribe(subscribe_id: int):
    """
    获取订阅详情
    """
    subscribe = await subscribe_oper.get_by_id(subscribe_id)
    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    return SubscribeResponse.from_orm(subscribe)


@router.post("", response_model=SubscribeResponse)
async def create_subscribe(subscribe: SubscribeCreate):
    """
    创建订阅
    """
    # 验证字段
    if subscribe.type in ("artist", "album"):
        if not subscribe.musicbrainz_id:
            raise HTTPException(status_code=400, detail="MusicBrainz ID 不能为空")
    else:
        if not subscribe.playlist_id:
            raise HTTPException(status_code=400, detail="歌单/榜单 ID 不能为空")

    # 创建订阅
    subscribe_data = subscribe.dict()
    result = await subscribe_oper.create(subscribe_data)

    return SubscribeResponse.from_orm(result)


@router.put("/{subscribe_id}", response_model=SubscribeResponse)
async def update_subscribe(subscribe_id: int, subscribe: SubscribeUpdate):
    """
    更新订阅
    """
    # 检查订阅是否存在
    existing = await subscribe_oper.get_by_id(subscribe_id)
    if not existing:
        raise HTTPException(status_code=404, detail="订阅不存在")

    # 更新订阅
    update_data = subscribe.dict(exclude_unset=True)
    result = await subscribe_oper.update(subscribe_id, update_data)

    return SubscribeResponse.from_orm(result)


@router.delete("/{subscribe_id}")
async def delete_subscribe(subscribe_id: int):
    """
    删除订阅
    """
    # 检查订阅是否存在
    existing = await subscribe_oper.get_by_id(subscribe_id)
    if not existing:
        raise HTTPException(status_code=404, detail="订阅不存在")

    # 删除订阅
    await subscribe_oper.delete(subscribe_id)

    return {"message": "删除成功"}


@router.post("/{subscribe_id}/check")
async def check_subscribe(subscribe_id: int):
    """
    检查订阅（手动触发）
    """
    # 检查订阅是否存在
    subscribe = await subscribe_oper.get_by_id(subscribe_id)
    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    try:
        if subscribe.type == "artist":
            releases = await subscribe_chain.check_artist(
                subscribe_id,
                subscribe.musicbrainz_id or "",
            )
        elif subscribe.type == "album":
            release = await subscribe_chain.check_album(
                subscribe_id,
                subscribe.musicbrainz_id or "",
            )
            releases = [release] if release else []
        elif subscribe.type in ("playlist", "chart"):
            releases = await subscribe_chain.check_playlist(
                subscribe_id,
                subscribe.playlist_id or "",
                subscribe.source_type,
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的订阅类型")

        return {
            "message": "检查完成",
            "new_releases": len(releases),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}") from e


@router.post("/check-all")
async def check_all_subscribes():
    """
    检查所有订阅
    """
    try:
        stats = await subscribe_chain.check_all()
        return {
            "message": "检查完成",
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}") from e


@router.get("/{subscribe_id}/releases")
async def get_subscribe_releases(
    subscribe_id: int,
    download_status: str | None = Query(None, description="下载状态"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    获取订阅的发布记录
    """
    # 检查订阅是否存在
    subscribe = await subscribe_oper.get_by_id(subscribe_id)
    if not subscribe:
        raise HTTPException(status_code=404, detail="订阅不存在")

    # 获取发布记录
    releases = await subscribe_chain.get_releases(subscribe_id, limit=limit)

    # 过滤
    if download_status:
        releases = [r for r in releases if r.download_status == download_status]

    return {
        "items": releases,
        "total": len(releases),
        "page": skip // limit + 1,
        "page_size": limit,
    }
