"""
Album Schema
专辑相关的数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AlbumBase(BaseModel):
    """Album 基础模型"""

    musicbrainz_id: str | None = None
    artist_id: int | None = None
    title: str = Field(..., description="专辑标题")
    title_pinyin: str | None = None
    disambiguation: str | None = None
    release_date: str | None = Field(None, description="发行日期 YYYY-MM-DD")
    release_type: str | None = Field(None, description="发行类型：Album, EP, Single, etc.")
    label: str | None = None
    catalog_number: str | None = None
    country: str | None = None
    cover_url: str | None = None
    cover_id: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    comment: str | None = None
    rating: float | None = Field(None, ge=0, le=5)
    rating_count: int | None = None
    track_count: int | None = None
    total_duration: int | None = Field(None, description="总时长（秒）")


class AlbumCreate(AlbumBase):
    """创建专辑请求模型"""

    pass


class AlbumUpdate(BaseModel):
    """更新专辑请求模型"""

    title: str | None = None
    title_pinyin: str | None = None
    disambiguation: str | None = None
    release_date: str | None = None
    release_type: str | None = None
    label: str | None = None
    catalog_number: str | None = None
    country: str | None = None
    cover_url: str | None = None
    cover_id: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    comment: str | None = None
    rating: float | None = Field(None, ge=0, le=5)
    rating_count: int | None = None
    track_count: int | None = None
    total_duration: int | None = None


class AlbumResponse(AlbumBase):
    """专辑响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlbumListResponse(BaseModel):
    """专辑列表响应模型"""

    id: int
    musicbrainz_id: str | None
    artist_id: int | None
    title: str
    release_date: str | None
    release_type: str | None
    cover_url: str | None
    genres: list[str] | None
    rating: float | None
    track_count: int | None
    total_duration: int | None

    class Config:
        from_attributes = True
