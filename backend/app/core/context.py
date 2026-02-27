"""
上下文数据类
定义常用的数据类和上下文对象
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MediaType(StrEnum):
    """媒体类型"""

    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class DownloadStatus(StrEnum):
    """下载状态"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloaderType(StrEnum):
    """下载器类型"""

    NETEASE = "netease"
    QQ = "qq"
    KUGOU = "kugou"
    KUWO = "kuwo"
    GENERIC = "generic"


class MediaServerType(StrEnum):
    """媒体服务器类型"""

    PLEX = "plex"
    JELLYFIN = "jellyfin"
    EMBY = "emby"


class MessageChannel(StrEnum):
    """消息渠道"""

    WEB = "web"
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"


class PlaylistType(StrEnum):
    """播放列表类型"""

    NORMAL = "normal"  # 普通播放列表
    SMART = "smart"  # 智能播放列表


class NotificationType(StrEnum):
    """通知类型"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class MusicInfo:
    """
    音乐信息数据类
    """

    # 艺术家信息
    artist: str | None = None
    artist_id: str | None = None

    # 专辑信息
    album: str | None = None
    album_id: str | None = None

    # 曲目信息
    title: str | None = None
    track_id: str | None = None

    # 音频信息
    duration: int | None = None
    track_number: int | None = None
    disc_number: int | None = None

    # 文件信息
    path: str | None = None
    file_format: str | None = None
    file_size: int | None = None
    bitrate: int | None = None

    # 元数据
    genres: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    year: int | None = None
    cover_url: str | None = None

    # MusicBrainz 信息
    musicbrainz_artist_id: str | None = None
    musicbrainz_album_id: str | None = None
    musicbrainz_track_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "artist": self.artist,
            "artist_id": self.artist_id,
            "album": self.album,
            "album_id": self.album_id,
            "title": self.title,
            "track_id": self.track_id,
            "duration": self.duration,
            "track_number": self.track_number,
            "disc_number": self.disc_number,
            "path": self.path,
            "file_format": self.file_format,
            "file_size": self.file_size,
            "bitrate": self.bitrate,
            "genres": self.genres,
            "tags": self.tags,
            "year": self.year,
            "cover_url": self.cover_url,
            "musicbrainz_artist_id": self.musicbrainz_artist_id,
            "musicbrainz_album_id": self.musicbrainz_album_id,
            "musicbrainz_track_id": self.musicbrainz_track_id,
        }


@dataclass
class DownloadSource:
    """
    下载源数据类
    """

    # 来源类型
    type: DownloaderType = DownloaderType.NETEASE

    # 音乐信息
    artist: str | None = None
    album: str | None = None
    title: str | None = None

    # 来源 ID
    source_id: str | None = None

    # URL
    url: str | None = None

    # 音质
    quality: str | None = None

    # 扩展信息
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DownloadTask:
    """
    下载任务数据类
    """

    # 任务 ID
    task_id: str

    # 下载源
    source: DownloadSource

    # 下载状态
    status: DownloadStatus = DownloadStatus.PENDING

    # 进度
    progress: float = 0.0  # 0.0 - 1.0

    # 下载速度（字节/秒）
    speed: float | None = None

    # 已下载大小
    downloaded_size: int = 0

    # 总大小
    total_size: int | None = None

    # 保存路径
    save_path: str | None = None

    # 错误信息
    error_message: str | None = None

    # 重试次数
    retry_count: int = 0


@dataclass
class PlaybackSession:
    """
    播放会话数据类
    """

    # 会话 ID
    session_id: str

    # 曲目 ID
    track_id: str

    # 用户 ID
    user_id: str | None = None

    # 播放位置（秒）
    position: float = 0.0

    # 总时长（秒）
    duration: float | None = None

    # 音量
    volume: float = 1.0

    # 是否静音
    muted: bool = False

    # 播放模式
    repeat_mode: str = "off"  # off, one, all

    # 是否随机
    shuffle: bool = False

    # 开始时间
    started_at: str | None = None


@dataclass
class SmartQuery:
    """
    智能查询数据类
    用于智能播放列表
    """

    # 条件列表
    conditions: list[dict[str, Any]] = field(default_factory=list)

    # 逻辑运算符（AND/OR）
    operator: str = "AND"

    # 排序字段
    sort_by: str | None = None

    # 排序方向（ASC/DESC）
    sort_order: str = "ASC"

    # 限制数量
    limit: int | None = None

    # 查询描述
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "conditions": self.conditions,
            "operator": self.operator,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "limit": self.limit,
            "description": self.description,
        }


@dataclass
class Context:
    """
    应用上下文数据类
    存储全局上下文信息
    """

    # 当前用户
    user_id: str | None = None

    # 请求 ID
    request_id: str | None = None

    # 客户端信息
    client_ip: str | None = None
    user_agent: str | None = None

    # 时间戳
    timestamp: str | None = None

    # 额外数据
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp,
            "extra": self.extra,
        }
