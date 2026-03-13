"""
API 端点基础测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAPIEndpointsBasic:
    """API 端点基础测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    def test_album_router_imports(self):
        """测试 album router 可导入"""
        from app.api.endpoints.album import router

        assert router is not None

    def test_artist_router_imports(self):
        """测试 artist router 可导入"""
        from app.api.endpoints.artist import router

        assert router is not None

    def test_track_router_imports(self):
        """测试 track router 可导入"""
        from app.api.endpoints.track import router

        assert router is not None

    def test_playlist_router_imports(self):
        """测试 playlist router 可导入"""
        from app.api.endpoints.playlist import router

        assert router is not None

    def test_library_router_imports(self):
        """测试 library router 可导入"""
        from app.api.endpoints.library import router

        assert router is not None

    def test_subscribe_router_imports(self):
        """测试 subscribe router 可导入"""
        from app.api.endpoints.subscribe import router

        assert router is not None

    def test_site_router_imports(self):
        """测试 site router 可导入"""
        from app.api.endpoints.site import router

        assert router is not None

    def test_player_router_imports(self):
        """测试 player router 可导入"""
        from app.api.endpoints.player import router

        assert router is not None

    def test_covers_router_imports(self):
        """测试 covers router 可导入"""
        from app.api.endpoints.covers import router

        assert router is not None

    def test_metadata_router_imports(self):
        """测试 metadata router 可导入"""
        from app.api.endpoints.metadata import router

        assert router is not None

    def test_stream_router_imports(self):
        """测试 stream router 可导入"""
        from app.api.endpoints.stream import router

        assert router is not None

    def test_subscribe_release_router_imports(self):
        """测试 subscribe_release router 可导入"""
        from app.api.endpoints.subscribe_release import router

        assert router is not None


class TestAPIRouterRoutes:
    """API 路由测试"""

    def test_album_routes_defined(self):
        """测试 album 路由定义"""
        from app.api.endpoints.album import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0

    def test_artist_routes_defined(self):
        """测试 artist 路由定义"""
        from app.api.endpoints.artist import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0

    def test_track_routes_defined(self):
        """测试 track 路由定义"""
        from app.api.endpoints.track import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0

    def test_playlist_routes_defined(self):
        """测试 playlist 路由定义"""
        from app.api.endpoints.playlist import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0
