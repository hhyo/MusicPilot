"""
Playback 完整测试
"""
import pytest


class TestPlaybackChain:
    def test_imports(self):
        from app.chain.playback import PlaybackChain
        assert PlaybackChain is not None

    def test_module(self):
        from app.chain import playback
        assert playback is not None


class TestPlaybackSession:
    def test_imports(self):
        from app.core.context import PlaybackSession
        assert PlaybackSession is not None
