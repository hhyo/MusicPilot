"""
Main 模块测试
"""


class TestMainModule:
    """Main 模块测试"""

    def test_main_import(self):
        """测试 main 模块导入"""
        from app import main

        assert main is not None


class TestAppCreation:
    """应用创建测试"""

    def test_factory_import(self):
        """测试 factory 模块导入"""
        from app.factory import create_app

        assert create_app is not None
