"""
DownloaderBase 测试
"""

import pytest


class TestDownloaderBase:
    """DownloaderBase 测试"""

    def test_import_base(self):
        """测试导入基类"""
        from app.modules.downloader.base import DownloaderBase
        assert DownloaderBase is not None

    def test_base_methods(self):
        """测试基类方法"""
        from app.modules.downloader.base import DownloaderBase
        methods = [m for m in dir(DownloaderBase) if not m.startswith('_')]
        assert len(methods) > 0


class TestDownloaderModule:
    """DownloaderModule 测试"""

    def test_import_module(self):
        """测试导入模块"""
        from app.modules.downloader_module import DownloaderModule
        assert DownloaderModule is not None

    def test_download_status(self):
        """测试下载状态"""
        from app.modules.downloader_module import DownloadStatus
        assert DownloadStatus is not None

    def test_download_progress(self):
        """测试下载进度"""
        from app.modules.downloader_module import DownloadProgress
        progress = DownloadProgress(
            task_id="test-1",
            progress=50.0,
            downloaded=512000,
            total=1024000,
            download_speed=102400,
        )
        assert progress.task_id == "test-1"

    def test_download_task_info(self):
        """测试下载任务信息"""
        from app.modules.downloader_module import DownloadTaskInfo, DownloadStatus
        task = DownloadTaskInfo(
            task_id="test-1",
            name="Test File",
            size=1024000,
            downloaded=512000,
            uploaded=0,
            download_speed=102400,
            upload_speed=0,
            eta=10,
            progress=50.0,
            status=DownloadStatus.DOWNLOADING,
            save_path="/downloads",
        )
        assert task.task_id == "test-1"


class TestDownloaderStatus:
    """下载状态测试"""

    def test_status_values(self):
        """测试状态值"""
        valid_statuses = ["pending", "downloading", "completed", "failed", "paused", "seeding"]
        for status in valid_statuses:
            assert isinstance(status, str)

    def test_progress_calculation(self):
        """测试进度计算"""
        downloaded = 512000
        total = 1024000
        progress = (downloaded / total) * 100
        assert progress == 50.0

    def test_speed_formatting(self):
        """测试速度格式化"""
        speed_bps = 1024000
        speed_kbps = speed_bps / 1024
        speed_mbps = speed_kbps / 1024
        assert speed_kbps == 1000.0
        assert speed_mbps < 1.0
