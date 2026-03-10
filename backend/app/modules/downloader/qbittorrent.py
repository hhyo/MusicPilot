"""
qBittorrent 下载器模块
支持 qBittorrent 4.1+ API

参考实现: MoviePilot app/modules/qbittorrent/
"""

from typing import Any

from app.modules.downloader_module import (
    DownloaderModule,
    DownloadProgress,
    DownloadStatus,
    DownloadTaskInfo,
)


class QbittorrentModule(DownloaderModule):
    """
    qBittorrent 下载器模块

    支持功能：
    - 添加种子（URL 或文件）
    - 标签管理
    - 文件选择
    - 速度统计
    - 已完成任务查询
    """

    module_type = "qbittorrent"

    def __init__(self):
        super().__init__()
        self.downloader_type = "qbittorrent"
        self._api_base = "/api/v2"
        self._sid: str | None = None  # Session ID
        self._default_tag: str = "musicpilot"  # 默认标签，用于识别 MusicPilot 任务

    # ========== 认证 ==========

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
            response = await self.client.post(
                f"{self._api_base}/auth/login",
                data={
                    "username": self.username or "",
                    "password": self.password or "",
                },
            )
            response.raise_for_status()

            # 保存 Session ID
            self._sid = response.cookies.get("SID")
            self.logger.info("qBittorrent 登录成功")
            return True
        except Exception as e:
            self.logger.error(f"qBittorrent 登录失败: {e}")
            return False

    async def _ensure_login(self) -> bool:
        """确保已登录"""
        if not self._sid:
            return await self._login()
        return True

    # ========== API 请求封装 ==========

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        files: dict | None = None,
    ) -> dict | list:
        """
        发送 API 请求

        Args:
            method: HTTP 方法（GET/POST）
            endpoint: API 端点
            data: POST 数据
            params: GET 参数
            files: 上传文件

        Returns:
            API 响应
        """
        if not await self._ensure_login():
            raise ValueError("qBittorrent 未登录")

        url = f"{self._api_base}{endpoint}"

        if method == "GET":
            response = await self.client.get(url, params=params)
        elif method == "POST":
            if files:
                response = await self.client.post(url, data=data, files=files)
            else:
                response = await self.client.post(url, data=data)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")

        response.raise_for_status()

        # 有些 API 返回空字符串
        text = response.text.strip()
        if not text:
            return {}

        return response.json()

    # ========== 基本操作 ==========

    async def add_torrent(
        self,
        torrent_url: str | None = None,
        torrent_file: bytes | None = None,
        save_path: str = "",
        paused: bool = False,
        tags: list[str] | None = None,
        category: str | None = None,
        cookie: str | None = None,
    ) -> str:
        """
        添加种子任务

        Args:
            torrent_url: 种子 URL 或磁力链接
            torrent_file: 种子文件内容（二选一）
            save_path: 保存路径
            paused: 是否暂停
            tags: 标签列表
            category: 分类
            cookie: Cookie（用于下载种子）

        Returns:
            任务 ID（hash）
        """
        self.logger.info(f"添加种子: URL={torrent_url}, 路径={save_path}")

        if not torrent_url and not torrent_file:
            raise ValueError("必须提供 torrent_url 或 torrent_file")

        try:
            # 构建请求数据
            data: dict[str, Any] = {
                "savepath": save_path,
                "paused": "true" if paused else "false",
            }

            # 添加默认标签
            all_tags = [self._default_tag]
            if tags:
                all_tags.extend(tags)
            data["tags"] = ",".join(all_tags)

            # 添加分类
            if category:
                data["category"] = category

            # 添加 Cookie
            if cookie:
                data["cookie"] = cookie

            files = None
            if torrent_file:
                # 上传种子文件
                files = {"torrents": ("torrent.torrent", torrent_file)}
            else:
                # 使用 URL
                data["urls"] = torrent_url

            # 调用添加种子 API
            await self._api_request("POST", "/torrents/add", data=data, files=files)

            # 获取刚添加的种子 hash
            # qBittorrent API 不直接返回 hash，需要通过标签查询
            torrent_hash = await self._get_torrent_id_by_tag(all_tags)

            if torrent_hash:
                self.logger.info(f"添加种子成功: {torrent_hash}")
                return torrent_hash
            else:
                raise ValueError("添加种子失败：无法获取种子 hash")

        except Exception as e:
            self.logger.error(f"添加种子失败: {e}")
            raise

    async def _get_torrent_id_by_tag(self, tags: list[str], retries: int = 5) -> str | None:
        """
        通过标签获取刚添加的种子 ID

        Args:
            tags: 标签列表
            retries: 重试次数

        Returns:
            种子 hash
        """
        import asyncio

        for _ in range(retries):
            await asyncio.sleep(1)
            torrents = await self._api_request(
                "GET", "/torrents/info", params={"tag": ",".join(tags)}
            )
            if torrents:
                torrent = torrents[0]
                # 移除临时标签，保留默认标签
                await self.remove_torrent_tags(torrent["hash"], tags)
                await self.set_torrent_tags(torrent["hash"], [self._default_tag])
                return torrent["hash"]

        return None

    async def get_task_progress(self, task_id: str) -> DownloadProgress | None:
        """获取任务进度"""
        try:
            torrents = await self._api_request("GET", "/torrents/info", params={"hashes": task_id})

            if not torrents:
                return None

            torrent = torrents[0]

            return DownloadProgress(
                task_id=task_id,
                progress=torrent.get("progress", 0) * 100,
                downloaded=torrent.get("downloaded", 0),
                total=torrent.get("size", 0),
                download_speed=torrent.get("dlspeed", 0),
                eta=torrent.get("eta", 0) if torrent.get("eta", -1) >= 0 else None,
            )
        except Exception as e:
            self.logger.error(f"获取任务进度失败: {e}")
            return None

    async def pause_torrent(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            await self._api_request("POST", "/torrents/pause", data={"hashes": task_id})
            return True
        except Exception as e:
            self.logger.error(f"暂停任务失败: {e}")
            return False

    async def resume_torrent(self, task_id: str) -> bool:
        """恢复任务"""
        try:
            await self._api_request("POST", "/torrents/resume", data={"hashes": task_id})
            return True
        except Exception as e:
            self.logger.error(f"恢复任务失败: {e}")
            return False

    async def remove_torrent(self, task_id: str, delete_files: bool = False) -> bool:
        """删除任务"""
        try:
            await self._api_request(
                "POST",
                "/torrents/delete",
                data={"hashes": task_id, "deleteFiles": "true" if delete_files else "false"},
            )
            return True
        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            return False

    async def get_all_tasks(self) -> list[DownloadTaskInfo]:
        """获取所有任务"""
        try:
            torrents = await self._api_request("GET", "/torrents/info")

            status_map = {
                "downloading": DownloadStatus.DOWNLOADING,
                "stalledDL": DownloadStatus.DOWNLOADING,
                "seeding": DownloadStatus.SEEDING,
                "stalledUP": DownloadStatus.SEEDING,
                "completed": DownloadStatus.COMPLETED,
                "pausedDL": DownloadStatus.PAUSED,
                "pausedUP": DownloadStatus.PAUSED,
                "error": DownloadStatus.ERROR,
                "missingFiles": DownloadStatus.ERROR,
            }

            tasks = []
            for torrent in torrents:
                state = torrent.get("state", "error")
                tags_str = torrent.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

                tasks.append(
                    DownloadTaskInfo(
                        task_id=torrent.get("hash", ""),
                        name=torrent.get("name", ""),
                        size=torrent.get("size", 0),
                        downloaded=torrent.get("downloaded", 0),
                        uploaded=torrent.get("uploaded", 0),
                        download_speed=torrent.get("dlspeed", 0),
                        upload_speed=torrent.get("upspeed", 0),
                        eta=torrent.get("eta", 0) if torrent.get("eta", -1) >= 0 else 0,
                        progress=torrent.get("progress", 0) * 100,
                        status=status_map.get(state, DownloadStatus.ERROR),
                        save_path=torrent.get("save_path", ""),
                        tags=tags,
                        category=torrent.get("category") or None,
                    )
                )

            return tasks
        except Exception as e:
            self.logger.error(f"获取所有任务失败: {e}")
            return []

    # ========== 标签管理 ==========

    async def set_torrent_tags(self, task_id: str | list[str], tags: list[str]) -> bool:
        """设置种子标签"""
        try:
            hashes = task_id if isinstance(task_id, str) else "|".join(task_id)
            await self._api_request(
                "POST",
                "/torrents/addTags",
                data={"hashes": hashes, "tags": ",".join(tags)},
            )
            return True
        except Exception as e:
            self.logger.error(f"设置标签失败: {e}")
            return False

    async def remove_torrent_tags(self, task_id: str | list[str], tags: list[str]) -> bool:
        """移除种子标签"""
        try:
            hashes = task_id if isinstance(task_id, str) else "|".join(task_id)
            await self._api_request(
                "POST",
                "/torrents/removeTags",
                data={"hashes": hashes, "tags": ",".join(tags)},
            )
            return True
        except Exception as e:
            self.logger.error(f"移除标签失败: {e}")
            return False

    # ========== 文件选择 ==========

    async def get_torrent_files(self, task_id: str) -> list[dict[str, Any]]:
        """
        获取种子文件列表

        Returns:
            [{"id": int, "name": str, "size": int, "progress": float, "priority": int}, ...]
        """
        try:
            files = await self._api_request("GET", "/torrents/files", params={"hash": task_id})

            result = []
            for f in files:
                result.append(
                    {
                        "id": f.get("index", 0),
                        "name": f.get("name", ""),
                        "size": f.get("size", 0),
                        "progress": f.get("progress", 0) * 100,
                        "priority": f.get("priority", 1),
                    }
                )
            return result
        except Exception as e:
            self.logger.error(f"获取种子文件列表失败: {e}")
            return []

    async def set_file_priority(self, task_id: str, file_ids: list[int], priority: int) -> bool:
        """
        设置文件下载优先级

        Args:
            task_id: 任务 ID
            file_ids: 文件 ID 列表
            priority: 优先级
                - 0 = 不下载
                - 1 = 正常
                - 6 = 高
                - 7 = 最高
        """
        try:
            await self._api_request(
                "POST",
                "/torrents/filePrio",
                data={
                    "hash": task_id,
                    "id": "|".join(str(i) for i in file_ids),
                    "priority": priority,
                },
            )
            return True
        except Exception as e:
            self.logger.error(f"设置文件优先级失败: {e}")
            return False

    # ========== 下载器信息 ==========

    async def get_transfer_info(self) -> dict[str, Any]:
        """
        获取下载器传输信息

        Returns:
            {
                "download_speed": int (B/s),
                "upload_speed": int (B/s),
                "downloaded": int (B),
                "uploaded": int (B),
            }
        """
        try:
            info = await self._api_request("GET", "/transfer/info")
            return {
                "download_speed": info.get("dl_info_speed", 0),
                "upload_speed": info.get("up_info_speed", 0),
                "downloaded": info.get("dl_info_data", 0),
                "uploaded": info.get("up_info_data", 0),
            }
        except Exception as e:
            self.logger.error(f"获取传输信息失败: {e}")
            return {
                "download_speed": 0,
                "upload_speed": 0,
                "downloaded": 0,
                "uploaded": 0,
            }

    # ========== 已完成任务 ==========

    async def get_completed_tasks(
        self, tags: list[str] | None = None, exclude_tags: list[str] | None = None
    ) -> list[DownloadTaskInfo]:
        """
        获取已完成的任务（seeding 状态）

        Args:
            tags: 只包含这些标签的任务
            exclude_tags: 排除包含这些标签的任务（如 "已整理"）

        Returns:
            已完成的任务列表
        """
        try:
            # 获取 seeding 状态的种子（已完成）
            torrents = await self._api_request(
                "GET", "/torrents/info", params={"filter": "seeding"}
            )

            result = []
            for torrent in torrents:
                tags_str = torrent.get("tags", "")
                torrent_tags = (
                    [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
                )

                # 过滤：只包含指定标签
                if tags and not all(t in torrent_tags for t in tags):
                    continue

                # 过滤：排除指定标签
                if exclude_tags and any(t in torrent_tags for t in exclude_tags):
                    continue

                # 必须包含默认标签（MusicPilot 任务）
                if self._default_tag not in torrent_tags:
                    continue

                result.append(
                    DownloadTaskInfo(
                        task_id=torrent.get("hash", ""),
                        name=torrent.get("name", ""),
                        size=torrent.get("size", 0),
                        downloaded=torrent.get("downloaded", 0),
                        uploaded=torrent.get("uploaded", 0),
                        download_speed=0,  # 已完成，速度为 0
                        upload_speed=torrent.get("upspeed", 0),
                        eta=0,
                        progress=100.0,
                        status=DownloadStatus.COMPLETED,
                        save_path=torrent.get("save_path", ""),
                        tags=torrent_tags,
                        category=torrent.get("category") or None,
                    )
                )

            return result
        except Exception as e:
            self.logger.error(f"获取已完成任务失败: {e}")
            return []

    # ========== 辅助方法 ==========

    async def get_downloading_tasks(self, tags: list[str] | None = None) -> list[DownloadTaskInfo]:
        """获取正在下载的任务"""
        try:
            torrents = await self._api_request(
                "GET", "/torrents/info", params={"filter": "downloading"}
            )

            result = []
            for torrent in torrents:
                tags_str = torrent.get("tags", "")
                torrent_tags = (
                    [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
                )

                # 过滤标签
                if tags and not all(t in torrent_tags for t in tags):
                    continue

                result.append(
                    DownloadTaskInfo(
                        task_id=torrent.get("hash", ""),
                        name=torrent.get("name", ""),
                        size=torrent.get("size", 0),
                        downloaded=torrent.get("downloaded", 0),
                        uploaded=torrent.get("uploaded", 0),
                        download_speed=torrent.get("dlspeed", 0),
                        upload_speed=torrent.get("upspeed", 0),
                        eta=torrent.get("eta", 0) if torrent.get("eta", -1) >= 0 else 0,
                        progress=torrent.get("progress", 0) * 100,
                        status=DownloadStatus.DOWNLOADING,
                        save_path=torrent.get("save_path", ""),
                        tags=torrent_tags,
                        category=torrent.get("category") or None,
                    )
                )

            return result
        except Exception as e:
            self.logger.error(f"获取下载中任务失败: {e}")
            return []

    # ========== 转移完成处理 ==========

    async def mark_as_transferred(self, task_id: str | list[str]) -> bool:
        """
        标记种子为已整理

        Args:
            task_id: 任务 ID 或任务 ID 列表

        Returns:
            是否成功
        """
        try:
            hashes = task_id if isinstance(task_id, str) else "|".join(task_id)
            # 添加"已整理"标签
            await self._api_request(
                "POST",
                "/torrents/addTags",
                data={"hashes": hashes, "tags": "已整理"},
            )
            self.logger.info(f"标记种子已整理: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"标记已整理失败: {e}")
            return False

    async def is_transferred(self, task_id: str) -> bool:
        """
        检查种子是否已整理

        Args:
            task_id: 任务 ID

        Returns:
            是否已整理
        """
        try:
            torrents = await self._api_request("GET", "/torrents/info", params={"hashes": task_id})
            if not torrents:
                return False
            tags_str = torrents[0].get("tags", "")
            return "已整理" in tags_str
        except Exception as e:
            self.logger.error(f"检查已整理状态失败: {e}")
            return False

    async def get_untransferred_tasks(
        self, tags: list[str] | None = None
    ) -> list[DownloadTaskInfo]:
        """
        获取已完成但未整理的任务

        Args:
            tags: 只包含这些标签的任务（可选）

        Returns:
            未整理的任务列表
        """
        return await self.get_completed_tasks(tags=tags, exclude_tags=["已整理"])

    # ========== 种子重命名 ==========

    async def rename_torrent(self, task_id: str, new_name: str) -> bool:
        """
        重命名种子

        Args:
            task_id: 任务 ID
            new_name: 新名称

        Returns:
            是否成功
        """
        try:
            await self._api_request(
                "POST",
                "/torrents/rename",
                data={"hash": task_id, "name": new_name},
            )
            self.logger.info(f"重命名种子: {task_id} -> {new_name}")
            return True
        except Exception as e:
            self.logger.error(f"重命名种子失败: {e}")
            return False

    # ========== 自动重连机制 ==========

    async def check_status(self) -> bool:
        """
        检查下载器状态，如果断开则尝试重连

        Returns:
            下载器是否可用
        """
        try:
            # 尝试获取传输信息，验证连接是否正常
            await self._api_request("GET", "/transfer/info")
            return True
        except Exception as e:
            self.logger.warning(f"下载器连接异常: {e}，尝试重新登录")
            # 重置 Session ID 并重新登录
            self._sid = None
            return await self._login()

    async def reconnect(self) -> bool:
        """
        强制重新连接下载器

        Returns:
            是否重连成功
        """
        self.logger.info("强制重连 qBittorrent")
        self._sid = None
        return await self._login()
