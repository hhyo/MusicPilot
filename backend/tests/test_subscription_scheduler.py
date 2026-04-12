"""Tests for the minimal in-process subscription scheduler."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.subscription_scheduler import SubscriptionSchedulerService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FakeRepository:
    def __init__(self, subscriptions, *, running_ids=None):
        self._subscriptions = subscriptions
        self.running_ids = running_ids or set()

    def list_subscriptions(self, *, subscription_type=None, status=None):  # noqa: ANN001
        assert subscription_type is None
        if status is None:
            return list(self._subscriptions)
        return [item for item in self._subscriptions if item.status == status]

    def has_running_run(self, subscription_id: str) -> bool:
        return subscription_id in self.running_ids


class SubscriptionSchedulerServiceTest(unittest.TestCase):
    def test_due_scheduled_subscription_executes_once(self) -> None:
        executed_ids: list[str] = []
        subscription = SimpleNamespace(
            id="sub-1",
            status="active",
            mode="scheduled",
            preference_json={"schedule_interval_minutes": 30},
            last_run_at=utc_now() - timedelta(minutes=31),
            updated_at=utc_now() - timedelta(minutes=60),
            created_at=utc_now() - timedelta(minutes=90),
        )
        service = SubscriptionSchedulerService(
            repository=FakeRepository([subscription]),
            execute_subscription=lambda subscription_id: executed_ids.append(subscription_id),
            default_interval_minutes=360,
        )

        result = service.run_pending_once(now=utc_now())

        self.assertEqual(executed_ids, ["sub-1"])
        self.assertEqual(result["executed_ids"], ["sub-1"])

    def test_manual_subscription_is_ignored(self) -> None:
        executed_ids: list[str] = []
        subscription = SimpleNamespace(
            id="sub-1",
            status="active",
            mode="manual",
            preference_json={"schedule_interval_minutes": 30},
            last_run_at=None,
            updated_at=utc_now() - timedelta(minutes=60),
            created_at=utc_now() - timedelta(minutes=90),
        )
        service = SubscriptionSchedulerService(
            repository=FakeRepository([subscription]),
            execute_subscription=lambda subscription_id: executed_ids.append(subscription_id),
            default_interval_minutes=360,
        )

        result = service.run_pending_once(now=utc_now())

        self.assertEqual(executed_ids, [])
        self.assertEqual(result["executed_ids"], [])

    def test_running_subscription_is_ignored(self) -> None:
        executed_ids: list[str] = []
        subscription = SimpleNamespace(
            id="sub-1",
            status="active",
            mode="scheduled",
            preference_json={"schedule_interval_minutes": 30},
            last_run_at=utc_now() - timedelta(minutes=31),
            updated_at=utc_now() - timedelta(minutes=60),
            created_at=utc_now() - timedelta(minutes=90),
        )
        service = SubscriptionSchedulerService(
            repository=FakeRepository([subscription], running_ids={"sub-1"}),
            execute_subscription=lambda subscription_id: executed_ids.append(subscription_id),
            default_interval_minutes=360,
        )

        result = service.run_pending_once(now=utc_now())

        self.assertEqual(executed_ids, [])
        self.assertEqual(result["executed_ids"], [])

    def test_naive_sqlite_timestamp_is_normalized(self) -> None:
        executed_ids: list[str] = []
        subscription = SimpleNamespace(
            id="sub-1",
            status="active",
            mode="scheduled",
            preference_json={"schedule_interval_minutes": 30},
            last_run_at=None,
            updated_at=(utc_now() - timedelta(minutes=31)).replace(tzinfo=None),
            created_at=(utc_now() - timedelta(minutes=90)).replace(tzinfo=None),
        )
        service = SubscriptionSchedulerService(
            repository=FakeRepository([subscription]),
            execute_subscription=lambda subscription_id: executed_ids.append(subscription_id),
            default_interval_minutes=360,
        )

        result = service.run_pending_once(now=utc_now())

        self.assertEqual(executed_ids, ["sub-1"])
        self.assertEqual(result["executed_ids"], ["sub-1"])

    def test_run_pending_once_also_reconciles_pending_handoffs(self) -> None:
        reconciled = {"applied_run_ids": ["srun-1"], "unresolved_run_ids": [], "skipped_record_ids": []}
        service = SubscriptionSchedulerService(
            repository=FakeRepository([]),
            execute_subscription=lambda subscription_id: None,
            default_interval_minutes=360,
            reconcile_pending_handoffs=lambda: reconciled,
        )

        result = service.run_pending_once(now=utc_now())

        self.assertEqual(result["handoff_reconcile"], reconciled)
