"""
插件管理器
管理插件的启动、停止、重载、事件处理
"""

from typing import Dict, List, Optional, Any, Type
from pathlib import Path
import importlib.util
import sys

from app.core.log import logger
from app.core.event import EventManager


class PluginBase:
    """
    插件基类
    所有插件都继承此类
    """

    # 插件 ID
    plugin_id: str = "base"

    # 插件名称
    plugin_name: str = "Base Plugin"

    # 插件版本
    plugin_version: str = "1.0.0"

    # 插件描述
    plugin_desc: str = ""

    # 插件作者
    plugin_author: str = ""

    # 插件类型（用于插件查找）
    plugin_type: str = "base"

    # 插件优先级（数值越大优先级越高）
    plugin_order: int = 0

    # 是否启用事件处理
    enable_event_handler: bool = True

    # 监听的事件类型列表
    event_types: List[str] = []

    def __init__(self):
        self._enabled = False
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self.logger = logger

    def init_plugin(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化插件

        Args:
            config: 插件配置
        """
        if self._initialized:
            return

        self._config = config or {}
        self.logger.info(f"初始化插件: {self.plugin_name} v{self.plugin_version}")
        self._initialized = True

    def enable(self):
        """启用插件"""
        if not self._initialized:
            self.init_plugin()

        self._enabled = True
        self.logger.info(f"启用插件: {self.plugin_name}")

    def disable(self):
        """禁用插件"""
        self._enabled = False
        self.logger.info(f"禁用插件: {self.plugin_name}")

    def reload(self, config: Optional[Dict[str, Any]] = None):
        """
        重载插件

        Args:
            config: 新的插件配置
        """
        self.logger.info(f"重载插件: {self.plugin_name}")
        self.disable()
        self._initialized = False
        self.init_plugin(config)
        self.enable()

    def is_enabled(self) -> bool:
        """插件是否启用"""
        return self._enabled

    def is_initialized(self) -> bool:
        """插件是否已初始化"""
        return self._initialized

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取插件配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def handle_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        事件处理函数（子类可覆盖）

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        pass


class PluginManager:
    """
    插件管理器
    管理所有插件的加载、启动、停止、事件处理
    """

    def __init__(self, event_manager: EventManager):
        self._plugins: Dict[str, PluginBase] = {}
        self.event_manager = event_manager
        self.logger = logger

    def register_plugin(self, plugin: PluginBase):
        """
        注册插件

        Args:
            plugin: 插件实例
        """
        plugin_id = plugin.plugin_id
        self._plugins[plugin_id] = plugin
        self.logger.info(f"注册插件: {plugin_id} ({plugin.plugin_name} v{plugin.plugin_version})")

        # 注册事件处理器
        if plugin.enable_event_handler and plugin.event_types:
            for event_type in plugin.event_types:
                self.event_manager.register(event_type, plugin.handle_event)
                self.logger.debug(f"注册事件处理器: {plugin_id} -> {event_type}")

    def unregister_plugin(self, plugin_id: str):
        """
        取消注册插件

        Args:
            plugin_id: 插件 ID
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return

        # 取消注册事件处理器
        if plugin.enable_event_handler and plugin.event_types:
            for event_type in plugin.event_types:
                self.event_manager.unregister(event_type, plugin.handle_event)

        del self._plugins[plugin_id]
        self.logger.info(f"取消注册插件: {plugin_id}")

    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """
        获取插件

        Args:
            plugin_id: 插件 ID

        Returns:
            插件实例
        """
        return self._plugins.get(plugin_id)

    def get_running_plugins(self) -> List[PluginBase]:
        """
        获取所有运行的插件

        Returns:
            运行中的插件列表
        """
        return [plugin for plugin in self._plugins.values() if plugin.is_enabled()]

    def get_running_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """
        获取指定类型的运行插件，按优先级排序

        Args:
            plugin_type: 插件类型

        Returns:
            运行中的插件列表（按优先级降序）
        """
        plugins = [
            plugin
            for plugin in self._plugins.values()
            if plugin.is_enabled() and plugin.plugin_type == plugin_type
        ]
        # 按优先级降序排序
        plugins.sort(key=lambda p: p.plugin_order, reverse=True)
        return plugins

    def start(self, plugin_id: str):
        """
        启动插件

        Args:
            plugin_id: 插件 ID
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.enable()
            self.logger.info(f"插件已启动: {plugin_id}")

    def stop(self, plugin_id: str):
        """
        停止插件

        Args:
            plugin_id: 插件 ID
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.disable()
            self.logger.info(f"插件已停止: {plugin_id}")

    def reload(self, plugin_id: str, config: Optional[Dict[str, Any]] = None):
        """
        重载插件

        Args:
            plugin_id: 插件 ID
            config: 新的插件配置
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.reload(config)
            self.logger.info(f"插件已重载: {plugin_id}")

    def load_plugins_from_dir(self, plugin_dir: Path):
        """
        从目录加载插件

        Args:
            plugin_dir: 插件目录路径
        """
        if not plugin_dir.exists():
            self.logger.warning(f"插件目录不存在: {plugin_dir}")
            return

        self.logger.info(f"开始加载插件，目录: {plugin_dir}")

        for plugin_path in plugin_dir.glob("*/"):
            if not plugin_path.is_dir():
                continue

            # 查找插件主文件
            plugin_file = plugin_path / "__init__.py"
            if not plugin_file.exists():
                continue

            try:
                # 动态导入插件模块
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{plugin_path.name}", plugin_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"plugin_{plugin_path.name}"] = module
                    spec.loader.exec_module(module)

                    # 查找插件类
                    plugin_class = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, PluginBase)
                            and attr != PluginBase
                        ):
                            plugin_class = attr
                            break

                    if plugin_class:
                        plugin_instance = plugin_class()
                        plugin_instance.init_plugin()
                        self.register_plugin(plugin_instance)

            except Exception as e:
                self.logger.error(f"加载插件失败: {plugin_path.name}, 错误: {e}")

        self.logger.info(f"插件加载完成，成功加载 {len(self._plugins)} 个插件")
