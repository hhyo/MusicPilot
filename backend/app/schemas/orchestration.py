"""Schemas for Phase 6 subscriptions, charts, and organize boundaries."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .acquisition import PathHandoffInfo, SearchCandidateDetail, SearchJobSummary
from .integration import AdapterMode, AdapterResolution, VerificationState
from .metadata import MetadataDetail
from .music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMetaBase,
    MusicRecognitionAssessment,
    MusicRecognitionState,
)
from .mvp import EntityType


class SubscriptionType(str, Enum):
    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"
    CHART_ENTRY = "chart_entry"


class SubscriptionState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class SubscriptionMode(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SCHEDULED_PLACEHOLDER = "scheduled_placeholder"


class SubscriptionRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    MATCHED = "matched"
    DISPATCHED = "dispatched"
    APPLIED = "applied"
    MANUAL_PENDING = "manual_pending"
    NO_RESULT = "no_result"
    FAILED = "failed"


class OrganizeStatus(str, Enum):
    PLANNED = "planned"
    PREVIEW_READY = "preview_ready"
    APPLY_PENDING = "apply_pending"
    APPLIED = "applied"
    FALLBACK_APPLIED = "fallback_applied"
    SKIPPED = "skipped"
    FAILED = "failed"


class OrganizeConflictPolicy(str, Enum):
    SKIP_EXISTING = "skip_existing"
    OVERWRITE = "overwrite"
    APPEND_SUFFIX = "append_suffix"


class ChartProviderInfo(BaseModel):
    id: str
    chart_source: str
    display_name: str
    enabled: bool = True
    mock: bool = True
    note: str
    integration_point: str


class ChartInfo(BaseModel):
    id: str
    chart_source: str
    chart_name: str
    chart_type: EntityType
    region: str | None = None
    category: str | None = None
    refresh_hint: str | None = None
    item_count: int = 0
    updated_at: datetime
    mock: bool = True
    note: str
    summary: str | None = None
    chart_group: str | None = None
    chart_scope: str | None = None
    freshness_label: str | None = None
    supports_subscription: bool = True


class ChartEntryInfo(BaseModel):
    item_id: str
    chart_id: str
    chart_source: str
    chart_name: str
    rank: int
    item_type: EntityType
    target_id: str
    target_name: str
    subtitle: str | None = None
    provider: str
    source_type: str
    target_payload: dict[str, Any] = Field(default_factory=dict)
    mock: bool = True
    note: str


class DiscoveryEntryView(BaseModel):
    entry: ChartEntryInfo
    media_input: MusicMediaInput
    meta_base: MusicMetaBase
    entry_summary: str
    badges: list[str] = Field(default_factory=list)
    highlight_reason: str | None = None
    recognition_assessment: MusicRecognitionAssessment = Field(
        default_factory=lambda: MusicRecognitionAssessment(state=MusicRecognitionState.READY)
    )


class DiscoveryEntryGroup(BaseModel):
    group_key: str
    group_label: str
    items: list[DiscoveryEntryView] = Field(default_factory=list)


class ChartListData(BaseModel):
    items: list[ChartInfo] = Field(default_factory=list)
    total: int = 0
    mock: bool = True
    note: str
    integration_point: str


class ChartDetailData(BaseModel):
    chart: ChartInfo
    items: list[ChartEntryInfo] = Field(default_factory=list)
    item_count: int = 0
    mock: bool = True
    note: str
    integration_point: str
    hero_entry: DiscoveryEntryView | None = None
    summary_stats: dict[str, str | int] = Field(default_factory=dict)
    entry_groups: list[DiscoveryEntryGroup] = Field(default_factory=list)
    recognition_summary: dict[str, int] = Field(default_factory=dict)


class CreateChartEntrySubscriptionRequest(BaseModel):
    chart_item_id: str
    mode: SubscriptionMode = SubscriptionMode.MANUAL
    preference_json: dict[str, Any] = Field(default_factory=dict)


class CreateSubscriptionRequest(BaseModel):
    subscription_type: SubscriptionType
    target_id: str
    target_name: str | None = None
    target_entity_type: EntityType | None = None
    mode: SubscriptionMode = SubscriptionMode.MANUAL
    preference_json: dict[str, Any] = Field(default_factory=dict)
    target_payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_target(self) -> "CreateSubscriptionRequest":
        if self.subscription_type == SubscriptionType.CHART_ENTRY and self.target_entity_type is None:
            raise ValueError("chart_entry subscription requires target_entity_type.")
        return self


class UpdateSubscriptionRequest(BaseModel):
    status: SubscriptionState | None = None
    mode: SubscriptionMode | None = None
    preference_json: dict[str, Any] | None = None


class SubscriptionSummary(BaseModel):
    id: str
    subscription_type: SubscriptionType
    target_id: str
    target_name: str
    target_entity_type: EntityType | None = None
    chart_source: str | None = None
    chart_name: str | None = None
    status: SubscriptionState
    mode: SubscriptionMode
    preference_json: dict[str, Any] = Field(default_factory=dict)
    target_payload: dict[str, Any] = Field(default_factory=dict)
    music_media_input: MusicMediaInput | None = None
    music_meta_base: MusicMetaBase | None = None
    music_recognition_assessment: MusicRecognitionAssessment | None = None
    music_media_info: MusicMediaInfo | None = None
    latest_run_status: str | None = None
    last_run_at: datetime | None = None
    mock: bool = True
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class OrganizeStrategySnapshot(BaseModel):
    strategy_name: str
    library_type: str = "music"
    root_path: str
    artist_dir_template: str
    album_dir_template: str
    track_file_template: str
    conflict_policy: OrganizeConflictPolicy = OrganizeConflictPolicy.SKIP_EXISTING
    template_note: str


class OrganizePlan(BaseModel):
    strategy: str
    strategy_snapshot: OrganizeStrategySnapshot
    target_library_path: str
    target_relative_path: str
    strategy_note: str


class OrganizePreviewResult(BaseModel):
    id: str
    subscription_run_id: str | None = None
    search_job_id: str | None = None
    candidate_id: str | None = None
    binding_id: str | None = None
    organizeable: bool
    organize_backend: AdapterMode = AdapterMode.MOCK
    adapter_mode: AdapterMode = AdapterMode.MOCK
    strategy: str = "music_default_layout"
    strategy_snapshot: OrganizeStrategySnapshot
    organize_status: OrganizeStatus
    target_library_path: str
    target_relative_path: str
    strategy_note: str
    integration_point: str
    capability_source: str = "mock.adapter"
    fallback_reason: str | None = None
    failure_reason: str | None = None
    path_handoff: PathHandoffInfo | None = None
    verification_state: VerificationState = VerificationState.PLACEHOLDER
    adapter_resolution: AdapterResolution | None = None
    music_media_input: MusicMediaInput | None = None
    music_meta_base: MusicMetaBase | None = None
    music_recognition_assessment: MusicRecognitionAssessment | None = None
    music_media_info: MusicMediaInfo | None = None
    mock: bool = True
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionRunSummary(BaseModel):
    id: str
    subscription_id: str
    search_job_id: str | None = None
    execution_status: SubscriptionRunStatus
    matched_candidates_count: int
    organize_record_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary_json: dict[str, Any] = Field(default_factory=dict)
    music_media_input: MusicMediaInput | None = None
    music_meta_base: MusicMetaBase | None = None
    music_recognition_assessment: MusicRecognitionAssessment | None = None
    music_media_info: MusicMediaInfo | None = None
    mock: bool = True
    note: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionDetail(SubscriptionSummary):
    recent_runs: list[SubscriptionRunSummary] = Field(default_factory=list)


class SubscriptionListData(BaseModel):
    items: list[SubscriptionSummary] = Field(default_factory=list)
    total: int = 0
    mock: bool = True
    note: str


class SubscriptionRunListData(BaseModel):
    subscription_id: str
    items: list[SubscriptionRunSummary] = Field(default_factory=list)
    total: int = 0
    mock: bool = True
    note: str


class SubscriptionRunDetail(SubscriptionRunSummary):
    subscription: SubscriptionSummary
    metadata_target: MetadataDetail | None = None
    search_job: SearchJobSummary | None = None
    candidates: list[SearchCandidateDetail] = Field(default_factory=list)
    organize_preview: OrganizePreviewResult | None = None


class OrganizePreviewRequest(BaseModel):
    candidate_id: str | None = None
    binding_id: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "OrganizePreviewRequest":
        if not self.candidate_id and not self.binding_id:
            raise ValueError("candidate_id or binding_id is required.")
        return self


class OrganizeApplyRequest(BaseModel):
    organize_job_id: str


class OrganizeRecordListData(BaseModel):
    items: list[OrganizePreviewResult] = Field(default_factory=list)
    total: int = 0
    mock: bool = True
    note: str


class OrganizeAdapterResult(BaseModel):
    organizeable: bool
    organize_backend: AdapterMode = AdapterMode.MOCK
    adapter_mode: AdapterMode = AdapterMode.MOCK
    strategy: str = "music_default_layout"
    strategy_snapshot: OrganizeStrategySnapshot
    organize_status: OrganizeStatus
    target_library_path: str
    target_relative_path: str
    strategy_note: str
    integration_point: str
    capability_source: str = "mock.adapter"
    fallback_reason: str | None = None
    failure_reason: str | None = None
    path_handoff: PathHandoffInfo | None = None
    verification_state: VerificationState = VerificationState.PLACEHOLDER
    adapter_resolution: AdapterResolution | None = None
    mock: bool = True
    note: str
