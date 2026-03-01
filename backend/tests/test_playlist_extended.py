"""
Playlist 扩展测试
"""

import pytest


class TestPlaylistModel:
    """Playlist 模型测试"""

    def test_playlist_creation(self):
        """测试播放列表创建"""
        from app.db.models.playlist import Playlist
        assert hasattr(Playlist, '__tablename__')

    def test_playlist_attributes(self):
        """测试播放列表属性"""
        from app.db.models.playlist import Playlist
        assert Playlist.__tablename__ == 'playlists'


class TestPlaylistSchema:
    """Playlist Schema 测试"""

    def test_playlist_base_creation(self):
        """测试 PlaylistBase 创建"""
        from app.schemas.playlist import PlaylistBase
        playlist = PlaylistBase(name="Test Playlist")
        assert playlist.name == "Test Playlist"

    def test_playlist_response_creation(self):
        """测试 PlaylistResponse 创建"""
        from app.schemas.playlist import PlaylistResponse
        from datetime import datetime, timezone
        playlist = PlaylistResponse(
            id=1,
            name="Test Playlist",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert playlist.id == 1
        assert playlist.name == "Test Playlist"
