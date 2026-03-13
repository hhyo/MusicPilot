"""
PlaylistChain 单元测试
测试播放列表链的功能
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.playlist import PlaylistChain
from app.core.context import PlaylistType, SmartQuery


class TestPlaylistChain:
    """PlaylistChain 测试类"""

    @pytest.fixture
    def chain(self):
        """创建 PlaylistChain 实例"""
        mock_db_manager = MagicMock()
        chain = PlaylistChain(db_manager=mock_db_manager)
        return chain

    @pytest.fixture
    def smart_query(self):
        """创建示例智能查询"""
        return SmartQuery(
            conditions=[{"field": "genre", "operator": "==", "value": "Rock"}],
            operator="AND",
            sort_by="rating",
            sort_order="DESC",
            limit=50,
        )

    # ==================== create 测试 ====================

    @pytest.mark.asyncio
    async def test_create_normal_playlist(self, chain):
        """测试创建普通播放列表"""
        mock_playlist = MagicMock()
        mock_playlist.id = 1

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.create = AsyncMock(return_value=mock_playlist)
            mock_oper_class.return_value = mock_oper

            result = await chain.create("My Playlist")

        assert result == 1

    @pytest.mark.asyncio
    async def test_create_smart_playlist(self, chain, smart_query):
        """测试创建智能播放列表"""
        mock_playlist = MagicMock()
        mock_playlist.id = 2

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.create = AsyncMock(return_value=mock_playlist)
            mock_oper_class.return_value = mock_oper

            result = await chain.create(
                "Smart Playlist",
                playlist_type=PlaylistType.SMART,
                description="Auto-generated",
                smart_query=smart_query,
            )

        assert result == 2

    @pytest.mark.asyncio
    async def test_create_with_description(self, chain):
        """测试创建带描述的播放列表"""
        mock_playlist = MagicMock()
        mock_playlist.id = 3

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.create = AsyncMock(return_value=mock_playlist)
            mock_oper_class.return_value = mock_oper

            result = await chain.create("New Playlist", description="Test description")

        assert result == 3

    # ==================== add_tracks 测试 ====================

    @pytest.mark.asyncio
    async def test_add_tracks(self, chain):
        """测试添加曲目到播放列表"""
        track_ids = [1, 2, 3]

        # Mock get_session as async context manager
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        chain.db_manager.get_session = mock_get_session

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.add_track = AsyncMock(return_value=True)
            mock_oper_class.return_value = mock_oper

            result = await chain.add_tracks(1, track_ids)

        assert result == 3

    @pytest.mark.asyncio
    async def test_add_tracks_empty_list(self, chain):
        """测试添加空曲目列表"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        chain.db_manager.get_session = mock_get_session

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper_class.return_value = mock_oper

            result = await chain.add_tracks(1, [])

        assert result == 0

    # ==================== remove_tracks 测试 ====================

    @pytest.mark.asyncio
    async def test_remove_tracks(self, chain):
        """测试从播放列表移除曲目"""
        track_ids = [1, 2]

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.remove_track = AsyncMock(return_value=True)
            mock_oper_class.return_value = mock_oper

            result = await chain.remove_tracks(1, track_ids)

        assert result == 2

    @pytest.mark.asyncio
    async def test_remove_tracks_partial_success(self, chain):
        """测试部分曲目移除成功"""
        track_ids = [1, 2, 3]

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.remove_track = AsyncMock(side_effect=[True, False, True])
            mock_oper_class.return_value = mock_oper

            result = await chain.remove_tracks(1, track_ids)

        assert result == 2

    # ==================== reorder_tracks 测试 ====================

    @pytest.mark.asyncio
    async def test_reorder_tracks(self, chain):
        """测试重新排序曲目"""
        track_ids = [3, 1, 2]

        with patch("app.db.operations.playlist.PlaylistOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.reorder_tracks = AsyncMock()
            mock_oper_class.return_value = mock_oper

            await chain.reorder_tracks(1, track_ids)

        mock_oper.reorder_tracks.assert_called_once()

    # ==================== generate_smart 测试 ====================

    @pytest.mark.asyncio
    async def test_generate_smart(self, chain, smart_query):
        """测试生成智能播放列表"""
        mock_tracks = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]

        with patch("app.db.operations.track.TrackOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.get_all = AsyncMock(return_value=mock_tracks)
            mock_oper_class.return_value = mock_oper

            result = await chain.generate_smart(smart_query)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_generate_smart_empty(self, chain):
        """测试生成空智能播放列表"""
        query = SmartQuery(limit=10)

        with patch("app.db.operations.track.TrackOper") as mock_oper_class:
            mock_oper = AsyncMock()
            mock_oper.get_all = AsyncMock(return_value=[])
            mock_oper_class.return_value = mock_oper

            result = await chain.generate_smart(query)

        assert len(result) == 0
