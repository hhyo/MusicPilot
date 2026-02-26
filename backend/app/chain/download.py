"""
下载链
处理音乐下载和整理
"""
from typing import List, Optional, Callable
from pathlib import Path

from app.chain import ChainBase
from app.core.context import DownloadStatus
from app.core.log import logger
from app.modules.downloader import (
    DownloadTask,
    DownloadSource,
    DownloadQuality,
    DownloadStatus as DownloaderTaskStatus,
)
from app.db.operations.download import DownloadHistoryOper


class DownloadChain(ChainBase):
    """
    下载链
    负责音乐下载、文件整理、元数据补全
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.download_oper = DownloadHistoryOper(self.db_manager)
        self._active_tasks: dict[str, DownloadTask] = {}
        self._max_retries = 3  # 最大重试次数

    async def search(
        self,
        keyword: str,
        source: DownloadSource = DownloadSource.NETEASE,
        limit: int = 20,
        quality: Optional[DownloadQuality] = None
    ) -> List[DownloadTask]:
        """
        搜索音乐

        Args:
            keyword: 搜索关键词
            source: 下载来源
            limit: 返回数量限制
            quality: 目标质量

        Returns:
            搜索结果列表
        """
        self.logger.info(f"搜索音乐: {keyword}")

        # 获取下载器
        downloader = self._get_downloader(source)
        if not downloader:
            raise ValueError(f"不支持的下载来源: {source}")

        # 搜索
        tasks = await downloader.search(keyword, limit, quality)

        self.logger.info(f"搜索完成: 找到 {len(tasks)} 个结果")

        return tasks

    async def download(
        self,
        task: DownloadTask,
        source: DownloadSource = DownloadSource.NETEASE,
        progress_callback: Optional[Callable] = None,
        retry_count: int = 0
    ) -> DownloadTask:
        """
        下载音乐

        Args:
            task: 下载任务
            source: 下载来源
            progress_callback: 进度回调函数
            retry_count: 当前重试次数

        Returns:
            完成的下载任务
        """
        self.logger.info(f"开始下载: {task.title or task.task_id} (重试 {retry_count}/{self._max_retries})")

        # 获取下载器
        downloader = self._get_downloader(source)
        if not downloader:
            raise ValueError(f"不支持的下载来源: {source}")

        # 保存到数据库
        await self._save_to_history(task, source)

        # 添加到活跃任务
        self._active_tasks[task.task_id] = task

        # 更新数据库状态为下载中
        await self.download_oper.update(
            task.task_id,
            status="downloading",
        )

        # 发送下载开始事件
        await self.put_message(
            EventType.DOWNLOAD_STARTED,
            {
                "task_id": task.task_id,
                "title": task.title,
                "artist": task.artist,
                "album": task.album,
                "quality": task.quality.value,
            }
        )

        try:
            # 执行下载
            downloaded_task = await downloader.download(task, progress_callback)

            # 检查是否需要重试
            if (downloaded_task.status == DownloaderTaskStatus.FAILED
                and retry_count < self._max_retries):
                self.logger.warning(
                    f"下载失败，准备重试 ({retry_count + 1}/{self._max_retries}): "
                    f"{downloaded_task.title} - {downloaded_task.error_message}"
                )

                # 延迟后重试
                import asyncio
                await asyncio.sleep(2 ** retry_count)  # 指数退避

                # 重试
                return await self.download(
                    task,
                    source,
                    progress_callback,
                    retry_count + 1,
                )

            # 下载完成处理
            await self.complete(downloaded_task)

            return downloaded_task

        except Exception as e:
            self.logger.error(f"下载异常: {task.title or task.task_id} - {e}")
            task.status = DownloaderTaskStatus.FAILED
            task.error_message = str(e)

            # 更新数据库
            await self.download_oper.update(
                task.task_id,
                status="failed",
                error_message=task.error_message,
            )

            # 发送下载失败事件
            await self.put_message(
                EventType.DOWNLOAD_FAILED,
                {
                    "task_id": task.task_id,
                    "error": task.error_message,
                }
            )

            return task

        finally:
            # 从活跃任务中移除
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]

    async def complete(self, task: DownloadTask) -> DownloadTask:
        """
        下载完成处理

        Args:
            task: 下载任务

        Returns:
            完成的下载任务
        """
        if task.status == DownloaderTaskStatus.COMPLETED:
            self.logger.info(f"下载完成: {task.title}")

            # 更新数据库
            await self.download_oper.update(
                task.task_id,
                status="completed",
                file_path=task.file_path,
                file_size=task.total_bytes,
                file_format=Path(task.file_path).suffix[1:] if task.file_path else None,
            )

            # 发送下载完成事件
            await self.put_message(
                EventType.DOWNLOAD_COMPLETED,
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "artist": task.artist,
                    "album": task.album,
                    "file_path": task.file_path,
                    "file_size": task.total_bytes,
                    "quality": task.quality.value,
                }
            )

            # TODO: 调用 TransferChain 整理文件
            # await self.run_module("transfer", task=task)

        else:
            self.logger.error(
                f"下载失败: {task.title} - {task.error_message}"
            )

            # 更新数据库
            await self.download_oper.update(
                task.task_id,
                status="failed",
                error_message=task.error_message,
            )

            # 发送下载失败事件
            await self.put_message(
                EventType.DOWNLOAD_FAILED,
                {
                    "task_id": task.task_id,
                    "error": task.error_message,
                }
            )

        return task

    async def search_and_download(
        self,
        keyword: str,
        source: DownloadSource = DownloadSource.NETEASE,
        quality: DownloadQuality = DownloadQuality.STANDARD,
        limit: int = 1
    ) -> List[DownloadTask]:
        """
        搜索并下载音乐

        Args:
            keyword: 搜索关键词
            source: 下载来源
            quality: 下载质量
            limit: 下载数量

        Returns:
            下载任务列表
        """
        # 搜索
        tasks = await self.search(keyword, source, limit, quality)

        if not tasks:
            self.logger.warning(f"未找到结果: {keyword}")
            return []

        # 下载
        download_tasks = []
        for task in tasks:
            downloaded_task = await self.download(task, source)
            download_tasks.append(downloaded_task)

        return download_tasks

    async def download_by_url(
        self,
        url: str,
        source: DownloadSource = DownloadSource.NETEASE,
        quality: DownloadQuality = DownloadQuality.STANDARD,
        metadata: Optional[dict] = None
    ) -> Optional[DownloadTask]:
        """
        通过 URL 下载

        Args:
            url: 音乐 URL 或 ID
            source: 下载来源
            quality: 下载质量
            metadata: 元数据

        Returns:
            下载任务
        """
        # 创建任务
        import time
        task = DownloadTask(
            task_id=f"{source.value}_{int(time.time())}",
            url=url,
            source=source,
            quality=quality,
            metadata=metadata or {},
        )

        # 下载
        return await self.download(task, source)

    async def download_batch(
        self,
        tasks: List[dict]
    ) -> List[DownloadTask]:
        """
        批量下载

        Args:
            tasks: 任务列表 [{keyword, source, quality}, ...]

        Returns:
            下载任务列表
        """
        self.logger.info(f"批量下载: {len(tasks)} 个任务")

        results = []

        for task_data in tasks:
            try:
                keyword = task_data.get("keyword")
                url = task_data.get("url")

                if keyword:
                    tasks = await self.search_and_download(
                        keyword=keyword,
                        source=DownloadSource(task_data.get("source", "netease")),
                        quality=DownloadQuality(task_data.get("quality", "standard")),
                    )
                    results.extend(tasks)
                elif url:
                    task = await self.download_by_url(
                        url=url,
                        source=DownloadSource(task_data.get("source", "netease")),
                        quality=DownloadQuality(task_data.get("quality", "standard")),
                        metadata=task_data.get("metadata"),
                    )
                    if task:
                        results.append(task)

            except Exception as e:
                self.logger.error(f"下载任务失败: {task_data}, 错误: {e}")

        self.logger.info(f"批量下载完成: 成功 {len(results)} 个")

        return results

    async def get_download_status(self, task_id: str) -> Optional[dict]:
        """
        获取下载状态

        Args:
            task_id: 任务 ID

        Returns:
            下载状态
        """
        # 检查活跃任务
        task = self._active_tasks.get(task_id)
        if task:
            return task.to_dict()

        # 从数据库查询
        history = await self.download_oper.get_by_source_id(task_id)
        if history:
            return {
                "task_id": history.source_id,
                "source": history.source,
                "artist": history.artist,
                "album": history.album,
                "title": history.title,
                "status": history.status,
                "file_path": history.file_path,
                "file_size": history.file_size,
                "error_message": history.error_message,
                "quality": history.quality,
                "created_at": history.created_at.isoformat() if history.created_at else None,
                "completed_at": history.completed_at.isoformat() if history.completed_at else None,
            }

        return None

    async def get_active_downloads(self) -> List[dict]:
        """
        获取活跃的下载任务

        Returns:
            下载任务列表
        """
        return [task.to_dict() for task in self._active_tasks.values()]

    async def cancel_download(self, task_id: str) -> bool:
        """
        取消下载任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        task = self._active_tasks.get(task_id)
        if task:
            task.status = DownloaderTaskStatus.CANCELLED
            self.logger.info(f"取消下载: {task.task_id}")

            # 更新数据库
            await self.download_oper.update(
                task_id,
                status="cancelled",
            )

            return True
        return False

    def _get_downloader(self, source: DownloadSource):
        """
        获取下载器实例

        Args:
            source: 下载来源

        Returns:
            下载器实例
        """
        from app.modules.downloader.netease import NeteaseDownloader

        downloaders = {
            DownloadSource.NETEASE: NeteaseDownloader,
            # TODO: 添加其他下载器
        }

        downloader_class = downloaders.get(source)
        if not downloader_class:
            return None

        return downloader_class()

    async def _save_to_history(
        self,
        task: DownloadTask,
        source: DownloadSource
    ):
        """
        保存到下载历史

        Args:
            task: 下载任务
            source: 下载来源
        """
        await self.download_oper.create(
            source=source.value,
            source_id=task.url,
            artist=task.artist,
            album=task.album,
            title=task.title,
            url=task.url,
            quality=task.quality.value,
            status="pending",
        )