"""
Metadata API 测试
"""

import pytest


class TestMetadataAPI:
    """Metadata API 测试"""

    def test_metadata_router_imports(self):
        """测试 metadata router 可导入"""
        from app.api.endpoints.metadata import router
        assert router is not None

    def test_metadata_module_imports(self):
        """测试 metadata 模块可导入"""
        from app.api.endpoints import metadata
        assert metadata is not None
