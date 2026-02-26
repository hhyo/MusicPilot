"""
Artist 操作类
"""
from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.artist import Artist
from app.db import OperBase


class ArtistOper(OperBase[Artist]):
    """Artist 操作类"""

    async def get_by_musicbrainz_id(self, musicbrainz_id: str) -> Optional[Artist]:
        """
        根据 MusicBrainz ID 获取艺术家

        Args:
            musicbrainz_id: MusicBrainz ID

        Returns:
            艺术家对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Artist).where(Artist.musicbrainz_id == musicbrainz_id)
            )
            return result.scalar_one_or_none()

    async def search_by_name(self, keyword: str, limit: int = 50) -> List[Artist]:
        """
        搜索艺术家（按名称）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            艺术家列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Artist).where(
                or_(
                    Artist.name.ilike(f"%{keyword}%"),
                    Artist.name_pinyin.ilike(f"%{keyword}%"),
                )
            ).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_top_rated(self, limit: int = 50) -> List[Artist]:
        """
        获取评分最高的艺术家

        Args:
            limit: 返回数量

        Returns:
            艺术家列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Artist).where(
                Artist.rating.isnot(None)
            ).order_by(Artist.rating.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_genre(self, genre: str, limit: int = 50) -> List[Artist]:
        """
        根据流派获取艺术家

        Args:
            genre: 流派
            limit: 返回数量

        Returns:
            艺术家列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Artist).where(
                Artist.genres.contains(genre)
            ).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def update_rating(self, id: int, rating: float, rating_count: int) -> Optional[Artist]:
        """
        更新评分

        Args:
            id: 艺术家 ID
            rating: 评分
            rating_count: 评分人数

        Returns:
            更新后的艺术家对象
        """
        return await self.update(id, rating=rating, rating_count=rating_count)
