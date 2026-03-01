"""
Core 模块扩展测试
"""

import pytest


class TestCoreCache:
    """Core Cache 测试"""

    def test_cache_import(self):
        """测试缓存模块导入"""
        from app.core.cache import AsyncFileCache
        assert AsyncFileCache is not None

    def test_cache_config(self, tmp_path):
        """测试缓存配置"""
        from app.core.cache import AsyncFileCache
        cache = AsyncFileCache(str(tmp_path), default_ttl=3600)
        assert cache.default_ttl == 3600


class TestCoreConfig:
    """Core Config 测试"""

    def test_config_import(self):
        """测试配置模块导入"""
        from app.core.config import settings
        assert settings is not None

    def test_config_defaults(self):
        """测试配置默认值"""
        from app.core.config import settings
        assert hasattr(settings, 'api_v1_prefix')


class TestCoreEvent:
    """Core Event 测试"""

    def test_event_bus_import(self):
        """测试事件总线导入"""
        from app.core.event import event_bus
        assert event_bus is not None

    def test_event_type_import(self):
        """测试事件类型导入"""
        from app.core.event import EventType
        assert EventType is not None


class TestCoreLog:
    """Core Log 测试"""

    def test_logger_import(self):
        """测试日志模块导入"""
        from app.core.log import logger
        assert logger is not None


class TestCoreModule:
    """Core Module 测试"""

    def test_module_manager_import(self):
        """测试模块管理器导入"""
        from app.core.module import ModuleManager
        assert ModuleManager is not None


class TestCorePlugin:
    """Core Plugin 测试"""

    def test_plugin_manager_import(self):
        """测试插件管理器导入"""
        from app.core.plugin import PluginManager
        assert PluginManager is not None


class TestCoreChain:
    """Core Chain 测试"""

    def test_chain_base_import(self):
        """测试 Chain 基类导入"""
        from app.core.chain import ChainBase
        assert ChainBase is not None
