"""
TorrentsChain 单元测试
测试资源搜索功能
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.torrents import TorrentInfo, TorrentsChain
from app.core.context import MusicInfo


class TestTorrentInfo:
    """TorrentInfo 测试类"""

    def test_to_dict(self):
        """测试转换为字典"""
        torrent = TorrentInfo(
            torrent_id="123",
            site_name="TestSite",
            title="Test Album",
            size=1024000,
            download_url="http://example.com/torrent",
            upload_time=datetime(2026, 1, 1, 12, 0, 0),
            seeders=10,
            leechers=2,
            is_free=True,
            format="FLAC",
            bitrate="24bit",
        )

        result = torrent.to_dict()

        assert result["torrent_id"] == "123"
        assert result["site_name"] == "TestSite"
        assert result["title"] == "Test Album"
        assert result["size"] == 1024000
        assert result["is_free"] is True
        assert result["format"] == "FLAC"

    def test_to_dict_no_upload_time(self):
        """测试无上传时间转换"""
        torrent = TorrentInfo(
            torrent_id="456",
            site_name="Site",
            title="Title",
            size=500,
            download_url="http://example.com/t",
        )

        result = torrent.to_dict()

        assert result["upload_time"] is None


class TestTorrentsChain:
    """TorrentsChain 测试类"""

    @pytest.fixture
    def chain(self):
        """创建 TorrentsChain 实例"""
        with patch("app.chain.torrents.db_manager"):
            with patch("app.chain.torrents.SiteOper"):
                with patch("app.chain.torrents.AsyncFileCache"):
                    chain = TorrentsChain()
                    return chain

    # ==================== _sort_results 测试 ====================

    def test_sort_results_free_first(self, chain):
        """测试免费种子优先排序"""
        torrents = [
            TorrentInfo("1", "Site", "A", 100, "url1", is_free=False, seeders=5),
            TorrentInfo("2", "Site", "B", 100, "url2", is_free=True, seeders=2),
        ]

        result = chain._sort_results(torrents)

        assert result[0].is_free is True

    def test_sort_results_by_seeders(self, chain):
        """测试按种子数排序"""
        torrents = [
            TorrentInfo("1", "Site", "A", 100, "url1", seeders=5, leechers=3),
            TorrentInfo("2", "Site", "B", 100, "url2", seeders=10, leechers=1),
        ]

        result = chain._sort_results(torrents)

        # 第二个种子活跃度更高 (10-1=9 > 5-3=2)
        assert result[0].seeders == 10

    # ==================== _filter_results 测试 ====================

    def test_filter_results_by_format(self, chain):
        """测试按格式过滤"""
        torrents = [
            TorrentInfo("1", "Site", "A", 100, "url1", format="FLAC"),
            TorrentInfo("2", "Site", "B", 100, "url2", format="MP3"),
        ]

        result = chain._filter_results(torrents, format="FLAC", min_size=None, max_size=None)

        assert len(result) == 1
        assert result[0].format == "FLAC"

    def test_filter_results_by_min_size(self, chain):
        """测试按最小大小过滤"""
        torrents = [
            TorrentInfo("1", "Site", "A", 50, "url1"),
            TorrentInfo("2", "Site", "B", 200, "url2"),
        ]

        result = chain._filter_results(torrents, format="", min_size=100, max_size=None)

        assert len(result) == 1
        assert result[0].size == 200

    def test_filter_results_by_max_size(self, chain):
        """测试按最大大小过滤"""
        torrents = [
            TorrentInfo("1", "Site", "A", 50, "url1"),
            TorrentInfo("2", "Site", "B", 200, "url2"),
        ]

        result = chain._filter_results(torrents, format="", min_size=None, max_size=100)

        assert len(result) == 1
        assert result[0].size == 50

    def test_filter_results_no_match(self, chain):
        """测试无匹配结果"""
        torrents = [
            TorrentInfo("1", "Site", "A", 50, "url1", format="MP3"),
        ]

        result = chain._filter_results(torrents, format="FLAC", min_size=None, max_size=None)

        assert len(result) == 0

    # ==================== _generate_cache_key 测试 ====================

    def test_generate_cache_key(self, chain):
        """测试缓存键生成"""
        music_info = MusicInfo(artist="Artist", album="Album")
        
        key1 = chain._generate_cache_key(music_info, "FLAC")
        key2 = chain._generate_cache_key(music_info, "FLAC")
        
        assert key1 == key2
        assert key1.startswith("torrent_search:")

    def test_generate_cache_key_different_params(self, chain):
        """测试不同参数生成不同缓存键"""
        music_info1 = MusicInfo(artist="Artist", album="Album")
        music_info2 = MusicInfo(artist="Artist", album="Album2")
        
        key1 = chain._generate_cache_key(music_info1, "FLAC")
        key2 = chain._generate_cache_key(music_info2, "FLAC")
        
        assert key1 != key2

    # ==================== search 测试 ====================

    @pytest.mark.asyncio
    async def test_search_no_enabled_sites(self, chain):
        """测试无启用站点"""
        chain.site_oper.get_enabled = AsyncMock(return_value=[])
        chain.cache.async_get = AsyncMock(return_value=None)

        music_info = MusicInfo(artist="Artist", album="Album")
        result = await chain.search(music_info)

        assert result == []

    @pytest.mark.asyncio
    async def test_search_with_cache(self, chain):
        """测试使用缓存搜索"""
        cached_data = [{
            "torrent_id": "cached-1",
            "site_name": "CachedSite",
            "title": "Cached Album",
            "size": 1000,
            "download_url": "http://cached.com/t",
            "upload_time": None,
            "seeders": 5,
            "leechers": 1,
            "is_free": False,
            "format": "FLAC",
            "bitrate": "",
        }]
        
        chain.cache.async_get = AsyncMock(return_value=cached_data)

        music_info = MusicInfo(artist="Artist", album="Album")
        result = await chain.search(music_info)

        assert len(result) == 1
        assert result[0].torrent_id == "cached-1"

    @pytest.mark.asyncio
    async def test_search_artist(self, chain):
        """测试搜索艺术家"""
        chain.site_oper.get_enabled = AsyncMock(return_value=[])
        chain.cache.async_get = AsyncMock(return_value=None)

        result = await chain.search_artist("Test Artist")

        # 无站点时返回空列表
        assert result == []

    @pytest.mark.asyncio
    async def test_search_album(self, chain):
        """测试搜索专辑"""
        chain.site_oper.get_enabled = AsyncMock(return_value=[])
        chain.cache.async_get = AsyncMock(return_value=None)

        result = await chain.search_album("Artist", "Album")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_title(self, chain):
        """测试搜索标题"""
        chain.site_oper.get_enabled = AsyncMock(return_value=[])
        chain.cache.async_get = AsyncMock(return_value=None)

        result = await chain.search_title("Test Title")

        assert result == []

    # ==================== _search_site 测试 ====================

    @pytest.mark.asyncio
    async def test_search_site_no_module(self, chain):
        """测试站点无对应模块"""
        mock_site = MagicMock()
        mock_site.name = "UnknownSite"

        chain.module_manager.get_running_modules_by_type = MagicMock(return_value=[])

        result = await chain._search_site(mock_site, MusicInfo(artist="Artist"), "FLAC")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_site_with_album(self, chain):
        """测试搜索专辑"""
        mock_site = MagicMock()
        mock_site.name = "TestSite"

        mock_result = MagicMock()
        mock_result.torrent_id = "t-1"
        mock_result.title = "Test Album"
        mock_result.size = 1000
        mock_result.download_url = "http://t.com/t"
        mock_result.upload_time = None
        mock_result.seeders = 5
        mock_result.leechers = 1
        mock_result.is_free = False
        mock_result.format = "FLAC"
        mock_result.bitrate = ""

        mock_module = MagicMock()
        mock_module.site_info.name = "TestSite"
        mock_module.search_album = AsyncMock(return_value=[mock_result])

        chain.module_manager.get_running_modules_by_type = MagicMock(
            return_value=[mock_module]
        )

        music_info = MusicInfo(artist="Artist", album="Album")
        result = await chain._search_site(mock_site, music_info, "FLAC")

        assert len(result) == 1
        assert result[0].torrent_id == "t-1"

    @pytest.mark.asyncio
    async def test_search_site_with_artist_only(self, chain):
        """测试仅搜索艺术家"""
        mock_site = MagicMock()
        mock_site.name = "TestSite"

        mock_module = MagicMock()
        mock_module.site_info.name = "TestSite"
        mock_module.search_artist = AsyncMock(return_value=[])

        chain.module_manager.get_running_modules_by_type = MagicMock(
            return_value=[mock_module]
        )

        music_info = MusicInfo(artist="Artist")
        result = await chain._search_site(mock_site, music_info, "FLAC")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_site_with_title_only(self, chain):
        """测试仅搜索标题"""
        mock_site = MagicMock()
        mock_site.name = "TestSite"

        mock_module = MagicMock()
        mock_module.site_info.name = "TestSite"
        mock_module.search_title = AsyncMock(return_value=[])

        chain.module_manager.get_running_modules_by_type = MagicMock(
            return_value=[mock_module]
        )

        music_info = MusicInfo(title="Title")
        result = await chain._search_site(mock_site, music_info, "FLAC")

        assert result == []
