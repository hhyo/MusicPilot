"""
Netease Downloader 测试
"""

import pytest


class TestNeteaseDownloader:
    """Netease Downloader 测试"""

    def test_netease_downloader_imports(self):
        """测试 NeteaseDownloader 可导入"""
        from app.modules.downloader.netease import NeteaseDownloader
        assert NeteaseDownloader is not None

    def test_netease_downloader_module(self):
        """测试 netease downloader 模块"""
        from app.modules.downloader import netease
        assert netease is not None


class TestNeteaseDownloaderBase:
    """Netease Downloader Base 测试"""

    def test_downloader_base_imports(self):
        """测试 DownloaderBase 可导入"""
        from app.modules.downloader.base import DownloaderBase
        assert DownloaderBase is not None

    def test_downloader_module_imports(self):
        """测试 downloader 模块可导入"""
        from app.modules import downloader
        assert downloader is not None
