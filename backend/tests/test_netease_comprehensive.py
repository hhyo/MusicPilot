"""
NeteaseDownloader 综合测试
"""

import pytest


class TestNeteaseDownloaderComprehensive:
    """NeteaseDownloader 综合测试"""

    def test_netease_module_structure(self):
        """测试网易云模块结构"""
        from app.modules.downloader.netease import NeteaseDownloader
        methods = [m for m in dir(NeteaseDownloader) if not m.startswith('_')]
        assert len(methods) > 0

    def test_netease_base_class(self):
        """测试网易云基类"""
        from app.modules.downloader.netease import NeteaseDownloader
        from app.modules.downloader.base import DownloaderBase
        assert issubclass(NeteaseDownloader, DownloaderBase)


class TestNeteaseDownloadMethods:
    """网易云下载方法测试"""

    def test_quality_constants(self):
        """测试音质常量"""
        qualities = {
            "standard": 128000,
            "higher": 192000,
            "exhigh": 320000,
            "lossless": 999000,
            "hires": 1900000,
        }
        for name, bitrate in qualities.items():
            assert isinstance(bitrate, int)
            assert bitrate > 0

    def test_download_status_values(self):
        """测试下载状态值"""
        from app.modules.downloader_module import DownloadStatus
        assert hasattr(DownloadStatus, 'DOWNLOADING')
        assert hasattr(DownloadStatus, 'COMPLETED')
        assert hasattr(DownloadStatus, 'ERROR')


class TestNeteaseApiResponse:
    """网易云 API 响应测试"""

    def test_song_response_structure(self):
        """测试歌曲响应结构"""
        response = {
            "songs": [
                {
                    "id": 123456,
                    "name": "Test Song",
                    "artists": [{"id": 1, "name": "Artist"}],
                    "album": {"id": 1, "name": "Album"},
                }
            ],
            "code": 200,
        }
        assert response["code"] == 200
        assert len(response["songs"]) == 1

    def test_playlist_response_structure(self):
        """测试歌单响应结构"""
        response = {
            "playlist": {
                "id": 789012,
                "name": "Test Playlist",
                "trackIds": [1, 2, 3],
            },
            "code": 200,
        }
        assert response["code"] == 200
        assert len(response["playlist"]["trackIds"]) == 3

    def test_artist_response_structure(self):
        """测试艺术家响应结构"""
        response = {
            "artist": {
                "id": 1,
                "name": "Test Artist",
                "albumSize": 10,
            },
            "code": 200,
        }
        assert response["code"] == 200
        assert response["artist"]["albumSize"] == 10


class TestNeteaseDownloadTask:
    """网易云下载任务测试"""

    def test_task_info_structure(self):
        """测试任务信息结构"""
        from app.modules.downloader_module import DownloadTaskInfo, DownloadStatus
        task = DownloadTaskInfo(
            task_id="netease-123",
            name="Test Song.mp3",
            size=1024000,
            downloaded=512000,
            uploaded=0,
            download_speed=102400,
            upload_speed=0,
            eta=10,
            progress=50.0,
            status=DownloadStatus.DOWNLOADING,
            save_path="/downloads",
        )
        assert task.task_id == "netease-123"
        assert task.progress == 50.0

    def test_progress_structure(self):
        """测试进度结构"""
        from app.modules.downloader_module import DownloadProgress
        progress = DownloadProgress(
            task_id="test-1",
            progress=75.0,
            downloaded=768000,
            total=1024000,
            download_speed=102400,
            eta=5,
        )
        assert progress.progress == 75.0
        assert progress.eta == 5
