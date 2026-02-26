"""
网易云音乐下载器
"""
import asyncio
import httpx
from typing import Optional, Tuple
from urllib.parse import quote

from .base import (
    DownloadStatus,
    DownloadQuality,
    DownloadSource,
    DownloadTask,
    DownloaderBase,
)


class NeteaseDownloader(DownloaderBase):
    """
    网易云音乐下载器

    注意: 网易云音乐的下载需要加密和签名处理
    这里提供一个基础实现框架
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

    def init_setting(self) -> Optional[Tuple[str, bool]]:
        """
        初始化下载器设置

        Returns:
            (字段定义, 是否必需)
        """
        # 网易云音乐暂时不需要配置
        return None

    async def search(
        self,
        keyword: str,
        limit: int = 20,
        quality: Optional[DownloadQuality] = None
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
        # 网易云搜索 API
        search_url = f"{self.api_url}/api/search/get/web"
        params = {
            "s": keyword,
            "type": "1",  # 1 = 单曲
            "offset": "0",
            "limit": str(limit),
        }

        tasks = []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200:
                    songs = data.get("result", {}).get("songs", [])
                    for song in songs:
                        task = DownloadTask(
                            task_id=f"netease_{song['id']}",
                            url=str(song["id"]),
                            source=self.source,
                            quality=quality or DownloadQuality.STANDARD,
                            artist=song.get("artists", [{}])[0].get("name") if song.get("artists") else None,
                            album=song.get("album", {}).get("name") if song.get("album") else None,
                            title=song.get("name"),
                            metadata={
                                "song_id": song["id"],
                                "artist_id": song.get("artists", [{}])[0].get("id") if song.get("artists") else None,
                                "album_id": song.get("album", {}).get("id") if song.get("album") else None,
                                "duration": song.get("duration") / 1000 if song.get("duration") else None,
                            },
                        )
                        tasks.append(task)

        except Exception as e:
            print(f"搜索失败: {e}")

        return tasks

    async def get_url(
        self,
        url: str,
        quality: DownloadQuality = DownloadQuality.STANDARD
    ) -> str:
        """
        获取实际下载 URL

        Args:
            url: 歌曲 ID
            quality: 目标质量

        Returns:
            实际下载 URL

        注意: 网易云音乐的获取下载 URL 接口需要加密和签名
        这里仅提供框架，实际实现需要参考网易云音乐加密算法
        """
        # 获取下载 URL 的 API
        download_url = f"{self.api_url}/api/song/enhance/player/url/v1"

        # 映射质量到网易云音乐格式
        quality_map = {
            DownloadQuality.LOSSLESS: "999000",
            DownloadQuality.HIGH: "320000",
            DownloadQuality.STANDARD: "128000",
        }
        br = quality_map.get(quality, "128000")

        params = {
            "ids": f"[{url}]",
            "br": br,
            "level": "standard",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 200 and data.get("data"):
                    return data["data"][0].get("url", "")
                else:
                    raise ValueError(f"获取下载 URL 失败: {data.get('message')}")

        except Exception as e:
            print(f"获取下载 URL 失败: {e}")
            raise

    async def download(
        self,
        task: DownloadTask,
        progress_callback: Optional[callable] = None
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
                raise ValueError("无法获取下载 URL")

            # 下载文件
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    # 获取文件大小
                    total_bytes = int(response.headers.get("content-length", 0))
                    task.total_bytes = total_bytes

                    # 确定目标路径
                    from pathlib import Path
                    if task.target_path:
                        target_dir = Path(task.target_path)
                    else:
                        target_dir = Path("/tmp/downloads")
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # 确定文件扩展名
                    ext = ".mp3" if task.quality != DownloadQuality.LOSSLESS else ".flac"
                    file_path = target_dir / f"{task.title or task.task_id}{ext}"

                    # 下载文件
                    downloaded_bytes = 0
                    with open(file_path, "wb") as f:
                        async for chunk in response.aiter_bytes(8192):
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            task.downloaded_bytes = downloaded_bytes
                            task.progress = (downloaded_bytes / total_bytes) if total_bytes > 0 else 0

                            if progress_callback:
                                progress_callback(task)

            # 下载完成
            task.status = DownloadStatus.COMPLETED
            task.file_path = str(file_path)
            task.progress = 1.0

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)
            print(f"下载失败: {e}")

        return task

    async def test(self) -> Tuple[bool, str]:
        """
        测试下载器连接

        Returns:
            (是否可用, 错误信息)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, timeout=5)
                if response.status_code == 200:
                    return True, "连接成功"
                else:
                    return False, f"连接失败: HTTP {response.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"