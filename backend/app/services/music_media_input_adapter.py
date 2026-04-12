"""Scenario input adapters for the unified music media chain."""

from __future__ import annotations

from ..schemas.metadata import MetadataDetail
from ..schemas.music_media import MusicMediaInfo, MusicMediaInput
from ..schemas.mvp import EntityType


class MusicMediaInputAdapter:
    """Normalizes upstream payloads into the shared input model."""

    def from_input(self, payload: MusicMediaInput) -> MusicMediaInput:
        return payload

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
