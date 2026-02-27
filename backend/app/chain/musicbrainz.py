"""
MusicBrainz 链
MusicBrainz 专用链
"""

from typing import List, Dict, Any, Optional

from app.chain import ChainBase
from app.core.log import logger


class MusicBrainzChain(ChainBase):
    """
    MusicBrainz 链
    专门处理 MusicBrainz 相关操作
    """

    async def search_artist(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索艺术家

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            艺术家列表
        """
        self.logger.info(f"搜索艺术家: {query}")

        # 检查缓存
        cache_key = f"mb_artist_search:{query}:{limit}"
        cached = self.get_cache(cache_key)
        if cached:
            return cached

        # 调用 MusicBrainz 模块
        results = await self.run_module("musicbrainz", "search_artist", query, limit)

        # 缓存结果
        self.set_cache(cache_key, results, ttl=86400)  # 24小时

        return results

    async def get_artist_discography(self, musicbrainz_id: str) -> Dict[str, Any]:
        """
        获取艺术家作品集

        Args:
            musicbrainz_id: MusicBrainz 艺术家 ID

        Returns:
            艺术家详情和作品集
        """
        self.logger.info(f"获取艺术家作品集: {musicbrainz_id}")

        # 检查缓存
        cache_key = f"mb_artist_discog:{musicbrainz_id}"
        cached = self.get_cache(cache_key)
        if cached:
            return cached

        # 调用 MusicBrainz 模块
        result = await self.run_module("musicbrainz", "get_artist_info", musicbrainz_id)

        # 缓存结果
        self.set_cache(cache_key, result, ttl=86400)

        return result

    async def search_album(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索专辑

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            专辑列表
        """
        self.logger.info(f"搜索专辑: {query}")

        # 检查缓存
        cache_key = f"mb_album_search:{query}:{limit}"
        cached = self.get_cache(cache_key)
        if cached:
            return cached

        # 调用 MusicBrainz 模块
        results = await self.run_module("musicbrainz", "search_album", query, limit)

        # 缓存结果
        self.set_cache(cache_key, results, ttl=86400)

        return results

    async def get_album_info(self, musicbrainz_id: str) -> Optional[Dict[str, Any]]:
        """
        获取专辑详情

        Args:
            musicbrainz_id: MusicBrainz 专辑 ID

        Returns:
            专辑详情
        """
        self.logger.info(f"获取专辑详情: {musicbrainz_id}")

        # 检查缓存
        cache_key = f"mb_album_info:{musicbrainz_id}"
        cached = self.get_cache(cache_key)
        if cached:
            return cached

        # 调用 MusicBrainz 模块
        result = await self.run_module("musicbrainz", "get_album_info", musicbrainz_id)

        # 缓存结果
        self.set_cache(cache_key, result, ttl=86400)

        return result

    async def search_track(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索曲目

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            曲目列表
        """
        self.logger.info(f"搜索曲目: {query}")

        # 检查缓存
        cache_key = f"mb_track_search:{query}:{limit}"
        cached = self.get_cache(cache_key)
        if cached:
            return cached

        # 调用 MusicBrainz 模块
        results = await self.run_module("musicbrainz", "search_track", query, limit)

        # 缓存结果
        self.set_cache(cache_key, results, ttl=3600)  # 1小时

        return results

    async def get_track_info(self, musicbrainz_id: str) -> Optional[Dict[str, Any]]:
        """
        获取曲目详情

        Args:
            musicbrainz_id: MusicBrainz 曲目 ID

        Returns:
            曲目详情
        """
        self.logger.info(f"获取曲目详情: {musicbrainz_id}")

        # 检查缓存
        cache_key = f"mb_track_info:{musicbrainz_id}"
        cached = self.get_cache(cache_key)
        if cached:
            return cached

        # 调用 MusicBrainz 模块
        result = await self.run_module("musicbrainz", "get_track_info", musicbrainz_id)

        # 缓存结果
        self.set_cache(cache_key, result, ttl=86400)

        return result

    async def download_cover(self, musicbrainz_id: str, cover_type: str = "front") -> Optional[str]:
        """
        下载封面图片

        Args:
            musicbrainz_id: MusicBrainz ID
            cover_type: 封面类型（front/back）

        Returns:
            保存的文件路径
        """
        self.logger.info(f"下载封面: {musicbrainz_id}")

        # 调用 MusicBrainz 模块
        result = await self.run_module("musicbrainz", "download_cover", musicbrainz_id, cover_type)

        return result
