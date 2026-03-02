"""
API 端点详细测试
"""
import pytest


class TestAlbumAPI:
    def test_router(self):
        from app.api.endpoints.album import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.album import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestArtistAPI:
    def test_router(self):
        from app.api.endpoints.artist import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.artist import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestTrackAPI:
    def test_router(self):
        from app.api.endpoints.track import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.track import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestPlaylistAPI:
    def test_router(self):
        from app.api.endpoints.playlist import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.playlist import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestSubscribeAPI:
    def test_router(self):
        from app.api.endpoints.subscribe import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.subscribe import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestSiteAPI:
    def test_router(self):
        from app.api.endpoints.site import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.site import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestPlayerAPI:
    def test_router(self):
        from app.api.endpoints.player import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.player import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestStreamAPI:
    def test_router(self):
        from app.api.endpoints.stream import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.stream import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestCoversAPI:
    def test_router(self):
        from app.api.endpoints.covers import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.covers import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestMetadataAPI:
    def test_router(self):
        from app.api.endpoints.metadata import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.metadata import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestLibraryAPI:
    def test_router(self):
        from app.api.endpoints.library import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.library import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestSubscribeReleaseAPI:
    def test_router(self):
        from app.api.endpoints.subscribe_release import router
        assert router is not None

    def test_routes(self):
        from app.api.endpoints.subscribe_release import router
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        assert len(routes) > 0


class TestAPIRouter:
    def test_apiv1(self):
        from app.api import apiv1
        assert apiv1 is not None
