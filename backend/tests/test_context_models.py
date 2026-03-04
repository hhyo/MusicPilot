"""
Context 模型测试
"""

from datetime import UTC


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

        info = MusicInfo(title="Test Song")
        assert info.title == "Test Song"
        assert info.artist is None
        assert info.album is None


class TestDownloadTask:
    """DownloadTask 测试"""

    def test_download_task_creation(self):
        """测试 DownloadTask 创建"""
        from app.core.context import DownloadTask

        task = DownloadTask(
            task_id="test-1",
            save_path="/downloads",
            source="test",
        )
        assert task.task_id == "test-1"
        assert task.save_path == "/downloads"
        assert task.source == "test"

    def test_download_task_progress(self):
        """测试 DownloadTask 进度"""
        from app.core.context import DownloadTask

        task = DownloadTask(
            task_id="test-1",
            save_path="/downloads",
            source="test",
            downloaded_size=512000,
            total_size=1024000,
        )
        assert task.downloaded_size == 512000
        assert task.total_size == 1024000


class TestPlaybackSession:
    """PlaybackSession 测试"""

    def test_playback_session_creation(self):
        """测试 PlaybackSession 创建"""
        from datetime import datetime

        from app.core.context import PlaybackSession

        session = PlaybackSession(
            session_id="session-1",
            track_id=1,
            user_id="user-1",
            position=0.0,
            duration=180.0,
            volume=1.0,
            muted=False,
            repeat_mode="off",
            shuffle=False,
            started_at=datetime.now(UTC).isoformat(),
        )
        assert session.session_id == "session-1"
        assert session.track_id == 1
        assert session.volume == 1.0

    def test_playback_session_defaults(self):
        """测试 PlaybackSession 默认值"""
        from app.core.context import PlaybackSession

        session = PlaybackSession(
            session_id="session-1",
            track_id=1,
        )
        assert session.position == 0.0
        assert session.volume == 1.0
        assert session.muted is False
        assert session.repeat_mode == "off"
        assert session.shuffle is False
