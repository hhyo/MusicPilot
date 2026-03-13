"""
元数据管理模块
提供音乐元数据的查询、解析、处理功能
"""

from pathlib import Path

import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

from app.core.context import MusicInfo
from app.core.log import logger


class MetadataParser:
    """
    元数据解析器
    解析音频文件的元数据
    """

    # 支持的音频格式
    SUPPORTED_FORMATS = [".mp3", ".flac", ".m4a", ".ogg", ".wav", ".wma", ".aac"]

    def __init__(self):
        self.logger = logger

    @staticmethod
    def is_supported_format(file_path: Path) -> bool:
        """
        检查文件是否为支持的音频格式

        Args:
            file_path: 文件路径

        Returns:
            是否支持
        """
        return file_path.suffix.lower() in MetadataParser.SUPPORTED_FORMATS

    def parse_file(self, file_path: Path) -> MusicInfo | None:
        """
        解析音频文件元数据

        Args:
            file_path: 文件路径

        Returns:
            音乐信息对象
        """
        if not file_path.exists():
            self.logger.warning(f"文件不存在: {file_path}")
            return None

        if not self.is_supported_format(file_path):
            self.logger.warning(f"不支持的文件格式: {file_path}")
            return None

        try:
            # 根据文件类型选择解析器
            if file_path.suffix.lower() == ".mp3":
                return self._parse_mp3(file_path)
            elif file_path.suffix.lower() == ".flac":
                return self._parse_flac(file_path)
            elif file_path.suffix.lower() in [".m4a", ".aac"]:
                return self._parse_m4a(file_path)
            elif file_path.suffix.lower() == ".ogg":
                return self._parse_ogg(file_path)
            elif file_path.suffix.lower() == ".wav":
                return self._parse_wav(file_path)
            else:
                # 使用通用解析器
                return self._parse_generic(file_path)

        except Exception as e:
            self.logger.error(f"解析文件元数据失败: {file_path}, 错误: {e}")
            return None

    def _parse_mp3(self, file_path: Path) -> MusicInfo:
        """解析 MP3 文件"""
        audio = MP3(file_path)
        music_info = MusicInfo()

        music_info.path = str(file_path)
        music_info.file_format = "mp3"
        music_info.file_size = file_path.stat().st_size
        music_info.duration = int(audio.info.length)

        if audio.info.bitrate:
            music_info.bitrate = audio.info.bitrate

        # 解析 ID3 标签
        if audio.tags:
            music_info.artist = self._get_tag_value(audio.tags, "TPE1")
            music_info.album = self._get_tag_value(audio.tags, "TALB")
            music_info.title = self._get_tag_value(audio.tags, "TIT2")

            # 曲目号
            track_number = self._get_tag_value(audio.tags, "TRCK")
            if track_number:
                if "/" in track_number:
                    track_part, _ = track_number.split("/", 1)
                    music_info.track_number = int(track_part) if track_part.isdigit() else None
                else:
                    music_info.track_number = int(track_number) if track_number.isdigit() else None

            # 年份
            year = self._get_tag_value(audio.tags, "TDRC") or self._get_tag_value(
                audio.tags, "TYER"
            )
            if year:
                music_info.year = int(year[:4]) if year[:4].isdigit() else None

            # 流派
            genre = self._get_tag_value(audio.tags, "TCON")
            if genre:
                music_info.genres = [genre]

            # MusicBrainz ID
            music_info.musicbrainz_track_id = self._get_tag_value(
                audio.tags, "UFID:http://musicbrainz.org"
            )
            music_info.musicbrainz_artist_id = self._get_tag_value(
                audio.tags, "TXXX:MusicBrainz Artist Id"
            )
            music_info.musicbrainz_album_id = self._get_tag_value(
                audio.tags, "TXXX:MusicBrainz Album Id"
            )

            # 封面（暂不提取）

        return music_info

    def _parse_flac(self, file_path: Path) -> MusicInfo:
        """解析 FLAC 文件"""
        audio = FLAC(file_path)
        music_info = MusicInfo()

        music_info.path = str(file_path)
        music_info.file_format = "flac"
        music_info.file_size = file_path.stat().st_size
        music_info.duration = int(audio.info.length)

        if audio.info.bitrate:
            music_info.bitrate = audio.info.bitrate

        # 解析 Vorbis 注释
        music_info.artist = audio.get("artist", [None])[0]
        music_info.album = audio.get("album", [None])[0]
        music_info.title = audio.get("title", [None])[0]

        # 曲目号
        track_number = audio.get("tracknumber", [None])[0]
        if track_number:
            if "/" in track_number:
                track_part, _ = track_number.split("/", 1)
                music_info.track_number = int(track_part) if track_part.isdigit() else None
            else:
                music_info.track_number = int(track_number) if track_number.isdigit() else None

        # 年份
        year = audio.get("date", [None])[0]
        if year:
            music_info.year = int(year[:4]) if year[:4].isdigit() else None

        # 流派
        genre = audio.get("genre", [None])[0]
        if genre:
            music_info.genres = [genre]

        # MusicBrainz ID
        music_info.musicbrainz_track_id = audio.get("MUSICBRAINZ_TRACKID", [None])[0]
        music_info.musicbrainz_artist_id = audio.get("MUSICBRAINZ_ARTISTID", [None])[0]
        music_info.musicbrainz_album_id = audio.get("MUSICBRAINZ_ALBUMID", [None])[0]

        return music_info

    def _parse_m4a(self, file_path: Path) -> MusicInfo:
        """解析 M4A 文件"""
        audio = MP4(file_path)
        music_info = MusicInfo()

        music_info.path = str(file_path)
        music_info.file_format = "m4a"
        music_info.file_size = file_path.stat().st_size
        music_info.duration = int(audio.info.length)

        if audio.info.bitrate:
            music_info.bitrate = audio.info.bitrate

        # 解析 MP4 标签
        music_info.artist = audio.get("\xa9ART", [None])[0]
        music_info.album = audio.get("\xa9alb", [None])[0]
        music_info.title = audio.get("\xa9nam", [None])[0]

        # 曲目号
        track_number = audio.get("trkn", [None])[0]
        if track_number:
            music_info.track_number = track_number[0] if track_number else None

        # 年份
        year = audio.get("\xa9day", [None])[0]
        if year:
            music_info.year = int(year[:4]) if year[:4].isdigit() else None

        # 流派
        genre = audio.get("\xa9gen", [None])[0]
        if genre:
            music_info.genres = [genre]

        # MusicBrainz ID（需要自定义标签）
        music_info.musicbrainz_track_id = audio.get(
            "----:com.apple.iTunes:MusicBrainz Track Id", [None]
        )[0]
        music_info.musicbrainz_artist_id = audio.get(
            "----:com.apple.iTunes:MusicBrainz Artist Id", [None]
        )[0]
        music_info.musicbrainz_album_id = audio.get(
            "----:com.apple.iTunes:MusicBrainz Album Id", [None]
        )[0]

        return music_info

    def _parse_ogg(self, file_path: Path) -> MusicInfo:
        """解析 OGG 文件"""
        audio = OggVorbis(file_path)
        music_info = MusicInfo()

        music_info.path = str(file_path)
        music_info.file_format = "ogg"
        music_info.file_size = file_path.stat().st_size
        music_info.duration = int(audio.info.length)

        if audio.info.bitrate:
            music_info.bitrate = audio.info.bitrate

        # 解析 Vorbis 注释
        music_info.artist = audio.get("artist", [None])[0]
        music_info.album = audio.get("album", [None])[0]
        music_info.title = audio.get("title", [None])[0]

        # 曲目号
        track_number = audio.get("tracknumber", [None])[0]
        if track_number:
            music_info.track_number = int(track_number) if track_number.isdigit() else None

        # 年份
        year = audio.get("date", [None])[0]
        if year:
            music_info.year = int(year[:4]) if year[:4].isdigit() else None

        # 流派
        genre = audio.get("genre", [None])[0]
        if genre:
            music_info.genres = [genre]

        return music_info

    def _parse_wav(self, file_path: Path) -> MusicInfo:
        """解析 WAV 文件"""
        audio = WAVE(file_path)
        music_info = MusicInfo()

        music_info.path = str(file_path)
        music_info.file_format = "wav"
        music_info.file_size = file_path.stat().st_size
        music_info.duration = int(audio.info.length)

        # WAV 文件通常没有元数据标签
        return music_info

    def _parse_generic(self, file_path: Path) -> MusicInfo:
        """使用通用解析器"""
        audio = mutagen.File(file_path)
        music_info = MusicInfo()

        music_info.path = str(file_path)
        music_info.file_format = file_path.suffix.lstrip(".")
        music_info.file_size = file_path.stat().st_size

        if audio:
            music_info.duration = int(audio.info.length)
            if audio.info.bitrate:
                music_info.bitrate = audio.info.bitrate

        return music_info

    @staticmethod
    def _get_tag_value(tags, tag_name: str) -> str | None:
        """
        获取标签值

        Args:
            tags: 标签对象
            tag_name: 标签名

        Returns:
            标签值
        """
        tag = tags.get(tag_name)
        if tag:
            return str(tag[0]) if tag else None
        return None


