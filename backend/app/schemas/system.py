"""
System Schema
系统配置相关的数据模型
"""
from datetime import datetime

from pydantic import BaseModel, Field


class SystemConfigBase(BaseModel):
    """SystemConfig 基础模型"""
    key: str = Field(..., description="配置键")
    value: Optional[str] = Field(None, description="配置值")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置请求模型"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置请求模型"""
    value: Optional[str] = None


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    """系统统计信息"""
    total_artists: int = Field(..., description="艺术家总数")
    total_albums: int = Field(..., description="专辑总数")
    total_tracks: int = Field(..., description="曲目总数")
    total_playlists: int = Field(..., description="播放列表总数")
    total_libraries: int = Field(..., description="音乐库总数")
    total_downloads: int = Field(..., description="下载总数")
    total_subscribes: int = Field(..., description="订阅总数")
    total_play_count: int = Field(..., description="总播放次数")
    total_storage: int = Field(..., description="总存储大小（字节）")


class SystemHealth(BaseModel):
    """系统健康状态"""
    status: str = Field(..., description="状态：healthy, degraded, unhealthy")
    database: str = Field(..., description="数据库状态")
    cache: str = Field(..., description="缓存状态")
    version: str = Field(..., description="系统版本")
    uptime: str = Field(..., description="运行时间")


class ScanAllRequest(BaseModel):
    """扫描所有音乐库请求模型"""
    force: bool = Field(default=False, description="是否强制扫描")


class LogEntry(BaseModel):
    """日志条目"""
    timestamp: str = Field(..., description="时间戳")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")


class LogsResponse(BaseModel):
    """日志响应"""
    logs: list[LogEntry] = Field(default_factory=list)
    total: int = Field(..., description="日志条数")