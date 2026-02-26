"""
上下文数据类
定义常用的数据类和上下文对象
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class MediaType(str, Enum):
    """媒体类型"""
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


class DownloadStatus(str, Enum):
    """下载状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloaderType(str, Enum):
    """下载器类型"""
    NETEASE = "netease"
    QQ = "qq"
    KUGOU = "kugou"
    KUWO = "kuwo"
    GENERIC = "generic"


class MediaServerType(str, Enum):
    """媒体服务器类型"""
    PLEX = "plex"
    JELLYFIN = "jellyfin"
    EMBY = "emby"


class MessageChannel(str, Enum):
    """消息渠道"""
    WEB = "web"
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"


class PlaylistType(str, Enum):
    """播放列表类型"""
    NORMAL = "normal"  # 普通播放列表
    SMART = "smart"    # 智能播放列表


class NotificationType(str, Enum):
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
    artist: Optional[str] = None
    artist_id: Optional[str] = None

    # 专辑信息
    album: Optional[str] = None
    album_id: Optional[str] = None

    # 曲目信息
    title: Optional[str] = None
    track_id: Optional[str] = None

    # 音频信息
    duration: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None

    # 文件信息
    path: Optional[str] = None
    file_format: Optional[str] = None
    file_size: Optional[int] = None
    bitrate: Optional[int] = None

    # 元数据
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    year: Optional[int] = None
    cover_url: Optional[str] = None

    # MusicBrainz 信息
    musicbrainz_artist_id: Optional[str] = None
    musicbrainz_album_id: Optional[str] = None
    musicbrainz_track_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
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
    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None

    # 来源 ID
    source_id: Optional[str] = None

    # URL
    url: Optional[str] = None

    # 音质
    quality: Optional[str] = None

    # 扩展信息
    extra: Dict[str, Any] = field(default_factory=dict)


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
    speed: Optional[float] = None

    # 已下载大小
    downloaded_size: int = 0

    # 总大小
    total_size: Optional[int] = None

    # 保存路径
    save_path: Optional[str] = None

    # 错误信息
    error_message: Optional[str] = None

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
    user_id: Optional[str] = None

    # 播放位置（秒）
    position: float = 0.0

    # 总时长（秒）
    duration: Optional[float] = None

    # 音量
    volume: float = 1.0

    # 是否静音
    muted: bool = False

    # 播放模式
    repeat_mode: str = "off"  # off, one, all

    # 是否随机
    shuffle: bool = False

    # 开始时间
    started_at: Optional[str] = None


@dataclass
class SmartQuery:
    """
    智能查询数据类
    用于智能播放列表
    """
    # 条件列表
    conditions: List[Dict[str, Any]] = field(default_factory=list)

    # 逻辑运算符（AND/OR）
    operator: str = "AND"

    # 排序字段
    sort_by: Optional[str] = None

    # 排序方向（ASC/DESC）
    sort_order: str = "ASC"

    # 限制数量
    limit: Optional[int] = None

    # 查询描述
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
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
    user_id: Optional[str] = None

    # 请求 ID
    request_id: Optional[str] = None

    # 客户端信息
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    # 时间戳
    timestamp: Optional[str] = None

    # 额外数据
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp,
            "extra": self.extra,
        }