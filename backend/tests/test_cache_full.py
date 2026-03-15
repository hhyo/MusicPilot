"""
Cache 完整测试
"""

import tempfile

import pytest


class TestFileCacheFull:
    """FileCache 完整测试"""

    def test_file_cache_imports(self):
        from app.core.cache import FileCache

        assert FileCache is not None

    def test_file_cache_creation(self):
        from app.core.cache import FileCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(tmpdir)
            assert cache is not None

    def test_file_cache_set_get(self):
        from app.core.cache import FileCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(tmpdir)
            cache.set("test_key", "test_value")
            result = cache.get("test_key")
            assert result == "test_value"

    def test_file_cache_delete(self):
        from app.core.cache import FileCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(tmpdir)
            cache.set("delete_key", "value")
            cache.delete("delete_key")
            result = cache.get("delete_key")
            assert result is None


class TestAsyncFileCacheFull:
    """AsyncFileCache 完整测试"""

    def test_async_file_cache_imports(self):
        from app.core.cache import AsyncFileCache

        assert AsyncFileCache is not None

    @pytest.mark.asyncio
    async def test_async_file_cache_creation(self):
        from app.core.cache import AsyncFileCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = AsyncFileCache(tmpdir)
            assert cache is not None

    def test_async_file_cache_set_get(self):
        from app.core.cache import AsyncFileCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = AsyncFileCache(tmpdir)
            cache.set("test_key", "test_value")
            result = cache.get("test_key")
            assert result == "test_value"


class TestCacheModuleFull:
    """Cache Module 完整测试"""

    def test_cache_module_imports(self):
        from app.core import cache

        assert cache is not None
