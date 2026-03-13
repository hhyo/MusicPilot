"""
Covers API 测试
"""


class TestCoversAPI:
    """Covers API 测试"""

    def test_covers_router_imports(self):
        """测试 covers router 可导入"""
        from app.api.endpoints.covers import router

        assert router is not None

    def test_covers_module_imports(self):
        """测试 covers 模块可导入"""
        from app.api.endpoints import covers

        assert covers is not None
