"""
Media Schema
媒体服务器相关的数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.types import MediaServerType


class MediaServerBase(BaseModel):
    """MediaServer 基础模型"""

    type: MediaServerType = Field(..., description="媒体服务器类型")
    name: str = Field(..., description="服务器名称")
    host: str = Field(..., description="服务器地址")
    port: int | None = Field(None, description="服务器端口")
    token: str | None = Field(None, description="访问令牌")
    library_id: str | None = Field(None, description="媒体库 ID")
    library_name: str | None = Field(None, description="媒体库名称")


class MediaServerCreate(MediaServerBase):
    """创建媒体服务器请求模型"""

    pass


class MediaServerUpdate(BaseModel):
    """更新媒体服务器请求模型"""

    name: str | None = None
    host: str | None = None
    port: int | None = None
    token: str | None = None
    library_id: str | None = None
    library_name: str | None = None
    enabled: bool | None = None


class MediaServerResponse(MediaServerBase):
    """媒体服务器响应模型"""

    id: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaServerListResponse(BaseModel):
    """媒体服务器列表响应模型"""

    id: int
    type: str
    name: str
    host: str
    port: int | None
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MediaServerStatus(BaseModel):
    """媒体服务器状态"""

    connected: bool = Field(..., description="是否已连接")
    library_synced: bool = Field(..., description="媒体库是否已同步")
    track_count: int | None = Field(None, description="曲目数量")
    last_sync: str | None = Field(None, description="最后同步时间")


class ScanMediaServerRequest(BaseModel):
    """扫描媒体服务器请求模型"""

    sync_metadata: bool = Field(default=True, description="是否同步元数据")
    sync_playback: bool = Field(default=True, description="是否同步播放状态")
