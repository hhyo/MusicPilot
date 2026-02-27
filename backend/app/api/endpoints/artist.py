"""
Artist API 端点
艺术家相关 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.operations.artist import ArtistOper
from app.schemas.artist import (
    ArtistCreate,
    ArtistListResponse,
    ArtistResponse,
    ArtistUpdate,
)
from app.schemas.response import PaginatedResponse, ResponseModel

router = APIRouter()


def get_artist_oper(db: AsyncSession = Depends(get_db)) -> ArtistOper:
    """获取 Artist 操作实例"""
    from app.db import db_manager

    return ArtistOper(db_manager)


@router.get("/", response_model=PaginatedResponse[ArtistListResponse])
async def get_artists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    artist_oper: ArtistOper = Depends(get_artist_oper),
):
    """
    获取艺术家列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数（最多 100）
    - **search**: 搜索关键词（按名称搜索）
    """
    if search:
        artists = await artist_oper.search_by_name(search, limit=limit)
    else:
        artists = await artist_oper.get_all(skip=skip, limit=limit)

    total = await artist_oper.count()
    total_pages = (total + limit - 1) // limit
    page = skip // limit + 1

    artist_list = [
        ArtistListResponse(
            id=a.id,
            musicbrainz_id=a.musicbrainz_id,
            name=a.name,
            image_url=a.image_url,
            genres=a.genres,
            rating=a.rating,
        )
        for a in artists
    ]

    return PaginatedResponse(
        data=artist_list,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/top", response_model=list[ArtistListResponse])
async def get_top_artists(
    limit: int = Query(50, ge=1, le=100),
    artist_oper: ArtistOper = Depends(get_artist_oper),
):
    """获取评分最高的艺术家"""
    artists = await artist_oper.get_top_rated(limit=limit)

    return [
        ArtistListResponse(
            id=a.id,
            musicbrainz_id=a.musicbrainz_id,
            name=a.name,
            image_url=a.image_url,
            genres=a.genres,
            rating=a.rating,
        )
        for a in artists
    ]


@router.get("/{artist_id}", response_model=ResponseModel[ArtistResponse])
async def get_artist(
    artist_id: int,
    artist_oper: ArtistOper = Depends(get_artist_oper),
):
    """获取艺术家详情"""
    artist = await artist_oper.get_by_id(artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="艺术家不存在")

    return ResponseModel(data=ArtistResponse.model_validate(artist))


@router.post("/", response_model=ResponseModel[ArtistResponse])
async def create_artist(
    artist: ArtistCreate,
    artist_oper: ArtistOper = Depends(get_artist_oper),
):
    """创建艺术家"""
    created_artist = await artist_oper.create(**artist.model_dump())
    return ResponseModel(
        message="艺术家创建成功",
        data=ArtistResponse.model_validate(created_artist),
    )


@router.put("/{artist_id}", response_model=ResponseModel[ArtistResponse])
async def update_artist(
    artist_id: int,
    artist: ArtistUpdate,
    artist_oper: ArtistOper = Depends(get_artist_oper),
):
    """更新艺术家"""
    updated_artist = await artist_oper.update(
        artist_id, **{k: v for k, v in artist.model_dump().items() if v is not None}
    )
    if not updated_artist:
        raise HTTPException(status_code=404, detail="艺术家不存在")

    return ResponseModel(
        message="艺术家更新成功",
        data=ArtistResponse.model_validate(updated_artist),
    )


@router.delete("/{artist_id}", response_model=ResponseModel[dict])
async def delete_artist(
    artist_id: int,
    artist_oper: ArtistOper = Depends(get_artist_oper),
):
    """删除艺术家"""
    success = await artist_oper.delete(artist_id)
    if not success:
        raise HTTPException(status_code=404, detail="艺术家不存在")

    return ResponseModel(message="艺术家删除成功", data={"id": artist_id})
