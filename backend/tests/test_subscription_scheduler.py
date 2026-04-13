"""Tests for the minimal in-process subscription scheduler."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.subscription_scheduler import SubscriptionSchedulerService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FakeRepository:
    def __init__(self, subscriptions, *, running_ids=None, latest_runs=None):
        self._subscriptions = subscriptions
        self.running_ids = running_ids or set()
        self.latest_runs = latest_runs or {}

    def list_subscriptions(self, *, subscription_type=None, status=None):  # noqa: ANN001
        assert subscription_type is None
        if status is None:
            return list(self._subscriptions)
        return [item for item in self._subscriptions if item.status == status]

    def has_running_run(self, subscription_id: str) -> bool:
        return subscription_id in self.running_ids

    def get_latest_run(self, subscription_id: str):
        return self.latest_runs.get(subscription_id)


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
        self.assertEqual(result["summary"]["executed"], 1)
        self.assertEqual(result["reason_counts"]["executed"], 1)
        self.assertTrue(result["diagnostics"][0]["due"])
        self.assertIn("started_at", result["window"])
        self.assertIn("finished_at", result["window"])

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
        self.assertEqual(result["reason_counts"]["not_scheduled"], 1)

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
        self.assertEqual(result["reason_counts"]["running"], 1)

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
        self.assertGreaterEqual(result["summary"]["considered"], 1)

    def test_run_pending_once_also_reconciles_pending_handoffs(self) -> None:
        reconciled = {
            "summary": {
                "applied": 1,
                "pending": 0,
                "unresolved": 0,
                "failed": 0,
                "skipped": 0,
            },
            "applied_run_ids": ["srun-1"],
            "unresolved_run_ids": [],
            "skipped_record_ids": [],
            "diagnostics": [],
        }
        service = SubscriptionSchedulerService(
            repository=FakeRepository([]),
            execute_subscription=lambda subscription_id: None,
            default_interval_minutes=360,
            reconcile_pending_handoffs=lambda: reconciled,
        )

        result = service.run_pending_once(now=utc_now())

        self.assertEqual(result["handoff_reconcile"]["summary"]["applied"], 1)
        self.assertEqual(result["summary"]["handoff_applied"], 1)
        self.assertEqual(result["task_boundary"]["scheduler_mode"], "in_process_polling")

    def test_recent_completed_run_is_duplicate_guarded(self) -> None:
        executed_ids: list[str] = []
        now = utc_now()
        subscription = SimpleNamespace(
            id="sub-1",
            status="active",
            mode="scheduled",
            preference_json={"schedule_interval_minutes": 30},
            last_run_at=now - timedelta(minutes=90),
            updated_at=now - timedelta(minutes=120),
            created_at=now - timedelta(minutes=180),
        )
        latest_run = SimpleNamespace(
            id="srun-1",
            execution_status="applied",
            finished_at=now - timedelta(minutes=5),
        )
        service = SubscriptionSchedulerService(
            repository=FakeRepository([subscription], latest_runs={"sub-1": latest_run}),
            execute_subscription=lambda subscription_id: executed_ids.append(subscription_id),
            default_interval_minutes=360,
        )

        result = service.run_pending_once(now=now)

        self.assertEqual(executed_ids, [])
        self.assertEqual(result["reason_counts"]["duplicate_guard"], 1)
        self.assertEqual(result["diagnostics"][0]["recent_run_id"], "srun-1")
        self.assertIsNotNone(result["diagnostics"][0]["duplicate_guard_until"])

    def test_recent_failed_run_waits_for_retry_window(self) -> None:
        executed_ids: list[str] = []
        now = utc_now()
        subscription = SimpleNamespace(
            id="sub-1",
            status="active",
            mode="scheduled",
            preference_json={
                "schedule_interval_minutes": 30,
                "scheduler_retry_window_minutes": 20,
            },
            last_run_at=now - timedelta(minutes=90),
            updated_at=now - timedelta(minutes=120),
            created_at=now - timedelta(minutes=180),
        )
        latest_run = SimpleNamespace(
            id="srun-1",
            execution_status="failed",
            finished_at=now - timedelta(minutes=5),
        )
        service = SubscriptionSchedulerService(
            repository=FakeRepository([subscription], latest_runs={"sub-1": latest_run}),
            execute_subscription=lambda subscription_id: executed_ids.append(subscription_id),
            default_interval_minutes=360,
        )

        result = service.run_pending_once(now=now)

        self.assertEqual(executed_ids, [])
        self.assertEqual(result["reason_counts"]["retry_window"], 1)
        self.assertEqual(result["diagnostics"][0]["recent_run_status"], "failed")
        self.assertIsNotNone(result["diagnostics"][0]["retry_eligible_at"])
