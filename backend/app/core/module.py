"""
模块管理器
管理所有系统模块的加载、启动、停止
"""

from importlib import import_module
from typing import Any

from app.core.log import logger


class ModuleBase:
    """
    模块基类
    所有系统模块都继承此类
    """

    # 模块类型（用于模块查找）
    module_type: str = "base"

    def __init__(self):
        self._enabled = False
        self._initialized = False
        self.logger = logger

    def init_module(self, config: dict[str, Any] | None = None):
        """
        初始化模块

        Args:
            config: 模块配置
        """
        if self._initialized:
            return

        self.logger.info(f"初始化模块: {self.__class__.__name__}")
        self._initialized = True
        self._enabled = True

    def stop_module(self):
        """停止模块"""
        self.logger.info(f"停止模块: {self.__class__.__name__}")
        self._enabled = False

    def is_enabled(self) -> bool:
        """模块是否启用"""
        return self._enabled

    def is_initialized(self) -> bool:
        """模块是否已初始化"""
        return self._initialized


class ModuleManager:
    """
    模块管理器
    管理所有系统模块的加载和运行
    """

    def __init__(self):
        self._modules: dict[str, ModuleBase] = {}
        self.logger = logger

    def register_module(self, module_id: str, module: ModuleBase):
        """
        注册模块

        Args:
            module_id: 模块 ID
            module: 模块实例
        """
        self._modules[module_id] = module
        self.logger.info(f"注册模块: {module_id} ({module.__class__.__name__})")

    def get_module(self, module_id: str) -> ModuleBase | None:
        """
        获取模块

        Args:
            module_id: 模块 ID

        Returns:
            模块实例
        """
        return self._modules.get(module_id)
    async def run_module(self, module_id: str, method: str, *args, **kwargs) -> Any:
        """
        运行模块的方法

        Args:
            module_id: 模块 ID
            method: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            方法返回值

        Raises:
            ValueError: 模块不存在或方法不存在
        """
        module = self.get_module(module_id)
        if not module:
            raise ValueError(f"模块不存在: {module_id}")

        method_func = getattr(module, method, None)
        if not method_func:
            raise ValueError(f"模块 {module_id} 没有方法 {method}")

        result = method_func(*args, **kwargs)
        # 支持异步方法
        import asyncio
        if asyncio.iscoroutine(result):
            return await result
        return result


    async def run_module(self, module_id: str, method: str, *args, **kwargs) -> Any:
        """
        运行模块的方法

        Args:
            module_id: 模块 ID
            method: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            方法返回值

        Raises:
            ValueError: 模块不存在或方法不存在
        """
        module = self.get_module(module_id)
        if not module:
            raise ValueError(f"模块不存在: {module_id}")

        method_func = getattr(module, method, None)
        if not method_func:
            raise ValueError(f"模块 {module_id} 没有方法 {method}")

        result = method_func(*args, **kwargs)
        # 支持异步方法
        import asyncio
        if asyncio.iscoroutine(result):
            return await result
        return result

    def get_running_modules(self) -> list[ModuleBase]:
        """
        获取所有运行的模块

        Returns:
            运行中的模块列表
        """
        return [module for module in self._modules.values() if module.is_enabled()]

    def get_running_modules_by_type(self, module_type: str) -> list[ModuleBase]:
        """
        获取指定类型的运行模块

        Args:
            module_type: 模块类型

        Returns:
            运行中的模块列表
        """
        return [
            module
            for module in self._modules.values()
            if module.is_enabled() and module.module_type == module_type
        ]

    def get_running_type_modules(self) -> dict[str, list[ModuleBase]]:
        """
        获取按类型分组的运行模块

        Returns:
            按类型分组的模块字典
        """
        result: dict[str, list[ModuleBase]] = {}
        for module in self.get_running_modules():
            if module.module_type not in result:
                result[module.module_type] = []
            result[module.module_type].append(module)
        return result

    def stop_module(self, module_id: str):
        """
        停止模块

        Args:
            module_id: 模块 ID
        """
        module = self.get_module(module_id)
        if module:
            module.stop_module()
            self.logger.info(f"模块已停止: {module_id}")

    def stop_all(self):
        """停止所有模块"""
        for module_id, module in self._modules.items():
            if module.is_enabled():
                module.stop_module()
                self.logger.info(f"模块已停止: {module_id}")

    def load_modules(self, module_configs: dict[str, dict[str, Any]]):
        """
        从配置加载模块

        Args:
            module_configs: 模块配置字典
        """
        self.logger.info(f"开始加载模块，共 {len(module_configs)} 个模块")

        for module_id, config in module_configs.items():
            try:
                # 动态导入模块
                module_path = config.get("module")
                if not module_path:
                    self.logger.warning(f"模块 {module_id} 缺少 module 路径配置")
                    continue

                module_class_path = f"app.modules.{module_path}"
                module_package = import_module(module_class_path)
                class_name = module_id.split("_")[0].capitalize() + "Module"
                module_class = getattr(module_package, class_name)

                # 创建模块实例
                module_instance = module_class()
                module_instance.init_module(config)

                # 注册模块
                self.register_module(module_id, module_instance)

            except Exception as e:
                self.logger.error(f"加载模块失败: {module_id}, 错误: {e}")

        self.logger.info(f"模块加载完成，成功加载 {len(self._modules)} 个模块")
