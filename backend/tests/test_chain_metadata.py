"""
MetadataChain 测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMetadataChain:
    """MetadataChain 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_metadata_chain_imports(self):
        """测试 MetadataChain 可导入"""
        from app.chain.metadata import MetadataChain
        assert MetadataChain is not None


class TestMetadataChainMethods:
    """MetadataChain 方法测试"""

    def test_metadata_chain_module_imports(self):
        """测试 metadata chain 模块可导入"""
        from app.chain import metadata
        assert metadata is not None
