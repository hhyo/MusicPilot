"""
Artist Schema
艺术家相关的数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ArtistBase(BaseModel):
    """Artist 基础模型"""
    musicbrainz_id: Optional[str] = None
    name: str = Field(..., description="艺术家名称")
    name_pinyin: Optional[str] = None
    sort_name: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = Field(None, description="类型：Person, Group, etc.")
    gender: Optional[str] = None
    birth_date: Optional[str] = Field(None, description="出生日期 YYYY-MM-DD")
    founded_date: Optional[str] = Field(None, description="成立日期 YYYY-MM-DD")
    image_url: Optional[str] = None
    biography: Optional[str] = None
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    rating_count: Optional[int] = None


class ArtistCreate(ArtistBase):
    """创建艺术家请求模型"""
    pass


class ArtistUpdate(BaseModel):
    """更新艺术家请求模型"""
    name: Optional[str] = None
    name_pinyin: Optional[str] = None
    sort_name: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    founded_date: Optional[str] = None
    image_url: Optional[str] = None
    biography: Optional[str] = None
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    rating_count: Optional[int] = None


class ArtistResponse(ArtistBase):
    """艺术家响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtistListResponse(BaseModel):
    """艺术家列表响应模型"""
    id: int
    musicbrainz_id: Optional[str]
    name: str
    image_url: Optional[str]
    genres: Optional[List[str]]
    rating: Optional[float]

    class Config:
        from_attributes = True