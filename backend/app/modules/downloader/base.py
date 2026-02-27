"""
下载器基类
定义下载器接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum

from app.core.module import ModuleBase


class DownloadStatus(str, Enum):
    """下载状态"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DownloadQuality(str, Enum):
    """下载质量"""

    LOSSLESS = "lossless"  # 无损 (FLAC)
    HIGH = "high"  # 高品质 (320kbps MP3)
    STANDARD = "standard"  # 标准 (128kbps MP3)
    LOW = "low"  # 低品质 (64kbps MP3)


class DownloadSource(str, Enum):
    """下载来源"""

    NETEASE = "netease"
    QQ = "qq"
    KUGOU = "kugou"
    KUWO = "kuwo"
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    CUSTOM = "custom"


class DownloadTask:
    """
    下载任务数据类
    """

    def __init__(
        self,
        task_id: str,
        url: str,
        source: DownloadSource,
        quality: DownloadQuality = DownloadQuality.STANDARD,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        title: Optional[str] = None,
        target_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.url = url
        self.source = source
        self.quality = quality
        self.artist = artist
        self.album = album
        self.title = title
        self.target_path = target_path
        self.metadata = metadata or {}
        self.status = DownloadStatus.PENDING
        self.progress = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.error_message: Optional[str] = None
        self.file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "url": self.url,
            "source": self.source.value,
            "quality": self.quality.value,
            "artist": self.artist,
            "album": self.album,
            "title": self.title,
            "target_path": self.target_path,
            "status": self.status.value,
            "progress": self.progress,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "error_message": self.error_message,
            "file_path": self.file_path,
        }


class DownloaderBase(ModuleBase, ABC):
    """
    下载器基类

    所有下载器必须继承此类并实现抽象方法
    继承自 ModuleBase 以支持模块管理
    """

    def __init__(self):
        super().__init__()
        self.module_type = "downloader"
        self.source: DownloadSource = DownloadSource.CUSTOM
        self.supported_qualities: list[DownloadQuality] = []
        self.config: Dict[str, Any] = {}

    @abstractmethod
    async def search(
        self, keyword: str, limit: int = 20, quality: Optional[DownloadQuality] = None
    ) -> list[DownloadTask]:
        """
        搜索音乐

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            quality: 目标质量

        Returns:
            下载任务列表
        """
        pass

    @abstractmethod
    async def download(
        self, task: DownloadTask, progress_callback: Optional[callable] = None
    ) -> DownloadTask:
        """
        下载音乐

        Args:
            task: 下载任务
            progress_callback: 进度回调函数

        Returns:
            完成的下载任务
        """
        pass

    @abstractmethod
    async def get_url(self, url: str, quality: DownloadQuality = DownloadQuality.STANDARD) -> str:
        """
        获取实际下载 URL

        Args:
            url: 原始 URL 或 ID
            quality: 目标质量

        Returns:
            实际下载 URL
        """
        pass

    @abstractmethod
    async def test(self) -> Tuple[bool, str]:
        """
        测试下载器连接

        Returns:
            (是否可用, 错误信息)
        """
        pass

    def get_type(self) -> DownloadSource:
        """
        获取下载器类型

        Returns:
            下载器类型
        """
        return self.source

    def init_setting(self) -> Optional[Tuple[str, bool]]:
        """
        初始化下载器设置

        Returns:
            (字段定义, 是否必需) 或 None
        """
        return None

    def supports_quality(self, quality: DownloadQuality) -> bool:
        """
        检查是否支持指定质量

        Args:
            quality: 下载质量

        Returns:
            是否支持
        """
        return quality in self.supported_qualities

    def get_supported_qualities(self) -> list[DownloadQuality]:
        """获取支持的质量列表"""
        return self.supported_qualities
