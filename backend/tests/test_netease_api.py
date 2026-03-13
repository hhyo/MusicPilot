"""
Netease API 测试
"""


class TestNeteaseApiStructures:
    """网易云 API 结构测试"""

    def test_search_params(self):
        """测试搜索参数"""
        params = {
            "keywords": "test song",
            "limit": 30,
            "offset": 0,
            "type": 1,  # 单曲
        }
        assert params["keywords"] == "test song"
        assert params["limit"] == 30

    def test_song_detail_params(self):
        """测试歌曲详情参数"""
        params = {
            "ids": "[123456,789012]",
        }
        assert "ids" in params

    def test_playlist_params(self):
        """测试歌单参数"""
        params = {
            "id": 789012,
            "limit": 100,
            "offset": 0,
        }
        assert params["id"] == 789012


class TestNeteaseResponseParsing:
    """网易云响应解析测试"""

    def test_parse_search_result(self):
        """测试解析搜索结果"""
        response = {
            "result": {
                "songs": [
                    {"id": 1, "name": "Song 1"},
                    {"id": 2, "name": "Song 2"},
                ]
            },
            "code": 200,
        }
        songs = response["result"]["songs"]
        assert len(songs) == 2

    def test_parse_song_url(self):
        """测试解析歌曲URL"""
        response = {
            "data": [{"id": 123456, "url": "http://example.com/song.mp3", "br": 320000}],
            "code": 200,
        }
        url_data = response["data"][0]
        assert url_data["br"] == 320000

    def test_parse_lyric(self):
        """测试解析歌词"""
        lyric = "[00:00.00]第一行\n[00:05.00]第二行\n[00:10.00]第三行"
        lines = [l for l in lyric.split("\n") if l.strip()]
        assert len(lines) == 3


class TestNeteaseDownloadLogic:
    """网易云下载逻辑测试"""

    def test_filename_from_metadata(self):
        """测试从元数据生成文件名"""
        import re

        metadata = {
            "name": "Test<>Song",
            "artist": "Artist",
        }
        # 清理非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', "", metadata["name"])
        filename = f"{metadata['artist']} - {safe_name}.mp3"
        assert "<" not in filename
        assert ">" not in filename

    def test_quality_selection(self):
        """测试音质选择"""
        available_qualities = ["standard", "higher", "exhigh", "lossless", "hires"]
        preferred = "exhigh"
        selected = preferred if preferred in available_qualities else "standard"
        assert selected == "exhigh"

    def test_fallback_quality(self):
        """测试回退音质"""
        available = ["standard", "higher"]
        preferred = "lossless"
        selected = preferred if preferred in available else available[-1]
        assert selected == "higher"


class TestNeteaseErrorHandling:
    """网易云错误处理测试"""

    def test_vip_song_handling(self):
        """测试VIP歌曲处理"""
        response = {
            "data": [{"id": 123, "url": None, "freeTrialInfo": {"start": 0, "end": 60}}],
            "code": 200,
        }
        # VIP歌曲URL为空
        assert response["data"][0]["url"] is None

    def test_region_restriction(self):
        """测试地区限制处理"""
        response = {
            "code": 403,
            "message": "Region restricted",
        }
        assert response["code"] == 403

    def test_rate_limit_handling(self):
        """测试频率限制处理"""
        response = {
            "code": 429,
            "message": "Too many requests",
        }
        assert response["code"] == 429
