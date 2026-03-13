"""
数据库操作扩展测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTrackOperExtended:
    """TrackOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_by_musicbrainz_id(self):
        """测试通过 MusicBrainz ID 获取曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_track.id = 1
        mock_track.musicbrainz_id = "mb-123"
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db_manager)
        result = await oper.get_by_musicbrainz_id("mb-123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_file_hash(self):
        """测试通过文件哈希获取曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_track.id = 1
        mock_track.file_hash = "abc123"
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db_manager)
        result = await oper.get_by_file_hash("abc123")

        assert result is not None


class TestAlbumOperExtended:
    """AlbumOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_by_artist_id(self):
        """测试通过艺术家ID获取专辑"""
        from app.db.models.album import Album
        from app.db.operations.album import AlbumOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_album.id = 1
        mock_result.scalars.return_value.all.return_value = [mock_album]
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = AlbumOper(Album, mock_db_manager)
        result = await oper.get_by_artist_id(1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_title(self):
        """测试通过标题搜索专辑"""
        from app.db.models.album import Album
        from app.db.operations.album import AlbumOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_album.id = 1
        mock_result.scalars.return_value.all.return_value = [mock_album]
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = AlbumOper(Album, mock_db_manager)
        result = await oper.search_by_title("Test")

        assert len(result) == 1


class TestArtistOperExtended:
    """ArtistOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        """测试通过名称搜索艺术家"""
        from app.db.models.artist import Artist
        from app.db.operations.artist import ArtistOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_artist.id = 1
        mock_artist.name = "Test Artist"
        mock_result.scalars.return_value.all.return_value = [mock_artist]
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = ArtistOper(Artist, mock_db_manager)
        result = await oper.search_by_name("Test")

        assert len(result) == 1


class TestSiteOperExtended:
    """SiteOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_enabled(self):
        """测试获取启用的站点"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_site.id = 1
        mock_site.enabled = True
        mock_result.scalars.return_value.all.return_value = [mock_site]
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(Site, mock_db_manager)
        result = await oper.get_enabled()

        assert len(result) == 1


class TestPlaylistOperExtended:
    """PlaylistOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_public_playlists(self):
        """测试获取公开播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db_manager = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_playlist.id = 1
        mock_result.scalars.return_value.all.return_value = [mock_playlist]
        mock_session.execute.return_value = mock_result
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(Playlist, mock_db_manager)
        result = await oper.get_public_playlists()

        assert len(result) == 1
