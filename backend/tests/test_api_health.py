"""
API 健康检查测试
"""

import pytest
from fastapi.testclient import TestClient


class TestAPIHealthCheck:
    """API 健康检查测试"""

    def test_health_endpoint_exists(self):
        """测试健康检查端点存在"""
        # 简单验证 API 结构
        from app.api.apiv1 import api_router
        assert api_router is not None

    def test_api_router_routes(self):
        """测试 API 路由"""
        from app.api.apiv1 import api_router
        routes = [route.path for route in api_router.routes]
        # 验证主要路由存在
        assert len(routes) > 0


class TestAPIEndpointStructure:
    """API 端点结构测试"""

    def test_album_endpoint_import(self):
        """测试专辑端点导入"""
        from app.api.endpoints import album
        assert album is not None

    def test_artist_endpoint_import(self):
        """测试艺术家端点导入"""
        from app.api.endpoints import artist
        assert artist is not None

    def test_track_endpoint_import(self):
        """测试曲目端点导入"""
        from app.api.endpoints import track
        assert track is not None

    def test_playlist_endpoint_import(self):
        """测试播放列表端点导入"""
        from app.api.endpoints import playlist
        assert playlist is not None

    def test_library_endpoint_import(self):
        """测试媒体库端点导入"""
        from app.api.endpoints import library
        assert library is not None

    def test_metadata_endpoint_import(self):
        """测试元数据端点导入"""
        from app.api.endpoints import metadata
        assert metadata is not None


class TestAPISchemaStructure:
    """API Schema 结构测试"""

    def test_response_model_structure(self):
        """测试响应模型结构"""
        from app.schemas.response import ResponseModel, PaginatedResponse
        assert ResponseModel is not None
        assert PaginatedResponse is not None

    def test_album_schema_import(self):
        """测试专辑 Schema 导入"""
        from app.schemas.album import AlbumBase, AlbumResponse
        assert AlbumBase is not None
        assert AlbumResponse is not None

    def test_artist_schema_import(self):
        """测试艺术家 Schema 导入"""
        from app.schemas.artist import ArtistBase, ArtistResponse
        assert ArtistBase is not None
        assert ArtistResponse is not None

    def test_track_schema_import(self):
        """测试曲目 Schema 导入"""
        from app.schemas.track import TrackBase, TrackResponse
        assert TrackBase is not None
        assert TrackResponse is not None
