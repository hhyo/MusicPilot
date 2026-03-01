"""
SubscribeOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSubscribeOperMethods:
    """SubscribeOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_by_musicbrainz_id(self):
        """测试通过 MusicBrainz ID 获取订阅"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_subscribe.id = 1
        mock_subscribe.musicbrainz_id = "mb-123"
        mock_result.scalar_one_or_none.return_value = mock_subscribe
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.get_by_musicbrainz_id("mb-123")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_playlist_id(self):
        """测试通过播放列表 ID 获取订阅"""
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
        result = await oper.get_by_playlist_id("playlist-123")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_type(self):
        """测试通过类型获取订阅"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_result.scalars.return_value.all.return_value = [mock_subscribe]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.get_by_type("artist")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_source_type(self):
        """测试通过来源类型获取订阅"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_result.scalars.return_value.all.return_value = [mock_subscribe]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.get_by_source_type("netease")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_active(self):
        """测试获取活跃订阅"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_result.scalars.return_value.all.return_value = [mock_subscribe]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.get_active()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        """测试通过名称搜索订阅"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_result.scalars.return_value.all.return_value = [mock_subscribe]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.search_by_name("Test")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_check_time(self):
        """测试更新检查时间"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_subscribe.id = 1
        mock_result.scalar_one_or_none.return_value = mock_subscribe
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.update_check_time(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_release(self):
        """测试更新发布数"""
        from app.db.operations.subscribe import SubscribeOper
        from app.db.models.subscribe import Subscribe
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_subscribe.id = 1
        mock_result.scalar_one_or_none.return_value = mock_subscribe
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = SubscribeOper(Subscribe, mock_db)
        result = await oper.update_release(1, 10)
        assert result is not None
