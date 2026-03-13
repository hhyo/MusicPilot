"""
资源搜索链
处理资源搜索、结果排序和过滤
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Any

from app.core.cache import AsyncFileCache
from app.core.context import MusicInfo
from app.core.event import EventType, event_bus
from app.core.log import logger
from app.core.module import ModuleManager
from app.db import db_manager
from app.db.models.site import Site
from app.db.operations.site import SiteOper


class TorrentInfo:
    """种子信息"""

    def __init__(
        self,
        torrent_id: str,
        site_name: str,
        title: str,
        size: int,
        download_url: str,
        upload_time: datetime | None = None,
        seeders: int = 0,
        leechers: int = 0,
        is_free: bool = False,
        format: str = "FLAC",
        bitrate: str = "",
    ):
        self.torrent_id = torrent_id
        self.site_name = site_name
        self.title = title
        self.size = size
        self.download_url = download_url
        self.upload_time = upload_time
        self.seeders = seeders
        self.leechers = leechers
        self.is_free = is_free
        self.format = format
        self.bitrate = bitrate

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "torrent_id": self.torrent_id,
            "site_name": self.site_name,
            "title": self.title,
            "size": self.size,
            "download_url": self.download_url,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "seeders": self.seeders,
            "leechers": self.leechers,
            "is_free": self.is_free,
            "format": self.format,
            "bitrate": self.bitrate,
        }


class TorrentsChain:
    """
    资源搜索链
    负责搜索资源、排序结果、过滤结果
    """

    def __init__(self, cache_dir: str = "/tmp/torrent_cache", cache_ttl: int = 1800):
        """
        初始化资源搜索链

        Args:
            cache_dir: 缓存目录
            cache_ttl: 缓存过期时间（秒），默认 30 分钟
        """
        self.logger = logger
        self.site_oper = SiteOper(Site, db_manager)
        self.module_manager = ModuleManager()
        self.cache = AsyncFileCache(cache_dir, cache_ttl)

    def _generate_cache_key(
        self,
        music_info: MusicInfo,
        format: str,
        sites: list[str] | None = None,
    ) -> str:
        """
        生成缓存键

        Args:
            music_info: 音乐信息
            format: 音质格式
            sites: 站点列表

        Returns:
            缓存键
        """
        # 将所有参数组合成字符串
        cache_data = {
            "artist": music_info.artist or "",
            "album": music_info.album or "",
            "title": music_info.title or "",
            "format": format,
            "sites": sorted(sites) if sites else [],
        }

        # 生成哈希键
        data_str = str(cache_data)
        return f"torrent_search:{hashlib.md5(data_str.encode()).hexdigest()}"

    async def search(
        self,
        music_info: MusicInfo,
        sites: list[str] | None = None,
        format: str = "FLAC",
        min_size: int | None = None,
        max_size: int | None = None,
        use_cache: bool = True,
    ) -> list[TorrentInfo]:
        """
        搜索资源

        Args:
            music_info: 音乐信息
            sites: 站点列表（None 表示搜索所有启用的站点）
            format: 音质格式（FLAC, MP3, 等）
            min_size: 最小文件大小（字节）
            max_size: 最大文件大小（字节）
            use_cache: 是否使用缓存

        Returns:
            种子信息列表
        """
        self.logger.info(f"开始搜索资源: {music_info.artist} - {music_info.album}")

        # 1. 检查缓存
        cache_key = self._generate_cache_key(music_info, format, sites)
        if use_cache:
            cached_results = await self.cache.async_get(cache_key)
            if cached_results:
                self.logger.info(f"从缓存获取结果: {len(cached_results)} 个")
                # 缓存中的结果是 TorrentInfo.to_dict() 的结果，需要转换回来
                return [
                    TorrentInfo(
                        torrent_id=r["torrent_id"],
                        site_name=r["site_name"],
                        title=r["title"],
                        size=r["size"],
                        download_url=r["download_url"],
                        upload_time=(
                            datetime.fromisoformat(r["upload_time"])
                            if r.get("upload_time")
                            else None
                        ),
                        seeders=r.get("seeders", 0),
                        leechers=r.get("leechers", 0),
                        is_free=r.get("is_free", False),
                        format=r.get("format", "FLAC"),
                        bitrate=r.get("bitrate", ""),
                    )
                    for r in cached_results
                ]

        # 2. 获取启用的站点
        enabled_sites = await self.site_oper.get_enabled()
        if sites:
            enabled_sites = [s for s in enabled_sites if s.name in sites]

        if not enabled_sites:
            self.logger.warning("没有启用的站点")
            return []

        # 3. 并发搜索所有站点
        tasks = [self._search_site(site, music_info, format) for site in enabled_sites]

        # 使用 asyncio.gather 并发执行搜索
        site_results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        results = []
        for site, site_results in zip(enabled_sites, site_results_list, strict=False):
            if isinstance(site_results, Exception):
                self.logger.error(f"站点 {site.name} 搜索失败: {site_results}")
            else:
                results.extend(site_results)
                self.logger.info(f"站点 {site.name} 找到 {len(site_results)} 个结果")

        # 4. 排序结果
        sorted_results = self._sort_results(results)

        # 5. 过滤结果
        filtered_results = self._filter_results(sorted_results, format, min_size, max_size)

        self.logger.info(f"搜索完成，找到 {len(filtered_results)} 个结果")

        # 6. 缓存结果（转换为字典格式）
        if use_cache and filtered_results:
            await self.cache.async_set(
                cache_key, [r.to_dict() for r in filtered_results], ttl=self.cache.default_ttl
            )

        # 7. 发送搜索事件
        await event_bus.emit(
            EventType.TORRENT_SEARCH,
            {
                "music_info": music_info.__dict__,
                "result_count": len(filtered_results),
            },
        )

        return filtered_results

    async def _search_site(
        self, site: Site, music_info: MusicInfo, format: str
    ) -> list[TorrentInfo]:
        """
        搜索单个站点

        Args:
            site: 站点对象
            music_info: 音乐信息
            format: 音质格式

        Returns:
            种子信息列表
        """
        # 获取站点的站点模块
        site_modules = self.module_manager.get_running_modules_by_type("site")

        for module in site_modules:
            # 找到对应的站点模块（通过站点名称匹配）
            if hasattr(module, "site_info") and module.site_info.name == site.name:
                try:
                    # 根据音乐信息搜索
                    if music_info.artist and music_info.album:
                        # 搜索专辑
                        results = await module.search_album(
                            music_info.artist, music_info.album, format
                        )
                    elif music_info.artist:
                        # 搜索艺术家
                        results = await module.search_artist(music_info.artist, format)
                    elif music_info.title:
                        # 搜索标题
                        results = await module.search_title(music_info.title, format)
                    else:
                        # 使用完整关键词搜索
                        keyword = music_info.to_dict()
                        keyword_str = " ".join(str(v) for v in keyword.values() if v)
                        results = await module.search_torrent(keyword_str, format)

                    # 将 TorrentResult 转换为 TorrentInfo
                    return [
                        TorrentInfo(
                            torrent_id=result.torrent_id,
                            site_name=module.site_info.name,
                            title=result.title,
                            size=result.size,
                            download_url=result.download_url,
                            upload_time=result.upload_time,
                            seeders=result.seeders,
                            leechers=result.leechers,
                            is_free=result.is_free,
                            format=result.format,
                            bitrate=result.bitrate,
                        )
                        for result in results
                    ]
                except Exception as e:
                    self.logger.error(f"站点 {site.name} 搜索失败: {e}")
                    return []

        # 如果没有找到对应的站点模块，返回空列表
        self.logger.warning(f"未找到站点 {site.name} 的模块")
        return []

    def _sort_results(self, results: list[TorrentInfo]) -> list[TorrentInfo]:
        """
        排序结果

        排序规则：
        1. 免费种子优先
        2. 种子活跃度（seeders - leechers）
        3. 上传时间（越新越好）
        4. 文件大小（适中优先）

        Args:
            results: 种子信息列表

        Returns:
            排序后的种子信息列表
        """

        def sort_key(torrent: TorrentInfo) -> tuple:
            # 免费种子优先级最高
            free_priority = 1 if torrent.is_free else 0
            # 种子活跃度
            activity = torrent.seeders - torrent.leechers
            # 上传时间（越新越好，使用时间戳的负数）
            upload_time = -torrent.upload_time.timestamp() if torrent.upload_time else 0
            # 文件大小（适中优先，使用绝对偏差的负数）
            # 假设理想大小为 500MB (500 * 1024 * 1024)
            ideal_size = 500 * 1024 * 1024
            size_deviation = -abs(torrent.size - ideal_size)

            return (free_priority, activity, upload_time, size_deviation)

        return sorted(results, key=sort_key, reverse=True)

    def _filter_results(
        self,
        results: list[TorrentInfo],
        format: str,
        min_size: int | None,
        max_size: int | None,
    ) -> list[TorrentInfo]:
        """
        过滤结果

        Args:
            results: 种子信息列表
            format: 音质格式
            min_size: 最小文件大小
            max_size: 最大文件大小

        Returns:
            过滤后的种子信息列表
        """
        filtered = []

        for torrent in results:
            # 过滤格式
            if format and torrent.format != format:
                continue

            # 过滤大小
            if min_size is not None and torrent.size < min_size:
                continue
            if max_size is not None and torrent.size > max_size:
                continue

            filtered.append(torrent)

        return filtered

    async def search_artist(
        self,
        artist: str,
        sites: list[str] | None = None,
        format: str = "FLAC",
    ) -> list[TorrentInfo]:
        """
        搜索艺术家资源

        Args:
            artist: 艺术家名称
            sites: 站点列表
            format: 音质格式

        Returns:
            种子信息列表
        """
        music_info = MusicInfo(artist=artist)
        return await self.search(music_info, sites=sites, format=format)

    async def search_album(
        self,
        artist: str,
        album: str,
        sites: list[str] | None = None,
        format: str = "FLAC",
        min_size: int | None = None,
        max_size: int | None = None,
    ) -> list[TorrentInfo]:
        """
        搜索专辑资源

        Args:
            artist: 艺术家名称
            album: 专辑名称
            sites: 站点列表
            format: 音质格式
            min_size: 最小文件大小
            max_size: 最大文件大小

        Returns:
            种子信息列表
        """
        music_info = MusicInfo(artist=artist, album=album)
        return await self.search(
            music_info, sites=sites, format=format, min_size=min_size, max_size=max_size
        )

    async def search_title(
        self,
        title: str,
        sites: list[str] | None = None,
        format: str = "FLAC",
    ) -> list[TorrentInfo]:
        """
        搜索标题资源

        Args:
            title: 标题
            sites: 站点列表
            format: 音质格式

        Returns:
            种子信息列表
        """
        music_info = MusicInfo(title=title)
        return await self.search(music_info, sites=sites, format=format)
