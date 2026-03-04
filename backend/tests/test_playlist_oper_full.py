"""
PlaylistOper 完整测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestPlaylistOperFull:
    """PlaylistOper 完整测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_playlist_oper_imports(self):
        """测试 PlaylistOper 可导入"""
        from app.db.operations.playlist import PlaylistOper

        assert PlaylistOper is not None

    @pytest.mark.asyncio
    async def test_playlist_oper_get_all(self, mock_db):
        """测试获取所有播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_result.scalars.return_value.all.return_value = [mock_playlist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(Playlist, mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_playlist_oper_get_by_id(self, mock_db):
        """测试通过 ID 获取播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_playlist.id = 1
        mock_playlist.name = "Test Playlist"
        mock_result.scalar_one_or_none.return_value = mock_playlist
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(Playlist, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None
