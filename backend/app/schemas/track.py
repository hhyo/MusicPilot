"""
Track Schema
曲目相关的数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    """Track 基础模型"""
    musicbrainz_id: Optional[str] = None
    album_id: Optional[int] = None
    artist_id: Optional[int] = None
    featured_artist_ids: Optional[List[int]] = None
    disc_number: Optional[int] = Field(1, description="碟片号")
    track_number: Optional[int] = Field(None, description="曲目号")
    title: str = Field(..., description="曲目标题")
    title_pinyin: Optional[str] = None
    duration: Optional[int] = Field(None, description="时长（秒）")
    position: Optional[int] = None
    path: Optional[str] = None
    file_format: Optional[str] = Field(None, description="文件格式：mp3, flac, etc.")
    bitrate: Optional[int] = Field(None, description="比特率（kbps）")
    sample_rate: Optional[int] = Field(None, description="采样率（Hz）")
    channels: Optional[int] = Field(None, description="声道数：1=mono, 2=stereo")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    lyrics: Optional[str] = None
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    comment: Optional[str] = None


class TrackCreate(TrackBase):
    """创建曲目请求模型"""
    pass


class TrackUpdate(BaseModel):
    """更新曲目请求模型"""
    album_id: Optional[int] = None
    artist_id: Optional[int] = None
    featured_artist_ids: Optional[List[int]] = None
    disc_number: Optional[int] = None
    track_number: Optional[int] = None
    title: Optional[str] = None
    title_pinyin: Optional[str] = None
    duration: Optional[int] = None
    position: Optional[int] = None
    path: Optional[str] = None
    file_format: Optional[str] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_size: Optional[int] = None
    lyrics: Optional[str] = None
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    comment: Optional[str] = None


class TrackResponse(TrackBase):
    """曲目响应模型"""
    id: int
    play_count: Optional[int] = None
    last_played: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackListResponse(BaseModel):
    """曲目列表响应模型"""
    id: int
    musicbrainz_id: Optional[str]
    album_id: Optional[int]
    artist_id: Optional[int]
    disc_number: Optional[int]
    track_number: Optional[int]
    title: str
    duration: Optional[int]
    path: Optional[str]
    file_format: Optional[str]
    play_count: Optional[int]

    class Config:
        from_attributes = True


class TrackStreamInfo(BaseModel):
    """曲目流媒体信息"""
    id: int
    title: str
    duration: int
    file_format: str
    file_size: int
    stream_url: Optional[str] = None