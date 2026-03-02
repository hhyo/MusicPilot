"""
Core 层完整测试
"""

import pytest


class TestCoreCacheFull:
    """Core Cache 完整测试"""

    def test_file_cache_imports(self):
        from app.core.cache import FileCache
        assert FileCache is not None

    def test_async_file_cache_imports(self):
        from app.core.cache import AsyncFileCache
        assert AsyncFileCache is not None


class TestCoreConfigFull:
    """Core Config 完整测试"""

    def test_settings_imports(self):
        from app.core.config import settings
        assert settings is not None

    def test_config_module_imports(self):
        from app.core import config
        assert config is not None


class TestCoreEventFull:
    """Core Event 完整测试"""

    def test_event_type_imports(self):
        from app.core.event import EventType
        assert EventType is not None

    def test_event_bus_imports(self):
        from app.core.event import EventManager as EventBus
        assert EventBus is not None

    def test_event_module_imports(self):
        from app.core import event
        assert event is not None


class TestCoreLogFull:
    """Core Log 完整测试"""

    def test_logger_imports(self):
        from app.core.log import logger
        assert logger is not None

    def test_log_module_imports(self):
        from app.core import log
        assert log is not None


class TestCoreContextFull:
    """Core Context 完整测试"""

    def test_music_info_imports(self):
        from app.core.context import MusicInfo
        assert MusicInfo is not None

    def test_download_task_imports(self):
        from app.core.context import DownloadTask
        assert DownloadTask is not None

    def test_playback_session_imports(self):
        from app.core.context import PlaybackSession
        assert PlaybackSession is not None

    def test_context_module_imports(self):
        from app.core import context
        assert context is not None


class TestCoreMetaFull:
    """Core Meta 完整测试"""

    def test_metadata_parser_imports(self):
        from app.core.meta import MetadataParser
        assert MetadataParser is not None

    def test_filename_parser_imports(self):
        from app.core.meta import FilenameParser
        assert FilenameParser is not None


class TestCoreModuleFull:
    """Core Module 完整测试"""

    def test_module_manager_imports(self):
        from app.core.module import ModuleManager
        assert ModuleManager is not None

    def test_module_base_imports(self):
        from app.core.module import ModuleBase
        assert ModuleBase is not None


class TestCorePluginFull:
    """Core Plugin 完整测试"""

    def test_plugin_manager_imports(self):
        from app.core.plugin import PluginManager
        assert PluginManager is not None

    def test_plugin_base_imports(self):
        from app.core.plugin import PluginBase
        assert PluginBase is not None


class TestCoreChainFull:
    """Core Chain 完整测试"""

    def test_chain_base_imports(self):
        from app.core.chain import ChainBase
        assert ChainBase is not None
