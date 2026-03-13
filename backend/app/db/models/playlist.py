"""
Playlist 数据库模型
"""

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.context import PlaylistType
from app.db import Base, TimestampMixin


class Playlist(Base, TimestampMixin):
    """播放列表模型"""

    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 类型
    type: Mapped[str] = mapped_column(String(20), nullable=False, default=PlaylistType.NORMAL.value)

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # 智能播放列表配置
    smart_query: Mapped[dict] = mapped_column(JSON, nullable=True)  # 智能查询条件

    # 排序配置
    order: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    # 是否公开
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 关联曲目（反向关系）
    tracks: Mapped[list] = relationship(
        "PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Playlist(id={self.id}, name='{self.name}', type='{self.type}')>"


class PlaylistTrack(Base, TimestampMixin):
    """播放列表曲目关联模型"""

    __tablename__ = "playlist_tracks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联
    playlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("playlists.id"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tracks.id"), nullable=False, index=True
    )

    # 排序
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # 添加时间
    added_at: Mapped[str] = mapped_column(String(50), nullable=True)

    # 关联（反向关系）
    playlist: Mapped[Playlist] = relationship("Playlist", back_populates="tracks")

    def __repr__(self):
        return f"<PlaylistTrack(playlist_id={self.playlist_id}, track_id={self.track_id}, position={self.position})>"
