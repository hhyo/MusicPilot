"""Discovery presentation assembly for product-facing chart views."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..schemas.mvp import EntityType
from ..schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartInfo,
    DiscoveryEntryGroup,
    DiscoveryEntryView,
    DiscoverySourceContext,
    DiscoveryTarget,
)


class DiscoveryAssembler:
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
        ready_count = sum(1 for item in entry_views if item.target.conversion_ready)
        detail.summary_stats = {
            "items": len(entry_views),
            "ready": ready_count,
            "group_count": len(detail.entry_groups),
        }
        detail.conversion_summary = {
            "ready": ready_count,
            "not_ready": len(entry_views) - ready_count,
        }
        return detail

    def _build_entry_view(self, chart: ChartInfo, entry: ChartEntryInfo) -> DiscoveryEntryView:
        target = self._build_target(chart, entry)
        return DiscoveryEntryView(
            entry=entry,
            target=target,
            entry_summary=self._entry_summary(entry, target),
            badges=target.discovery_badges,
            highlight_reason=self._highlight_reason(chart, entry),
        )

    def _build_target(self, chart: ChartInfo, entry: ChartEntryInfo) -> DiscoveryTarget:
        if self._is_rss_entry(entry):
            return self._build_rss_lookup_target(chart, entry)

        provider_id = (entry.target_id or "").strip()
        conversion_ready = bool(provider_id)
        return DiscoveryTarget(
            target_kind=entry.item_type,
            provider="musicbrainz",
            provider_id=provider_id,
            display_title=entry.target_name,
            display_subtitle=entry.subtitle,
            source_context=DiscoverySourceContext(
                chart_source=entry.chart_source,
                chart_id=entry.chart_id,
                chart_name=entry.chart_name,
                rank=entry.rank,
                chart_type=chart.chart_type,
            ),
            conversion_ready=conversion_ready,
            conversion_note=None if conversion_ready else "Missing provider target id.",
            resolution_mode="direct_id",
            resolution_hints={},
            discovery_badges=self._build_badges(chart, entry),
        )

    def _build_rss_lookup_target(self, chart: ChartInfo, entry: ChartEntryInfo) -> DiscoveryTarget:
        hints = self._build_rss_resolution_hints(entry)
        conversion_ready, conversion_note = self._resolve_rss_lookup_readiness(entry=entry, hints=hints)
        return DiscoveryTarget(
            target_kind=entry.item_type,
            provider="musicbrainz",
            provider_id="",
            display_title=entry.target_name,
            display_subtitle=entry.subtitle,
            source_context=DiscoverySourceContext(
                chart_source=entry.chart_source,
                chart_id=entry.chart_id,
                chart_name=entry.chart_name,
                rank=entry.rank,
                chart_type=chart.chart_type,
            ),
            conversion_ready=conversion_ready,
            conversion_note=conversion_note,
            resolution_mode="search_lookup",
            resolution_hints=hints,
            discovery_badges=self._build_badges(chart, entry),
        )

    @staticmethod
    def _is_rss_entry(entry: ChartEntryInfo) -> bool:
        return entry.chart_source == "rss_feed" or entry.source_type.startswith("rss_feed/")

    def _build_rss_resolution_hints(self, entry: ChartEntryInfo) -> dict[str, Any]:
        payload = dict(entry.target_payload or {})
        hints: dict[str, Any] = {
            "family": payload.get("family"),
            "provider_origin_url": payload.get("provider_origin_url"),
            "provider_origin_id": payload.get("provider_origin_id"),
        }

        if entry.item_type == EntityType.TRACK:
            hints["title"] = payload.get("title")
            hints["artist_name"] = payload.get("artist_name")
            hints["album_title"] = payload.get("album_title")
        elif entry.item_type == EntityType.ALBUM:
            hints["album_title"] = payload.get("album_title")
            hints["artist_name"] = payload.get("artist_name")
        elif entry.item_type == EntityType.ARTIST:
            hints["artist_name"] = payload.get("artist_name")

        for key in (
            "cover_url",
            "published_at",
            "raw_context",
            "title_candidates",
            "artist_name_candidates",
            "album_title_candidates",
        ):
            if key in payload:
                hints[key] = payload.get(key)
        return {key: value for key, value in hints.items() if value is not None}

    def _resolve_rss_lookup_readiness(self, *, entry: ChartEntryInfo, hints: dict[str, Any]) -> tuple[bool, str | None]:
        if entry.item_type == EntityType.TRACK:
            required = ("title", "artist_name")
            label = "title + artist_name"
        elif entry.item_type == EntityType.ALBUM:
            required = ("album_title", "artist_name")
            label = "album_title + artist_name"
        else:
            required = ("artist_name",)
            label = "artist_name"

        missing = [key for key in required if not str(hints.get(key) or "").strip()]
        if not missing:
            return True, None
        return False, f"Missing RSS lookup hints: requires {label}."

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

    def _entry_summary(self, entry: ChartEntryInfo, target: DiscoveryTarget) -> str:
        if target.display_subtitle:
            return f"{target.display_title} · {target.display_subtitle}"
        return target.display_title

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
