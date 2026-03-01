"""
Operations 扩展测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTrackOperExtended:
    """TrackOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_by_album_id(self):
        """测试通过专辑ID获取曲目"""
        from app.db.operations.track import TrackOper
        from app.db.models.track import Track
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = TrackOper(Track, mock_db)
        result = await oper.get_by_album_id(1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_artist_id(self):
        """测试通过艺术家ID获取曲目"""
        from app.db.operations.track import TrackOper
        from app.db.models.track import Track
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = TrackOper(Track, mock_db)
        result = await oper.get_by_artist_id(1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_title(self):
        """测试通过标题搜索曲目"""
        from app.db.operations.track import TrackOper
        from app.db.models.track import Track
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = TrackOper(Track, mock_db)
        result = await oper.search_by_title("Test")
        assert len(result) == 1


class TestAlbumOperExtended:
    """AlbumOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_by_artist_id(self):
        """测试通过艺术家ID获取专辑"""
        from app.db.operations.album import AlbumOper
        from app.db.models.album import Album
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_result.scalars.return_value.all.return_value = [mock_album]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = AlbumOper(Album, mock_db)
        result = await oper.get_by_artist_id(1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recent(self):
        """测试获取最近专辑"""
        from app.db.operations.album import AlbumOper
        from app.db.models.album import Album
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_result.scalars.return_value.all.return_value = [mock_album]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = AlbumOper(Album, mock_db)
        result = await oper.get_recent()
        assert len(result) == 1


class TestArtistOperExtended:
    """ArtistOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_top_rated(self):
        """测试获取高评分艺术家"""
        from app.db.operations.artist import ArtistOper
        from app.db.models.artist import Artist
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_result.scalars.return_value.all.return_value = [mock_artist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = ArtistOper(Artist, mock_db)
        result = await oper.get_top_rated()
        assert len(result) == 1


class TestSubscribeReleaseOperExtended:
    """SubscribeReleaseOper 扩展测试"""

    @pytest.mark.asyncio
    async def test_get_by_subscribe_id(self):
        """测试通过订阅ID获取发布"""
        from app.db.operations.subscribe_release import SubscribeReleaseOper
        from app.db.models.subscribe_release import SubscribeRelease
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_release = MagicMock(spec=SubscribeRelease)
        mock_result.scalars.return_value.all.return_value = [mock_release]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeReleaseOper(SubscribeRelease, mock_db)
        result = await oper.get_by_subscribe_id(1)
        assert len(result) == 1
