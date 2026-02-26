"""
SubscribeRelease 操作类
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.subscribe_release import SubscribeRelease
from app.db import OperBase


class SubscribeReleaseOper(OperBase[SubscribeRelease]):
    """SubscribeRelease 操作类"""

    async def get_by_subscribe_id(self, subscribe_id: int, limit: int = 100) -> List[SubscribeRelease]:
        """
        根据订阅 ID 获取发布记录

        Args:
            subscribe_id: 订阅 ID
            limit: 返回数量

        Returns:
            发布记录列表
        """
        async with self.db_manager.get_session() as session:
            query = select(SubscribeRelease).where(
                SubscribeRelease.subscribe_id == subscribe_id
            ).order_by(SubscribeRelease.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_status(
        self,
        download_status: str,
        subscribe_id: Optional[int] = None,
        limit: int = 100
    ) -> List[SubscribeRelease]:
        """
        根据下载状态获取发布记录

        Args:
            download_status: 下载状态
            subscribe_id: 订阅 ID（可选）
            limit: 返回数量

        Returns:
            发布记录列表
        """
        async with self.db_manager.get_session() as session:
            query = select(SubscribeRelease).where(
                SubscribeRelease.download_status == download_status
            )

            if subscribe_id is not None:
                query = query.where(SubscribeRelease.subscribe_id == subscribe_id)

            query = query.order_by(SubscribeRelease.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_downloading(self) -> List[SubscribeRelease]:
        """
        获取正在下载的发布记录

        Returns:
            发布记录列表
        """
        return await self.get_by_status("downloading")

    async def get_failed(self, limit: int = 100) -> List[SubscribeRelease]:
        """
        获取下载失败的发布记录

        Args:
            limit: 返回数量

        Returns:
            发布记录列表
        """
        return await self.get_by_status("failed", limit=limit)

    async def get_by_torrent_id(self, torrent_id: str) -> Optional[SubscribeRelease]:
        """
        根据种子 ID 获取发布记录

        Args:
            torrent_id: 种子 ID

        Returns:
            发布记录对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SubscribeRelease).where(SubscribeRelease.torrent_id == torrent_id)
            )
            return result.scalar_one_or_none()

    async def update_download_status(
        self,
        id: int,
        download_status: str,
        error_message: Optional[str] = None
    ) -> Optional[SubscribeRelease]:
        """
        更新下载状态

        Args:
            id: 发布记录 ID
            download_status: 下载状态
            error_message: 错误信息

        Returns:
            更新后的发布记录对象
        """
        update_data = {"download_status": download_status}
        if error_message is not None:
            update_data["error_message"] = error_message
        return await self.update(id, **update_data)

    async def get_pending_count(self, subscribe_id: Optional[int] = None) -> int:
        """
        获取待下载数量

        Args:
            subscribe_id: 订阅 ID（可选）

        Returns:
            待下载数量
        """
        filters = {"download_status": "pending"}
        if subscribe_id is not None:
            filters["subscribe_id"] = subscribe_id
        return await self.count(**filters)

    async def get_release_statistics(self, subscribe_id: int) -> dict:
        """
        获取订阅发布统计

        Args:
            subscribe_id: 订阅 ID

        Returns:
            统计信息
        """
        async with self.db_manager.get_session() as session:
            total = await session.execute(
                select(func.count(SubscribeRelease.id)).where(
                    SubscribeRelease.subscribe_id == subscribe_id
                )
            )

            pending = await session.execute(
                select(func.count(SubscribeRelease.id)).where(
                    and_(
                        SubscribeRelease.subscribe_id == subscribe_id,
                        SubscribeRelease.download_status == "pending"
                    )
                )
            )

            downloading = await session.execute(
                select(func.count(SubscribeRelease.id)).where(
                    and_(
                        SubscribeRelease.subscribe_id == subscribe_id,
                        SubscribeRelease.download_status == "downloading"
                    )
                )
            )

            completed = await session.execute(
                select(func.count(SubscribeRelease.id)).where(
                    and_(
                        SubscribeRelease.subscribe_id == subscribe_id,
                        SubscribeRelease.download_status == "completed"
                    )
                )
            )

            failed = await session.execute(
                select(func.count(SubscribeRelease.id)).where(
                    and_(
                        SubscribeRelease.subscribe_id == subscribe_id,
                        SubscribeRelease.download_status == "failed"
                    )
                )
            )

            return {
                "total": total.scalar() or 0,
                "pending": pending.scalar() or 0,
                "downloading": downloading.scalar() or 0,
                "completed": completed.scalar() or 0,
                "failed": failed.scalar() or 0,
            }