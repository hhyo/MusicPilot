"""Shared domain enums and lightweight DTOs used across backend services."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChartType(str, Enum):
    TRACK = "track"
    ALBUM = "album"
    ARTIST = "artist"


class EntityType(str, Enum):
    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"


class SubscriptionTargetType(str, Enum):
    CHART = "chart"
    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"


class SubscriptionStatus(str, Enum):
    DRAFT = "draft"
    ENABLED = "enabled"
    PAUSED = "paused"
    DISABLED = "disabled"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLED = "cancelled"
    MATCHED = "matched"
    MANUAL_PENDING = "manual_pending"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    NO_RESULT = "no_result"
    FAILED = "failed"


class DecisionStatus(str, Enum):
    AUTO_DOWNLOAD = "auto_download"
    MANUAL_CONFIRM = "manual_confirm"
    REJECT = "reject"
    PENDING = "pending"


class TriggerSource(str, Enum):
    MANUAL = "manual"
    CHART = "chart"
    SUBSCRIPTION = "subscription"
    ARTIST_WATCH = "artist_watch"


class AudioProfile(str, Enum):
    MP3 = "mp3"
    AAC = "aac"
    FLAC = "flac"
    APE = "ape"
    WAV = "wav"
    HIRES = "hires"


class ReleaseType(str, Enum):
    SINGLE = "single"
    EP = "ep"
    ALBUM = "album"
    COMPILATION = "compilation"
    LIVE = "live"
    REMASTER = "remaster"
    DELUXE = "deluxe"


class ChartProviderMode(str, Enum):
    MOCK = "mock"
    LISTENBRAINZ = "listenbrainz"
    RSS_FEED = "rss_feed"


class DashboardSummary(BaseModel):
    subscriptions_total: int = 0
    jobs_running: int = 0
    downloads_pending: int = 0
    organize_failed: int = 0


class Provider(BaseModel):
    id: str
    name: str
    type: str
    enabled: bool


class Chart(BaseModel):
    id: str
    provider: str
    name: str
    chart_type: ChartType
    region: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)


class ChartEntry(BaseModel):
    rank: int
    entity_type: EntityType
    entity_id: str
    title: str
    subtitle: str | None = None


class Artist(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)


class Album(BaseModel):
    id: str
    title: str
    artist_ids: list[str]
    year: int | None = None
    release_type: ReleaseType | None = None


class Track(BaseModel):
    id: str
    title: str
    artist_ids: list[str]
    album_id: str | None = None
    version: str | None = None


class SearchHit(BaseModel):
    entity_type: EntityType
    score: float
    artist: Artist | None = None
    album: Album | None = None
    track: Track | None = None


class Subscription(BaseModel):
    id: str
    target_type: SubscriptionTargetType
    target_id: str
    profile_id: str
    status: SubscriptionStatus
    rule_json: dict[str, Any] = Field(default_factory=dict)


class SearchJob(BaseModel):
    id: str
    target_type: SubscriptionTargetType
    target_id: str
    trigger_source: TriggerSource
    profile_id: str
    status: JobStatus


class SearchResult(BaseModel):
    id: str
    site_id: str
    raw_title: str
    normalized_title: str
    size_bytes: int
    seeders: int
    leechers: int
    audio_profile: AudioProfile
    score_total: float
    decision: DecisionStatus
    reason_codes: list[str] = Field(default_factory=list)


class DownloadBinding(BaseModel):
    id: str
    result_id: str
    downloader_task_id: str
    status: str


class OrganizeJob(BaseModel):
    id: str
    library_item_id: str
    status: str


class ProviderSettings(BaseModel):
    chart_providers: list[Provider] = Field(default_factory=list)
    metadata_providers: list[Provider] = Field(default_factory=list)
    pt_sites: list[Provider] = Field(default_factory=list)


class ChartRssFeedSettings(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    url: HttpUrl
    category: str = Field(min_length=1)
    region: str = Field(min_length=1)
    enabled: bool = True

    model_config = ConfigDict(extra="forbid")


class ProviderSettingsUpdatePayload(BaseModel):
    chart_provider_mode: ChartProviderMode
    chart_rss_feeds: list[ChartRssFeedSettings] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ProviderSettingsResponse(BaseModel):
    chart_provider_mode: ChartProviderMode
    chart_rss_feeds: list[ChartRssFeedSettings] = Field(default_factory=list)
    metadata_provider_mode: str | None = None


class RuleProfile(BaseModel):
    id: str
    name: str
    audio_profiles: list[AudioProfile] = Field(default_factory=list)
    allow_live: bool = False
    allow_remaster: bool = False
    auto_download_threshold: float = 90.0
    manual_confirm_threshold: float = 70.0


class SearchRequest(BaseModel):
    keyword: str
    type: EntityType = EntityType.TRACK
    filters: dict[str, Any] = Field(default_factory=dict)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CreateChartSubscriptionRequest(BaseModel):
    profile_id: str
    top_n: int | None = Field(default=None, ge=1)
    region: str | None = None
    allow_keywords: list[str] = Field(default_factory=list)


class CreateSubscriptionRequest(BaseModel):
    target_type: SubscriptionTargetType
    target_id: str
    profile_id: str
    rule_json: dict[str, Any] = Field(default_factory=dict)


class UpdateSubscriptionRequest(BaseModel):
    status: SubscriptionStatus | None = None
    profile_id: str | None = None
    rule_json: dict[str, Any] = Field(default_factory=dict)


class CreateJobRequest(BaseModel):
    target_type: SubscriptionTargetType
    target_id: str
    trigger_source: TriggerSource
    profile_id: str


class DispatchDownloadRequest(BaseModel):
    result_id: str
    downloader_id: str
    save_path_policy: str = "auto"
    manual_confirm: bool = True
