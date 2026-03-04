"""
Schemas 单元测试
测试 Pydantic 模型
"""


class TestResponseSchema:
    """Response 模型测试"""

    def test_response_model_success(self):
        """测试成功响应"""
        from app.schemas.response import ResponseModel

        response = ResponseModel(success=True, message="success", data={"key": "value"})

        assert response.success is True
        assert response.message == "success"
        assert response.data == {"key": "value"}

    def test_response_model_error(self):
        """测试错误响应"""
        from app.schemas.response import ResponseModel

        response = ResponseModel(success=False, message="Bad Request", data=None)

        assert response.success is False
        assert response.data is None

    def test_paginated_response(self):
        """测试分页响应"""
        from app.schemas.response import PaginatedResponse

        response = PaginatedResponse(
            data=[{"id": 1}, {"id": 2}], total=100, page=1, page_size=20, total_pages=5
        )

        assert response.success is True
        assert len(response.data) == 2
        assert response.total == 100


class TestArtistSchema:
    """Artist 模型测试"""

    def test_artist_creation(self):
        """测试创建艺术家"""
        from app.schemas.artist import ArtistCreate

        artist = ArtistCreate(name="Test Artist", musicbrainz_id="mb-123")

        assert artist.name == "Test Artist"
        assert artist.musicbrainz_id == "mb-123"


class TestAlbumSchema:
    """Album 模型测试"""

    def test_album_creation(self):
        """测试创建专辑"""
        from app.schemas.album import AlbumCreate

        album = AlbumCreate(title="Test Album", artist_id=1)

        assert album.title == "Test Album"
        assert album.artist_id == 1


class TestTrackSchema:
    """Track 模型测试"""

    def test_track_creation(self):
        """测试创建曲目"""
        from app.schemas.track import TrackCreate

        track = TrackCreate(title="Test Track", album_id=1)

        assert track.title == "Test Track"
        assert track.album_id == 1


class TestPlaylistSchema:
    """Playlist 模型测试"""

    def test_playlist_creation(self):
        """测试创建播放列表"""
        from app.schemas.playlist import PlaylistCreate

        playlist = PlaylistCreate(name="My Playlist", description="Test playlist")

        assert playlist.name == "My Playlist"
        assert playlist.description == "Test playlist"


class TestSiteSchema:
    """Site 模型测试"""

    def test_site_creation(self):
        """测试创建站点"""
        from app.schemas.site import SiteCreate

        site = SiteCreate(name="Test Site", url="https://example.com", site_type="pt")

        assert site.name == "Test Site"
        assert site.url == "https://example.com"


class TestSubscribeSchema:
    """Subscribe 模型测试"""

    def test_subscribe_creation(self):
        """测试创建订阅"""
        from app.schemas.subscribe import SubscribeCreate

        subscribe = SubscribeCreate(type="artist", name="Test Artist", musicbrainz_id="mb-123")

        assert subscribe.type == "artist"
        assert subscribe.name == "Test Artist"


class TestLibrarySchema:
    """Library 模型测试"""

    def test_library_creation(self):
        """测试创建媒体库"""
        from app.schemas.library import LibraryCreate

        library = LibraryCreate(name="Music Library", path="/music")

        assert library.name == "Music Library"
        assert library.path == "/music"
