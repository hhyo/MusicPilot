"""Music metadata recovery helpers for organize preview/apply planning."""

from __future__ import annotations

import re
from dataclasses import dataclass

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


class MusicMetadataResolver:
    def resolve(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
    ) -> MusicOrganizeMetadata:
        title = metadata_detail.title if metadata_detail else candidate.title
        artist_name = (
            metadata_detail.artist_name
            if metadata_detail and metadata_detail.artist_name
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "artist" else candidate.site_name)
        )
        album_title = (
            metadata_detail.album_title
            if metadata_detail and metadata_detail.album_title
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "album" else title)
        )
        track_title = (
            metadata_detail.track_title
            if metadata_detail and metadata_detail.track_title
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "track" else title)
        )
        year = str(metadata_detail.year) if metadata_detail and metadata_detail.year else "unknown"
        format_ext = slugify(candidate.format_tag or "bin")

        return MusicOrganizeMetadata(
            title=slugify(title),
            artist_name=slugify(artist_name),
            album_title=slugify(album_title),
            track_title=slugify(track_title),
            year=year,
            format_ext=format_ext,
        )
