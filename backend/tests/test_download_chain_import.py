"""
DownloadChain 导入测试
"""


class TestDownloadChainImport:
    """DownloadChain 导入测试"""

    def test_download_chain_imports(self):
        """测试 DownloadChain 可导入"""
        from app.chain.download import DownloadChain

        assert DownloadChain is not None

    def test_download_chain_module_imports(self):
        """测试 download chain 模块可导入"""
        from app.chain import download

        assert download is not None
