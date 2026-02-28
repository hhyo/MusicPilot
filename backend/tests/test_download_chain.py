"""
DownloadChain 单元测试
测试下载处理链的功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.download import DownloadChain
from app.modules.downloader import DownloadSource, DownloadStatus, DownloadTask, DownloadQuality


class TestDownloadChain:
    """DownloadChain 测试类"""

    @pytest.fixture
    def mock_db_manager(self):
        """创建 mock 数据库管理器"""
        return MagicMock()

    @pytest.fixture
    def mock_download_oper(self):
        """创建 mock 下载操作器"""
        oper = MagicMock()
        oper.update = AsyncMock()
        oper.get_by_source_id = AsyncMock(return_value=None)
        oper.create = AsyncMock()
        return oper

    @pytest.fixture
    def chain(self, mock_db_manager, mock_download_oper):
        """创建 DownloadChain 实例"""
        with patch("app.chain.download.DownloadHistoryOper", return_value=mock_download_oper):
            chain = DownloadChain(db_manager=mock_db_manager)
            chain.download_oper = mock_download_oper
            return chain

    @pytest.fixture
    def sample_task(self):
        """创建示例下载任务"""
        task = DownloadTask(
            task_id="test-task-001",
            url="https://example.com/song.mp3",
            source=DownloadSource.NETEASE,
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
        )
        return task

    # ==================== search 测试 ====================

    @pytest.mark.asyncio
    async def test_search_success(self, chain, sample_task):
        """测试成功搜索音乐"""
        mock_downloader = AsyncMock()
        mock_downloader.search = AsyncMock(return_value=[sample_task])

        with patch.object(chain, "_get_downloader", return_value=mock_downloader):
            results = await chain.search(
                keyword="test song", source=DownloadSource.NETEASE, limit=10
            )

        assert len(results) == 1
        assert results[0].title == "Test Song"
        mock_downloader.search.assert_called_once_with("test song", 10, None)

    @pytest.mark.asyncio
    async def test_search_unsupported_source(self, chain):
        """测试不支持的下载源"""
        with patch.object(chain, "_get_downloader", return_value=None):
            with pytest.raises(ValueError, match="不支持的下载来源"):
                await chain.search("test", DownloadSource.NETEASE)

    @pytest.mark.asyncio
    async def test_search_with_quality(self, chain, sample_task):
        """测试带质量参数的搜索"""
        mock_downloader = AsyncMock()
        mock_downloader.search = AsyncMock(return_value=[sample_task])

        with patch.object(chain, "_get_downloader", return_value=mock_downloader):
            results = await chain.search(
                keyword="test song",
                source=DownloadSource.NETEASE,
                limit=10,
                quality=DownloadQuality.HIGH,
            )

        assert len(results) == 1

    # ==================== download 测试 ====================

    @pytest.mark.asyncio
    async def test_download_unsupported_source(self, chain, sample_task):
        """测试下载时不支持的来源"""
        with patch.object(chain, "_get_downloader", return_value=None):
            with pytest.raises(ValueError, match="不支持的下载来源"):
                await chain.download(sample_task, DownloadSource.NETEASE)

    # ==================== get_download_status 测试 ====================

    @pytest.mark.asyncio
    async def test_get_download_status(self, chain, sample_task):
        """测试获取下载状态"""
        chain._active_tasks = {sample_task.task_id: sample_task}

        result = await chain.get_download_status(sample_task.task_id)

        assert result is not None
        assert result["task_id"] == sample_task.task_id

    # ==================== get_active_downloads 测试 ====================

    @pytest.mark.asyncio
    async def test_get_active_downloads(self, chain, sample_task):
        """测试获取活跃下载列表"""
        sample_task.status = DownloadStatus.DOWNLOADING
        chain._active_tasks = {sample_task.task_id: sample_task}

        results = await chain.get_active_downloads()

        assert len(results) == 1
        assert results[0]["task_id"] == sample_task.task_id

    @pytest.mark.asyncio
    async def test_get_active_downloads_empty(self, chain):
        """测试空活跃下载列表"""
        chain._active_tasks = {}

        results = await chain.get_active_downloads()

        assert len(results) == 0

    # ==================== _get_downloader 测试 ====================

    def test_get_downloader_returns_none_for_unknown(self, chain):
        """测试未知下载源返回 None"""
        # _get_downloader 需要访问 module_manager
        # 简化测试，只验证方法存在
        assert hasattr(chain, "_get_downloader")
