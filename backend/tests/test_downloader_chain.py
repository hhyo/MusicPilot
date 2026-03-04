"""
DownloaderChain 单元测试
测试下载器对接功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.downloader import DownloaderChain


class TestDownloaderChain:
    """DownloaderChain 测试类"""

    @pytest.fixture
    def chain(self):
        """创建 DownloaderChain 实例"""
        with patch("app.chain.downloader.db_manager"):
            with patch("app.chain.downloader.SiteOper"):
                chain = DownloaderChain()
                return chain

    # ==================== push_torrent 测试 ====================

    @pytest.mark.asyncio
    async def test_push_torrent_success(self, chain):
        """测试成功推送种子"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.add_torrent = AsyncMock(return_value="task-123")

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        with patch("app.chain.downloader.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()

            result = await chain.push_torrent(
                "http://example.com/torrent.torrent",
                "/downloads",
                "TestSite",
            )

        assert result == "task-123"

    @pytest.mark.asyncio
    async def test_push_torrent_with_paused(self, chain):
        """测试暂停模式推送种子"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.add_torrent = AsyncMock(return_value="task-456")

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        with patch("app.chain.downloader.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()

            result = await chain.push_torrent(
                "http://example.com/torrent.torrent",
                "/downloads",
                "TestSite",
                paused=True,
            )

        assert result == "task-456"

    @pytest.mark.asyncio
    async def test_push_torrent_no_downloader(self, chain):
        """测试找不到下载器"""
        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[])

        with pytest.raises(ValueError, match="未找到下载器"):
            await chain.push_torrent(
                "http://example.com/torrent.torrent",
                "/downloads",
                "TestSite",
                downloader="transmission",
            )

    @pytest.mark.asyncio
    async def test_push_torrent_module_error(self, chain):
        """测试下载器模块错误"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.add_torrent = AsyncMock(side_effect=Exception("Connection error"))

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        with pytest.raises(Exception, match="Connection error"):
            await chain.push_torrent(
                "http://example.com/torrent.torrent",
                "/downloads",
                "TestSite",
            )

    # ==================== get_progress 测试 ====================

    @pytest.mark.asyncio
    async def test_get_progress_success(self, chain):
        """测试获取下载进度成功"""
        mock_progress = MagicMock()
        mock_progress.task_id = "task-123"
        mock_progress.progress = 50.0

        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.get_task_progress = AsyncMock(return_value=mock_progress)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        with patch("app.chain.downloader.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()

            result = await chain.get_progress("task-123")

        assert result is not None
        assert result.task_id == "task-123"

    @pytest.mark.asyncio
    async def test_get_progress_not_found(self, chain):
        """测试获取不存在的任务进度"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.get_task_progress = AsyncMock(return_value=None)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        with patch("app.chain.downloader.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()

            result = await chain.get_progress("nonexistent")

        assert result is None

    # ==================== pause_torrent 测试 ====================

    @pytest.mark.asyncio
    async def test_pause_torrent_success(self, chain):
        """测试暂停任务成功"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.pause_torrent = AsyncMock(return_value=True)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        result = await chain.pause_torrent("task-123")

        assert result is True

    # ==================== resume_torrent 测试 ====================

    @pytest.mark.asyncio
    async def test_resume_torrent_success(self, chain):
        """测试恢复任务成功"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.resume_torrent = AsyncMock(return_value=True)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        result = await chain.resume_torrent("task-123")

        assert result is True

    # ==================== remove_torrent 测试 ====================

    @pytest.mark.asyncio
    async def test_remove_torrent_success(self, chain):
        """测试删除任务成功"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.remove_torrent = AsyncMock(return_value=True)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        result = await chain.remove_torrent("task-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_remove_torrent_with_files(self, chain):
        """测试删除任务及文件"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.remove_torrent = AsyncMock(return_value=True)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        with patch("app.chain.downloader.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()

            result = await chain.remove_torrent("task-123", delete_files=True)

        assert result is True

    # ==================== get_all_tasks 测试 ====================

    @pytest.mark.asyncio
    async def test_get_all_tasks(self, chain):
        """测试获取所有任务"""
        mock_tasks = [
            MagicMock(task_id="task-1", progress=50.0),
            MagicMock(task_id="task-2", progress=100.0),
        ]

        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.get_all_tasks = AsyncMock(return_value=mock_tasks)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        result = await chain.get_all_tasks()

        assert len(result) == 2

    # ==================== check_downloader_status 测试 ====================

    @pytest.mark.asyncio
    async def test_check_downloader_status(self, chain):
        """测试获取下载器状态"""
        mock_module = MagicMock()
        mock_module.downloader_type = "qbittorrent"
        mock_module.check_status = AsyncMock(return_value=True)

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[mock_module])

        result = await chain.check_downloader_status()

        assert result is True

    @pytest.mark.asyncio
    async def test_check_downloader_status_not_found(self, chain):
        """测试下载器不存在时返回 False"""
        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[])

        result = await chain.check_downloader_status()

        assert result is False
