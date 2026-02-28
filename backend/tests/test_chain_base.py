"""
ChainBase 单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestChainBase:
    """ChainBase 测试类"""

    @pytest.mark.asyncio
    async def test_chain_base_init(self):
        """测试 ChainBase 初始化"""
        from app.core.chain import ChainBase

        # 创建测试用的 ChainBase 子类
        class TestChain(ChainBase):
            pass

        chain = TestChain()
        assert chain.logger is not None
        assert chain.db_manager is not None
        assert chain.module_manager is not None
        assert chain.plugin_manager is not None

    @pytest.mark.asyncio
    async def test_run_module(self):
        """测试 run_module 方法"""
        from app.core.chain import ChainBase
        from app.core.module import ModuleManager

        # Mock ModuleManager
        mock_manager = MagicMock(spec=ModuleManager)
        mock_manager.run_module = AsyncMock(return_value="test_result")

        class TestChain(ChainBase):
            pass

        chain = TestChain(module_manager=mock_manager)
        result = await chain.run_module("test_module", "test_method", arg1="value1")

        mock_manager.run_module.assert_called_once_with(
            "test_module", "test_method", arg1="value1"
        )
        assert result == "test_result"

    @pytest.mark.asyncio
    async def test_run_plugin(self):
        """测试 run_plugin 方法"""
        from app.core.chain import ChainBase
        from app.core.plugin import PluginManager

        # Mock PluginManager
        mock_manager = MagicMock(spec=PluginManager)
        mock_manager.run_plugin = AsyncMock(return_value="plugin_result")

        class TestChain(ChainBase):
            pass

        chain = TestChain(plugin_manager=mock_manager)
        result = await chain.run_plugin("test_plugin", "test_method")

        mock_manager.run_plugin.assert_called_once()
        assert result == "plugin_result"

    @pytest.mark.asyncio
    async def test_send_event(self):
        """测试 send_event 方法"""
        from app.core.chain import ChainBase
        from app.core.event import EventType

        with patch("app.core.chain.event_bus") as mock_event_bus:
            mock_event_bus.publish = AsyncMock()

            class TestChain(ChainBase):
                pass

            chain = TestChain()
            await chain.send_event(EventType.PLAYER_PLAY, {"track_id": 1})

            mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_module(self):
        """测试 get_module 方法"""
        from app.core.chain import ChainBase
        from app.core.module import ModuleManager, ModuleBase

        # Mock ModuleManager
        mock_module = MagicMock(spec=ModuleBase)
        mock_manager = MagicMock(spec=ModuleManager)
        mock_manager.get_module = MagicMock(return_value=mock_module)

        class TestChain(ChainBase):
            pass

        chain = TestChain(module_manager=mock_manager)
        result = await chain.get_module("test_module")

        mock_manager.get_module.assert_called_once_with("test_module")
        assert result == mock_module
