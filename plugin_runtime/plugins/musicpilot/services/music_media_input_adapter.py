"""Scenario input adapters for the unified music media chain."""

from __future__ import annotations

from ..schemas.metadata import MetadataDetail
from ..schemas.music_media import MusicMediaInfo, MusicMediaInput
from ..schemas.mvp import EntityType
from ..schemas.orchestration import ChartEntryInfo, ChartInfo


class MusicMediaInputAdapter:
    """Normalizes upstream payloads into the shared input model."""

    def from_input(self, payload: MusicMediaInput) -> MusicMediaInput:
        return payload

    def from_discovery_entry(self, chart: ChartInfo, entry: ChartEntryInfo) -> MusicMediaInput:
        payload = dict(entry.target_payload or {})
        artist_name = self._pick_artist_name(entry, payload)
        return MusicMediaInput(
            entity_hint=entry.item_type,
            source_kind="discovery",
            title=self._pick_title(entry, payload),
            subtitle=entry.subtitle,
            artist_names=[artist_name] if artist_name else [],
            album_title=self._pick_album_title(entry, payload),
            album_artist_names=[],
            release_date=payload.get("published_at"),
            external_refs=self._discovery_external_refs(entry, payload),
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

    def from_music_media_info(
        self,
        payload: MusicMediaInfo,
        *,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return MusicMediaInput(
            entity_hint=payload.entity_type,
            source_kind=source_kind,
            title=payload.title,
            artist_names=list(payload.artist_names),
            album_title=payload.album_title,
            album_artist_names=list(payload.album_artist_names),
            release_date=payload.release_date,
            year=payload.year,
            track_number=payload.track_number,
            disc_number=payload.disc_number,
            external_refs=self._music_media_external_refs(payload),
            source_context=source_context or {},
            raw_context=raw_context or {},
        )

    def from_metadata_detail(
        self,
        payload: MetadataDetail,
        *,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return MusicMediaInput(
            entity_hint=payload.entity_type,
            source_kind=source_kind,
            title=payload.track_title or payload.title,
            artist_names=[payload.artist_name] if payload.artist_name else [],
            album_title=payload.album_title,
            album_artist_names=[],
            year=payload.year,
            track_number=None,
            disc_number=None,
            external_refs=self._metadata_external_refs(payload),
            source_context=source_context or {},
            raw_context=raw_context or {},
        )

    @staticmethod
    def _music_media_external_refs(payload: MusicMediaInfo) -> dict[str, str]:
        refs = dict(payload.external_refs)
        if payload.provider == "musicbrainz" and payload.provider_id:
            key = MusicMediaInputAdapter._musicbrainz_ref_key(payload.entity_type)
            if key is not None:
                refs.setdefault(key, payload.provider_id)
        return {key: str(value) for key, value in refs.items() if value}

    @staticmethod
    def _metadata_external_refs(payload: MetadataDetail) -> dict[str, str]:
        refs = dict(payload.external_ids)
        if payload.provider == "musicbrainz" and payload.id:
            key = MusicMediaInputAdapter._musicbrainz_ref_key(payload.entity_type)
            if key is not None:
                refs.setdefault(key, payload.id)
        return {key: str(value) for key, value in refs.items() if value}

    @staticmethod
    def _musicbrainz_ref_key(entity_type: EntityType) -> str | None:
        if entity_type == EntityType.ARTIST:
            return "musicbrainz_artist_id"
        if entity_type == EntityType.ALBUM:
            return "musicbrainz_release_group_id"
        if entity_type == EntityType.TRACK:
            return "musicbrainz_recording_id"
        return None

    @classmethod
    def _discovery_external_refs(cls, entry: ChartEntryInfo, payload: dict[str, object]) -> dict[str, str]:
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

    @staticmethod
    def _pick_title(entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        if entry.item_type == EntityType.ARTIST:
            return None
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return entry.target_name or None

    @staticmethod
    def _pick_artist_name(entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        artist_name = payload.get("artist_name")
        if isinstance(artist_name, str) and artist_name.strip():
            return artist_name.strip()
        if entry.item_type == EntityType.ARTIST and entry.target_id:
            return entry.target_name or None
        return None

    @staticmethod
    def _pick_album_title(entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        album_title = payload.get("album_title")
        if isinstance(album_title, str) and album_title.strip():
            return album_title.strip()
        if entry.item_type == EntityType.ALBUM:
            return entry.target_name or None
        return None
