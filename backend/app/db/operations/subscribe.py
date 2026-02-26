"""
Subscribe 操作类
"""
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.subscribe import Subscribe
from app.db import OperBase


class SubscribeOper(OperBase[Subscribe]):
    """Subscribe 操作类"""

    async def get_by_musicbrainz_id(self, musicbrainz_id: str) -> Optional[Subscribe]:
        """
        根据 MusicBrainz ID 获取订阅

        Args:
            musicbrainz_id: MusicBrainz ID

        Returns:
            订阅对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Subscribe).where(Subscribe.musicbrainz_id == musicbrainz_id)
            )
            return result.scalar_one_or_none()

    async def get_by_type(self, sub_type: str, skip: int = 0, limit: int = 100) -> List[Subscribe]:
        """
        根据类型获取订阅

        Args:
            sub_type: 订阅类型（artist, album）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            订阅列表
        """
        return await self.get_all(skip=skip, limit=limit, type=sub_type)

    async def get_active(self, skip: int = 0, limit: int = 100) -> List[Subscribe]:
        """
        获取活跃的订阅

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            订阅列表
        """
        return await self.get_all(skip=skip, limit=limit, state="active")

    async def search_by_name(self, keyword: str, limit: int = 50) -> List[Subscribe]:
        """
        搜索订阅（按名称）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            订阅列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Subscribe).where(
                Subscribe.name.ilike(f"%{keyword}%")
            ).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def update_check_time(self, id: int) -> Optional[Subscribe]:
        """
        更新检查时间

        Args:
            id: 订阅 ID

        Returns:
            更新后的订阅对象
        """
        from datetime import datetime
        return await self.update(id, last_check=datetime.utcnow().isoformat())

    async def update_release(
        self,
        id: int,
        release_count: Optional[int] = None
    ) -> Optional[Subscribe]:
        """
        更新发布信息

        Args:
            id: 订阅 ID
            release_count: 发布数量

        Returns:
            更新后的订阅对象
        """
        from datetime import datetime

        update_data = {"last_release": datetime.utcnow().isoformat()}
        if release_count is not None:
            update_data["release_count"] = release_count
        else:
            # 增加发布数量
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(Subscribe).where(Subscribe.id == id)
                )
                subscribe = result.scalar_one_or_none()
                if subscribe:
                    update_data["release_count"] = (subscribe.release_count or 0) + 1

        return await self.update(id, **update_data)
