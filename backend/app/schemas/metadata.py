"""Metadata DTOs for Phase 2 search and detail routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .mvp import EntityType, ReleaseType


class MetadataSearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=120)
    type: EntityType = Field(default=EntityType.TRACK)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)


class MetadataReference(BaseModel):
    id: str
    title: str
    entity_type: EntityType
    subtitle: str | None = None
    track_number: int | None = None
    disc_number: int | None = None


class MetadataSummary(BaseModel):
    entity_type: EntityType
    id: str
    title: str
    artist_name: str | None = None
    album_title: str | None = None
    track_title: str | None = None
    aliases: list[str] = Field(default_factory=list)
    year: int | None = None
    release_type: ReleaseType | None = None
    genres: list[str] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)
    provider: str
    source_type: str
    mock: bool = True
    note: str


class MetadataDetail(MetadataSummary):
    country: str | None = None
    duration_seconds: int | None = None
    disambiguation: str | None = None
    release_count: int | None = None
    metadata_stage: str = "metadata_only"
    integration_point: str
    related_artists: list[MetadataReference] = Field(default_factory=list)
    related_album: MetadataReference | None = None
    related_albums: list[MetadataReference] = Field(default_factory=list)
    tracks: list[MetadataReference] = Field(default_factory=list)
    todo: list[str] = Field(default_factory=list)


class MetadataSearchData(BaseModel):
    keyword: str
    entity_type: EntityType
    page: int
    page_size: int
    total: int
    provider: str
    source_type: str
    integration_point: str
    items: list[MetadataSummary] = Field(default_factory=list)


class SeedArtist(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    year: int | None = None
    country: str | None = None
    external_ids: dict[str, str] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None


class SeedAlbum(BaseModel):
    id: str
    title: str
    artist_ids: list[str] = Field(default_factory=list)
    artist_name: str | None = None
    aliases: list[str] = Field(default_factory=list)
    year: int | None = None
    release_type: ReleaseType | None = None
    genres: list[str] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None


class SeedTrack(BaseModel):
    id: str
    title: str
    artist_ids: list[str] = Field(default_factory=list)
    artist_name: str | None = None
    album_id: str | None = None
    album_title: str | None = None
    aliases: list[str] = Field(default_factory=list)
    year: int | None = None
    version: str | None = None
    release_type: ReleaseType | None = None
    genres: list[str] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: int | None = None
    note: str | None = None


class MetadataSeedCatalog(BaseModel):
    provider: str
    source_type: str
    note: str
    artists: list[SeedArtist] = Field(default_factory=list)
    albums: list[SeedAlbum] = Field(default_factory=list)
    tracks: list[SeedTrack] = Field(default_factory=list)
