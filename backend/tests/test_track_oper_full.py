"""
TrackOper 完整测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTrackOperFull:
    """TrackOper 完整测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取曲目"""
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
        """测试获取所有曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_album_id(self):
        """测试通过专辑 ID 获取曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

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
        """测试通过艺术家 ID 获取曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

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
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

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

    @pytest.mark.asyncio
    async def test_get_most_played(self):
        """测试获取最多播放曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.get_most_played(limit=10)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recently_played(self):
        """测试获取最近播放曲目"""
        from app.db.models.track import Track
        from app.db.operations.track import TrackOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_track = MagicMock(spec=Track)
        mock_result.scalars.return_value.all.return_value = [mock_track]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = TrackOper(Track, mock_db)
        result = await oper.get_recently_played(limit=10)
        assert len(result) == 1
