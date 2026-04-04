"""Music metadata recovery helpers for organize preview/apply planning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from ..schemas.acquisition import SearchCandidateDetail
from ..schemas.metadata import MetadataDetail


def slugify(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return normalized or "unknown"


@dataclass(frozen=True)
class MusicOrganizeMetadata:
    title: str
    artist_name: str
    album_title: str
    track_title: str
    year: str
    format_ext: str


@dataclass(frozen=True)
class _MusicPathHints:
    artist_name: str | None = None
    album_title: str | None = None
    track_title: str | None = None
    title: str | None = None
    year: str | None = None
    format_ext: str | None = None


class MusicMetadataResolver:
    def resolve(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
    ) -> MusicOrganizeMetadata:
        raw_payload = candidate.raw_payload or {}
        hints = self._parse_source_path_hints(candidate)

        explicit_title = self._first_optional(
            self._coerce_text(raw_payload.get("track_title")),
            self._coerce_text(raw_payload.get("title")),
        )
        explicit_artist_name = self._first_optional(
            self._coerce_text(raw_payload.get("artist_name")),
            self._coerce_text(raw_payload.get("album_artist")),
        )
        explicit_album_title = self._coerce_text(raw_payload.get("album_title"))
        explicit_track_title = self._coerce_text(raw_payload.get("track_title"))
        explicit_year = self._normalize_year(raw_payload.get("year") or raw_payload.get("release_year"))

        title = self._first_non_empty(
            metadata_detail.title if metadata_detail else None,
            explicit_title,
            hints.title,
            candidate.title,
        )
        artist_name = self._first_non_empty(
            metadata_detail.artist_name if metadata_detail and metadata_detail.artist_name else None,
            explicit_artist_name,
            metadata_detail.title if metadata_detail and metadata_detail.entity_type == "artist" else None,
            hints.artist_name,
            candidate.site_name,
        )
        album_title = self._first_non_empty(
            metadata_detail.album_title if metadata_detail and metadata_detail.album_title else None,
            explicit_album_title,
            metadata_detail.title if metadata_detail and metadata_detail.entity_type == "album" else None,
            hints.album_title,
            title,
        )
        track_title = self._first_non_empty(
            metadata_detail.track_title if metadata_detail and metadata_detail.track_title else None,
            explicit_track_title,
            metadata_detail.title if metadata_detail and metadata_detail.entity_type == "track" else None,
            hints.track_title,
            title,
        )
        year = self._first_non_empty(
            str(metadata_detail.year) if metadata_detail and metadata_detail.year else None,
            explicit_year,
            hints.year,
            "unknown",
        )
        format_ext = slugify(candidate.format_tag or hints.format_ext or "bin")

        return MusicOrganizeMetadata(
            title=slugify(title),
            artist_name=slugify(artist_name),
            album_title=slugify(album_title),
            track_title=slugify(track_title),
            year=year,
            format_ext=format_ext,
        )

    def _parse_source_path_hints(self, candidate: SearchCandidateDetail) -> _MusicPathHints:
        source_path = self._resolve_source_path(candidate)
        if not source_path:
            return _MusicPathHints()

        path = PurePosixPath(source_path)
        stem = path.stem
        parent_dir = path.parent.name if path.parent != path else None
        grandparent_dir = path.parent.parent.name if path.parent.parent != path.parent else None

        parsed_track_title = self._parse_track_title(stem)
        parsed_year, parsed_album_title = self._parse_album_dir(parent_dir)

        return _MusicPathHints(
            artist_name=grandparent_dir or None,
            album_title=parsed_album_title or parent_dir or None,
            track_title=parsed_track_title or stem or None,
            title=parsed_track_title or stem or None,
            year=parsed_year,
            format_ext=path.suffix.lstrip(".") or None,
        )

    def _resolve_source_path(self, candidate: SearchCandidateDetail) -> str | None:
        raw_payload = candidate.raw_payload or {}
        if isinstance(raw_payload.get("host_transfer_source_path"), str):
            return raw_payload["host_transfer_source_path"]
        if isinstance(raw_payload.get("local_file_path"), str):
            return raw_payload["local_file_path"]
        if candidate.path_handoff and candidate.path_handoff.source_path:
            return candidate.path_handoff.source_path
        return None

    def _parse_album_dir(self, value: str | None) -> tuple[str | None, str | None]:
        if not value:
            return None, None
        match = re.match(r"^\s*(\d{4})\s*-\s*(.+?)\s*$", value)
        if match:
            return match.group(1), match.group(2)
        return None, value

    def _parse_track_title(self, value: str | None) -> str | None:
        if not value:
            return None
        match = re.match(r"^\s*\d{1,2}\s*[-._ ]+\s*(.+?)\s*$", value)
        if match:
            return match.group(1)
        return value

    def _coerce_text(self, value: object) -> str | None:
        if isinstance(value, str) and value.strip():
            return value
        return None

    def _normalize_year(self, value: object) -> str | None:
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            match = re.match(r"^\s*(\d{4})\s*$", value)
            if match:
                return match.group(1)
        return None

    def _first_non_empty(self, *values: str | None) -> str:
        for value in values:
            if value and str(value).strip():
                return str(value)
        return "unknown"

    def _first_optional(self, *values: str | None) -> str | None:
        for value in values:
            if value and str(value).strip():
                return str(value)
        return None
