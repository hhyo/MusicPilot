"""Adapter boundary for metadata providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from time import monotonic, sleep

import httpx

from ..core.runtime_cache import RuntimeTTLCache, stable_cache_key
from ..schemas.metadata import (
    MetadataDetail,
    MetadataReference,
    MetadataSearchData,
    MetadataSearchRequest,
    MetadataSeedCatalog,
    MetadataSummary,
    SeedAlbum,
    SeedArtist,
    SeedTrack,
)
from ..schemas.mvp import EntityType, ReleaseType


class MetadataProviderAdapter(ABC):
    """Provider boundary for metadata search/detail and optional seed ingestion."""

    @property
    @abstractmethod
    def provider(self) -> str:
        """Logical provider name."""

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Descriptor for source provenance."""

    @property
    def supports_live_queries(self) -> bool:
        return False

    @abstractmethod
    def load_seed_catalog(self) -> MetadataSeedCatalog:
        """Return the local seed catalog for the current stage."""

    def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement live search")

    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
        raise NotImplementedError(f"{self.__class__.__name__} does not implement live detail")


class MockMetadataProviderAdapter(MetadataProviderAdapter):
    """Local-seed metadata adapter for the minimum loop."""

    @property
    def provider(self) -> str:
        return "mock_seed_catalog"

    @property
    def source_type(self) -> str:
        return "local_seed"

    def load_seed_catalog(self) -> MetadataSeedCatalog:
        return MetadataSeedCatalog(
            provider=self.provider,
            source_type=self.source_type,
            note=(
                "当前元数据来自本地静态 seed，不代表已接入 QQ、网易云、Spotify、"
                "MusicBrainz 等外部音乐源。"
            ),
            artists=[
                SeedArtist(
                    id="artist-adele",
                    name="Adele",
                    aliases=["阿黛尔"],
                    genres=["Pop", "Soul"],
                    year=2008,
                    country="UK",
                    external_ids={"musicbrainz": "mock-mb-artist-adele"},
                    metadata_json={"query_builder_hint": "adele"},
                ),
                SeedArtist(
                    id="artist-taylor-swift",
                    name="Taylor Swift",
                    aliases=["泰勒·斯威夫特", "TS"],
                    genres=["Pop", "Country"],
                    year=2006,
                    country="US",
                    external_ids={"musicbrainz": "mock-mb-artist-taylor-swift"},
                    metadata_json={"query_builder_hint": "taylor swift"},
                ),
                SeedArtist(
                    id="artist-daft-punk",
                    name="Daft Punk",
                    aliases=["蠢朋克"],
                    genres=["Electronic", "Disco"],
                    year=1993,
                    country="FR",
                    external_ids={"musicbrainz": "mock-mb-artist-daft-punk"},
                    metadata_json={"query_builder_hint": "daft punk"},
                ),
                SeedArtist(
                    id="artist-billie-eilish",
                    name="Billie Eilish",
                    aliases=["比莉·艾利什"],
                    genres=["Pop", "Alternative"],
                    year=2016,
                    country="US",
                    external_ids={"musicbrainz": "mock-mb-artist-billie-eilish"},
                    metadata_json={"query_builder_hint": "billie eilish"},
                ),
            ],
            albums=[
                SeedAlbum(
                    id="album-25",
                    title="25",
                    artist_ids=["artist-adele"],
                    artist_name="Adele",
                    aliases=["二十五"],
                    year=2015,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Soul"],
                    external_ids={"musicbrainz": "mock-mb-album-25"},
                ),
                SeedAlbum(
                    id="album-1989-tv",
                    title="1989 (Taylor's Version)",
                    artist_ids=["artist-taylor-swift"],
                    artist_name="Taylor Swift",
                    aliases=["1989 重录版"],
                    year=2023,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop"],
                    external_ids={"musicbrainz": "mock-mb-album-1989-tv"},
                ),
                SeedAlbum(
                    id="album-random-access-memories",
                    title="Random Access Memories",
                    artist_ids=["artist-daft-punk"],
                    artist_name="Daft Punk",
                    aliases=["随机存取的回忆"],
                    year=2013,
                    release_type=ReleaseType.ALBUM,
                    genres=["Electronic", "Disco"],
                    external_ids={"musicbrainz": "mock-mb-album-ram"},
                ),
                SeedAlbum(
                    id="album-hit-me-hard-and-soft",
                    title="Hit Me Hard and Soft",
                    artist_ids=["artist-billie-eilish"],
                    artist_name="Billie Eilish",
                    year=2024,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Alternative"],
                    external_ids={"musicbrainz": "mock-mb-album-hit-me-hard-and-soft"},
                ),
            ],
            tracks=[
                SeedTrack(
                    id="track-hello",
                    title="Hello",
                    artist_ids=["artist-adele"],
                    artist_name="Adele",
                    album_id="album-25",
                    album_title="25",
                    year=2015,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Soul"],
                    external_ids={"musicbrainz": "mock-mb-track-hello"},
                    duration_seconds=295,
                ),
                SeedTrack(
                    id="track-anti-hero",
                    title="Anti-Hero",
                    artist_ids=["artist-taylor-swift"],
                    artist_name="Taylor Swift",
                    album_title="Midnights",
                    aliases=["反英雄"],
                    year=2022,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop"],
                    external_ids={"musicbrainz": "mock-mb-track-anti-hero"},
                    duration_seconds=201,
                ),
                SeedTrack(
                    id="track-get-lucky",
                    title="Get Lucky",
                    artist_ids=["artist-daft-punk"],
                    artist_name="Daft Punk",
                    album_id="album-random-access-memories",
                    album_title="Random Access Memories",
                    year=2013,
                    release_type=ReleaseType.ALBUM,
                    genres=["Electronic", "Disco"],
                    external_ids={"musicbrainz": "mock-mb-track-get-lucky"},
                    duration_seconds=369,
                ),
                SeedTrack(
                    id="track-birds-of-a-feather",
                    title="Birds of a Feather",
                    artist_ids=["artist-billie-eilish"],
                    artist_name="Billie Eilish",
                    album_id="album-hit-me-hard-and-soft",
                    album_title="Hit Me Hard and Soft",
                    year=2024,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Alternative"],
                    external_ids={"musicbrainz": "mock-mb-track-birds-of-a-feather"},
                    duration_seconds=210,
                ),
            ],
        )


