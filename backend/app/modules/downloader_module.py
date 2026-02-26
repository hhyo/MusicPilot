"""
下载器模块基类
所有下载器模块都继承此类
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.core.module import ModuleBase
from app.core.log import logger
import httpx


class DownloadStatus(str, Enum):
    """下载状态"""
    DOWNLOADING = "downloading"
    SEEDING = "seeding"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class DownloadTaskInfo:
    """下载任务信息"""

    task_id: str
    name: str
    size: int
    downloaded: int
    uploaded: int
    download_speed: int
    upload_speed: int
    eta: int  # 预计剩余时间（秒）
    progress: float  # 进度百分比（0-100）
    status: DownloadStatus
    save_path: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "size": self.size,
            "downloaded": self.downloaded,
            "uploaded": self.uploaded,
            "download_speed": self.download_speed,
            "upload_speed": self.upload_speed,
            "eta": self.eta,
            "progress": self.progress,
            "status": self.status.value,
            "save_path": self.save_path,
        }


@dataclass
class DownloadProgress:
    """下载进度"""

    task_id: str
    progress: float  # 进度百分比（0-100）
    downloaded: int
    total: int
    download_speed: int
    eta: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "progress": self.progress,
            "downloaded": self.downloaded,
            "total": self.total,
            "download_speed": self.download_speed,
            "eta": self.eta,
        }


class DownloaderModule(ModuleBase):
    """
    下载器模块基类
    所有下载器模块都继承此类
    """

    module_type = "downloader"

    def __init__(self):
        super().__init__()
        self.downloader_type: str = ""
        self.base_url: str = ""
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.client: Optional[httpx.AsyncClient] = None

    def init_module(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化模块

        Args:
            config: 模块配置
        """
        super().init_module(config)

        if config:
            # 设置下载器类型
            self.downloader_type = config.get("type", "")
            self.base_url = config.get("url", "")
            self.username = config.get("username")
            self.password = config.get("password")

            # 创建 HTTP 客户端
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                auth=(self.username, self.password) if self.username and self.password else None,
            )

    def stop_module(self):
        """停止模块"""
        super().stop_module()

        # 关闭 HTTP 客户端
        if self.client:
            import asyncio
            try:
                asyncio.create_task(self.client.aclose())
            except Exception:
                pass

    async def add_torrent(self, torrent_url: str, save_path: str, paused: bool = False) -> str:
        """
        添加种子任务

        Args:
            torrent_url: 种子 URL
            save_path: 保存路径
            paused: 是否暂停

        Returns:
            任务 ID
        """
        self.logger.info(f"添加种子: {torrent_url}, 路径: {save_path}")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 add_torrent 方法")

    async def get_task_progress(self, task_id: str) -> Optional[DownloadProgress]:
        """
        获取任务进度

        Args:
            task_id: 任务 ID

        Returns:
            下载进度
        """
        self.logger.debug(f"获取任务进度: {task_id}")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 get_task_progress 方法")

    async def pause_torrent(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        self.logger.info(f"暂停任务: {task_id}")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 pause_torrent 方法")

    async def resume_torrent(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        self.logger.info(f"恢复任务: {task_id}")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 resume_torrent 方法")

    async def remove_torrent(self, task_id: str, delete_files: bool = False) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID
            delete_files: 是否删除文件

        Returns:
            是否成功
        """
        self.logger.info(f"删除任务: {task_id}, 删除文件: {delete_files}")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 remove_torrent 方法")

    async def get_all_tasks(self) -> List[DownloadTaskInfo]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        self.logger.debug("获取所有任务")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 get_all_tasks 方法")

    async def check_status(self) -> bool:
        """
        检查下载器状态

        Returns:
            下载器是否可用
        """
        self.logger.info(f"检查下载器状态: {self.downloader_type}")

        if not self.client:
            return False

        try:
            # 默认实现：尝试访问基础 URL
            response = await self.client.get("/")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"检查下载器状态失败: {e}")
            return False

    async def get_torrent_file(self, torrent_url: str) -> bytes:
        """
        获取种子文件

        Args:
            torrent_url: 种子 URL

        Returns:
            种子文件内容
        """
        self.logger.debug(f"获取种子文件: {torrent_url}")

        if not self.client:
            raise ValueError("HTTP 客户端未初始化")

        response = await self.client.get(torrent_url)
        response.raise_for_status()
        return response.content