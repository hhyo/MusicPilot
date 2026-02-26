"""
Library 数据库模型
"""
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, TimestampMixin


class Library(Base, TimestampMixin):
    """音乐库模型"""
    __tablename__ = "libraries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)

    # 扫描配置
    scan_interval: Mapped[int] = mapped_column(Integer, nullable=True, default=86400)  # 默认每天扫描一次（秒）
    last_scan_time: Mapped[str] = mapped_column(String(50), nullable=True)
    auto_scan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scan_recursive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 统计信息
    track_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    album_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    artist_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    total_size: Mapped[BigInteger] = mapped_column(BigInteger, nullable=True)  # 字节

    def __repr__(self):
        return f"<Library(id={self.id}, name='{self.name}', path='{self.path}')>"
