"""Placeholder service for Phase 1 MVP routes."""

from __future__ import annotations

from ..schemas.common import Pagination
from ..schemas.mvp import (
    Album,
    Artist,
    AudioProfile,
    Chart,
    ChartEntry,
    ChartType,
    CreateChartSubscriptionRequest,
    CreateJobRequest,
    CreateSubscriptionRequest,
    DashboardSummary,
    DecisionStatus,
    DispatchDownloadRequest,
    DownloadBinding,
    EntityType,
    JobStatus,
    OrganizeJob,
    Provider,
    ProviderSettings,
    ReleaseType,
    RuleProfile,
    SearchHit,
    SearchJob,
    SearchRequest,
    SearchResult,
    Subscription,
    SubscriptionStatus,
    SubscriptionTargetType,
    Track,
    TriggerSource,
    UpdateSubscriptionRequest,
)


class MvpPlaceholderService:
    def dashboard_summary(self) -> dict:
        return DashboardSummary().model_dump(mode="json")

    def chart_providers(self) -> list[dict]:
        return [
            Provider(id="chart-qq", name="QQ Music Charts", type="chart", enabled=False).model_dump(
                mode="json"
            ),
            Provider(
                id="chart-netease",
                name="NetEase Charts",
                type="chart",
                enabled=False,
            ).model_dump(mode="json"),
        ]

    def list_charts(self) -> dict:
        data = [
            Chart(
                id="chart-mock-top-001",
                provider="chart-qq",
                name="Mock Top 100",
                chart_type=ChartType.TRACK,
                region="CN",
            ).model_dump(mode="json")
        ]
        pagination = Pagination(page=1, page_size=20, total=1).model_dump(mode="json")
        return {"items": data, "pagination": pagination}

    def chart_detail(self, chart_id: str) -> dict:
        chart = Chart(
            id=chart_id,
            provider="chart-qq",
            name="Mock Top 100",
            chart_type=ChartType.TRACK,
            region="CN",
        ).model_dump(mode="json")
        entries = [
            ChartEntry(
                rank=1,
                entity_type=EntityType.TRACK,
                entity_id="track-mock-001",
                title="Mock Track",
                subtitle="Placeholder Artist",
            ).model_dump(mode="json")
        ]
        return {"chart": chart, "entries": entries}

    def create_chart_subscription(
        self, chart_id: str, payload: CreateChartSubscriptionRequest
    ) -> dict:
        return Subscription(
            id=f"sub-chart-{chart_id}",
            target_type=SubscriptionTargetType.CHART,
            target_id=chart_id,
            profile_id=payload.profile_id,
            status=SubscriptionStatus.DRAFT,
            rule_json={
                "top_n": payload.top_n,
                "region": payload.region,
                "allow_keywords": payload.allow_keywords,
            },
        ).model_dump(mode="json")

    def search(self, payload: SearchRequest) -> dict:
        artist = Artist(id="artist-mock-001", name="Mock Artist", aliases=["Phase 1 Artist"])
        album = Album(
            id="album-mock-001",
            title="Mock Album",
            artist_ids=[artist.id],
            year=2026,
            release_type=ReleaseType.ALBUM,
        )
        track = Track(
            id="track-mock-001",
            title=f"{payload.keyword} Placeholder",
            artist_ids=[artist.id],
            album_id=album.id,
            version="mock-version",
        )
        items = [
            SearchHit(
                entity_type=payload.type,
                score=0.98,
                artist=artist,
                album=album,
                track=track,
            ).model_dump(mode="json")
        ]
        return {
            "items": items,
            "pagination": Pagination(page=payload.page, page_size=payload.page_size, total=1).model_dump(
                mode="json"
            ),
            "query_echo": payload.model_dump(mode="json"),
        }

    def artist_detail(self, artist_id: str) -> dict:
        return Artist(id=artist_id, name="Mock Artist", aliases=["Phase 1 Artist"]).model_dump(
            mode="json"
        )

    def album_detail(self, album_id: str) -> dict:
        return Album(
            id=album_id,
            title="Mock Album",
            artist_ids=["artist-mock-001"],
            year=2026,
            release_type=ReleaseType.ALBUM,
        ).model_dump(mode="json")

    def track_detail(self, track_id: str) -> dict:
        return Track(
            id=track_id,
            title="Mock Track",
            artist_ids=["artist-mock-001"],
            album_id="album-mock-001",
            version="mock-version",
        ).model_dump(mode="json")

    def list_subscriptions(self) -> list[dict]:
        return [
            Subscription(
                id="sub-mock-001",
                target_type=SubscriptionTargetType.ARTIST,
                target_id="artist-mock-001",
                profile_id="default-lossless",
                status=SubscriptionStatus.ENABLED,
                rule_json={"allow_live": False},
            ).model_dump(mode="json")
        ]

    def create_subscription(self, payload: CreateSubscriptionRequest) -> dict:
        return Subscription(
            id="sub-created-mock",
            target_type=payload.target_type,
            target_id=payload.target_id,
            profile_id=payload.profile_id,
            status=SubscriptionStatus.DRAFT,
            rule_json=payload.rule_json,
        ).model_dump(mode="json")

    def update_subscription(self, subscription_id: str, payload: UpdateSubscriptionRequest) -> dict:
        return Subscription(
            id=subscription_id,
            target_type=SubscriptionTargetType.ALBUM,
            target_id="album-mock-001",
            profile_id=payload.profile_id or "default-lossless",
            status=payload.status or SubscriptionStatus.ENABLED,
            rule_json=payload.rule_json,
        ).model_dump(mode="json")

    def run_subscription(self, subscription_id: str) -> dict:
        return SearchJob(
            id=f"job-run-{subscription_id}",
            target_type=SubscriptionTargetType.ALBUM,
            target_id="album-mock-001",
            trigger_source=TriggerSource.SUBSCRIPTION,
            profile_id="default-lossless",
            status=JobStatus.QUEUED,
        ).model_dump(mode="json")

    def list_jobs(self) -> list[dict]:
        return [
            SearchJob(
                id="job-mock-001",
                target_type=SubscriptionTargetType.ALBUM,
                target_id="album-mock-001",
                trigger_source=TriggerSource.MANUAL,
                profile_id="default-lossless",
                status=JobStatus.MANUAL_PENDING,
            ).model_dump(mode="json")
        ]

    def create_job(self, payload: CreateJobRequest) -> dict:
        return SearchJob(
            id="job-created-mock",
            target_type=payload.target_type,
            target_id=payload.target_id,
            trigger_source=payload.trigger_source,
            profile_id=payload.profile_id,
            status=JobStatus.QUEUED,
        ).model_dump(mode="json")

    def job_results(self, job_id: str) -> list[dict]:
        return [
            SearchResult(
                id=f"result-{job_id}",
                site_id="site-mock-001",
                raw_title="Mock Artist - Mock Album [FLAC]",
                normalized_title="mock artist mock album flac",
                size_bytes=1024 * 1024 * 320,
                seeders=12,
                leechers=0,
                audio_profile=AudioProfile.FLAC,
                score_total=96.5,
                decision=DecisionStatus.MANUAL_CONFIRM,
                reason_codes=["mock_score", "mock_host_unverified"],
            ).model_dump(mode="json")
        ]

    def dispatch_download(self, payload: DispatchDownloadRequest) -> dict:
        return DownloadBinding(
            id="binding-mock-001",
            result_id=payload.result_id,
            downloader_task_id="dry-run-task",
            status="submitted",
        ).model_dump(mode="json")

    def organize_jobs(self) -> list[dict]:
        return [
            OrganizeJob(
                id="organize-mock-001",
                library_item_id="library-mock-001",
                status="queued",
            ).model_dump(mode="json")
        ]

    def retry_library_item(self, item_id: str) -> dict:
        return OrganizeJob(
            id=f"organize-retry-{item_id}",
            library_item_id=item_id,
            status="queued",
        ).model_dump(mode="json")

    def provider_settings(self) -> dict:
        settings = ProviderSettings(
            chart_providers=[
                Provider(id="chart-qq", name="QQ Music Charts", type="chart", enabled=False)
            ],
            metadata_providers=[
                Provider(id="metadata-mock", name="Mock Metadata Provider", type="metadata", enabled=False)
            ],
            pt_sites=[Provider(id="pt-mock", name="Mock PT Provider", type="pt", enabled=False)],
        )
        return settings.model_dump(mode="json")

    def update_provider_settings(self, payload: ProviderSettings) -> dict:
        return payload.model_dump(mode="json")

    def profiles(self) -> list[dict]:
        return [
            RuleProfile(
                id="default-lossless",
                name="Default Lossless",
                audio_profiles=[AudioProfile.FLAC],
                allow_live=False,
                allow_remaster=False,
                auto_download_threshold=92.0,
                manual_confirm_threshold=75.0,
            ).model_dump(mode="json")
        ]

    def update_profile(self, payload: RuleProfile) -> dict:
        return payload.model_dump(mode="json")

