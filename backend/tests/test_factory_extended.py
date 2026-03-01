"""
Factory 扩展测试
"""

import pytest


class TestFactoryFunctions:
    """Factory 函数测试"""

    def test_create_app_import(self):
        """测试 create_app 导入"""
        from app.factory import create_app
        assert create_app is not None

    def test_lifespan_import(self):
        """测试 lifespan 导入"""
        from app.factory import lifespan
        assert lifespan is not None


class TestAppConfiguration:
    """应用配置测试"""

    def test_settings_import(self):
        """测试 settings 导入"""
        from app.core.config import settings
        assert settings is not None

    def test_api_prefix(self):
        """测试 API 前缀"""
        from app.core.config import settings
        assert hasattr(settings, 'api_v1_prefix')

    def test_media_path(self):
        """测试媒体路径"""
        from app.core.config import settings
        assert hasattr(settings, 'media_path')


class TestAppRoutes:
    """应用路由测试"""

    def test_api_router_import(self):
        """测试 API 路由导入"""
        from app.api.apiv1 import api_router
        assert api_router is not None

    def test_router_count(self):
        """测试路由数量"""
        from app.api.apiv1 import api_router
        routes = list(api_router.routes)
        assert len(routes) > 0
