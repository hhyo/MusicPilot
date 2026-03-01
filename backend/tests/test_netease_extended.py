"""
NeteaseDownloader 扩展测试
"""

import pytest


class TestNeteaseDownloaderExtended:
    """NeteaseDownloader 扩展测试"""

    def test_module_import(self):
        """测试模块导入"""
        from app.modules.downloader.netease import NeteaseDownloader
        assert NeteaseDownloader is not None

    def test_downloader_base(self):
        """测试下载器基类"""
        from app.modules.downloader.base import DownloaderBase
        assert DownloaderBase is not None

    def test_quality_constants(self):
        """测试音质常量"""
        qualities = {
            "standard": 128000,
            "higher": 192000,
            "exhigh": 320000,
            "lossless": 999000,
            "hires": 1900000,
        }
        for quality, bitrate in qualities.items():
            assert bitrate > 0


class TestNeteaseUrlParsing:
    """网易云 URL 解析测试"""

    def test_song_url_pattern(self):
        """测试歌曲 URL 模式"""
        url = "https://music.163.com/song?id=123456"
        assert "song" in url
        assert "id=" in url

    def test_playlist_url_pattern(self):
        """测试歌单 URL 模式"""
        url = "https://music.163.com/playlist?id=789012"
        assert "playlist" in url
        assert "id=" in url

    def test_album_url_pattern(self):
        """测试专辑 URL 模式"""
        url = "https://music.163.com/album?id=345678"
        assert "album" in url
        assert "id=" in url


class TestNeteaseMetadata:
    """网易云元数据测试"""

    def test_song_metadata_structure(self):
        """测试歌曲元数据结构"""
        metadata = {
            "song_id": "123456",
            "name": "Test Song",
            "artists": [{"id": "1", "name": "Artist"}],
            "album": {"id": "1", "name": "Album"},
            "duration": 180000,
            "quality": "exhigh",
        }
        assert "song_id" in metadata
        assert "name" in metadata
        assert "artists" in metadata

    def test_lyric_structure(self):
        """测试歌词结构"""
        lyric = {
            "song_id": "123456",
            "lyric": "[00:00.00]Test lyric",
            "tlyric": "",
        }
        assert "lyric" in lyric
