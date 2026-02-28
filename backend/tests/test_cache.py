"""
FileCache 单元测试
测试文件缓存功能
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.cache import AsyncFileCache, FileCache


class TestFileCache:
    """FileCache 测试类"""

    @pytest.fixture
    def cache_dir(self):
        """创建临时缓存目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cache(self, cache_dir):
        """创建 FileCache 实例"""
        return FileCache(cache_dir, default_ttl=3600)

    # ==================== __init__ 测试 ====================

    def test_init_creates_directory(self, cache_dir):
        """测试初始化创建目录"""
        new_dir = Path(cache_dir) / "new_cache"
        assert not new_dir.exists()

        FileCache(new_dir)

        assert new_dir.exists()

    def test_init_default_ttl(self, cache_dir):
        """测试默认 TTL 设置"""
        cache = FileCache(cache_dir, default_ttl=7200)

        assert cache.default_ttl == 7200

    # ==================== set/get 测试 ====================

    def test_set_and_get(self, cache):
        """测试设置和获取缓存"""
        cache.set("test_key", {"data": "value"})

        result = cache.get("test_key")

        assert result == {"data": "value"}

    def test_get_nonexistent_key(self, cache):
        """测试获取不存在的缓存"""
        result = cache.get("nonexistent")

        assert result is None

    def test_set_with_custom_ttl(self, cache):
        """测试设置自定义 TTL"""
        cache.set("test_key", "value", ttl=60)

        result = cache.get("test_key")
        assert result == "value"

    def test_set_with_zero_ttl(self, cache):
        """测试 TTL 为 0 时缓存不过期"""
        cache.set("test_key", "value", ttl=0)

        result = cache.get("test_key")
        # TTL=0 意味着永不过期，应该能获取到
        assert result == "value"

    def test_get_expired_cache(self, cache):
        """测试获取过期的缓存"""
        # 设置一个短 TTL 并等待过期
        cache.set("test_key", "value", ttl=1)

        # 立即获取应该有值
        result_immediate = cache.get("test_key")
        assert result_immediate == "value"

        # 等待过期
        import time

        time.sleep(1.5)

        result = cache.get("test_key")
        assert result is None

    def test_set_overwrite(self, cache):
        """测试覆盖缓存"""
        cache.set("test_key", "value1")
        cache.set("test_key", "value2")

        result = cache.get("test_key")

        assert result == "value2"

    # ==================== delete 测试 ====================

    def test_delete_existing_cache(self, cache):
        """测试删除存在的缓存"""
        cache.set("test_key", "value")
        cache.delete("test_key")

        result = cache.get("test_key")
        assert result is None

    def test_delete_nonexistent_cache(self, cache):
        """测试删除不存在的缓存（不应报错）"""
        # 不应抛出异常
        cache.delete("nonexistent_key")

    # ==================== exists 测试 ====================

    def test_exists_true(self, cache):
        """测试缓存存在"""
        cache.set("test_key", "value")

        assert cache.exists("test_key") is True

    def test_exists_false(self, cache):
        """测试缓存不存在"""
        assert cache.exists("nonexistent") is False

    # ==================== clear 测试 ====================

    def test_clear(self, cache):
        """测试清空缓存"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    # ==================== get_size 测试 ====================

    def test_get_size_empty(self, cache):
        """测试空缓存大小"""
        size = cache.get_size()

        assert size == 0

    def test_get_size_with_data(self, cache):
        """测试有数据时的缓存大小"""
        cache.set("key1", "a" * 100)
        cache.set("key2", "b" * 200)

        size = cache.get_size()

        # 大小应该大于 0
        assert size > 0

    # ==================== cleanup_expired 测试 ====================

    def test_cleanup_expired(self, cache):
        """测试清理过期缓存"""
        import time

        cache.set("keep", "value1", ttl=3600)  # 不过期
        cache.set("expire", "value2", ttl=1)  # 1秒后过期

        # 等待过期
        time.sleep(1.5)

        cache.cleanup_expired()

        assert cache.exists("keep") is True
        assert cache.exists("expire") is False

    # ==================== 特殊字符键测试 ====================

    def test_special_characters_in_key(self, cache):
        """测试键包含特殊字符"""
        special_key = "key/with: special?chars*and spaces"
        cache.set(special_key, "value")

        result = cache.get(special_key)

        assert result == "value"

    # ==================== 复杂类型测试 ====================

    def test_cache_dict(self, cache):
        """测试缓存字典"""
        data = {"name": "test", "values": [1, 2, 3]}
        cache.set("dict_key", data)

        result = cache.get("dict_key")

        assert result == data

    def test_cache_list(self, cache):
        """测试缓存列表"""
        data = [1, 2, 3, 4, 5]
        cache.set("list_key", data)

        result = cache.get("list_key")

        assert result == data


class TestAsyncFileCache:
    """AsyncFileCache 测试类"""

    @pytest.fixture
    def cache_dir(self):
        """创建临时缓存目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cache(self, cache_dir):
        """创建 AsyncFileCache 实例"""
        return AsyncFileCache(cache_dir)

    # ==================== async_get/set 测试 ====================

    @pytest.mark.asyncio
    async def test_async_set_and_get(self, cache):
        """测试异步设置和获取"""
        await cache.async_set("async_key", "async_value")

        result = await cache.async_get("async_key")

        assert result == "async_value"

    @pytest.mark.asyncio
    async def test_async_get_nonexistent(self, cache):
        """测试异步获取不存在的缓存"""
        result = await cache.async_get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_async_delete(self, cache):
        """测试异步删除"""
        await cache.async_set("delete_key", "value")
        await cache.async_delete("delete_key")

        result = await cache.async_get("delete_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_clear(self, cache):
        """测试异步清空"""
        await cache.async_set("key1", "value1")
        await cache.async_set("key2", "value2")

        await cache.async_clear()

        assert await cache.async_get("key1") is None
        assert await cache.async_get("key2") is None

    @pytest.mark.asyncio
    async def test_async_cleanup_expired(self, cache):
        """测试异步清理过期"""
        import time

        await cache.async_set("keep", "value", ttl=3600)
        await cache.async_set("expire", "value", ttl=1)

        # 等待过期
        await asyncio.sleep(1.5)

        await cache.async_cleanup_expired()

        assert await cache.async_get("keep") == "value"
        assert await cache.async_get("expire") is None
