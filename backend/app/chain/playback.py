"""
播放链
处理播放控制
"""
from typing import Optional, Dict, Any

from app.chain import ChainBase
from app.core.context import PlaybackSession, DownloadStatus
from app.core.log import logger


class PlaybackChain(ChainBase):
    """
    播放链
    负责播放控制、状态同步
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sessions: Dict[str, PlaybackSession] = {}

    async def play(self, track_id: int, user_id: Optional[str] = None) -> PlaybackSession:
        """
        播放曲目

        Args:
            track_id: 曲目 ID
            user_id: 用户 ID

        Returns:
            播放会话对象
        """
        self.logger.info(f"播放曲目: {track_id}")

        # 查询曲目信息
        from app.db.operations.track import TrackOper
        track_oper = TrackOper(self.db_manager)
        track = await track_oper.get_by_id(track_id)

        if not track:
            self.logger.error(f"曲目不存在: {track_id}")
            raise ValueError(f"曲目不存在: {track_id}")

        # 创建播放会话
        from datetime import datetime
        session_id = f"{user_id or 'anonymous'}:{track_id}:{datetime.now().timestamp()}"

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

        self._sessions[session_id] = session

        # 更新播放次数
        await track_oper.update_play_count(track_id)

        # 发送播放开始事件
        self.send_event("playback.started", {
            "session_id": session_id,
            "track_id": track_id,
            "user_id": user_id,
        })

        # 同步到媒体服务器
        await self.sync_to_media_server(session)

        return session

    async def pause(self, session_id: str):
        """
        暂停播放

        Args:
            session_id: 会话 ID
        """
        self.logger.info(f"暂停播放: {session_id}")

        session = self._sessions.get(session_id)
        if not session:
            return

        # 发送播放暂停事件
        self.send_event("playback.paused", {
            "session_id": session_id,
            "position": session.position,
        })

        # 同步到媒体服务器
        await self.sync_stop_to_media_server(session)

    async def stop(self, session_id: str):
        """
        停止播放

        Args:
            session_id: 会话 ID
        """
        self.logger.info(f"停止播放: {session_id}")

        session = self._sessions.get(session_id)
        if not session:
            return

        # 移除会话
        del self._sessions[session_id]

        # 发送播放停止事件
        self.send_event("playback.stopped", {
            "session_id": session_id,
            "position": session.position,
        })

        # 同步到媒体服务器
        await self.sync_stop_to_media_server(session)

    async def skip(self, session_id: str, direction: str = "next"):
        """
        跳过曲目

        Args:
            session_id: 会话 ID
            direction: 方向（next/prev）
        """
        self.logger.info(f"跳过曲目: {session_id} - {direction}")

        session = self._sessions.get(session_id)
        if not session:
            return

        # TODO: 实现播放列表跳转逻辑

        # 发送跳过事件
        self.send_event("playback.skipped", {
            "session_id": session_id,
            "direction": direction,
        })

    async def seek(self, session_id: str, position: float):
        """
        跳转到指定位置

        Args:
            session_id: 会话 ID
            position: 位置（秒）
        """
        self.logger.info(f"跳转到位置: {session_id} - {position}s")

        session = self._sessions.get(session_id)
        if not session:
            return

        session.position = position

        # 同步到媒体服务器
        await self.sync_playback_to_media_server(session)

    async def sync_playback_to_media_server(self, session: PlaybackSession):
        """
        同步播放状态到媒体服务器

        Args:
            session: 播放会话对象
        """
        # 调用媒体服务器模块同步
        await self.run_module("media", "sync_playback", session)

    async def sync_stop_to_media_server(self, session: PlaybackSession):
        """
        同步停止状态到媒体服务器

        Args:
            session: 播放会话对象
        """
        # 调用媒体服务器模块同步
        await self.run_module("media", "sync_stop", session)

    def get_session(self, session_id: str) -> Optional[PlaybackSession]:
        """
        获取播放会话

        Args:
            session_id: 会话 ID

        Returns:
            播放会话对象
        """
        return self._sessions.get(session_id)