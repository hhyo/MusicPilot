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
        params: dict[str, object] = {
            "query": payload.keyword.strip(),
            "limit": payload.page_size,
            "offset": (payload.page - 1) * payload.page_size,
            "fmt": "json",
        }
        if self._should_use_dismax(payload.keyword):
            params["dismax"] = "true"
        data = self._get(
            path,
            params,
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
        release_groups = data.get("release-groups", [])
        related_albums = self._build_artist_related_albums(release_groups)
        featured_albums, featured_singles, featured_other_releases = self._build_artist_featured_release_groups(
            related_albums
        )
        return MetadataDetail(
            entity_type=EntityType.ARTIST,
            id=data["id"],
            title=data["name"],
            artist_name=data["name"],
            sort_name=data.get("sort-name"),
            artist_type=data.get("type"),
            aliases=aliases,
            year=self._extract_year(data.get("life-span", {}).get("begin")),
            genres=genres,
            external_ids={"musicbrainz": data["id"]},
            provider=self.provider,
            source_type=self.source_type,
            mock=False,
            note="当前艺人详情来自 MusicBrainz WS/2。",
            disambiguation=data.get("disambiguation"),
            country=data.get("country"),
            area_name=(data.get("area") or {}).get("name"),
            begin_area_name=(data.get("begin-area") or {}).get("name"),
            end_area_name=(data.get("end-area") or {}).get("name"),
            ended=(data.get("life-span") or {}).get("ended"),
            release_group_count=len(release_groups),
            primary_release_types=self._extract_primary_release_types(release_groups),
            featured_albums=featured_albums,
            featured_singles=featured_singles,
            featured_other_releases=featured_other_releases,
            featured_release_group_counts={
                "album": sum(1 for item in related_albums if self._reference_primary_type(item) == "album"),
                "single": sum(1 for item in related_albums if self._reference_primary_type(item) == "single"),
                "other": sum(
                    1
                    for item in related_albums
                    if self._reference_primary_type(item) not in {"album", "single"}
                ),
                "total": len(related_albums),
            },
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
        release_detail = self._get_release_detail(best_release["id"]) if best_release else None
        tracks = self._map_release_tracks(release_detail, artist_name) if release_detail else []
        release_context = self._build_release_context(best_release, release_detail)
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
            country=release_context["country"],
            status=release_context["status"],
            barcode=release_context["barcode"],
            media_format=release_context["media_format"],
            track_count=release_context["track_count"],
            disc_count=release_context["disc_count"],
            label_names=release_context["label_names"],
            secondary_types=self._extract_secondary_types(data),
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
            {"fmt": "json", "inc": "artist-credits+releases+release-groups"},
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
        best_release = self._select_best_release(releases)
        release_detail = self._get_release_detail(best_release["id"]) if best_release and best_release.get("id") else None
        related_album = self._resolve_related_album(releases, artist_name, release_detail)
        release_context = self._build_release_context(best_release, release_detail)
        secondary_types = self._extract_release_group_secondary_types(best_release, release_detail)
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
            country=release_context["country"],
            status=release_context["status"],
            barcode=release_context["barcode"],
            media_format=release_context["media_format"],
            track_count=release_context["track_count"],
            disc_count=release_context["disc_count"],
            label_names=release_context["label_names"],
            secondary_types=secondary_types,
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
        release_detail: dict | None = None,
    ) -> MetadataReference | None:
        if not releases:
            return None
        release = self._select_best_release(releases) or releases[0]
        release_group = release.get("release-group")
        if not release_group and release_detail:
            release_group = release_detail.get("release-group")
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
        return self._map_release_tracks(release, artist_name)

    def _map_release_tracks(
        self,
        release: dict,
        artist_name: str | None,
    ) -> list[MetadataReference]:
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

    def _build_release_context(
        self,
        release: dict | None,
        release_detail: dict | None,
    ) -> dict[str, object]:
        source = release_detail or {}
        return {
            "country": source.get("country") or (release or {}).get("country"),
            "status": source.get("status") or (release or {}).get("status"),
            "barcode": source.get("barcode") or (release or {}).get("barcode"),
            "label_names": self._extract_label_names(source),
            "media_format": self._extract_media_format(source),
            "track_count": self._extract_track_count(source),
            "disc_count": self._extract_disc_count(source),
        }

    @staticmethod
    def _extract_label_names(release_detail: dict) -> list[str]:
        names: list[str] = []
        for item in release_detail.get("label-info", []):
            label = item.get("label") or {}
            name = (label.get("name") or "").strip()
            if name:
                names.append(name)
        return names

    @staticmethod
    def _extract_media_format(release_detail: dict) -> str | None:
        formats = []
        for media in release_detail.get("media", []):
            fmt = (media.get("format") or "").strip()
            if fmt and fmt not in formats:
                formats.append(fmt)
        return " / ".join(formats) if formats else None

    @staticmethod
    def _extract_track_count(release_detail: dict) -> int | None:
        total = sum(len(media.get("tracks", [])) for media in release_detail.get("media", []))
        return total or None

    @staticmethod
    def _extract_disc_count(release_detail: dict) -> int | None:
        count = len(release_detail.get("media", []))
        return count or None

    @staticmethod
    def _extract_secondary_types(data: dict) -> list[str]:
        return [item.strip() for item in data.get("secondary-types", []) if isinstance(item, str) and item.strip()]

    def _extract_release_group_secondary_types(
        self,
        release: dict | None,
        release_detail: dict | None,
    ) -> list[str]:
        release_group = (release or {}).get("release-group") or (release_detail or {}).get("release-group") or {}
        return self._extract_secondary_types(release_group)

    def _build_artist_related_albums(self, release_groups: list[dict]) -> list[MetadataReference]:
        sorted_items = sorted(release_groups, key=self._artist_release_group_sort_key)
        result: list[MetadataReference] = []
        for item in sorted_items:
            item_id = item.get("id")
            title = item.get("title")
            if not item_id or not title:
                continue
            subtitle = self._format_release_group_subtitle(item)
            result.append(
                MetadataReference(
                    id=item_id,
                    title=title,
                    entity_type=EntityType.ALBUM,
                    subtitle=subtitle,
                )
            )
        return result

    @staticmethod
    def _extract_primary_release_types(release_groups: list[dict]) -> list[str]:
        seen: list[str] = []
        for item in sorted(release_groups, key=MusicBrainzMetadataProviderAdapter._artist_release_group_sort_key):
            primary_type = (item.get("primary-type") or "").strip()
            if primary_type and primary_type not in seen:
                seen.append(primary_type)
        return seen

    @staticmethod
    def _artist_release_group_sort_key(item: dict) -> tuple[int, str, str]:
        priority = {
            "album": 0,
            "ep": 1,
            "single": 2,
            "compilation": 3,
            "live": 4,
        }
        primary_type = (item.get("primary-type") or "").strip().lower()
        year = MusicBrainzMetadataProviderAdapter._extract_year(item.get("first-release-date")) or 0
        title = (item.get("title") or "").strip().lower()
        return (priority.get(primary_type, 9), -year, title)

    @staticmethod
    def _format_release_group_subtitle(item: dict) -> str | None:
        parts: list[str] = []
        primary_type = (item.get("primary-type") or "").strip()
        year = MusicBrainzMetadataProviderAdapter._extract_year(item.get("first-release-date"))
        if primary_type:
            parts.append(primary_type)
        if year:
            parts.append(str(year))
        return " · ".join(parts) if parts else None

    @staticmethod
    def _reference_primary_type(item: MetadataReference) -> str | None:
        if not item.subtitle:
            return None
        return item.subtitle.split("·", 1)[0].strip().lower()

    def _build_artist_featured_release_groups(
        self,
        related_albums: list[MetadataReference],
    ) -> tuple[list[MetadataReference], list[MetadataReference], list[MetadataReference]]:
        albums = [item for item in related_albums if self._reference_primary_type(item) == "album"][:3]
        singles = [item for item in related_albums if self._reference_primary_type(item) == "single"][:3]
        others = [
            item
            for item in related_albums
            if self._reference_primary_type(item) not in {"album", "single"}
        ][:3]
        return albums, singles, others

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
    def _should_use_dismax(keyword: str) -> bool:
        normalized = keyword.strip()
        if not normalized:
            return False
        advanced_tokens = (":", " AND ", " OR ", " NOT ", "\"", "(", ")")
        return not any(token in normalized for token in advanced_tokens)

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
