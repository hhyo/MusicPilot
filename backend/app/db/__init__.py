"""
数据库基础模块
提供数据库连接、会话管理和通用操作
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.core.config import settings
from app.core.log import logger


# Base 类用于所有数据库模型
class Base(DeclarativeBase):
    """所有数据库模型的基类"""

    pass


class TimestampMixin:
    """时间戳混入类"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class DatabaseManager:
    """
    数据库管理器
    管理数据库连接和会话
    """

    def __init__(self, database_url: str | None = None):
        """
        初始化数据库管理器

        Args:
            database_url: 数据库连接 URL
        """
        self.database_url = database_url or settings.database_url
        self._engine = None
        self._async_session_maker = None
        self.logger = logger

    def init_db(self):
        """初始化数据库"""
        self.logger.info(f"初始化数据库: {self.database_url}")

        # 创建异步引擎
        self._engine = create_async_engine(
            self.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # 创建会话工厂
        self._async_session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.logger.info("数据库初始化完成")

    async def create_tables(self):
        """创建所有表"""
        self.logger.info("创建数据库表")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("数据库表创建完成")

    async def drop_tables(self):
        """删除所有表"""
        self.logger.warning("删除数据库表")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        self.logger.info("数据库表删除完成")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话

        Yields:
            数据库会话
        """
        if not self._async_session_maker:
            raise RuntimeError("数据库未初始化，请先调用 init_db()")

        async with self._async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.logger.error(f"数据库操作失败: {e}")
                raise
            finally:
                await session.close()

    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self.logger.info("数据库连接已关闭")

    @property
    def engine(self):
        """获取数据库引擎"""
        if not self._engine:
            raise RuntimeError("数据库未初始化，请先调用 init_db()")
        return self._engine


# 泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)


class OperBase[ModelType: Base]:
    """
    数据库操作基类
    提供通用的 CRUD 操作
    """

    def __init__(self, model: type[ModelType], db_manager: DatabaseManager):
        """
        初始化操作基类

        Args:
            model: 数据库模型类
            db_manager: 数据库管理器
        """
        self.model = model
        self.db_manager = db_manager
        self.logger = logger

    async def get_by_id(self, id: int) -> ModelType | None:
        """
        根据 ID 获取记录

        Args:
            id: 记录 ID

        Returns:
            记录对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> list[ModelType]:
        """
        获取所有记录

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            **filters: 过滤条件

        Returns:
            记录列表
        """
        async with self.db_manager.get_session() as session:
            query = select(self.model)

            # 应用过滤条件
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

            # 应用分页
            query = query.offset(skip).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        """
        创建新记录

        Args:
            **kwargs: 模型字段值

        Returns:
            创建的记录对象
        """
        async with self.db_manager.get_session() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            self.logger.debug(f"创建记录: {self.model.__name__} ID={obj.id}")
            return obj

    async def update(self, id: int, **kwargs) -> ModelType | None:
        """
        更新记录

        Args:
            id: 记录 ID
            **kwargs: 更新的字段值

        Returns:
            更新后的记录对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                update(self.model).where(self.model.id == id).values(**kwargs)
            )
            await session.commit()

            if result.rowcount == 0:
                return None

            obj = await self.get_by_id(id)
            self.logger.debug(f"更新记录: {self.model.__name__} ID={id}")
            return obj

    async def delete(self, id: int) -> bool:
        """
        删除记录

        Args:
            id: 记录 ID

        Returns:
            是否删除成功
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(delete(self.model).where(self.model.id == id))
            await session.commit()
            success = result.rowcount > 0
            if success:
                self.logger.debug(f"删除记录: {self.model.__name__} ID={id}")
            return success

    async def count(self, **filters) -> int:
        """
        统计记录数量

        Args:
            **filters: 过滤条件

        Returns:
            记录数量
        """
        async with self.db_manager.get_session() as session:
            query = select(func.count(self.model.id))

            # 应用过滤条件
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

            result = await session.execute(query)
            return result.scalar() or 0

    async def exists(self, id: int) -> bool:
        """
        检查记录是否存在

        Args:
            id: 记录 ID

        Returns:
            是否存在
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(func.count(self.model.id)).where(self.model.id == id)
            )
            return (result.scalar() or 0) > 0

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelType]:
        """
        批量创建记录

        Args:
            items: 记录数据列表

        Returns:
            创建的记录对象列表
        """
        async with self.db_manager.get_session() as session:
            objects = [self.model(**item) for item in items]
            session.add_all(objects)
            await session.commit()
            self.logger.debug(f"批量创建记录: {self.model.__name__} 数量={len(objects)}")
            return objects


# 全局数据库管理器实例
db_manager = DatabaseManager()
