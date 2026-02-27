"""
Subscribe Schema
订阅相关的数据模型
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SubscribeBase(BaseModel):
    """Subscribe 基础模型"""

    type: str = Field(..., description="订阅类型：artist, album, playlist, chart")
    source_type: str = Field(
        default="musicbrainz", description="来源类型：musicbrainz, netease, qq"
    )
    musicbrainz_id: str | None = None
    playlist_id: str | None = None
    name: str = Field(..., description="订阅名称")
    description: str | None = None
    auto_download: bool = Field(default=True, description="是否自动下载")
    download_format: str | None = Field(None, description="下载格式：mp3, flac")
    rules: dict[str, Any] | None = Field(None, description="订阅规则（JSON）")


class SubscribeCreate(SubscribeBase):
    """创建订阅请求模型"""

    pass


class SubscribeUpdate(BaseModel):
    """更新订阅请求模型"""

    name: str | None = None
    description: str | None = None
    auto_download: bool | None = None
    download_format: str | None = None
    rules: dict[str, Any] | None = None
    state: str | None = Field(None, description="状态：active, paused")


class SubscribeResponse(SubscribeBase):
    """订阅响应模型"""

    id: int
    last_check: str | None = None
    last_release: str | None = None
    release_count: int | None = None
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
    last_check: str | None
    last_release: str | None
    release_count: int | None
    state: str

    class Config:
        from_attributes = True


class CheckSubscribeResponse(BaseModel):
    """检查订阅响应模型"""

    has_new_releases: bool = Field(..., description="是否有新发布")
    new_releases_count: int = Field(default=0, description="新发布数量")
    last_check: str
