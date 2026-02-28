"""
MetadataParser 和 FilenameParser 单元测试
测试元数据解析功能
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.meta import FilenameParser, MetadataParser, metadata_parser, filename_parser


class TestMetadataParser:
    """MetadataParser 测试类"""

    @pytest.fixture
    def parser(self):
        """创建 MetadataParser 实例"""
        return MetadataParser()

    # ==================== is_supported_format 测试 ====================

    def test_is_supported_format_mp3(self, parser):
        """测试支持的 MP3 格式"""
        assert parser.is_supported_format(Path("test.mp3")) is True
        assert parser.is_supported_format(Path("test.MP3")) is True

    def test_is_supported_format_flac(self, parser):
        """测试支持的 FLAC 格式"""
        assert parser.is_supported_format(Path("test.flac")) is True

    def test_is_supported_format_m4a(self, parser):
        """测试支持的 M4A 格式"""
        assert parser.is_supported_format(Path("test.m4a")) is True
        assert parser.is_supported_format(Path("test.aac")) is True

    def test_is_supported_format_ogg(self, parser):
        """测试支持的 OGG 格式"""
        assert parser.is_supported_format(Path("test.ogg")) is True

    def test_is_supported_format_wav(self, parser):
        """测试支持的 WAV 格式"""
        assert parser.is_supported_format(Path("test.wav")) is True

    def test_is_supported_format_unsupported(self, parser):
        """测试不支持的格式"""
        assert parser.is_supported_format(Path("test.txt")) is False
        assert parser.is_supported_format(Path("test.pdf")) is False
        assert parser.is_supported_format(Path("test.exe")) is False

    # ==================== parse_file 测试 ====================

    def test_parse_file_nonexistent(self, parser):
        """测试解析不存在的文件"""
        result = parser.parse_file(Path("/nonexistent/file.mp3"))

        assert result is None

    def test_parse_file_unsupported_format(self, parser):
        """测试解析不支持的格式"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not audio")
            file_path = Path(f.name)

        result = parser.parse_file(file_path)

        assert result is None

    def test_parse_file_empty_mp3(self, parser):
        """测试解析空 MP3 文件"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"")
            file_path = Path(f.name)

        # 空文件会导致解析失败，应返回 None
        result = parser.parse_file(file_path)
        assert result is None


class TestFilenameParser:
    """FilenameParser 测试类"""

    @pytest.fixture
    def parser(self):
        """创建 FilenameParser 实例"""
        return FilenameParser()

    # ==================== parse 测试 ====================

    def test_parse_artist_title(self, parser):
        """测试解析 "Artist - Title" 格式"""
        file_path = Path("/music/Artist Name - Song Title.mp3")

        result = parser.parse(file_path)

        assert result.artist == "Artist Name"
        assert result.title == "Song Title"

    def test_parse_simple_filename(self, parser):
        """测试解析简单文件名"""
        file_path = Path("/music/Just A Song.mp3")

        result = parser.parse(file_path)

        # 简单文件名应使用原文件名作为标题
        assert result.title is not None

    def test_parse_with_track_number(self, parser):
        """测试解析带曲目号的文件名"""
        file_path = Path("/music/01 - Song Title.mp3")

        result = parser.parse(file_path)

        assert result.title == "Song Title"
        # track_number depends on pattern matching

    def test_parse_with_album(self, parser):
        """测试解析带专辑名的文件名"""
        file_path = Path("/music/Artist - Album - Song.mp3")

        result = parser.parse(file_path)

        # 可能匹配多种模式
        assert result.title is not None

    def test_parse_with_brackets(self, parser):
        """测试解析带括号的文件名"""
        file_path = Path("/music/Artist - Song [2024].mp3")

        result = parser.parse(file_path)

        # 括号内容应被清理
        assert result.artist == "Artist"
        assert "Song" in result.title

    def test_parse_with_parentheses(self, parser):
        """测试解析带圆括号的文件名"""
        file_path = Path("/music/Artist - Song (Remix).mp3")

        result = parser.parse(file_path)

        assert result.artist == "Artist"
        assert "Song" in result.title

    # ==================== _clean_filename 测试 ====================

    def test_clean_filename_removes_brackets(self, parser):
        """测试清理方括号"""
        result = parser._clean_filename("Song [2024] [Remaster]")

        assert "[2024]" not in result
        assert "[Remaster]" not in result

    def test_clean_filename_removes_parentheses(self, parser):
        """测试清理圆括号"""
        result = parser._clean_filename("Song (Remix) (Live)")

        assert "(Remix)" not in result
        assert "(Live)" not in result

    def test_clean_filename_removes_braces(self, parser):
        """测试清理花括号"""
        result = parser._clean_filename("Song {Special Edition}")

        assert "{Special Edition}" not in result

    def test_clean_filename_collapses_spaces(self, parser):
        """测试合并多个空格"""
        result = parser._clean_filename("Song   Title    Here")

        assert "   " not in result
        assert "  " not in result

    def test_clean_filename_strips_whitespace(self, parser):
        """测试去除首尾空格"""
        result = parser._clean_filename("  Song Title  ")

        assert result == "Song Title"


class TestGlobalInstances:
    """全局实例测试"""

    def test_metadata_parser_instance(self):
        """测试全局元数据解析器实例"""
        assert metadata_parser is not None
        assert isinstance(metadata_parser, MetadataParser)

    def test_filename_parser_instance(self):
        """测试全局文件名解析器实例"""
        assert filename_parser is not None
        assert isinstance(filename_parser, FilenameParser)
