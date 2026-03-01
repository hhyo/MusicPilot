"""
Schema 验证测试
"""

import pytest


class TestAlbumSchema:
    """Album Schema 测试"""

    def test_album_base_creation(self):
        """测试 AlbumBase 创建"""
        from app.schemas.album import AlbumBase
        album = AlbumBase(
            title="Test Album",
            artist_id=1,
        )
        assert album.title == "Test Album"

    def test_album_response_creation(self):
        """测试 AlbumResponse 创建"""
        from app.schemas.album import AlbumResponse
        album = AlbumResponse(
            id=1,
            title="Test Album",
            artist_id=1,
        )
        assert album.id == 1


class TestArtistSchema:
    """Artist Schema 测试"""

    def test_artist_base_creation(self):
        """测试 ArtistBase 创建"""
        from app.schemas.artist import ArtistBase
        artist = ArtistBase(name="Test Artist")
        assert artist.name == "Test Artist"

    def test_artist_response_creation(self):
        """测试 ArtistResponse 创建"""
        from app.schemas.artist import ArtistResponse
        artist = ArtistResponse(
            id=1,
            name="Test Artist",
        )
        assert artist.id == 1


class TestTrackSchema:
    """Track Schema 测试"""

    def test_track_base_creation(self):
        """测试 TrackBase 创建"""
        from app.schemas.track import TrackBase
        track = TrackBase(
            title="Test Track",
            album_id=1,
        )
        assert track.title == "Test Track"


class TestPlaylistSchema:
    """Playlist Schema 测试"""

    def test_playlist_base_creation(self):
        """测试 PlaylistBase 创建"""
        from app.schemas.playlist import PlaylistBase
        playlist = PlaylistBase(name="Test Playlist")
        assert playlist.name == "Test Playlist"


class TestSiteSchema:
    """Site Schema 测试"""

    def test_site_base_creation(self):
        """测试 SiteBase 创建"""
        from app.schemas.site import SiteBase
        site = SiteBase(
            name="Test Site",
            url="https://example.com",
        )
        assert site.name == "Test Site"


class TestSubscribeSchema:
    """Subscribe Schema 测试"""

    def test_subscribe_base_creation(self):
        """测试 SubscribeBase 创建"""
        from app.schemas.subscribe import SubscribeBase
        subscribe = SubscribeBase(
            name="Test Subscribe",
            type="artist",
        )
        assert subscribe.name == "Test Subscribe"


class TestResponseSchema:
    """Response Schema 测试"""

    def test_response_model_creation(self):
        """测试 ResponseModel 创建"""
        from app.schemas.response import ResponseModel
        response = ResponseModel(data={"key": "value"})
        assert response.success is True

    def test_paginated_response_creation(self):
        """测试 PaginatedResponse 创建"""
        from app.schemas.response import PaginatedResponse
        response = PaginatedResponse(
            data=[{"id": 1}],
            total=1,
        )
        assert response.total == 1

    def test_error_response_creation(self):
        """测试 ErrorResponse 创建"""
        from app.schemas.response import ErrorResponse
        response = ErrorResponse(message="Test error")
        assert response.success is False
