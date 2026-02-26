"""
下载进度监控定时任务
定期检查下载器状态并更新数据库
"""
from typing import Optional
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.chain.downloader import DownloaderChain
from app.db.operations.subscribe_release import SubscribeReleaseOper
from app.db.operations.download import DownloadHistoryOper
from app.core.log import logger
from app.db.models.subscribe_release import SubscribeRelease
from app.db.models.download import DownloadHistory
from app.db import db_manager


class DownloadMonitorTask:
    """
    下载进度监控任务
    """

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.downloader_chain = DownloaderChain()
        self.subscribe_release_oper = SubscribeReleaseOper(SubscribeRelease, db_manager)
        self.download_history_oper = DownloadHistoryOper(DownloadHistory, db_manager)

    async def check_download_progress(self):
        """
        检查下载进度

        定期检查所有正在下载的任务，更新进度到数据库
        """
        logger.info("开始检查下载进度")

        try:
            # 获取所有正在下载的订阅发布记录
            downloading_releases = await self.subscribe_release_oper.get_downloading()

            if not downloading_releases:
                logger.info("没有正在下载的任务")
                return

            for release in downloading_releases:
                if not release.downloader_task_id:
                    continue

                try:
                    # 获取下载进度
                    progress = await self.downloader_chain.get_progress(
                        release.downloader_task_id,
                        release.downloader or "qbittorrent"
                    )

                    if progress:
                        # 计算进度百分比
                        progress_percent = 0
                        if progress.total > 0:
                            progress_percent = (progress.downloaded / progress.total) * 100

                        # 更新订阅发布记录
                        await self.subscribe_release_oper.update_download_status(
                            release.id,
                            "downloading"
                        )

                        # 检查是否完成
                        if progress_percent >= 100 or progress.downloaded >= progress.total:
                            # 下载完成
                            await self._handle_download_complete(release)
                        else:
                            # 更新进度（如果有 DownloadHistory 记录）
                            await self._update_download_progress(release, progress)

                    logger.debug(
                        f"更新下载进度: {release.id}, 进度: {progress_percent:.2f}%"
                    )
                except Exception as e:
                    logger.error(f"检查下载进度失败: {release.id}, 错误: {e}")
                    # 标记为失败
                    await self.subscribe_release_oper.update_download_status(
                        release.id, "failed", str(e)
                    )

            logger.info(f"检查下载进度完成，共处理 {len(downloading_releases)} 个任务")
        except Exception as e:
            logger.error(f"检查下载进度失败: {e}")

    async def _handle_download_complete(self, release: SubscribeRelease):
        """
        处理下载完成

        Args:
            release: 订阅发布记录
        """
        logger.info(f"下载完成: {release.id}")

        try:
            # 更新订阅发布记录状态
            await self.subscribe_release_oper.update_download_status(
                release.id, "completed"
            )

            # TODO: 触发 TransferChain 进行文件转移
            # from app.chain.transfer import TransferChain
            # transfer_chain = TransferChain()
            # await transfer_chain.transfer_downloaded_file(release.id)

            logger.info(f"下载完成处理完成: {release.id}")
        except Exception as e:
            logger.error(f"处理下载完成失败: {release.id}, 错误: {e}")

    async def _update_download_progress(
        self, release: SubscribeRelease, progress
    ):
        """
        更新下载进度

        Args:
            release: 订阅发布记录
            progress: 下载进度
        """
        # 如果有 DownloadHistory 记录，更新进度
        # 这里可以扩展为更新 DownloadHistory 的进度字段
        logger.debug(
            f"更新进度: 任务 {release.id}, 已下载 {progress.downloaded}/{progress.total}"
        )

    async def check_failed_downloads(self):
        """
        检查失败的任务

        定期检查失败的任务，尝试重新下载
        """
        logger.info("开始检查失败任务")

        try:
            # 获取失败的任务
            failed_releases = await self.subscribe_release_oper.get_failed()

            if not failed_releases:
                logger.info("没有失败的任务")
                return

            for release in failed_releases:
                # 检查失败时间，如果是最近失败的，尝试重新下载
                # 这里可以添加重试逻辑
                logger.debug(f"失败任务: {release.id}")

            logger.info(f"检查失败任务完成，共 {len(failed_releases)} 个任务")
        except Exception as e:
            logger.error(f"检查失败任务失败: {e}")

    def start(self, interval: int = 60):
        """
        启动监控任务

        Args:
            interval: 检查间隔（秒）
        """
        logger.info(f"启动下载进度监控任务，间隔: {interval} 秒")

        # 添加定时任务
        self.scheduler.add_job(
            self.check_download_progress,
            'interval',
            seconds=interval,
            id='check_download_progress',
            name='检查下载进度',
            replace_existing=True
        )

        # 添加失败任务检查（每 5 分钟）
        self.scheduler.add_job(
            self.check_failed_downloads,
            'interval',
            seconds=300,
            id='check_failed_downloads',
            name='检查失败任务',
            replace_existing=True
        )

    def stop(self):
        """停止监控任务"""
        logger.info("停止下载进度监控任务")

        # 移除定时任务
        self.scheduler.remove_job('check_download_progress')
        self.scheduler.remove_job('check_failed_downloads')

    def get_status(self) -> dict:
        """
        获取监控状态

        Returns:
            监控状态
        """
        return {
            "check_download_progress": self.scheduler.get_job('check_download_progress') is not None,
            "check_failed_downloads": self.scheduler.get_job('check_failed_downloads') is not None,
        }