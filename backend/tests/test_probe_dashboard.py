from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_music_dashboard_chain, get_music_system_chain
from app.main import app
from app.db.models import (
    Base,
    ChartModel,
    DownloadBindingModel,
    OrganizeRecordModel,
    SearchCandidateModel,
    SearchJobModel,
    SubscriptionModel,
    SubscriptionRunModel,
)
from app.chain.dashboard import MusicDashboardChain


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class DummyMusicSystemChain:
    def __init__(self) -> None:
        self._summary = {
            "capability": "health",
            "status": "unverified",
            "host_online": True,
            "capability_available": True,
            "adapter_mode": "host",
            "active_mode": "prefer_host",
            "host_integration_enabled": True,
            "capability_source": "host.probe",
            "verification_state": "unverified",
            "fallback_reason": None,
            "integration_point": "DummyHostCapabilitiesService.health",
            "note": "Health was derived from a real host-backed endpoint.",
            "todo": [],
        }

    def probe_health(self) -> dict:
        return {
            "summary": self._summary,
            "checks": {
                "host_online": True,
                "plugin_api_registered": True,
                "note": "Host health probe completed through configured endpoint.",
            },
            "runtime_state": {"host_integration_enabled": True},
            "validation_matrix_summary": None,
        }

    def list_sites(self) -> dict:
        return {
            "summary": {**self._summary, "capability": "sites"},
            "items": [{"id": "site-1", "name": "Test Site", "enabled": True, "visibility": "observed", "note": "Observed from host endpoint."}],
        }

    def search_summary(self) -> dict:
        return {
            "summary": {**self._summary, "capability": "search"},
            "query_echo": {},
            "sample_result_fields": ["meta_info"],
            "sample_result_count": 1,
        }

    def probe_search(self, payload) -> dict:
        return self.search_summary()

    def list_downloaders(self) -> dict:
        return {
            "summary": {**self._summary, "capability": "downloaders"},
            "items": [{"id": "dl-1", "name": "QB", "is_default": True, "status": "observed", "note": "Observed from host endpoint."}],
        }

    def probe_dispatch(self, payload) -> dict:
        return {
            "summary": {**self._summary, "capability": "dispatch"},
            "request_echo": {},
            "dispatch_preview": {"accepted": True},
        }

    def probe_notify(self, payload) -> dict:
        return {
            "summary": {**self._summary, "capability": "notify", "status": "disabled", "capability_available": False, "fallback_reason": "host_notify_path_missing"},
            "request_echo": {},
            "notification_preview": {"sent": False},
        }

    def config_summary(self) -> dict:
        return {
            "summary": {**self._summary, "capability": "config", "status": "disabled", "capability_available": False, "fallback_reason": "host_config_path_missing"},
            "operation": "summary",
            "request_echo": {},
            "config_preview": {"supported_operations": ["read", "write"], "storage_connected": False},
        }

    def probe_config(self, payload) -> dict:
        return self.config_summary()

    def validation_matrix(self) -> dict | None:
        return {
            "phase": "Phase 8",
            "generated_at": "2026-04-13T00:00:00Z",
            "samples": [],
            "summary": {
                "generated_at": "2026-04-13T00:00:00Z",
                "sample_count": 0,
                "stable_count": 0,
                "single_sample_count": 0,
                "blocked_count": 0,
                "flaky_count": 0,
                "verified_count": 0,
                "unverified_count": 0,
                "placeholder_count": 0,
                "note": "empty",
            },
            "note": "empty",
        }


