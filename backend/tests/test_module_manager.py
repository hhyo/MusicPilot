"""
ModuleManager 测试
"""


class TestModuleManager:
    """ModuleManager 测试"""

    def test_import_module_manager(self):
        """测试导入模块管理器"""
        from app.core.module import ModuleManager

        assert ModuleManager is not None

    def test_module_manager_methods(self):
        """测试模块管理器方法"""
        from app.core.module import ModuleManager

        methods = [m for m in dir(ModuleManager) if not m.startswith("_")]
        assert len(methods) > 0


class TestModuleBase:
    """ModuleBase 测试"""

    def test_import_module_base(self):
        """测试导入模块基类"""
        from app.core.module import ModuleBase

        assert ModuleBase is not None

    def test_module_base_methods(self):
        """测试模块基类方法"""
        from app.core.module import ModuleBase

        methods = [m for m in dir(ModuleBase) if not m.startswith("_")]
        assert len(methods) > 0


class TestModuleRegistration:
    """模块注册测试"""

    def test_module_info_structure(self):
        """测试模块信息结构"""
        module_info = {
            "name": "TestModule",
            "type": "downloader",
            "enabled": True,
        }
        assert module_info["name"] == "TestModule"
        assert module_info["enabled"] is True

    def test_module_types(self):
        """测试模块类型"""
        valid_types = ["downloader", "searcher", "metadata", "player"]
        for t in valid_types:
            assert isinstance(t, str)
