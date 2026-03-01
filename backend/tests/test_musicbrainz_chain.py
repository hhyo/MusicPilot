"""
MusicBrainzChain 单元测试
测试 MusicBrainz 查询功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.chain.musicbrainz import MusicBrainzChain


class TestMusicBrainzChain:
    """MusicBrainzChain 测试类"""

    @pytest.fixture
    def chain(self):
        """创建 MusicBrainzChain 实例"""
        mock_db_manager = MagicMock()
        chain = MusicBrainzChain(db_manager=mock_db_manager)
        return chain

    # ==================== search_artist 测试 ====================

    @pytest.mark.asyncio
    async def test_search_artist(self, chain):
        """测试搜索艺术家"""
        mock_results = [
            {"id": "artist-1", "name": "Test Artist"},
            {"id": "artist-2", "name": "Another Artist"},
        ]

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_results

            result = await chain.search_artist("Test")

        assert len(result) == 2
        assert result[0]["name"] == "Test Artist"

    @pytest.mark.asyncio
    async def test_search_artist_with_limit(self, chain):
        """测试带限制的搜索艺术家"""
        mock_results = [{"id": "artist-1", "name": "Test Artist"}]

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_results

            result = await chain.search_artist("Test", limit=10)

        mock_run.assert_called_with("musicbrainz", "search_artist", "Test", 10)

    # ==================== get_artist_discography 测试 ====================

    @pytest.mark.asyncio
    async def test_get_artist_discography(self, chain):
        """测试获取艺术家作品集"""
        mock_result = {
            "id": "artist-1",
            "name": "Test Artist",
            "albums": [{"id": "album-1", "title": "Album 1"}],
        }

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            result = await chain.get_artist_discography("artist-1")

        assert result["id"] == "artist-1"
        assert len(result["albums"]) == 1

    # ==================== search_album 测试 ====================

    @pytest.mark.asyncio
    async def test_search_album(self, chain):
        """测试搜索专辑"""
        mock_results = [
            {"id": "album-1", "title": "Test Album"},
        ]

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_results

            result = await chain.search_album("Test Album")

        assert len(result) == 1
        assert result[0]["title"] == "Test Album"

    # ==================== get_album_info 测试 ====================

    @pytest.mark.asyncio
    async def test_get_album_info(self, chain):
        """测试获取专辑详情"""
        mock_result = {
            "id": "album-1",
            "title": "Test Album",
            "artist_credit": {"name": "Test Artist"},
        }

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            result = await chain.get_album_info("album-1")

        assert result["id"] == "album-1"

    @pytest.mark.asyncio
    async def test_get_album_info_not_found(self, chain):
        """测试获取不存在的专辑"""
        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = None

            result = await chain.get_album_info("nonexistent")

        assert result is None

    # ==================== search_track 测试 ====================

    @pytest.mark.asyncio
    async def test_search_track(self, chain):
        """测试搜索曲目"""
        mock_results = [
            {"id": "track-1", "title": "Test Track"},
        ]

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_results

            result = await chain.search_track("Test Track")

        assert len(result) == 1

    # ==================== get_track_info 测试 ====================

    @pytest.mark.asyncio
    async def test_get_track_info(self, chain):
        """测试获取曲目详情"""
        mock_result = {
            "id": "track-1",
            "title": "Test Track",
            "artist_credit": {"name": "Test Artist"},
        }

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            result = await chain.get_track_info("track-1")

        assert result["id"] == "track-1"

    # ==================== download_cover 测试 ====================

    @pytest.mark.asyncio
    async def test_download_cover(self, chain):
        """测试下载封面"""
        mock_result = "/path/to/cover.jpg"

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            result = await chain.download_cover("album-1")

        assert result == "/path/to/cover.jpg"

    @pytest.mark.asyncio
    async def test_download_cover_back(self, chain):
        """测试下载背面封面"""
        mock_result = "/path/to/back.jpg"

        with patch.object(chain, "run_module", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result

            result = await chain.download_cover("album-1", cover_type="back")

        mock_run.assert_called_with("musicbrainz", "download_cover", "album-1", "back")
