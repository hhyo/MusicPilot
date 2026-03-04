"""
Context 完整测试
"""


class TestContextFull:
    """Context 完整测试"""

    def test_music_info_imports(self):
        from app.core.context import MusicInfo

        assert MusicInfo is not None

    def test_download_task_imports(self):
        from app.core.context import DownloadTask

        assert DownloadTask is not None

    def test_playback_session_imports(self):
        from app.core.context import PlaybackSession

        assert PlaybackSession is not None

    def test_download_source_imports(self):
        from app.core.context import DownloadSource

        assert DownloadSource is not None

    def test_download_status_imports(self):
        from app.core.context import DownloadStatus

        assert DownloadStatus is not None

    def test_downloader_type_imports(self):
        from app.core.context import DownloaderType

        assert DownloaderType is not None


class TestMusicInfoCreation:
    """MusicInfo 创建测试"""

    def test_music_info_creation_basic(self):
        from app.core.context import MusicInfo

        info = MusicInfo(title="Test Song", artist="Test Artist", album="Test Album")
        assert info.title == "Test Song"
        assert info.artist == "Test Artist"
        assert info.album == "Test Album"


class TestDownloadStatus:
    """DownloadStatus 测试"""

    def test_download_status_values(self):
        from app.core.context import DownloadStatus

        assert DownloadStatus.PENDING is not None
        assert DownloadStatus.DOWNLOADING is not None
        assert DownloadStatus.COMPLETED is not None
        assert DownloadStatus.FAILED is not None
        assert DownloadStatus.CANCELLED is not None


class TestDownloaderType:
    """DownloaderType 测试"""

    def test_downloader_type_values(self):
        from app.core.context import DownloaderType

        assert DownloaderType.NETEASE is not None
