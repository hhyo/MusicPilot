"""
所有 Operations 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAllOperations:
    """所有 Operations 测试"""

    @pytest.mark.asyncio
    async def test_track_oper(self):
        """测试 TrackOper"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_album_oper(self):
        """测试 AlbumOper"""
        from app.db.models.album import Album
        from app.db.operations.album import AlbumOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = AlbumOper(Album, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_artist_oper(self):
        """测试 ArtistOper"""
        from app.db.models.artist import Artist
        from app.db.operations.artist import ArtistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = ArtistOper(Artist, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_playlist_oper(self):
        """测试 PlaylistOper"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(Playlist, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_site_oper(self):
        """测试 SiteOper"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(Site, mock_db)
        result = await oper.get_enabled()
        assert result == []

    @pytest.mark.asyncio
    async def test_library_oper(self):
        """测试 LibraryOper"""
        from app.db.models.library import Library
        from app.db.operations.library import LibraryOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = LibraryOper(Library, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_subscribe_oper(self):
        """测试 SubscribeOper"""
        from app.db.models.subscribe import Subscribe
        from app.db.operations.subscribe import SubscribeOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_media_server_oper(self):
        """测试 MediaServerOper"""
        from app.db.models.media import MediaServer
        from app.db.operations.media import MediaServerOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = MediaServerOper(MediaServer, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_download_history_oper(self):
        """测试 DownloadHistoryOper"""
        from app.db.models.download import DownloadHistory
        from app.db.operations.download import DownloadHistoryOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = DownloadHistoryOper(DownloadHistory, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_subscribe_release_oper(self):
        """测试 SubscribeReleaseOper"""
        from app.db.models.subscribe_release import SubscribeRelease
        from app.db.operations.subscribe_release import SubscribeReleaseOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SubscribeReleaseOper(SubscribeRelease, mock_db)
        result = await oper.get_by_id(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_system_config_oper(self):
        """测试 SystemConfigOper"""
        from app.db.models.system import SystemConfig
        from app.db.operations.system import SystemConfigOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SystemConfigOper(SystemConfig, mock_db)
        result = await oper.get_by_id(1)
        assert result is None
