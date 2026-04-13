"""Minimal in-process subscription scheduler."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from ..schemas.orchestration import (
    PendingHandoffReconcileResult,
    SubscriptionSchedulerDiagnostic,
    SubscriptionSchedulerRunResult,
    SubscriptionSchedulerSummary,
    SubscriptionSchedulerTaskBoundary,
    SubscriptionSchedulerWindow,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_timestamp(value: datetime, *, default_tz: timezone = timezone.utc) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=default_tz)
    return value.astimezone(default_tz)


def normalize_subscription_mode(value: str | None) -> str:
    return value or "manual"


class SubscriptionSchedulerService:
    def __init__(
        self,
        *,
        repository,
        execute_subscription: Callable[[str], Any],
        default_interval_minutes: int,
        reconcile_pending_handoffs: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self.repository = repository
        self.execute_subscription = execute_subscription
        self.default_interval_minutes = default_interval_minutes
        self.reconcile_pending_handoffs = reconcile_pending_handoffs

    def schedule_interval_minutes(self, subscription) -> int:
        preference_json = getattr(subscription, "preference_json", None) or {}
        value = preference_json.get("schedule_interval_minutes")
        if isinstance(value, int) and value > 0:
            return value
        return self.default_interval_minutes

    def _next_run_at(self, subscription, now: datetime) -> datetime:
        baseline = (
            getattr(subscription, "last_run_at", None)
            or getattr(subscription, "updated_at", None)
            or getattr(subscription, "created_at", None)
            or now
        )
        baseline = normalize_timestamp(baseline)
        return baseline + timedelta(minutes=self.schedule_interval_minutes(subscription))

    def _skip_reason(self, subscription, now: datetime) -> str | None:
        if normalize_subscription_mode(getattr(subscription, "mode", None)) != "scheduled":
            return "not_scheduled"
        if getattr(subscription, "status", None) != "active":
            return "inactive"
        if self.repository.has_running_run(subscription.id):
            return "running"
        latest_run = getattr(self.repository, "get_latest_run", lambda _subscription_id: None)(subscription.id)
        if latest_run is not None:
            latest_status = str(getattr(latest_run, "execution_status", "") or "")
            finished_at = getattr(latest_run, "finished_at", None)
            if finished_at is not None:
                finished_at = normalize_timestamp(finished_at)
                if latest_status == "failed":
                    if now < self._retry_eligible_at(subscription, finished_at):
                        return "retry_window"
                elif now < self._duplicate_guard_until(subscription, finished_at):
                    return "duplicate_guard"
        if now < self._next_run_at(subscription, now):
            return "not_due"
        return None

    def is_due(self, subscription, now: datetime) -> bool:
        return self._skip_reason(subscription, now) is None

    def run_pending_once(self, *, now: datetime | None = None) -> dict[str, Any]:
        current_time = normalize_timestamp(now or utc_now())
        executed_ids: list[str] = []
        skipped_ids: list[str] = []
        errors: dict[str, str] = {}
        diagnostics: list[SubscriptionSchedulerDiagnostic] = []
        reason_counts: dict[str, int] = {}
        considered = 0

        for subscription in self.repository.list_subscriptions(status="active"):
            considered += 1
            normalized_mode = normalize_subscription_mode(getattr(subscription, "mode", None))
            interval_minutes = self.schedule_interval_minutes(subscription)
            next_run_at = self._next_run_at(subscription, current_time)
            latest_run = getattr(self.repository, "get_latest_run", lambda _subscription_id: None)(subscription.id)
            recent_run_id = getattr(latest_run, "id", None)
            recent_run_status = getattr(latest_run, "execution_status", None)
            finished_at = getattr(latest_run, "finished_at", None)
            duplicate_guard_until = None
            retry_eligible_at = None
            if finished_at is not None:
                normalized_finished_at = normalize_timestamp(finished_at)
                if recent_run_status == "failed":
                    retry_eligible_at = self._retry_eligible_at(subscription, normalized_finished_at)
                else:
                    duplicate_guard_until = self._duplicate_guard_until(subscription, normalized_finished_at)
            reason = self._skip_reason(subscription, current_time)
            if reason is not None:
                skipped_ids.append(subscription.id)
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                diagnostics.append(
                    SubscriptionSchedulerDiagnostic(
                        subscription_id=subscription.id,
                        mode=normalized_mode,
                        status=getattr(subscription, "status", "unknown"),
                        reason=reason,
                        due=False,
                        interval_minutes=interval_minutes,
                        last_run_at=getattr(subscription, "last_run_at", None),
                        next_run_at=next_run_at,
                        recent_run_id=recent_run_id,
                        recent_run_status=recent_run_status,
                        duplicate_guard_until=duplicate_guard_until,
                        retry_eligible_at=retry_eligible_at,
                    )
                )
                continue
            try:
                self.execute_subscription(subscription.id)
                executed_ids.append(subscription.id)
                reason_counts["executed"] = reason_counts.get("executed", 0) + 1
                diagnostics.append(
                    SubscriptionSchedulerDiagnostic(
                        subscription_id=subscription.id,
                        mode=normalized_mode,
                        status=getattr(subscription, "status", "unknown"),
                        reason="executed",
                        due=True,
                        interval_minutes=interval_minutes,
                        last_run_at=getattr(subscription, "last_run_at", None),
                        next_run_at=next_run_at,
                        recent_run_id=recent_run_id,
                        recent_run_status=recent_run_status,
                        duplicate_guard_until=duplicate_guard_until,
                        retry_eligible_at=retry_eligible_at,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors[subscription.id] = str(exc)
                reason_counts["error"] = reason_counts.get("error", 0) + 1
                diagnostics.append(
                    SubscriptionSchedulerDiagnostic(
                        subscription_id=subscription.id,
                        mode=normalized_mode,
                        status=getattr(subscription, "status", "unknown"),
                        reason="error",
                        due=True,
                        interval_minutes=interval_minutes,
                        last_run_at=getattr(subscription, "last_run_at", None),
                        next_run_at=next_run_at,
                        recent_run_id=recent_run_id,
                        recent_run_status=recent_run_status,
                        duplicate_guard_until=duplicate_guard_until,
                        retry_eligible_at=retry_eligible_at,
                        error_message=str(exc),
                    )
                )

        handoff_reconcile = PendingHandoffReconcileResult()
        if self.reconcile_pending_handoffs is not None:
            handoff_reconcile = PendingHandoffReconcileResult.model_validate(self.reconcile_pending_handoffs())

        summary = SubscriptionSchedulerSummary(
            considered=considered,
            executed=len(executed_ids),
            skipped=len(skipped_ids),
            errors=len(errors),
            handoff_applied=handoff_reconcile.summary.applied,
            handoff_unresolved=handoff_reconcile.summary.unresolved,
        )
        finished_at = utc_now()
        window = SubscriptionSchedulerWindow(
            started_at=current_time,
            finished_at=finished_at,
            duration_seconds=max(0.0, (finished_at - current_time).total_seconds()),
        )
        report = SubscriptionSchedulerRunResult(
            executed_ids=executed_ids,
            skipped_ids=skipped_ids,
            error_ids=list(errors.keys()),
            errors=errors,
            summary=summary,
            reason_counts=reason_counts,
            window=window,
            diagnostics=diagnostics,
            handoff_reconcile=handoff_reconcile,
            task_boundary=SubscriptionSchedulerTaskBoundary(),
        )
        return report.model_dump(mode="json")

    def _retry_window_minutes(self, subscription) -> int:
        preference_json = getattr(subscription, "preference_json", None) or {}
        value = preference_json.get("scheduler_retry_window_minutes")
        if isinstance(value, int) and value > 0:
            return value
        return self.schedule_interval_minutes(subscription)

    def _duplicate_guard_until(self, subscription, finished_at: datetime) -> datetime:
        return finished_at + timedelta(minutes=self.schedule_interval_minutes(subscription))

    def _retry_eligible_at(self, subscription, finished_at: datetime) -> datetime:
        return finished_at + timedelta(minutes=self._retry_window_minutes(subscription))
