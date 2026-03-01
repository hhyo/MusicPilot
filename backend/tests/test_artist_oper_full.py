"""
ArtistOper 完整测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestArtistOperFull:
    """ArtistOper 完整测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_artist_oper_imports(self):
        """测试 ArtistOper 可导入"""
        from app.db.operations.artist import ArtistOper
        assert ArtistOper is not None

    @pytest.mark.asyncio
    async def test_artist_oper_get_by_id(self, mock_db):
        """测试通过 ID 获取艺术家"""
        from app.db.operations.artist import ArtistOper
        from app.db.models.artist import Artist
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_artist.id = 1
        mock_artist.name = "Test Artist"
        mock_result.scalar_one_or_none.return_value = mock_artist
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = ArtistOper(Artist, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_artist_oper_get_all(self, mock_db):
        """测试获取所有艺术家"""
        from app.db.operations.artist import ArtistOper
        from app.db.models.artist import Artist
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_result.scalars.return_value.all.return_value = [mock_artist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = ArtistOper(Artist, mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio

    @pytest.mark.asyncio
    async def test_artist_oper_get_by_musicbrainz_id(self, mock_db):
        """测试通过 MusicBrainz ID 获取艺术家"""
        from app.db.operations.artist import ArtistOper
        from app.db.models.artist import Artist
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_artist = MagicMock(spec=Artist)
        mock_artist.id = 1
        mock_artist.musicbrainz_id = "mb-123"
        mock_result.scalar_one_or_none.return_value = mock_artist
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = ArtistOper(Artist, mock_db)
        result = await oper.get_by_musicbrainz_id("mb-123")
        assert result is not None
