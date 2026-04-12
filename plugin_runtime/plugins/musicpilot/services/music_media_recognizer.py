"""Recognition stage for the unified music media chain."""

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

    def __init__(self, metadata_service, metadata_adapter):
        self.metadata_service = metadata_service
        self.metadata_adapter = metadata_adapter

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
                search_result = self.metadata_service.search(
                    MetadataSearchRequest(
                        keyword=keyword,
                        type=base.entity_type,
                        page=1,
                        page_size=10,
                    )
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
            provider=winner.provider or self.metadata_adapter.provider,
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
        artists = cls._build_search_text_candidates(
            primary=primary_artist,
            extras=base.alias_artist_names,
            title_mode=False,
        )
        titles = cls._build_search_text_candidates(
            primary=base.canonical_title,
            extras=base.alias_titles,
            title_mode=True,
        )
        albums = cls._build_search_text_candidates(
            primary=base.canonical_album_title,
            extras=base.alias_album_titles,
            title_mode=False,
        )

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
            text = re.sub(
                r"\s*[\(\[][^)\]]*\b(?:live|remaster(?:ed)?|version|edit|mono|stereo|instrumental|acoustic|karaoke|bonus track)\b[^)\]]*[\)\]]\s*$",
                "",
                text,
                flags=re.IGNORECASE,
            )
            text = re.sub(
                r"\s*[\(\[][^)\]]*\b(?:official\s+)?(?:video|audio|mv|lyrics?|lyric video|performance)\b[^)\]]*[\)\]]\s*$",
                "",
                text,
                flags=re.IGNORECASE,
            )
            text = re.sub(
                r"\s*[-:]\s*.*\b(?:live|remaster(?:ed)?|version|edit|mono|stereo|instrumental|acoustic|karaoke|bonus track)\b.*$",
                "",
                text,
                flags=re.IGNORECASE,
            )
            text = re.sub(
                r"\s*[-:]\s*.*\b(?:official\s+)?(?:video|audio|mv|lyrics?|lyric video|performance)\b.*$",
                "",
                text,
                flags=re.IGNORECASE,
            )
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
    def _select_metadata_search_winner(
        cls,
        *,
        base: MusicMetaBase,
        items: list[MetadataSummary],
    ) -> MetadataSummary | None:
        def normalize(value: str | None) -> str:
            return cls._normalize_search_text(value)

        def normalize_title(value: str | None) -> str:
            return cls._normalize_search_title(value)

        def artist_tokens(value: str | None) -> list[str]:
            normalized = cls._normalize_artist_credit_text(value)
            if not normalized:
                return []
            normalized = re.sub(r"\b(featuring|feat\.?|ft\.?|with)\b", ",", normalized)
            normalized = normalized.replace("&", ",")
            normalized = re.sub(r"\band\b", ",", normalized)
            normalized = normalized.replace("/", ",").replace(" x ", ",")
            parts = [part.strip(" .-_") for part in normalized.split(",")]
            return [part for part in parts if part]

        def artist_credit_matches(hint_value: str | None, candidate_value: str | None) -> bool:
            hint_normalized = cls._normalize_artist_credit_text(hint_value)
            candidate_normalized = cls._normalize_artist_credit_text(candidate_value)
            if not hint_normalized:
                return False
            if cls._normalize_artist_simple(hint_value) == cls._normalize_artist_simple(candidate_value):
                return True

            hint_parts = artist_tokens(hint_value)
            candidate_parts = artist_tokens(candidate_value)
            if len(hint_parts) <= 1 and len(candidate_parts) <= 1:
                return hint_normalized == candidate_normalized
            if not hint_parts or not candidate_parts:
                return hint_normalized == candidate_normalized
            return set(hint_parts) == set(candidate_parts)

        def artist_credit_score(hint_candidates: list[str], candidate_value: str | None) -> int:
            best = -1
            candidate_simple = cls._normalize_artist_simple(candidate_value)
            candidate_parts = artist_tokens(candidate_value)
            for index, candidate in enumerate(hint_candidates):
                if not artist_credit_matches(candidate, candidate_value):
                    continue
                score = max(0, 100 - index * 10)
                candidate_simple_hint = cls._normalize_artist_simple(candidate)
                hint_parts = artist_tokens(candidate)
                if hint_parts and candidate_parts and set(hint_parts) == set(candidate_parts):
                    score += 30
                    if len(hint_parts) > 1:
                        score += 20
                elif candidate_simple_hint == candidate_simple:
                    score += 15
                elif len(hint_parts) == 1:
                    score += 5
                best = max(best, score)
            return best

        primary_artist = " & ".join(base.canonical_artist_names).strip()
        hint_artist_raw = primary_artist
        hint_title_raw = base.canonical_title or ""
        hint_album_raw = base.canonical_album_title or ""

        hint_artist_candidates_raw = cls._build_search_text_candidates(
            primary=hint_artist_raw,
            extras=base.alias_artist_names,
            title_mode=False,
        )
        hint_title_candidates_raw = cls._build_search_text_candidates(
            primary=hint_title_raw,
            extras=base.alias_titles,
            title_mode=True,
        )
        hint_album_candidates_raw = cls._build_search_text_candidates(
            primary=hint_album_raw,
            extras=base.alias_album_titles,
            title_mode=False,
        )

        hint_artist = normalize(hint_artist_raw)
        hint_title = normalize_title(hint_title_raw)
        hint_title_exact = normalize(hint_title_raw)
        hint_album = normalize(hint_album_raw)
        hint_title_candidates = {normalize_title(value) for value in hint_title_candidates_raw if value}
        hint_album_candidates = {normalize(value) for value in hint_album_candidates_raw if value}

        scored: list[tuple[int, int, MetadataSummary]] = []
        for index, item in enumerate(items):
            item_title = normalize_title(item.track_title or item.title)
            item_title_exact = normalize(item.track_title or item.title)
            item_album = normalize(item.album_title)

            if base.entity_type == EntityType.TRACK:
                if not hint_title_candidates or not hint_artist_candidates_raw:
                    continue
                if item_title not in hint_title_candidates:
                    continue
                if hint_album_candidates and item_album not in hint_album_candidates:
                    continue
                artist_score = artist_credit_score(hint_artist_candidates_raw, item.artist_name)
                if artist_score < 0:
                    continue
                score = 300 + artist_score
                if hint_album_candidates:
                    score += 40
                if hint_title_exact and item_title_exact == hint_title_exact:
                    score += 20
            elif base.entity_type == EntityType.ALBUM:
                if not hint_album_candidates:
                    continue
                if item_title not in hint_album_candidates and item_album not in hint_album_candidates:
                    continue
                score = 200
                if hint_artist and normalize(item.artist_name) == hint_artist:
                    score += 30
                if item_title == hint_album or item_album == hint_album:
                    score += 20
            else:
                if not hint_artist_candidates_raw:
                    continue
                artist_score = artist_credit_score(hint_artist_candidates_raw, item.artist_name or item.title)
                if artist_score < 0:
                    continue
                score = 150 + artist_score
            scored.append((score, -index, item))

        if not scored:
            return None
        scored.sort(reverse=True)
        return scored[0][2]
