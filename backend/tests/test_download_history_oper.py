"""
DownloadHistoryOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestDownloadHistoryOper:
    """DownloadHistoryOper 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_download_history_oper_imports(self):
        """测试 DownloadHistoryOper 可导入"""
        from app.db.operations.download import DownloadHistoryOper
        assert DownloadHistoryOper is not None

    @pytest.mark.asyncio
    async def test_download_history_oper_get_all(self, mock_db):
        """测试获取所有下载历史"""
        from app.db.operations.download import DownloadHistoryOper
        from app.db.models.download import DownloadHistory
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_history = MagicMock(spec=DownloadHistory)
        mock_result.scalars.return_value.all.return_value = [mock_history]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = DownloadHistoryOper(DownloadHistory, mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_download_history_oper_get_by_id(self, mock_db):
        """测试通过 ID 获取下载历史"""
        from app.db.operations.download import DownloadHistoryOper
        from app.db.models.download import DownloadHistory
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_history = MagicMock(spec=DownloadHistory)
        mock_history.id = 1
        mock_result.scalar_one_or_none.return_value = mock_history
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = DownloadHistoryOper(DownloadHistory, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None
