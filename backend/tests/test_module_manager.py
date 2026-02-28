"""
ModuleManager 单元测试
"""

import pytest
from unittest.mock import MagicMock

from app.core.module import ModuleBase, ModuleManager


class TestModule(ModuleBase):
    """测试用模块"""

    module_type = "test"

    def test_method(self, value: str) -> str:
        """测试方法"""
        return f"processed: {value}"

    async def async_method(self, value: str) -> str:
        """异步测试方法"""
        return f"async processed: {value}"


class TestModuleBase:
    """ModuleBase 测试类"""

    def test_init(self):
        """测试初始化"""
        module = TestModule()
        assert not module._enabled
        assert not module._initialized

    def test_init_module(self):
        """测试模块初始化"""
        module = TestModule()
        module.init_module()
        assert module._enabled
        assert module._initialized

    def test_stop_module(self):
        """测试停止模块"""
        module = TestModule()
        module.init_module()
        module.stop_module()
        assert not module._enabled

    def test_is_enabled(self):
        """测试 is_enabled"""
        module = TestModule()
        assert not module.is_enabled()
        module.init_module()
        assert module.is_enabled()


class TestModuleManager:
    """ModuleManager 测试类"""

    def test_init(self):
        """测试初始化"""
        manager = ModuleManager()
        assert len(manager._modules) == 0

    def test_register_module(self):
        """测试注册模块"""
        manager = ModuleManager()
        module = TestModule()

        manager.register_module("test_module", module)

        assert "test_module" in manager._modules
        assert manager.get_module("test_module") == module

    def test_get_module_not_found(self):
        """测试获取不存在的模块"""
        manager = ModuleManager()
        assert manager.get_module("nonexistent") is None

    def test_get_running_modules(self):
        """测试获取运行中的模块"""
        manager = ModuleManager()
        module1 = TestModule()
        module2 = TestModule()

        module1.init_module()
        # module2 不初始化

        manager.register_module("module1", module1)
        manager.register_module("module2", module2)

        running = manager.get_running_modules()
        assert len(running) == 1
        assert running[0] == module1

    def test_stop_module(self):
        """测试停止模块"""
        manager = ModuleManager()
        module = TestModule()
        module.init_module()

        manager.register_module("test_module", module)
        manager.stop_module("test_module")

        assert not module.is_enabled()

    def test_stop_all(self):
        """测试停止所有模块"""
        manager = ModuleManager()
        module1 = TestModule()
        module2 = TestModule()

        module1.init_module()
        module2.init_module()

        manager.register_module("module1", module1)
        manager.register_module("module2", module2)

        manager.stop_all()

        assert not module1.is_enabled()
        assert not module2.is_enabled()

    @pytest.mark.asyncio
    async def test_run_module(self):
        """测试运行模块方法"""
        manager = ModuleManager()
        module = TestModule()
        module.init_module()

        manager.register_module("test_module", module)

        # 测试同步方法
        result = await manager.run_module("test_module", "test_method", "hello")
        assert result == "processed: hello"

        # 测试异步方法
        async_result = await manager.run_module("test_module", "async_method", "world")
        assert async_result == "async processed: world"

    @pytest.mark.asyncio
    async def test_run_module_not_found(self):
        """测试运行不存在的模块"""
        manager = ModuleManager()

        with pytest.raises(ValueError, match="模块不存在"):
            await manager.run_module("nonexistent", "test_method")

    @pytest.mark.asyncio
    async def test_run_module_method_not_found(self):
        """测试运行不存在的方法"""
        manager = ModuleManager()
        module = TestModule()
        module.init_module()

        manager.register_module("test_module", module)

        with pytest.raises(ValueError, match="没有方法"):
            await manager.run_module("test_module", "nonexistent_method")
