"""
Subscribe API 测试
"""


class TestSubscribeAPI:
    """Subscribe API 测试"""

    def test_subscribe_router_imports(self):
        """测试 subscribe router 可导入"""
        from app.api.endpoints.subscribe import router

        assert router is not None

    def test_subscribe_module_imports(self):
        """测试 subscribe 模块可导入"""
        from app.api.endpoints import subscribe

        assert subscribe is not None
