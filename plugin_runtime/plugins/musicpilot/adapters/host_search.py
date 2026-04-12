"""Host PT search adapter boundary with MoviePilot runtime mapping."""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Any

from .host_http import HostHttpClient, HostTransportError
from ..core.config import Settings
from ..schemas.acquisition import HostSearchCandidate, QueryBuildResult
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterSelectionMode, VerificationState
from ..schemas.music_media import MusicMediaInfo
from ..schemas.mvp import EntityType


def normalize_title(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())


class HostSearchAdapter(ABC):
    @abstractmethod
    def search(self, *, query_build: QueryBuildResult, media: MusicMediaInfo) -> list[HostSearchCandidate]:
        """Search host PT sites with the built query payload."""


class MockHostSearchAdapter(HostSearchAdapter):
    """Stable mock PT search adapter for the Phase 3 minimum loop."""

    def search(self, *, query_build: QueryBuildResult, media: MusicMediaInfo) -> list[HostSearchCandidate]:
        primary_artist = " ".join(media.artist_names or media.album_artist_names) or (media.title or media.provider_id)
        primary_title = media.title or media.album_title or primary_artist

        if media.entity_type == EntityType.ALBUM:
            exact_title = f"{primary_artist} - {primary_title} ({media.year}) [FLAC] [24bit]"
            manual_title = f"{primary_artist} - {primary_title} Deluxe Edition [AAC 320]"
            reject_title = f"{primary_artist} Karaoke Tribute Collection [MP3 128]"
        elif media.entity_type == EntityType.TRACK:
            exact_title = f"{primary_artist} - {primary_title} [{media.album_title}] [FLAC]"
            manual_title = f"{primary_artist} - {primary_title} Acoustic Session [AAC 320]"
            reject_title = f"{primary_artist} - {primary_title} Instrumental Cover [MP3 128]"
        else:
            exact_title = f"{primary_title} Discography Collection [FLAC]"
            manual_title = f"{primary_title} Anthology Selection [AAC 320]"
            reject_title = f"{primary_title} Tribute Karaoke Pack [MP3 128]"

        return [
            HostSearchCandidate(
                site_id="mock-site-lossless",
                site_name="Mock Lossless",
                title=exact_title,
                normalized_title=normalize_title(exact_title),
                size_bytes=2_048_000_000,
                seeders=28,
                peers=4,
                format_tag="flac",
                bitrate_kbps=1000,
                source_tags=["lossless", "official", media.entity_type.value],
                note="当前候选来自 mock host search adapter，不代表已接入真实 PT 站点。",
                adapter_resolution=AdapterResolution(
                    adapter_key="mock_host_search",
                    adapter_mode=AdapterMode.MOCK,
                    selection_mode=AdapterSelectionMode.MOCK,
                    capability_source="mock.adapter",
                    verification_state=VerificationState.PLACEHOLDER,
                    integration_point="MockHostSearchAdapter.search",
                    host_integration_enabled=False,
                ),
                raw_payload={
                    "query_preview": [query.query for query in query_build.ordered_queries[:2]],
                    "variant": "exact_lossless",
                },
            ),
            HostSearchCandidate(
                site_id="mock-site-scene",
                site_name="Mock Scene",
                title=manual_title,
                normalized_title=normalize_title(manual_title),
                size_bytes=680_000_000,
                seeders=9,
                peers=6,
                format_tag="aac",
                bitrate_kbps=320,
                source_tags=["deluxe", "scene", "anthology"],
                note="当前候选来自 mock host search adapter，用于验证人工确认边界。",
                adapter_resolution=AdapterResolution(
                    adapter_key="mock_host_search",
                    adapter_mode=AdapterMode.MOCK,
                    selection_mode=AdapterSelectionMode.MOCK,
                    capability_source="mock.adapter",
                    verification_state=VerificationState.PLACEHOLDER,
                    integration_point="MockHostSearchAdapter.search",
                    host_integration_enabled=False,
                ),
                raw_payload={"variant": "manual_review"},
            ),
            HostSearchCandidate(
                site_id="mock-site-noisy",
                site_name="Mock Noisy",
                title=reject_title,
                normalized_title=normalize_title(reject_title),
                size_bytes=120_000_000,
                seeders=2,
                peers=8,
                format_tag="mp3",
                bitrate_kbps=128,
                source_tags=["karaoke", "cover", "low_quality"],
                note="当前候选来自 mock host search adapter，用于验证拒绝与负向关键词惩罚。",
                adapter_resolution=AdapterResolution(
                    adapter_key="mock_host_search",
                    adapter_mode=AdapterMode.MOCK,
                    selection_mode=AdapterSelectionMode.MOCK,
                    capability_source="mock.adapter",
                    verification_state=VerificationState.PLACEHOLDER,
                    integration_point="MockHostSearchAdapter.search",
                    host_integration_enabled=False,
                ),
                raw_payload={"variant": "reject_case"},
            ),
        ]


