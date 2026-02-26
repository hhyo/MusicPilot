"""
下载链
处理音乐下载任务
"""
from typing import List, Optional
from pathlib import Path

from app.chain import ChainBase
from app.core.context import DownloadSource, DownloadTask, DownloadStatus, DownloaderType
from app.core.log import logger


class DownloadChain(ChainBase):
    """
    下载链
    负责搜索音乐、下载文件、完成下载处理
    """

    async def search(self, query: str, source: str = "netease") -> List[DownloadSource]:
        """
        搜索音乐

        Args:
            query: 搜索关键词
            source: 下载器类型

        Returns:
            下载源列表
        """
        self.logger.info(f"搜索音乐: {query}")

        # 检查缓存
        cache_key = f"search:{source}:{query}"
        cached = self.get_cache(cache_key)
        if cached:
            self.logger.debug(f"使用缓存的搜索结果: {query}")
            return cached

        # 调用下载器模块搜索
        results = await self.run_module(source, "search_track", query)

        if not results:
            self.logger.warning(f"未找到搜索结果: {query}")
            return []

        # 缓存结果（5分钟）
        self.set_cache(cache_key, results, ttl=300)

        return results

    async def download(self, source: DownloadSource, save_path: str) -> DownloadTask:
        """
        下载音乐

        Args:
            source: 下载源
            save_path: 保存路径

        Returns:
            下载任务对象
        """
        self.logger.info(f"开始下载: {source.title}")

        # 创建下载任务
        task = DownloadTask(
            task_id=f"{source.type}:{source.source_id}",
            source=source,
            status=DownloadStatus.PENDING,
            save_path=save_path,
        )

        # 发送下载开始事件
        self.send_event("download.started", {
            "task_id": task.task_id,
            "title": source.title,
            "source": source.type.value,
        })

        # 调用下载器模块下载
        result = await self.run_module(source.type.value, "download_track", source)

        if result:
            task.status = DownloadStatus.COMPLETED
            task.file_path = result
            task.downloaded_size = Path(result).stat().st_size if Path(result).exists() else 0

            # 发送下载完成事件
            self.send_event("download.completed", {
                "task_id": task.task_id,
                "file_path": result,
            })

            self.logger.info(f"下载完成: {source.title}")
        else:
            task.status = DownloadStatus.FAILED
            task.error_message = "下载失败"

            # 发送下载失败事件
            self.send_event("download.failed", {
                "task_id": task.task_id,
                "error": task.error_message,
            })

            self.logger.error(f"下载失败: {source.title}")

        return task

    async def complete(self, task: DownloadTask):
        """
        下载完成处理

        Args:
            task: 下载任务对象
        """
        self.logger.info(f"处理下载完成: {task.source.title}")

        # 调用 TransferChain 整理文件
        transfer_result = await self.run_module("transfer", "organize", task)

        # 调用 MetadataChain 补全元数据
        from app.chain.metadata import MetadataChain
        metadata_chain = MetadataChain(
            event_manager=self.event_manager,
            module_manager=self.module_manager,
            plugin_manager=self.plugin_manager,
            cache=self.cache,
        )

        metadata = await metadata_chain.recognize(task.file_path)
        completed_metadata = await metadata_chain.complete(metadata)

        # 发送转移完成事件
        self.send_event("transfer.completed", {
            "task_id": task.task_id,
            "metadata": completed_metadata.to_dict(),
        })

        return completed_metadata