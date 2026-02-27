"""
Download Schema
下载相关的数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.types import DownloaderType, DownloadStatus


class DownloadBase(BaseModel):
    """Download 基础模型"""

    artist: str | None = None
    album: str | None = None
    title: str | None = None
    url: str | None = None
    quality: str | None = Field(None, description="音质：128k, 320k, lossless, flac")


class DownloadRequest(DownloadBase):
    """下载请求模型"""

    pass


class DownloadHistoryBase(BaseModel):
    """DownloadHistory 基础模型"""

    source: DownloaderType = Field(..., description="下载来源")
    source_id: str | None = None
    artist: str | None = None
    album: str | None = None
    title: str | None = None
    url: str | None = None
    quality: str | None = None


class DownloadHistoryResponse(DownloadHistoryBase):
    """下载历史响应模型"""

    id: int
    status: DownloadStatus
    error_message: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    file_format: str | None = None
    completed_at: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DownloadHistoryListResponse(BaseModel):
    """下载历史列表响应模型"""

    id: int
    source: str
    artist: str | None
    album: str | None
    title: str | None
    status: str
    quality: str | None
    file_path: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DownloadProgress(BaseModel):
    """下载进度响应模型"""

    id: int
    status: DownloadStatus
    progress: float = Field(..., description="进度 0.0-1.0")
    speed: float | None = Field(None, description="下载速度（字节/秒）")
    downloaded_size: int = Field(..., description="已下载大小（字节）")
    total_size: int | None = Field(None, description="总大小（字节）")
    error_message: str | None = None


class RetryDownloadRequest(BaseModel):
    """重试下载请求模型"""

    pass
