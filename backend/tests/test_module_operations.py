"""
Module Operations 测试
"""


class TestModuleManagerOperations:
    """ModuleManager 操作测试"""

    def test_module_manager_import(self):
        """测试 ModuleManager 导入"""
        from app.core.module import ModuleManager

        assert ModuleManager is not None

    def test_module_manager_methods(self):
        """测试 ModuleManager 方法"""
        from app.core.module import ModuleManager

        methods = [m for m in dir(ModuleManager) if not m.startswith("_")]
        assert len(methods) > 0


class TestPluginManagerOperations:
    """PluginManager 操作测试"""

    def test_plugin_manager_import(self):
        """测试 PluginManager 导入"""
        from app.core.plugin import PluginManager

        assert PluginManager is not None

    def test_plugin_manager_methods(self):
        """测试 PluginManager 方法"""
        from app.core.plugin import PluginManager

        methods = [m for m in dir(PluginManager) if not m.startswith("_")]
        assert len(methods) > 0


class TestDownloaderModuleOperations:
    """DownloaderModule 操作测试"""

    def test_downloader_module_import(self):
        """测试 DownloaderModule 导入"""
        from app.modules.downloader_module import DownloaderModule

        assert DownloaderModule is not None

    def test_downloader_module_methods(self):
        """测试 DownloaderModule 方法"""
        from app.modules.downloader_module import DownloaderModule

        methods = [m for m in dir(DownloaderModule) if not m.startswith("_")]
        assert len(methods) > 0


class TestBaseDownloaderOperations:
    """BaseDownloader 操作测试"""

    def test_base_downloader_import(self):
        """测试 DownloaderBase 导入"""
        from app.modules.downloader.base import DownloaderBase

        assert DownloaderBase is not None

    def test_base_downloader_methods(self):
        """测试 DownloaderBase 方法"""
        from app.modules.downloader.base import DownloaderBase

        methods = [m for m in dir(DownloaderBase) if not m.startswith("_")]
        assert len(methods) > 0


class TestChainOperations:
    """Chain 操作测试"""

    def test_chain_base_import(self):
        """测试 ChainBase 导入"""
        from app.core.chain import ChainBase

        assert ChainBase is not None

    def test_chain_base_methods(self):
        """测试 ChainBase 方法"""
        from app.core.chain import ChainBase

        methods = [m for m in dir(ChainBase) if not m.startswith("_")]
        assert len(methods) > 0
