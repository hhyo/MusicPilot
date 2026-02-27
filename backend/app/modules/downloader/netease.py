"""
网易云音乐下载器
"""

from pathlib import Path
from typing import Any

import httpx

from .base import (
    DownloaderBase,
    DownloadQuality,
    DownloadSource,
    DownloadStatus,
    DownloadTask,
)


class NeteaseDownloader(DownloaderBase):
    """
    网易云音乐下载器

    支持搜索、下载、获取实际下载 URL
    """

    def __init__(self):
        super().__init__()
        self.source = DownloadSource.NETEASE
        self.supported_qualities = [
            DownloadQuality.LOSSLESS,
            DownloadQuality.HIGH,
            DownloadQuality.STANDARD,
        ]
        self.base_url = "https://music.163.com"
        self.api_url = "https://interface.music.163.com"
        self.weapi_url = "https://music.163.com/weapi"
        self.timeout = 30

    def init_setting(self) -> tuple[str, bool] | None:
        """
        初始化下载器设置

        Returns:
            (字段定义, 是否必需)
        """
        # 网易云音乐暂时不需要配置
        # 未来可以添加：登录账号、cookie 等
        return None

    def _map_quality(self, quality: DownloadQuality) -> str:
        """
        映射质量到网易云音乐格式

        Args:
            quality: 下载质量

        Returns:
            网易云音乐质量格式
        """
        quality_map = {
            DownloadQuality.LOSSLESS: "999000",  # FLAC 无损
            DownloadQuality.HIGH: "320000",  # 320kbps
            DownloadQuality.STANDARD: "128000",  # 128kbps
        }
        return quality_map.get(quality, "128000")

    def _map_level(self, quality: DownloadQuality) -> str:
        """
        映射质量到网易云音乐 level

        Args:
            quality: 下载质量

        Returns:
            level 字符串
        """
        level_map = {
            DownloadQuality.LOSSLESS: "lossless",
            DownloadQuality.HIGH: "exhigh",
            DownloadQuality.STANDARD: "standard",
        }
        return level_map.get(quality, "standard")

    async def search(
        self, keyword: str, limit: int = 20, quality: DownloadQuality | None = None
    ) -> list[DownloadTask]:
        """
        搜索音乐

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            quality: 目标质量（暂未使用）

        Returns:
            下载任务列表
        """
        # 使用 Web API 搜索
        search_url = f"{self.api_url}/api/search/get/web"
        params = {
            "s": keyword,
            "type": "1",  # 1 = 单曲
            "offset": "0",
            "limit": str(limit),
        }

        tasks = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200:
                    songs = data.get("result", {}).get("songs", [])
                    for song in songs:
                        # 获取艺术家名称
                        artist_name = None
                        if song.get("artists"):
                            artist_name = ", ".join(
                                [artist.get("name", "") for artist in song["artists"]]
                            )

                        # 获取专辑名称
                        album_name = (
                            song.get("album", {}).get("name") if song.get("album") else None
                        )

                        task = DownloadTask(
                            task_id=f"netease_{song['id']}",
                            url=str(song["id"]),
                            source=self.source,
                            quality=quality or DownloadQuality.STANDARD,
                            artist=artist_name,
                            album=album_name,
                            title=song.get("name"),
                            metadata={
                                "song_id": song["id"],
                                "artist_ids": [a.get("id") for a in song.get("artists", [])],
                                "album_id": (
                                    song.get("album", {}).get("id") if song.get("album") else None
                                ),
                                "duration": (
                                    song.get("duration") / 1000 if song.get("duration") else None
                                ),
                                "album_pic": (
                                    song.get("album", {}).get("picUrl")
                                    if song.get("album")
                                    else None
                                ),
                            },
                        )
                        tasks.append(task)

        except Exception as e:
            self.logger.error(f"搜索失败: {e}")

        return tasks

    async def get_url(self, url: str, quality: DownloadQuality = DownloadQuality.STANDARD) -> str:
        """
        获取实际下载 URL

        Args:
            url: 歌曲 ID
            quality: 目标质量

        Returns:
            实际下载 URL

        注意: 网易云音乐的获取下载 URL 接口需要特定的加密处理
        这里使用 Web API 的 player url 接口
        """
        # 使用 Web API 获取下载 URL
        download_url = f"{self.api_url}/api/song/enhance/player/url/v1"

        # 映射质量参数
        br = self._map_quality(quality)
        level = self._map_level(quality)

        params = {
            "ids": f"[{url}]",
            "br": br,
            "level": level,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(download_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200 and data.get("data"):
                    return data["data"][0].get("url", "")
                else:
                    error_msg = data.get("message", "未知错误")
                    raise ValueError(f"获取下载 URL 失败: {error_msg}")

        except Exception as e:
            self.logger.error(f"获取下载 URL 失败: {e}")
            raise

    async def download(
        self, task: DownloadTask, progress_callback: callable | None = None
    ) -> DownloadTask:
        """
        下载音乐

        Args:
            task: 下载任务
            progress_callback: 进度回调函数

        Returns:
            完成的下载任务
        """
        task.status = DownloadStatus.DOWNLOADING

        try:
            # 获取实际下载 URL
            download_url = await self.get_url(task.url, task.quality)

            if not download_url:
                raise ValueError("无法获取下载 URL，可能因为版权保护或未登录")

            self.logger.info(f"开始下载: {task.title} ({task.quality})")

            # 下载文件
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    # 获取文件大小
                    total_bytes = int(response.headers.get("content-length", 0))
                    task.total_bytes = total_bytes

                    # 确定目标路径
                    if task.target_path:
                        target_dir = Path(task.target_path)
                    else:
                        target_dir = Path("/tmp/downloads/netease")
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # 确定文件扩展名
                    ext = ".flac" if task.quality == DownloadQuality.LOSSLESS else ".mp3"
                    # 清理文件名
                    safe_title = "".join(
                        c if c.isalnum() or c in " -_()" else "_" for c in task.title or "unknown"
                    )
                    file_path = target_dir / f"{safe_title}{ext}"

                    # 下载文件
                    downloaded_bytes = 0
                    with open(file_path, "wb") as f:
                        async for chunk in response.aiter_bytes(8192):
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            task.downloaded_bytes = downloaded_bytes
                            task.progress = (
                                (downloaded_bytes / total_bytes) if total_bytes > 0 else 0
                            )

                            if progress_callback:
                                progress_callback(task)

            # 下载完成
            task.status = DownloadStatus.COMPLETED
            task.file_path = str(file_path)
            task.progress = 1.0

            self.logger.info(f"下载完成: {task.title} -> {file_path}")

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)
            self.logger.error(f"下载失败: {task.title} - {e}")

        return task

    async def get_song_detail(self, song_id: str) -> dict[str, Any] | None:
        """
        获取歌曲详细信息

        Args:
            song_id: 歌曲 ID

        Returns:
            歌曲详细信息
        """
        detail_url = f"{self.api_url}/api/song/detail"
        params = {"ids": f"[{song_id}]"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(detail_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200 and data.get("songs"):
                    return data["songs"][0]
        except Exception as e:
            self.logger.error(f"获取歌曲详情失败: {e}")

        return None

    async def get_artist_songs(self, artist_id: str, limit: int = 50) -> list[DownloadTask]:
        """
        获取艺术家的歌曲列表

        Args:
            artist_id: 艺术家 ID
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        # 艺术家歌曲 API
        artist_url = f"{self.api_url}/api/v1/artist/songs"
        params = {
            "id": artist_id,
            "limit": str(limit),
            "offset": "0",
        }

        tasks = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(artist_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200:
                    songs = data.get("songs", [])
                    for song in songs:
                        # 获取艺术家名称
                        artist_name = (
                            song.get("ar", [{}])[0].get("name") if song.get("ar") else None
                        )

                        # 获取专辑名称
                        album_name = song.get("al", {}).get("name") if song.get("al") else None

                        task = DownloadTask(
                            task_id=f"netease_{song['id']}",
                            url=str(song["id"]),
                            source=self.source,
                            quality=DownloadQuality.STANDARD,
                            artist=artist_name,
                            album=album_name,
                            title=song.get("name"),
                            metadata={
                                "song_id": song["id"],
                                "artist_ids": [a.get("id") for a in song.get("ar", [])],
                                "album_id": (
                                    song.get("al", {}).get("id") if song.get("al") else None
                                ),
                                "duration": song.get("dt") / 1000 if song.get("dt") else None,
                                "album_pic": (
                                    song.get("al", {}).get("picUrl") if song.get("al") else None
                                ),
                            },
                        )
                        tasks.append(task)

        except Exception as e:
            self.logger.error(f"获取艺术家歌曲失败: {e}")

        return tasks

    async def get_album_songs(self, album_id: str) -> list[DownloadTask]:
        """
        获取专辑的歌曲列表

        Args:
            album_id: 专辑 ID

        Returns:
            歌曲列表
        """
        # 专辑歌曲 API
        album_url = f"{self.api_url}/api/album/{album_id}"

        tasks = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(album_url)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200:
                    album_data = data.get("album", {})
                    songs = data.get("songs", [])

                    artist_name = None
                    if album_data.get("artists"):
                        artist_name = ", ".join(
                            [artist.get("name", "") for artist in album_data["artists"]]
                        )

                    album_name = album_data.get("name")

                    for song in songs:
                        task = DownloadTask(
                            task_id=f"netease_{song['id']}",
                            url=str(song["id"]),
                            source=self.source,
                            quality=DownloadQuality.STANDARD,
                            artist=artist_name,
                            album=album_name,
                            title=song.get("name"),
                            metadata={
                                "song_id": song["id"],
                                "artist_ids": [a.get("id") for a in song.get("ar", [])],
                                "album_id": album_id,
                                "duration": song.get("dt") / 1000 if song.get("dt") else None,
                                "album_pic": album_data.get("picUrl"),
                            },
                        )
                        tasks.append(task)

        except Exception as e:
            self.logger.error(f"获取专辑歌曲失败: {e}")

        return tasks

    async def fetch_playlist(self, playlist_id: str) -> list[DownloadTask]:
        """
        抓取网易云音乐歌单

        Args:
            playlist_id: 歌单 ID

        Returns:
            歌曲列表
        """
        self.logger.info(f"抓取网易云音乐歌单: {playlist_id}")

        # 歌单详情 API
        playlist_url = f"{self.api_url}/api/v6/playlist/detail"
        params = {"id": playlist_id}

        tasks = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(playlist_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200:
                    playlist_data = data.get("playlist", {})
                    tracks = playlist_data.get("tracks", [])

                    # 歌单名称
                    playlist_name = playlist_data.get("name", "")
                    self.logger.info(f"歌单 '{playlist_name}' 包含 {len(tracks)} 首歌曲")

                    for track in tracks:
                        # 获取艺术家名称
                        artist_name = None
                        if track.get("ar"):
                            artist_name = ", ".join(
                                [artist.get("name", "") for artist in track["ar"]]
                            )

                        # 获取专辑名称
                        album_name = None
                        if track.get("al"):
                            album_name = track["al"].get("name")

                        # 创建下载任务
                        task = DownloadTask(
                            task_id=f"netease_{track['id']}",
                            url=str(track["id"]),
                            source=self.source,
                            quality=DownloadQuality.STANDARD,
                            artist=artist_name,
                            album=album_name,
                            title=track.get("name"),
                            metadata={
                                "song_id": track["id"],
                                "artist_ids": [a.get("id") for a in track.get("ar", [])],
                                "album_id": (
                                    track.get("al", {}).get("id") if track.get("al") else None
                                ),
                                "duration": track.get("dt") / 1000 if track.get("dt") else None,
                                "album_pic": (
                                    track.get("al", {}).get("picUrl") if track.get("al") else None
                                ),
                                "playlist_id": playlist_id,
                                "playlist_name": playlist_name,
                            },
                        )
                        tasks.append(task)

                    self.logger.info(f"歌单抓取完成，获取 {len(tasks)} 首歌曲")

        except Exception as e:
            self.logger.error(f"抓取歌单失败: {e}")

        return tasks

    async def fetch_chart(self, chart_id: str = "19723756") -> list[DownloadTask]:
        """
        抓取网易云音乐榜单

        Args:
            chart_id: 榜单 ID，默认飙升榜 (19723756)
                常见榜单:
                - 飙升榜: 19723756
                - 热歌榜: 3779629
                - 新歌榜: 2884035
                - 原创榜: 2884035
                - 说唱榜: 991319590

        Returns:
            歌曲列表
        """
        self.logger.info(f"抓取网易云音乐榜单: {chart_id}")

        # 榜单详情 API（使用歌单接口，榜单本质上是特殊歌单）
        playlist_url = f"{self.api_url}/api/v6/playlist/detail"
        params = {"id": chart_id}

        tasks = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(playlist_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200:
                    playlist_data = data.get("playlist", {})
                    tracks = playlist_data.get("tracks", [])

                    # 榜单名称
                    chart_name = playlist_data.get("name", "")
                    self.logger.info(f"榜单 '{chart_name}' 包含 {len(tracks)} 首歌曲")

                    for idx, track in enumerate(tracks, start=1):
                        # 获取艺术家名称
                        artist_name = None
                        if track.get("ar"):
                            artist_name = ", ".join(
                                [artist.get("name", "") for artist in track["ar"]]
                            )

                        # 获取专辑名称
                        album_name = None
                        if track.get("al"):
                            album_name = track["al"].get("name")

                        # 创建下载任务
                        task = DownloadTask(
                            task_id=f"netease_{track['id']}",
                            url=str(track["id"]),
                            source=self.source,
                            quality=DownloadQuality.STANDARD,
                            artist=artist_name,
                            album=album_name,
                            title=track.get("name"),
                            metadata={
                                "song_id": track["id"],
                                "artist_ids": [a.get("id") for a in track.get("ar", [])],
                                "album_id": (
                                    track.get("al", {}).get("id") if track.get("al") else None
                                ),
                                "duration": track.get("dt") / 1000 if track.get("dt") else None,
                                "album_pic": (
                                    track.get("al", {}).get("picUrl") if track.get("al") else None
                                ),
                                "chart_id": chart_id,
                                "chart_name": chart_name,
                                "rank": idx,  # 排名
                            },
                        )
                        tasks.append(task)

                    self.logger.info(f"榜单抓取完成，获取 {len(tasks)} 首歌曲")

        except Exception as e:
            self.logger.error(f"抓取榜单失败: {e}")

        return tasks

    async def test(self) -> tuple[bool, str]:
        """
        测试下载器连接

        Returns:
            (是否可用, 错误信息)
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self.base_url)
                if response.status_code == 200:
                    # 测试搜索功能
                    result = await self.search("test", limit=1)
                    if result:
                        return True, "连接成功，搜索功能正常"
                    else:
                        return False, "搜索功能异常"
                else:
                    return False, f"连接失败: HTTP {response.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
