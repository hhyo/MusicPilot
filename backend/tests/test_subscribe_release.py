"""
SubscribeRelease 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSubscribeReleaseOper:
    """SubscribeReleaseOper 测试"""

    @pytest.mark.asyncio
    async def test_get_by_subscribe_id(self):
        """测试通过订阅 ID 获取"""
        from app.db.models.subscribe_release import SubscribeRelease
        from app.db.operations.subscribe_release import SubscribeReleaseOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SubscribeReleaseOper(mock_db)
        result = await oper.get_by_subscribe_id(1)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_torrent_id(self):
        """测试通过种子 ID 获取"""
        from app.db.models.subscribe_release import SubscribeRelease
        from app.db.operations.subscribe_release import SubscribeReleaseOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SubscribeReleaseOper(mock_db)
        result = await oper.get_by_torrent_id("torrent-123")
        assert result is None


class TestSubscribeReleaseModel:
    """SubscribeRelease 模型测试"""

    def test_model_import(self):
        """测试模型导入"""
        from app.db.models.subscribe_release import SubscribeRelease

        assert SubscribeRelease is not None

    def test_model_table(self):
        """测试模型表名"""
        from app.db.models.subscribe_release import SubscribeRelease

        assert hasattr(SubscribeRelease, "__tablename__")
