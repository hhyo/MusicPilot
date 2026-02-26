"""
下载链
处理音乐下载和整理
"""
from typing import List, Optional
from pathlib import Path

from app.chain import ChainBase
from app.core.context import DownloadStatus
from app.core.log import logger
from app.modules.downloader import DownloadTask, DownloadSource, DownloadQuality
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
        self.logger.info(f"搜索音乐: {keyword}")

        # 获取下载器
        downloader = self._get_downloader(source)
        if not downloader:
            raise ValueError(f"不支持的下载来源: {source}")

        # 搜索
        tasks = await downloader.search(keyword, limit, quality)

        if not tasks:
            self.logger.warning(f"未找到结果: {keyword}")
            return []

        # 创建下载记录
        download_tasks = []
        for task in tasks:
            # 保存到数据库
            await self._save_to_history(task, keyword, source)

            # 执行下载
            downloaded_task = await self._download_task(task, downloader)

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
        self.logger.info(f"通过 URL 下载: {url}")

        downloader = self._get_downloader(source)
        if not downloader:
            raise ValueError(f"不支持的下载来源: {source}")

        # 创建任务
        import time
        task = DownloadTask(
            task_id=f"{source.value}_{int(time.time())}",
            url=url,
            source=source,
            quality=quality,
            metadata=metadata or {},
        )

        # 保存到数据库
        await self._save_to_history(task, url, source)

        # 执行下载
        downloaded_task = await self._download_task(task, downloader)

        return downloaded_task

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

        return results

    async def get_download_status(self, task_id: str) -> Optional[dict]:
        """
        获取下载状态

        Args:
            task_id: 任务 ID

        Returns:
            下载状态
        """
        task = self._active_tasks.get(task_id)
        if task:
            return task.to_dict()

        # 从数据库查询
        history = await self.download_oper.get_by_source_id(task_id)
        if history:
            return {
                "task_id": history.source_id,
                "status": history.status,
                "file_path": history.file_path,
                "error_message": history.error_message,
            }

        return None

    async def get_active_downloads(self) -> List[dict]:
        """
        获取活跃的下载任务

        Returns:
            下载任务列表
        """
        return [task.to_dict() for task in self._active_tasks.values()]

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

    async def _download_task(
        self,
        task: DownloadTask,
        downloader
    ) -> DownloadTask:
        """
        执行下载任务

        Args:
            task: 下载任务
            downloader: 下载器实例

        Returns:
            完成的下载任务
        """
        self._active_tasks[task.task_id] = task

        def progress_callback(t: DownloadTask):
            """进度回调"""
            self.logger.debug(
                f"下载进度: {t.title or t.task_id} - {t.progress:.1%}"
            )

        try:
            downloaded_task = await downloader.download(
                task,
                progress_callback=progress_callback
            )

            # 更新数据库状态
            if downloaded_task.status == DownloadStatus.COMPLETED:
                await self.download_oper.update(
                    downloaded_task.task_id,
                    status="completed",
                    file_path=downloaded_task.file_path,
                    file_size=downloaded_task.total_bytes,
                )
                self.logger.info(f"下载完成: {downloaded_task.title}")
            else:
                await self.download_oper.update(
                    downloaded_task.task_id,
                    status="failed",
                    error_message=downloaded_task.error_message,
                )
                self.logger.error(
                    f"下载失败: {downloaded_task.title} - {downloaded_task.error_message}"
                )

        finally:
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]

        return downloaded_task

    async def _save_to_history(
        self,
        task: DownloadTask,
        query: str,
        source: DownloadSource
    ):
        """
        保存到下载历史

        Args:
            task: 下载任务
            query: 搜索关键词或 URL
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