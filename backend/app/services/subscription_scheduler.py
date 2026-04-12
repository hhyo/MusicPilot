"""Minimal in-process subscription scheduler."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from ..schemas.orchestration import (
    SubscriptionSchedulerDiagnostic,
    SubscriptionSchedulerRunResult,
    SubscriptionSchedulerSummary,
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
                        error_message=str(exc),
                    )
                )

        handoff_reconcile = {
            "applied_run_ids": [],
            "unresolved_run_ids": [],
            "skipped_record_ids": [],
        }
        if self.reconcile_pending_handoffs is not None:
            handoff_reconcile = self.reconcile_pending_handoffs()

        summary = SubscriptionSchedulerSummary(
            considered=considered,
            executed=len(executed_ids),
            skipped=len(skipped_ids),
            errors=len(errors),
            handoff_applied=len(handoff_reconcile.get("applied_run_ids", [])),
            handoff_unresolved=len(handoff_reconcile.get("unresolved_run_ids", [])),
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
        )
        return report.model_dump(mode="json")
