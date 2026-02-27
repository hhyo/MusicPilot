"""
qBittorrent 下载器模块
支持 qBittorrent 4.1+ API
"""

from typing import Optional, List
import hashlib

from app.modules.downloader_module import (
    DownloaderModule,
    DownloadTaskInfo,
    DownloadProgress,
    DownloadStatus,
)
from app.core.log import logger
from app.core.context import DownloadContext


class QbittorrentModule(DownloaderModule):
    """
    qBittorrent 下载器模块
    """

    module_type = "qbittorrent"

    def __init__(self):
        super().__init__()
        self.downloader_type = "qbittorrent"
        self._api_base = "/api/v2"
        self._sid = None  # Session ID

    async def _login(self) -> bool:
        """
        登录 qBittorrent

        Returns:
            是否登录成功
        """
        self.logger.info(f"登录 qBittorrent: {self.base_url}")

        if not self.client:
            return False

        try:
            # 调用登录 API
            response = await self.client.post(
                f"{self._api_base}/auth/login",
                data={
                    "username": self.username,
                    "password": self.password,
                },
            )
            response.raise_for_status()

            # 保存 Session ID
            self._sid = response.cookies.get("SID")
            self.logger.info(f"qBittorrent 登录成功，SID: {self._sid}")

            return True
        except Exception as e:
            self.logger.error(f"qBittorrent 登录失败: {e}")
            return False

    async def _api_request(
        self, method: str, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None
    ) -> dict:
        """
        发送 API 请求

        Args:
            method: HTTP 方法（GET/POST）
            endpoint: API 端点
            data: POST 数据
            params: GET 参数

        Returns:
            API 响应
        """
        url = f"{self._api_base}{endpoint}"

        if method == "GET":
            response = await self.client.get(url, params=params)
        elif method == "POST":
            response = await self.client.post(url, data=data)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")

        response.raise_for_status()
        return response.json()

    async def add_torrent(self, torrent_url: str, save_path: str, paused: bool = False) -> str:
        """
        添加种子任务

        Args:
            torrent_url: 种子 URL
            save_path: 保存路径
            paused: 是否暂停

        Returns:
            任务 ID（qBittorrent 使用 hash）
        """
        self.logger.info(f"添加种子: {torrent_url}, 路径: {save_path}")

        # 确保已登录
        if not self._sid:
            if not await self._login():
                raise ValueError("qBittorrent 登录失败")

        try:
            # 调用添加种子 API
            response_data = await self._api_request(
                "POST",
                "/torrents/add",
                data={
                    "urls": torrent_url,
                    "savepath": save_path,
                    "paused": paused,
                },
            )

            # 获取种子信息（获取 hash）
            torrents = await self._api_request("GET", "/torrents/info")
            if torrents:
                # 返回最后一个添加的种子的 hash
                return torrents[-1].get("hash", "")

            raise ValueError("添加种子失败")
        except Exception as e:
            self.logger.error(f"添加种子失败: {e}")
            raise

    async def get_task_progress(self, task_id: str) -> Optional[DownloadProgress]:
        """
        获取任务进度

        Args:
            task_id: 任务 ID（hash）

        Returns:
            下载进度
        """
        self.logger.debug(f"获取任务进度: {task_id}")

        try:
            # 获取种子信息
            torrents = await self._api_request("GET", "/torrents/info", params={"hashes": task_id})

            if not torrents:
                return None

            torrent = torrents[0]

            # 映射状态
            status_map = {
                "downloading": DownloadStatus.DOWNLOADING,
                "seeding": DownloadStatus.SEEDING,
                "completed": DownloadStatus.COMPLETED,
                "paused": DownloadStatus.PAUSED,
                "error": DownloadStatus.ERROR,
            }

            return DownloadProgress(
                task_id=task_id,
                progress=torrent.get("progress", 0) * 100,
                downloaded=torrent.get("downloaded", 0),
                total=torrent.get("size", 0),
                download_speed=torrent.get("dl_speed", 0),
                eta=torrent.get("eta", 0) if torrent.get("eta") not in [-1, -2] else None,
            )
        except Exception as e:
            self.logger.error(f"获取任务进度失败: {e}")
            return None

    async def pause_torrent(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务 ID（hash）

        Returns:
            是否成功
        """
        self.logger.info(f"暂停任务: {task_id}")

        try:
            await self._api_request("POST", "/torrents/pause", data={"hashes": task_id})
            return True
        except Exception as e:
            self.logger.error(f"暂停任务失败: {e}")
            return False

    async def resume_torrent(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务 ID（hash）

        Returns:
            是否成功
        """
        self.logger.info(f"恢复任务: {task_id}")

        try:
            await self._api_request("POST", "/torrents/resume", data={"hashes": task_id})
            return True
        except Exception as e:
            self.logger.error(f"恢复任务失败: {e}")
            return False

    async def remove_torrent(self, task_id: str, delete_files: bool = False) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID（hash）
            delete_files: 是否删除文件

        Returns:
            是否成功
        """
        self.logger.info(f"删除任务: {task_id}, 删除文件: {delete_files}")

        try:
            endpoint = "/torrents/delete" if delete_files else "/torrents/delete"
            await self._api_request(
                "POST",
                endpoint,
                data={
                    "hashes": task_id,
                    "deleteFiles": delete_files,
                },
            )
            return True
        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            return False

    async def get_all_tasks(self) -> List[DownloadTaskInfo]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        self.logger.debug("获取所有任务")

        try:
            # 获取种子列表
            torrents = await self._api_request("GET", "/torrents/info")

            # 映射状态
            status_map = {
                "downloading": DownloadStatus.DOWNLOADING,
                "seeding": DownloadStatus.SEEDING,
                "completed": DownloadStatus.COMPLETED,
                "paused": DownloadStatus.PAUSED,
                "error": DownloadStatus.ERROR,
            }

            tasks = []
            for torrent in torrents:
                tasks.append(
                    DownloadTaskInfo(
                        task_id=torrent.get("hash", ""),
                        name=torrent.get("name", ""),
                        size=torrent.get("size", 0),
                        downloaded=torrent.get("downloaded", 0),
                        uploaded=torrent.get("uploaded", 0),
                        download_speed=torrent.get("dl_speed", 0),
                        upload_speed=torrent.get("up_speed", 0),
                        eta=torrent.get("eta", 0) if torrent.get("eta") not in [-1, -2] else 0,
                        progress=torrent.get("progress", 0) * 100,
                        status=status_map.get(torrent.get("state", "error"), DownloadStatus.ERROR),
                        save_path=torrent.get("save_path", ""),
                    )
                )

            return tasks
        except Exception as e:
            self.logger.error(f"获取所有任务失败: {e}")
            return []

    async def check_status(self) -> bool:
        """
        检查下载器状态

        Returns:
            下载器是否可用
        """
        self.logger.info(f"检查 qBittorrent 状态")

        try:
            # 尝试登录
            return await self._login()
        except Exception as e:
            self.logger.error(f"检查 qBittorrent 状态失败: {e}")
            return False
