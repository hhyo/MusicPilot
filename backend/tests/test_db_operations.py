"""
数据库操作单元测试
测试 DatabaseManager 和 OperBase
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db import DatabaseManager, OperBase
from app.db.models.artist import Artist


class TestOperBase:
    """OperBase 基类测试"""

    @pytest.fixture
    def mock_db_manager(self):
        """创建模拟数据库管理器"""
        manager = MagicMock(spec=DatabaseManager)
        return manager

    @pytest.fixture
    def oper(self, mock_db_manager):
        """创建 OperBase 实例"""
        return OperBase(Artist, mock_db_manager)

    def _create_mock_session(self):
        """创建模拟会话"""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        return mock_session

    def _create_context_manager(self, mock_session):
        """创建异步上下文管理器"""

        @asynccontextmanager
        async def cm():
            yield mock_session

        return cm()

    # ==================== create 测试 ====================

    @pytest.mark.asyncio
    async def test_create_success(self, oper, mock_db_manager):
        """测试创建记录成功"""
        mock_session = self._create_mock_session()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.create(name="Test Artist")

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_kwargs(self, oper, mock_db_manager):
        """测试带参数创建记录"""
        mock_session = self._create_mock_session()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.create(
            name="Test Artist", musicbrainz_id="mb-123", image_url="http://example.com/image.jpg"
        )

        mock_session.add.assert_called_once()

    # ==================== get_by_id 测试 ====================

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, oper, mock_db_manager):
        """测试按 ID 查找记录成功"""
        mock_artist = MagicMock(spec=Artist)
        mock_artist.id = 1
        mock_artist.name = "Test Artist"

        mock_session = self._create_mock_session()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_artist)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.get_by_id(1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, oper, mock_db_manager):
        """测试按 ID 查找记录不存在"""
        mock_session = self._create_mock_session()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.get_by_id(999)

        assert result is None

    # ==================== get_all 测试 ====================

    @pytest.mark.asyncio
    async def test_get_all(self, oper, mock_db_manager):
        """测试获取所有记录"""
        mock_artists = [MagicMock(spec=Artist), MagicMock(spec=Artist)]

        mock_session = self._create_mock_session()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_artists)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.get_all()

        assert len(result) == 2

    # ==================== update 测试 ====================

    @pytest.mark.asyncio
    async def test_update_success(self, oper, mock_db_manager):
        """测试更新记录成功"""
        mock_artist = MagicMock(spec=Artist)
        mock_artist.id = 1
        mock_artist.name = "Original"

        mock_session = self._create_mock_session()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_artist)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.update(1, name="Updated Artist")

        mock_session.commit.assert_called_once()

    # ==================== delete 测试 ====================

    @pytest.mark.asyncio
    async def test_delete_success(self, oper, mock_db_manager):
        """测试删除记录成功"""
        mock_session = self._create_mock_session()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.delete(1)

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is True

    # ==================== count 测试 ====================

    @pytest.mark.asyncio
    async def test_count(self, oper, mock_db_manager):
        """测试计数"""
        mock_session = self._create_mock_session()
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=10)
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_db_manager.get_session = mock_get_session

        result = await oper.count()

        assert result == 10


class TestDatabaseManager:
    """DatabaseManager 测试"""

    def test_init_with_url(self):
        """测试使用 URL 初始化"""
        url = "sqlite+aiosqlite:///test.db"
        manager = DatabaseManager(url)

        assert manager.database_url == url

    def test_init_without_url(self):
        """测试不使用 URL 初始化（使用默认设置）"""
        with patch("app.db.settings") as mock_settings:
            mock_settings.database_url = "sqlite+aiosqlite:///default.db"
            manager = DatabaseManager()

            assert manager.database_url == "sqlite+aiosqlite:///default.db"

    def test_init_db(self):
        """测试初始化数据库"""
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        manager.init_db()

        assert manager._engine is not None
        assert manager._async_session_maker is not None

    @pytest.mark.asyncio
    async def test_get_session_before_init(self):
        """测试在初始化前获取会话"""
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")

        with pytest.raises(RuntimeError, match="数据库未初始化"):
            async with manager.get_session():
                pass

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """测试成功获取会话"""
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        manager.init_db()

        async with manager.get_session() as session:
            assert session is not None

    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭数据库连接"""
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        manager.init_db()

        await manager.close()

        # 关闭后引擎应该被释放

    def test_engine_property_before_init(self):
        """测试在初始化前访问引擎属性"""
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")

        with pytest.raises(RuntimeError, match="数据库未初始化"):
            _ = manager.engine

    def test_engine_property_after_init(self):
        """测试初始化后访问引擎属性"""
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        manager.init_db()

        assert manager.engine is not None
