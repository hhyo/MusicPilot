from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.dependencies import get_subscription_execution_service
from app.main import app


class FakeSubscriptionExecutionService:
    def __init__(self) -> None:
        self.execute_calls: list[tuple[str, bool, str | None]] = []
        self.list_runs_calls: list[tuple[str, str | None, int | None]] = []

    def execute(self, subscription_id: str, *, preview_only: bool = False, retry_run_id: str | None = None):
        self.execute_calls.append((subscription_id, preview_only, retry_run_id))
        return {
            "id": "srun-preview",
            "subscription_id": subscription_id,
            "execution_status": "manual_pending",
            "summary_json": {
                "preview_only": preview_only,
                "retry_run_id": retry_run_id,
            },
        }

    def list_runs(
        self,
        subscription_id: str,
        *,
        execution_status: str | None = None,
        limit: int | None = None,
    ):
        normalized_status = getattr(execution_status, "value", execution_status)
        self.list_runs_calls.append((subscription_id, normalized_status, limit))
        return {
            "subscription_id": subscription_id,
            "items": [],
            "total": 0,
        }


class SubscriptionRouteManagementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakeSubscriptionExecutionService()
        app.dependency_overrides[get_subscription_execution_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_subscription_execution_service, None)

    def test_run_route_accepts_preview_only_and_retry_run_id(self) -> None:
        response = self.client.post(
            "/api/v1/plugin/musicpilot/subscriptions/sub-001/run",
            params={
                "preview_only": "true",
                "retry_run_id": "srun-previous",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.execute_calls, [("sub-001", True, "srun-previous")])
        self.assertTrue(response.json()["data"]["summary_json"]["preview_only"])
        self.assertEqual(response.json()["data"]["summary_json"]["retry_run_id"], "srun-previous")

    def test_runs_route_forwards_execution_status_and_limit(self) -> None:
        response = self.client.get(
            "/api/v1/plugin/musicpilot/subscriptions/sub-001/runs",
            params={
                "execution_status": "failed",
                "limit": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.list_runs_calls, [("sub-001", "failed", 2)])
        self.assertEqual(response.json()["data"]["subscription_id"], "sub-001")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
