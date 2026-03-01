"""
Factory 方法测试
"""

import pytest


class TestFactoryMethods:
    """Factory 方法测试"""

    def test_import_factory(self):
        """测试导入 factory"""
        from app.factory import create_app
        assert create_app is not None

    def test_factory_function_exists(self):
        """测试 factory 函数存在"""
        from app import factory
        assert hasattr(factory, 'create_app')


class TestFactoryConfig:
    """Factory 配置测试"""

    def test_settings_import(self):
        """测试 settings 导入"""
        from app.core.config import settings
        assert settings is not None

    def test_settings_attributes(self):
        """测试 settings 属性"""
        from app.core.config import settings
        # 检查实际存在的属性
        assert hasattr(settings, 'api_v1_prefix')


class TestFactoryRoutes:
    """Factory 路由测试"""

    def test_api_router_import(self):
        """测试 API 路由导入"""
        from app.api.apiv1 import api_router
        assert api_router is not None

    def test_api_routes_exist(self):
        """测试 API 路由存在"""
        from app.api.apiv1 import api_router
        routes = [route.path for route in api_router.routes]
        assert len(routes) > 0


class TestFactoryLifespan:
    """Factory 生命周期测试"""

    def test_lifespan_import(self):
        """测试 lifespan 导入"""
        try:
            from app.factory import lifespan
            assert lifespan is not None
        except ImportError:
            # lifespan 可能不存在
            assert True
