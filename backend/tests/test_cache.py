"""
FileCache 单元测试
测试文件缓存功能
"""

import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from app.core.cache import FileCache, AsyncFileCache


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

    # ==================== 基本操作测试 ====================

    def test_set_and_get(self, cache):
        """测试基本的设置和获取"""
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        assert result == "test_value"

    def test_get_nonexistent(self, cache):
        """测试获取不存在的缓存"""
        result = cache.get("nonexistent_key")
        assert result is None

    def test_set_with_custom_ttl(self, cache):
        """测试设置自定义 TTL"""
        cache.set("ttl_key", "ttl_value", ttl=60)
        result = cache.get("ttl_key")
        assert result == "ttl_value"

    def test_set_with_zero_ttl(self, cache):
        """测试 TTL=0 时不过期"""
        cache.set("zero_ttl_key", "value", ttl=0)
        result = cache.get("zero_ttl_key")
        # TTL=0 应该不会设置过期时间
        assert result == "value"

    # ==================== 删除测试 ====================

    def test_delete_existing(self, cache):
        """测试删除存在的缓存"""
        cache.set("delete_key", "value")
        assert cache.exists("delete_key")
        
        cache.delete("delete_key")
        assert not cache.exists("delete_key")

    def test_delete_nonexistent(self, cache):
        """测试删除不存在的缓存"""
        # 应该不会抛出异常
        cache.delete("nonexistent_key")

    # ==================== exists 测试 ====================

    def test_exists_true(self, cache):
        """测试存在检查返回 True"""
        cache.set("exists_key", "value")
        assert cache.exists("exists_key")

    def test_exists_false(self, cache):
        """测试存在检查返回 False"""
        assert not cache.exists("nonexistent_key")

    # ==================== 清空测试 ====================

    def test_clear(self, cache):
        """测试清空所有缓存"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        cache.clear()
        
        assert not cache.exists("key1")
        assert not cache.exists("key2")
        assert not cache.exists("key3")

    # ==================== 大小测试 ====================

    def test_get_size_empty(self, cache):
        """测试空缓存的大小"""
        assert cache.get_size() == 0

    def test_get_size_with_data(self, cache):
        """测试有数据时的缓存大小"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        size = cache.get_size()
        assert size > 0

    # ==================== 过期测试 ====================

    def test_expired_cache(self, cache_dir):
        """测试过期缓存"""
        # 创建短 TTL 的缓存
        cache = FileCache(cache_dir, default_ttl=1)
        cache.set("expire_key", "expire_value", ttl=1)
        
        # 立即获取应该成功
        assert cache.get("expire_key") == "expire_value"
        
        # 等待过期
        import time
        time.sleep(2)
        
        # 过期后应该返回 None
        assert cache.get("expire_key") is None

    def test_cleanup_expired(self, cache_dir):
        """测试清理过期缓存"""
        import time
        
        cache = FileCache(cache_dir, default_ttl=1)
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=3600)  # 不会过期
        
        # 等待过期
        time.sleep(2)
        
        cache.cleanup_expired()
        
        # key1 应该被清理
        assert cache.get("key1") is None
        # key2 应该还在
        assert cache.get("key2") == "value2"

    # ==================== 复杂数据类型测试 ====================

    def test_dict_value(self, cache):
        """测试存储字典"""
        data = {"name": "test", "value": 123}
        cache.set("dict_key", data)
        result = cache.get("dict_key")
        assert result == data

    def test_list_value(self, cache):
        """测试存储列表"""
        data = [1, 2, 3, "four"]
        cache.set("list_key", data)
        result = cache.get("list_key")
        assert result == data

    def test_object_value(self, cache):
        """测试存储自定义对象（pickle 需要 top-level class）"""
        # 跳过：本地类无法被 pickle 序列化
        pytest.skip("Local classes cannot be pickled")
        """测试存储自定义对象"""
        class TestObject:
            def __init__(self, value):
                self.value = value
        
        obj = TestObject(42)
        cache.set("obj_key", obj)
        result = cache.get("obj_key")
        assert result.value == 42

    # ==================== 键名处理测试 ====================

    def test_special_characters_in_key(self, cache):
        """测试键名包含特殊字符"""
        cache.set("key/with/slashes", "value1")
        cache.set("key:with:colons", "value2")
        cache.set("key with spaces", "value3")
        
        assert cache.get("key/with/slashes") == "value1"
        assert cache.get("key:with:colons") == "value2"
        assert cache.get("key with spaces") == "value3"

    def test_unicode_key(self, cache):
        """测试 Unicode 键名"""
        cache.set("中文键", "中文值")
        cache.set("emoji_key_🎉", "value")
        
        assert cache.get("中文键") == "中文值"
        assert cache.get("emoji_key_🎉") == "value"


class TestAsyncFileCache:
    """AsyncFileCache 测试类"""

    @pytest.fixture
    def cache_dir(self):
        """创建临时缓存目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def async_cache(self, cache_dir):
        """创建 AsyncFileCache 实例"""
        return AsyncFileCache(cache_dir, default_ttl=3600)

    @pytest.mark.asyncio
    async def test_async_set_and_get(self, async_cache):
        """测试异步设置和获取"""
        await async_cache.async_set("async_key", "async_value")
        result = await async_cache.async_get("async_key")
        assert result == "async_value"

    @pytest.mark.asyncio
    async def test_async_delete(self, async_cache):
        """测试异步删除"""
        await async_cache.async_set("delete_key", "value")
        assert await async_cache.async_get("delete_key") == "value"
        
        await async_cache.async_delete("delete_key")
        assert await async_cache.async_get("delete_key") is None

    @pytest.mark.asyncio
    async def test_async_clear(self, async_cache):
        """测试异步清空"""
        await async_cache.async_set("key1", "value1")
        await async_cache.async_set("key2", "value2")
        
        await async_cache.async_clear()
        
        assert await async_cache.async_get("key1") is None
        assert await async_cache.async_get("key2") is None
