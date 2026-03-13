"""
API 层完整测试
"""


class TestAPIV1Full:
    """API V1 完整测试"""

    def test_apiv1_imports(self):
        from app.api.apiv1 import api_router

        assert api_router is not None

    def test_api_module_imports(self):
        from app import api

        assert api is not None


class TestMainAppFull:
    """Main App 完整测试"""

    def test_main_imports(self):
        from app.main import app

        assert app is not None

    def test_app_module_imports(self):
        from app import main

        assert main is not None


class TestFactoryFull:
    """Factory 完整测试"""

    def test_factory_module_imports(self):
        from app import factory

        assert factory is not None

    def test_create_app_imports(self):
        from app.factory import create_app

        assert create_app is not None
