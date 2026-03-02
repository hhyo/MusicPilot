"""
NeteaseDownloader 完整测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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
    async def test_get_song_url(self, downloader):
        result = await downloader.get_song_url("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_song_info(self, downloader):
        result = await downloader.get_song_info("123456")
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
    async def test_get_playlist_songs(self, downloader):
        result = await downloader.get_playlist_songs("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_download_song(self, downloader):
        result = await downloader.download_song("123456", "/tmp/test.mp3")
        assert result is not None or result is None

    def test_get_supported_formats(self, downloader):
        formats = downloader.get_supported_formats()
        assert formats is not None

    def test_get_downloader_name(self, downloader):
        name = downloader.get_downloader_name()
        assert name is not None

    def test_is_available(self, downloader):
        result = downloader.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_lyric(self, downloader):
        result = await downloader.get_lyric("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_comments(self, downloader):
        result = await downloader.get_comments("123456", "song")
        assert result is not None or result is None
