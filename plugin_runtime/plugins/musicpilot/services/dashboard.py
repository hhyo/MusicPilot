"""Aggregated dashboard summary service."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.acquisition import DownloadBindingModel, SearchCandidateModel, SearchJobModel
from ..models.orchestration import OrganizeRecordModel, SubscriptionModel, SubscriptionRunModel
from ..schemas.orchestration import (
    DashboardDiscoveryDiagnostics,
    DashboardHandoffDiagnostics,
    DashboardOrganizeDiagnostics,
    DashboardProviderDiagnostics,
    DashboardSchedulerDiagnostics,
    DashboardSummary,
)
from ..core.config import settings
from .subscription_scheduler import normalize_subscription_mode, normalize_timestamp


class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    def summary(self) -> DashboardSummary:
        return DashboardSummary(
            provider=self._provider_diagnostics(),
            discovery=self._discovery_diagnostics(),
            handoff=self._handoff_diagnostics(),
            organize=self._organize_diagnostics(),
            scheduler=self._scheduler_diagnostics(),
        )

    def _provider_diagnostics(self) -> DashboardProviderDiagnostics:
        chart_rss_feeds = settings.chart_rss_feeds or []
        return DashboardProviderDiagnostics(
            chart_provider_mode=str(settings.chart_provider_mode),
            metadata_provider_mode=settings.metadata_provider_mode,
            host_integration_enabled=settings.host_integration_enabled,
            host_search_mode=settings.host_search_mode,
            host_dispatch_mode=settings.host_dispatch_mode,
            host_organize_mode=settings.host_organize_mode,
            chart_rss_feed_total=len(chart_rss_feeds),
            chart_rss_feed_enabled_total=sum(1 for feed in chart_rss_feeds if self._feed_enabled(feed)),
        )

    def _discovery_diagnostics(self) -> DashboardDiscoveryDiagnostics:
        return DashboardDiscoveryDiagnostics(
            subscriptions_total=self._count(select(func.count()).select_from(SubscriptionModel)),
            subscriptions_active_total=self._count(
                select(func.count()).select_from(SubscriptionModel).where(SubscriptionModel.status == "active")
            ),
            search_jobs_total=self._count(select(func.count()).select_from(SearchJobModel)),
            jobs_running=self._count(
                select(func.count())
                .select_from(SearchJobModel)
                .where(SearchJobModel.status == "running")
            ),
            search_candidates_total=self._count(select(func.count()).select_from(SearchCandidateModel)),
        )

    def _handoff_diagnostics(self) -> DashboardHandoffDiagnostics:
        bindings = list(self.session.scalars(select(DownloadBindingModel)).all())
        downloads_pending_statuses = {
            "pending",
            "awaiting_manual_confirmation",
            "mock_submitted",
            "host_submitted",
        }
        return DashboardHandoffDiagnostics(
            download_bindings_total=len(bindings),
            downloads_pending=sum(1 for binding in bindings if binding.dispatch_status in downloads_pending_statuses),
            downloads_resolved=sum(1 for binding in bindings if binding.dispatch_status not in downloads_pending_statuses),
            bindings_with_path_handoff=sum(1 for binding in bindings if self._has_path_handoff(binding.raw_payload)),
        )

    def _organize_diagnostics(self) -> DashboardOrganizeDiagnostics:
        records = list(self.session.scalars(select(OrganizeRecordModel)).all())
        return DashboardOrganizeDiagnostics(
            organize_records_total=len(records),
            organize_preview_ready=sum(1 for record in records if record.organize_status == "preview_ready"),
            organize_applied=sum(1 for record in records if record.organize_status == "applied"),
            organize_failed=sum(1 for record in records if record.organize_status == "failed"),
            organize_with_binding=sum(1 for record in records if record.binding_id is not None),
            organize_with_failure_reason=sum(1 for record in records if bool(record.failure_reason)),
        )

    def _scheduler_diagnostics(self) -> DashboardSchedulerDiagnostics:
        subscriptions = list(self.session.scalars(select(SubscriptionModel)).all())
        now = datetime.now(timezone.utc)
        scheduled_subscriptions = [
            subscription
            for subscription in subscriptions
            if normalize_subscription_mode(getattr(subscription, "mode", None)) == "scheduled"
            and getattr(subscription, "status", None) == "active"
        ]
        return DashboardSchedulerDiagnostics(
            scheduler_enabled=settings.subscription_scheduler_enabled,
            scheduled_active_total=len(scheduled_subscriptions),
            scheduled_due_total=sum(1 for subscription in scheduled_subscriptions if self._is_due(subscription, now)),
            running_runs_total=self._count(
                select(func.count())
                .select_from(SubscriptionRunModel)
                .where(SubscriptionRunModel.execution_status == "running")
            ),
            default_interval_minutes=settings.subscription_scheduler_default_interval_minutes,
            poll_seconds=settings.subscription_scheduler_poll_seconds,
        )

    def _count(self, statement) -> int:
        return int(self.session.scalar(statement) or 0)

    def _feed_enabled(self, feed: object) -> bool:
        if isinstance(feed, dict):
            return bool(feed.get("enabled", True))
        return bool(getattr(feed, "enabled", True))

    def _has_path_handoff(self, payload: dict | None) -> bool:
        if not isinstance(payload, dict):
            return False
        path_handoff = payload.get("path_handoff")
        if not isinstance(path_handoff, dict):
            return False
        return bool(path_handoff.get("source_path"))

    def _is_due(self, subscription, now: datetime) -> bool:
        baseline = (
            getattr(subscription, "last_run_at", None)
            or getattr(subscription, "updated_at", None)
            or getattr(subscription, "created_at", None)
            or now
        )
        baseline = normalize_timestamp(baseline)
        interval_minutes = self._schedule_interval_minutes(subscription)
        return now >= baseline + timedelta(minutes=interval_minutes)

    def _schedule_interval_minutes(self, subscription) -> int:
        preference_json = getattr(subscription, "preference_json", None) or {}
        value = preference_json.get("schedule_interval_minutes")
        if isinstance(value, int) and value > 0:
            return value
        return settings.subscription_scheduler_default_interval_minutes
