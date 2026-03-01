"""
Context 模型测试
"""

import pytest


class TestMusicInfo:
    """MusicInfo 测试"""

    def test_music_info_creation(self):
        """测试 MusicInfo 创建"""
        from app.core.context import MusicInfo
        info = MusicInfo(
            artist="Test Artist",
            album="Test Album",
            title="Test Song",
        )
        assert info.artist == "Test Artist"
        assert info.album == "Test Album"
        assert info.title == "Test Song"

    def test_music_info_optional_fields(self):
        """测试 MusicInfo 可选字段"""
        from app.core.context import MusicInfo
        info = MusicInfo(title="Test")
        assert info.title == "Test"


class TestDownloadTask:
    """DownloadTask 测试"""

    def test_download_task_creation(self):
        """测试 DownloadTask 创建"""
        from app.core.context import DownloadTask
        task = DownloadTask(
            task_id="test-1",
            save_path="/downloads",
            source="netease",
        )
        assert task.task_id == "test-1"
        assert task.source == "netease"


class TestPlaybackSession:
    """PlaybackSession 测试"""

    def test_playback_session_creation(self):
        """测试 PlaybackSession 创建"""
        from app.core.context import PlaybackSession
        session = PlaybackSession(
            session_id="session-1",
            track_id=1,
        )
        assert session.session_id == "session-1"
        assert session.track_id == 1

    def test_playback_session_defaults(self):
        """测试 PlaybackSession 默认值"""
        from app.core.context import PlaybackSession
        session = PlaybackSession(
            session_id="session-1",
            track_id=1,
        )
        assert session.volume == 1.0
        assert session.muted is False
        assert session.repeat_mode == "off"


class TestContextModule:
    """Context 模块测试"""

    def test_context_import(self):
        """测试 context 模块导入"""
        from app.core import context
        assert context is not None

    def test_context_classes(self):
        """测试 context 类"""
        from app.core.context import MusicInfo, DownloadTask, PlaybackSession
        assert MusicInfo is not None
        assert DownloadTask is not None
        assert PlaybackSession is not None
