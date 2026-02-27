"""
Album 数据库模型
"""

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class Album(Base, TimestampMixin):
    """专辑模型"""

    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # MusicBrainz ID
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # 艺术家关联
    artist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("artists.id"), nullable=True, index=True
    )

    # 基本信息
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title_pinyin: Mapped[str] = mapped_column(String(255), nullable=True)
    disambiguation: Mapped[str] = mapped_column(String(255), nullable=True)

    # 发行信息
    release_date: Mapped[str] = mapped_column(String(50), nullable=True)  # YYYY-MM-DD
    release_type: Mapped[str] = mapped_column(String(50), nullable=True)  # Album, EP, Single, etc.
    label: Mapped[str] = mapped_column(String(255), nullable=True)
    catalog_number: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)

    # 封面图片
    cover_url: Mapped[str] = mapped_column(String(500), nullable=True)
    cover_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 本地封面 ID

    # 标签和评分
    genres: Mapped[list] = mapped_column(JSON, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=True)

    # 统计信息
    track_count: Mapped[int] = mapped_column(Integer, nullable=True)
    total_duration: Mapped[int] = mapped_column(Integer, nullable=True)  # 秒

    def __repr__(self):
        return f"<Album(id={self.id}, title='{self.title}')>"
