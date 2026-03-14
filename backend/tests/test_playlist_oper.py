"""
PlaylistOper 测试
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestPlaylistOperMethods:
    """PlaylistOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_with_tracks(self):
        """测试获取带曲目的播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_playlist.id = 1
        mock_playlist.name = "Test Playlist"
        mock_result.scalar_one_or_none.return_value = mock_playlist
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(mock_db)
        result = await oper.get_with_tracks(1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_public_playlists(self):
        """测试获取公开播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_result.scalars.return_value.all.return_value = [mock_playlist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(mock_db)
        result = await oper.get_public_playlists()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_smart_playlists(self):
        """测试获取智能播放列表"""
        from app.db.models.playlist import Playlist
        from app.db.operations.playlist import PlaylistOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_playlist = MagicMock(spec=Playlist)
        mock_result.scalars.return_value.all.return_value = [mock_playlist]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = PlaylistOper(mock_db)
        result = await oper.get_smart_playlists()
        assert len(result) == 1


class TestSiteOperMethods:
    """SiteOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_enabled(self):
        """测试获取启用的站点"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_site.enabled = True
        mock_result.scalars.return_value.all.return_value = [mock_site]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(mock_db)
        result = await oper.get_enabled()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_downloader(self):
        """测试通过下载器获取站点"""
        from app.db.models.site import Site
        from app.db.operations.site import SiteOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_site = MagicMock(spec=Site)
        mock_result.scalars.return_value.all.return_value = [mock_site]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SiteOper(mock_db)
        result = await oper.get_by_downloader("qbittorrent")
        assert len(result) == 1


class TestSystemConfigOper:
    """SystemConfigOper 测试"""

    @pytest.mark.asyncio
    async def test_get_by_key(self):
        """测试通过key获取配置"""
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


class TestSubscribeOperMethods:
    """SubscribeOper 方法测试"""

    @pytest.mark.asyncio
    async def test_get_active(self):
        """测试获取活跃的订阅"""
        from app.db.models.subscribe import Subscribe
        from app.db.operations.subscribe import SubscribeOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_subscribe.enabled = True
        mock_result.scalars.return_value.all.return_value = [mock_subscribe]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SubscribeOper(mock_db)
        result = await oper.get_active()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_type(self):
        """测试通过类型获取订阅"""
        from app.db.models.subscribe import Subscribe
        from app.db.operations.subscribe import SubscribeOper

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_subscribe = MagicMock(spec=Subscribe)
        mock_result.scalars.return_value.all.return_value = [mock_subscribe]
        mock_session.execute.return_value = mock_result
        mock_db.get_session.return_value.__aenter__.return_value = mock_session

        oper = SubscribeOper(mock_db)
        result = await oper.get_by_type("artist")
        assert len(result) == 1
