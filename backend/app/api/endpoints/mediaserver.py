"""
MediaServer API 端点 - 媒体服务器管理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/mediaserver", tags=["媒体服务器"])


class MediaServer(BaseModel):
    type: str
    name: str
    enabled: bool


class ServerResponse(BaseModel):
    server: MediaServer


@router.get("/servers", response_model=list[MediaServer], summary="获取媒体服务器列表")
async def get_mediaserver_servers():
    """获取配置的媒体服务器列表"""
    servers = [
        MediaServer(type="jellyfin", name="Jellyfin", enabled=True),
        MediaServer(type="plex", name="Plex", enabled=False),
    ]
    return servers


@router.post("/servers", summary="添加媒体服务器")
async def add_mediaserver_server(server_type: str, name: str, url: str, api_key: str):
    """添加新的媒体服务器"""
    return {
        "server": {
            "type": server_type,
            "name": name,
            "enabled": True,
            "url": url,
        }
    }


@router.post("/servers/{server_id}/refresh", summary="刷新媒体库")
async def refresh_mediaserver_library(server_id: str):
    """刷新指定媒体服务器的媒体库"""
    return {"message": "媒体库刷新已提交", "server_id": server_id}


@router.post("/notify-all", summary="通知所有媒体服务器")
async def notify_all_mediaservers():
    """通知所有媒体服务器刷新媒体库"""
    return {"message": "已通知所有媒体服务器"}