"""
SubscribeChain 单元测试
测试订阅功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.subscribe import SubscribeChain


class TestSubscribeChain:
    """SubscribeChain 测试类"""

    @pytest.fixture
    def chain(self):
        """创建 SubscribeChain 实例"""
        with patch("app.chain.subscribe.db_manager"):
            with patch("app.chain.subscribe.SubscribeOper"):
                with patch("app.chain.subscribe.SubscribeReleaseOper"):
                    with patch("app.chain.subscribe.TorrentsChain"):
                        with patch("app.chain.subscribe.DownloaderChain"):
                            with patch("app.chain.subscribe.NeteaseDownloader"):
                                chain = SubscribeChain()
                                return chain

    # ==================== match_rules 测试 ====================

    def test_match_rules_no_rules(self, chain):
        """测试无规则时匹配成功"""
        result = chain.match_rules({})
        assert result is True

    def test_match_rules_format_match(self, chain):
        """测试格式匹配"""
        torrent_info = MagicMock(format="FLAC")
        rules = {"format": "FLAC"}
        result = chain.match_rules(rules, torrent_info)
        assert result is True

    def test_match_rules_format_not_match(self, chain):
        """测试格式不匹配"""
        torrent_info = MagicMock(format="MP3")
        rules = {"format": "FLAC"}
        result = chain.match_rules(rules, torrent_info)
        assert result is False

    def test_match_rules_min_size(self, chain):
        """测试最小大小检查"""
        torrent_info = MagicMock(size=100)
        rules = {"min_size": 50}
        result = chain.match_rules(rules, torrent_info)
        assert result is True

    def test_match_rules_min_size_not_match(self, chain):
        """测试最小大小不满足"""
        torrent_info = MagicMock(size=30)
        rules = {"min_size": 50}
        result = chain.match_rules(rules, torrent_info)
        assert result is False

    def test_match_rules_max_size(self, chain):
        """测试最大大小检查"""
        torrent_info = MagicMock(size=100)
        rules = {"max_size": 200}
        result = chain.match_rules(rules, torrent_info)
        assert result is True

    def test_match_rules_max_size_exceeded(self, chain):
        """测试超过最大大小"""
        torrent_info = MagicMock(size=300)
        rules = {"max_size": 200}
        result = chain.match_rules(rules, torrent_info)
        assert result is False

    def test_match_rules_min_bitrate(self, chain):
        """测试最小比特率检查"""
        torrent_info = MagicMock(bitrate="320kbps")
        rules = {"min_bitrate": 256}
        result = chain.match_rules(rules, torrent_info)
        assert result is True

    def test_match_rules_min_bitrate_not_match(self, chain):
        """测试比特率不满足"""
        torrent_info = MagicMock(bitrate="128kbps")
        rules = {"min_bitrate": 256}
        result = chain.match_rules(rules, torrent_info)
        assert result is False

    # ==================== push_download 测试 ====================

    @pytest.mark.asyncio
    async def test_push_download_success(self, chain):
        """测试推送下载成功"""
        chain.downloader_chain.push_torrent = AsyncMock(return_value="task-123")

        result = await chain.push_download(
            "http://example.com/torrent.torrent", "Test Album"
        )

        assert result["task_id"] == "task-123"
        assert result["status"] == "downloading"

    @pytest.mark.asyncio
    async def test_push_download_failure(self, chain):
        """测试推送下载失败"""
        chain.downloader_chain.push_torrent = AsyncMock(
            side_effect=Exception("Connection error")
        )

        result = await chain.push_download(
            "http://example.com/torrent.torrent", "Test Album"
        )

        assert result["status"] == "failed"
        assert "Connection error" in result["error"]

    # ==================== check_playlist 测试 ====================

    @pytest.mark.asyncio
    async def test_check_playlist_netease_playlist(self, chain):
        """测试检查网易云歌单"""
        mock_task = MagicMock()
        mock_task.title = "Test Song"
        mock_task.artist = "Test Artist"
        mock_task.album = "Test Album"
        mock_task.metadata = {
            "song_id": "12345",
            "duration": 180,
            "album_pic": "http://example.com/pic.jpg",
        }

        chain.netease_downloader.fetch_playlist = AsyncMock(return_value=[mock_task])
        chain.subscribe_release_oper.get_by_release_id = AsyncMock(return_value=None)
        chain.subscribe_release_oper.create = AsyncMock()

        # Mock subscribe
        mock_subscribe = MagicMock()
        mock_subscribe.type = "playlist"
        chain.subscribe_oper.get_by_id = AsyncMock(return_value=mock_subscribe)

        result = await chain.check_playlist(1, "playlist-123", "netease")

        assert len(result) == 1
        assert result[0]["title"] == "Test Song"

    @pytest.mark.asyncio
    async def test_check_playlist_netease_chart(self, chain):
        """测试检查网易云音乐榜单"""
        mock_task = MagicMock()
        mock_task.title = "Chart Song"
        mock_task.artist = "Chart Artist"
        mock_task.album = "Chart Album"
        mock_task.metadata = {"song_id": "54321"}

        chain.netease_downloader.fetch_chart = AsyncMock(return_value=[mock_task])
        chain.subscribe_release_oper.get_by_release_id = AsyncMock(return_value=None)
        chain.subscribe_release_oper.create = AsyncMock()

        # Mock subscribe
        mock_subscribe = MagicMock()
        mock_subscribe.type = "chart"
        chain.subscribe_oper.get_by_id = AsyncMock(return_value=mock_subscribe)

        result = await chain.check_playlist(1, "chart-123", "netease")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_check_playlist_qq_unsupported(self, chain):
        """测试 QQ 音乐暂不支持"""
        result = await chain.check_playlist(1, "qq-playlist", "qq")

        assert result == []

    @pytest.mark.asyncio
    async def test_check_playlist_unknown_source(self, chain):
        """测试未知来源类型"""
        result = await chain.check_playlist(1, "playlist-123", "unknown")

        assert result == []

    # ==================== check_all 测试 ====================

    @pytest.mark.asyncio
    async def test_check_all_no_subscribes(self, chain):
        """测试无订阅时检查"""
        chain.subscribe_oper.get_enabled = AsyncMock(return_value=[])

        with patch("app.chain.subscribe.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()
            result = await chain.check_all()

        assert result["total"] == 0
        assert result["processed"] == 0

    @pytest.mark.asyncio
    async def test_check_all_artist_subscribe(self, chain):
        """测试检查艺术家订阅"""
        mock_subscribe = MagicMock()
        mock_subscribe.id = 1
        mock_subscribe.type = "artist"
        mock_subscribe.musicbrainz_id = "mb-123"

        chain.subscribe_oper.get_enabled = AsyncMock(return_value=[mock_subscribe])
        chain.check_artist = AsyncMock(return_value=[])

        with patch("app.chain.subscribe.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()
            result = await chain.check_all()

        assert result["total"] == 1
        assert result["processed"] == 1

    @pytest.mark.asyncio
    async def test_check_all_album_subscribe(self, chain):
        """测试检查专辑订阅"""
        mock_subscribe = MagicMock()
        mock_subscribe.id = 1
        mock_subscribe.type = "album"
        mock_subscribe.musicbrainz_id = "mb-456"

        chain.subscribe_oper.get_enabled = AsyncMock(return_value=[mock_subscribe])
        chain.check_album = AsyncMock(return_value=None)

        with patch("app.chain.subscribe.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()
            result = await chain.check_all()

        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_check_all_with_error(self, chain):
        """测试检查时有错误"""
        mock_subscribe = MagicMock()
        mock_subscribe.id = 1
        mock_subscribe.type = "artist"
        mock_subscribe.musicbrainz_id = "mb-789"

        chain.subscribe_oper.get_enabled = AsyncMock(return_value=[mock_subscribe])
        chain.check_artist = AsyncMock(side_effect=Exception("Network error"))

        with patch("app.chain.subscribe.event_bus") as mock_event_bus:
            mock_event_bus.emit = AsyncMock()
            result = await chain.check_all()

        assert result["errors"] == 1

    # ==================== get_releases 测试 ====================

    @pytest.mark.asyncio
    async def test_get_releases(self, chain):
        """测试获取订阅发布记录"""
        mock_releases = [MagicMock(id=1), MagicMock(id=2)]
        chain.subscribe_release_oper.get_by_subscribe_id = AsyncMock(
            return_value=mock_releases
        )

        result = await chain.get_releases(1)

        assert len(result) == 2

    # ==================== process_album 测试 ====================

    @pytest.mark.asyncio
    async def test_process_album_no_results(self, chain):
        """测试处理专辑无结果"""
        chain.torrents_chain.search = AsyncMock(return_value=[])
        chain.match_rules = MagicMock(return_value=True)

        result = await chain.process_album("Artist", "Album", "mb-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_process_album_rules_not_match(self, chain):
        """测试专辑不匹配订阅规则"""
        chain.match_rules = MagicMock(return_value=False)

        result = await chain.process_album(
            "Artist", "Album", "mb-123", rules={"format": "FLAC"}
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_process_album_success(self, chain):
        """测试处理专辑成功"""
        mock_torrent = MagicMock()
        mock_torrent.download_url = "http://example.com/torrent.torrent"
        mock_torrent.title = "Test Album"
        mock_torrent.to_dict = MagicMock(return_value={"title": "Test Album"})

        chain.torrents_chain.search = AsyncMock(return_value=[mock_torrent])
        chain.match_rules = MagicMock(return_value=True)
        chain.push_download = AsyncMock(
            return_value={"task_id": "task-123", "status": "downloading"}
        )

        result = await chain.process_album("Artist", "Album", "mb-123")

        assert result is not None
        assert result["download_task"]["task_id"] == "task-123"