class MusicBrainzMetadataProviderAdapter(MetadataProviderAdapter):
    """Minimal MusicBrainz WS/2 metadata provider."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        base_url: str = "https://musicbrainz.org/ws/2",
        user_agent: str = "MusicPilot/0.1.0 (local)",
        timeout_seconds: float = 15.0,
        cache_enabled: bool = True,
        cache_maxsize: int = 512,
        search_cache_ttl_seconds: int = 1800,
        detail_cache_ttl_seconds: int = 21600,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"User-Agent": user_agent},
            timeout=timeout_seconds,
        )
        self._last_request_at = 0.0
        self._search_cache = (
            RuntimeTTLCache(
                region="musicpilot_metadata_search",
                maxsize=cache_maxsize,
                ttl=search_cache_ttl_seconds,
            )
            if cache_enabled
            else None
        )
        self._detail_cache = (
            RuntimeTTLCache(
                region="musicpilot_metadata_detail",
                maxsize=cache_maxsize,
                ttl=detail_cache_ttl_seconds,
            )
            if cache_enabled
            else None
        )

    @property
    def provider(self) -> str:
        return "musicbrainz"

    @property
    def source_type(self) -> str:
        return "musicbrainz_ws2"

    @property
    def supports_live_queries(self) -> bool:
        return True

    def load_seed_catalog(self) -> MetadataSeedCatalog:
        raise NotImplementedError("MusicBrainz provider does not provide a local seed catalog.")

    def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
        cache_key = stable_cache_key(
            "musicbrainz_search",
            entity_type=payload.type.value,
            keyword=payload.keyword.strip().lower(),
            page=payload.page,
            page_size=payload.page_size,
        )
        if self._search_cache is not None:
            cached_result = self._search_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        path, response_key = self._search_path(payload.type)
        data = self._get(
            path,
            {
                "query": payload.keyword.strip(),
                "limit": payload.page_size,
                "offset": (payload.page - 1) * payload.page_size,
                "fmt": "json",
            },
        )
        items = [self._map_search_item(payload.type, item) for item in data.get(response_key, [])]
        result = MetadataSearchData(
            keyword=payload.keyword,
            entity_type=payload.type,
            page=payload.page,
            page_size=payload.page_size,
            total=int(data.get("count", len(items))),
            provider=self.provider,
            source_type=self.source_type,
            integration_point="MusicBrainzMetadataProviderAdapter.search",
            items=items,
        )
        if self._search_cache is not None:
            self._search_cache.set(cache_key, result)
        return result

    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
        cache_key = stable_cache_key(
            "musicbrainz_detail",
            entity_type=entity_type.value,
            entity_id=entity_id,
        )
        if self._detail_cache is not None:
            cached_result = self._detail_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        if entity_type == EntityType.ARTIST:
            result = self._get_artist_detail(entity_id)
        elif entity_type == EntityType.ALBUM:
            result = self._get_album_detail(entity_id)
        else:
            result = self._get_track_detail(entity_id)

        if self._detail_cache is not None:
            self._detail_cache.set(cache_key, result)
        return result

    def _get_artist_detail(self, artist_id: str) -> MetadataDetail:
        data = self._get(
            f"artist/{artist_id}",
            {"fmt": "json", "inc": "aliases+release-groups"},
        )
        aliases = self._extract_aliases(data)
        genres = self._extract_tags(data)
        related_albums = [
            MetadataReference(
                id=item["id"],
                title=item["title"],
                entity_type=EntityType.ALBUM,
                subtitle=item.get("primary-type"),
            )
            for item in data.get("release-groups", [])
        ]
        return MetadataDetail(
            entity_type=EntityType.ARTIST,
            id=data["id"],
            title=data["name"],
            artist_name=data["name"],
            aliases=aliases,
            year=self._extract_year(data.get("life-span", {}).get("begin")),
            genres=genres,
            external_ids={"musicbrainz": data["id"]},
            provider=self.provider,
            source_type=self.source_type,
            mock=False,
            note="当前艺人详情来自 MusicBrainz WS/2。",
            country=data.get("country"),
            integration_point="MusicBrainzMetadataProviderAdapter.get_artist_detail",
            related_albums=related_albums,
            todo=[
                "当前详情直接来自 MusicBrainz，不包含 PT 搜索、下载派发或整理结果。",
            ],
        )

    def _get_album_detail(self, album_id: str) -> MetadataDetail:
        data = self._get(
            f"release-group/{album_id}",
            {"fmt": "json", "inc": "aliases+artist-credits+releases"},
        )
        artist_name = self._join_artist_credit(data.get("artist-credit", []))
        releases = data.get("releases", [])
        related_artists = [
            MetadataReference(
                id=item["artist"]["id"],
                title=item["artist"]["name"],
                entity_type=EntityType.ARTIST,
                subtitle=item.get("name"),
            )
            for item in data.get("artist-credit", [])
            if item.get("artist")
        ]
        best_release = self._select_best_release(releases)
        tracks = self._fetch_release_tracks(best_release["id"], artist_name) if best_release else []
        return MetadataDetail(
            entity_type=EntityType.ALBUM,
            id=data["id"],
            title=data["title"],
            artist_name=artist_name,
            album_title=data["title"],
            aliases=self._extract_aliases(data),
            year=self._extract_year(data.get("first-release-date")),
            release_type=self._map_release_type(data.get("primary-type")),
            genres=self._extract_tags(data),
            external_ids={"musicbrainz": data["id"]},
            provider=self.provider,
            source_type=self.source_type,
            mock=False,
            note="当前专辑详情来自 MusicBrainz WS/2。",
            disambiguation=data.get("disambiguation"),
            release_count=len(releases),
            integration_point="MusicBrainzMetadataProviderAdapter.get_album_detail",
            related_artists=related_artists,
            tracks=tracks,
            todo=[
                "当前详情直接来自 MusicBrainz，不包含 PT 搜索、下载派发或整理结果。",
            ],
        )

    def _get_track_detail(self, track_id: str) -> MetadataDetail:
        data = self._get(
            f"recording/{track_id}",
            {"fmt": "json", "inc": "artist-credits+releases"},
        )
        artist_name = self._join_artist_credit(data.get("artist-credit", []))
        related_artists = [
            MetadataReference(
                id=item["artist"]["id"],
                title=item["artist"]["name"],
                entity_type=EntityType.ARTIST,
                subtitle=item.get("name"),
            )
            for item in data.get("artist-credit", [])
            if item.get("artist")
        ]
        releases = data.get("releases", [])
        related_album = self._resolve_related_album(releases, artist_name)
        return MetadataDetail(
            entity_type=EntityType.TRACK,
            id=data["id"],
            title=data["title"],
            artist_name=artist_name,
            album_title=related_album.title if related_album else self._extract_release_title(data),
            track_title=data["title"],
            aliases=self._extract_aliases(data),
            year=self._extract_year(releases[0].get("date")) if releases else None,
            genres=self._extract_tags(data),
            external_ids={"musicbrainz": data["id"]},
            provider=self.provider,
            source_type=self.source_type,
            mock=False,
            note="当前歌曲详情来自 MusicBrainz WS/2。",
            duration_seconds=self._extract_duration_seconds(data.get("length")),
            disambiguation=data.get("disambiguation"),
            integration_point="MusicBrainzMetadataProviderAdapter.get_track_detail",
            related_artists=related_artists,
            related_album=related_album,
            todo=[
                "当前详情直接来自 MusicBrainz，不包含 PT 搜索、下载派发或整理结果。",
            ],
        )

    def _search_path(self, entity_type: EntityType) -> tuple[str, str]:
        if entity_type == EntityType.ARTIST:
            return "artist", "artists"
        if entity_type == EntityType.ALBUM:
            return "release-group", "release-groups"
        return "recording", "recordings"

    def _map_search_item(self, entity_type: EntityType, item: dict) -> MetadataSummary:
        if entity_type == EntityType.ARTIST:
            title = item["name"]
            artist_name = item["name"]
            album_title = None
            track_title = None
            year = self._extract_year(item.get("life-span", {}).get("begin"))
            release_type = None
        elif entity_type == EntityType.ALBUM:
            title = item["title"]
            artist_name = self._join_artist_credit(item.get("artist-credit", []))
            album_title = item["title"]
            track_title = None
            year = self._extract_year(item.get("first-release-date"))
            release_type = self._map_release_type(item.get("primary-type"))
        else:
            title = item["title"]
            artist_name = self._join_artist_credit(item.get("artist-credit", []))
            album_title = self._extract_release_title(item)
            track_title = item["title"]
            year = self._extract_year(self._extract_release_date(item))
            release_type = None

        return MetadataSummary(
            entity_type=entity_type,
            id=item["id"],
            title=title,
            artist_name=artist_name,
            album_title=album_title,
            track_title=track_title,
            aliases=self._extract_aliases(item),
            year=year,
            release_type=release_type,
            genres=self._extract_tags(item),
            external_ids={"musicbrainz": item["id"]},
            provider=self.provider,
            source_type=self.source_type,
            mock=False,
            note=f"当前结果来自 MusicBrainz WS/2 {entity_type.value} 查询。",
        )

    def _get(self, path: str, params: dict[str, object]) -> dict:
        self._respect_rate_limit()
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def _get_release_detail(self, release_id: str) -> dict:
        return self._get(
            f"release/{release_id}",
            {"fmt": "json", "inc": "recordings+artist-credits"},
        )

    def _resolve_related_album(
        self,
        releases: list[dict],
        artist_name: str | None,
    ) -> MetadataReference | None:
        if not releases:
            return None
        release = self._select_best_release(releases) or releases[0]
        release_group = release.get("release-group")
        if not release_group and release.get("id"):
            release_group = self._get_release_detail(release["id"]).get("release-group")
        if not release_group:
            return MetadataReference(
                id=release["id"],
                title=release.get("title") or "Unknown Release",
                entity_type=EntityType.ALBUM,
                subtitle=artist_name,
            )
        return MetadataReference(
            id=release_group["id"],
            title=release_group.get("title") or release.get("title") or "Unknown Release Group",
            entity_type=EntityType.ALBUM,
            subtitle=artist_name,
        )

    def _fetch_release_tracks(
        self,
        release_id: str,
        artist_name: str | None,
    ) -> list[MetadataReference]:
        release = self._get_release_detail(release_id)
        tracks: list[MetadataReference] = []
        for disc_index, media in enumerate(release.get("media", []), start=1):
            disc_number = self._extract_int(media.get("position")) or disc_index
            for track in media.get("tracks", []):
                recording = track.get("recording", {})
                track_id = recording.get("id") or track.get("id")
                track_title = recording.get("title") or track.get("title")
                if not track_id or not track_title:
                    continue
                track_number = self._extract_int(track.get("position")) or self._extract_int(track.get("number"))
                tracks.append(
                    MetadataReference(
                        id=track_id,
                        title=track_title,
                        entity_type=EntityType.TRACK,
                        subtitle=artist_name,
                        track_number=track_number,
                        disc_number=disc_number,
                    )
                )
        return tracks

    @staticmethod
    def _select_best_release(releases: list[dict]) -> dict | None:
        if not releases:
            return None

        def sort_key(item: dict) -> tuple[int, str, str]:
            status = (item.get("status") or "").strip().lower()
            date = (item.get("date") or "").strip()
            title = (item.get("title") or "").strip().lower()
            return (0 if status == "official" else 1, date or "9999-99-99", title)

        return sorted(releases, key=sort_key)[0]

    @staticmethod
    def _extract_int(value: object) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            digits = "".join(char for char in value if char.isdigit())
            if digits:
                return int(digits)
        return None

    def _respect_rate_limit(self) -> None:
        elapsed = monotonic() - self._last_request_at
        if self._last_request_at and elapsed < 1.0:
            sleep(1.0 - elapsed)
        self._last_request_at = monotonic()

    @staticmethod
    def _extract_aliases(data: dict) -> list[str]:
        return [item.get("name", "").strip() for item in data.get("aliases", []) if item.get("name")]

    @staticmethod
    def _extract_tags(data: dict) -> list[str]:
        return [item.get("name", "").strip() for item in data.get("tags", []) if item.get("name")]

    @staticmethod
    def _extract_year(value: str | None) -> int | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).year
        except ValueError:
            if len(value) >= 4 and value[:4].isdigit():
                return int(value[:4])
        return None

    @staticmethod
    def _extract_duration_seconds(length_ms: int | None) -> int | None:
        if length_ms is None:
            return None
        return int(length_ms // 1000)

    @staticmethod
    def _join_artist_credit(items: list[dict]) -> str | None:
        parts: list[str] = []
        for item in items:
            if item.get("name"):
                parts.append(item["name"])
            elif item.get("artist", {}).get("name"):
                parts.append(item["artist"]["name"])
        return ", ".join(parts) if parts else None

    @staticmethod
    def _extract_release_title(item: dict) -> str | None:
        releases = item.get("releases", [])
        if not releases:
            return None
        return releases[0].get("title")

    @staticmethod
    def _extract_release_date(item: dict) -> str | None:
        releases = item.get("releases", [])
        if not releases:
            return None
        return releases[0].get("date")

    @staticmethod
    def _map_release_type(value: str | None) -> ReleaseType | None:
        if not value:
            return None
        mapping = {
            "album": ReleaseType.ALBUM,
            "single": ReleaseType.SINGLE,
            "ep": ReleaseType.EP,
            "compilation": ReleaseType.COMPILATION,
            "live": ReleaseType.LIVE,
        }
        return mapping.get(value.strip().lower())
