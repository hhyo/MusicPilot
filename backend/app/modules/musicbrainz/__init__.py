"""
MusicBrainz 模块
使用 musicbrainzngs 库集成 MusicBrainz API
"""
import time
from typing import Optional, List, Dict, Any
from musicbrainzngs import set_useragent, get_artist_by_id, search_artists
from musicbrainzngs import get_release_group_by_id, search_release_groups
from musicbrainzngs import get_recording_by_id, search_recordings
from musicbrainzngs import get_release_cover_url

from app.core.module import ModuleBase
from app.core.log import logger
from app.core.config import settings


class MusicBrainzModule(ModuleBase):
    """
    MusicBrainz 模块
    提供 MusicBrainz API 集成功能
    """

    module_type = "musicbrainz"

    def __init__(self):
        super().__init__()
        # 设置 User-Agent（MusicBrainz 要求）
        set_useragent(
            f"{settings.musicbrainz_app_name}/{settings.musicbrainz_app_version}",
            "https://github.com/hhyo/MusicPilot"
        )
        self._last_request_time = 0
        self._rate_limit = 1.0  # 1 请求/秒

    def _rate_limit(self):
        """遵守 API 速率限制"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        self._last_request_time = time.time()

    async def search_artist(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索艺术家

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            艺术家列表
        """
        self._rate_limit()
        self.logger.info(f"搜索艺术家: {query}")

        result = search_artists(query, limit=limit)
        artists = []

        for artist in result.get("artist-list", []):
            artists.append({
                "id": artist.get("id"),
                "name": artist.get("name"),
                "type": artist.get("type"),
                "disambiguation": artist.get("disambiguation"),
                "country": artist.get("country"),
                "gender": artist.get("gender"),
            })

        self.logger.info(f"找到 {len(artists)} 个艺术家")
        return artists

    async def get_artist_info(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """
        获取艺术家详情

        Args:
            artist_id: MusicBrainz 艺术家 ID

        Returns:
            艺术家详情
        """
        self._rate_limit()
        self.logger.info(f"获取艺术家详情: {artist_id}")

        try:
            artist = get_artist_by_id(artist_id)
        except Exception as e:
            self.logger.error(f"获取艺术家详情失败: {e}")
            return None

        if not artist:
            self.logger.warning(f"艺术家不存在: {artist_id}")
            return None

        # 提取艺术家信息
        artist_info = {
            "id": artist.get("id"),
            "name": artist.get("name"),
            "type": artist.get("type"),
            "disambiguation": artist.get("disambiguation"),
            "country": artist.get("country"),
            "gender": artist.get("gender"),
            "life_span": artist.get("life-span"),
            "image_url": self._get_artist_image(artist),
        }

        # 获取作品集
        releases = []
        release_groups = artist.get("release-group-list", [])
        for rg in release_groups[:50]:  # 限制最多 50 个专辑
            releases.append({
                "id": rg.get("id"),
                "title": rg.get("title"),
                "type": rg.get("type"),
                "first_release_date": rg.get("first-release-date"),
                "primary_type": rg.get("primary-type"),
            })

        artist_info["releases"] = releases
        artist_info["release_count"] = len(releases)

        self.logger.info(f"获取艺术家详情成功: {artist_info['name']}")
        return artist_info

    async def search_album(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索专辑

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            专辑列表
        """
        self._rate_limit()
        self.logger.info(f"搜索专辑: {query}")

        result = search_release_groups(query, limit=limit)
        albums = []

        for rg in result.get("release-group-list", []):
            album = {
                "id": rg.get("id"),
                "title": rg.get("title"),
                "type": rg.get("type"),
                "primary_type": rg.get("primary-type"),
                "first_release_date": rg.get("first-release-date"),
                "artist_credit": self._parse_artist_credit(rg.get("artist-credit")),
            }
            albums.append(album)

        self.logger.info(f"找到 {len(albums)} 个专辑")
        return albums

    async def get_album_info(self, album_id: str) -> Optional[Dict[str, Any]]:
        """
        获取专辑详情

        Args:
            album_id: MusicBrainz 专辑 ID

        Returns:
            专辑详情
        """
        self._rate_limit()
        self.logger.info(f"获取专辑详情: {album_id}")

        try:
            rg = get_release_group_by_id(album_id)
        except Exception as e:
            self.logger.error(f"获取专辑详情失败: {e}")
            return None

        if not rg:
            self.logger.warning(f"专辑不存在: {album_id}")
            return None

        # 提取专辑信息
        album_info = {
            "id": rg.get("id"),
            "title": rg.get("title"),
            "type": rg.get("type"),
            "primary_type": rg.get("primary-type"),
            "disambiguation": rg.get("disambiguation"),
            "first_release_date": rg.get("first-release-date"),
            "artist_credit": self._parse_artist_credit(rg.get("artist-credit")),
            "cover_url": self._get_album_cover(rg),
            "tags": [tag.get("name") for tag in rg.get("tag-list", [])],
        }

        self.logger.info(f"获取专辑详情成功: {album_info['title']}")
        return album_info

    async def search_track(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索曲目

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            曲目列表
        """
        self._rate_limit()
        self.logger.info(f"搜索曲目: {query}")

        result = search_recordings(query, limit=limit)
        tracks = []

        for recording in result.get("recording-list", []):
            track = {
                "id": recording.get("id"),
                "title": recording.get("title"),
                "artist_credit": self._parse_artist_credit(recording.get("artist-credit")),
            }
            tracks.append(track)

        self.logger.info(f"找到 {len(tracks)} 个曲目")
        return tracks

    async def get_track_info(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        获取曲目详情

        Args:
            track_id: MusicBrainz 曲目 ID

        Returns:
            曲目详情
        """
        self._rate_limit()
        self.logger.info(f"获取曲目详情: {track_id}")

        try:
            recording = get_recording_by_id(track_id)
        except Exception as e:
            self.logger.error(f"获取曲目详情失败: {e}")
            return None

        if not recording:
            self.logger.warning(f"曲目不存在: {track_id}")
            return None

        # 提取曲目信息
        track_info = {
            "id": recording.get("id"),
            "title": recording.get("title"),
            "length": recording.get("length"),
            "artist_credit": self._parse_artist_credit(recording.get("artist-credit")),
        }

        self.logger.info(f"获取曲目详情成功: {track_info['title']}")
        return track_info

    async def download_cover(
        self,
        musicbrainz_id: str,
        cover_type: str = "front"
    ) -> Optional[str]:
        """
        下载封面图片

        Args:
            musicbrainz_id: MusicBrainz ID
            cover_type: 封面类型（front/back）

        Returns:
            封面 URL
        """
        self._rate_limit()
        self.logger.info(f"下载封面: {musicbrainz_id}, 类型: {cover_type}")

        try:
            cover_url = get_release_cover_url(musicbrainz_id, cover_type)
            self.logger.info(f"获取封面 URL 成功: {cover_url}")
            return cover_url
        except Exception as e:
            self.logger.error(f"下载封面失败: {e}")
            return None

    def _parse_artist_credit(self, artist_credit: Any) -> Optional[Dict[str, Any]]:
        """
        解析艺术家署名

        Args:
            artist_credit: 艺术家署名对象

        Returns:
            艺术家信息字典
        """
        if not artist_credit:
            return None

        if isinstance(artist_credit, list):
            # 多艺术家
            names = [ac.get("name") or ac.get("artist", {}).get("name")
                      for ac in artist_credit]
            return {
                "names": names,
                "joinphrase": artist_credit[0].get("joinphrase", ", "),
            }
        elif isinstance(artist_credit, dict):
            # 单艺术家
            artist = artist_credit.get("artist", {})
            return {
                "id": artist.get("id"),
                "name": artist.get("name"),
            }
        return None

    def _get_artist_image(self, artist: Dict) -> Optional[str]:
        """
        获取艺术家图片 URL

        Args:
            artist: 艺术家对象

        Returns:
            图片 URL
        """
        # TODO: 实现从其他服务获取艺术家图片（如 Spotify）
        return None

    def _get_album_cover(self, release_group: Dict) -> Optional[str]:
        """
        获取专辑封面 URL

        Args:
            release_group: 发行组对象

        Returns:
            封面 URL
        """
        # 获取第一个发行
        releases = release_group.get("release-list", [])
        if not releases:
            return None

        release_id = releases[0].get("id")
        if not release_id:
            return None

        try:
            return self.download_cover(release_id, "front")
        except Exception:
            return None
