"""
SystemConfig 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSystemConfigOper:
    """SystemConfigOper 测试"""

    @pytest.mark.asyncio
    async def test_get_by_key(self):
        """测试通过 key 获取配置"""
        from app.db.models.system import SystemConfig
        from app.db.operations.system import SystemConfigOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_config = MagicMock(spec=SystemConfig)
        mock_config.key = "test_key"
        mock_config.value = "test_value"
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SystemConfigOper(mock_db)
        result = await oper.get_by_key("test_key")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all(self):
        """测试获取所有配置"""
        from app.db.models.system import SystemConfig
        from app.db.operations.system import SystemConfigOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_config = MagicMock(spec=SystemConfig)
        mock_result.scalars.return_value.all.return_value = [mock_config]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SystemConfigOper(mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_set_value(self):
        """测试设置配置值"""
        from app.db.models.system import SystemConfig
        from app.db.operations.system import SystemConfigOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_config = MagicMock(spec=SystemConfig)
        mock_config.key = "test_key"
        mock_config.value = "test_value"
        mock_session.execute.return_value = MagicMock()
        mock_session.commit = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SystemConfigOper(mock_db)
        result = await oper.set_value("test_key", "test_value")
        assert result is not None
