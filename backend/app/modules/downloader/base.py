"""
下载器基类
定义下载器接口
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum

from app.core.module import ModuleBase


class DownloadStatus(StrEnum):
    """下载状态"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class DownloadTask:
    """下载任务"""

    def __init__(
        self,
        url: str,
        output_path: str,
        filename: str | None = None,
        headers: dict | None = None,
        **kwargs,
    ):
        self.url = url
        self.output_path = output_path
        self.filename = filename
        self.headers = headers or {}
        self.extra = kwargs


class DownloaderBase(ModuleBase, ABC):
    """
    下载器基类
    所有下载器都需要继承此类并实现相关方法
    """

    @abstractmethod
    async def download(self, task: DownloadTask, progress_callback: Callable | None = None) -> bool:
        """
        执行下载任务

        Args:
            task: 下载任务
            progress_callback: 进度回调函数

        Returns:
            下载是否成功
        """
        pass

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """
        取消下载任务

        Args:
            task_id: 任务ID

        Returns:
            取消是否成功
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> DownloadStatus | None:
        """
        获取下载任务状态

        Args:
            task_id: 任务ID

        Returns:
            下载状态
        """
        pass
