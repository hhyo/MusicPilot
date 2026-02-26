"""
Library 操作类
"""
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.library import Library
from app.db import OperBase


class LibraryOper(OperBase[Library]):
    """Library 操作类"""

    async def get_by_path(self, path: str) -> Optional[Library]:
        """
        根据路径获取音乐库

        Args:
            path: 路径

        Returns:
            音乐库对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Library).where(Library.path == path)
            )
            return result.scalar_one_or_none()

    async def get_auto_scan_libraries(self) -> List[Library]:
        """
        获取需要自动扫描的音乐库

        Returns:
            音乐库列表
        """
        return await self.get_all(auto_scan=True)

    async def update_scan_time(self, id: int) -> Optional[Library]:
        """
        更新扫描时间

        Args:
            id: 音乐库 ID

        Returns:
            更新后的音乐库对象
        """
        from datetime import datetime
        return await self.update(id, last_scan_time=datetime.utcnow().isoformat())

    async def update_stats(
        self,
        id: int,
        track_count: int,
        album_count: int,
        artist_count: int,
        total_size: int
    ) -> Optional[Library]:
        """
        更新统计信息

        Args:
            id: 音乐库 ID
            track_count: 曲目数量
            album_count: 专辑数量
            artist_count: 艺术家数量
            total_size: 总大小（字节）

        Returns:
            更新后的音乐库对象
        """
        return await self.update(
            id,
            track_count=track_count,
            album_count=album_count,
            artist_count=artist_count,
            total_size=total_size
        )
