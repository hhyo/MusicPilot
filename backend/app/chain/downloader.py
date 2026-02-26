"""
下载器对接链
处理种子下载器的推送、监控和控制
"""
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.log import logger
from app.core.event import event_bus, EventType
from app.core.module import ModuleManager
from app.modules.downloader_module import DownloadTaskInfo, DownloadProgress
from app.db.operations.site import SiteOper
from app.db.models.site import Site
from app.db import db_manager


class DownloaderChain:
    """
    下载器对接链
    负责推送种子到下载器、监控下载进度、控制任务
    """

    def __init__(self):
        self.logger = logger
        self.site_oper = SiteOper(Site, db_manager)
        self.module_manager = ModuleManager()

    async def push_torrent(
        self,
        torrent_url: str,
        download_dir: str,
        site_name: str,
        downloader: str = "qbittorrent",
        paused: bool = False,
    ) -> str:
        """
        推送种子到下载器

        Args:
            torrent_url: 种子 URL
            download_dir: 下载目录
            site_name: 站点名称
            downloader: 下载器类型
            paused: 是否暂停

        Returns:
            下载器任务 ID
        """
        self.logger.info(f"推送种子: {torrent_url}, 下载器: {downloader}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            # 找到对应的下载器模块（通过下载器类型匹配）
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    # 推送种子
                    task_id = await module.add_torrent(torrent_url, download_dir, paused)

                    # 发送下载开始事件
                    await event_bus.emit(
                        EventType.DownloadStarted,
                        {
                            "task_id": task_id,
                            "torrent_url": torrent_url,
                            "download_dir": download_dir,
                            "site_name": site_name,
                            "downloader": downloader,
                        },
                    )

                    self.logger.info(f"种子推送成功，任务 ID: {task_id}")
                    return task_id
                except Exception as e:
                    self.logger.error(f"推送种子失败: {e}")
                    raise

        # 如果没有找到对应的下载器模块，抛出异常
        raise ValueError(f"未找到下载器 {downloader} 的模块")

    async def get_progress(self, task_id: str, downloader: str = "qbittorrent") -> Optional[DownloadProgress]:
        """
        获取下载进度

        Args:
            task_id: 任务 ID
            downloader: 下载器类型

        Returns:
            下载进度
        """
        self.logger.debug(f"获取下载进度: {task_id}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    progress = await module.get_task_progress(task_id)

                    # 发送下载进度事件
                    if progress:
                        await event_bus.emit(
                            EventType.DownloadProgress,
                            {
                                "task_id": task_id,
                                "downloader": downloader,
                                "progress": progress.__dict__,
                            },
                        )

                    return progress
                except Exception as e:
                    self.logger.error(f"获取下载进度失败: {e}")
                    raise

        # 如果没有找到对应的下载器模块，抛出异常
        raise ValueError(f"未找到下载器 {downloader} 的模块")

    async def pause_torrent(self, task_id: str, downloader: str = "qbittorrent") -> bool:
        """
        暂停下载

        Args:
            task_id: 任务 ID
            downloader: 下载器类型

        Returns:
            是否成功
        """
        self.logger.info(f"暂停下载: {task_id}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    success = await module.pause_torrent(task_id)
                    self.logger.info(f"暂停下载{'成功' if success else '失败'}: {task_id}")
                    return success
                except Exception as e:
                    self.logger.error(f"暂停下载失败: {e}")
                    raise

        # 如果没有找到对应的下载器模块，抛出异常
        raise ValueError(f"未找到下载器 {downloader} 的模块")

    async def resume_torrent(self, task_id: str, downloader: str = "qbittorrent") -> bool:
        """
        恢复下载

        Args:
            task_id: 任务 ID
            downloader: 下载器类型

        Returns:
            是否成功
        """
        self.logger.info(f"恢复下载: {task_id}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    success = await module.resume_torrent(task_id)
                    self.logger.info(f"恢复下载{'成功' if success else '失败'}: {task_id}")
                    return success
                except Exception as e:
                    self.logger.error(f"恢复下载失败: {e}")
                    raise

        # 如果没有找到对应的下载器模块，抛出异常
        raise ValueError(f"未找到下载器 {downloader} 的模块")

    async def remove_torrent(self, task_id: str, downloader: str = "qbittorrent", delete_files: bool = False) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID
            downloader: 下载器类型
            delete_files: 是否删除文件

        Returns:
            是否成功
        """
        self.logger.info(f"删除任务: {task_id}, 删除文件: {delete_files}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    success = await module.remove_torrent(task_id, delete_files)
                    self.logger.info(f"删除任务{'成功' if success else '失败'}: {task_id}")

                    # 发送下载完成事件
                    if delete_files:
                        await event_bus.emit(
                            EventType.DownloadCompleted,
                            {
                                "task_id": task_id,
                                "downloader": downloader,
                            },
                        )

                    return success
                except Exception as e:
                    self.logger.error(f"删除任务失败: {e}")
                    raise

        # 如果没有找到对应的下载器模块，抛出异常
        raise ValueError(f"未找到下载器 {downloader} 的模块")

    async def get_all_tasks(self, downloader: str = "qbittorrent") -> list[DownloadTaskInfo]:
        """
        获取所有任务

        Args:
            downloader: 下载器类型

        Returns:
            任务列表
        """
        self.logger.debug(f"获取所有任务: {downloader}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    tasks = await module.get_all_tasks()
                    return tasks
                except Exception as e:
                    self.logger.error(f"获取所有任务失败: {e}")
                    raise

        # 如果没有找到对应的下载器模块，抛出异常
        raise ValueError(f"未找到下载器 {downloader} 的模块")

    async def check_downloader_status(self, downloader: str = "qbittorrent") -> bool:
        """
        检查下载器状态

        Args:
            downloader: 下载器类型

        Returns:
            下载器是否可用
        """
        self.logger.info(f"检查下载器状态: {downloader}")

        # 获取下载器模块
        downloader_modules = self.module_manager.get_running_modules_by_type("downloader")

        for module in downloader_modules:
            if hasattr(module, "downloader_type") and module.downloader_type == downloader:
                try:
                    return await module.check_status()
                except Exception as e:
                    self.logger.error(f"检查下载器状态失败: {e}")
                    return False

        # 如果没有找到对应的下载器模块，返回 False
        return False