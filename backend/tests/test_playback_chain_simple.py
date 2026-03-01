"""
PlaybackChain 简单测试
"""

import pytest


class TestPlaybackChainSimple:
    """PlaybackChain 简单测试"""

    @pytest.mark.asyncio
    async def test_playback_chain_imports(self):
        """测试 PlaybackChain 可导入"""
        from app.chain.playback import PlaybackChain
        assert PlaybackChain is not None

    def test_playback_chain_module(self):
        """测试 playback chain 模块"""
        from app.chain import playback
        assert playback is not None
