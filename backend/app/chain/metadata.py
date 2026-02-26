"""
元数据处理链
处理音乐元数据的识别、补全
"""
from typing import Optional, Dict, Any
from pathlib import Path

from app.chain import ChainBase
from app.core.context import MusicInfo
from app.core.meta import MetadataParser, FilenameParser
from app.core.log import logger


class MetadataChain(ChainBase):
    """
    元数据处理链
    负责提取本地元数据、解析文件名、查询在线数据库、补全元数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata_parser = MetadataParser()
        self.filename_parser = FilenameParser()

    async def recognize(self, file_path: str) -> Optional[MusicInfo]:
        """
        识别音乐文件的元数据

        Args:
            file_path: 文件路径

        Returns:
            音乐信息对象
        """
        path = Path(file_path)

        # 1. 提取本地元数据
        local_metadata = self.metadata_parser.parse_file(path)

        # 2. 解析文件名
        filename_metadata = self.filename_parser.parse(path)

        # 3. 合并元数据（文件名优先级较低）
        if local_metadata:
            merged = MusicInfo(
                artist=local_metadata.artist or filename_metadata.artist,
                album=local_metadata.album or filename_metadata.album,
                title=local_metadata.title or filename_metadata.title,
                duration=local_metadata.duration or filename_metadata.duration,
                track_number=local_metadata.track_number or filename_metadata.track_number,
                disc_number=local_metadata.disc_number,
                path=str(path),
                file_format=local_metadata.file_format,
                file_size=local_metadata.file_size,
                bitrate=local_metadata.bitrate,
                sample_rate=local_metadata.sample_rate,
                channels=local_metadata.channels,
                genres=local_metadata.genres or filename_metadata.genres,
                musicbrainz_artist_id=local_metadata.musicbrainz_artist_id,
                musicbrainz_album_id=local_metadata.musicbrainz_album_id,
                musicbrainz_track_id=local_metadata.musicbrainz_track_id,
            )
        else:
            merged = filename_metadata
            merged.path = str(path)

        self.logger.info(f"识别元数据: {path.name}")

        return merged

    async def complete(self, metadata: MusicInfo) -> MusicInfo:
        """
        补全元数据

        Args:
            metadata: 音乐信息对象

        Returns:
            补全后的音乐信息对象
        """
        # 检查缓存
        cache_key = f"metadata:{metadata.musicbrainz_track_id or metadata.path}"
        cached = self.get_cache(cache_key)
        if cached:
            self.logger.debug(f"使用缓存的元数据: {metadata.title}")
            return cached

        # 调用 MusicBrainz 查询
        if metadata.musicbrainz_track_id:
            # 已有 MusicBrainz ID，直接查询
            track_info = await self.run_module("musicbrainz", "get_track_info", metadata.musicbrainz_track_id)
        else:
            # 通过标题查询
            query = f"{metadata.artist} {metadata.title}" if metadata.artist else metadata.title
            results = await self.run_module("musicbrainz", "search_track", query)
            if results:
                # 使用第一个结果
                track_id = results[0].get("id")
                track_info = await self.run_module("musicbrainz", "get_track_info", track_id)
            else:
                track_info = None

        # 合并查询结果
        if track_info:
            if not metadata.artist and track_info.get("artist"):
                metadata.artist = track_info["artist"]
            if not metadata.album and track_info.get("album"):
                metadata.album = track_info["album"]
            if not metadata.title and track_info.get("title"):
                metadata.title = track_info["title"]
            if not metadata.musicbrainz_artist_id and track_info.get("artist_id"):
                metadata.musicbrainz_artist_id = track_info["artist_id"]
            if not metadata.musicbrainz_album_id and track_info.get("album_id"):
                metadata.musicbrainz_album_id = track_info["album_id"]
            if not metadata.musicbrainz_track_id and track_info.get("id"):
                metadata.musicbrainz_track_id = track_info["id"]

            # 缓存结果
            self.set_cache(cache_key, metadata, ttl=86400)  # 24小时

        self.logger.info(f"补全元数据: {metadata.title}")

        return metadata