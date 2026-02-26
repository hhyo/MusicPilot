"""
Playlist Schema
播放列表相关的数据模型
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.types import PlaylistType


class PlaylistBase(BaseModel):
    """Playlist 基础模型"""
    type: PlaylistType = Field(default=PlaylistType.NORMAL, description="播放列表类型")
    name: str = Field(..., description="播放列表名称")
    description: Optional[str] = None
    cover_url: Optional[str] = None
    smart_query: Optional[dict[str, Any]] = Field(None, description="智能播放列表查询条件")
    order: Optional[int] = Field(0, description="排序")
    is_public: bool = Field(default=False, description="是否公开")


class PlaylistCreate(PlaylistBase):
    """创建播放列表请求模型"""
    pass


class PlaylistUpdate(BaseModel):
    """更新播放列表请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    smart_query: Optional[dict[str, Any]] = None
    order: Optional[int] = None
    is_public: Optional[bool] = None


class PlaylistResponse(PlaylistBase):
    """播放列表响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistTrackBase(BaseModel):
    """PlaylistTrack 基础模型"""
    playlist_id: int
    track_id: int
    position: int = Field(..., description="位置")
    added_at: Optional[str] = None


class PlaylistTrackResponse(PlaylistTrackBase):
    """播放列表曲目关联响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistWithTracksResponse(PlaylistResponse):
    """带曲目的播放列表响应模型"""
    tracks: List[PlaylistTrackResponse] = []


class PlaylistListResponse(BaseModel):
    """播放列表列表响应模型"""
    id: int
    type: str
    name: str
    cover_url: Optional[str]
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AddTrackRequest(BaseModel):
    """添加曲目到播放列表请求模型"""
    track_id: int
    position: Optional[int] = Field(None, description="位置，None 表示添加到最后")


class BatchAddTracksRequest(BaseModel):
    """批量添加曲目到播放列表请求模型"""
    track_ids: List[int] = Field(..., description="曲目 ID 列表")


class ReorderTracksRequest(BaseModel):
    """重新排序曲目请求模型"""
    track_ids: List[int] = Field(..., description="曲目 ID 列表（按新顺序排列）")