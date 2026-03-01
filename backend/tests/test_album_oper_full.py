"""
AlbumOper 完整测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAlbumOperFull:
    """AlbumOper 完整测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_album_oper_imports(self):
        """测试 AlbumOper 可导入"""
        from app.db.operations.album import AlbumOper
        assert AlbumOper is not None

    @pytest.mark.asyncio
    async def test_album_oper_get_all(self, mock_db):
        """测试获取所有专辑"""
        from app.db.operations.album import AlbumOper
        from app.db.models.album import Album
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_result.scalars.return_value.all.return_value = [mock_album]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = AlbumOper(Album, mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_album_oper_get_by_id(self, mock_db):
        """测试通过 ID 获取专辑"""
        from app.db.operations.album import AlbumOper
        from app.db.models.album import Album
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_album = MagicMock(spec=Album)
        mock_album.id = 1
        mock_album.title = "Test Album"
        mock_result.scalar_one_or_none.return_value = mock_album
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = AlbumOper(Album, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_album_oper_get_by_artist_id(self, mock_db):
        """测试通过艺术家 ID 获取专辑"""
        from app.db.operations.album import AlbumOper
        from app.db.models.album import Album
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = AlbumOper(Album, mock_db)
        result = await oper.get_by_artist_id(1)
        assert result is not None
