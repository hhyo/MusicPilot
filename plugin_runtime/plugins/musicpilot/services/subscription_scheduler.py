"""Minimal in-process subscription scheduler."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_timestamp(value: datetime, *, default_tz: timezone = timezone.utc) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=default_tz)
    return value.astimezone(default_tz)


def normalize_subscription_mode(value: str | None) -> str:
    if value == "scheduled_placeholder":
        return "scheduled"
    return value or "manual"


class SubscriptionSchedulerService:
    def __init__(
        self,
        *,
        repository,
        execute_subscription: Callable[[str], Any],
        default_interval_minutes: int,
    ) -> None:
        self.repository = repository
        self.execute_subscription = execute_subscription
        self.default_interval_minutes = default_interval_minutes

    def schedule_interval_minutes(self, subscription) -> int:
        preference_json = getattr(subscription, "preference_json", None) or {}
        value = preference_json.get("schedule_interval_minutes")
        if isinstance(value, int) and value > 0:
            return value
        return self.default_interval_minutes

    def is_due(self, subscription, now: datetime) -> bool:
        if normalize_subscription_mode(getattr(subscription, "mode", None)) != "scheduled":
            return False
        if getattr(subscription, "status", None) != "active":
            return False
        if self.repository.has_running_run(subscription.id):
            return False

        baseline = (
            getattr(subscription, "last_run_at", None)
            or getattr(subscription, "updated_at", None)
            or getattr(subscription, "created_at", None)
            or now
        )
        baseline = normalize_timestamp(baseline)
        interval_minutes = self.schedule_interval_minutes(subscription)
        return now >= baseline + timedelta(minutes=interval_minutes)

    def run_pending_once(self, *, now: datetime | None = None) -> dict[str, Any]:
        current_time = now or utc_now()
        executed_ids: list[str] = []
        skipped_ids: list[str] = []
        errors: dict[str, str] = {}

        for subscription in self.repository.list_subscriptions(status="active"):
            normalized_mode = normalize_subscription_mode(getattr(subscription, "mode", None))
            if normalized_mode != "scheduled":
                continue
            if not self.is_due(subscription, current_time):
                skipped_ids.append(subscription.id)
                continue
            try:
                self.execute_subscription(subscription.id)
                executed_ids.append(subscription.id)
            except Exception as exc:  # noqa: BLE001
                errors[subscription.id] = str(exc)

        return {
            "executed_ids": executed_ids,
            "skipped_ids": skipped_ids,
            "error_ids": list(errors.keys()),
            "errors": errors,
        }
