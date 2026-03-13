"""
Track Schema
曲目相关的数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    """Track 基础模型"""

    musicbrainz_id: str | None = None
    album_id: int | None = None
    artist_id: int | None = None
    featured_artist_ids: list[int] | None = None
    disc_number: int | None = Field(1, description="碟片号")
    track_number: int | None = Field(None, description="曲目号")
    title: str = Field(..., description="曲目标题")
    title_pinyin: str | None = None
    duration: int | None = Field(None, description="时长（秒）")
    position: int | None = None
    path: str | None = None
    file_format: str | None = Field(None, description="文件格式：mp3, flac, etc.")
    bitrate: int | None = Field(None, description="比特率（kbps）")
    sample_rate: int | None = Field(None, description="采样率（Hz）")
    channels: int | None = Field(None, description="声道数：1=mono, 2=stereo")
    file_size: int | None = Field(None, description="文件大小（字节）")
    lyrics: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    comment: str | None = None


class TrackCreate(TrackBase):
    """创建曲目请求模型"""

    pass


class TrackUpdate(BaseModel):
    """更新曲目请求模型"""

    album_id: int | None = None
    artist_id: int | None = None
    featured_artist_ids: list[int] | None = None
    disc_number: int | None = None
    track_number: int | None = None
    title: str | None = None
    title_pinyin: str | None = None
    duration: int | None = None
    position: int | None = None
    path: str | None = None
    file_format: str | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    file_size: int | None = None
    lyrics: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    comment: str | None = None


class TrackResponse(TrackBase):
    """曲目响应模型"""

    id: int
    play_count: int | None = None
    last_played: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackListResponse(BaseModel):
    """曲目列表响应模型"""

    id: int
    musicbrainz_id: str | None
    album_id: int | None
    artist_id: int | None
    disc_number: int | None
    track_number: int | None
    title: str
    duration: int | None
    path: str | None
    file_format: str | None
    play_count: int | None

    class Config:
        from_attributes = True


class TrackStreamInfo(BaseModel):
    """曲目流媒体信息"""

    id: int
    title: str
    duration: int
    file_format: str
    file_size: int
    stream_url: str | None = None
