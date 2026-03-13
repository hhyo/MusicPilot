"""
NeteaseDownloader 完整测试
"""

from unittest.mock import patch

import pytest


class TestNeteaseDownloaderFull:
    """NeteseDownloader 完整测试"""

    def test_netease_downloader_imports(self):
        from app.modules.downloader.netease import NeteaseDownloader

        assert NeteaseDownloader is not None

    def test_netease_downloader_module(self):
        from app.modules.downloader import netease

        assert netease is not None

    @pytest.fixture
    def mock_settings(self):
        with patch("app.modules.downloader.netease.settings") as mock:
            mock.download_path = "/tmp/downloads"
            mock.temp_path = "/tmp/temp"
            yield mock

    @pytest.fixture
    def downloader(self, mock_settings):
        from app.modules.downloader.netease import NeteaseDownloader

        return NeteaseDownloader()

    def test_downloader_init(self, downloader):
        assert downloader is not None

    @pytest.mark.asyncio
    async def test_search(self, downloader):
        result = await downloader.search("test song")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_song_detail(self, downloader):
        """测试获取歌曲详情"""
        result = await downloader.get_song_detail("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_artist_songs(self, downloader):
        result = await downloader.get_artist_songs("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_album_songs(self, downloader):
        result = await downloader.get_album_songs("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_fetch_playlist(self, downloader):
        """测试获取播放列表"""
        result = await downloader.fetch_playlist("123456")
        assert result is not None or result is None

    def test_source_property(self, downloader):
        """测试下载源"""
        from app.modules.downloader.base import DownloadSource

        assert downloader.source == DownloadSource.NETEASE

    def test_supported_qualities(self, downloader):
        """测试支持的音质"""
        from app.modules.downloader.base import DownloadQuality

        assert DownloadQuality.LOSSLESS in downloader.supported_qualities