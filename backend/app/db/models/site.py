"""
Site 资源站点数据库模型
"""
from sqlalchemy import String, Text, Integer, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, TimestampMixin


class Site(Base, TimestampMixin):
    """资源站点模型"""
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    # 认证信息
    cookie: Mapped[str] = mapped_column(Text, nullable=True)
    passkey: Mapped[str] = mapped_column(String(100), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(100), nullable=True)

    # 连接配置
    proxy: Mapped[str] = mapped_column(String(500), nullable=True)
    ua: Mapped[str] = mapped_column(String(500), nullable=True)
    timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # RSS 配置
    rss: Mapped[str] = mapped_column(String(500), nullable=True)
    rss_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # 下载器配置
    downloader: Mapped[str] = mapped_column(String(50), nullable=False, default="qbittorrent")

    # 优先级
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 站点类型：resource（资源站点）, other（其他）
    site_type: Mapped[str] = mapped_column(String(50), nullable=False, default="resource")

    def __repr__(self):
        return f"<Site(id={self.id}, name='{self.name}', url='{self.url}', enabled={self.enabled})>"