"""
Subscribe 数据库模型
"""
from sqlalchemy import String, Text, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, TimestampMixin


class Subscribe(Base, TimestampMixin):
    """订阅模型"""
    __tablename__ = "subscribes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 类型：artist, album
    type: Mapped[str] = mapped_column(String(20), nullable=False)

    # MusicBrainz ID
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 下载配置
    auto_download: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    download_format: Mapped[str] = mapped_column(String(50), nullable=True)  # mp3, flac, etc.

    # 检查和发布
    last_check: Mapped[str] = mapped_column(String(50), nullable=True)
    last_release: Mapped[str] = mapped_column(String(50), nullable=True)
    release_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    # 状态：active, paused
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    def __repr__(self):
        return f"<Subscribe(id={self.id}, name='{self.name}', type='{self.type}')>"