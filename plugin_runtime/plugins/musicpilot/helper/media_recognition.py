"""Recognition stage helpers for the unified music media chain."""

from __future__ import annotations

import re

import httpx
from fastapi import HTTPException

from ..schemas.metadata import MetadataSearchRequest, MetadataSummary
from ..schemas.music_media import (
    MusicMediaInfo,
    MusicMediaMatchStrategy,
    MusicMetaBase,
    MusicRecognitionAssessment,
    MusicRecognitionState,
)
from ..schemas.shared import EntityType


class MusicMediaRecognizer:
    """Recognizes formal media objects from normalized music metadata."""

    def __init__(self, metadata_module, metadata_provider):
        self.metadata_module = metadata_module
        self.metadata_provider = metadata_provider

    def assess(self, base: MusicMetaBase) -> MusicRecognitionAssessment:
        if base.external_refs.get("provider") and base.external_refs.get("provider_id"):
            return MusicRecognitionAssessment(state=MusicRecognitionState.DIRECT)

        direct_ref_keys = {
            EntityType.ARTIST: "musicbrainz_artist_id",
            EntityType.ALBUM: "musicbrainz_release_group_id",
            EntityType.TRACK: "musicbrainz_recording_id",
        }
        direct_key = direct_ref_keys[base.entity_type]
        if base.external_refs.get(direct_key):
            return MusicRecognitionAssessment(state=MusicRecognitionState.DIRECT)

        if base.entity_type == EntityType.TRACK:
            if base.canonical_title and base.canonical_artist_names:
                return MusicRecognitionAssessment(state=MusicRecognitionState.READY)
            return MusicRecognitionAssessment(
                state=MusicRecognitionState.INSUFFICIENT,
                note="Missing music meta base fields: requires canonical_title + canonical_artist_names.",
            )

        if base.entity_type == EntityType.ALBUM:
            if base.canonical_album_title and base.canonical_artist_names:
                return MusicRecognitionAssessment(state=MusicRecognitionState.READY)
            return MusicRecognitionAssessment(
                state=MusicRecognitionState.INSUFFICIENT,
                note="Missing music meta base fields: requires canonical_album_title + canonical_artist_names.",
            )

        if base.canonical_artist_names:
            return MusicRecognitionAssessment(state=MusicRecognitionState.READY)
        return MusicRecognitionAssessment(
            state=MusicRecognitionState.INSUFFICIENT,
            note="Missing music meta base fields: requires canonical_artist_names.",
        )

    def recognize(self, base: MusicMetaBase) -> MusicMediaInfo:
        generic_provider = (base.external_refs.get("provider") or "").strip()
        generic_provider_id = (base.external_refs.get("provider_id") or "").strip()
        recording_id = base.external_refs.get("musicbrainz_recording_id")
        album_id = base.external_refs.get("musicbrainz_release_group_id")
        artist_id = base.external_refs.get("musicbrainz_artist_id")
        provider_id = generic_provider_id or recording_id or album_id or artist_id or ""
        provider = generic_provider or "musicbrainz"

        if provider_id:
            return MusicMediaInfo(
                entity_type=base.entity_type,
                provider=provider,
                provider_id=provider_id,
                title=base.canonical_title,
                artist_names=list(base.canonical_artist_names),
                album_title=base.canonical_album_title,
                album_artist_names=list(base.canonical_album_artist_names),
                release_date=base.canonical_release_date,
                year=base.canonical_year,
                track_number=base.track_number,
                disc_number=base.disc_number,
                external_refs=dict(base.external_refs),
                match_confidence=1.0,
                match_strategy=MusicMediaMatchStrategy.STRONG_REF,
                match_evidence=[{"field": "provider_id", "value": provider_id}],
                diagnostics=[],
            )

        return self._recognize_from_metadata_search(base)

    def _recognize_from_metadata_search(self, base: MusicMetaBase) -> MusicMediaInfo:
        query_keywords = self._build_search_keywords(base)
        if not query_keywords:
            raise HTTPException(status_code=400, detail="Insufficient music media input for metadata resolution.")

        saw_items = False
        winner: MetadataSummary | None = None
        winner_keyword: str | None = None
        for keyword in query_keywords:
            try:
                search_result = self.metadata_module.search(
                    MetadataSearchRequest(keyword=keyword, type=base.entity_type, page=1, page_size=10)
                )
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail="Metadata provider search request failed.") from exc

            if not search_result.items:
                continue

            saw_items = True
            winner = self._select_metadata_search_winner(base=base, items=search_result.items)
            if winner is not None:
                winner_keyword = keyword
                break

        if winner is None:
            if saw_items:
                raise HTTPException(status_code=404, detail="No metadata match satisfied music media input.")
            raise HTTPException(status_code=404, detail="No metadata match found for music media input.")

        return MusicMediaInfo(
            entity_type=base.entity_type,
            provider=winner.provider or self.metadata_provider.provider,
            provider_id=winner.id,
            title=winner.track_title or winner.title,
            artist_names=[winner.artist_name] if winner.artist_name else list(base.canonical_artist_names),
            album_title=winner.album_title,
            album_artist_names=list(base.canonical_album_artist_names),
            release_date=base.canonical_release_date,
            year=winner.year or base.canonical_year,
            track_number=base.track_number,
            disc_number=base.disc_number,
            external_refs=dict(base.external_refs),
            match_confidence=0.85,
            match_strategy=MusicMediaMatchStrategy.METADATA_SEARCH,
            match_evidence=[{"field": "keyword", "value": winner_keyword or ""}],
            diagnostics=[],
        )

    @classmethod
    def _build_search_keywords(cls, base: MusicMetaBase) -> list[str]:
        primary_artist = " & ".join(base.canonical_artist_names).strip()
        artists = cls._build_search_text_candidates(primary=primary_artist, extras=base.alias_artist_names, title_mode=False)
        titles = cls._build_search_text_candidates(primary=base.canonical_title, extras=base.alias_titles, title_mode=True)
        albums = cls._build_search_text_candidates(primary=base.canonical_album_title, extras=base.alias_album_titles, title_mode=False)

        if base.entity_type == EntityType.TRACK:
            candidates: list[list[str]] = []
            for artist in artists:
                for title in titles:
                    for album in albums[:2]:
                        if album:
                            candidates.append([artist, title, album])
                    candidates.append([artist, title])
            for title in titles:
                for artist in artists:
                    candidates.append([title, artist])
        elif base.entity_type == EntityType.ALBUM:
            candidates = []
            for artist in artists:
                for album in albums:
                    candidates.append([artist, album])
            for album in albums:
                for artist in artists:
                    candidates.append([album, artist])
                candidates.append([album])
        else:
            candidates = [[artist] for artist in artists]

        keywords: list[str] = []
        seen: set[str] = set()
        for parts in candidates:
            keyword = " ".join(part for part in parts if part).strip()
            if not keyword or keyword in seen:
                continue
            keywords.append(keyword)
            seen.add(keyword)
        return keywords

    @classmethod
    def _clean_search_text(cls, value: object) -> str:
        if value is None:
            return ""
        text = str(value).replace("\u00A0", " ").strip()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def _clean_search_title(cls, value: object) -> str:
        text = cls._clean_search_text(value)
        if not text:
            return ""
        previous = None
        while text != previous:
            previous = text
            text = re.sub(r"\s*[\(\[][^)\]]*\b(?:live|remaster(?:ed)?|version|edit|mono|stereo|instrumental|acoustic|karaoke|bonus track)\b[^)\]]*[\)\]]\s*$", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*[\(\[][^)\]]*\b(?:official\s+)?(?:video|audio|mv|lyrics?|lyric video|performance)\b[^)\]]*[\)\]]\s*$", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*[-:]\s*.*\b(?:live|remaster(?:ed)?|version|edit|mono|stereo|instrumental|acoustic|karaoke|bonus track)\b.*$", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*[-:]\s*.*\b(?:official\s+)?(?:video|audio|mv|lyrics?|lyric video|performance)\b.*$", "", text, flags=re.IGNORECASE)
        return cls._clean_search_text(text)

    @classmethod
    def _build_search_text_candidates(cls, *, primary: object, extras: object, title_mode: bool) -> list[str]:
        values: list[str] = []

        def append(raw: object) -> None:
            if raw is None:
                return
            if isinstance(raw, (list, tuple, set)):
                for item in raw:
                    append(item)
                return
            cleaned = cls._clean_search_title(raw) if title_mode else cls._clean_search_text(raw)
            if cleaned:
                values.append(cleaned)

        append(primary)
        append(extras)

        deduped: list[str] = []
        seen: set[str] = set()
        for value in values:
            key = cls._normalize_search_text(value)
            if not key or key in seen:
                continue
            deduped.append(value)
            seen.add(key)
        return deduped

    @classmethod
    def _normalize_search_text(cls, value: str | None) -> str:
        text = cls._clean_search_text(value).lower()
        if not text:
            return ""
        text = re.sub(r"[‐‑‒–—−]+", " ", text)
        text = re.sub(r"[“”\"'`]+", "", text)
        text = re.sub(r"[,:;!?]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def _normalize_search_title(cls, value: str | None) -> str:
        return cls._normalize_search_text(cls._clean_search_title(value))

    @classmethod
    def _normalize_artist_simple(cls, value: str | None) -> str:
        normalized = cls._normalize_search_text(value)
        normalized = re.sub(r"[\W_]+", " ", normalized, flags=re.UNICODE)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @classmethod
    def _normalize_artist_credit_text(cls, value: str | None) -> str:
        text = cls._clean_search_text(value).lower()
        if not text:
            return ""
        text = re.sub(r"[‐‑‒–—−]+", " ", text)
        text = re.sub(r"[“”\"'`]+", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def _select_metadata_search_winner(cls, *, base: MusicMetaBase, items: list[MetadataSummary]) -> MetadataSummary | None:
        def normalize(value: str | None) -> str:
            return cls._normalize_search_text(value)

        def normalize_title(value: str | None) -> str:
            return cls._normalize_search_title(value)

        def normalize_title_raw(value: str | None) -> str:
            return cls._normalize_search_text(value)

        def artist_tokens(value: str | None) -> list[str]:
            normalized = cls._normalize_artist_credit_text(value)
            if not normalized:
                return []
            chunks = re.split(r"\s*(?:feat\.?|ft\.?|featuring|with|x|&|,|/|and)\s*", normalized)
            return [chunk.strip() for chunk in chunks if chunk.strip()]

        canonical_title = normalize_title(base.canonical_title)
        canonical_title_raw = normalize_title_raw(base.canonical_title)
        canonical_album = normalize(base.canonical_album_title)
        canonical_artist_credit = cls._normalize_artist_credit_text(" ".join(base.canonical_artist_names))
        canonical_artist_simple = cls._normalize_artist_simple(" ".join(base.canonical_artist_names))
        alias_titles = {normalize_title(value) for value in base.alias_titles if normalize_title(value)}
        alias_artists = {cls._normalize_artist_credit_text(value) for value in base.alias_artist_names if cls._normalize_artist_credit_text(value)}
        alias_artists_simple = {cls._normalize_artist_simple(value) for value in base.alias_artist_names if cls._normalize_artist_simple(value)}
        alias_albums = {normalize(value) for value in base.alias_album_titles if normalize(value)}

        winner: MetadataSummary | None = None
        winner_score = -1
        for item in items:
            title_score = 0
            item_title = normalize_title(item.track_title or item.title)
            item_title_raw = normalize_title_raw(item.track_title or item.title)
            item_album = normalize(item.album_title)
            item_artist_credit = cls._normalize_artist_credit_text(item.artist_name)
            item_artist_simple = cls._normalize_artist_simple(item.artist_name)
            exact_title_match = False
            expected_tokens = artist_tokens(canonical_artist_credit)
            actual_tokens = set(artist_tokens(item_artist_credit))

            if canonical_title_raw and item_title_raw == canonical_title_raw:
                title_score += 72
                exact_title_match = True
            elif canonical_title and item_title == canonical_title:
                title_score += 58
            elif canonical_title and canonical_title in item_title:
                title_score += 45
            elif item_title in alias_titles:
                title_score += 40

            artist_score = 0
            if expected_tokens and actual_tokens and set(expected_tokens) == actual_tokens:
                artist_score += 60
            elif canonical_artist_credit and item_artist_credit == canonical_artist_credit:
                artist_score += 60
            elif canonical_artist_simple and item_artist_simple == canonical_artist_simple:
                artist_score += 40
            elif item_artist_credit in alias_artists or item_artist_simple in alias_artists_simple:
                artist_score += 36
            else:
                if expected_tokens and set(expected_tokens).issubset(actual_tokens):
                    artist_score += 50
                elif expected_tokens and actual_tokens and actual_tokens.intersection(expected_tokens):
                    artist_score += 24

            album_score = 0
            if canonical_album and item_album == canonical_album:
                album_score += 24
            elif canonical_album and item_album and canonical_album in item_album:
                album_score += 14
            elif item_album in alias_albums:
                album_score += 12

            if base.entity_type == EntityType.TRACK:
                if canonical_title and title_score == 0:
                    continue
                if canonical_artist_credit and artist_score == 0:
                    continue
                if canonical_album and album_score == 0:
                    continue
            elif base.entity_type == EntityType.ALBUM:
                if canonical_album and max(title_score, album_score) == 0:
                    continue
                if canonical_artist_credit and artist_score == 0:
                    continue
            else:
                if canonical_artist_credit and artist_score == 0:
                    continue

            year_score = 6 if item.year and base.canonical_year and item.year == base.canonical_year else 0
            score = title_score + artist_score + album_score + year_score
            if exact_title_match:
                score += 5
            if score > winner_score:
                winner_score = score
                winner = item
        return winner
