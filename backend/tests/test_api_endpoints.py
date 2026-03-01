"""
API 端点测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAlbumEndpoint:
    """专辑端点测试"""

    @pytest.mark.asyncio
    async def test_get_albums_endpoint(self):
        """测试获取专辑列表"""
        from app.api.endpoints.album import router
        assert router is not None

    def test_album_router_routes(self):
        """测试专辑路由"""
        from app.api.endpoints.album import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestArtistEndpoint:
    """艺术家端点测试"""

    def test_artist_router(self):
        """测试艺术家路由"""
        from app.api.endpoints.artist import router
        assert router is not None

    def test_artist_routes(self):
        """测试艺术家路由列表"""
        from app.api.endpoints.artist import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestTrackEndpoint:
    """曲目端点测试"""

    def test_track_router(self):
        """测试曲目路由"""
        from app.api.endpoints.track import router
        assert router is not None

    def test_track_routes(self):
        """测试曲目路由列表"""
        from app.api.endpoints.track import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestPlaylistEndpoint:
    """播放列表端点测试"""

    def test_playlist_router(self):
        """测试播放列表路由"""
        from app.api.endpoints.playlist import router
        assert router is not None

    def test_playlist_routes(self):
        """测试播放列表路由列表"""
        from app.api.endpoints.playlist import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestLibraryEndpoint:
    """媒体库端点测试"""

    def test_library_router(self):
        """测试媒体库路由"""
        from app.api.endpoints.library import router
        assert router is not None

    def test_library_routes(self):
        """测试媒体库路由列表"""
        from app.api.endpoints.library import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestMetadataEndpoint:
    """元数据端点测试"""

    def test_metadata_router(self):
        """测试元数据路由"""
        from app.api.endpoints.metadata import router
        assert router is not None

    def test_metadata_routes(self):
        """测试元数据路由列表"""
        from app.api.endpoints.metadata import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestSiteEndpoint:
    """站点端点测试"""

    def test_site_router(self):
        """测试站点路由"""
        from app.api.endpoints.site import router
        assert router is not None

    def test_site_routes(self):
        """测试站点路由列表"""
        from app.api.endpoints.site import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestSubscribeEndpoint:
    """订阅端点测试"""

    def test_subscribe_router(self):
        """测试订阅路由"""
        from app.api.endpoints.subscribe import router
        assert router is not None

    def test_subscribe_routes(self):
        """测试订阅路由列表"""
        from app.api.endpoints.subscribe import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0


class TestPlayerEndpoint:
    """播放器端点测试"""

    def test_player_router(self):
        """测试播放器路由"""
        from app.api.endpoints.player import router
        assert router is not None

    def test_player_routes(self):
        """测试播放器路由列表"""
        from app.api.endpoints.player import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0
