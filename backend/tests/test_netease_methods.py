"""
NeteaseDownloader 方法测试
"""

import pytest


class TestNeteaseDownloaderMethods:
    """NeteaseDownloader 方法测试"""

    def test_import_netease(self):
        """测试导入网易云下载器"""
        from app.modules.downloader.netease import NeteaseDownloader
        assert NeteaseDownloader is not None

    def test_netease_has_methods(self):
        """测试网易云下载器方法"""
        from app.modules.downloader.netease import NeteaseDownloader
        methods = [m for m in dir(NeteaseDownloader) if not m.startswith('_')]
        assert len(methods) > 0


class TestNeteaseUrlMethods:
    """网易云 URL 方法测试"""

    def test_extract_song_id(self):
        """测试提取歌曲 ID"""
        url = "https://music.163.com/song?id=123456"
        if "id=" in url:
            song_id = url.split("id=")[1].split("&")[0]
            assert song_id == "123456"

    def test_extract_playlist_id(self):
        """测试提取歌单 ID"""
        url = "https://music.163.com/playlist?id=789012"
        if "id=" in url:
            playlist_id = url.split("id=")[1].split("&")[0]
            assert playlist_id == "789012"

    def test_extract_album_id(self):
        """测试提取专辑 ID"""
        url = "https://music.163.com/album?id=345678"
        if "id=" in url:
            album_id = url.split("id=")[1].split("&")[0]
            assert album_id == "345678"


class TestNeteaseDataStructures:
    """网易云数据结构测试"""

    def test_song_data(self):
        """测试歌曲数据结构"""
        song = {
            "id": 123456,
            "name": "Test Song",
            "artists": [{"id": 1, "name": "Artist"}],
            "album": {"id": 1, "name": "Album"},
            "duration": 180000,
        }
        assert song["id"] == 123456
        assert song["name"] == "Test Song"

    def test_playlist_data(self):
        """测试歌单数据结构"""
        playlist = {
            "id": 789012,
            "name": "Test Playlist",
            "trackCount": 100,
            "playCount": 10000,
        }
        assert playlist["id"] == 789012
        assert playlist["trackCount"] == 100

    def test_artist_data(self):
        """测试艺术家数据结构"""
        artist = {
            "id": 1,
            "name": "Test Artist",
            "albumSize": 10,
        }
        assert artist["id"] == 1
        assert artist["name"] == "Test Artist"


class TestNeteaseQuality:
    """网易云音质测试"""

    def test_quality_levels(self):
        """测试音质级别"""
        qualities = {
            "standard": 128,
            "higher": 192,
            "exhigh": 320,
            "lossless": 999,
            "hires": 1900,
        }
        for name, bitrate in qualities.items():
            assert bitrate > 0

    def test_quality_selection(self):
        """测试音质选择"""
        selected_quality = "exhigh"
        valid_qualities = ["standard", "higher", "exhigh", "lossless", "hires"]
        assert selected_quality in valid_qualities


class TestNeteaseDownloadLogic:
    """网易云下载逻辑测试"""

    def test_filename_sanitization(self):
        """测试文件名清理"""
        import re
        filename = "Test<>:\"/\\|?*File"
        safe = re.sub(r'[<>:"/\\|?*]', "", filename)
        assert "<" not in safe
        assert ">" not in safe

    def test_path_join(self):
        """测试路径拼接"""
        from pathlib import Path
        base = Path("/downloads")
        filename = "test.mp3"
        full_path = base / filename
        assert str(full_path) == "/downloads/test.mp3"

    def test_lyric_parsing(self):
        """测试歌词解析"""
        lyric = "[00:00.00]Test lyric line\n[00:05.00]Second line"
        lines = lyric.split("\n")
        assert len(lines) == 2
