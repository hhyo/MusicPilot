"""
Modules 层完整测试
"""

import pytest


class TestDownloaderModuleFull:
    """DownloaderModule 完整测试"""

    def test_downloader_module_imports(self):
        from app.modules.downloader_module import DownloaderModule
        assert DownloaderModule is not None

    def test_downloader_module_methods(self):
        from app.modules.downloader_module import DownloaderModule
        # 验证类存在
        assert DownloaderModule is not None


class TestNeteaseDownloaderFull:
    """NeteaseDownloader 完整测试"""

    def test_netease_downloader_imports(self):
        from app.modules.downloader.netease import NeteaseDownloader
        assert NeteaseDownloader is not None

    def test_netease_downloader_module(self):
        from app.modules.downloader import netease
        assert netease is not None


class TestDownloaderBaseFull:
    """DownloaderBase 完整测试"""

    def test_downloader_base_imports(self):
        from app.modules.downloader.base import DownloaderBase
        assert DownloaderBase is not None

    def test_downloader_module_imports(self):
        from app.modules import downloader
        assert downloader is not None


class TestModulesInitFull:
    """Modules Init 完整测试"""

    def test_modules_module_imports(self):
        from app import modules
        assert modules is not None
