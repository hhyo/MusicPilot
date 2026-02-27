"""
MediaServer 数据库模型
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class MediaServer(Base, TimestampMixin):
    """媒体服务器模型"""

    __tablename__ = "media_servers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 类型
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # plex, jellyfin

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # 连接信息
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=True)
    token: Mapped[str] = mapped_column(String(255), nullable=True)

    # 媒体库信息
    library_id: Mapped[str] = mapped_column(String(100), nullable=True)
    library_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<MediaServer(id={self.id}, name='{self.name}', type='{self.type}')>"
