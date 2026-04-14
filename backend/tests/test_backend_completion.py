from __future__ import annotations

import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.dependencies import (
    get_music_download_chain,
    get_music_dashboard_chain,
    get_music_search_chain,
    get_music_system_chain,
    get_music_transfer_chain,
)
from app.chain.download import MusicDownloadChain
from app.chain.system import MusicSystemChain
from app.chain.transfer import MusicTransferChain
from app.main import app
from app.db.models import (
    AppSettingModel,
    Base,
    DownloadBindingModel,
    OrganizeRecordModel,
    SearchCandidateModel,
    SearchJobModel,
    SubscriptionModel,
)
from app.schemas.acquisition import SearchJobSummary
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMetaBase,
    MusicRecognitionAssessment,
)
from app.schemas.shared import AudioProfile, RuleProfile
from app.schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeConflictPolicy,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)
from app.chain.dashboard import MusicDashboardChain
from app.helper.settings import SettingsHelper


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class DashboardRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)

        self.session.add(
            SubscriptionModel(
                id="sub-001",
                subscription_type="artist",
                target_id="artist-001",
                target_name="Adele",
                status="active",
                mode="manual",
                preference_json={},
                target_payload_json={},
                music_media_input={},
                music_meta_base={},
                music_recognition_assessment={},
                music_media_info={},
                mock=False,
                note="test",
            )
        )
        self.session.add(
            SubscriptionModel(
                id="sub-002",
                subscription_type="album",
                target_id="album-001",
                target_name="25",
                status="active",
                mode="scheduled",
                preference_json={"schedule_interval_minutes": 5},
                target_payload_json={},
                music_media_input={},
                music_meta_base={},
                music_recognition_assessment={},
                music_media_info={},
                latest_run_status="queued",
                last_run_at=datetime.now(timezone.utc) - timedelta(hours=1),
                mock=False,
                note="scheduled",
            )
        )
        self.session.add(
            SearchJobModel(
                id="job-001",
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
                note="test",
            )
        )
        self.session.add(
            SearchCandidateModel(
                id="cand-001",
                job_id="job-001",
                site_id="site-001",
                site_name="Test Site",
                title="Adele - Hello",
                normalized_title="adele hello",
                decision="pending",
                raw_payload={},
                mock=False,
                note="test",
            )
        )
        self.session.add(
            DownloadBindingModel(
                id="bind-001",
                job_id="job-001",
                candidate_id="cand-001",
                target_downloader="QB",
                downloader_task_id="task-001",
                dispatchable=True,
                dispatch_status="host_submitted",
                mock=False,
                note="test",
                raw_payload={},
            )
        )
        self.session.add(
            OrganizeRecordModel(
                id="org-001",
                organizeable=False,
                organize_status="failed",
                target_library_path="/library/music/Adele",
                strategy_note="failed",
                integration_point="test",
                mock=False,
                raw_payload={},
            )
        )
        self.session.commit()

        self.chain = MusicDashboardChain(session=self.session)
        app.dependency_overrides[get_music_dashboard_chain] = lambda: self.chain
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_music_dashboard_chain, None)

    def test_dashboard_summary_returns_real_aggregated_counts(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/dashboard/summary")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["mock"])
        self.assertEqual(body["data"]["provider"]["chart_provider_mode"], "mock")
        self.assertEqual(body["data"]["provider"]["metadata_provider_mode"], "seed")
        self.assertEqual(body["data"]["discovery"]["subscriptions_total"], 2)
        self.assertEqual(body["data"]["discovery"]["jobs_running"], 1)
        self.assertEqual(body["data"]["handoff"]["downloads_pending"], 1)
        self.assertEqual(body["data"]["organize"]["organize_failed"], 1)
        self.assertEqual(body["data"]["scheduler"]["scheduled_active_total"], 1)
        self.assertEqual(body["data"]["scheduler"]["scheduled_due_total"], 1)


class SettingsProfilesRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.env_settings = SimpleNamespace(
            chart_provider_mode="mock",
            chart_rss_feeds=[],
            metadata_provider_mode="seed",
        )
        self.chain = MusicSystemChain(
            settings_helper=SettingsHelper(session=self.session, env_settings=self.env_settings),
            host_probe=None,
            host_integration=None,
            validation_matrix=None,
        )
        app.dependency_overrides[get_music_system_chain] = lambda: self.chain
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_music_system_chain, None)

    def test_get_rule_profiles_returns_real_defaults(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/settings/profiles")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["mock"])
        self.assertEqual(body["data"][0]["id"], "default-lossless")

    def test_put_rule_profile_persists_profile(self) -> None:
        payload = {
            "id": "default-hires",
            "name": "Default Hi-Res",
            "audio_profiles": ["flac", "hires"],
            "allow_live": True,
            "allow_remaster": True,
            "auto_download_threshold": 96.0,
            "manual_confirm_threshold": 82.0,
        }

        put_response = self.client.put("/api/v1/plugin/musicpilot/settings/profiles", json=payload)
        get_response = self.client.get("/api/v1/plugin/musicpilot/settings/profiles")

        self.assertEqual(put_response.status_code, 200)
        self.assertFalse(put_response.json()["mock"])
        self.assertEqual(put_response.json()["data"]["id"], "default-hires")
        self.assertEqual(
            [item["id"] for item in self.session.get(AppSettingModel, "rule_profiles").value_json],
            ["default-lossless", "default-hires"],
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual([item["id"] for item in get_response.json()["data"]], ["default-lossless", "default-hires"])


class DownloadsWorkspaceRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.session.add(
            SearchJobModel(
                id="job-001",
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
                note="test",
            )
        )
        self.session.add(
            SearchCandidateModel(
                id="cand-001",
                job_id="job-001",
                site_id="site-001",
                site_name="Test Site",
                title="Adele - Hello",
                normalized_title="adele hello",
                decision="auto_download",
                dispatch_status="host_submitted",
                dispatchable=True,
                raw_payload={
                    "adapter_resolution": {
                        "adapter_key": "real_host_search",
                        "adapter_mode": "host",
                        "capability_source": "settings.mode.prefer_host",
                    }
                },
                mock=False,
                note="candidate",
            )
        )
        self.session.add(
            DownloadBindingModel(
                id="bind-001",
                job_id="job-001",
                candidate_id="cand-001",
                target_downloader="QB",
                downloader_task_id="task-001",
                dispatchable=True,
                dispatch_status="host_submitted",
                mock=False,
                note="binding",
                integration_point="DispatchService.dispatch",
                raw_payload={
                    "path_handoff": {
                        "download_hash": "task-001",
                        "source_path": "/downloads/Adele - Hello.flac",
                        "source_filetype": "file",
                        "handoff_source": "history_download",
                        "handoff_status": "resolved",
                        "verification_state": "verified",
                        "note": "resolved",
                        "raw_summary": {},
                    },
                    "host_response_summary": {"download_id": "task-001"},
                },
            )
        )
        self.session.commit()

        self.chain = MusicDownloadChain(session=self.session, resolver=SimpleNamespace())
        app.dependency_overrides[get_music_download_chain] = lambda: self.chain
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_music_download_chain, None)

    def test_list_download_bindings_supports_filters(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/downloads/bindings", params={"job_id": "job-001"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["mock"])
        self.assertEqual(body["data"]["total"], 1)
        self.assertEqual(body["data"]["items"][0]["id"], "bind-001")

    def test_get_download_binding_detail_returns_candidate_and_handoff(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/downloads/bindings/bind-001")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["mock"])
        self.assertEqual(body["data"]["id"], "bind-001")
        self.assertEqual(body["data"]["candidate"]["id"], "cand-001")
        self.assertEqual(body["data"]["path_handoff"]["download_hash"], "task-001")


class FakeJobManagementService:
    def __init__(self) -> None:
        self.retried: list[str] = []
        self.deleted: list[str] = []

    def retry_job(self, job_id: str):
        self.retried.append(job_id)
        return SearchJobSummary(
            id=job_id,
            music_media_input=MusicMediaInput(source_kind="manual"),
            music_meta_base=MusicMetaBase(entity_type="track", evidence=[]),
            music_recognition_assessment=MusicRecognitionAssessment(state="ready", note="retry"),
            music_media_info=MusicMediaInfo(
                entity_type="track",
                provider="musicbrainz",
                provider_id="recording-hello",
                title="Hello",
                artist_names=["Adele"],
                match_strategy="strong_ref",
                match_confidence=1.0,
                match_evidence=[],
                diagnostics=[],
                external_refs={},
                album_artist_names=[],
                related_artist_ids=[],
                related_track_ids=[],
            ),
            trigger_source="manual",
            profile_id="default-lossless",
            mode="manual",
            status="matched",
            created_at="2026-04-12T00:00:00Z",
            updated_at="2026-04-12T00:00:00Z",
            mock=False,
            note="retry",
            summary={},
        )

    def delete_job(self, job_id: str):
        self.deleted.append(job_id)
        return {"id": job_id, "deleted": True}


class JobsManagementRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakeJobManagementService()
        app.dependency_overrides[get_music_search_chain] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_music_search_chain, None)

    def test_retry_job_route_is_available(self) -> None:
        response = self.client.post("/api/v1/plugin/musicpilot/jobs/job-001/retry")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.retried, ["job-001"])

    def test_delete_job_route_is_available(self) -> None:
        response = self.client.delete("/api/v1/plugin/musicpilot/jobs/job-001")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.deleted, ["job-001"])
        self.assertEqual(response.json()["data"]["deleted"], True)


class OrganizeManagementTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)

        self.session.add(
            SearchJobModel(
                id="job-org",
                trigger_source="manual",
                profile_id="default-lossless",
                mode="manual",
                status="matched",
                music_media_input={},
                music_meta_base={},
                music_recognition_assessment={},
                music_media_info={},
                query_payload={},
                summary_json={},
                mock=False,
                note="job",
            )
        )
        self.session.add(
            SearchCandidateModel(
                id="cand-org",
                job_id="job-org",
                site_id="site-org",
                site_name="Organize Site",
                title="Adele - Hello",
                normalized_title="adele hello",
                decision="auto_download",
                dispatch_status="host_submitted",
                dispatchable=True,
                raw_payload={},
                mock=False,
                note="candidate",
            )
        )

        self.session.add(
            OrganizeRecordModel(
                id="org-failed",
                search_job_id="job-org",
                candidate_id="cand-org",
                organizeable=False,
                organize_status="failed",
                target_library_path="/library/music/Adele",
                strategy_note="failed",
                integration_point="test",
                mock=False,
                raw_payload={
                    "strategy": "music_default_layout",
                    "strategy_snapshot": {
                        "strategy_name": "music_default_layout",
                        "library_type": "music",
                        "root_path": "/library/music",
                        "artist_dir_template": "{artist_name}",
                        "album_dir_template": "{artist_name}/{year} - {album_title}",
                        "track_file_template": "{track_title}.{format_ext}",
                        "conflict_policy": "skip_existing",
                        "template_note": "test",
                    },
                    "target_library_path": "/library/music/Adele",
                    "target_relative_path": "Adele",
                    "strategy_note": "failed",
                },
            )
        )
        self.session.commit()

        apply_result = OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy="music_default_layout",
            strategy_snapshot=OrganizeStrategySnapshot(
                strategy_name="music_default_layout",
                library_type="music",
                root_path="/library/music",
                artist_dir_template="{artist_name}",
                album_dir_template="{artist_name}/{year} - {album_title}",
                track_file_template="{track_title}.{format_ext}",
                conflict_policy=OrganizeConflictPolicy.SKIP_EXISTING,
                template_note="test",
            ),
            organize_status=OrganizeStatus.APPLIED,
            target_library_path="/library/music/Adele",
            target_relative_path="Adele",
            strategy_note="applied",
            integration_point="DummyApplyResolver.apply",
            verification_state=VerificationState.UNVERIFIED,
            mock=True,
            note="applied",
        )

        class DummyApplyResolver:
            def preview(self, **kwargs):  # pragma: no cover
                raise NotImplementedError

            def apply(self, **kwargs):
                return SimpleNamespace(result=apply_result, resolution=None)

        class DummyMusicMediaChain:
            def hydrate(self, media):  # pragma: no cover
                return None

        self.service = MusicTransferChain(
            session=self.session,
            resolver=DummyApplyResolver(),
            strategy_service=SimpleNamespace(build_plan=lambda **kwargs: None),
            path_handoff_service=SimpleNamespace(),
            music_media_chain=DummyMusicMediaChain(),
        )

    def tearDown(self) -> None:
        self.session.close()

    def test_list_records_supports_status_filter(self) -> None:
        result = self.service.list_records(status="failed")

        self.assertEqual(result.total, 1)
        self.assertEqual(result.items[0].id, "org-failed")

    def test_retry_record_reapplies_existing_record(self) -> None:
        result = self.service.retry("org-failed")

        self.assertEqual(result.id, "org-failed")
        self.assertEqual(result.organize_status, OrganizeStatus.APPLIED)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
