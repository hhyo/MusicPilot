"""
播放控制链
处理播放控制、状态同步
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from app.chain import ChainBase
from app.core.context import PlaybackSession
from app.core.log import logger
from app.db.operations.track import TrackOper
from app.db.operations.playlist import PlaylistOper
from app.core.config import settings


class PlaybackChain(ChainBase):
    """
    播放控制链
    负责播放控制、状态同步、历史记录、队列管理
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sessions: Dict[str, PlaybackSession] = {}
        self._play_queue: List[int] = []  # 播放队列（曲目 ID 列表）
        self._history: List[Dict[str, Any]] = []  # 播放历史
        self._current_index = -1  # 当前播放队列索引
        self.logger = logger
        self.track_oper = TrackOper(self.db_manager)
        self.playlist_oper = PlaylistOper(self.db_manager)

    # ========== 会话管理 ==========

    async def create_session(
        self, track_id: int, user_id: Optional[str] = None, playlist_id: Optional[int] = None
    ) -> PlaybackSession:
        """
        创建播放会话

        Args:
            track_id: 曲目 ID
            user_id: 用户 ID
            playlist_id: 播放列表 ID

        Returns:
            播放会话对象
        """
        self.logger.info(
            f"创建播放会话: track_id={track_id}, user_id={user_id}, playlist_id={playlist_id}"
        )

        # 查询曲目信息
        track = await self.track_oper.get_by_id(track_id)
        if not track:
            raise ValueError(f"曲目不存在: {track_id}")

        # 如果在播放中，先停止当前曲目
        if self._sessions:
            current_session = list(self._sessions.values())[0]
            await self.stop(current_session.session_id)

        # 添加到播放历史
        await self.add_to_history(track_id, user_id)

        # 如果有播放列表，设置队列
        if playlist_id:
            await self.set_playlist(playlist_id)

        # 创建播放会话
        import time

        session_id = f"{user_id or 'anonymous'}:{track_id}:{time.time()}"

        session = PlaybackSession(
            session_id=session_id,
            track_id=track_id,
            user_id=user_id,
            position=0.0,
            duration=track.duration / 1000 if track.duration else None,
            volume=1.0,
            muted=False,
            repeat_mode="off",
            shuffle=False,
            started_at=datetime.utcnow().isoformat(),
        )

        self._sessions = {session_id: session}

        # 更新播放次数
        await self.track_oper.update_play_count(track_id)

        # 发送播放开始事件
        self.send_event(
            "playback.started",
            {
                "session_id": session_id,
                "track_id": track_id,
                "user_id": user_id,
                "playlist_id": playlist_id,
            },
        )

        # 同步到媒体服务器
        await self.sync_playback_to_media_server(session)

        return session

    def get_session(self, session_id: str) -> Optional[PlaybackSession]:
        """
        获取播放会话

        Args:
            session_id: 会话 ID

        Returns:
            播放会话对象
        """
        return self._sessions.get(session_id)

    def get_current_session(self) -> Optional[PlaybackSession]:
        """获取当前播放会话"""
        if self._sessions:
            return list(self._sessions.values())[0]
        return None

    async def destroy_session(self, session_id: str):
        """
        销毁播放会话

        Args:
            session_id: 会话 ID
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]

            # 同步停止状态到媒体服务器
            await self.sync_stop_to_media_server(session)

            # 移除会话
            del self._sessions[session_id]

            self.logger.info(f"播放会话已销毁: {session_id}")

    async def destroy_current_session(self):
        """销毁当前播放会话"""
        session = self.get_current_session()
        if session:
            await self.destroy_session(session.session_id)

    # ========== 播放控制 ==========

    async def play(self, track_id: int, user_id: Optional[str] = None):
        """
        播放曲目

        Args:
            track_id: 曲目 ID
            user_id: 用户 ID
        """
        self.logger.info(f"播放曲目: {track_id}")
        await self.create_session(track_id, user_id)

    async def pause(self, session_id: Optional[str] = None):
        """
        暂停播放

        Args:
            session_id: 会话 ID，None 表示当前会话
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        session.is_playing = False

        # 发送播放暂停事件
        self.send_event(
            "playback.paused",
            {
                "session_id": session.session_id,
                "position": session.position,
            },
        )

        # 同步暂停状态到媒体服务器
        await self.sync_stop_to_media_server(session)

    async def stop(self, session_id: Optional[str] = None):
        """
        停止播放

        Args:
            session_id: 会话 ID，None 表示当前会话
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        # 移除会话
        await self.destroy_session(session.session_id)

        # 发送播放停止事件
        self.send_event(
            "playback.stopped",
            {
                "session_id": session.session_id,
                "position": session.position,
            },
        )

    async def next(self, session_id: Optional[str] = None):
        """
        下一首

        Args:
            session_id: 会话 ID，None 表示当前会话
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            self.logger.warning("没有正在播放的曲目")
            return

        self.logger.info(f"播放下一首: {session.title}")

        # 获取下一首曲目
        next_track_id = self._get_next_track()
        if next_track_id:
            await self.play(next_track_id, session.user_id)
        else:
            self.logger.info("没有更多曲目，停止播放")
            await self.stop()

    async def previous(self, session_id: Optional[str] = None):
        """
        上一首

        Args:
            session_id: 会话 ID，None 表示当前会话
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            self.logger.warning("没有正在播放的曲目")
            return

        self.logger.info(f"播放上一首: {session.title}")

        # 获取上一首曲目
        prev_track_id = self._get_previous_track()
        if prev_track_id:
            await self.play(prev_track_id, session.user_id)
        else:
            self.logger.info("没有上一首曲目")

    async def seek(self, position: float, session_id: Optional[str] = None):
        """
        跳转到指定位置

        Args:
            position: 位置（秒）
            session_id: 会话 ID，None 表示当前会话
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        session.position = position

        # 同步进度到媒体服务器
        await self.sync_playback_to_media_server(session)

        # 发送进度更新事件
        self.send_event(
            "playback.seek",
            {
                "session_id": session.session_id,
                "position": position,
            },
        )

        self.logger.info(f"跳转到位置: {position}s")

    # ========== 进度控制 ==========

    async def update_progress(
        self, session_id: str, position: float, duration: Optional[float] = None
    ):
        """
        更新播放进度

        Args:
            session_id: 会话 ID
            position: 当前位置（秒）
            duration: 总时长（秒）
        """
        session = self._sessions.get(session_id)
        if not session:
            return

        session.position = position
        if duration:
            session.duration = duration

        # 同步进度到媒体服务器
        await self.sync_playback_to_media_server(session)

        # 发送进度事件
        self.send_event(
            "playback.progress",
            {
                "session_id": session_id,
                "position": position,
                "duration": session.duration,
            },
        )

    # ========== 播放队列管理 ==========

    async def set_playlist(self, playlist_id: int):
        """
        设置播放列表

        Args:
            playlist_id: 播放列表 ID
        """
        self.logger.info(f"设置播放列表: {playlist_id}")

        # 获取播放列表的曲目
        from app.db.models.playlist import PlaylistTrack

        async with self.db_manager.get_session() as db:
            from sqlalchemy import select

            result = await db.execute(
                select(PlaylistTrack.track_id)
                .where(PlaylistTrack.playlist_id == playlist_id)
                .order_by(PlaylistTrack.position)
            )
            tracks = result.scalars().all()
            self._play_queue = list(tracks)
            self._current_index = 0 if tracks else -1

        self.logger.info(f"播放队列更新: {len(self._play_queue)} 首曲目")

    async def enqueue(self, track_ids: List[int]):
        """
        将曲目加入队列

        Args:
            track_ids: 曲目 ID 列表
        """
        self._play_queue.extend(track_ids)
        self.logger.info(f"加入队列: {len(track_ids)} 首曲目")

    async def clear_queue(self):
        """清空播放队列"""
        self._play_queue = []
        self._current_index = -1
        self.logger.info("播放队列已清空")

    async def get_queue(self) -> List[int]:
        """获取当前播放队列"""
        return self._play_queue.copy()

    def _get_next_track(self) -> Optional[int]:
        """获取下一首曲目"""
        if not self._play_queue:
            return None

        # 随机播放
        if self._current_index >= len(self._play_queue) - 1:
            self._current_index = 0

        # 如果是 shuffle 模式，随机选择
        current_session = self.get_current_session()
        if current_session and current_session.shuffle:
            import random

            index = random.randint(0, len(self._play_queue) - 1)
            return self._play_queue[index]
        else:
            self._current_index = (self._current_index + 1) % len(self._play_queue)
            return self._play_queue[self._current_index]

    def _get_previous_track(self) -> Optional[int]:
        """获取上一首曲目"""
        if not self._play_queue:
            return None

        if self._current_index <= 0:
            self._current_index = len(self._play_queue) - 1

        current_session = self.get_current_session()
        if current_session and current_session.shuffle:
            import random

            index = random.randint(0, len(self._play_queue) - 1)
            return self._play_queue[index]
        else:
            self._current_index = (self._current_index - 1) % len(self._play_queue)
            return self._play_queue[self._current_index]

    # ========== 播放历史 ==========

    async def add_to_history(self, track_id: int, user_id: Optional[str] = None):
        """
        添加到播放历史

        Args:
            track_id: 曲目 ID
            user_id: 用户 ID
        """
        track = await self.track_oper.get_by_id(track_id)
        if not track:
            return

        history_item = {
            "track_id": track_id,
            "title": track.title,
            "artist_id": track.artist_id,
            "album_id": track.album_id,
            "user_id": user_id,
            "played_at": datetime.utcnow().isoformat(),
        }

        self._history.append(history_item)

        # 只保留最近 1000 条历史
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

        self.logger.debug(f"添加到历史: {track.title}")

    async def get_history(
        self, user_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取播放历史

        Args:
            user_id: 用户 ID
            limit: 返回数量

        Returns:
            历史记录列表
        """
        history = self._history.copy()

        if user_id:
            history = [h for h in history if h.get("user_id") == user_id]

        # 返回最近的记录
        return history[-limit:] if history else []

    async def clear_history(self):
        """清空播放历史"""
        self._history = []
        self.logger.info("播放历史已清空")

    # ========== 播放模式 ==========

    async def set_repeat_mode(self, repeat_mode: str, session_id: Optional[str] = None):
        """
        设置播放模式

        Args:
            repeat_mode: 播放模式（off/one/all）
            session_id: 会话 ID
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        session.repeat_mode = repeat_mode

        self.logger.info(f"设置播放模式: {repeat_mode}")

        # 发送模式变更事件
        self.send_event(
            "playback.repeat_mode_changed",
            {
                "session_id": session.session_id,
                "repeat_mode": repeat_mode,
            },
        )

    async def toggle_shuffle(self, session_id: Optional[str] = None):
        """
        切换随机播放

        Args:
            session_id: 会话 ID
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        session.shuffle = not session.shuffle

        self.logger.info(f"随机播放: {session.shuffle}")

        # 发送模式变更事件
        self.send_event(
            "playback.shuffle_toggled",
            {
                "session_id": session.session_id,
                "shuffle": session.shuffle,
            },
        )

    # ========== 音量控制 ==========

    async def set_volume(self, volume: float, session_id: Optional[str] = None):
        """
        设置音量

        Args:
            volume: 音量（0.0-1.0）
            session_id: 会话 ID
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        session.volume = max(0.0, min(1.0, volume))

        # 同步音量到媒体服务器
        await self.sync_playback_to_media_server(session)

        # 发送音量变更事件
        self.send_event(
            "playback.volume_changed",
            {
                "session_id": session.session_id,
                "volume": session.volume,
            },
        )

        self.logger.info(f"设置音量: {session.volume}")

    async def toggle_mute(self, session_id: Optional[str] = None):
        """
        切换静音

        Args:
            session_id: 会话 ID
        """
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()

        if not session:
            return

        session.muted = not session.muted

        self.logger.info(f"静音: {session.muted}")

        # 发送静音状态事件
        self.send_event(
            "playback.mute_toggled",
            {
                "session_id": session.session_id,
                "muted": session.muted,
            },
        )

    # ========== 媒体服务器同步 ==========

    async def sync_playback_to_media_server(self, session: PlaybackSession):
        """
        同步播放状态到媒体服务器

        Args:
            session: 播放会话对象
        """
        # 获取启用的媒体服务器
        from app.db.operations.media import MediaServerOper

        media_oper = MediaServerOper(self.db_manager)
        servers = await media_oper.get_enabled()

        # 同步到所有启用的服务器
        for server in servers:
            try:
                await self.run_module("media", "sync_playback", server, session.to_dict())
            except Exception as e:
                self.logger.error(f"同步播放状态到 {server.name} 失败: {e}")

    async def sync_stop_to_media_server(self, session: PlaybackSession):
        """
        同步停止状态到媒体服务器

        Args:
            session: 播放会话对象
        """
        # 获取启用的媒体服务器
        from app.db.operations.media import MediaServerOper

        media_oper = MediaServerOper(self.db_manager)
        servers = await media_oper.get_enabled()

        # 同步到所有启用的服务器
        for server in servers:
            try:
                await self.run_module("media", "sync_stop", server, session.to_dict())
            except Exception as e:
                self.logger.error(f"同步停止状态到 {server.name} 失败: {e}")

    # ========== 状态获取 ==========

    def get_all_sessions(self) -> List[PlaybackSession]:
        """获取所有播放会话"""
        return list(self._sessions.values())

    def get_queue_info(self) -> Dict[str, Any]:
        """
        获取队列信息

        Returns:
            队列信息字典
        """
        current_session = self.get_current_session()
        current_track_id = current_session.track_id if current_session else None

        # 获取当前曲目信息
        current_track = None
        if current_track_id:
            import asyncio

            try:
                current_track = asyncio.run(self.track_oper.get_by_id(current_track_id))
            except:
                pass

        # 获取下一首曲目信息
        next_track_id = self._get_next_track()
        next_track = None
        if next_track_id:
            try:
                next_track = asyncio.run(self.track_oper.get_by_id(next_track_id))
            except:
                pass

        return {
            "queue": self._play_queue,
            "current_index": self._current_index,
            "is_shuffle": current_session.shuffle if current_session else False,
            "repeat_mode": current_session.repeat_mode if current_session else "off",
            "current_track": current_track,
            "next_track": next_track,
        }
