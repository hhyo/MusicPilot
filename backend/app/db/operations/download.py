"""
DownloadHistory 操作类
"""

from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.download import DownloadHistory
from app.db import OperBase
from app.core.context import DownloadStatus, DownloaderType


class DownloadHistoryOper(OperBase[DownloadHistory]):
    """DownloadHistory 操作类"""

    async def get_by_source_id(self, source_id: str) -> Optional[DownloadHistory]:
        """
        根据来源 ID 获取下载历史

        Args:
            source_id: 来源 ID

        Returns:
            下载历史对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(DownloadHistory).where(DownloadHistory.source_id == source_id)
            )
            return result.scalar_one_or_none()

    async def get_by_status(
        self, status: DownloadStatus, skip: int = 0, limit: int = 100
    ) -> List[DownloadHistory]:
        """
        根据状态获取下载历史

        Args:
            status: 下载状态
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            下载历史列表
        """
        return await self.get_all(skip=skip, limit=limit, status=status.value)

    async def get_by_source(
        self, source: DownloaderType, skip: int = 0, limit: int = 100
    ) -> List[DownloadHistory]:
        """
        根据来源获取下载历史

        Args:
            source: 下载器类型
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            下载历史列表
        """
        return await self.get_all(skip=skip, limit=limit, source=source.value)

    async def search_by_title(self, keyword: str, limit: int = 50) -> List[DownloadHistory]:
        """
        搜索下载历史（按标题）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            下载历史列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(DownloadHistory)
                .where(DownloadHistory.title.ilike(f"%{keyword}%"))
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_recent(self, limit: int = 50) -> List[DownloadHistory]:
        """
        获取最近的下载记录

        Args:
            limit: 返回数量

        Returns:
            下载历史列表
        """
        async with self.db_manager.get_session() as session:
            query = select(DownloadHistory).order_by(DownloadHistory.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_failed(self, limit: int = 50) -> List[DownloadHistory]:
        """
        获取失败的下载记录

        Args:
            limit: 返回数量

        Returns:
            下载历史列表
        """
        return await self.get_by_status(DownloadStatus.FAILED, limit=limit)

    async def update_status(
        self, id: int, status: DownloadStatus, error_message: Optional[str] = None
    ) -> Optional[DownloadHistory]:
        """
        更新下载状态

        Args:
            id: 下载历史 ID
            status: 下载状态
            error_message: 错误信息

        Returns:
            更新后的下载历史对象
        """
        from datetime import datetime

        update_data = {"status": status.value}
        if error_message:
            update_data["error_message"] = error_message

        if status == DownloadStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow().isoformat()

        return await self.update(id, **update_data)
