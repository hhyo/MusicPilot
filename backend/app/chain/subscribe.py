"""
订阅链
处理艺术家、专辑、歌单、榜单订阅
"""

from typing import Any

from app.chain.downloader import DownloaderChain
from app.chain.torrents import TorrentsChain
from app.core.context import MusicInfo
from app.core.event import EventType, event_bus
from app.core.log import logger
from app.db import db_manager
from app.db.models.subscribe import Subscribe
from app.db.models.subscribe_release import SubscribeRelease
from app.db.operations.subscribe import SubscribeOper
from app.db.operations.subscribe_release import SubscribeReleaseOper
from app.modules.downloader.netease import NeteaseDownloader


class SubscribeChain:
    """
    订阅链
    负责检查订阅更新、发现新内容、下载新内容
    支持艺术家、专辑、歌单、榜单四种订阅类型
    """

    def __init__(self):
        self.logger = logger
        self.subscribe_oper = SubscribeOper(Subscribe, db_manager)
        self.subscribe_release_oper = SubscribeReleaseOper(SubscribeRelease, db_manager)
        self.torrents_chain = TorrentsChain()
        self.downloader_chain = DownloaderChain()
        self.netease_downloader = NeteaseDownloader()

    async def check_artist(self, subscribe_id: int, musicbrainz_id: str) -> list[dict[str, Any]]:
        """
        检查艺术家订阅

        Args:
            subscribe_id: 订阅 ID
            musicbrainz_id: MusicBrainz ID

        Returns:
            新专辑列表
        """
        self.logger.info(f"检查艺术家订阅: {subscribe_id} - {musicbrainz_id}")

        # TODO: 调用 MusicBrainz 模块获取艺术家的新专辑
        # 这里需要集成 MusicBrainzChain

        # 临时返回空列表
        releases = []

        # 记录到 SubscribeRelease
        for release in releases:
            await self.subscribe_release_oper.create(
                {
                    "subscribe_id": subscribe_id,
                    "release_type": "album",
                    "musicbrainz_id": release.get("id"),
                    "title": release.get("title"),
                    "artist": release.get("artist"),
                    "download_status": "pending",
                }
            )

        return releases

    async def check_album(self, subscribe_id: int, musicbrainz_id: str) -> dict[str, Any] | None:
        """
        检查专辑订阅

        Args:
            subscribe_id: 订阅 ID
            musicbrainz_id: MusicBrainz ID

        Returns:
            专辑信息
        """
        self.logger.info(f"检查专辑订阅: {subscribe_id} - {musicbrainz_id}")

        # TODO: 调用 MusicBrainz 模块获取专辑信息

        # 临时返回 None
        return None

    async def check_playlist(
        self, subscribe_id: int, playlist_id: str, source_type: str = "netease"
    ) -> list[dict[str, Any]]:
        """
        检查歌单/榜单订阅

        Args:
            subscribe_id: 订阅 ID
            playlist_id: 歌单/榜单 ID
            source_type: 来源类型（netease, qq）

        Returns:
            新歌曲列表
        """
        self.logger.info(f"检查歌单/榜单订阅: {subscribe_id} - {playlist_id} ({source_type})")

        songs = []

        try:
            if source_type == "netease":
                # 获取歌单或榜单
                if subscribe_id:  # 需要获取订阅类型
                    subscribe = await self.subscribe_oper.get_by_id(subscribe_id)
                    sub_type = subscribe.type if subscribe else "playlist"

                    if sub_type == "playlist":
                        # 抓取歌单
                        tasks = await self.netease_downloader.fetch_playlist(playlist_id)
                    elif sub_type == "chart":
                        # 抓取榜单
                        tasks = await self.netease_downloader.fetch_chart(playlist_id)
                    else:
                        self.logger.warning(f"未知的订阅类型: {sub_type}")
                        return []
                else:
                    # 默认作为歌单处理
                    tasks = await self.netease_downloader.fetch_playlist(playlist_id)

                # 转换为字典格式
                songs = [
                    {
                        "song_id": task.metadata.get("song_id"),
                        "title": task.title,
                        "artist": task.artist,
                        "album": task.album,
                        "source": "netease",
                        "duration": task.metadata.get("duration"),
                        "album_pic": task.metadata.get("album_pic"),
                    }
                    for task in tasks
                ]

                # 记录新歌曲到 SubscribeRelease
                for song in songs:
                    # 检查是否已记录
                    existing = await self.subscribe_release_oper.get_by_release_id(
                        subscribe_id, song["song_id"]
                    )
                    if not existing:
                        await self.subscribe_release_oper.create(
                            {
                                "subscribe_id": subscribe_id,
                                "release_type": "track",
                                "musicbrainz_id": song["song_id"],
                                "title": song["title"],
                                "artist": song["artist"],
                                "download_status": "pending",
                            }
                        )

            elif source_type == "qq":
                # TODO: 实现 QQ 音乐歌单/榜单抓取
                self.logger.warning("QQ 音乐歌单/榜单抓取暂未实现")
            else:
                self.logger.warning(f"未知的来源类型: {source_type}")

        except Exception as e:
            self.logger.error(f"检查歌单/榜单订阅失败: {e}")

        return songs

    async def process_album(
        self,
        artist: str,
        album: str,
        musicbrainz_id: str,
        rules: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        处理专辑搜索和下载

        Args:
            artist: 艺术家名称
            album: 专辑名称
            musicbrainz_id: MusicBrainz ID
            rules: 订阅规则

        Returns:
            下载任务信息
        """
        self.logger.info(f"处理专辑: {artist} - {album}")

        # 匹配订阅规则
        if rules and not self.match_rules(rules):
            self.logger.info("专辑不符合订阅规则，跳过下载")
            return None

        # 搜索种子资源
        music_info = MusicInfo(artist=artist, album=album)
        results = await self.torrents_chain.search(music_info)

        if not results:
            self.logger.warning(f"未找到专辑资源: {artist} - {album}")
            return None

        # 使用第一个结果
        torrent_info = results[0]

        # 推送下载
        download_task = await self.push_download(
            torrent_info.download_url,
            torrent_info.title,
        )

        return {
            "torrent": torrent_info.to_dict(),
            "download_task": download_task,
        }

    async def push_download(
        self,
        download_url: str,
        title: str,
        downloader: str = "qbittorrent",
    ) -> dict[str, Any]:
        """
        推送下载

        Args:
            download_url: 下载 URL
            title: 标题
            downloader: 下载器类型

        Returns:
            下载任务信息
        """
        self.logger.info(f"推送下载: {title}")

        try:
            task_id = await self.downloader_chain.push_torrent(
                torrent_url=download_url,
                download_dir="/downloads",  # TODO: 从配置获取
                site_name="musicpilot",
                downloader=downloader,
            )

            return {
                "task_id": task_id,
                "status": "downloading",
            }
        except Exception as e:
            self.logger.error(f"推送下载失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    def match_rules(self, rules: dict[str, Any], torrent_info: Any = None) -> bool:
        """
        匹配订阅规则

        Args:
            rules: 订阅规则
            torrent_info: 种子信息（可选）

        Returns:
            是否匹配
        """
        # 格式检查
        if "format" in rules and torrent_info and torrent_info.format != rules["format"]:
            return False

        # 大小检查
        if "min_size" in rules and torrent_info and torrent_info.size < rules["min_size"]:
            return False

        if "max_size" in rules and torrent_info and torrent_info.size > rules["max_size"]:
            return False

        # 比特率检查
        if "min_bitrate" in rules and torrent_info and torrent_info.bitrate:
            # 比特率解析（例如 "320kbps" -> 320）
            try:
                bitrate = int("".join(filter(str.isdigit, torrent_info.bitrate)))
                if bitrate < rules["min_bitrate"]:
                    return False
            except ValueError:
                pass

        return True

    async def check_all(self) -> dict[str, Any]:
        """
        检查所有订阅

        Returns:
            检查结果统计
        """
        self.logger.info("开始检查所有订阅")

        stats = {
            "total": 0,
            "processed": 0,
            "new_content": 0,
            "errors": 0,
        }

        # 获取所有启用的订阅
        subscribes = await self.subscribe_oper.get_enabled()
        stats["total"] = len(subscribes)

        for subscribe in subscribes:
            try:
                if subscribe.type == "artist":
                    releases = await self.check_artist(
                        subscribe.id,
                        subscribe.musicbrainz_id or "",
                    )
                    stats["new_content"] += len(releases)

                elif subscribe.type == "album":
                    release = await self.check_album(
                        subscribe.id,
                        subscribe.musicbrainz_id or "",
                    )
                    if release:
                        stats["new_content"] += 1

                elif subscribe.type in ("playlist", "chart"):
                    songs = await self.check_playlist(
                        subscribe.id,
                        subscribe.playlist_id or "",
                        subscribe.source_type,
                    )
                    stats["new_content"] += len(songs)

                stats["processed"] += 1

            except Exception as e:
                self.logger.error(f"检查订阅失败 ({subscribe.id}): {e}")
                stats["errors"] += 1

        # 发送订阅检查事件
        await event_bus.emit(
            EventType.SUBSCRIBE_CHECK,
            {
                "stats": stats,
            },
        )

        self.logger.info(f"订阅检查完成: {stats}")

        return stats

    async def get_releases(
        self,
        subscribe_id: int,
        limit: int = 100,
    ) -> list[SubscribeRelease]:
        """
        获取订阅的发布记录

        Args:
            subscribe_id: 订阅 ID
            limit: 返回数量限制

        Returns:
            发布记录列表
        """
        return await self.subscribe_release_oper.get_by_subscribe_id(
            subscribe_id,
            limit=limit,
        )
