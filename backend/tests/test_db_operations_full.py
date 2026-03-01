"""
数据库操作完整测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAllDbOperations:
    """所有数据库操作测试"""

    @pytest.mark.asyncio
    async def test_track_oper_methods(self):
        """测试 TrackOper 方法"""
        from app.db.operations.track import TrackOper
        from app.db.models.track import Track
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_track.id = 1
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = TrackOper(Track, mock_db)
        
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_album_oper_methods(self):
        """测试 AlbumOper 方法"""
        from app.db.operations.album import AlbumOper
        from app.db.models.album import Album
        
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
    async def test_artist_oper_methods(self):
        """测试 ArtistOper 方法"""
        from app.db.operations.artist import ArtistOper
        from app.db.models.artist import Artist
        
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
    async def test_playlist_oper_methods(self):
        """测试 PlaylistOper 方法"""
        from app.db.operations.playlist import PlaylistOper
        from app.db.models.playlist import Playlist
        
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
    async def test_subscribe_oper_methods(self):
        """测试 SubscribeOper 方法"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_subscribe.id = 1
        mock_result.scalar_one_or_none.return_value = mock_subscribe
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_site_oper_methods(self):
        """测试 SiteOper 方法"""
        from app.db.operations.site import SiteOper
        from app.db.models.site import Site
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_site.id = 1
        mock_result.scalar_one_or_none.return_value = mock_site
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SiteOper(Site, mock_db)
        
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_library_oper_methods(self):
        """测试 LibraryOper 方法"""
        from app.db.operations.library import LibraryOper
        from app.db.models.library import Library
        
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
    async def test_media_oper_methods(self):
        """测试 MediaServerOper 方法"""
        from app.db.operations.media import MediaServerOper
        from app.db.models.media import MediaServer
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_media = MagicMock(spec=MediaServer)
        mock_media.id = 1
        mock_result.scalar_one_or_none.return_value = mock_media
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = MediaServerOper(MediaServer, mock_db)
        
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_download_oper_methods(self):
        """测试 DownloadHistoryOper 方法"""
        from app.db.operations.download import DownloadHistoryOper
        from app.db.models.download import DownloadHistory
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_download = MagicMock(spec=DownloadHistory)
        mock_download.id = 1
        mock_result.scalar_one_or_none.return_value = mock_download
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = DownloadHistoryOper(DownloadHistory, mock_db)
        
        result = await oper.get_by_id(1)
        assert result is not None
