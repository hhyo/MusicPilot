"""Discovery presentation assembly for product-facing chart views."""

from __future__ import annotations

from collections import defaultdict

from ..schemas.music_media import MusicMediaInput, MusicMetaBase
from ..schemas.mvp import EntityType
from ..schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartInfo,
    DiscoveryEntryGroup,
    DiscoveryEntryView,
)
from .music_media_input_adapter import MusicMediaInputAdapter
from .music_meta_base_builder import MusicMetaBaseBuilder


class DiscoveryAssembler:
    def __init__(self) -> None:
        self.input_adapter = MusicMediaInputAdapter()
        self.base_builder = MusicMetaBaseBuilder()

    def build_chart_info(self, chart: ChartInfo) -> ChartInfo:
        chart.summary = self._build_chart_summary(chart)
        chart.chart_group = self._chart_group(chart.chart_type)
        chart.chart_scope = chart.category or "discovery"
        chart.freshness_label = self._build_freshness_label(chart)
        chart.supports_subscription = True
        return chart

    def build_detail(self, detail: ChartDetailData) -> ChartDetailData:
        detail.chart = self.build_chart_info(detail.chart)
        entry_views = [self._build_entry_view(detail.chart, item) for item in detail.items]
        detail.hero_entry = entry_views[0] if entry_views else None
        detail.entry_groups = self._group_entries(entry_views)
        ready_count = sum(1 for item in entry_views if item.recognition_state in {"direct", "ready"})
        detail.summary_stats = {
            "items": len(entry_views),
            "ready": ready_count,
            "group_count": len(detail.entry_groups),
        }
        detail.recognition_summary = {
            "ready": ready_count,
            "not_ready": len(entry_views) - ready_count,
        }
        return detail

    def _build_entry_view(self, chart: ChartInfo, entry: ChartEntryInfo) -> DiscoveryEntryView:
        media_input = self.input_adapter.from_discovery_entry(chart, entry)
        meta_base = self.base_builder.build(media_input)
        recognition_state, recognition_note = self._resolve_recognition_state(entry=entry, meta_base=meta_base)
        return DiscoveryEntryView(
            entry=entry,
            media_input=media_input,
            meta_base=meta_base,
            entry_summary=self._entry_summary(entry),
            badges=self._build_badges(chart, entry),
            highlight_reason=self._highlight_reason(chart, entry),
            recognition_state=recognition_state,
            recognition_note=recognition_note,
        )

    def _resolve_recognition_state(
        self,
        *,
        entry: ChartEntryInfo,
        meta_base: MusicMetaBase,
    ) -> tuple[str, str | None]:
        direct_ref_keys = {
            EntityType.ARTIST: "musicbrainz_artist_id",
            EntityType.ALBUM: "musicbrainz_release_group_id",
            EntityType.TRACK: "musicbrainz_recording_id",
        }
        direct_key = direct_ref_keys[entry.item_type]
        if meta_base.external_refs.get(direct_key):
            return "direct", None

        if entry.item_type == EntityType.TRACK:
            if meta_base.canonical_title and meta_base.canonical_artist_names:
                return "ready", None
            return "insufficient", "Missing music meta base fields: requires canonical_title + canonical_artist_names."

        if entry.item_type == EntityType.ALBUM:
            if meta_base.canonical_album_title and meta_base.canonical_artist_names:
                return "ready", None
            return (
                "insufficient",
                "Missing music meta base fields: requires canonical_album_title + canonical_artist_names.",
            )

        if meta_base.canonical_artist_names:
            return "ready", None
        return "insufficient", "Missing music meta base fields: requires canonical_artist_names."

    def _build_badges(self, chart: ChartInfo, entry: ChartEntryInfo) -> list[str]:
        badges: list[str] = []
        if chart.category:
            badges.append(chart.category)
        if chart.refresh_hint:
            badges.append(chart.refresh_hint)
        if entry.rank <= 3:
            badges.append(f"top-{entry.rank}")
        badges.append(self._chart_group(entry.item_type))
        return badges

    def _group_entries(self, entry_views: list[DiscoveryEntryView]) -> list[DiscoveryEntryGroup]:
        grouped: dict[str, list[DiscoveryEntryView]] = defaultdict(list)
        for entry in entry_views:
            grouped[self._chart_group(entry.entry.item_type)].append(entry)
        ordered_groups: list[DiscoveryEntryGroup] = []
        labels = {"artists": "Artists", "albums": "Albums", "tracks": "Tracks"}
        for key in ("artists", "albums", "tracks"):
            items = grouped.get(key)
            if items:
                ordered_groups.append(DiscoveryEntryGroup(group_key=key, group_label=labels[key], items=items))
        return ordered_groups

    def _build_chart_summary(self, chart: ChartInfo) -> str:
        if chart.chart_type == EntityType.ARTIST:
            return "Browse high-signal artists from the current chart source."
        if chart.chart_type == EntityType.ALBUM:
            return "Browse notable releases ready for deeper metadata inspection."
        return "Browse standout tracks that can later flow into metadata and acquisition."

    def _build_freshness_label(self, chart: ChartInfo) -> str:
        if chart.refresh_hint:
            return chart.refresh_hint.replace("-", " ")
        return "live"

    def _entry_summary(self, entry: ChartEntryInfo) -> str:
        if entry.subtitle:
            return f"{entry.target_name} · {entry.subtitle}"
        return entry.target_name

    def _highlight_reason(self, chart: ChartInfo, entry: ChartEntryInfo) -> str:
        if entry.rank == 1:
            return f"Top {self._chart_group(chart.chart_type)[:-1]} in this chart."
        return f"Rank #{entry.rank} in {chart.chart_name}."

    def _chart_group(self, chart_type: EntityType) -> str:
        if chart_type == EntityType.ARTIST:
            return "artists"
        if chart_type == EntityType.ALBUM:
            return "albums"
        return "tracks"
