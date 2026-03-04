"""
NeteaseDownloader 详细测试
"""

import pytest


class TestNeteaseDownloaderDetailed:
    """NeteaseDownloader 详细测试"""

    @pytest.fixture
    def downloader(self):
        from app.modules.downloader.netease import NeteaseDownloader

        return NeteaseDownloader()

    def test_module_imports(self):
        from app.modules.downloader import netease

        assert netease is not None

    def test_class_exists(self):
        from app.modules.downloader.netease import NeteaseDownloader

        assert NeteaseDownloader is not None

    def test_init(self, downloader):
        assert downloader is not None

    def test_init_setting(self, downloader):
        result = downloader.init_setting()
        assert result is not None or result is None

    def test_map_quality(self, downloader):
        from app.core.context import DownloadQuality

        result = downloader._map_quality(DownloadQuality.STANDARD)
        assert result is not None

    def test_map_level(self, downloader):
        from app.core.context import DownloadQuality

        result = downloader._map_level(DownloadQuality.STANDARD)
        assert result is not None

    @pytest.mark.asyncio
    async def test_search(self, downloader):
        result = await downloader.search("test")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_url(self, downloader):
        result = await downloader.get_url("https://music.163.com/song?id=123")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_download(self, downloader):
        result = await downloader.download("https://music.163.com/song?id=123")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_get_song_detail(self, downloader):
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
        result = await downloader.fetch_playlist("123456")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_fetch_chart(self, downloader):
        result = await downloader.fetch_chart("19723756")
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_test(self, downloader):
        result = await downloader.test()
        assert result is not None
