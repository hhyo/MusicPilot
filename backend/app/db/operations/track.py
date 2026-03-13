"""
Track 操作类
"""

from sqlalchemy import and_, or_, select

from app.db import OperBase
from app.db.models.track import Track


class TrackOper(OperBase[Track]):
    """Track 操作类"""

    async def get_by_musicbrainz_id(self, musicbrainz_id: str) -> Track | None:
        """
        根据 MusicBrainz ID 获取曲目

        Args:
            musicbrainz_id: MusicBrainz ID

        Returns:
            曲目对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Track).where(Track.musicbrainz_id == musicbrainz_id)
            )
            return result.scalar_one_or_none()

    async def get_by_album_id(self, album_id: int, skip: int = 0, limit: int = 100) -> list[Track]:
        """
        获取专辑的曲目列表

        Args:
            album_id: 专辑 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Track)
                .where(Track.album_id == album_id)
                .order_by(Track.disc_number.asc(), Track.track_number.asc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_artist_id(
        self, artist_id: int, skip: int = 0, limit: int = 100
    ) -> list[Track]:
        """
        获取艺术家的曲目列表

        Args:
            artist_id: 艺术家 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Track).where(Track.artist_id == artist_id).offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def search_by_title(self, keyword: str, limit: int = 50) -> list[Track]:
        """
        搜索曲目（按标题）

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Track)
                .where(
                    or_(
                        Track.title.ilike(f"%{keyword}%"),
                        Track.title_pinyin.ilike(f"%{keyword}%"),
                    )
                )
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_path(self, path: str) -> Track | None:
        """
        根据文件路径获取曲目

        Args:
            path: 文件路径

        Returns:
            曲目对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(Track).where(Track.path == path))
            return result.scalar_one_or_none()

    async def get_by_library(
        self, path_prefix: str, skip: int = 0, limit: int = 100
    ) -> list[Track]:
        """
        获取指定目录下的曲目

        Args:
            path_prefix: 路径前缀
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Track).where(Track.path.like(f"{path_prefix}%")).offset(skip).limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_most_played(self, limit: int = 50) -> list[Track]:
        """
        获取播放次数最多的曲目

        Args:
            limit: 返回数量

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Track)
                .where(Track.play_count > 0)
                .order_by(Track.play_count.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_recently_played(self, limit: int = 50) -> list[Track]:
        """
        获取最近播放的曲目

        Args:
            limit: 返回数量

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Track)
                .where(Track.last_played.isnot(None))
                .order_by(Track.last_played.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def update_play_count(self, id: int) -> Track | None:
        """
        更新播放次数

        Args:
            id: 曲目 ID

        Returns:
            更新后的曲目对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(Track).where(Track.id == id))
            track = result.scalar_one_or_none()
            if not track:
                return None

            new_count = (track.play_count or 0) + 1
            await session.execute(
                Track.__table__.update()
                .where(Track.id == id)
                .values(play_count=new_count, last_played=Track.updated_at)
            )
            await session.commit()
            track.play_count = new_count
            return track

    async def get_by_size_and_duration(
        self, file_size: int, duration: float | None = None
    ) -> list[Track]:
        """
        根据文件大小和时长获取曲目（用于去重）

        Args:
            file_size: 文件大小（字节）
            duration: 时长（秒）

        Returns:
            曲目列表
        """
        async with self.db_manager.get_session() as session:
            conditions = [Track.file_size == file_size]

            if duration is not None:
                # 允许 1 秒的误差
                conditions.append(Track.duration >= duration - 1, Track.duration <= duration + 1)

            query = select(Track).where(and_(*conditions))
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_file_hash(self, file_hash: str) -> Track | None:
        """
        根据文件哈希获取曲目（用于去重）

        Args:
            file_hash: 文件哈希值

        Returns:
            曲目对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(Track).where(Track.file_hash == file_hash))
            return result.scalar_one_or_none()
