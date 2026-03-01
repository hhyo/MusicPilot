"""
LibraryOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestLibraryOperMethods:
    """LibraryOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取媒体库"""
        from app.db.operations.library import LibraryOper
        from app.db.models.library import Library
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_library = MagicMock(spec=Library)
        mock_library.id = 1
        mock_library.name = "Test Library"
        mock_result.scalar_one_or_none.return_value = mock_library
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = LibraryOper(Library, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all(self):
        """测试获取所有媒体库"""
        from app.db.operations.library import LibraryOper
        from app.db.models.library import Library
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_library = MagicMock(spec=Library)
        mock_result.scalars.return_value.all.return_value = [mock_library]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = LibraryOper(Library, mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_auto_scan_libraries(self):
        """测试获取自动扫描媒体库"""
        from app.db.operations.library import LibraryOper
        from app.db.models.library import Library
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_library = MagicMock(spec=Library)
        mock_result.scalars.return_value.all.return_value = [mock_library]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = LibraryOper(Library, mock_db)
        result = await oper.get_auto_scan_libraries()
        assert len(result) == 1


class TestMediaServerOperMethods:
    """MediaServerOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取媒体服务器"""
        from app.db.operations.media import MediaServerOper
        from app.db.models.media import MediaServer
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_server = MagicMock(spec=MediaServer)
        mock_server.id = 1
        mock_server.name = "Test Server"
        mock_result.scalar_one_or_none.return_value = mock_server
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = MediaServerOper(MediaServer, mock_db)
        result = await oper.get_by_id(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all(self):
        """测试获取所有媒体服务器"""
        from app.db.operations.media import MediaServerOper
        from app.db.models.media import MediaServer
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_server = MagicMock(spec=MediaServer)
        mock_result.scalars.return_value.all.return_value = [mock_server]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = MediaServerOper(MediaServer, mock_db)
        result = await oper.get_all()
        assert len(result) == 1


class TestDownloadHistoryOperMethods:
    """DownloadHistoryOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """测试通过 ID 获取下载历史"""
        from app.db.operations.download import DownloadHistoryOper
        from app.db.models.download import DownloadHistory
        
        mock_db = MagicMock()
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

    @pytest.mark.asyncio
    async def test_get_recent(self):
        """测试获取最近下载历史"""
        from app.db.operations.download import DownloadHistoryOper
        from app.db.models.download import DownloadHistory
        
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_history = MagicMock(spec=DownloadHistory)
        mock_result.scalars.return_value.all.return_value = [mock_history]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = DownloadHistoryOper(DownloadHistory, mock_db)
        result = await oper.get_recent(limit=10)
        assert len(result) == 1
