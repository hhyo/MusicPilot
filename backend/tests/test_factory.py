"""
Factory 模块测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCreateApp:
    """create_app 测试类"""

    def test_create_app_basic(self):
        """测试创建基本应用"""
        with patch("app.factory.settings") as mock_settings:
            mock_settings.api_docs_enabled = True
            mock_settings.app_debug = False
            mock_settings.api_v1_prefix = "/api/v1"
            mock_settings.media_path = MagicMock()
            mock_settings.media_path.exists.return_value = False
            
            with patch("app.factory.lifespan"):
                from app.factory import create_app
                
                app = create_app()
                
                assert app.title == "MusicPilot"
                assert app.version == "0.1.0"

    def test_create_app_with_docs_disabled(self):
        """测试禁用 API 文档"""
        with patch("app.factory.settings") as mock_settings:
            mock_settings.api_docs_enabled = False
            mock_settings.app_debug = False
            mock_settings.api_v1_prefix = "/api/v1"
            mock_settings.media_path = MagicMock()
            mock_settings.media_path.exists.return_value = False
            
            with patch("app.factory.lifespan"):
                from app.factory import create_app
                
                app = create_app()
                
                assert app.docs_url is None
                assert app.redoc_url is None
