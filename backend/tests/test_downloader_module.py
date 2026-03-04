"""
Downloader Module 测试
"""


class TestDownloaderModule:
    """Downloader Module 测试"""

    def test_downloader_module_imports(self):
        """测试 downloader_module 模块可导入"""
        from app.modules import downloader_module

        assert downloader_module is not None

    def test_downloader_module_class_imports(self):
        """测试 DownloaderModule 可导入"""
        from app.modules.downloader_module import DownloaderModule

        assert DownloaderModule is not None