class FilenameParser:
    """
    文件名解析器
    从文件名提取音乐信息
    """

    # 常见的文件名模式
    PATTERNS = [
        # Artist - Album - Track - Title.mp3
        r"^(?P<artist>.+?)\s*-\s*(?P<album>.+?)\s*-\s*(?P<track>\d+)?\s*-\s*(?P<title>.+)$",
        # Artist - Title.mp3
        r"^(?P<artist>.+?)\s*-\s*(?P<title>.+)$",
        # Album - Track - Title.mp3
        r"^(?P<album>.+?)\s*-\s*(?P<track>\d+)?\s*-\s*(?P<title>.+)$",
        # Track - Title.mp3
        r"^(?P<track>\d+)\s*-\s*(?P<title>.+)$",
    ]

    def __init__(self):
        self.logger = logger

    def parse(self, file_path: Path) -> MusicInfo:
        """
        解析文件名

        Args:
            file_path: 文件路径

        Returns:
            音乐信息对象
        """
        music_info = MusicInfo()
        filename = file_path.stem  # 不含扩展名的文件名

        # 移除常见的括号内容
        filename = self._clean_filename(filename)

        # 尝试匹配模式
        import re

        for pattern in self.PATTERNS:
            match = re.match(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                if "artist" in groups and groups["artist"]:
                    music_info.artist = groups["artist"]
                if "album" in groups and groups["album"]:
                    music_info.album = groups["album"]
                if "title" in groups and groups["title"]:
                    music_info.title = groups["title"]
                if "track" in groups and groups["track"]:
                    music_info.track_number = int(groups["track"])
                break

        # 如果没有提取到标题，使用文件名
        if not music_info.title:
            music_info.title = filename

        return music_info

    def _clean_filename(self, filename: str) -> str:
        """
        清理文件名

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        import re

        # 移除方括号内容 [xxx]
        filename = re.sub(r"\[.*?\]", "", filename)
        # 移除圆括号内容 (xxx)
        filename = re.sub(r"\(.*?\)", "", filename)
        # 移除花括号内容 {xxx}
        filename = re.sub(r"\{.*?\}", "", filename)
        # 替换多个空格为单个空格
        filename = re.sub(r"\s+", " ", filename)
        # 去除首尾空格
        filename = filename.strip()

        return filename


# 全局实例
metadata_parser = MetadataParser()
filename_parser = FilenameParser()
