"""
数据库操作全面测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTrackOperComprehensive:
    """TrackOper 全面测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_track.id = 1
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all(self):
        """测试获取所有"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.get_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """测试存在检查"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.exists(1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.delete(1)
        assert result is True


class TestAlbumOperComprehensive:
    """AlbumOper 全面测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取"""
        from app.db.models.album import Album
        from app.db.operations.album import AlbumOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_album.id = 1
        mock_result.scalar_one_or_none.return_value = mock_album
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = AlbumOper(Album, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_by_title(self):
        """测试通过标题搜索"""
        from app.db.models.album import Album
        from app.db.operations.album import AlbumOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_result.scalars.return_value.all.return_value = [mock_album]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = AlbumOper(Album, mock_db)
        result = await oper.search_by_title("Test")
        assert len(result) == 1


class TestArtistOperComprehensive:
    """ArtistOper 全面测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取"""
        from app.db.models.artist import Artist
        from app.db.operations.artist import ArtistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_artist.id = 1
        mock_result.scalar_one_or_none.return_value = mock_artist
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = ArtistOper(Artist, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        """测试通过名称搜索"""
        from app.db.models.artist import Artist
        from app.db.operations.artist import ArtistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_result.scalars.return_value.all.return_value = [mock_artist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = ArtistOper(Artist, mock_db)
        result = await oper.search_by_name("Test")
        assert len(result) == 1


class TestPlaylistOperComprehensive:
    """PlaylistOper 全面测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_playlist.id = 1
        mock_result.scalar_one_or_none.return_value = mock_playlist
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(Playlist, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_public_playlists(self):
        """测试获取公开播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_result.scalars.return_value.all.return_value = [mock_playlist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(Playlist, mock_db)
        result = await oper.get_public_playlists()
        assert len(result) == 1


class TestSiteOperComprehensive:
    """SiteOper 全面测试"""

    @pytest.mark.asyncio
    async def test_get_enabled(self):
        """测试获取启用的站点"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_site.enabled = True
        mock_result.scalars.return_value.all.return_value = [mock_site]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(Site, mock_db)
        result = await oper.get_enabled()
        assert len(result) == 1


class TestLibraryOperComprehensive:
    """LibraryOper 全面测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取"""
        from app.db.models.library import Library
        from app.db.operations.library import LibraryOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_library = MagicMock(spec=Library)
        mock_library.id = 1
        mock_result.scalar_one_or_none.return_value = mock_library
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = LibraryOper(Library, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_auto_scan_libraries(self):
        """测试获取自动扫描媒体库"""
        from app.db.models.library import Library
        from app.db.operations.library import LibraryOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_library = MagicMock(spec=Library)
        mock_result.scalars.return_value.all.return_value = [mock_library]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = LibraryOper(Library, mock_db)
        result = await oper.get_auto_scan_libraries()
        assert len(result) == 1
