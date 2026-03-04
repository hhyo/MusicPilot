"""
下载监控任务完整测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDownloadMonitorTaskFull:
    """DownloadMonitorTask 完整测试"""

    @pytest.mark.asyncio
    async def test_check_download_progress_no_tasks(self):
        """测试无下载任务时检查进度"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.download_monitor import DownloadMonitorTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)

        with patch("app.tasks.download_monitor.DownloaderChain"):
            with patch("app.tasks.download_monitor.SubscribeReleaseOper") as mock_oper:
                with patch("app.tasks.download_monitor.DownloadHistoryOper"):
                    mock_oper.return_value.get_downloading = AsyncMock(return_value=[])

                    task = DownloadMonitorTask(mock_scheduler)
                    await task.check_download_progress()

                    mock_oper.return_value.get_downloading.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_download_progress_with_tasks(self):
        """测试有下载任务时检查进度"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.download_monitor import DownloadMonitorTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        mock_release = MagicMock()
        mock_release.id = 1
        mock_release.downloader_task_id = "task-123"
        mock_release.downloader = "qbittorrent"

        mock_progress = MagicMock()
        mock_progress.downloaded = 512000
        mock_progress.total = 1024000

        with patch("app.tasks.download_monitor.DownloaderChain") as mock_chain:
            mock_chain.return_value.get_progress = AsyncMock(return_value=mock_progress)

            with patch("app.tasks.download_monitor.SubscribeReleaseOper") as mock_oper:
                mock_oper.return_value.get_downloading = AsyncMock(return_value=[mock_release])
                mock_oper.return_value.update_download_status = AsyncMock()

                with patch("app.tasks.download_monitor.DownloadHistoryOper"):
                    task = DownloadMonitorTask(mock_scheduler)
                    await task.check_download_progress()

                    mock_oper.return_value.get_downloading.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_failed_downloads(self):
        """测试检查失败任务"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.download_monitor import DownloadMonitorTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)

        with patch("app.tasks.download_monitor.DownloaderChain"):
            with patch("app.tasks.download_monitor.SubscribeReleaseOper") as mock_oper:
                mock_oper.return_value.get_failed = AsyncMock(return_value=[])

                with patch("app.tasks.download_monitor.DownloadHistoryOper"):
                    task = DownloadMonitorTask(mock_scheduler)
                    await task.check_failed_downloads()

                    mock_oper.return_value.get_failed.assert_called_once()

    def test_start_monitor(self):
        """测试启动监控"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.download_monitor import DownloadMonitorTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        mock_scheduler.add_job = MagicMock()

        with patch("app.tasks.download_monitor.DownloaderChain"):
            with patch("app.tasks.download_monitor.SubscribeReleaseOper"):
                with patch("app.tasks.download_monitor.DownloadHistoryOper"):
                    task = DownloadMonitorTask(mock_scheduler)
                    task.start(interval=60)

                    # 验证添加了两个定时任务
                    assert mock_scheduler.add_job.call_count == 2

    def test_stop_monitor(self):
        """测试停止监控"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.download_monitor import DownloadMonitorTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        mock_scheduler.remove_job = MagicMock()

        with patch("app.tasks.download_monitor.DownloaderChain"):
            with patch("app.tasks.download_monitor.SubscribeReleaseOper"):
                with patch("app.tasks.download_monitor.DownloadHistoryOper"):
                    task = DownloadMonitorTask(mock_scheduler)
                    task.stop()

                    # 验证移除了两个定时任务
                    assert mock_scheduler.remove_job.call_count == 2

    def test_get_status(self):
        """测试获取状态"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.download_monitor import DownloadMonitorTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        mock_scheduler.get_job = MagicMock(return_value=None)

        with patch("app.tasks.download_monitor.DownloaderChain"):
            with patch("app.tasks.download_monitor.SubscribeReleaseOper"):
                with patch("app.tasks.download_monitor.DownloadHistoryOper"):
                    task = DownloadMonitorTask(mock_scheduler)
                    status = task.get_status()

                    assert "check_download_progress" in status
                    assert "check_failed_downloads" in status


class TestSubscribeCheckTaskFull:
    """SubscribeCheckTask 完整测试"""

    def test_import_subscribe_check(self):
        """测试导入订阅检查模块"""
        from app.tasks.subscribe_check import SubscribeCheckTask

        assert SubscribeCheckTask is not None

    @pytest.mark.asyncio
    async def test_subscribe_check_creation(self):
        """测试订阅检查任务创建"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from app.tasks.subscribe_check import SubscribeCheckTask

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)

        with patch("app.tasks.subscribe_check.SubscribeChain"):
            task = SubscribeCheckTask(mock_scheduler)
            assert task is not None
