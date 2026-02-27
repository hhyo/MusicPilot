"""
Library API 端点
音乐库相关 API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.db import get_db
from app.db.operations.library import LibraryOper
from app.db.operations.track import TrackOper
from app.schemas.library import (
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryListResponse,
    ScanLibraryRequest,
)
from app.schemas.response import ResponseModel, PaginatedResponse
from app.chain.metadata import MetadataChain
from app.core.event import EventManager
from app.core.module import ModuleManager
from app.core.plugin import PluginManager
from app.core.cache import AsyncFileCache
from app.core.config import settings
from app.core.log import logger
import asyncio

router = APIRouter()

# 扫描任务状态
scan_tasks: dict[str, dict] = {}


def get_library_oper(db: AsyncSession = Depends(get_db)) -> LibraryOper:
    """获取 Library 操作实例"""
    from app.db import db_manager

    return LibraryOper(db_manager)


def get_track_oper(db: AsyncSession = Depends(get_db)) -> TrackOper:
    """获取 Track 操作实例"""
    from app.db import db_manager

    return TrackOper(db_manager)


async def get_metadata_chain():
    """获取 MetadataChain 实例"""
    # 创建核心组件
    event_manager = EventManager()
    module_manager = ModuleManager()
    plugin_manager = PluginManager(event_manager)
    cache = AsyncFileCache(settings.cache_path, settings.cache_ttl)

    # 返回 MetadataChain
    return MetadataChain(
        event_manager=event_manager,
        module_manager=module_manager,
        plugin_manager=plugin_manager,
        cache=cache,
    )


async def recursive_scan(directory: Path, recursive: bool = True) -> List[str]:
    """
    递归扫描目录，查找音乐文件

    Args:
        directory: 目录路径
        recursive: 是否递归扫描

    Returns:
        音乐文件路径列表
    """
    music_extensions = [".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma"]
    music_files = []

    if not directory.exists():
        logger.warning(f"目录不存在: {directory}")
        return music_files

    if recursive:
        # 递归扫描
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in music_extensions:
                music_files.append(str(file_path))
    else:
        # 只扫描当前目录
        for file_path in directory.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in music_extensions:
                music_files.append(str(file_path))

    # 按文件名排序
    music_files.sort()
    logger.info(f"扫描完成，找到 {len(music_files)} 个音乐文件")

    return music_files


async def process_file_batch(file_paths: List[str], metadata_chain: MetadataChain, task_id: str):
    """
    批量处理文件（后台任务）

    Args:
        file_paths: 文件路径列表
        metadata_chain: MetadataChain 实例
        task_id: 任务 ID
    """
    total = len(file_paths)
    success = 0
    failed = 0

    scan_tasks[task_id]["status"] = "scanning"
    scan_tasks[task_id]["total"] = total
    scan_tasks[task_id]["processed"] = 0
    scan_tasks[task_id]["success"] = 0
    scan_tasks[task_id]["failed"] = 0

    results = await metadata_chain.batch_recognize(file_paths)

    for result in results:
        scan_tasks[task_id]["processed"] += 1

        if result.get("success"):
            success += 1
            scan_tasks[task_id]["success"] += 1
        else:
            failed += 1
            scan_tasks[task_id]["failed"] += 1

        # 更新进度（每处理 10 个文件）
        if scan_tasks[task_id]["processed"] % 10 == 0:
            logger.info(f"扫描进度: {scan_tasks[task_id]['processed']}/{total}")

    scan_tasks[task_id]["status"] = "completed"
    scan_tasks[task_id]["success_count"] = success
    scan_tasks[task_id]["failed_count"] = failed
    logger.info(f"扫描完成: {success} 成功, {failed} 失败")


@router.get("/", response_model=PaginatedResponse[LibraryListResponse])
async def get_libraries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    library_oper: LibraryOper = Depends(get_library_oper),
):
    """获取音乐库列表"""
    libraries = await library_oper.get_all(skip=skip, limit=limit)

    total = await library_oper.count()
    total_pages = (total + limit - 1) // limit
    page = skip // limit + 1

    library_list = [
        LibraryListResponse(
            id=lib.id,
            name=lib.name,
            path=lib.path,
            last_scan_time=lib.last_scan_time,
            auto_scan=lib.auto_scan,
            track_count=lib.track_count,
            album_count=lib.album_count,
            artist_count=lib.artist_count,
            total_size=lib.total_size,
        )
        for lib in libraries
    ]

    return PaginatedResponse(
        data=library_list,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/{library_id}", response_model=ResponseModel[LibraryResponse])
async def get_library(
    library_id: int,
    library_oper: LibraryOper = Depends(get_library_oper),
):
    """获取音乐库详情"""
    library = await library_oper.get_by_id(library_id)
    if not library:
        raise HTTPException(status_code=404, detail="音乐库不存在")

    return ResponseModel(data=LibraryResponse.model_validate(library))


@router.post("/", response_model=ResponseModel[LibraryResponse])
async def create_library(
    library: LibraryCreate,
    library_oper: LibraryOper = Depends(get_library_oper),
):
    """创建音乐库"""
    # 检查路径是否存在
    path = Path(library.path)
    if not path.exists():
        raise HTTPException(status_code=400, detail="路径不存在")

    created_library = await library_oper.create(**library.model_dump())
    return ResponseModel(
        message="音乐库创建成功",
        data=LibraryResponse.model_validate(created_library),
    )


@router.put("/{library_id}", response_model=ResponseModel[LibraryResponse])
async def update_library(
    library_id: int,
    library: LibraryUpdate,
    library_oper: LibraryOper = Depends(get_library_oper),
):
    """更新音乐库"""
    updated_library = await library_oper.update(
        library_id, **{k: v for k, v in library.model_dump().items() if v is not None}
    )
    if not updated_library:
        raise HTTPException(status_code=404, detail="音乐库不存在")

    return ResponseModel(
        message="音乐库更新成功",
        data=LibraryResponse.model_validate(updated_library),
    )


@router.delete("/{library_id}", response_model=ResponseModel[dict])
async def delete_library(
    library_id: int,
    library_oper: LibraryOper = Depends(get_library_oper),
):
    """删除音乐库"""
    success = await library_oper.delete(library_id)
    if not success:
        raise HTTPException(status_code=404, detail="音乐库不存在")

    return ResponseModel(message="音乐库删除成功", data={"id": library_id})


@router.post("/{library_id}/scan", response_model=ResponseModel[dict])
async def scan_library(
    library_id: int,
    request: ScanLibraryRequest,
    background_tasks: BackgroundTasks,
    library_oper: LibraryOper = Depends(get_library_oper),
):
    """
    扫描音乐库

    - **library_id**: 音乐库 ID
    - **recursive**: 是否递归扫描（默认使用配置值）
    """
    library = await library_oper.get_by_id(library_id)
    if not library:
        raise HTTPException(status_code=404, detail="音乐库不存在")

    # 确定是否递归扫描
    recursive = request.recursive if request.recursive is not None else library.scan_recursive

    # 创建任务 ID
    import time

    task_id = f"scan_{library_id}_{int(time.time())}"

    # 初始化任务状态
    scan_tasks[task_id] = {
        "library_id": library_id,
        "status": "pending",
        "total": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "started_at": None,
        "completed_at": None,
    }

    # 后台任务
    async def run_scan():
        scan_tasks[task_id]["started_at"] = time.time()
        scan_tasks[task_id]["status"] = "preparing"

        # 扫描目录
        music_files = await recursive_scan(Path(library.path), recursive)

        if not music_files:
            scan_tasks[task_id]["status"] = "completed"
            scan_tasks[task_id]["completed_at"] = time.time()
            return

        # 获取 MetadataChain
        metadata_chain = await get_metadata_chain()

        # 批量处理
        await process_file_batch(music_files, metadata_chain, task_id)

        scan_tasks[task_id]["completed_at"] = time.time()

        # 更新音乐库统计
        track_oper = TrackOper()
        tracks = await track_oper.get_by_library(library.path)

        await library_oper.update_stats(
            library_id,
            track_count=len(tracks),
            album_count=len(set(t.album_id for t in tracks if t.album_id)),
            artist_count=len(set(t.artist_id for t in tracks if t.artist_id)),
            total_size=sum(t.file_size for t in tracks if t.file_size or 0),
        )

        # 更新扫描时间
        await library_oper.update_scan_time(library_id)

        logger.info(f"音乐库扫描完成: {library.name} (ID: {library_id})")

    background_tasks.add_task(run_scan)

    return ResponseModel(
        message="音乐库扫描任务已创建",
        data={
            "task_id": task_id,
            "library_id": library_id,
            "status": "pending",
        },
    )


@router.get("/{library_id}/scan/status", response_model=ResponseModel[dict])
async def get_scan_status(library_id: int):
    """
    获取扫描进度

    Args:
        library_id: 音乐库 ID

    Returns:
        扫描任务状态
    """
    # 查找该音乐库的最新任务
    latest_task = None
    for task_id, task_data in scan_tasks.items():
        if task_data.get("library_id") == library_id:
            if latest_task is None or task_data.get("started_at", 0) > latest_task.get(
                "started_at", 0
            ):
                latest_task = task_data

    if not latest_task:
        return ResponseModel(
            data={
                "library_id": library_id,
                "status": "no_task",
            }
        )

    return ResponseModel(
        data={
            "library_id": library_id,
            "task_id": latest_task.get("task_id") if "task_id" in latest_task else None,
            "status": latest_task.get("status"),
            "total": latest_task.get("total", 0),
            "processed": latest_task.get("processed", 0),
            "success": latest_task.get("success", 0),
            "failed": latest_task.get("failed", 0),
            "started_at": latest_task.get("started_at"),
            "completed_at": latest_task.get("completed_at"),
        }
    )
