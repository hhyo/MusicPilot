"""
Chain 基类
提供链式业务逻辑处理的基础功能
"""

import time
from typing import Any

from app.core.event import EventType, event_bus
from app.core.log import logger
from app.core.module import ModuleManager
from app.core.plugin import PluginManager
from app.db import DatabaseManager
from app.db import db_manager as global_db_manager


class ChainBase:
    """
    Chain 基类

    所有业务逻辑链的基类，提供：
    - 模块管理（ModuleManager）访问
    - 插件管理（PluginManager）访问
    - 事件总线（EventBus）访问
    - 数据库会话管理
    - 缓存支持
    """

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        module_manager: ModuleManager | None = None,
        plugin_manager: PluginManager | None = None,
    ):
        """
        初始化 Chain 基类

        Args:
            db_manager: 数据库管理器，默认使用全局实例
            module_manager: 模块管理器，默认创建新实例
            plugin_manager: 插件管理器，默认创建新实例
        """
        self.logger = logger
        self.db_manager = db_manager or global_db_manager
        self.module_manager = module_manager or ModuleManager()
        self.plugin_manager = plugin_manager or PluginManager()
        self._cache: dict[str, tuple[Any, float | None]] = {}

    async def run_module(self, module_name: str, method: str, *args, **kwargs) -> Any:
        """
        运行指定模块的方法

        Args:
            module_name: 模块名称
            method: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            模块方法的返回值
        """
        return await self.module_manager.run_module(module_name, method, *args, **kwargs)

    async def run_plugin(self, plugin_name: str, method: str, *args, **kwargs) -> Any:
        """
        运行指定插件的方法

        Args:
            plugin_name: 插件名称
            method: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            插件方法的返回值
        """
        return await self.plugin_manager.run_plugin(plugin_name, method, *args, **kwargs)

    async def send_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """
        发送事件到事件总线

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        await event_bus.publish(event_type, data)

    async def put_message(self, event_type: EventType, data: dict[str, Any]) -> None:
        """
        发送消息（send_event 的别名）

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        await self.send_event(event_type, data)

    async def get_module(self, module_name: str) -> Any:
        """
        获取模块实例

        Args:
            module_name: 模块名称

        Returns:
            模块实例
        """
        return self.module_manager.get_module(module_name)

    async def get_plugin(self, plugin_name: str) -> Any:
        """
        获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            插件实例
        """
        return self.plugin_manager.get_plugin(plugin_name)

    def get_cache(self, key: str) -> Any | None:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或过期则返回 None
        """
        if key in self._cache:
            value, expires_at = self._cache[key]
            if expires_at is None or time.time() < expires_at:
                return value
            del self._cache[key]
        return None

    def set_cache(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示永不过期
        """
        expires_at = time.time() + ttl if ttl else None
        self._cache[key] = (value, expires_at)
