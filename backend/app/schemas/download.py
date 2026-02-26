"""
Download Schema
下载相关的数据模型
"""
from datetime import datetime


from pydantic import BaseModel, Field

from app.schemas.types import DownloadStatus, DownloaderType


class DownloadBase(BaseModel):
    """Download 基础模型"""
    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    quality: Optional[str] = Field(None, description="音质：128k, 320k, lossless, flac")


class DownloadRequest(DownloadBase):
    """下载请求模型"""
    pass


class DownloadHistoryBase(BaseModel):
    """DownloadHistory 基础模型"""
    source: DownloaderType = Field(..., description="下载来源")
    source_id: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    quality: Optional[str] = None


class DownloadHistoryResponse(DownloadHistoryBase):
    """下载历史响应模型"""
    id: int
    status: DownloadStatus
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DownloadHistoryListResponse(BaseModel):
    """下载历史列表响应模型"""
    id: int
    source: str
    artist: Optional[str]
    album: Optional[str]
    title: Optional[str]
    status: str
    quality: Optional[str]
    file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DownloadProgress(BaseModel):
    """下载进度响应模型"""
    id: int
    status: DownloadStatus
    progress: float = Field(..., description="进度 0.0-1.0")
    speed: Optional[float] = Field(None, description="下载速度（字节/秒）")
    downloaded_size: int = Field(..., description="已下载大小（字节）")
    total_size: Optional[int] = Field(None, description="总大小（字节）")
    error_message: Optional[str] = None


class RetryDownloadRequest(BaseModel):
    """重试下载请求模型"""
    pass
