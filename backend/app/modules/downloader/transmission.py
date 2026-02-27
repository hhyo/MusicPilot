"""
Transmission 下载器模块
支持 Transmission RPC 2.0+
"""

from typing import Optional, List
import base64

from app.modules.downloader_module import (
    DownloaderModule,
    DownloadTaskInfo,
    DownloadProgress,
    DownloadStatus,
)
from app.core.log import logger


class TransmissionModule(DownloaderModule):
    """
    Transmission 下载器模块
    """

    module_type = "transmission"

    def __init__(self):
        super().__init__()
        self.downloader_type = "transmission"
        self._rpc_path = "/transmission/rpc"
        self._session_id = None  # Session ID

    async def _get_session_id(self) -> str:
        """
        获取 Session ID

        Returns:
            Session ID
        """
        if not self.client:
            raise ValueError("HTTP 客户端未初始化")

        # 尝试调用 API
        response = await self.client.post(
            self._rpc_path,
            json={"method": "session-get"},
        )

        # 如果返回 409，需要先获取 Session ID
        if response.status_code == 409:
            self._session_id = response.headers.get("X-Transmission-Session-Id")
            return self._session_id

        # 返回成功的响应中的 session_id
        data = response.json()
        return data.get("arguments", {}).get("session-id", "")

    async def _api_request(self, method: str, arguments: dict) -> dict:
        """
        发送 RPC 请求

        Args:
            method: RPC 方法名
            arguments: 参数

        Returns:
            API 响应
        """
        # 获取 Session ID
        if not self._session_id:
            self._session_id = await self._get_session_id()

        # 发送请求
        headers = {}
        if self._session_id:
            headers["X-Transmission-Session-Id"] = self._session_id

        response = await self.client.post(
            self._rpc_path,
            headers=headers,
            json={
                "method": method,
                "arguments": arguments,
            },
        )

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
            任务 ID（Transmission 使用 id）
        """
        self.logger.info(f"添加种子: {torrent_url}, 路径: {save_path}")

        try:
            # 调用添加种子 API
            response_data = await self._api_request(
                "torrent-add",
                {
                    "filename": torrent_url,
                    "download-dir": save_path,
                    "paused": paused,
                },
            )

            # 获取添加的种子 ID
            torrent_data = response_data.get("arguments", {})
            if "torrent-added" in torrent_data:
                return str(torrent_data["torrent-added"].get("id", 0))
            elif "torrent-duplicate" in torrent_data:
                return str(torrent_data["torrent-duplicate"].get("id", 0))

            raise ValueError("添加种子失败")
        except Exception as e:
            self.logger.error(f"添加种子失败: {e}")
            raise

    async def get_task_progress(self, task_id: str) -> Optional[DownloadProgress]:
        """
        获取任务进度

        Args:
            task_id: 任务 ID（id）

        Returns:
            下载进度
        """
        self.logger.debug(f"获取任务进度: {task_id}")

        try:
            # 获取种子信息
            response_data = await self._api_request(
                "torrent-get",
                {
                    "fields": [
                        "id",
                        "name",
                        "sizeWhenDone",
                        "downloadedEver",
                        "eta",
                        "rateDownload",
                    ],
                    "ids": int(task_id),
                },
            )

            torrents = response_data.get("arguments", {}).get("torrents", [])
            if not torrents:
                return None

            torrent = torrents[0]

            # 计算进度
            size_when_done = torrent.get("sizeWhenDone", 0)
            downloaded_ever = torrent.get("downloadedEver", 0)
            progress = (downloaded_ever / size_when_done * 100) if size_when_done > 0 else 0

            # 映射状态（Transmission 使用不同的状态码）
            status_code = torrent.get("status", 0)
            if status_code == 0:  # stopped
                status = DownloadStatus.PAUSED
            elif status_code in [1, 2, 3, 4, 5]:  # download/check/wait
                status = DownloadStatus.DOWNLOADING
            elif status_code == 6:  # seed
                status = DownloadStatus.SEEDING
            else:
                status = DownloadStatus.ERROR

            return DownloadProgress(
                task_id=task_id,
                progress=progress,
                downloaded=downloaded_ever,
                total=size_when_done,
                download_speed=torrent.get("rateDownload", 0),
                eta=torrent.get("eta", -1) if torrent.get("eta", -1) >= 0 else None,
            )
        except Exception as e:
            self.logger.error(f"获取任务进度失败: {e}")
            return None

    async def pause_torrent(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务 ID（id）

        Returns:
            是否成功
        """
        self.logger.info(f"暂停任务: {task_id}")

        try:
            await self._api_request(
                "torrent-stop",
                {"ids": [int(task_id)]},
            )
            return True
        except Exception as e:
            self.logger.error(f"暂停任务失败: {e}")
            return False

    async def resume_torrent(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务 ID（id）

        Returns:
            是否成功
        """
        self.logger.info(f"恢复任务: {task_id}")

        try:
            await self._api_request(
                "torrent-start",
                {"ids": [int(task_id)]},
            )
            return True
        except Exception as e:
            self.logger.error(f"恢复任务失败: {e}")
            return False

    async def remove_torrent(self, task_id: str, delete_files: bool = False) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID（id）
            delete_files: 是否删除文件

        Returns:
            是否成功
        """
        self.logger.info(f"删除任务: {task_id}, 删除文件: {delete_files}")

        try:
            method = "torrent-remove" if delete_files else "torrent-remove"
            await self._api_request(
                method,
                {
                    "ids": [int(task_id)],
                    "delete-local-data": delete_files,
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
            response_data = await self._api_request(
                "torrent-get",
                {
                    "fields": [
                        "id",
                        "name",
                        "totalSize",
                        "downloadedEver",
                        "uploadedEver",
                        "rateDownload",
                        "rateUpload",
                        "eta",
                        "percentDone",
                        "status",
                        "downloadDir",
                    ],
                },
            )

            torrents = response_data.get("arguments", {}).get("torrents", [])

            tasks = []
            for torrent in torrents:
                # 映射状态
                status_code = torrent.get("status", 0)
                if status_code == 0:  # stopped
                    status = DownloadStatus.PAUSED
                elif status_code in [1, 2, 3, 4, 5]:  # download/check/wait
                    status = DownloadStatus.DOWNLOADING
                elif status_code == 6:  # seed
                    status = DownloadStatus.SEEDING
                else:
                    status = DownloadStatus.ERROR

                tasks.append(
                    DownloadTaskInfo(
                        task_id=str(torrent.get("id", 0)),
                        name=torrent.get("name", ""),
                        size=torrent.get("totalSize", 0),
                        downloaded=torrent.get("downloadedEver", 0),
                        uploaded=torrent.get("uploadedEver", 0),
                        download_speed=torrent.get("rateDownload", 0),
                        upload_speed=torrent.get("rateUpload", 0),
                        eta=torrent.get("eta", -1) if torrent.get("eta", -1) >= 0 else 0,
                        progress=torrent.get("percentDone", 0) * 100,
                        status=status,
                        save_path=torrent.get("downloadDir", ""),
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
        self.logger.info(f"检查 Transmission 状态")

        try:
            # 尝试获取 Session ID
            await self._get_session_id()
            return True
        except Exception as e:
            self.logger.error(f"检查 Transmission 状态失败: {e}")
            return False
