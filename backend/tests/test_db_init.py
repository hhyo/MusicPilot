"""
数据库初始化测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseInit:
    """数据库初始化测试类"""

    @pytest.mark.asyncio
    async def test_init_database(self):
        """测试初始化数据库"""
        mock_manager = MagicMock()
        mock_manager.init_db = AsyncMock()
        mock_manager.create_tables = AsyncMock()

        with patch("app.db.init.db_manager", mock_manager), patch("app.db.init.logger"):
            from app.db.init import init_database

            await init_database()

            mock_manager.init_db.assert_called_once()
            mock_manager.create_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_drop_database(self):
        """测试删除数据库"""
        mock_manager = MagicMock()
        mock_manager.drop_tables = AsyncMock()

        with patch("app.db.init.db_manager", mock_manager), patch("app.db.init.logger"):
            from app.db.init import drop_database

            await drop_database()

            mock_manager.drop_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database(self):
        """测试关闭数据库连接"""
        mock_manager = MagicMock()
        mock_manager.close = AsyncMock()

        with patch("app.db.init.db_manager", mock_manager):
            from app.db.init import close_database

            await close_database()

            mock_manager.close.assert_called_once()
