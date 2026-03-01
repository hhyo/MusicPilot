"""
LibraryOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestLibraryOper:
    """LibraryOper 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_library_oper_imports(self):
        """测试 LibraryOper 可导入"""
        from app.db.operations.library import LibraryOper
        assert LibraryOper is not None

    @pytest.mark.asyncio
    async def test_library_oper_get_by_id(self, mock_db):
        """测试通过 ID 获取媒体库"""
        from app.db.operations.library import LibraryOper
        from app.db.models.library import Library
        
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
    async def test_library_oper_get_all(self, mock_db):
        """测试获取所有媒体库"""
        from app.db.operations.library import LibraryOper
        from app.db.models.library import Library
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_library = MagicMock(spec=Library)
        mock_result.scalars.return_value.all.return_value = [mock_library]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        
        oper = LibraryOper(Library, mock_db)
        result = await oper.get_all()
        assert len(result) == 1
