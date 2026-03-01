"""
MusicBrainzChain 测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMusicBrainzChain:
    """MusicBrainzChain 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_musicbrainz_chain_imports(self):
        """测试 MusicBrainzChain 可导入"""
        from app.chain.musicbrainz import MusicBrainzChain
        assert MusicBrainzChain is not None


class TestMusicBrainzChainMethods:
    """MusicBrainzChain 方法测试"""

    def test_musicbrainz_chain_module_imports(self):
        """测试 musicbrainz chain 模块可导入"""
        from app.chain import musicbrainz
        assert musicbrainz is not None
