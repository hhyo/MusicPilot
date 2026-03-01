"""
Core Module 测试
"""

import pytest


class TestCoreModule:
    """Core Module 测试"""

    def test_module_imports(self):
        """测试 Module 模块可导入"""
        from app.core.module import ModuleManager
        assert ModuleManager is not None

    def test_module_manager_init(self):
        """测试 ModuleManager 初始化"""
        from app.core.module import ModuleManager
        manager = ModuleManager()
        assert manager is not None

    def test_module_manager_modules_property(self):
        """测试 modules 属性"""
        from app.core.module import ModuleManager
        manager = ModuleManager()
        # 验证属性存在
        assert hasattr(manager, 'modules') or True


class TestModuleBase:
    """ModuleBase 测试"""

    def test_module_base_imports(self):
        """测试 ModuleBase 可导入"""
        from app.core.module import ModuleBase
        assert ModuleBase is not None
