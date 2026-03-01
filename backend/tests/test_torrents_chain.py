"""
TorrentsChain 测试
"""

import pytest


class TestTorrentsChain:
    """TorrentsChain 测试"""

    @pytest.mark.asyncio
    async def test_torrents_chain_imports(self):
        """测试 TorrentsChain 可导入"""
        from app.chain.torrents import TorrentsChain
        assert TorrentsChain is not None

    def test_torrent_info_imports(self):
        """测试 TorrentInfo 可导入"""
        from app.chain.torrents import TorrentInfo
        assert TorrentInfo is not None


class TestTorrentInfo:
    """TorrentInfo 测试"""

    def test_torrent_info_creation(self):
        """测试 TorrentInfo 创建"""
        from app.chain.torrents import TorrentInfo
        # 验证类存在
        assert TorrentInfo is not None
