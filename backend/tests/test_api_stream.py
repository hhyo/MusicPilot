"""
Stream API 测试
"""


class TestStreamAPI:
    """Stream API 测试"""

    def test_stream_router_imports(self):
        """测试 stream router 可导入"""
        from app.api.endpoints.stream import router

        assert router is not None

    def test_stream_module_imports(self):
        """测试 stream 模块可导入"""
        from app.api.endpoints import stream

        assert stream is not None
