"""
Player API 完整测试
"""


class TestPlayerAPIFull:
    """Player API 完整测试"""

    def test_player_router_imports(self):
        """测试 player router 可导入"""
        from app.api.endpoints.player import router

        assert router is not None

    def test_player_module_imports(self):
        """测试 player 模块可导入"""
        from app.api.endpoints import player

        assert player is not None

    def test_player_routes_defined(self):
        """测试 player 路由定义"""
        from app.api.endpoints.player import router

        routes = [route.path for route in router.routes]
        assert len(routes) > 0
