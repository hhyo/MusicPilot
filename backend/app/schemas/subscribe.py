"""
Subscribe Schema
订阅相关的数据模型
"""
from typing import Optional, List
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
    total: int = Field(..., description="总数")
    subscribes: List[SubscribeResponse] = Field(default_factory=list)


class SubscribeRelease(BaseModel):
    """订阅发布信息"""
    id: Optional[int] = None
    musicbrainz_id: Optional[str] = None
    title: str = Field(..., description="发布标题")
    release_date: Optional[str] = Field(None, description="发布日期")
    release_type: Optional[str] = Field(None, description="发布类型：album, ep, single")
    downloaded: bool = Field(default=False, description="是否已下载")
    download_status: Optional[str] = Field(None, description="下载状态")
    file_path: Optional[str] = Field(None, description="文件路径")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class CheckSubscribeResponse(BaseModel):
    """检查订阅响应模型"""
    subscribe_id: int = Field(..., description="订阅 ID")
    new_releases: int = Field(..., description="新发布数量")
    message: str = Field(..., description="消息")