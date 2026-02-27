"""
Player API 端点
播放器状态管理
"""


from fastapi import APIRouter, Depends, HTTPException

from app.chain.playback import PlaybackChain
from app.core.config import settings
from app.schemas.response import ResponseModel

router = APIRouter()


async def get_playback_chain() -> PlaybackChain:
    """获取 PlaybackChain 实例"""
    # 创建核心组件
    from app.core.cache import AsyncFileCache
    from app.core.event import EventManager
    from app.core.module import ModuleManager
    from app.core.plugin import PluginManager

    event_manager = EventManager()
    module_manager = ModuleManager()
    plugin_manager = PluginManager(event_manager)
    cache = AsyncFileCache(settings.cache_path, settings.cache_ttl)

    # 创建 PlaybackChain
    return PlaybackChain(
        event_manager=event_manager,
        module_manager=module_manager,
        plugin_manager=plugin_manager,
        cache=cache,
    )


@router.get("/current", response_model=ResponseModel[dict])
async def get_current_state(
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    获取当前播放状态

    返回当前曲目、播放状态、进度、队列信息等
    """
    # 获取队列信息
    queue_info = playback_chain.get_queue_info()

    # 获取播放历史
    history = await playback_chain.get_history(limit=20)

    # 组装响应
    return ResponseModel(
        data={
            "is_playing": False,
            "track": queue_info.get("current_track"),
            "next_track": queue_info.get("next_track"),
            "queue": queue_info.get("queue"),
            "current_index": queue_info.get("current_index"),
            "queue_count": len(queue_info.get("queue", [])),
            "repeat_mode": queue_info.get("repeat_mode"),
            "shuffle": queue_info.get("is_shuffle"),
            "volume": 1.0,
            "position": (
                queue_info.get("current_track", {}).get("position", 0)
                if queue_info.get("current_track")
                else 0
            ),
            "duration": (
                queue_info.get("current_track", {}).get("duration", 0)
                if queue_info.get("current_track")
                else 0
            ),
            "history": history[:10],  # 最近 10 条
        }
    )


@router.get("/history", response_model=ResponseModel[list])
async def get_play_history(
    limit: int = 50,
    user_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    获取播放历史

    - **limit**: 返回数量（最多 100）
    - **user_id**: 用户 ID（可选，筛选特定用户的历史）
    """
    history = await playback_chain.get_history(user_id=user_id, limit=min(limit, 100))

    return ResponseModel(data=history)


@router.post("/play", response_model=ResponseModel[dict])
async def play_track(
    track_id: int,
    user_id: str | None = None,
    playlist_id: int | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    播放指定曲目

    - **track_id**: 曲目 ID
    - **user_id**: 用户 ID（可选）
    - **playlist_id**: 播放列表 ID（可选，从播放列表开始播放）
    """
    try:
        session = await playback_chain.play(track_id, user_id, playlist_id)

        return ResponseModel(
            message="开始播放",
            data={
                "session_id": session.session_id,
                "track_id": session.track_id,
                "is_playing": session.is_playing,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None


@router.post("/pause", response_model=ResponseModel[dict])
async def pause(
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    暂停播放

    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.pause(session_id)

    current_session = playback_chain.get_current_session()
    session_id = current_session.session_id if current_session else None

    return ResponseModel(
        message="已暂停",
        data={
            "session_id": session_id,
            "is_playing": False,
        },
    )


@router.post("/stop", response_model=ResponseModel[dict])
async def stop(
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    停止播放

    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.stop(session_id)

    return ResponseModel(message="已停止", data={})


@router.post("/next", response_model=ResponseModel[dict])
async def next_track(
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    下一首

    - **session_id**: 会话 ID，None 表示当前会话
    """
    current_session = playback_chain.get_current_session()
    session_id = current_session.session_id if current_session else None

    await playback_chain.next(session_id)

    return ResponseModel(
        message="播放下一首",
        data={
            "session_id": session_id,
            "track_id": (
                playback_chain.get_current_session().track_id
                if playback_chain.get_current_session()
                else None
            ),
        },
    )


@router.post("/previous", response_model=ResponseModel[dict])
async def previous_track(
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    上一首

    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.previous(session_id)

    current_session = playback_chain.get_current_session()
    session_id = current_session.session_id if current_session else None

    return ResponseModel(
        message="播放上一首",
        data={
            "session_id": session_id,
            "track_id": current_session.track_id if current_session else None,
        },
    )


@router.post("/seek", response_model=ResponseModel[dict])
async def seek_to_position(
    position: float,
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    跳转到指定位置

    - **position**: 位置（秒）
    - **session_id**: session ID, None 表示当前会话
    """
    await playback_chain.seek(position, session_id)

    return ResponseModel(
        message=f"跳转到 {position} 秒",
        data={
            "position": position,
        },
    )


@router.post("/volume", response_model=ResponseModel[dict])
async def set_volume(
    volume: float,
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    设置音量

    - **volume**: 音量（0.0-1.0）
    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.set_volume(volume, session_id)

    return ResponseModel(
        message=f"音量设置为 {int(volume * 100)}%",
        data={
            "volume": volume,
        },
    )


@router.post("/mute", response_model=ResponseModel[dict])
async def toggle_mute(
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    切换静音

    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.toggle_mute(session_id)

    current_session = playback_chain.get_current_session()

    return ResponseModel(
        message=f"静音: {'开启' if current_session and current_session.muted else '关闭'}",
        data={
            "muted": current_session.muted if current_session else False,
        },
    )


@router.post("/repeat", response_model=ResponseModel[dict])
async def set_repeat_mode(
    mode: str,
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    设置循环模式

    - **mode**: 循环模式（off/one/all）
    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.set_repeat_mode(mode, session_id)

    current_session = playback_chain.get_current_session()

    return ResponseModel(
        message=f"循环模式: {mode}",
        data={
            "repeat_mode": current_session.repeat_mode if current_session else "off",
        },
    )


@router.post("/shuffle", response_model=ResponseModel[dict])
async def toggle_shuffle(
    session_id: str | None = None,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    切换随机播放

    - **session_id**: 会话 ID，None 表示当前会话
    """
    await playback_chain.toggle_shuffle(session_id)

    current_session = playback_chain.get_current_session()

    return ResponseModel(
        message=f"随机播放: {'开启' if current_session and current_session.shuffle else '关闭'}",
        data={
            "shuffle": current_session.shuffle if current_session else False,
        },
    )


@router.get("/queue", response_model=ResponseModel[dict])
async def get_queue(
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    获取播放队列

    返回当前队列和队列信息
    """
    queue_info = playback_chain.get_queue_info()

    # 获取队列中的曲目详情
    track_ids = queue_info.get("queue", [])
    tracks = []
    if track_ids:
        from app.db.operations.track import TrackOper

        track_oper = TrackOper(playback_chain.db_manager)
        for track_id in track_ids[:20]:  # 最多显示 20 首
            track = await track_oper.get_by_id(track_id)
            if track:
                tracks.append(
                    {
                        "id": track.id,
                        "title": track.title,
                        "artist_id": track.artist_id,
                        "album_id": track.album_id,
                        "duration": track.duration,
                        "file_format": track.file_format,
                    }
                )

    return ResponseModel(
        data={
            "queue": queue_info.get("queue", []),
            "tracks": tracks,
            "current_index": queue_info.get("current_index"),
            "is_shuffle": queue_info.get("is_shuffle"),
            "repeat_mode": queue_info.get("repeat_mode"),
            "queue_count": len(queue_info.get("queue", [])),
            "total_count": len(track_ids),
        }
    )


@router.post("/queue/{track_id}", response_model=ResponseModel[dict])
async def add_to_queue(
    track_id: int,
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    添加曲目到队列

    - **track_id**: 曲目 ID
    """
    await playback_chain.enqueue([track_id])

    return ResponseModel(
        message="已添加到队列", data={"queue_count": len(playback_chain.get_queue())}
    )


@router.delete("/queue", response_model=ResponseModel[dict])
async def clear_queue(
    playback_chain: PlaybackChain = Depends(get_playback_chain),
):
    """
    清空播放队列
    """
    await playback_chain.clear_queue()

    return ResponseModel(message="队列已清空", data={"queue_count": 0})
