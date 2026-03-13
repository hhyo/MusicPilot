"""
DownloadChain 简单测试
"""

import pytest


class TestDownloadChainSimple:
    """DownloadChain 简单测试"""

    @pytest.mark.asyncio
    async def test_download_chain_imports(self):
        """测试 DownloadChain 可导入"""
        from app.chain.download import DownloadChain

        assert DownloadChain is not None

    def test_download_chain_module(self):
        """测试 download chain 模块"""
        from app.chain import download

        assert download is not None
