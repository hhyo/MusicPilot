"""
播放列表链
处理播放列表管理
"""

from typing import List, Optional

from app.chain import ChainBase
from app.core.context import PlaylistType, SmartQuery
from app.core.log import logger


class PlaylistChain(ChainBase):
    """
    播放列表链
    负责播放列表的创建、管理、智能生成
    """

    async def create(
        self,
        name: str,
        playlist_type: PlaylistType = PlaylistType.NORMAL,
        description: Optional[str] = None,
        smart_query: Optional[SmartQuery] = None,
    ) -> int:
        """
        创建播放列表

        Args:
            name: 播放列表名称
            playlist_type: 播放列表类型
            description: 描述
            smart_query: 智能查询条件（仅智能播放列表）

        Returns:
            播放列表 ID
        """
        self.logger.info(f"创建播放列表: {name}")

        from app.db.operations.playlist import PlaylistOper

        playlist_oper = PlaylistOper(self.db_manager)

        playlist = await playlist_oper.create(
            type=playlist_type.value,
            name=name,
            description=description,
            smart_query=smart_query.to_dict() if smart_query else None,
        )

        self.logger.info(f"播放列表创建成功: {playlist.id}")

        return playlist.id

    async def add_tracks(self, playlist_id: int, track_ids: List[int]) -> int:
        """
        添加曲目到播放列表

        Args:
            playlist_id: 播放列表 ID
            track_ids: 曲目 ID 列表

        Returns:
            添加的曲目数量
        """
        self.logger.info(f"添加曲目到播放列表: {playlist_id}, 共 {len(track_ids)} 首")

        from app.db.operations.playlist import PlaylistOper

        playlist_oper = PlaylistOper(self.db_manager)

        # 获取当前最大位置
        from app.db.models.playlist import PlaylistTrack
        from sqlalchemy import select, func

        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(func.max(PlaylistTrack.position)).where(
                    PlaylistTrack.playlist_id == playlist_id
                )
            )
            max_position = result.scalar_one_or_none() or 0

        # 批量添加
        added = 0
        for i, track_id in enumerate(track_ids):
            await playlist_oper.add_track(playlist_id, track_id, max_position + i + 1)
            added += 1

        self.logger.info(f"成功添加 {added} 首曲目")

        return added

    async def remove_tracks(self, playlist_id: int, track_ids: List[int]) -> int:
        """
        从播放列表移除曲目

        Args:
            playlist_id: 播放列表 ID
            track_ids: 曲目 ID 列表

        Returns:
            移除的曲目数量
        """
        self.logger.info(f"从播放列表移除曲目: {playlist_id}, 共 {len(track_ids)} 首")

        from app.db.operations.playlist import PlaylistOper

        playlist_oper = PlaylistOper(self.db_manager)

        removed = 0
        for track_id in track_ids:
            if await playlist_oper.remove_track(playlist_id, track_id):
                removed += 1

        self.logger.info(f"成功移除 {removed} 首曲目")

        return removed

    async def reorder_tracks(self, playlist_id: int, track_ids: List[int]):
        """
        重新排序播放列表曲目

        Args:
            playlist_id: 播放列表 ID
            track_ids: 曲目 ID 列表（按新顺序排列）
        """
        self.logger.info(f"重新排序播放列表: {playlist_id}")

        from app.db.operations.playlist import PlaylistOper

        playlist_oper = PlaylistOper(self.db_manager)

        await playlist_oper.reorder_tracks(playlist_id, track_ids)

        self.logger.info("排序完成")

    async def generate_smart(self, query: SmartQuery) -> List[int]:
        """
        生成智能播放列表

        Args:
            query: 智能查询条件

        Returns:
            曲目 ID 列表
        """
        self.logger.info("生成智能播放列表")

        # 根据查询条件筛选曲目
        track_ids = await self._execute_smart_query(query)

        self.logger.info(f"生成 {len(track_ids)} 首曲目")

        return track_ids

    async def _execute_smart_query(self, query: SmartQuery) -> List[int]:
        """
        执行智能查询

        Args:
            query: 智能查询对象

        Returns:
            曲目 ID 列表
        """
        # TODO: 实现实际的智能查询逻辑
        # 这里需要根据 query.conditions 解析条件并查询数据库

        # 临时实现：返回随机曲目
        from app.db.operations.track import TrackOper

        track_oper = TrackOper(self.db_manager)
        tracks = await track_oper.get_all(limit=query.limit or 100)

        return [track.id for track in tracks]
