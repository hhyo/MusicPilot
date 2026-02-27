"""
Playlist 操作类
"""


from sqlalchemy import and_, delete, select

from app.db import OperBase
from app.db.models.playlist import Playlist, PlaylistTrack


class PlaylistOper(OperBase[Playlist]):
    """Playlist 操作类"""

    async def get_with_tracks(self, playlist_id: int) -> Playlist | None:
        """
        获取播放列表及其曲目

        Args:
            playlist_id: 播放列表 ID

        Returns:
            播放列表对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(Playlist).where(Playlist.id == playlist_id))
            playlist = result.scalar_one_or_none()
            if playlist:
                # 加载曲目关系
                await session.refresh(playlist, ["tracks"])
            return playlist

    async def get_public_playlists(self, skip: int = 0, limit: int = 100) -> list[Playlist]:
        """
        获取公开播放列表

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            播放列表列表
        """
        return await self.get_all(skip=skip, limit=limit, is_public=True)

    async def get_smart_playlists(self, skip: int = 0, limit: int = 100) -> list[Playlist]:
        """
        获取智能播放列表

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            播放列表列表
        """
        from app.core.context import PlaylistType

        return await self.get_all(skip=skip, limit=limit, type=PlaylistType.SMART.value)

    async def add_track(
        self, playlist_id: int, track_id: int, position: int | None = None
    ) -> PlaylistTrack | None:
        """
        添加曲目到播放列表

        Args:
            playlist_id: 播放列表 ID
            track_id: 曲目 ID
            position: 位置（None 表示添加到最后）

        Returns:
            播放列表曲目关联对象
        """
        async with self.db_manager.get_session() as session:
            # 如果没有指定位置，获取当前最大位置
            if position is None:
                result = await session.execute(
                    select(PlaylistTrack.position)
                    .where(PlaylistTrack.playlist_id == playlist_id)
                    .order_by(PlaylistTrack.position.desc())
                    .limit(1)
                )
                max_position = result.scalar_one_or_none()
                position = (max_position or 0) + 1

            # 创建关联
            playlist_track = PlaylistTrack(
                playlist_id=playlist_id, track_id=track_id, position=position
            )
            session.add(playlist_track)
            await session.commit()
            await session.refresh(playlist_track)
            return playlist_track

    async def remove_track(self, playlist_id: int, track_id: int) -> bool:
        """
        从播放列表移除曲目

        Args:
            playlist_id: 播放列表 ID
            track_id: 曲目 ID

        Returns:
            是否删除成功
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                delete(PlaylistTrack).where(
                    and_(
                        PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.track_id == track_id
                    )
                )
            )
            await session.commit()
            return result.rowcount > 0

    async def clear_tracks(self, playlist_id: int) -> bool:
        """
        清空播放列表的所有曲目

        Args:
            playlist_id: 播放列表 ID

        Returns:
            是否清空成功
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def reorder_tracks(self, playlist_id: int, track_ids: list[int]) -> bool:
        """
        重新排序播放列表曲目

        Args:
            playlist_id: 播放列表 ID
            track_ids: 曲目 ID 列表（按新顺序排列）

        Returns:
            是否排序成功
        """
        async with self.db_manager.get_session() as session:
            # 获取所有曲目关联
            result = await session.execute(
                select(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist_id)
                .order_by(PlaylistTrack.position)
            )
            tracks = result.scalars().all()

            # 创建 ID 映射
            track_map = {track.track_id: track for track in tracks}

            # 更新位置
            for position, track_id in enumerate(track_ids, start=1):
                if track_id in track_map:
                    track_map[track_id].position = position

            await session.commit()
            return True
