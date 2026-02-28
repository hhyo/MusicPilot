"""
PluginManager 单元测试
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.core.plugin import PluginBase, PluginManager


class TestPlugin(PluginBase):
    """测试用插件"""

    plugin_id = "test_plugin"
    plugin_name = "Test Plugin"
    plugin_version = "1.0.0"
    plugin_type = "test"
    plugin_order = 10
    event_types = ["test_event"]

    def handle_event(self, event_type: str, data: dict | None = None):
        """事件处理"""
        return f"handled: {event_type}"


class TestPluginBase:
    """PluginBase 测试类"""

    def test_init(self):
        """测试初始化"""
        plugin = TestPlugin()
        assert not plugin._enabled
        assert not plugin._initialized
        assert plugin.plugin_id == "test_plugin"

    def test_init_plugin(self):
        """测试插件初始化"""
        plugin = TestPlugin()
        plugin.init_plugin()
        assert plugin._initialized

    def test_enable_disable(self):
        """测试启用/禁用"""
        plugin = TestPlugin()
        plugin.enable()
        assert plugin.is_enabled()

        plugin.disable()
        assert not plugin.is_enabled()

    def test_reload(self):
        """测试重载"""
        plugin = TestPlugin()
        plugin.init_plugin({"key": "value"})
        plugin.enable()

        plugin.reload({"key": "new_value"})

        assert plugin.is_enabled()
        assert plugin.get_config("key") == "new_value"

    def test_get_config(self):
        """测试获取配置"""
        plugin = TestPlugin()
        plugin.init_plugin({"key": "value"})

        assert plugin.get_config("key") == "value"
        assert plugin.get_config("nonexistent", "default") == "default"


class TestPluginManager:
    """PluginManager 测试类"""

    def test_init_without_event_manager(self):
        """测试无 event_manager 初始化"""
        manager = PluginManager()
        assert manager.event_manager is None
        assert len(manager._plugins) == 0

    def test_init_with_event_manager(self):
        """测试有 event_manager 初始化"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        assert manager.event_manager == mock_event_manager

    def test_register_plugin_with_event_manager(self):
        """测试注册插件（有 event_manager）"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        plugin = TestPlugin()
        plugin.enable_event_handler = True

        manager.register_plugin(plugin)

        assert "test_plugin" in manager._plugins
        assert manager.get_plugin("test_plugin") == plugin
        # 验证事件注册被调用
        mock_event_manager.register.assert_called()

    def test_register_plugin_without_event_manager(self):
        """测试注册插件（无 event_manager，不启用事件处理）"""
        manager = PluginManager()
        plugin = TestPlugin()
        plugin.enable_event_handler = False  # 不启用事件处理

        manager.register_plugin(plugin)

        assert "test_plugin" in manager._plugins
        assert manager.get_plugin("test_plugin") == plugin

    def test_unregister_plugin_with_event_manager(self):
        """测试取消注册插件（有 event_manager）"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        plugin = TestPlugin()
        plugin.enable_event_handler = True

        manager.register_plugin(plugin)
        manager.unregister_plugin("test_plugin")

        assert "test_plugin" not in manager._plugins
        mock_event_manager.unregister.assert_called()

    def test_get_plugin_not_found(self):
        """测试获取不存在的插件"""
        manager = PluginManager()
        assert manager.get_plugin("nonexistent") is None

    def test_get_running_plugins(self):
        """测试获取运行中的插件"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        
        plugin1 = TestPlugin()
        plugin1.plugin_id = "plugin1"
        plugin1.enable_event_handler = False
        plugin2 = TestPlugin()
        plugin2.plugin_id = "plugin2"
        plugin2.enable_event_handler = False

        plugin1.enable()
        # plugin2 不启用

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        running = manager.get_running_plugins()
        assert len(running) == 1
        assert running[0] == plugin1

    def test_get_running_plugins_by_type(self):
        """测试按类型获取运行中的插件"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        
        plugin1 = TestPlugin()
        plugin1.plugin_id = "plugin1"
        plugin1.plugin_type = "type1"
        plugin1.enable_event_handler = False
        plugin2 = TestPlugin()
        plugin2.plugin_id = "plugin2"
        plugin2.plugin_type = "type2"
        plugin2.enable_event_handler = False

        plugin1.enable()
        plugin2.enable()

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        running = manager.get_running_plugins_by_type("type1")
        assert len(running) == 1
        assert running[0] == plugin1

    def test_start_stop(self):
        """测试启动和停止插件"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        plugin = TestPlugin()
        plugin.enable_event_handler = False

        manager.register_plugin(plugin)
        manager.start("test_plugin")
        assert plugin.is_enabled()

        manager.stop("test_plugin")
        assert not plugin.is_enabled()

    def test_reload(self):
        """测试重载插件"""
        mock_event_manager = MagicMock()
        manager = PluginManager(event_manager=mock_event_manager)
        plugin = TestPlugin()
        plugin.enable_event_handler = False

        manager.register_plugin(plugin)
        manager.start("test_plugin")
        manager.reload("test_plugin", {"key": "value"})

        assert plugin.is_enabled()
        assert plugin.get_config("key") == "value"
