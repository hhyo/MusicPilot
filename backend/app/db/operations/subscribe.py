"""
Subscribe 操作类
"""

from sqlalchemy import select

from app.db import OperBase
from app.db.models.subscribe import Subscribe


class SubscribeOper(OperBase[Subscribe]):
    """Subscribe 操作类"""

    async def get_by_musicbrainz_id(self, musicbrainz_id: str) -> Subscribe | None:
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

    async def get_by_playlist_id(self, playlist_id: str) -> Subscribe | None:
        """
        根据歌单/榜单 ID 获取订阅

        Args:
            playlist_id: 歌单/榜单 ID

        Returns:
            订阅对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Subscribe).where(Subscribe.playlist_id == playlist_id)
            )
            return result.scalar_one_or_none()

    async def get_by_type(self, sub_type: str, skip: int = 0, limit: int = 100) -> list[Subscribe]:
        """
        根据类型获取订阅

        Args:
            sub_type: 订阅类型（artist, album, playlist, chart）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            订阅列表
        """
        return await self.get_all(skip=skip, limit=limit, type=sub_type)

    async def get_by_source_type(
        self, source_type: str, skip: int = 0, limit: int = 100
    ) -> list[Subscribe]:
        """
        根据来源类型获取订阅

        Args:
            source_type: 来源类型（musicbrainz, netease, qq）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            订阅列表
        """
        return await self.get_all(skip=skip, limit=limit, source_type=source_type)

    async def get_active(self, skip: int = 0, limit: int = 100) -> list[Subscribe]:
        """
        获取活跃的订阅

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            订阅列表
        """
        return await self.get_all(skip=skip, limit=limit, state="active")

    async def search_by_name(self, keyword: str, limit: int = 50) -> list[Subscribe]:
        """
        搜索订阅（按名称）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            订阅列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Subscribe).where(Subscribe.name.ilike(f"%{keyword}%")).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def update_check_time(self, id: int) -> Subscribe | None:
        """
        更新检查时间

        Args:
            id: 订阅 ID

        Returns:
            更新后的订阅对象
        """
        from datetime import datetime

        return await self.update(id, last_check=datetime.utcnow().isoformat())

    async def update_release(self, id: int, release_count: int | None = None) -> Subscribe | None:
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
                result = await session.execute(select(Subscribe).where(Subscribe.id == id))
                subscribe = result.scalar_one_or_none()
                if subscribe:
                    update_data["release_count"] = (subscribe.release_count or 0) + 1

        return await self.update(id, **update_data)
