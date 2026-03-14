"""
SystemConfigOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSystemConfigOper:
    """SystemConfigOper 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_system_config_oper_imports(self):
        """测试 SystemConfigOper 可导入"""
        from app.db.operations.system import SystemConfigOper

        assert SystemConfigOper is not None

    @pytest.mark.asyncio
    async def test_system_config_oper_get_all(self, mock_db):
        """测试获取所有系统配置"""
        from app.db.models.system import SystemConfig
        from app.db.operations.system import SystemConfigOper

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
    async def test_system_config_oper_get_by_key(self, mock_db):
        """测试通过 key 获取配置"""
        from app.db.models.system import SystemConfig
        from app.db.operations.system import SystemConfigOper

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
