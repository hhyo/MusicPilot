"""
Subscribe API 完整测试
"""


class TestSubscribeAPIFull:
    """Subscribe API 完整测试"""

    def test_subscribe_router_imports(self):
        """测试 subscribe router 可导入"""
        from app.api.endpoints.subscribe import router

        assert router is not None

    def test_subscribe_module_imports(self):
        """测试 subscribe 模块可导入"""
        from app.api.endpoints import subscribe

        assert subscribe is not None

    def test_subscribe_routes_defined(self):
        """测试 subscribe 路由定义"""
        from app.api.endpoints.subscribe import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0
