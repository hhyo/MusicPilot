"""
Subscribe Schema
订阅相关的数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SubscribeBase(BaseModel):
    """Subscribe 基础模型"""
    type: str = Field(..., description="订阅类型：artist, album")
    musicbrainz_id: Optional[str] = None
    name: str = Field(..., description="订阅名称")
    description: Optional[str] = None
    auto_download: bool = Field(default=True, description="是否自动下载")
    download_format: Optional[str] = Field(None, description="下载格式：mp3, flac")


class SubscribeCreate(SubscribeBase):
    """创建订阅请求模型"""
    pass


class SubscribeUpdate(BaseModel):
    """更新订阅请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    auto_download: Optional[bool] = None
    download_format: Optional[str] = None
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
    name: str
    auto_download: bool
    last_check: Optional[str]
    last_release: Optional[str]
    release_count: Optional[int]
    state: str

    class Config:
        from_attributes = True


class SubscribeRelease(BaseModel):
    """订阅发布信息"""
    id: Optional[int] = None
    title: str
    release_date: Optional[str] = None
    release_type: Optional[str] = None
    cover_url: Optional[str] = None


class CheckSubscribeResponse(BaseModel):
    """检查订阅响应模型"""
    has_new_releases: bool = Field(..., description="是否有新发布")
    new_releases: list[SubscribeRelease] = Field(default_factory=list)
    last_check: str