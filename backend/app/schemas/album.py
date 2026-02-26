"""
Album Schema
专辑相关的数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AlbumBase(BaseModel):
    """Album 基础模型"""
    musicbrainz_id: Optional[str] = None
    artist_id: Optional[int] = None
    title: str = Field(..., description="专辑标题")
    title_pinyin: Optional[str] = None
    disambiguation: Optional[str] = None
    release_date: Optional[str] = Field(None, description="发行日期 YYYY-MM-DD")
    release_type: Optional[str] = Field(None, description="发行类型：Album, EP, Single, etc.")
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    country: Optional[str] = None
    cover_url: Optional[str] = None
    cover_id: Optional[str] = None
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    comment: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    rating_count: Optional[int] = None
    track_count: Optional[int] = None
    total_duration: Optional[int] = Field(None, description="总时长（秒）")


class AlbumCreate(AlbumBase):
    """创建专辑请求模型"""
    pass


class AlbumUpdate(BaseModel):
    """更新专辑请求模型"""
    title: Optional[str] = None
    title_pinyin: Optional[str] = None
    disambiguation: Optional[str] = None
    release_date: Optional[str] = None
    release_type: Optional[str] = None
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    country: Optional[str] = None
    cover_url: Optional[str] = None
    cover_id: Optional[str] = None
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    comment: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    rating_count: Optional[int] = None
    track_count: Optional[int] = None
    total_duration: Optional[int] = None


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
    musicbrainz_id: Optional[str]
    artist_id: Optional[int]
    title: str
    release_date: Optional[str]
    release_type: Optional[str]
    cover_url: Optional[str]
    genres: Optional[List[str]]
    rating: Optional[float]
    track_count: Optional[int]
    total_duration: Optional[int]

    class Config:
        from_attributes = True
