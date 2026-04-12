"""Build normalized intermediate metadata for the music media chain."""

from __future__ import annotations

from ..schemas.music_media import MusicMediaInput, MusicMetaBase
from ..schemas.shared import EntityType


class MusicMetaBaseBuilder:
    """Converts raw music clues into a normalized intermediate base."""

    def build(self, payload: MusicMediaInput) -> MusicMetaBase:
        entity_type = payload.entity_hint or EntityType.TRACK
        raw_context = payload.raw_context if isinstance(payload.raw_context, dict) else {}

        def _collect_aliases(key: str) -> list[str]:
            value = raw_context.get(key, [])
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if value:
                return [str(value).strip()]
            return []

        return MusicMetaBase(
            entity_type=entity_type,
            canonical_title=payload.title
            or payload.album_title
            or (payload.artist_names[0] if payload.artist_names else None),
            canonical_artist_names=list(payload.artist_names),
            canonical_album_title=payload.album_title,
            canonical_album_artist_names=list(payload.album_artist_names),
            canonical_release_date=payload.release_date,
            canonical_year=payload.year,
            track_number=payload.track_number,
            disc_number=payload.disc_number,
            alias_titles=_collect_aliases("title_candidates"),
            alias_artist_names=_collect_aliases("artist_name_candidates"),
            alias_album_titles=_collect_aliases("album_title_candidates"),
            external_refs=dict(payload.external_refs),
            source_refs={
                key: value
                for key, value in payload.external_refs.items()
                if key.startswith("source_")
            },
            evidence=[{"field": "source_kind", "value": payload.source_kind, "source": "input"}],
        )
