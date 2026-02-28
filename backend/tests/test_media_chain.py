"""
MediaChain 单元测试
测试媒体服务器同步功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.media import MediaChain


class TestMediaChain:
    """MediaChain 测试类"""

    @pytest.fixture
    def chain(self):
        """创建 MediaChain 实例"""
        mock_db_manager = MagicMock()
        chain = MediaChain(db_manager=mock_db_manager)
        return chain

    @pytest.fixture
    def mock_server(self):
        """创建模拟媒体服务器"""
        server = MagicMock()
        server.id = 1
        server.type = "plex"
        server.name = "Test Plex"
        return server

    # ==================== scan_library 测试 ====================

    @pytest.mark.asyncio
    async def test_scan_library_plex(self, chain, mock_server):
        """测试扫描 Plex 音乐库"""
        mock_tracks = [MagicMock(id=1), MagicMock(id=2)]

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=mock_server)
            mock_media_oper_class.return_value = mock_media_oper

            with patch("app.db.operations.track.TrackOper") as mock_track_oper_class:
                mock_track_oper = AsyncMock()
                mock_track_oper.get_all = AsyncMock(return_value=mock_tracks)
                mock_track_oper_class.return_value = mock_track_oper

                with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
                    mock_run.return_value = {"success": True, "scanned": 2}

                    result = await chain.scan_library(1)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_scan_library_jellyfin(self, chain):
        """测试扫描 Jellyfin 音乐库"""
        mock_server = MagicMock()
        mock_server.id = 2
        mock_server.type = "jellyfin"
        mock_tracks = [MagicMock(id=1)]

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=mock_server)
            mock_media_oper_class.return_value = mock_media_oper

            with patch("app.db.operations.track.TrackOper") as mock_track_oper_class:
                mock_track_oper = AsyncMock()
                mock_track_oper.get_all = AsyncMock(return_value=mock_tracks)
                mock_track_oper_class.return_value = mock_track_oper

                with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
                    mock_run.return_value = {"success": True}

                    result = await chain.scan_library(2)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_scan_library_server_not_found(self, chain):
        """测试扫描不存在的媒体服务器"""
        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=None)
            mock_media_oper_class.return_value = mock_media_oper

            result = await chain.scan_library(999)

        assert result["success"] is False
        assert "不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_scan_library_unsupported_type(self, chain):
        """测试扫描不支持的媒体服务器类型"""
        mock_server = MagicMock()
        mock_server.id = 3
        mock_server.type = "unsupported"

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=mock_server)
            mock_media_oper_class.return_value = mock_media_oper

            with patch("app.db.operations.track.TrackOper") as mock_track_oper_class:
                mock_track_oper = AsyncMock()
                mock_track_oper.get_all = AsyncMock(return_value=[])
                mock_track_oper_class.return_value = mock_track_oper

                result = await chain.scan_library(3)

        assert result["success"] is False
        assert "不支持" in result["error"]

    # ==================== sync_metadata 测试 ====================

    @pytest.mark.asyncio
    async def test_sync_metadata_success(self, chain, mock_server):
        """测试同步元数据成功"""
        mock_tracks = [MagicMock(id=1)]

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=mock_server)
            mock_media_oper_class.return_value = mock_media_oper

            with patch("app.db.operations.track.TrackOper") as mock_track_oper_class:
                mock_track_oper = AsyncMock()
                mock_track_oper.get_all = AsyncMock(return_value=mock_tracks)
                mock_track_oper_class.return_value = mock_track_oper

                with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
                    mock_run.return_value = {"success": True}

                    result = await chain.sync_metadata(1)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_sync_metadata_server_not_found(self, chain):
        """测试同步元数据时服务器不存在"""
        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=None)
            mock_media_oper_class.return_value = mock_media_oper

            result = await chain.sync_metadata(999)

        assert result["success"] is False

    # ==================== sync_playback 测试 ====================

    @pytest.mark.asyncio
    async def test_sync_playback(self, chain, mock_server):
        """测试同步播放状态"""
        session_data = {"track_id": 1, "position": 30}

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_enabled = AsyncMock(return_value=[mock_server])
            mock_media_oper_class.return_value = mock_media_oper

            with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
                await chain.sync_playback(session_data)

        mock_run.assert_called()

    @pytest.mark.asyncio
    async def test_sync_playback_multiple_servers(self, chain):
        """测试同步到多个服务器"""
        mock_plex = MagicMock()
        mock_plex.type = "plex"
        mock_jellyfin = MagicMock()
        mock_jellyfin.type = "jellyfin"
        
        session_data = {"track_id": 1}

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_enabled = AsyncMock(return_value=[mock_plex, mock_jellyfin])
            mock_media_oper_class.return_value = mock_media_oper

            with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
                await chain.sync_playback(session_data)

        # 应该调用两次（两个服务器）
        assert mock_run.call_count == 2

    # ==================== sync_stop 测试 ====================

    @pytest.mark.asyncio
    async def test_sync_stop(self, chain, mock_server):
        """测试同步停止状态"""
        session_data = {"track_id": 1}

        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_enabled = AsyncMock(return_value=[mock_server])
            mock_media_oper_class.return_value = mock_media_oper

            with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
                await chain.sync_stop(session_data)

        mock_run.assert_called()

    # ==================== get_status 测试 ====================

    @pytest.mark.asyncio
    async def test_get_status_connected(self, chain, mock_server):
        """测试获取服务器状态（已连接）"""
        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=mock_server)
            mock_media_oper.test_connection = AsyncMock(return_value=(True, "连接成功"))
            mock_media_oper_class.return_value = mock_media_oper

            result = await chain.get_status(1)

        assert result["connected"] is True
        assert result["type"] == "plex"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, chain):
        """测试获取不存在服务器的状态"""
        with patch("app.db.operations.media.MediaServerOper") as mock_media_oper_class:
            mock_media_oper = AsyncMock()
            mock_media_oper.get_by_id = AsyncMock(return_value=None)
            mock_media_oper_class.return_value = mock_media_oper

            result = await chain.get_status(999)

        assert result["success"] is False
