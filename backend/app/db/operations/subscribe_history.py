"""
SubscribeHistory 操作类
"""
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.models.subscribe_history import SubscribeHistory
from app.db import OperBase


class SubscribeHistoryOper(OperBase[SubscribeHistory]):
    """SubscribeHistory 操作类"""

    async def get_by_subscribe(
        self,
        subscribe_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SubscribeHistory]:
        """
        获取订阅的历史记录

        Args:
            subscribe_id: 订阅 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            历史记录列表
        """
        async with self.db_manager.get_session() as session:
            query = select(SubscribeHistory).where(
                SubscribeHistory.subscribe_id == subscribe_id
            ).order_by(
                SubscribeHistory.release_date.desc()
            ).offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_musicbrainz_id(
        self,
        musicbrainz_id: str
    ) -> Optional[SubscribeHistory]:
        """
        根据 MusicBrainz ID 获取历史记录

        Args:
            musicbrainz_id: MusicBrainz ID

        Returns:
            历史记录对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SubscribeHistory).where(
                    SubscribeHistory.musicbrainz_id == musicbrainz_id
                ).order_by(SubscribeHistory.created_at.desc())
            )
            return result.scalar_one_or_none()

    async def get_recent_releases(
        self,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[SubscribeHistory]:
        """
        获取最近的发布

        Args:
            days: 天数
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            历史记录列表
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        async with self.db_manager.get_session() as session:
            query = select(SubscribeHistory).where(
                and_(
                    SubscribeHistory.release_date >= since_date.isoformat(),
                    SubscribeHistory.downloaded == True
                )
            ).order_by(
                SubscribeHistory.release_date.desc()
            ).offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_pending_downloads(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[SubscribeHistory]:
        """
        获取待下载的发布

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            历史记录列表
        """
        async with self.db_manager.get_session() as session:
            query = select(SubscribeHistory).where(
                SubscribeHistory.downloaded == False
            ).order_by(
                SubscribeHistory.release_date.desc()
            ).offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def check_exists(
        self,
        subscribe_id: int,
        musicbrainz_id: str
    ) -> bool:
        """
        检查发布是否已存在

        Args:
            subscribe_id: 订阅 ID
            musicbrainz_id: MusicBrainz ID

        Returns:
            是否存在
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SubscribeHistory).where(
                    and_(
                        SubscribeHistory.subscribe_id == subscribe_id,
                        SubscribeHistory.musicbrainz_id == musicbrainz_id
                    )
                )
            )
            return result.scalar_one_or_none() is not None

    async def update_download_status(
        self,
        id: int,
        downloaded: bool,
        download_status: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Optional[SubscribeHistory]:
        """
        更新下载状态

        Args:
            id: 历史记录 ID
            downloaded: 是否已下载
            download_status: 下载状态
            file_path: 文件路径

        Returns:
            更新后的历史记录对象
        """
        update_data = {"downloaded": downloaded}
        if download_status:
            update_data["download_status"] = download_status
        if file_path:
            update_data["file_path"] = file_path

        return await self.update(id, **update_data)

    async def get_stats(self, subscribe_id: int) -> dict:
        """
        获取订阅统计信息

        Args:
            subscribe_id: 订阅 ID

        Returns:
            统计信息
        """
        async with self.db_manager.get_session() as session:
            # 总发布数
            total_result = await session.execute(
                select(SubscribeHistory).where(
                    SubscribeHistory.subscribe_id == subscribe_id
                )
            )
            total = len(total_result.scalars().all())

            # 已下载
            downloaded_result = await session.execute(
                select(SubscribeHistory).where(
                    and_(
                        SubscribeHistory.subscribe_id == subscribe_id,
                        SubscribeHistory.downloaded == True
                    )
                )
            )
            downloaded = len(downloaded_result.scalars().all())

            # 待下载
            pending_result = await session.execute(
                select(SubscribeHistory).where(
                    and_(
                        SubscribeHistory.subscribe_id == subscribe_id,
                        SubscribeHistory.downloaded == False
                    )
                )
            )
            pending = len(pending_result.scalars().all())

            return {
                "total": total,
                "downloaded": downloaded,
                "pending": pending,
            }