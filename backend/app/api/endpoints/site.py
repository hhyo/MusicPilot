"""
站点管理 API 端点
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DatabaseManager, db_manager
from app.db.operations.site import SiteOper
from app.db.models.site import Site
from app.schemas.site import (
    SiteBase,
    SiteCreate,
    SiteUpdate,
    SiteResponse,
    SiteListResponse,
    TestSiteRequest,
    TestSiteResponse,
)
from app.schemas.response import ResponseModel
from app.core.log import logger

router = APIRouter(prefix="/sites", tags=["站点管理"])


async def get_db():
    """获取数据库会话"""
    async with db_manager.get_session() as session:
        yield session


@router.get("", response_model=SiteListResponse, summary="获取站点列表")
async def get_sites(
    skip: int = 0,
    limit: int = 100,
    enabled: bool = None,
    downloader: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取站点列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **enabled**: 是否启用（可选）
    - **downloader**: 下载器类型（可选）
    """
    oper = SiteOper(Site, db_manager)

    if enabled is not None:
        sites = await oper.get_all(skip=skip, limit=limit, enabled=enabled)
    elif downloader is not None:
        sites = await oper.get_by_downloader(downloader)
        sites = sites[skip:skip + limit]
    else:
        sites = await oper.get_all(skip=skip, limit=limit)

    total = await oper.count() if enabled is None and downloader is None else len(sites)

    return SiteListResponse(total=total, items=sites)


@router.get("/enabled", response_model=List[SiteResponse], summary="获取启用的站点")
async def get_enabled_sites(db: AsyncSession = Depends(get_db)):
    """
    获取所有启用的站点，按优先级排序
    """
    oper = SiteOper(Site, db_manager)
    sites = await oper.get_enabled()
    return sites


@router.get("/{site_id}", response_model=SiteResponse, summary="获取站点详情")
async def get_site(site_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据ID获取站点详情
    """
    oper = SiteOper(Site, db_manager)
    site = await oper.get_by_id(site_id)

    if not site:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")

    return site


@router.post("", response_model=SiteResponse, summary="创建站点")
async def create_site(site: SiteCreate, db: AsyncSession = Depends(get_db)):
    """
    创建新站点
    """
    oper = SiteOper(Site, db_manager)
    new_site = await oper.create(**site.model_dump())
    logger.info(f"创建站点: {new_site.name}")
    return new_site


@router.put("/{site_id}", response_model=SiteResponse, summary="更新站点")
async def update_site(site_id: int, site: SiteUpdate, db: AsyncSession = Depends(get_db)):
    """
    更新站点信息
    """
    oper = SiteOper(Site, db_manager)
    updated_site = await oper.update(site_id, **site.model_dump(exclude_unset=True))

    if not updated_site:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")

    logger.info(f"更新站点: {site_id}")
    return updated_site


@router.delete("/{site_id}", response_model=ResponseModel, summary="删除站点")
async def delete_site(site_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除站点
    """
    oper = SiteOper(Site, db_manager)
    success = await oper.delete(site_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")

    logger.info(f"删除站点: {site_id}")
    return ResponseModel(success=True, message="站点删除成功")


@router.post("/{site_id}/toggle", response_model=SiteResponse, summary="切换站点启用状态")
async def toggle_site(site_id: int, db: AsyncSession = Depends(get_db)):
    """
    切换站点的启用状态
    """
    oper = SiteOper(Site, db_manager)
    site = await oper.toggle_enabled(site_id)

    if not site:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")

    logger.info(f"切换站点启用状态: {site_id}, 新状态: {site.enabled}")
    return site


@router.post("/test", response_model=TestSiteResponse, summary="测试站点连接")
async def test_site(request: TestSiteRequest, db: AsyncSession = Depends(get_db)):
    """
    测试站点连接
    """
    oper = SiteOper(Site, db_manager)
    success, message = await oper.test_connection(request.id)
    return TestSiteResponse(success=success, message=message)