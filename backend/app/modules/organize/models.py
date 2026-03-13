"""Organize Module 模型"""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from app.db import Base


class OrganizeStatus(enum.StrEnum):
    """整理状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OrganizeTask(Base):
    """整理任务模型"""

    __tablename__ = "organize_tasks"

    id = Column(Integer, primary_key=True, index=True)
    download_task_id = Column(Integer, nullable=False)
    source_path = Column(String(500), nullable=False)
    target_path = Column(String(500), nullable=False)
    metadata_json = Column(Text)  # JSON 格式的元数据
    status = Column(Enum(OrganizeStatus), default=OrganizeStatus.PENDING)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime)
