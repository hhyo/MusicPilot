"""
Subscribe Schema
订阅相关的数据模型
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SubscribeBase(BaseModel):
    """Subscribe 基础模型"""

    type: str = Field(..., description="订阅类型：artist, album, playlist, chart")
    source_type: str = Field(
        default="musicbrainz", description="来源类型：musicbrainz, netease, qq"
    )
    musicbrainz_id: Optional[str] = None
    playlist_id: Optional[str] = None
    name: str = Field(..., description="订阅名称")
    description: Optional[str] = None
    auto_download: bool = Field(default=True, description="是否自动下载")
    download_format: Optional[str] = Field(None, description="下载格式：mp3, flac")
    rules: Optional[Dict[str, Any]] = Field(None, description="订阅规则（JSON）")


class SubscribeCreate(SubscribeBase):
    """创建订阅请求模型"""

    pass


class SubscribeUpdate(BaseModel):
    """更新订阅请求模型"""

    name: Optional[str] = None
    description: Optional[str] = None
    auto_download: Optional[bool] = None
    download_format: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    state: Optional[str] = Field(None, description="状态：active, paused")


class SubscribeResponse(SubscribeBase):
    """订阅响应模型"""

    id: int
    last_check: Optional[str] = None
    last_release: Optional[str] = None
    release_count: Optional[int] = None
    state: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscribeListResponse(BaseModel):
    """订阅列表响应模型"""

    id: int
    type: str
    source_type: str
    name: str
    auto_download: bool
    last_check: Optional[str]
    last_release: Optional[str]
    release_count: Optional[int]
    state: str

    class Config:
        from_attributes = True


class CheckSubscribeResponse(BaseModel):
    """检查订阅响应模型"""

    has_new_releases: bool = Field(..., description="是否有新发布")
    new_releases_count: int = Field(default=0, description="新发布数量")
    last_check: str
