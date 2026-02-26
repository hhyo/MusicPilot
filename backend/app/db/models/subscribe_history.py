"""
SubscribeHistory 数据库模型
记录订阅发布历史
"""
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, TimestampMixin


class SubscribeHistory(Base, TimestampMixin):
    """订阅历史模型"""
    __tablename__ = "subscribe_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联订阅
    subscribe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscribes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 发布信息
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_date: Mapped[str] = mapped_column(String(50), nullable=True)
    release_type: Mapped[str] = mapped_column(String(50), nullable=True)  # album, ep, single, etc.

    # 下载信息
    downloaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    download_status: Mapped[str] = mapped_column(String(50), nullable=True)  # pending, downloading, completed, failed
    file_path: Mapped[str] = mapped_column(String(1000), nullable=True)

    # 额外信息
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # 存储额外的发布信息

    def __repr__(self):
        return (
            f"<SubscribeHistory(id={self.id}, subscribe_id={self.subscribe_id}, "
            f"title='{self.title}', downloaded={self.downloaded})>"
        )