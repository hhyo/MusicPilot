"""
SubscribeRelease 订阅发布记录数据库模型
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class SubscribeRelease(Base, TimestampMixin):
    """订阅发布记录模型"""

    __tablename__ = "subscribe_releases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联订阅
    subscribe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscribes.id"), nullable=False, index=True
    )

    # 发布类型：album, playlist_update
    release_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 音乐信息
    artist: Mapped[str] = mapped_column(String(255), nullable=True)
    album: Mapped[str] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)

    # MusicBrainz 信息
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # 发布时间
    release_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 下载状态：pending, downloading, completed, failed
    download_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # 种子信息
    torrent_id: Mapped[str] = mapped_column(String(100), nullable=True)
    torrent_site: Mapped[str] = mapped_column(String(100), nullable=True)
    torrent_size: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # 下载器任务ID
    downloader_task_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # 错误信息
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<SubscribeRelease(id={self.id}, subscribe_id={self.subscribe_id}, release_type='{self.release_type}', download_status='{self.download_status}')>"
