"""
SystemConfig 数据库模型
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class SystemConfig(Base, TimestampMixin):
    """系统配置模型"""

    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 配置键
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # 配置值
    value: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"
