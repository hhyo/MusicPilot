"""Scenario input helpers for the unified music media chain."""

from __future__ import annotations

from fastapi import HTTPException

from ..schemas.music_media import MusicMediaInfo, MusicMediaInput, MusicMediaSourceKind
from ..schemas.orchestration import ChartEntryInfo, ChartInfo
from ..schemas.shared import EntityType


class MusicMediaInputHelper:
    """Normalizes upstream payloads into the shared input model."""

    def from_input(self, payload: MusicMediaInput) -> MusicMediaInput:
        return payload

    def from_discovery_entry(self, chart: ChartInfo, entry: ChartEntryInfo) -> MusicMediaInput:
        payload = dict(entry.target_payload or {})
        artist_name = self._pick_artist_name(entry, payload)
        return MusicMediaInput(
            entity_hint=entry.item_type,
            source_kind=MusicMediaSourceKind.DISCOVERY,
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
        source_kind: str | MusicMediaSourceKind,
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

    def from_provider_ref(
        self,
        *,
        entity_type: EntityType,
        provider: str,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        refs: dict[str, str] = {}
        if provider == "musicbrainz":
            key = self._musicbrainz_ref_key(entity_type)
            if key is not None:
                refs[key] = provider_id
        else:
            refs["provider"] = provider
            refs["provider_id"] = provider_id

        return MusicMediaInput(
            entity_hint=entity_type,
            source_kind=source_kind,
            external_refs=refs,
            source_context=source_context or {},
            raw_context=raw_context or {},
        )

    def from_target_payload_ref(
        self,
        *,
        entity_type: EntityType,
        target_id: str,
        target_payload: dict | None,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        payload = target_payload or {}
        provider_ref = payload.get("provider_ref")
        if isinstance(provider_ref, dict):
            provider = str(provider_ref.get("provider") or "").strip()
            provider_id = str(provider_ref.get("provider_id") or "").strip()
            if provider and provider_id:
                return self.from_provider_ref(
                    entity_type=entity_type,
                    provider=provider,
                    provider_id=provider_id,
                    source_kind=source_kind,
                    source_context=source_context,
                    raw_context=raw_context,
                )

        resolved_target_id = str(payload.get("target_id") or target_id).strip()
        provider = str(payload.get("provider") or "").strip()
        provider_id = str(payload.get("provider_id") or "").strip()
        if provider and provider_id:
            return self.from_provider_ref(
                entity_type=entity_type,
                provider=provider,
                provider_id=provider_id,
                source_kind=source_kind,
                source_context=source_context,
                raw_context=raw_context,
            )
        if provider:
            return self.from_provider_ref(
                entity_type=entity_type,
                provider=provider,
                provider_id=resolved_target_id,
                source_kind=source_kind,
                source_context=source_context,
                raw_context=raw_context,
            )

        direct_refs = self._direct_external_refs(entity_type=entity_type, payload=payload, target_id=resolved_target_id)
        title = self._coerce_text(payload.get("title"))
        subtitle = self._coerce_text(payload.get("subtitle"))
        artist_names = self._coerce_text_list(payload.get("artist_names"), payload.get("artist_name"))
        album_title = self._coerce_text(payload.get("album_title"))
        album_artist_names = self._coerce_text_list(payload.get("album_artist_names"))
        release_date = self._coerce_text(payload.get("published_at") or payload.get("release_date"))

        if direct_refs or self._has_structured_music_clues(
            title=title,
            subtitle=subtitle,
            artist_names=artist_names,
            album_title=album_title,
            album_artist_names=album_artist_names,
            release_date=release_date,
        ):
            return MusicMediaInput(
                entity_hint=entity_type,
                source_kind=source_kind,
                title=title,
                subtitle=subtitle,
                artist_names=artist_names,
                album_title=album_title,
                album_artist_names=album_artist_names,
                release_date=release_date,
                external_refs=direct_refs,
                source_context=source_context or {},
                raw_context=raw_context or {},
            )

        raise HTTPException(
            status_code=400,
            detail="Music media input requires a provider ref, structured music clues, or explicit external refs.",
        )

    @classmethod
    def _direct_external_refs(cls, *, entity_type: EntityType, payload: dict[str, object], target_id: str) -> dict[str, str]:
        refs: dict[str, str] = {}
        key = cls._musicbrainz_ref_key(entity_type)
        if key and target_id:
            refs[key] = target_id
        for ref_key in (
            "musicbrainz_artist_id",
            "musicbrainz_release_group_id",
            "musicbrainz_recording_id",
            "isrc",
            "upc",
            "source_id",
            "source_url",
        ):
            value = payload.get(ref_key)
            if isinstance(value, str) and value.strip():
                refs[ref_key] = value.strip()
        return refs

    @staticmethod
    def _coerce_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _coerce_text_list(cls, *values: object) -> list[str]:
        items: list[str] = []
        for value in values:
            if value is None:
                continue
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    text = cls._coerce_text(item)
                    if text:
                        items.append(text)
                continue
            text = cls._coerce_text(value)
            if text:
                items.append(text)
        deduped: list[str] = []
        seen: set[str] = set()
        for item in items:
            if item in seen:
                continue
            deduped.append(item)
            seen.add(item)
        return deduped

    @staticmethod
    def _has_structured_music_clues(
        *,
        title: str | None,
        subtitle: str | None,
        artist_names: list[str],
        album_title: str | None,
        album_artist_names: list[str],
        release_date: str | None,
    ) -> bool:
        return any((title, subtitle, artist_names, album_title, album_artist_names, release_date))

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
    def _music_media_external_refs(cls, payload: MusicMediaInfo) -> dict[str, str]:
        refs = dict(payload.external_refs)
        key = cls._musicbrainz_ref_key(payload.entity_type)
        if key and payload.provider == "musicbrainz" and payload.provider_id:
            refs.setdefault(key, payload.provider_id)
        else:
            refs.setdefault("provider", payload.provider)
            refs.setdefault("provider_id", payload.provider_id)
        return refs

    def _discovery_external_refs(self, entry: ChartEntryInfo, payload: dict[str, object]) -> dict[str, str]:
        refs: dict[str, str] = {}
        direct_key = self._musicbrainz_ref_key(entry.item_type)
        source_id = self._coerce_text(payload.get("source_id")) or self._coerce_text(payload.get("provider_origin_id"))
        source_url = self._coerce_text(payload.get("source_url")) or self._coerce_text(payload.get("provider_origin_url"))
        provider_ref = payload.get("provider_ref")
        if isinstance(provider_ref, dict):
            provider = self._coerce_text(provider_ref.get("provider"))
            provider_id = self._coerce_text(provider_ref.get("provider_id"))
            if provider and provider_id:
                refs["provider"] = provider
                refs["provider_id"] = provider_id
                if direct_key and provider == "musicbrainz":
                    refs.setdefault(direct_key, provider_id)
        if direct_key:
            for ref_key in (
                "musicbrainz_artist_id",
                "musicbrainz_release_group_id",
                "musicbrainz_recording_id",
            ):
                value = self._coerce_text(payload.get(ref_key))
                if value:
                    refs[ref_key] = value
            if (
                direct_key not in refs
                and entry.target_id
                and (entry.provider == "musicbrainz" or entry.chart_source == "listenbrainz")
            ):
                refs[direct_key] = entry.target_id
        if not refs and entry.provider and entry.target_id:
            refs["provider"] = entry.provider
            refs["provider_id"] = entry.target_id
        for ref_key in ("isrc", "upc"):
            value = self._coerce_text(payload.get(ref_key))
            if value:
                refs[ref_key] = value
        if source_id:
            refs["source_id"] = source_id
        if source_url:
            refs["source_url"] = source_url
        return refs

    def _pick_artist_name(self, entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        artist_names = self._coerce_text_list(payload.get("artist_name_candidates"), payload.get("artist_names"), payload.get("artist_name"))
        if artist_names:
            return artist_names[0]
        return self._coerce_text(entry.subtitle)

    def _pick_album_title(self, entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        album_titles = self._coerce_text_list(payload.get("album_title_candidates"), payload.get("album_title"))
        if album_titles:
            return album_titles[0]
        if entry.item_type == EntityType.ALBUM:
            return entry.target_name
        return None

    def _pick_title(self, entry: ChartEntryInfo, payload: dict[str, object]) -> str | None:
        title_candidates = self._coerce_text_list(payload.get("title_candidates"), payload.get("title"))
        if title_candidates:
            return title_candidates[0]
        return entry.target_name
