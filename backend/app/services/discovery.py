"""Discovery presentation assembly for product-facing chart views."""

from __future__ import annotations

from collections import defaultdict

from ..schemas.music_media import MusicMediaInput
from ..schemas.mvp import EntityType
from ..schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartInfo,
    DiscoveryEntryGroup,
    DiscoveryEntryView,
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
        ready_count = sum(1 for item in entry_views if item.conversion_state in {"direct", "ready"})
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
        media_input = self._build_media_input_payload(chart, entry)
        conversion_state, conversion_note = self._resolve_conversion_state(entry=entry, media_input=media_input)
        return DiscoveryEntryView(
            entry=entry,
            media_input=media_input,
            entry_summary=self._entry_summary(entry),
            badges=self._build_badges(chart, entry),
            highlight_reason=self._highlight_reason(chart, entry),
            conversion_state=conversion_state,
            conversion_note=conversion_note,
        )

    def _build_media_input_payload(self, chart: ChartInfo, entry: ChartEntryInfo) -> MusicMediaInput:
        payload = dict(entry.target_payload or {})
        artist_name = self._pick_artist_name(entry, payload)
        external_refs = self._build_external_refs(entry, payload)
        return MusicMediaInput(
            entity_hint=entry.item_type,
            source_kind="discovery",
            title=self._pick_title(entry, payload),
            subtitle=entry.subtitle,
            artist_names=[artist_name] if artist_name else [],
            album_title=self._pick_album_title(entry, payload),
            album_artist_names=[],
            release_date=payload.get("published_at"),
            external_refs=external_refs,
            source_context={
                "chart_id": entry.chart_id,
                "chart_source": entry.chart_source,
                "chart_name": entry.chart_name,
                "chart_type": chart.chart_type.value,
                "rank": entry.rank,
                "provider": entry.provider,
                "source_type": entry.source_type,
                "family": payload.get("family"),
            },
            raw_context=payload.get("raw_context") or payload,
        )

    def _build_external_refs(self, entry: ChartEntryInfo, payload: dict[str, object]) -> dict[str, str]:
        refs: dict[str, str] = {}
        target_id = (entry.target_id or "").strip()
        if entry.item_type == EntityType.ARTIST and target_id:
            refs["musicbrainz_artist_id"] = target_id
        elif entry.item_type == EntityType.ALBUM and target_id:
            refs["musicbrainz_release_group_id"] = target_id
        elif entry.item_type == EntityType.TRACK and target_id:
            refs["musicbrainz_recording_id"] = target_id

        for key in (
            "musicbrainz_artist_id",
            "musicbrainz_release_group_id",
            "musicbrainz_recording_id",
            "isrc",
            "upc",
        ):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                refs[key] = value.strip()

        origin_id = payload.get("provider_origin_id")
        origin_url = payload.get("provider_origin_url")
        if isinstance(origin_id, str) and origin_id.strip():
            refs["source_id"] = origin_id.strip()
        if isinstance(origin_url, str) and origin_url.strip():
            refs["source_url"] = origin_url.strip()
        return refs

    def _resolve_conversion_state(
        self,
        *,
        entry: ChartEntryInfo,
        media_input: MusicMediaInput,
    ) -> tuple[str, str | None]:
        direct_ref_keys = {
            EntityType.ARTIST: "musicbrainz_artist_id",
            EntityType.ALBUM: "musicbrainz_release_group_id",
            EntityType.TRACK: "musicbrainz_recording_id",
        }
        direct_key = direct_ref_keys[entry.item_type]
        if media_input.external_refs.get(direct_key):
            return "direct", None

        if entry.item_type == EntityType.TRACK:
            if media_input.title and media_input.artist_names:
                return "ready", None
            return "insufficient", "Missing media input fields: requires title + artist_names."

        if entry.item_type == EntityType.ALBUM:
            if media_input.album_title and media_input.artist_names:
                return "ready", None
            return "insufficient", "Missing media input fields: requires album_title + artist_names."

        if media_input.artist_names:
            return "ready", None
        return "insufficient", "Missing media input fields: requires artist_names."

    def _pick_title(self, entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        if entry.item_type == EntityType.ARTIST:
            return None
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return entry.target_name or None

    def _pick_artist_name(self, entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        artist_name = payload.get("artist_name")
        if isinstance(artist_name, str) and artist_name.strip():
            return artist_name.strip()
        if entry.item_type == EntityType.ARTIST and entry.target_id:
            return entry.target_name or None
        return None

    def _pick_album_title(self, entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        album_title = payload.get("album_title")
        if isinstance(album_title, str) and album_title.strip():
            return album_title.strip()
        if entry.item_type == EntityType.ALBUM:
            return entry.target_name or None
        return None

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
