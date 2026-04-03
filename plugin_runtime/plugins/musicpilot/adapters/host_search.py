"""Host PT search adapter boundary for Phase 3."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .host_http import HostHttpClient, HostTransportError
from ..core.config import Settings
from ..schemas.acquisition import HostSearchCandidate, QueryBuildResult
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterStrategy, VerificationState
from ..schemas.metadata import MetadataDetail
from ..schemas.mvp import EntityType


def normalize_title(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())


class HostSearchAdapter(ABC):
    @abstractmethod
    def search(self, *, query_build: QueryBuildResult, detail: MetadataDetail) -> list[HostSearchCandidate]:
        """Search host PT sites with the built query payload."""


class MockHostSearchAdapter(HostSearchAdapter):
    """Stable mock PT search adapter for the Phase 3 minimum loop."""

    def search(self, *, query_build: QueryBuildResult, detail: MetadataDetail) -> list[HostSearchCandidate]:
        if detail.entity_type == EntityType.ALBUM:
            exact_title = f"{detail.artist_name} - {detail.title} ({detail.year}) [FLAC] [24bit]"
            manual_title = f"{detail.artist_name} - {detail.title} Deluxe Edition [AAC 320]"
            reject_title = f"{detail.artist_name} Karaoke Tribute Collection [MP3 128]"
        elif detail.entity_type == EntityType.TRACK:
            exact_title = f"{detail.artist_name} - {detail.title} [{detail.album_title}] [FLAC]"
            manual_title = f"{detail.artist_name} - {detail.title} Acoustic Session [AAC 320]"
            reject_title = f"{detail.artist_name} - {detail.title} Instrumental Cover [MP3 128]"
        else:
            exact_title = f"{detail.title} Discography Collection [FLAC]"
            manual_title = f"{detail.title} Anthology Selection [AAC 320]"
            reject_title = f"{detail.title} Tribute Karaoke Pack [MP3 128]"

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
                source_tags=["lossless", "official", detail.entity_type.value],
                note="当前候选来自 mock host search adapter，不代表已接入真实 PT 站点。",
                adapter_resolution=AdapterResolution(
                    adapter_key="mock_host_search",
                    adapter_mode=AdapterMode.MOCK,
                    strategy=AdapterStrategy.MOCK,
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
                    strategy=AdapterStrategy.MOCK,
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
                    strategy=AdapterStrategy.MOCK,
                    capability_source="mock.adapter",
                    verification_state=VerificationState.PLACEHOLDER,
                    integration_point="MockHostSearchAdapter.search",
                    host_integration_enabled=False,
                ),
                raw_payload={"variant": "reject_case"},
            ),
        ]


class RealHostSearchAdapter(HostSearchAdapter):
    """Host-backed PT search skeleton for Phase 5.

    The request/response mapping is intentionally generic because the final host contract
    is still unverified. This adapter should only be selected by the resolver when host
    integration is enabled and the search capability is considered available.
    """

    def __init__(self, *, settings: Settings, client: HostHttpClient):
        self.settings = settings
        self.client = client

    def search(self, *, query_build: QueryBuildResult, detail: MetadataDetail) -> list[HostSearchCandidate]:
        payload = {
            "queries": [item.query for item in query_build.ordered_queries],
            "query_context": query_build.query_context.model_dump(mode="json"),
            "preferences": query_build.preferences.model_dump(mode="json"),
            "query_source_type": query_build.query_source_type.value,
            "query_source_id": query_build.query_source_id,
            "detail": detail.model_dump(mode="json"),
        }
        response = self.client.post_json(self.settings.host_search_path, payload)
        items = self._extract_items(response)

        candidates: list[HostSearchCandidate] = []
        for index, item in enumerate(items, start=1):
            title = str(item.get("raw_title") or item.get("title") or f"host-candidate-{index}")
            size_value = item.get("size_bytes", item.get("size", 0))
            size_bytes = self._to_int(size_value)
            seeders = self._to_int(item.get("seeders", 0))
            peers = self._to_int(item.get("peers", item.get("leechers", 0)))
            bitrate = item.get("bitrate_kbps", item.get("bitrate"))
            source_tags = item.get("source_tags") or item.get("tags") or []

            candidates.append(
                HostSearchCandidate(
                    site_id=str(item.get("site_id") or item.get("site") or f"host-site-{index}"),
                    site_name=str(item.get("site_name") or item.get("site") or "Host Site"),
                    title=title,
                    normalized_title=normalize_title(str(item.get("normalized_title") or title)),
                    size_bytes=size_bytes,
                    seeders=seeders,
                    peers=peers,
                    format_tag=self._extract_format(item),
                    bitrate_kbps=self._to_int(bitrate) if bitrate is not None else None,
                    source_tags=[str(tag) for tag in source_tags],
                    mock=False,
                    note=(
                        "当前候选来自 configured host search endpoint。字段映射已落为可联调骨架，但 MoviePilot "
                        "真实返回结构仍需联调确认。"
                    ),
                    adapter_resolution=AdapterResolution(
                        adapter_key="real_host_search",
                        adapter_mode=AdapterMode.HOST,
                        strategy=AdapterStrategy.PREFER_HOST,
                        capability_source="host.endpoint",
                        verification_state=VerificationState(self.settings.host_verification_state),
                        integration_point="RealHostSearchAdapter.search",
                        host_integration_enabled=self.settings.host_integration_enabled,
                    ),
                    raw_payload=item,
                )
            )

        if not candidates and self.settings.host_strict_empty_as_error:
            raise HostTransportError(
                "Configured host search endpoint returned no parsable candidates.",
                reason_code="host_search_empty",
            )
        return candidates

    def _extract_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data", payload)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [item for item in data["items"] if isinstance(item, dict)]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return []

    def _extract_format(self, payload: dict[str, Any]) -> str | None:
        value = payload.get("format_tag") or payload.get("audio_profile") or payload.get("format")
        return str(value).lower() if value else None

    def _to_int(self, value: Any) -> int:
        if value in (None, ""):
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
