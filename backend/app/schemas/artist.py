"""
Artist Schema
艺术家相关的数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ArtistBase(BaseModel):
    """Artist 基础模型"""

    musicbrainz_id: str | None = None
    name: str = Field(..., description="艺术家名称")
    name_pinyin: str | None = None
    sort_name: str | None = None
    country: str | None = None
    type: str | None = Field(None, description="类型：Person, Group, etc.")
    gender: str | None = None
    birth_date: str | None = Field(None, description="出生日期 YYYY-MM-DD")
    founded_date: str | None = Field(None, description="成立日期 YYYY-MM-DD")
    image_url: str | None = None
    biography: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    rating: float | None = Field(None, ge=0, le=5)
    rating_count: int | None = None


class ArtistCreate(ArtistBase):
    """创建艺术家请求模型"""

    pass


class ArtistUpdate(BaseModel):
    """更新艺术家请求模型"""

    name: str | None = None
    name_pinyin: str | None = None
    sort_name: str | None = None
    country: str | None = None
    type: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    founded_date: str | None = None
    image_url: str | None = None
    biography: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    rating: float | None = Field(None, ge=0, le=5)
    rating_count: int | None = None


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
    musicbrainz_id: str | None
    name: str
    image_url: str | None
    genres: list[str] | None
    rating: float | None

    class Config:
        from_attributes = True
