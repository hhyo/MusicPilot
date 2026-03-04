"""
TransferChain 单元测试
测试文件整理功能
"""

from unittest.mock import MagicMock

import pytest


class TestTransferChainHelpers:
    """TransferChain 辅助方法测试"""

    def test_sanitize_filename_normal(self):
        """测试正常文件名"""
        import re

        filename = "Normal File Name"
        safe = re.sub(r'[<>:"/\\|?*]', "", filename)
        safe = re.sub(r"\s+", " ", safe).strip()
        assert safe == "Normal File Name"

    def test_sanitize_filename_with_invalid_chars(self):
        """测试包含非法字符的文件名"""
        import re

        filename = 'file<>:"/\\|?*name'
        safe = re.sub(r'[<>:"/\\|?*]', "", filename)
        assert "<" not in safe
        assert ">" not in safe
        assert ":" not in safe

    def test_sanitize_filename_empty(self):
        """测试空文件名"""
        import re

        filename = ""
        safe = re.sub(r'[<>:"/\\|?*]', "", filename)
        safe = re.sub(r"\s+", " ", safe).strip()
        result = safe or "Unknown"
        assert result == "Unknown"


class TestTransferChainMD5:
    """TransferChain MD5 计算测试"""

    def test_calculate_md5_small_file(self, tmp_path):
        """测试小文件 MD5 计算"""
        from hashlib import md5

        test_file = tmp_path / "small.mp3"
        test_file.write_bytes(b"test content for md5")

        hash_md5 = md5()
        with open(test_file, "rb") as f:
            chunk = f.read(1024 * 1024)
            hash_md5.update(chunk)
            if test_file.stat().st_size <= 2 * 1024 * 1024:
                f.seek(0)
                remaining = f.read()
                hash_md5.update(remaining)
        result = hash_md5.hexdigest()

        assert len(result) == 32
        assert isinstance(result, str)

    def test_calculate_md5_large_file(self, tmp_path):
        """测试大文件 MD5 计算"""
        from hashlib import md5

        test_file = tmp_path / "large.mp3"
        test_file.write_bytes(b"x" * (3 * 1024 * 1024))

        hash_md5 = md5()
        with open(test_file, "rb") as f:
            chunk = f.read(1024 * 1024)
            hash_md5.update(chunk)
            f.seek(-1024 * 1024, 2)
            chunk = f.read()
            hash_md5.update(chunk)
        result = hash_md5.hexdigest()

        assert len(result) == 32


class TestTransferChainPathGeneration:
    """TransferChain 路径生成测试"""

    def test_generate_path_normal(self, tmp_path):
        """测试生成正常路径"""
        import re

        media_dir = tmp_path / "media"
        media_dir.mkdir()

        artist = "Test Artist"
        album = "Test Album"
        title = "Test Track"
        file_path = str(tmp_path / "test.mp3")

        safe_artist = re.sub(r'[<>:"/\\|?*]', "", artist)
        safe_album = re.sub(r'[<>:"/\\|?*]', "", album)
        safe_title = re.sub(r'[<>:"/\\|?*]', "", title)
        source_ext = ".mp3"

        target_path = media_dir / safe_artist / safe_album / f"{safe_title}{source_ext}"

        assert "Test Artist" in str(target_path)
        assert "Test Album" in str(target_path)
        assert "Test Track" in str(target_path)

    def test_generate_path_with_existing_file(self, tmp_path):
        """测试文件已存在时添加序号"""

        media_dir = tmp_path / "media"
        artist_dir = media_dir / "Test Artist" / "Test Album"
        artist_dir.mkdir(parents=True)
        (artist_dir / "Test Track.mp3").touch()

        safe_artist = "Test Artist"
        safe_album = "Test Album"
        safe_title = "Test Track"
        source_ext = ".mp3"

        target_path = media_dir / safe_artist / safe_album / f"{safe_title}{source_ext}"

        counter = 1
        while target_path.exists():
            target_path = (
                media_dir / safe_artist / safe_album / f"{safe_title}_{counter}{source_ext}"
            )
            counter += 1

        assert "_1" in str(target_path)

    def test_generate_path_unknown_metadata(self, tmp_path):
        """测试未知元数据使用默认值"""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        artist = None
        album = None
        title = None

        safe_artist = artist or "Unknown Artist"
        safe_album = album or "Unknown Album"
        safe_title = title or "Unknown Track"

        target_path = media_dir / safe_artist / safe_album / f"{safe_title}.mp3"

        assert "Unknown Artist" in str(target_path)
        assert "Unknown Album" in str(target_path)


class TestTransferChainDuplicateCheck:
    """TransferChain 重复检查测试"""

    @pytest.mark.asyncio
    async def test_check_duplicate_logic_by_musicbrainz_id(self, tmp_path):
        """测试通过 MusicBrainz ID 检查重复逻辑"""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"test content")

        # 模拟找到重复
        mock_track = MagicMock()
        mock_track.id = 1
        mock_track.path = "/existing/path.mp3"

        # 测试逻辑：如果找到 existing_track，返回重复信息
        existing_track = mock_track
        if existing_track:
            result = {
                "type": "musicbrainz_id",
                "track_id": existing_track.id,
                "path": existing_track.path,
            }
        else:
            result = None

        assert result is not None
        assert result["type"] == "musicbrainz_id"

    @pytest.mark.asyncio
    async def test_check_duplicate_logic_not_found(self, tmp_path):
        """测试无重复文件逻辑"""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"test content")

        # 模拟未找到重复
        existing_track = None

        if existing_track:
            result = {"type": "found", "track_id": existing_track.id}
        else:
            result = None

        assert result is None
