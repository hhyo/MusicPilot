"""
Library API 测试
"""


class TestLibraryAPI:
    """Library API 测试"""

    def test_library_router_imports(self):
        """测试 library router 可导入"""
        from app.api.endpoints.library import router

        assert router is not None

    def test_library_module_imports(self):
        """测试 library 模块可导入"""
        from app.api.endpoints import library

        assert library is not None