class RealHostSearchAdapter(HostSearchAdapter):
    """MoviePilot-backed PT search adapter.

    Runtime verification in Phase 7A confirmed that MoviePilot search is not a generic
    JSON POST endpoint. The verified host semantics are:
    - ``GET /api/v1/search/title`` with ``keyword`` and ``page`` query params.
    - ``GET /api/v1/search/media/{mediaid}`` with query params when a compatible media id exists.
    - ``GET /api/v1/search/last`` returning ``List[Context]`` directly.
    """

    def __init__(self, *, settings: Settings, client: HostHttpClient):
        self.settings = settings
        self.client = client

    def search(self, *, query_build: QueryBuildResult, media: MusicMediaInfo) -> list[HostSearchCandidate]:
        media_id = self._resolve_media_id(query_build)
        if media_id:
            items = self._search_by_media(media_id=media_id, media=media)
            if items:
                return items

        for clause in self._iter_positive_queries(query_build):
            items = self._search_by_title(clause_query=clause.query, media=media, query_type=clause.query_type)
            if items:
                return items

        if self.settings.host_strict_empty_as_error:
            raise HostTransportError(
                "MoviePilot search endpoints were reachable but returned no parsable candidates for the current query set.",
                reason_code="moviepilot_search_empty",
            )
        return []

    def _search_by_title(
        self,
        *,
        clause_query: str,
        media: MusicMediaInfo,
        query_type: str,
    ) -> list[HostSearchCandidate]:
        payload = self.client.get_json(
            self.settings.host_search_title_path,
            params={"keyword": clause_query, "page": 0},
            auth_mode="x_api_key",
        )
        if payload.get("success") is False:
            if self._is_empty_search_response(payload):
                return []
            raise HostTransportError(
                f"MoviePilot search/title rejected the request: {payload.get('message') or 'unknown error'}",
                reason_code="moviepilot_search_title_rejected",
            )
        return self._map_context_items(
            self._extract_context_items(payload),
            media=media,
            endpoint_label="search.title",
            note=(
                "当前候选来自真实 MoviePilot `/api/v1/search/title` 返回结构，字段映射已经按宿主 Context/TorrentInfo "
                "语义收敛。"
            ),
            query_query=clause_query,
            query_type=query_type,
        )

    def _search_by_media(self, *, media_id: str, media: MusicMediaInfo) -> list[HostSearchCandidate]:
        base_path = self.settings.host_search_media_path or "/api/v1/search/media"
        payload = self.client.get_json(
            f"{base_path.rstrip('/')}/{media_id}",
            params={"area": "title"},
            auth_mode="x_api_key",
        )
        if payload.get("success") is False:
            if self._is_empty_search_response(payload):
                return []
            raise HostTransportError(
                f"MoviePilot search/media rejected the request: {payload.get('message') or 'unknown error'}",
                reason_code="moviepilot_search_media_rejected",
            )
        return self._map_context_items(
            self._extract_context_items(payload),
            media=media,
            endpoint_label="search.media",
            note=(
                "当前候选来自真实 MoviePilot `/api/v1/search/media/{mediaid}` 返回结构。"
                "Phase 8 已补到多条真实正向样例，`search/media` 现在可作为更稳定的 host-backed 候选输入。"
            ),
            query_query=media_id,
            query_type="canonical",
            verification_state=VerificationState.VERIFIED,
        )

    def _extract_context_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [item for item in data["items"] if isinstance(item, dict)]
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []

    def _map_context_items(
        self,
        items: list[dict[str, Any]],
        *,
        media: MusicMediaInfo,
        endpoint_label: str,
        note: str,
        query_query: str,
        query_type: str,
        verification_state: VerificationState = VerificationState.VERIFIED,
    ) -> list[HostSearchCandidate]:
        candidates: list[HostSearchCandidate] = []
        seen: set[str] = set()

        for index, item in enumerate(items, start=1):
            context = item if isinstance(item, dict) else {}
            torrent = context.get("torrent_info") if isinstance(context.get("torrent_info"), dict) else context
            title = str(torrent.get("title") or context.get("title") or f"moviepilot-candidate-{index}")
            page_url = str(torrent.get("page_url") or torrent.get("enclosure") or "")
            dedupe_key = page_url or f"{torrent.get('site_name')}::{title}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            labels = [str(label) for label in (torrent.get("labels") or []) if label]
            resolution = AdapterResolution(
                adapter_key="real_host_search",
                adapter_mode=AdapterMode.HOST,
                selection_mode=AdapterSelectionMode.PREFER_HOST,
                capability_source=f"moviepilot.runtime.{endpoint_label}",
                verification_state=verification_state,
                integration_point=f"RealHostSearchAdapter.{endpoint_label}",
                host_integration_enabled=self.settings.host_integration_enabled,
            )
            raw_payload = {
                "host_context": context,
                "query_query": query_query,
                "query_type": query_type,
                "endpoint": endpoint_label,
                "page_url": page_url or None,
                "host_media_reference": self._extract_media_reference(context),
                "adapter_resolution": resolution.model_dump(mode="json"),
            }

            candidates.append(
                HostSearchCandidate(
                    site_id=str(torrent.get("site") or torrent.get("site_id") or f"site-{index}"),
                    site_name=str(torrent.get("site_name") or context.get("site_name") or "MoviePilot Site"),
                    title=title,
                    normalized_title=normalize_title(title),
                    size_bytes=self._to_int(torrent.get("size", torrent.get("size_bytes", 0))),
                    seeders=self._to_int(torrent.get("seeders", 0)),
                    peers=self._to_int(torrent.get("peers", torrent.get("leechers", 0))),
                    format_tag=self._extract_format(torrent, title, labels),
                    bitrate_kbps=self._extract_bitrate(torrent, title),
                    source_tags=self._build_source_tags(labels, torrent),
                    mock=False,
                    note=note,
                    adapter_resolution=resolution,
                    raw_payload=raw_payload,
                )
            )

        return candidates

    def _extract_media_reference(self, context: dict[str, Any]) -> dict[str, Any]:
        media = context.get("media_info") if isinstance(context.get("media_info"), dict) else {}
        return {
            "tmdbid": media.get("tmdb_id") or media.get("tmdbid"),
            "doubanid": media.get("douban_id") or media.get("doubanid"),
            "title": media.get("title") or media.get("original_title"),
            "year": media.get("year"),
        }

    def _resolve_media_id(self, query_build: QueryBuildResult) -> str | None:
        external_refs = query_build.query_context.external_refs
        for key in ("moviepilot_mediaid", "mediaid"):
            value = external_refs.get(key)
            if value:
                return value
        if external_refs.get("moviepilot_tmdb_id"):
            return f"tmdb:{external_refs['moviepilot_tmdb_id']}"
        if external_refs.get("moviepilot_douban_id"):
            return f"douban:{external_refs['moviepilot_douban_id']}"
        if external_refs.get("moviepilot_bangumi_id"):
            return f"bangumi:{external_refs['moviepilot_bangumi_id']}"
        return None

    def _iter_positive_queries(self, query_build: QueryBuildResult) -> list[Any]:
        queries: list[Any] = []
        seen: set[str] = set()
        for clause in query_build.ordered_queries:
            if clause.query_type == "negative":
                continue
            normalized = normalize_title(clause.query)
            if normalized in seen:
                continue
            seen.add(normalized)
            queries.append(clause)
            if len(queries) >= 4:
                break
        return queries

    def _is_empty_search_response(self, payload: dict[str, Any]) -> bool:
        message = str(payload.get("message") or "")
        return "未搜索到任何资源" in message or message == ""

    def _extract_format(self, payload: dict[str, Any], title: str, labels: list[str]) -> str | None:
        for value in (payload.get("audio_profile"), payload.get("format"), payload.get("format_tag")):
            if value:
                return str(value).lower()
        title_lower = title.lower()
        for marker in ("flac", "ape", "wav", "aac", "mp3", "alac", "dsd"):
            if marker in title_lower:
                return marker
        for label in labels:
            lowered = label.lower()
            for marker in ("flac", "ape", "wav", "aac", "mp3", "alac", "dsd"):
                if marker in lowered:
                    return marker
        return None

    def _extract_bitrate(self, payload: dict[str, Any], title: str) -> int | None:
        for value in (payload.get("bitrate_kbps"), payload.get("bitrate")):
            if value not in (None, ""):
                return self._to_int(value)
        match = re.search(r"(?P<bitrate>\d{3,4})\s?(?:kbps|k)", title.lower())
        if match:
            return self._to_int(match.group("bitrate"))
        return None

    def _build_source_tags(self, labels: list[str], payload: dict[str, Any]) -> list[str]:
        tags = list(labels)
        for key in ("volume_factor", "date_elapsed", "site_name"):
            value = payload.get(key)
            if value:
                tags.append(str(value))
        return tags

    def _to_int(self, value: Any) -> int:
        if value in (None, ""):
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
