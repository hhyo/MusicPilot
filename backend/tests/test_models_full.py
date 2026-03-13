"""
数据库模型层完整测试
"""


class TestArtistModelFull:
    """Artist Model 完整测试"""

    def test_artist_model_imports(self):
        from app.db.models.artist import Artist

        assert Artist is not None

    def test_artist_model_attributes(self):
        from app.db.models.artist import Artist

        # 验证模型存在
        assert hasattr(Artist, "__tablename__")


class TestAlbumModelFull:
    """Album Model 完整测试"""

    def test_album_model_imports(self):
        from app.db.models.album import Album

        assert Album is not None

    def test_album_model_attributes(self):
        from app.db.models.album import Album

        assert hasattr(Album, "__tablename__")


class TestTrackModelFull:
    """Track Model 完整测试"""

    def test_track_model_imports(self):
        from app.db.models.track import Track

        assert Track is not None

    def test_track_model_attributes(self):
        from app.db.models.track import Track

        assert hasattr(Track, "__tablename__")


class TestPlaylistModelFull:
    """Playlist Model 完整测试"""

    def test_playlist_model_imports(self):
        from app.db.models.playlist import Playlist

        assert Playlist is not None

    def test_playlist_model_attributes(self):
        from app.db.models.playlist import Playlist

        assert hasattr(Playlist, "__tablename__")


class TestSubscribeModelFull:
    """Subscribe Model 完整测试"""

    def test_subscribe_model_imports(self):
        from app.db.models.subscribe import Subscribe

        assert Subscribe is not None

    def test_subscribe_model_attributes(self):
        from app.db.models.subscribe import Subscribe

        assert hasattr(Subscribe, "__tablename__")


class TestSiteModelFull:
    """Site Model 完整测试"""

    def test_site_model_imports(self):
        from app.db.models.site import Site

        assert Site is not None

    def test_site_model_attributes(self):
        from app.db.models.site import Site

        assert hasattr(Site, "__tablename__")


class TestLibraryModelFull:
    """Library Model 完整测试"""

    def test_library_model_imports(self):
        from app.db.models.library import Library

        assert Library is not None

    def test_library_model_attributes(self):
        from app.db.models.library import Library

        assert hasattr(Library, "__tablename__")


class TestDownloadModelFull:
    """Download Model 完整测试"""

    def test_download_history_model_imports(self):
        from app.db.models.download import DownloadHistory

        assert DownloadHistory is not None

    def test_download_model_attributes(self):
        from app.db.models.download import DownloadHistory

        assert hasattr(DownloadHistory, "__tablename__")


class TestMediaModelFull:
    """Media Model 完整测试"""

    def test_media_server_model_imports(self):
        from app.db.models.media import MediaServer

        assert MediaServer is not None

    def test_media_model_attributes(self):
        from app.db.models.media import MediaServer

        assert hasattr(MediaServer, "__tablename__")


class TestSystemModelFull:
    """System Model 完整测试"""

    def test_system_config_model_imports(self):
        from app.db.models.system import SystemConfig

        assert SystemConfig is not None

    def test_system_model_attributes(self):
        from app.db.models.system import SystemConfig

        assert hasattr(SystemConfig, "__tablename__")


class TestSubscribeReleaseModelFull:
    """SubscribeRelease Model 完整测试"""

    def test_subscribe_release_model_imports(self):
        from app.db.models.subscribe_release import SubscribeRelease

        assert SubscribeRelease is not None

    def test_subscribe_release_model_attributes(self):
        from app.db.models.subscribe_release import SubscribeRelease

        assert hasattr(SubscribeRelease, "__tablename__")


class TestModelsInitFull:
    """Models Init 完整测试"""

    def test_models_module_imports(self):
        from app.db import models

        assert models is not None

    def test_all_models_exported(self):
        from app.db.models import (
            Album,
            Artist,
            Track,
        )

        assert Artist is not None
        assert Album is not None
        assert Track is not None
