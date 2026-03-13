"""
Download API 端点 - 下载管理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/download", tags=["下载管理"])


class DownloadTask(BaseModel):
    id: int
    torrent_url: str
    status: str


class DownloadClient(BaseModel):
    type: str
    name: str


@router.get("/tasks", summary="获取下载任务列表")
async def get_download_tasks():
    """获取下载任务列表"""
    return {"tasks": []}


@router.post("/tasks", summary="添加下载任务")
async def add_download_task(torrent_url: str, save_path: str):
    """添加新的下载任务"""
    return {
        "task": {
            "id": 1,
            "torrent_url": torrent_url,
            "status": "pending",
            "save_path": save_path,
        }
    }


@router.delete("/tasks/{task_id}", summary="删除下载任务")
async def delete_download_task(task_id: int):
    """删除指定的下载任务"""
    return {"message": "任务已删除", "task_id": task_id}


@router.get("/clients", response_model=list[DownloadClient], summary="获取下载器列表")
async def get_download_clients():
    """获取支持的下载器列表"""
    clients = [
        DownloadClient(type="transmission", name="Transmission"),
        DownloadClient(type="qbittorrent", name="qBittorrent"),
    ]
    return clients