"""
Library API 完整测试
"""


class TestLibraryAPIFull:
    """Library API 完整测试"""

    def test_library_router_imports(self):
        """测试 library router 可导入"""
        from app.api.endpoints.library import router

        assert router is not None

    def test_library_module_imports(self):
        """测试 library 模块可导入"""
        from app.api.endpoints import library

        assert library is not None

    def test_library_routes_defined(self):
        """测试 library 路由定义"""
        from app.api.endpoints.library import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0
