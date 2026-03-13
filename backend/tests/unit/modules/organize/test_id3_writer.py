"""ID3 标签写入测试"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from app.modules.organize.id3_writer import ID3Writer


class TestID3Writer:
    """测试 ID3Writer"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        writer1 = ID3Writer()
        writer2 = ID3Writer()

        assert writer1 is writer2

    def test_prepare_metadata(self):
        """测试元数据准备"""
        writer = ID3Writer()

        metadata = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "albumartist": "Test Album Artist",
            "tracknumber": "01",
            "tracktotal": "10",
            "date": "2024",
            "genre": "Rock",
            "discnumber": "1",
            "disctotal": "1",
        }

        result = writer._prepare_metadata(metadata)

        assert result["TIT2"] == "Test Song"
        assert result["TPE1"] == "Test Artist"
        assert result["TALB"] == "Test Album"
        assert result["TPE2"] == "Test Album Artist"
        assert result["TRCK"] == "01/10"
        assert result["TDRC"] == "2024"
        assert result["TCON"] == "Rock"
        assert result["TPOS"] == "1/1"

    @pytest.mark.asyncio
    async def test_write_tags_to_flac(self):
        """测试写入 FLAC 标签"""
        writer = ID3Writer()

        # Mock mutagen and os.path.exists (patch in the module where it's used)
        mock_audio = MagicMock()
        mock_audio.tags = {}

        with (
            patch("app.modules.organize.id3_writer.FLAC", return_value=mock_audio),
            patch("app.modules.organize.id3_writer.os.path.exists", return_value=True),
        ):
            metadata = {"title": "Test Song", "artist": "Test Artist", "album": "Test Album"}

            result = await writer.write_tags("/test/test.flac", metadata)

            assert result is True
            assert mock_audio.tags["TIT2"] == "Test Song"
            assert mock_audio.tags["TPE1"] == "Test Artist"
            assert mock_audio.tags["TALB"] == "Test Album"
            mock_audio.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_tags_to_mp3(self):
        """测试写入 MP3 标签"""
        writer = ID3Writer()

        # Mock mutagen and os.path.exists
        mock_audio = MagicMock()
        mock_audio.tags = MagicMock()

        with (
            patch("app.modules.organize.id3_writer.MP3", return_value=mock_audio),
            patch("app.modules.organize.id3_writer.os.path.exists", return_value=True),
        ):
            metadata = {"title": "Test Song", "artist": "Test Artist"}

            result = await writer.write_tags("/test/test.mp3", metadata)

            assert result is True
            mock_audio.tags.__setitem__.assert_any_call("TIT2", "Test Song")
            mock_audio.tags.__setitem__.assert_any_call("TPE1", "Test Artist")
            mock_audio.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_tags_unsupported_format(self):
        """测试不支持的格式"""
        writer = ID3Writer()

        with patch("app.modules.organize.id3_writer.os.path.exists", return_value=True):
            metadata = {"title": "Test"}
            result = await writer.write_tags("/test/test.wav", metadata)

            assert result is False

    @pytest.mark.asyncio
    async def test_write_tags_file_not_found(self):
        """测试文件不存在"""
        writer = ID3Writer()

        with patch("app.modules.organize.id3_writer.os.path.exists", return_value=False):
            result = await writer.write_tags("/test/not_exist.flac", {"title": "Test"})

            assert result is False
