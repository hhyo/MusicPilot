"""
站点模块基类
所有站点模块都继承此类
"""

import contextlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import feedparser
import httpx

from app.core.module import ModuleBase


@dataclass
class SiteInfo:
    """站点信息"""

    name: str
    url: str
    domain: str
    cookie: str | None = None
    passkey: str | None = None
    username: str | None = None
    password: str | None = None
    proxy: str | None = None
    ua: str | None = None
    timeout: int = 30

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "url": self.url,
            "domain": self.domain,
            "cookie": self.cookie,
            "passkey": self.passkey,
            "username": self.username,
            "password": self.password,
            "proxy": self.proxy,
            "ua": self.ua,
            "timeout": self.timeout,
        }


@dataclass
class TorrentResult:
    """种子搜索结果"""

    torrent_id: str
    title: str
    size: int
    download_url: str
    upload_time: datetime | None = None
    seeders: int = 0
    leechers: int = 0
    is_free: bool = False
    format: str = "FLAC"
    bitrate: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "torrent_id": self.torrent_id,
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


class SiteModule(ModuleBase):
    """
    站点模块基类
    所有站点模块都继承此类
    """

    module_type = "site"

    def __init__(self):
        super().__init__()
        self.site_info: SiteInfo | None = None
        self.client: httpx.AsyncClient | None = None

    def init_module(self, config: dict[str, Any] | None = None):
        """
        初始化模块

        Args:
            config: 模块配置
        """
        super().init_module(config)

        if config:
            # 创建站点信息
            self.site_info = SiteInfo(
                name=config.get("name", ""),
                url=config.get("url", ""),
                domain=config.get("domain", ""),
                cookie=config.get("cookie"),
                passkey=config.get("passkey"),
                username=config.get("username"),
                password=config.get("password"),
                proxy=config.get("proxy"),
                ua=config.get("ua"),
                timeout=config.get("timeout", 30),
            )

            # 创建 HTTP 客户端
            client_kwargs = {
                "timeout": self.site_info.timeout,
                "headers": {"User-Agent": self.site_info.ua or "Mozilla/5.0"},
            }

            if self.site_info.cookie:
                client_kwargs["cookies"] = {"cookie": self.site_info.cookie}

            if self.site_info.proxy:
                client_kwargs["proxies"] = {
                    "http://": self.site_info.proxy,
                    "https://": self.site_info.proxy,
                }

            self.client = httpx.AsyncClient(**client_kwargs)

    def stop_module(self):
        """停止模块"""
        super().stop_module()

        # 关闭 HTTP 客户端
        if self.client:
            import asyncio

            with contextlib.suppress(Exception):
                asyncio.create_task(self.client.aclose())

    async def login(self) -> bool:
        """
        登录站点

        Returns:
            是否登录成功
        """
        self.logger.info(f"站点 {self.site_info.name} 登录")

        # 默认实现：使用 Cookie 直接返回成功
        # 子类可以重写此方法实现实际的登录逻辑
        return bool(self.site_info and self.site_info.cookie)

    async def search_torrent(
        self,
        keyword: str,
        format: str = "FLAC",
        page: int = 1,
    ) -> list[TorrentResult]:
        """
        搜索种子

        Args:
            keyword: 搜索关键词
            format: 音质格式
            page: 页码

        Returns:
            种子搜索结果列表
        """
        self.logger.info(f"搜索种子: {keyword}, 格式: {format}")

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 search_torrent 方法")

    async def get_torrent_details(self, torrent_id: str) -> dict[str, Any] | None:
        """
        获取种子详情

        Args:
            torrent_id: 种子 ID

        Returns:
            种子详情
        """
        self.logger.info(f"获取种子详情: {torrent_id}")

        # 子类可以重写此方法
        return None

    async def check_status(self) -> bool:
        """
        检查站点状态

        Returns:
            站点是否可用
        """
        self.logger.info(f"检查站点状态: {self.site_info.name}")

        if not self.client:
            return False

        try:
            response = await self.client.get(self.site_info.url)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"检查站点状态失败: {e}")
            return False

    async def parse_search_results(self, html: str) -> list[TorrentResult]:
        """
        解析搜索结果

        Args:
            html: HTML 内容

        Returns:
            种子搜索结果列表
        """
        # 子类可以重写此方法
        return []

    async def normalize_result(self, raw_result: Any) -> TorrentResult:
        """
        标准化搜索结果

        Args:
            raw_result: 原始结果

        Returns:
            标准化后的种子结果
        """
        # 子类可以重写此方法
        if isinstance(raw_result, TorrentResult):
            return raw_result

        # 默认实现：尝试从字典创建 TorrentResult
        if isinstance(raw_result, dict):
            return TorrentResult(
                torrent_id=raw_result.get("torrent_id", ""),
                title=raw_result.get("title", ""),
                size=raw_result.get("size", 0),
                download_url=raw_result.get("download_url", ""),
                upload_time=raw_result.get("upload_time"),
                seeders=raw_result.get("seeders", 0),
                leechers=raw_result.get("leechers", 0),
                is_free=raw_result.get("is_free", False),
                format=raw_result.get("format", "FLAC"),
                bitrate=raw_result.get("bitrate", ""),
            )

        raise ValueError("无法标准化结果")

    async def search_artist(
        self,
        artist: str,
        format: str = "FLAC",
        page: int = 1,
    ) -> list[TorrentResult]:
        """
        搜索艺术家

        Args:
            artist: 艺术家名称
            format: 音质格式
            page: 页码

        Returns:
            种子搜索结果列表
        """
        return await self.search_torrent(artist, format, page)

    async def search_album(
        self,
        artist: str,
        album: str,
        format: str = "FLAC",
        page: int = 1,
    ) -> list[TorrentResult]:
        """
        搜索专辑

        Args:
            artist: 艺术家名称
            album: 专辑名称
            format: 音质格式
            page: 页码

        Returns:
            种子搜索结果列表
        """
        keyword = f"{artist} {album}"
        return await self.search_torrent(keyword, format, page)

    async def search_title(
        self,
        title: str,
        format: str = "FLAC",
        page: int = 1,
    ) -> list[TorrentResult]:
        """
        搜索标题

        Args:
            title: 标题
            format: 音质格式
            page: 页码

        Returns:
            种子搜索结果列表
        """
        return await self.search_torrent(title, format, page)

    async def parse_rss(self, rss_url: str) -> list[TorrentResult]:
        """
        解析 RSS 种子源

        Args:
            rss_url: RSS 订阅 URL

        Returns:
            种子搜索结果列表
        """
        self.logger.info(f"解析 RSS: {rss_url}")

        if not self.client:
            self.logger.error("HTTP 客户端未初始化")
            return []

        try:
            # 获取 RSS 内容
            response = await self.client.get(rss_url)
            response.raise_for_status()

            # 解析 RSS
            feed = feedparser.parse(response.text)

            results = []
            for entry in feed.entries:
                try:
                    # 解析上传时间
                    upload_time = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        upload_time = datetime(*entry.published_parsed[:6])

                    # 解析种子大小（从标题或描述中提取）
                    size = 0
                    if hasattr(entry, "size"):
                        size = entry.size
                    elif hasattr(entry, "description"):
                        # 尝试从描述中提取大小
                        import re

                        size_match = re.search(
                            r"(\d+(?:\.\d+)?)\s*(GB|MB|KB)", entry.description, re.IGNORECASE
                        )
                        if size_match:
                            value = float(size_match.group(1))
                            unit = size_match.group(2).upper()
                            if unit == "GB":
                                size = int(value * 1024 * 1024 * 1024)
                            elif unit == "MB":
                                size = int(value * 1024 * 1024)
                            elif unit == "KB":
                                size = int(value * 1024)

                    # 检查是否免费
                    is_free = False
                    title_lower = entry.title.lower() if hasattr(entry, "title") else ""
                    if "free" in title_lower or "免费" in title_lower:
                        is_free = True

                    # 推断格式
                    format = "FLAC"
                    if "mp3" in title_lower:
                        format = "MP3"
                    elif "ape" in title_lower:
                        format = "APE"

                    # 创建 TorrentResult
                    torrent_id = getattr(entry, "id", str(hash(entry.get("link", ""))))
                    download_url = entry.get("link", "")
                    title = entry.get("title", "")

                    # 获取种子数和下载数（如果有）
                    seeders = getattr(entry, "seeders", 0)
                    leechers = getattr(entry, "leechers", 0)

                    # 如果是 NexusPHP 类型的站点，可能会在 torrent 属性中
                    if hasattr(entry, "torrent"):
                        seeders = getattr(entry.torrent, "seeders", seeders)
                        leechers = getattr(entry.torrent, "leechers", leechers)
                        size = getattr(entry.torrent, "contentLength", size)
                        download_url = getattr(entry.torrent, "downloadUrl", download_url)

                    result = TorrentResult(
                        torrent_id=torrent_id,
                        title=title,
                        size=size,
                        download_url=download_url,
                        upload_time=upload_time,
                        seeders=seeders,
                        leechers=leechers,
                        is_free=is_free,
                        format=format,
                        bitrate="",
                    )

                    results.append(result)

                except Exception as e:
                    self.logger.warning(f"解析 RSS 条目失败: {e}")
                    continue

            self.logger.info(f"解析 RSS 完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            self.logger.error(f"解析 RSS 失败: {e}")
            return []