class ProbeRouteContractTest(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_music_system_chain] = lambda: DummyMusicSystemChain()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_music_system_chain, None)

    def test_probe_health_route_drops_generic_todo_copy(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/probe/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["todo"])
        self.assertIn("诊断", body["note"])
        self.assertEqual(body["data"]["summary"]["status"], "unverified")

    def test_probe_validation_matrix_route_drops_todo_copy(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/probe/validation-matrix")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["todo"])
        self.assertIn("验证矩阵", body["note"])


class DashboardDiagnosticsRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        now = datetime.now(timezone.utc)

        self.session.add_all(
            [
                ChartModel(
                    id="chart-a",
                    chart_source="rss_feed",
                    chart_name="Chart A",
                    chart_type="track",
                    region="Global",
                    category="demo",
                    refresh_hint="hourly",
                    item_count=10,
                    source_updated_at=now - timedelta(hours=3),
                    last_refreshed_at=now - timedelta(hours=3),
                    last_refresh_status="success",
                    last_error=None,
                    stale=True,
                    mock=False,
                    note="live",
                    integration_point="test",
                ),
                ChartModel(
                    id="chart-b",
                    chart_source="rss_feed",
                    chart_name="Chart B",
                    chart_type="track",
                    region="Global",
                    category="demo",
                    refresh_hint="hourly",
                    item_count=10,
                    source_updated_at=now,
                    last_refreshed_at=now,
                    last_refresh_status="error",
                    last_error="rss timeout",
                    stale=False,
                    mock=False,
                    note="live",
                    integration_point="test",
                ),
            ]
        )
        self.session.add_all(
            [
                SubscriptionModel(
                    id="sub-001",
                    subscription_type="artist",
                    target_id="artist-001",
                    target_name="Adele",
                    status="active",
                    mode="scheduled",
                    preference_json={"schedule_interval_minutes": 5},
                    target_payload_json={},
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    last_run_at=now - timedelta(hours=2),
                    mock=False,
                    note="scheduled",
                ),
                SubscriptionModel(
                    id="sub-002",
                    subscription_type="album",
                    target_id="album-001",
                    target_name="25",
                    status="paused",
                    mode="manual",
                    preference_json={},
                    target_payload_json={},
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    mock=False,
                    note="manual",
                ),
            ]
        )
        self.session.add_all(
            [
                SearchJobModel(
                    id="job-running",
                    trigger_source="manual",
                    profile_id="default-lossless",
                    mode="manual",
                    status="running",
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    query_payload={},
                    summary_json={},
                    mock=False,
                    note="running",
                ),
                SearchJobModel(
                    id="job-failed",
                    trigger_source="manual",
                    profile_id="default-lossless",
                    mode="manual",
                    status="failed",
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    query_payload={},
                    summary_json={},
                    mock=False,
                    note="failed",
                ),
                SearchJobModel(
                    id="job-dispatched",
                    trigger_source="manual",
                    profile_id="default-lossless",
                    mode="manual",
                    status="dispatched",
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    query_payload={},
                    summary_json={},
                    mock=False,
                    note="dispatched",
                ),
            ]
        )
        self.session.add_all(
            [
                SearchCandidateModel(
                    id="cand-pending",
                    job_id="job-running",
                    site_id="site-001",
                    site_name="Test Site",
                    title="Adele - Hello",
                    normalized_title="adele hello",
                    decision="pending",
                    dispatch_status="pending",
                    dispatchable=True,
                    raw_payload={},
                    mock=False,
                    note="pending",
                ),
                SearchCandidateModel(
                    id="cand-auto",
                    job_id="job-dispatched",
                    site_id="site-001",
                    site_name="Test Site",
                    title="Adele - Skyfall",
                    normalized_title="adele skyfall",
                    decision="auto_download",
                    dispatch_status="host_submitted",
                    dispatchable=True,
                    raw_payload={},
                    mock=False,
                    note="auto",
                ),
                SearchCandidateModel(
                    id="cand-manual",
                    job_id="job-running",
                    site_id="site-001",
                    site_name="Test Site",
                    title="Adele - Easy On Me",
                    normalized_title="adele easy on me",
                    decision="manual_confirm",
                    dispatch_status="awaiting_manual_confirmation",
                    dispatchable=True,
                    raw_payload={},
                    mock=False,
                    note="manual",
                ),
                SearchCandidateModel(
                    id="cand-rejected",
                    job_id="job-failed",
                    site_id="site-001",
                    site_name="Test Site",
                    title="Adele - Rumour Has It",
                    normalized_title="adele rumour has it",
                    decision="rejected",
                    dispatch_status="failed",
                    dispatchable=False,
                    raw_payload={},
                    mock=False,
                    note="rejected",
                ),
            ]
        )
        self.session.add_all(
            [
                DownloadBindingModel(
                    id="bind-pending",
                    job_id="job-running",
                    candidate_id="cand-pending",
                    target_downloader="QB",
                    downloader_task_id="task-001",
                    dispatchable=True,
                    dispatch_status="host_submitted",
                    mock=False,
                    note="pending",
                    raw_payload={"path_handoff": {"status": "pending_history_sync"}},
                ),
                DownloadBindingModel(
                    id="bind-failed",
                    job_id="job-failed",
                    candidate_id="cand-rejected",
                    target_downloader="QB",
                    downloader_task_id="task-002",
                    dispatchable=True,
                    dispatch_status="failed",
                    mock=False,
                    note="failed",
                    raw_payload={"path_handoff": {"status": "failed", "source_path": "/downloads/a.flac"}},
                ),
                DownloadBindingModel(
                    id="bind-downloaded",
                    job_id="job-dispatched",
                    candidate_id="cand-auto",
                    target_downloader="QB",
                    downloader_task_id="task-003",
                    dispatchable=True,
                    dispatch_status="downloaded",
                    mock=False,
                    note="downloaded",
                    raw_payload={"path_handoff": {"status": "ready", "source_path": "/downloads/b.flac"}},
                ),
            ]
        )
        self.session.add_all(
            [
                OrganizeRecordModel(
                    id="org-preview",
                    binding_id="bind-pending",
                    organizeable=True,
                    organize_status="preview_ready",
                    target_library_path="/library/preview",
                    strategy_note="preview",
                    integration_point="test",
                    mock=False,
                    raw_payload={},
                ),
                OrganizeRecordModel(
                    id="org-apply-pending",
                    binding_id="bind-downloaded",
                    organizeable=True,
                    organize_status="apply_pending",
                    target_library_path="/library/apply",
                    strategy_note="apply",
                    integration_point="test",
                    mock=False,
                    raw_payload={},
                ),
                OrganizeRecordModel(
                    id="org-failed",
                    binding_id="bind-failed",
                    organizeable=False,
                    organize_status="failed",
                    target_library_path="/library/failed",
                    strategy_note="failed",
                    integration_point="test",
                    mock=False,
                    raw_payload={},
                    failure_reason="permission denied",
                ),
            ]
        )
        self.session.add_all(
            [
                SubscriptionRunModel(
                    id="run-running",
                    subscription_id="sub-001",
                    execution_status="running",
                    matched_candidates_count=0,
                    summary_json={},
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    mock=False,
                    note="running",
                ),
                SubscriptionRunModel(
                    id="run-failed",
                    subscription_id="sub-001",
                    execution_status="failed",
                    matched_candidates_count=0,
                    summary_json={},
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    mock=False,
                    note="failed",
                ),
                SubscriptionRunModel(
                    id="run-manual",
                    subscription_id="sub-001",
                    execution_status="manual_pending",
                    matched_candidates_count=1,
                    summary_json={},
                    music_media_input={},
                    music_meta_base={},
                    music_recognition_assessment={},
                    music_media_info={},
                    mock=False,
                    note="manual",
                ),
            ]
        )
        self.session.commit()

        app.dependency_overrides[get_music_dashboard_chain] = lambda: MusicDashboardChain(session=self.session)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_music_dashboard_chain, None)

    def test_dashboard_summary_exposes_runtime_ops_blocks(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/dashboard/summary")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        provider = body["data"]["provider"]
        search = body["data"]["search"]
        downloads = body["data"]["downloads"]
        handoff = body["data"]["handoff"]
        organize = body["data"]["organize"]
        scheduler = body["data"]["scheduler"]

        self.assertEqual(provider["chart_runtime_total"], 2)
        self.assertEqual(provider["chart_runtime_stale_total"], 1)
        self.assertEqual(provider["chart_runtime_failed_total"], 1)
        self.assertIn("host_verification_state", provider)

        self.assertEqual(search["jobs_failed"], 1)
        self.assertEqual(search["jobs_dispatched"], 1)
        self.assertEqual(search["candidates_manual_confirm"], 1)
        self.assertEqual(search["candidates_rejected"], 1)

        self.assertEqual(downloads["bindings_failed"], 1)
        self.assertEqual(downloads["bindings_downloaded"], 1)
        self.assertEqual(downloads["bindings_manual_confirmation"], 0)

        self.assertEqual(handoff["handoff_pending_total"], 1)
        self.assertEqual(handoff["handoff_failed_total"], 1)
        self.assertEqual(handoff["handoff_ready_total"], 1)

        self.assertEqual(organize["organize_apply_pending"], 1)
        self.assertEqual(organize["organize_failed"], 1)

        self.assertEqual(scheduler["failed_runs_total"], 1)
        self.assertEqual(scheduler["manual_pending_runs_total"], 1)


if __name__ == "__main__":
    unittest.main()
