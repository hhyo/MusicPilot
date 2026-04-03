"""Host PT search adapter boundary for Phase 3."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas.acquisition import HostSearchCandidate, QueryBuildResult
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
                raw_payload={"variant": "reject_case"},
            ),
        ]
