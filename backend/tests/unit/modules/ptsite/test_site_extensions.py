"""PT 站点扩展测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.site.models import SiteConfig, TorrentInfo
from app.modules.site.sites.mteam import MTeamSite
from app.modules.site.sites.opencd import OpenCDSite


class TestMTeamSite:
    """测试 MTeam 站点"""

    def test_site_initialization(self):
        """测试站点初始化"""
        config = SiteConfig(name="mteam", url="https://kp.m-team.cc", api_key="test-api-key")
        site = MTeamSite(config)

        assert site.name == "mteam"
        assert site.config.url == "https://kp.m-team.cc"

    @pytest.mark.asyncio
    async def test_search_torrents(self):
        """测试搜索种子"""
        config = SiteConfig(name="mteam", url="https://kp.m-team.cc", api_key="test-key")
        site = MTeamSite(config)

        # Mock httpx
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "12345",
                    "name": "Test Album FLAC",
                    "size": "1024000000",
                    "seeders": 10,
                    "leechers": 2,
                    "downloadUrl": "https://kp.m-team.cc/download/12345",
                }
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            results = await site.search("Test Album")

            assert len(results) == 1
            assert results[0].name == "Test Album FLAC"
            assert results[0].site == "mteam"

    @pytest.mark.asyncio
    async def test_get_torrent_detail(self):
        """测试获取种子详情"""
        config = SiteConfig(name="mteam", url="https://kp.m-team.cc", api_key="test-key")
        site = MTeamSite(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "12345",
                "name": "Test Album FLAC",
                "size": "1024000000",
                "description": "Test description",
                "files": ["01.flac", "02.flac"],
            }
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            detail = await site.get_detail("12345")

            assert detail is not None
            assert detail.name == "Test Album FLAC"


class TestOpenCDSite:
    """测试 OpenCD 站点"""

    def test_site_initialization(self):
        """测试站点初始化"""
        config = SiteConfig(name="opencd", url="https://open.cd", cookie="test-cookie")
        site = OpenCDSite(config)

        assert site.name == "opencd"
        assert site.config.url == "https://open.cd"

    @pytest.mark.asyncio
    async def test_search_torrents(self):
        """测试搜索种子"""
        config = SiteConfig(name="opencd", url="https://open.cd", cookie="test-cookie")
        site = OpenCDSite(config)

        # Mock httpx
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <table class="torrents">
            <tr>
                <td class="name"><a href="/details.php?id=12345">Test Album FLAC</a></td>
                <td class="size">1.02 GB</td>
                <td class="seeders">10</td>
            </tr>
        </table>
        </html>
        """

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await site.search("Test Album")

            assert len(results) == 1
            assert results[0].name == "Test Album FLAC"
            assert results[0].site == "opencd"

    @pytest.mark.asyncio
    async def test_get_download_url(self):
        """测试获取下载链接"""
        config = SiteConfig(name="opencd", url="https://open.cd", cookie="test-cookie")
        site = OpenCDSite(config)

        url = await site.get_download_url("12345")

        assert "download.php?id=12345" in url


class TestTorrentInfo:
    """测试 TorrentInfo 模型"""

    def test_torrent_info_creation(self):
        """测试种子信息创建"""
        torrent = TorrentInfo(
            id="12345",
            name="Test Album FLAC",
            site="mteam",
            size=1024000000,
            seeders=10,
            leechers=2,
            download_url="https://example.com/download",
        )

        assert torrent.id == "12345"
        assert torrent.name == "Test Album FLAC"
        assert torrent.size == 1024000000
