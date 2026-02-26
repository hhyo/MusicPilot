"""
Library Schema
音乐库相关的数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LibraryBase(BaseModel):
    """Library 基础模型"""
    name: str = Field(..., description="音乐库名称")
    path: str = Field(..., description="音乐库路径")
    scan_interval: Optional[int] = Field(86400, description="扫描间隔（秒），默认每天")
    auto_scan: bool = Field(default=True, description="是否自动扫描")
    scan_recursive: bool = Field(default=True, description="是否递归扫描")


class LibraryCreate(LibraryBase):
    """创建音乐库请求模型"""
    pass


class LibraryUpdate(BaseModel):
    """更新音乐库请求模型"""
    name: Optional[str] = None
    path: Optional[str] = None
    scan_interval: Optional[int] = None
    auto_scan: Optional[bool] = None
    scan_recursive: Optional[bool] = None


class LibraryResponse(LibraryBase):
    """音乐库响应模型"""
    id: int
    last_scan_time: Optional[str] = None
    track_count: Optional[int] = None
    album_count: Optional[int] = None
    artist_count: Optional[int] = None
    total_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LibraryListResponse(BaseModel):
    """音乐库列表响应模型"""
    id: int
    name: str
    path: str
    last_scan_time: Optional[str]
    auto_scan: bool
    track_count: Optional[int]
    album_count: Optional[int]
    artist_count: Optional[int]
    total_size: Optional[int]

    class Config:
        from_attributes = True


class ScanLibraryRequest(BaseModel):
    """扫描音乐库请求模型"""
    recursive: Optional[bool] = Field(None, description="是否递归扫描，None 表示使用配置值")