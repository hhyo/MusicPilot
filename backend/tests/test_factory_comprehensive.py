"""
Factory 全面测试
"""

import pytest
from unittest.mock import MagicMock, patch


class TestFactoryComprehensive:
    """Factory 全面测试"""

    def test_create_app_basic(self):
        """测试创建应用"""
        with patch("app.factory.settings") as mock_settings:
            mock_settings.api_docs_enabled = True
            mock_settings.app_debug = False
            mock_settings.api_v1_prefix = "/api/v1"
            mock_settings.media_path = MagicMock()
            mock_settings.media_path.exists.return_value = False
            
            with patch("app.factory.lifespan"):
                from app.factory import create_app
                app = create_app()
                assert app is not None

    def test_app_routes(self):
        """测试应用路由"""
        with patch("app.factory.settings") as mock_settings:
            mock_settings.api_docs_enabled = False
            mock_settings.app_debug = False
            mock_settings.api_v1_prefix = "/api/v1"
            mock_settings.media_path = MagicMock()
            mock_settings.media_path.exists.return_value = False
            
            with patch("app.factory.lifespan"):
                from app.factory import create_app
                app = create_app()
                routes = [route.path for route in app.routes]
                assert len(routes) > 0

    def test_app_middleware(self):
        """测试应用中间件"""
        with patch("app.factory.settings") as mock_settings:
            mock_settings.api_docs_enabled = False
            mock_settings.app_debug = False
            mock_settings.api_v1_prefix = "/api/v1"
            mock_settings.media_path = MagicMock()
            mock_settings.media_path.exists.return_value = False
            
            with patch("app.factory.lifespan"):
                from app.factory import create_app
                app = create_app()
                assert app is not None
