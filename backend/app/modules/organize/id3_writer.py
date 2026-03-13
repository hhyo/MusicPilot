"""ID3 标签写入器"""

import os
from pathlib import Path

from mutagen.flac import FLAC
from mutagen.mp3 import MP3


class ID3Writer:
    """ID3 标签写入器 - 支持 FLAC 和 MP3"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _prepare_metadata(self, metadata: dict) -> dict[str, str]:
        """准备元数据映射"""
        mapping = {}

        # 标准 ID3 标签映射
        if "title" in metadata:
            mapping["TIT2"] = metadata["title"]
        if "artist" in metadata:
            mapping["TPE1"] = metadata["artist"]
        if "album" in metadata:
            mapping["TALB"] = metadata["album"]
        if "albumartist" in metadata:
            mapping["TPE2"] = metadata["albumartist"]
        if "tracknumber" in metadata:
            track = metadata["tracknumber"]
            tracktotal = metadata.get("tracktotal", "")
            mapping["TRCK"] = f"{track}/{tracktotal}" if tracktotal else track
        if "date" in metadata or "year" in metadata:
            mapping["TDRC"] = metadata.get("date") or metadata.get("year", "")
        if "genre" in metadata:
            mapping["TCON"] = metadata["genre"]
        if "discnumber" in metadata:
            disc = metadata["discnumber"]
            disctotal = metadata.get("disctotal", "")
            mapping["TPOS"] = f"{disc}/{disctotal}" if disctotal else disc

        return mapping

    async def write_tags(self, file_path: str, metadata: dict) -> bool:
        """写入标签到音频文件"""
        try:
            if not os.path.exists(file_path):
                return False

            ext = Path(file_path).suffix.lower()

            if ext == ".flac":
                return await self._write_flac_tags(file_path, metadata)
            elif ext == ".mp3":
                return await self._write_mp3_tags(file_path, metadata)
            else:
                return False

        except Exception as e:
            print(f"写入标签失败: {e}")
            return False

    async def _write_flac_tags(self, file_path: str, metadata: dict) -> bool:
        """写入 FLAC 标签"""
        audio = FLAC(file_path)

        # 准备元数据
        tags = self._prepare_metadata(metadata)

        # 写入标签
        for key, value in tags.items():
            audio.tags[key] = value

        audio.save()
        return True

    async def _write_mp3_tags(self, file_path: str, metadata: dict) -> bool:
        """写入 MP3 标签"""
        audio = MP3(file_path)

        # 添加 ID3 标签（如果不存在）
        if audio.tags is None:
            audio.add_tags()

        # 准备元数据
        tags = self._prepare_metadata(metadata)

        # 写入标签
        for key, value in tags.items():
            audio.tags[key] = value

        audio.save()
        return True
