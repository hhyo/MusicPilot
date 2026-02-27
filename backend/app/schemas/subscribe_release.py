"""
SubscribeRelease Schema
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SubscribeReleaseBase(BaseModel):
    """订阅发布记录基础模型"""

    subscribe_id: int = Field(..., description="订阅ID")
    release_type: str = Field(..., description="发布类型")
    artist: str | None = Field(None, description="艺术家")
    album: str | None = Field(None, description="专辑")
    title: str | None = Field(None, description="标题")
    musicbrainz_id: str | None = Field(None, description="MusicBrainz ID")
    release_date: datetime | None = Field(None, description="发布时间")
    download_status: str = Field("pending", description="下载状态")
    torrent_id: str | None = Field(None, description="种子ID")
    torrent_site: str | None = Field(None, description="站点名称")
    torrent_size: int | None = Field(None, description="种子大小（字节）")
    downloader_task_id: str | None = Field(None, description="下载器任务ID")
    error_message: str | None = Field(None, description="错误信息")


class SubscribeReleaseCreate(SubscribeReleaseBase):
    """创建订阅发布记录"""

    pass


class SubscribeReleaseUpdate(BaseModel):
    """更新订阅发布记录"""

    download_status: str | None = None
    torrent_id: str | None = None
    torrent_site: str | None = None
    torrent_size: int | None = None
    downloader_task_id: str | None = None
    error_message: str | None = None


class SubscribeReleaseResponse(SubscribeReleaseBase):
    """订阅发布记录响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscribeReleaseListResponse(BaseModel):
    """订阅发布记录列表响应"""

    total: int
    items: list[SubscribeReleaseResponse]


class SubscribeReleaseStatistics(BaseModel):
    """订阅发布统计"""

    total: int = Field(..., description="总数量")
    pending: int = Field(..., description="待下载数量")
    downloading: int = Field(..., description="下载中数量")
    completed: int = Field(..., description="已完成数量")
    failed: int = Field(..., description="失败数量")
