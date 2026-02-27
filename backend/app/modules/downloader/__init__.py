"""
下载器模块
"""

from .base import (
    DownloadStatus,
    DownloadQuality,
    DownloadSource,
    DownloadTask,
    DownloaderBase,
)

from .netease import NeteaseDownloader

__all__ = [
    "DownloadStatus",
    "DownloadQuality",
    "DownloadSource",
    "DownloadTask",
    "DownloaderBase",
    "NeteaseDownloader",
]
