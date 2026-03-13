"""
PlaybackChain 导入测试
"""


class TestPlaybackChainImport:
    """PlaybackChain 导入测试"""

    def test_playback_chain_imports(self):
        """测试 PlaybackChain 可导入"""
        from app.chain.playback import PlaybackChain

        assert PlaybackChain is not None

    def test_playback_chain_module_imports(self):
        """测试 playback chain 模块可导入"""
        from app.chain import playback

        assert playback is not None
