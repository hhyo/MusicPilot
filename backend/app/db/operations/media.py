"""
MediaServer 操作类
"""


from sqlalchemy import select

from app.core.context import MediaServerType
from app.db import OperBase
from app.db.models.media import MediaServer


class MediaServerOper(OperBase[MediaServer]):
    """MediaServer 操作类"""

    async def get_by_type(
        self, server_type: MediaServerType, skip: int = 0, limit: int = 100
    ) -> list[MediaServer]:
        """
        根据类型获取媒体服务器

        Args:
            server_type: 服务器类型
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            媒体服务器列表
        """
        return await self.get_all(skip=skip, limit=limit, type=server_type.value)

    async def get_enabled(self, server_type: MediaServerType | None = None) -> list[MediaServer]:
        """
        获取启用的媒体服务器

        Args:
            server_type: 服务器类型（None 表示所有类型）

        Returns:
            媒体服务器列表
        """
        if server_type:
            return await self.get_all(type=server_type.value, enabled=True)
        return await self.get_all(enabled=True)

    async def search_by_name(self, keyword: str, limit: int = 50) -> list[MediaServer]:
        """
        搜索媒体服务器（按名称）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            媒体服务器列表
        """
        async with self.db_manager.get_session() as session:
            query = select(MediaServer).where(MediaServer.name.ilike(f"%{keyword}%")).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def test_connection(self, id: int) -> tuple[bool, str]:
        """
        测试媒体服务器连接

        Args:
            id: 媒体服务器 ID

        Returns:
            (是否成功, 消息)
        """
        server = await self.get_by_id(id)
        if not server:
            return False, "媒体服务器不存在"

        # TODO: 实现实际连接测试
        # 根据类型调用相应的模块进行连接测试
        if server.type == MediaServerType.PLEX.value:
            return await self._test_plex(server)
        elif server.type == MediaServerType.JELLYFIN.value:
            return await self._test_jellyfin(server)
        else:
            return False, f"不支持的媒体服务器类型: {server.type}"

    async def _test_plex(self, server: MediaServer) -> tuple[bool, str]:
        """测试 Plex 连接"""
        # TODO: 实现 Plex 连接测试
        return True, "连接成功"

    async def _test_jellyfin(self, server: MediaServer) -> tuple[bool, str]:
        """测试 Jellyfin 连接"""
        # TODO: 实现 Jellyfin 连接测试
        return True, "连接成功"

    async def toggle_enabled(self, id: int) -> MediaServer | None:
        """
        切换媒体服务器启用状态

        Args:
            id: 媒体服务器 ID

        Returns:
            更新后的媒体服务器对象
        """
        server = await self.get_by_id(id)
        if not server:
            return None
        return await self.update(id, enabled=not server.enabled)
