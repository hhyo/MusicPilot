"""
资源搜索链
处理资源搜索、结果排序和过滤
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.log import logger
from app.core.context import MusicInfo
from app.core.event import event_bus, EventType
from app.db.operations.site import SiteOper
from app.db.models.site import Site
from app.db import db_manager


class TorrentInfo:
    """种子信息"""

    def __init__(
        self,
        torrent_id: str,
        site_name: str,
        title: str,
        size: int,
        download_url: str,
        upload_time: Optional[datetime] = None,
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

    def to_dict(self) -> Dict[str, Any]:
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

    def __init__(self):
        self.logger = logger
        self.site_oper = SiteOper(Site, db_manager)

    async def search(
        self,
        music_info: MusicInfo,
        sites: Optional[List[str]] = None,
        format: str = "FLAC",
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[TorrentInfo]:
        """
        搜索资源

        Args:
            music_info: 音乐信息
            sites: 站点列表（None 表示搜索所有启用的站点）
            format: 音质格式（FLAC, MP3, 等）
            min_size: 最小文件大小（字节）
            max_size: 最大文件大小（字节）

        Returns:
            种子信息列表
        """
        self.logger.info(f"开始搜索资源: {music_info.artist} - {music_info.album}")

        # 1. 获取启用的站点
        enabled_sites = await self.site_oper.get_enabled()
        if sites:
            enabled_sites = [s for s in enabled_sites if s.name in sites]

        if not enabled_sites:
            self.logger.warning("没有启用的站点")
            return []

        # 2. 并发搜索所有站点
        results = []
        for site in enabled_sites:
            try:
                site_results = await self._search_site(site, music_info, format)
                results.extend(site_results)
                self.logger.info(f"站点 {site.name} 找到 {len(site_results)} 个结果")
            except Exception as e:
                self.logger.error(f"站点 {site.name} 搜索失败: {e}")

        # 3. 排序结果
        sorted_results = self._sort_results(results)

        # 4. 过滤结果
        filtered_results = self._filter_results(
            sorted_results, format, min_size, max_size
        )

        self.logger.info(f"搜索完成，找到 {len(filtered_results)} 个结果")

        # 5. 发送搜索事件
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
    ) -> List[TorrentInfo]:
        """
        搜索单个站点

        Args:
            site: 站点对象
            music_info: 音乐信息
            format: 音质格式

        Returns:
            种子信息列表
        """
        # TODO: 调用站点模块的搜索方法
        # 这里需要根据站点类型调用对应的搜索模块
        # 目前返回空列表
        self.logger.info(f"搜索站点: {site.name}")
        return []

    def _sort_results(self, results: List[TorrentInfo]) -> List[TorrentInfo]:
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
            upload_time = (
                -torrent.upload_time.timestamp()
                if torrent.upload_time
                else 0
            )
            # 文件大小（适中优先，使用绝对偏差的负数）
            # 假设理想大小为 500MB (500 * 1024 * 1024)
            ideal_size = 500 * 1024 * 1024
            size_deviation = -abs(torrent.size - ideal_size)

            return (free_priority, activity, upload_time, size_deviation)

        return sorted(results, key=sort_key, reverse=True)

    def _filter_results(
        self,
        results: List[TorrentInfo],
        format: str,
        min_size: Optional[int],
        max_size: Optional[int],
    ) -> List[TorrentInfo]:
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
        sites: Optional[List[str]] = None,
        format: str = "FLAC",
    ) -> List[TorrentInfo]:
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
        sites: Optional[List[str]] = None,
        format: str = "FLAC",
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[TorrentInfo]:
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
        sites: Optional[List[str]] = None,
        format: str = "FLAC",
    ) -> List[TorrentInfo]:
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