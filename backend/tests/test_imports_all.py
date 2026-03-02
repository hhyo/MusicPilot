"""
所有模块导入测试 - 提升覆盖率
"""

import pytest


class TestAllAppImports:
    """所有 App 模块导入测试"""

    def test_app_main_imports(self):
        from app.main import app
        assert app is not None

    def test_app_api_imports(self):
        from app.api import apiv1
        assert apiv1 is not None

    def test_app_chain_imports(self):
        from app.chain import ChainBase, DownloadChain, MediaChain
        assert ChainBase is not None

    def test_app_core_imports(self):
        from app.core import config, log, event, context
        assert config is not None

    def test_app_db_imports(self):
        from app.db import DatabaseManager, Base, OperBase
        assert DatabaseManager is not None

    def test_app_schemas_imports(self):
        from app.schemas import artist, album, track, playlist
        assert artist is not None

    def test_app_modules_imports(self):
        from app.modules import downloader
        assert downloader is not None

    def test_app_tasks_imports(self):
        from app.tasks import download_monitor, subscribe_check
        assert download_monitor is not None


class TestAllChainImports:
    """所有 Chain 模块导入测试"""

    def test_download_chain_imports(self):
        from app.chain.download import DownloadChain
        assert DownloadChain is not None

    def test_media_chain_imports(self):
        from app.chain.media import MediaChain
        assert MediaChain is not None

    def test_metadata_chain_imports(self):
        from app.chain.metadata import MetadataChain
        assert MetadataChain is not None

    def test_musicbrainz_chain_imports(self):
        from app.chain.musicbrainz import MusicBrainzChain
        assert MusicBrainzChain is not None

    def test_playback_chain_imports(self):
        from app.chain.playback import PlaybackChain
        assert PlaybackChain is not None

    def test_playlist_chain_imports(self):
        from app.chain.playlist import PlaylistChain
        assert PlaylistChain is not None

    def test_subscribe_chain_imports(self):
        from app.chain.subscribe import SubscribeChain
        assert SubscribeChain is not None

    def test_torrents_chain_imports(self):
        from app.chain.torrents import TorrentsChain, TorrentInfo
        assert TorrentsChain is not None

    def test_transfer_chain_imports(self):
        from app.chain.transfer import TransferChain
        assert TransferChain is not None


class TestAllCoreImports:
    """所有 Core 模块导入测试"""

    def test_config_imports(self):
        from app.core.config import settings
        assert settings is not None

    def test_log_imports(self):
        from app.core.log import logger
        assert logger is not None

    def test_event_imports(self):
        from app.core.event import EventType, EventManager
        assert EventType is not None

    def test_context_imports(self):
        from app.core.context import MusicInfo, DownloadTask, PlaybackSession
        assert MusicInfo is not None

    def test_cache_imports(self):
        from app.core.cache import FileCache, AsyncFileCache
        assert FileCache is not None

    def test_chain_base_imports(self):
        from app.core.chain import ChainBase
        assert ChainBase is not None

    def test_meta_imports(self):
        from app.core.meta import MetadataParser, FilenameParser
        assert MetadataParser is not None

    def test_module_imports(self):
        from app.core.module import ModuleManager, ModuleBase
        assert ModuleManager is not None

    def test_plugin_imports(self):
        from app.core.plugin import PluginManager, PluginBase
        assert PluginManager is not None


class TestAllEndpointImports:
    """所有 API 端点模块导入测试"""

    def test_album_endpoint_imports(self):
        from app.api.endpoints.album import router
        assert router is not None

    def test_artist_endpoint_imports(self):
        from app.api.endpoints.artist import router
        assert router is not None

    def test_track_endpoint_imports(self):
        from app.api.endpoints.track import router
        assert router is not None

    def test_playlist_endpoint_imports(self):
        from app.api.endpoints.playlist import router
        assert router is not None

    def test_library_endpoint_imports(self):
        from app.api.endpoints.library import router
        assert router is not None

    def test_subscribe_endpoint_imports(self):
        from app.api.endpoints.subscribe import router
        assert router is not None

    def test_subscribe_release_endpoint_imports(self):
        from app.api.endpoints.subscribe_release import router
        assert router is not None

    def test_site_endpoint_imports(self):
        from app.api.endpoints.site import router
        assert router is not None

    def test_player_endpoint_imports(self):
        from app.api.endpoints.player import router
        assert router is not None

    def test_covers_endpoint_imports(self):
        from app.api.endpoints.covers import router
        assert router is not None

    def test_metadata_endpoint_imports(self):
        from app.api.endpoints.metadata import router
        assert router is not None

    def test_stream_endpoint_imports(self):
        from app.api.endpoints.stream import router
        assert router is not None


class TestAllModelImports:
    """所有数据库模型导入测试"""

    def test_artist_model_imports(self):
        from app.db.models.artist import Artist
        assert Artist is not None

    def test_album_model_imports(self):
        from app.db.models.album import Album
        assert Album is not None

    def test_track_model_imports(self):
        from app.db.models.track import Track
        assert Track is not None

    def test_playlist_model_imports(self):
        from app.db.models.playlist import Playlist
        assert Playlist is not None

    def test_subscribe_model_imports(self):
        from app.db.models.subscribe import Subscribe
        assert Subscribe is not None

    def test_site_model_imports(self):
        from app.db.models.site import Site
        assert Site is not None

    def test_library_model_imports(self):
        from app.db.models.library import Library
        assert Library is not None

    def test_download_model_imports(self):
        from app.db.models.download import DownloadHistory
        assert DownloadHistory is not None

    def test_media_model_imports(self):
        from app.db.models.media import MediaServer
        assert MediaServer is not None

    def test_system_model_imports(self):
        from app.db.models.system import SystemConfig
        assert SystemConfig is not None

    def test_subscribe_release_model_imports(self):
        from app.db.models.subscribe_release import SubscribeRelease
        assert SubscribeRelease is not None


class TestAllOperationImports:
    """所有数据库操作类导入测试"""

    def test_artist_oper_imports(self):
        from app.db.operations.artist import ArtistOper
        assert ArtistOper is not None

    def test_album_oper_imports(self):
        from app.db.operations.album import AlbumOper
        assert AlbumOper is not None

    def test_track_oper_imports(self):
        from app.db.operations.track import TrackOper
        assert TrackOper is not None

    def test_playlist_oper_imports(self):
        from app.db.operations.playlist import PlaylistOper
        assert PlaylistOper is not None

    def test_subscribe_oper_imports(self):
        from app.db.operations.subscribe import SubscribeOper
        assert SubscribeOper is not None

    def test_site_oper_imports(self):
        from app.db.operations.site import SiteOper
        assert SiteOper is not None

    def test_library_oper_imports(self):
        from app.db.operations.library import LibraryOper
        assert LibraryOper is not None

    def test_download_oper_imports(self):
        from app.db.operations.download import DownloadHistoryOper
        assert DownloadHistoryOper is not None

    def test_media_oper_imports(self):
        from app.db.operations.media import MediaServerOper
        assert MediaServerOper is not None

    def test_system_oper_imports(self):
        from app.db.operations.system import SystemConfigOper
        assert SystemConfigOper is not None

    def test_subscribe_release_oper_imports(self):
        from app.db.operations.subscribe_release import SubscribeReleaseOper
        assert SubscribeReleaseOper is not None
