"""
文件缓存模块
提供文件和内存缓存功能
"""
import json
import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional, Union
from datetime import datetime, timedelta

from app.core.log import logger


class FileCache:
    """
    文件缓存类
    支持文件系统缓存和 TTL 过期时间
    """

    def __init__(self, cache_dir: Union[str, Path], default_ttl: int = 3600):
        """
        初始化文件缓存

        Args:
            cache_dir: 缓存目录
            default_ttl: 默认过期时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger

    def _get_cache_path(self, key: str) -> Path:
        """
        获取缓存文件路径

        Args:
            key: 缓存键

        Returns:
            缓存文件路径
        """
        # 使用 MD5 哈希作为文件名，避免特殊字符问题
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)

            # 检查是否过期
            expires_at = cache_data.get("expires_at")
            if expires_at and datetime.now() > expires_at:
                self.logger.debug(f"缓存已过期: {key}")
                cache_file.unlink(missing_ok=True)
                return None

            return cache_data.get("value")

        except Exception as e:
            self.logger.error(f"读取缓存失败: {key}, 错误: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
        """
        cache_file = self._get_cache_path(key)

        try:
            expires_at = None
            if ttl is not None:
                if ttl > 0:
                    expires_at = datetime.now() + timedelta(seconds=ttl)
            else:
                if self.default_ttl > 0:
                    expires_at = datetime.now() + timedelta(seconds=self.default_ttl)

            cache_data = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now(),
            }

            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            self.logger.debug(f"设置缓存: {key}, TTL: {ttl or self.default_ttl}s")

        except Exception as e:
            self.logger.error(f"设置缓存失败: {key}, 错误: {e}")

    def delete(self, key: str):
        """
        删除缓存

        Args:
            key: 缓存键
        """
        cache_file = self._get_cache_path(key)

        if cache_file.exists():
            try:
                cache_file.unlink()
                self.logger.debug(f"删除缓存: {key}")
            except Exception as e:
                self.logger.error(f"删除缓存失败: {key}, 错误: {e}")

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        return self.get(key) is not None

    def clear(self):
        """清空所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink(missing_ok=True)
            self.logger.info("清空所有缓存")
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")

    def get_size(self) -> int:
        """
        获取缓存目录大小（字节）

        Returns:
            缓存目录大小
        """
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))
            return total_size
        except Exception as e:
            self.logger.error(f"获取缓存大小失败: {e}")
            return 0

    def cleanup_expired(self):
        """清理所有过期的缓存"""
        try:
            now = datetime.now()
            cleaned = 0

            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, "rb") as f:
                        cache_data = pickle.load(f)

                    expires_at = cache_data.get("expires_at")
                    if expires_at and now > expires_at:
                        cache_file.unlink(missing_ok=True)
                        cleaned += 1

                except Exception:
                    cache_file.unlink(missing_ok=True)
                    cleaned += 1

            self.logger.info(f"清理过期缓存完成，清理了 {cleaned} 个文件")

        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {e}")


class AsyncFileCache(FileCache):
    """
    异步文件缓存类
    支持异步操作
    """
    import asyncio

    async def async_get(self, key: str) -> Optional[Any]:
        """
        异步获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值
        """
        # 在线程池中执行同步操作
        return await self.asyncio.get_event_loop().run_in_executor(
            None, self.get, key
        )

    async def async_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        异步设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        await self.asyncio.get_event_loop().run_in_executor(
            None, self.set, key, value, ttl
        )

    async def async_delete(self, key: str):
        """
        异步删除缓存

        Args:
            key: 缓存键
        """
        await self.asyncio.get_event_loop().run_in_executor(
            None, self.delete, key
        )

    async def async_clear(self):
        """异步清空所有缓存"""
        await self.asyncio.get_event_loop().run_in_executor(
            None, self.clear
        )

    async def async_cleanup_expired(self):
        """异步清理所有过期的缓存"""
        await self.asyncio.get_event_loop().run_in_executor(
            None, self.cleanup_expired
        )