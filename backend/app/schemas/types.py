"""
类型枚举
定义所有枚举类型
"""

from enum import Enum


class EventType(str, Enum):
    """事件类型枚举"""

    # 元数据事件
    METADATA_RECOGNIZED = "metadata.recognized"
    METADATA_COMPLETED = "metadata.completed"
    METADATA_FAILED = "metadata.failed"

    # 下载事件
    DOWNLOAD_STARTED = "download.started"
    DOWNLOAD_PROGRESS = "download.progress"
    DOWNLOAD_COMPLETED = "download.completed"
    DOWNLOAD_FAILED = "download.failed"

    # 转移事件
    TRANSFER_STARTED = "transfer.started"
    TRANSFER_COMPLETED = "transfer.completed"
    TRANSFER_FAILED = "transfer.failed"

    # 订阅事件
    SUBSCRIBE_NEW_RELEASE = "subscribe.new_release"
    SUBSCRIBE_CHECKED = "subscribe.checked"
    SUBSCRIBE_COMPLETE = "subscribe.complete"

    # 播放事件
    PLAYBACK_STARTED = "playback.started"
    PLAYBACK_STOPPED = "playback.stopped"
    PLAYBACK_PAUSED = "playback.paused"
    PLAYBACK_RESUMED = "playback.resumed"
    PLAYBACK_SKIPPED = "playback.skipped"

    # 媒体同步事件
    MEDIA_SYNC_STARTED = "media.sync_started"
    MEDIA_SYNC_COMPLETED = "media.sync_completed"
    MEDIA_SYNC_FAILED = "media.sync_failed"

    # 系统事件
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"


class DownloadStatus(str, Enum):
    """下载状态枚举"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MediaType(str, Enum):
    """媒体类型枚举"""

    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class PlaylistType(str, Enum):
    """播放列表类型枚举"""

    NORMAL = "normal"
    SMART = "smart"


class DownloaderType(str, Enum):
    """下载器类型枚举"""

    NETEASE = "netease"
    QQ = "qq"
    KUGOU = "kugou"
    KUWO = "kuwo"
    GENERIC = "generic"


class MediaServerType(str, Enum):
    """媒体服务器类型枚举"""

    PLEX = "plex"
    JELLYFIN = "jellyfin"
    EMBY = "emby"


class MessageChannel(str, Enum):
    """消息渠道枚举"""

    WEB = "web"
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"


class NotificationType(str, Enum):
    """通知类型枚举"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
