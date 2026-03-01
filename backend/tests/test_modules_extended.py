"""
模块扩展测试
"""

import pytest


class TestDownloaderBase:
    """DownloaderBase 测试"""

    def test_import_base(self):
        """测试导入基类"""
        from app.modules.downloader.base import DownloaderBase
        assert DownloaderBase is not None

    def test_download_status_enum(self):
        """测试下载状态枚举"""
        from app.modules.downloader_module import DownloadStatus
        assert hasattr(DownloadStatus, 'SEEDING')


class TestDownloaderModule:
    """DownloaderModule 测试"""

    def test_import_module(self):
        """测试导入模块"""
        from app.modules.downloader_module import DownloaderModule
        assert DownloaderModule is not None


class TestCoreContext:
    """Core Context 测试"""

    def test_music_info_creation(self):
        """测试 MusicInfo 创建"""
        from app.core.context import MusicInfo
        info = MusicInfo(
            artist="Test Artist",
            album="Test Album",
            title="Test Song",
        )
        assert info.artist == "Test Artist"
        assert info.album == "Test Album"
        assert info.title == "Test Song"

    def test_playback_session_creation(self):
        """测试 PlaybackSession 创建"""
        from app.core.context import PlaybackSession
        session = PlaybackSession(
            session_id="session-1",
            track_id=1,
        )
        assert session.session_id == "session-1"
        assert session.track_id == 1


class TestDbModels:
    """数据库模型测试"""

    def test_track_model(self):
        """测试 Track 模型"""
        from app.db.models.track import Track
        assert hasattr(Track, '__tablename__')

    def test_album_model(self):
        """测试 Album 模型"""
        from app.db.models.album import Album
        assert hasattr(Album, '__tablename__')

    def test_artist_model(self):
        """测试 Artist 模型"""
        from app.db.models.artist import Artist
        assert hasattr(Artist, '__tablename__')

    def test_playlist_model(self):
        """测试 Playlist 模型"""
        from app.db.models.playlist import Playlist
        assert hasattr(Playlist, '__tablename__')

    def test_site_model(self):
        """测试 Site 模型"""
        from app.db.models.site import Site
        assert hasattr(Site, '__tablename__')

    def test_subscribe_model(self):
        """测试 Subscribe 模型"""
        from app.db.models.subscribe import Subscribe
        assert hasattr(Subscribe, '__tablename__')

    def test_library_model(self):
        """测试 Library 模型"""
        from app.db.models.library import Library
        assert hasattr(Library, '__tablename__')

    def test_media_model(self):
        """测试 Media 模型"""
        from app.db.models.media import MediaServer
        assert hasattr(MediaServer, '__tablename__')

    def test_download_model(self):
        """测试 Download 模型"""
        from app.db.models.download import DownloadHistory
        assert hasattr(DownloadHistory, '__tablename__')
