"""Schemas for Phase 3 query building, search jobs, scoring, and dispatch."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .integration import AdapterMode, AdapterResolution, VerificationState
from .music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMediaMatchStrategy,
    MusicMetaBase,
    MusicRecognitionAssessment,
)
from .shared import DecisionStatus, EntityType, JobStatus, TriggerSource


class QueryPreferences(BaseModel):
    preferred_formats: list[str] = Field(default_factory=lambda: ["FLAC"])
    prefer_lossless: bool = True
    include_aliases: bool = True
    include_year: bool = True
    allow_live: bool = False
    allow_remaster: bool = False
    negative_keywords: list[str] = Field(default_factory=list)
    auto_download_threshold: float = Field(default=90.0, ge=0, le=100)
    manual_confirm_threshold: float = Field(default=70.0, ge=0, le=100)


class QueryBuildRequest(BaseModel):
    input: MusicMediaInput
    preferences: QueryPreferences = Field(default_factory=QueryPreferences)


class QueryClause(BaseModel):
    query_type: Literal["canonical", "alias", "relaxed", "negative"]
    source: str
    query: str
    explanation: str
    priority: int = Field(default=100, ge=1)


class QueryContext(BaseModel):
    entity_type: EntityType
    provider: str
    provider_id: str
    title: str
    artist_names: list[str] = Field(default_factory=list)
    album_title: str | None = None
    album_artist_names: list[str] = Field(default_factory=list)
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    external_refs: dict[str, str] = Field(default_factory=dict)
    match_strategy: MusicMediaMatchStrategy | None = None
    note: str
    summary: str


class QueryBuildResult(BaseModel):
    entity_type: EntityType
    provider: str
    provider_id: str
    music_media_info: MusicMediaInfo
    mock: bool = True
    preferences: QueryPreferences
    canonical_queries: list[QueryClause] = Field(default_factory=list)
    alias_queries: list[QueryClause] = Field(default_factory=list)
    relaxed_queries: list[QueryClause] = Field(default_factory=list)
    negative_queries: list[QueryClause] = Field(default_factory=list)
    ordered_queries: list[QueryClause] = Field(default_factory=list)
    query_context: QueryContext
    note: str
    integration_point: str
    todo: list[str] = Field(default_factory=list)


class HostSearchCandidate(BaseModel):
    site_id: str
    site_name: str
    title: str
    normalized_title: str
    size_bytes: int = 0
    seeders: int = 0
    peers: int = 0
    format_tag: str | None = None
    bitrate_kbps: int | None = None
    source_tags: list[str] = Field(default_factory=list)
    mock: bool = True
    note: str
    adapter_resolution: AdapterResolution | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class PathHandoffInfo(BaseModel):
    download_hash: str | None = None
    source_path: str | None = None
    source_filetype: str | None = None
    source_name: str | None = None
    source_basename: str | None = None
    source_extension: str | None = None
    handoff_source: str
    handoff_status: str
    verification_state: VerificationState = VerificationState.UNVERIFIED
    note: str
    raw_summary: dict[str, Any] = Field(default_factory=dict)


class ScoreBreakdownItem(BaseModel):
    score: float
    reason: str


class CandidateScoreResult(BaseModel):
    raw_score: float
    score_total: float
    score_breakdown: dict[str, ScoreBreakdownItem]
    decision: DecisionStatus
    reason_codes: list[str] = Field(default_factory=list)
    dispatchable: bool = False


class SearchJobCreateRequest(BaseModel):
    input: MusicMediaInput
    trigger_source: TriggerSource = TriggerSource.MANUAL
    profile_id: str = "default-lossless"
    mode: Literal["manual", "auto"] = "manual"
    preferences: QueryPreferences = Field(default_factory=QueryPreferences)


class SearchJobSummary(BaseModel):
    id: str
    music_media_input: MusicMediaInput
    music_meta_base: MusicMetaBase
    music_recognition_assessment: MusicRecognitionAssessment
    music_media_info: MusicMediaInfo
    trigger_source: TriggerSource
    profile_id: str
    mode: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    mock: bool = True
    note: str | None = None
    query_build: QueryBuildResult | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    adapter_resolution: AdapterResolution | None = None


class SearchCandidateDetail(BaseModel):
    id: str
    job_id: str
    site_id: str
    site_name: str
    title: str
    normalized_title: str
    size_bytes: int
    seeders: int
    peers: int
    format_tag: str | None = None
    bitrate_kbps: int | None = None
    source_tags: list[str] = Field(default_factory=list)
    raw_score: float
    score_total: float
    score_breakdown: dict[str, ScoreBreakdownItem] = Field(default_factory=dict)
    decision: DecisionStatus
    reason_codes: list[str] = Field(default_factory=list)
    dispatchable: bool = False
    dispatch_status: str = "pending"
    mock: bool = True
    note: str | None = None
    created_at: datetime
    adapter_resolution: AdapterResolution | None = None
    path_handoff: PathHandoffInfo | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class SearchCandidateListData(BaseModel):
    job_id: str
    items: list[SearchCandidateDetail] = Field(default_factory=list)
    total: int = 0
    mock: bool = True
    note: str
    adapter_resolution: AdapterResolution | None = None


class DownloadBindingSummary(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    target_downloader: str
    downloader_task_id: str | None = None
    dispatchable: bool = False
    dispatch_status: str
    mock: bool = True
    note: str | None = None
    integration_point: str | None = None
    dispatched_at: datetime
    path_handoff: PathHandoffInfo | None = None
    host_response_summary: dict[str, Any] = Field(default_factory=dict)


class DownloadBindingDetail(DownloadBindingSummary):
    candidate: SearchCandidateDetail | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class DownloadBindingListData(BaseModel):
    items: list[DownloadBindingSummary] = Field(default_factory=list)
    total: int = 0
    mock: bool = True
    note: str


class MutationResult(BaseModel):
    id: str
    deleted: bool = False


class DispatchRequest(BaseModel):
    result_id: str
    downloader_id: str = "mock-downloader"
    save_path_policy: Literal["auto", "manual"] = "auto"
    manual_confirm: bool = True


class DispatchResult(BaseModel):
    candidate_id: str
    job_id: str
    dispatchable: bool
    dispatch_status: str
    target_downloader: str
    downloader_task_id: str | None = None
    note: str
    integration_point: str
    mock: bool = True
    binding_id: str | None = None
    dispatch_backend: AdapterMode = AdapterMode.MOCK
    capability_source: str = "mock.adapter"
    fallback_reason: str | None = None
    failure_reason: str | None = None
    verification_state: VerificationState = VerificationState.PLACEHOLDER
    path_handoff: PathHandoffInfo | None = None
    host_response_summary: dict[str, Any] = Field(default_factory=dict)
    adapter_resolution: AdapterResolution | None = None


class DispatchAdapterResult(BaseModel):
    dispatchable: bool
    dispatch_status: str
    target_downloader: str
    downloader_task_id: str | None = None
    note: str
    integration_point: str
    mock: bool = True
    dispatch_backend: AdapterMode = AdapterMode.MOCK
    capability_source: str = "mock.adapter"
    fallback_reason: str | None = None
    failure_reason: str | None = None
    verification_state: VerificationState = VerificationState.PLACEHOLDER
    path_handoff: PathHandoffInfo | None = None
    host_response_summary: dict[str, Any] = Field(default_factory=dict)
    adapter_resolution: AdapterResolution | None = None
