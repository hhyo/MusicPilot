"""
SiteOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSiteOper:
    """SiteOper 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = MagicMock()
        mock.get_session.return_value.__aenter__ = AsyncMock()
        mock.get_session.return_value.__aexit__ = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_site_oper_imports(self):
        """测试 SiteOper 可导入"""
        from app.db.operations.site import SiteOper

        assert SiteOper is not None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_site_oper_get_all(self, mock_db):
        """测试获取所有站点"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_result.scalars.return_value.all.return_value = [mock_site]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(mock_db)
        result = await oper.get_all()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_site_oper_get_enabled(self, mock_db):
        """测试获取启用的站点"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(mock_db)
        result = await oper.get_enabled()
        assert result is not None
