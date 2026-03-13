"""
DownloadHistory 数据库模型
"""

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.context import DownloadStatus
from app.db import Base, TimestampMixin


class DownloadHistory(Base, TimestampMixin):
    """下载历史模型"""

    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 来源信息
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # 下载器类型
    source_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 来源 ID

    # 音乐信息
    artist: Mapped[str] = mapped_column(String(255), nullable=True)
    album: Mapped[str] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)

    # 下载信息
    url: Mapped[str] = mapped_column(String(1000), nullable=True)
    quality: Mapped[str] = mapped_column(String(50), nullable=True)  # 128k, 320k, lossless, etc.
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DownloadStatus.PENDING.value
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # 文件信息
    file_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[BigInteger] = mapped_column(BigInteger, nullable=True)  # 字节
    file_format: Mapped[str] = mapped_column(String(10), nullable=True)

    # 完成时间
    completed_at: Mapped[str] = mapped_column(String(50), nullable=True)

    def __repr__(self):
        return f"<DownloadHistory(id={self.id}, title='{self.title}', status='{self.status}')>"
