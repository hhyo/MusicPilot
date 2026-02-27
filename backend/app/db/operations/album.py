"""
Album 操作类
"""

from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.album import Album
from app.db import OperBase


class AlbumOper(OperBase[Album]):
    """Album 操作类"""

    async def get_by_musicbrainz_id(self, musicbrainz_id: str) -> Optional[Album]:
        """
        根据 MusicBrainz ID 获取专辑

        Args:
            musicbrainz_id: MusicBrainz ID

        Returns:
            专辑对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Album).where(Album.musicbrainz_id == musicbrainz_id)
            )
            return result.scalar_one_or_none()

    async def get_by_artist_id(
        self, artist_id: int, skip: int = 0, limit: int = 100
    ) -> List[Album]:
        """
        获取艺术家的专辑列表

        Args:
            artist_id: 艺术家 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            专辑列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Album).where(Album.artist_id == artist_id).offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def search_by_title(self, keyword: str, limit: int = 50) -> List[Album]:
        """
        搜索专辑（按标题）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            专辑列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Album)
                .where(
                    or_(
                        Album.title.ilike(f"%{keyword}%"),
                        Album.title_pinyin.ilike(f"%{keyword}%"),
                    )
                )
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_genre(self, genre: str, limit: int = 50) -> List[Album]:
        """
        根据流派获取专辑

        Args:
            genre: 流派
            limit: 返回数量

        Returns:
            专辑列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Album).where(Album.genres.contains(genre)).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_recent(self, limit: int = 50) -> List[Album]:
        """
        获取最近的专辑

        Args:
            limit: 返回数量

        Returns:
            专辑列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Album).order_by(Album.release_date.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_top_rated(self, limit: int = 50) -> List[Album]:
        """
        获取评分最高的专辑

        Args:
            limit: 返回数量

        Returns:
            专辑列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Album)
                .where(Album.rating.isnot(None))
                .order_by(Album.rating.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()
