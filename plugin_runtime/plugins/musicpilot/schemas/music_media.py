"""Core domain models for the unified music media chain."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .metadata import MetadataDetail
from .mvp import EntityType


class MusicMediaSourceKind(str, Enum):
    DISCOVERY = "discovery"
    DETAIL = "detail"
    SEARCH = "search"
    SUBSCRIPTION = "subscription"
    SUBSCRIPTION_DETAIL = "subscription_detail"
    SUBSCRIPTION_RESOLUTION = "subscription_resolution"
    ACQUISITION = "acquisition"
    LIBRARY = "library"
    MANUAL = "manual"


class MusicRecognitionState(str, Enum):
    DIRECT = "direct"
    READY = "ready"
    INSUFFICIENT = "insufficient"
    FAILED = "failed"


class MusicMediaMatchStrategy(str, Enum):
    STRONG_REF = "strong_ref"
    METADATA_SEARCH = "metadata_search"


class MusicMediaInput(BaseModel):
    """Raw music clues collected from an upstream scenario."""

    entity_hint: EntityType | None = None
    source_kind: MusicMediaSourceKind
    title: str | None = None
    subtitle: str | None = None
    artist_names: list[str] = Field(default_factory=list)
    album_title: str | None = None
    album_artist_names: list[str] = Field(default_factory=list)
    release_date: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    external_refs: dict[str, str] = Field(default_factory=dict)
    source_context: dict[str, Any] = Field(default_factory=dict)
    raw_context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class MusicMetaBase(BaseModel):
    """Normalized music metadata before final entity recognition."""

    entity_type: EntityType
    canonical_title: str | None = None
    canonical_artist_names: list[str] = Field(default_factory=list)
    canonical_album_title: str | None = None
    canonical_album_artist_names: list[str] = Field(default_factory=list)
    canonical_release_date: str | None = None
    canonical_year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    alias_titles: list[str] = Field(default_factory=list)
    alias_artist_names: list[str] = Field(default_factory=list)
    alias_album_titles: list[str] = Field(default_factory=list)
    featuring_artist_names: list[str] = Field(default_factory=list)
    external_refs: dict[str, str] = Field(default_factory=dict)
    source_refs: dict[str, str] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    normalization_notes: list[str] = Field(default_factory=list)
    confidence_hint: float | None = None

    model_config = ConfigDict(extra="forbid")


class MusicMediaInfo(BaseModel):
    """Resolved formal music media object used by downstream flows."""

    entity_type: EntityType
    provider: str
    provider_id: str
    title: str | None = None
    artist_names: list[str] = Field(default_factory=list)
    album_title: str | None = None
    album_artist_names: list[str] = Field(default_factory=list)
    release_date: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    related_artist_ids: list[str] = Field(default_factory=list)
    related_album_id: str | None = None
    related_track_ids: list[str] = Field(default_factory=list)
    external_refs: dict[str, str] = Field(default_factory=dict)
    match_confidence: float | None = None
    match_strategy: MusicMediaMatchStrategy | None = None
    match_evidence: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    cover_url: str | None = None
    disambiguation: str | None = None
    release_context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class MusicRecognitionAssessment(BaseModel):
    """Recognition readiness summary emitted by the unified chain."""

    state: MusicRecognitionState
    note: str | None = None

    model_config = ConfigDict(extra="forbid")


class MusicPrepareRequest(BaseModel):
    input: MusicMediaInput

    model_config = ConfigDict(extra="forbid")


class MusicResolveRequest(BaseModel):
    input: MusicMediaInput

    model_config = ConfigDict(extra="forbid")


class MusicPrepareResponse(BaseModel):
    input: MusicMediaInput
    base: MusicMetaBase
    assessment: MusicRecognitionAssessment

    model_config = ConfigDict(extra="forbid")


class MusicResolveResponse(BaseModel):
    base: MusicMetaBase
    assessment: MusicRecognitionAssessment
    media: MusicMediaInfo

    model_config = ConfigDict(extra="forbid")


class MusicResolveDetailRequest(BaseModel):
    input: MusicMediaInput

    model_config = ConfigDict(extra="forbid")


class MusicResolveDetailResponse(BaseModel):
    base: MusicMetaBase
    assessment: MusicRecognitionAssessment
    media: MusicMediaInfo
    detail: MetadataDetail

    model_config = ConfigDict(extra="forbid")
