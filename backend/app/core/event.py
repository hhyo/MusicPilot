"""
事件管理器
实现事件的发送、注册、处理，支持消息通知
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from app.core.log import logger


class EventType(StrEnum):
    """事件类型枚举"""

    # 元数据事件
    MetadataRecognized = "metadata.recognized"
    MetadataCompleted = "metadata.completed"
    MetadataFailed = "metadata.failed"

    # 下载事件
    DownloadStarted = "download.started"
    DownloadProgress = "download.progress"
    DownloadCompleted = "download.completed"
    DownloadFailed = "download.failed"

    # 种子搜索事件
    TorrentSearch = "torrent.search"
    TorrentSearchResult = "torrent.search_result"
    TorrentSearchFailed = "torrent.search_failed"

    # 转移事件
    TransferStarted = "transfer.started"
    TransferCompleted = "transfer.completed"
    TransferFailed = "transfer.failed"

    # 订阅事件
    SubscribeNewRelease = "subscribe.new_release"
    SubscribeChecked = "subscribe.checked"
    SubscribeComplete = "subscribe.complete"

    # 播放事件
    PlaybackStarted = "playback.started"
    PlaybackStopped = "playback.stopped"
    PlaybackPaused = "playback.paused"
    PlaybackResumed = "playback.resumed"
    PlaybackSkipped = "playback.skipped"

    # 媒体同步事件
    MediaSyncStarted = "media.sync_started"
    MediaSyncCompleted = "media.sync_completed"
    MediaSyncFailed = "media.sync_failed"

    # 系统事件
    SystemStarted = "system.started"
    SystemStopped = "system.stopped"
    SystemError = "system.error"

    # 消息渠道
    MessageChannelWeb = "web"
    MessageChannelTelegram = "telegram"
    MessageChannelSlack = "slack"


class EventManager:
    """
    事件管理器
    管理事件的发送和订阅
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self.logger = logger

    def register(self, event_type: str, handler: Callable):
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self._handlers[event_type].append(handler)
        self.logger.debug(f"注册事件处理器: {event_type}")

    def unregister(self, event_type: str, handler: Callable):
        """
        取消注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self.logger.debug(f"取消注册事件处理器: {event_type}")
            except ValueError:
                pass

    def send_event(self, event_type: str, data: dict[str, Any] | None = None):
        """
        发送事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self.logger.debug(f"发送事件: {event_type}, 数据: {data}")

        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    result = handler(data)
                    # 支持异步处理器
                    if hasattr(result, "__await__"):
                        asyncio.create_task(result)
                except Exception as e:
                    self.logger.error(f"事件处理器执行失败: {event_type}, 错误: {e}")

    def emit(self, event_type: str, data: dict[str, Any] | None = None):
        """
        发送事件（别名）

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self.send_event(event_type, data)

    def put_message(self, channel: str, title: str, content: str, **kwargs):
        """
        发送消息通知

        Args:
            channel: 消息渠道（web/telegram/slack）
            title: 消息标题
            content: 消息内容
            **kwargs: 其他参数
        """
        self.logger.info(f"发送消息: [{channel}] {title}: {content}")

        # 发送消息事件
        self.send_event(
            EventType.MessageChannelWeb,
            {"channel": channel, "title": title, "content": content, **kwargs},
        )


# 全局事件管理器实例
event_bus = EventManager()
