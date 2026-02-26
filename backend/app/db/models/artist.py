"""
Artist 数据库模型
"""
from sqlalchemy import String, Text, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, TimestampMixin


class Artist(Base, TimestampMixin):
    """艺术家模型"""
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # MusicBrainz ID
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_pinyin: Mapped[str] = mapped_column(String(255), nullable=True)
    sort_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # 地域信息
    country: Mapped[str] = mapped_column(String(100), nullable=True)

    # 类型信息
    type: Mapped[str] = mapped_column(String(50), nullable=True)  # Person, Group, etc.
    gender: Mapped[str] = mapped_column(String(50), nullable=True)

    # 日期信息
    birth_date: Mapped[str] = mapped_column(String(50), nullable=True)  # YYYY-MM-DD
    founded_date: Mapped[str] = mapped_column(String(50), nullable=True)  # YYYY-MM-DD

    # 图片和简介
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    biography: Mapped[str] = mapped_column(Text, nullable=True)

    # 标签和评分
    genres: Mapped[list] = mapped_column(JSON, nullable=True)  # ["Rock", "Pop", ...]
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return f"<Artist(id={self.id}, name='{self.name}')>"