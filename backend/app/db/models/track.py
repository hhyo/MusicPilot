"""
Track 数据库模型
"""

from sqlalchemy import String, Text, Integer, Float, JSON, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, TimestampMixin


class Track(Base, TimestampMixin):
    """曲目模型"""

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # MusicBrainz ID
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # 关联
    album_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("albums.id"), nullable=True, index=True
    )
    artist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("artists.id"), nullable=True, index=True
    )
    featured_artist_ids: Mapped[list] = mapped_column(JSON, nullable=True)  # 特邀艺术家 ID 列表

    # 碟片和曲目号
    disc_number: Mapped[int] = mapped_column(Integer, nullable=True, default=1)
    track_number: Mapped[int] = mapped_column(Integer, nullable=True)

    # 基本信息
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title_pinyin: Mapped[str] = mapped_column(String(255), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)  # 秒
    position: Mapped[int] = mapped_column(Integer, nullable=True)  # 专辑中的位置

    # 文件信息
    path: Mapped[str] = mapped_column(String(1000), nullable=True, index=True)
    file_format: Mapped[str] = mapped_column(String(10), nullable=True)  # mp3, flac, etc.
    file_hash: Mapped[str] = mapped_column(String(32), nullable=True, index=True)  # MD5 哈希
    bitrate: Mapped[int] = mapped_column(Integer, nullable=True)  # kbps
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=True)  # Hz
    channels: Mapped[int] = mapped_column(Integer, nullable=True)  # 1=mono, 2=stereo
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=True)  # 字节

    # 歌词
    lyrics: Mapped[str] = mapped_column(Text, nullable=True)

    # 标签和评论
    genres: Mapped[list] = mapped_column(JSON, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    # 播放统计
    play_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    last_played: Mapped[str] = mapped_column(String(50), nullable=True)

    def __repr__(self):
        return f"<Track(id={self.id}, title='{self.title}')>"
