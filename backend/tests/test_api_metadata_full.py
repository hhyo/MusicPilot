"""
Metadata API 完整测试
"""

import pytest


class TestMetadataAPIFull:
    """Metadata API 完整测试"""

    def test_metadata_router_imports(self):
        """测试 metadata router 可导入"""
        from app.api.endpoints.metadata import router
        assert router is not None

    def test_metadata_module_imports(self):
        """测试 metadata 模块可导入"""
        from app.api.endpoints import metadata
        assert metadata is not None

    def test_metadata_routes_defined(self):
        """测试 metadata 路由定义"""
        from app.api.endpoints.metadata import router
        routes = [route.path for route in router.routes]
        assert len(routes) > 0
