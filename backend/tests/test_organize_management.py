from __future__ import annotations

import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_organize_service
from app.main import app
from app.models import Base, DownloadBindingModel, OrganizeRecordModel, SearchCandidateModel, SearchJobModel
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.music_media import MusicMediaInfo
from app.schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeConflictPolicy,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)
from app.services.host_integration import OrganizeExecutionResult
from app.services.organize import OrganizeService
from app.services.organize_strategy import OrganizeStrategyService
from app.repositories.orchestration import OrchestrationRepository

from tests.test_organize_integration import DummyMockOrganizeAdapter
from tests.test_query_builder import build_track_detail, build_track_media


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class DummyMusicMediaChain:
    def __init__(self) -> None:
        self.calls: list[MusicMediaInfo] = []

    def hydrate(self, media: MusicMediaInfo):
        self.calls.append(media)
        return build_track_detail()


class CapturingPreviewResolver:
    def __init__(self, result: OrganizeAdapterResult):
        self.result = result
        self.preview_calls: list[dict[str, object]] = []
        self.apply_calls: list[dict[str, object]] = []

    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):
        self.preview_calls.append(
            {
                "candidate": candidate,
                "metadata_detail": metadata_detail,
                "binding_id": binding_id,
                "plan": plan,
            }
        )
        return OrganizeExecutionResult(result=self.result, resolution=self.result.adapter_resolution)

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):  # pragma: no cover
        self.apply_calls.append(
            {
                "organize_job_id": organize_job_id,
                "candidate": candidate,
                "metadata_detail": metadata_detail,
                "binding_id": binding_id,
                "plan": plan,
            }
        )
        return OrganizeExecutionResult(result=self.result, resolution=self.result.adapter_resolution)


class RepairingPathHandoffService:
    def resolve_from_download_with_retry(self, download_hash: str | None):  # noqa: ANN001
        if download_hash != "stub-download-001":
            return None
        from app.schemas.acquisition import PathHandoffInfo

        return PathHandoffInfo(
            download_hash=download_hash,
            source_path="/downloads/Adele/2015 - 25/01 - Hello.flac",
            source_filetype="file",
            source_name="01 - Hello.flac",
            source_basename="01 - Hello",
            source_extension="flac",
            handoff_source="moviepilot.runtime.history.download",
            handoff_status="resolved_from_history_download",
            verification_state=VerificationState.VERIFIED,
            note="resolved",
            raw_summary={"download_hash": download_hash},
        )

    def build_pending(self, *, download_hash: str | None, handoff_source: str):  # pragma: no cover
        raise AssertionError(f"unexpected build_pending for {download_hash}/{handoff_source}")

    def build_unresolved(self, *, download_hash: str | None, handoff_source: str):  # pragma: no cover
        raise AssertionError(f"unexpected build_unresolved for {download_hash}/{handoff_source}")


class OrganizeManagementRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.repository = OrchestrationRepository(self.session)
        self.detail = build_track_detail()
        self.media = build_track_media()
        from tests.test_organize_integration import build_settings as build_organize_settings

        self.settings = build_organize_settings(
            host_organize_mode="prefer_host",
            host_assume_organize_available=True,
            host_base_url="http://127.0.0.1:8090",
        )
        self.preview_result = OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.HOST,
            adapter_mode=AdapterMode.HOST,
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
            organize_status=OrganizeStatus.PREVIEW_READY,
            target_library_path="/library/music",
            target_relative_path="adele/2015 - 25/hello.flac",
            strategy_note="preview",
            integration_point="TestResolver.preview",
            capability_source="test",
            verification_state=VerificationState.VERIFIED,
            mock=False,
            note="preview",
        )

        self.job = SearchJobModel(
            id="job-001",
            trigger_source="manual",
            profile_id="default-lossless",
            mode="manual",
            status="queued",
            music_media_input={
                "entity_hint": "track",
                "source_kind": "manual",
                "title": self.detail.track_title,
                "artist_names": [self.detail.artist_name],
                "album_title": self.detail.album_title,
                "album_artist_names": [],
                "external_refs": {},
                "source_context": {},
                "raw_context": {},
            },
            music_meta_base={
                "entity_type": "track",
                "canonical_title": self.detail.title,
                "canonical_artist_names": [self.detail.artist_name],
                "canonical_album_title": self.detail.album_title,
                "canonical_album_artist_names": [],
                "external_refs": {},
                "source_refs": {},
                "evidence": [],
                "normalization_notes": [],
            },
            music_media_info=self.media.model_dump(mode="json"),
            query_payload={},
            summary_json={},
        )
        self.candidate = SearchCandidateModel(
            id="cand-001",
            job_id=self.job.id,
            site_id="site-001",
            site_name="Test Site",
            title="Adele - Hello",
            normalized_title="adele hello",
            size_bytes=1024,
            seeders=1,
            peers=0,
            source_tags=[],
            score_breakdown={},
            reason_codes=[],
            raw_payload={},
        )
        self.binding = DownloadBindingModel(
            id="bind-001",
            job_id=self.job.id,
            candidate_id=self.candidate.id,
            target_downloader="QB",
            downloader_task_id="stub-download-001",
            dispatchable=True,
            dispatch_status="host_submitted",
            mock=False,
            note="binding",
            integration_point="test.binding",
            raw_payload={
                "path_handoff": {
                    "download_hash": "stub-download-001",
                    "source_path": None,
                    "source_filetype": None,
                    "handoff_source": "moviepilot.runtime.history.download",
                    "handoff_status": "pending_history_sync",
                    "verification_state": "unverified",
                    "note": "pending",
                    "raw_summary": {"download_hash": "stub-download-001"},
                }
            },
        )
        self.session.add_all([self.job, self.candidate, self.binding])
        self.session.commit()

        self.record = self.repository.create_organize_record(
            subscription_run_id="run-001",
            search_job_id=self.job.id,
            candidate_id=self.candidate.id,
            binding_id=self.binding.id,
            result=self.preview_result,
            music_media_input=self.job.music_media_input,
            music_meta_base=self.job.music_meta_base,
            music_recognition_assessment={},
            music_media_info=self.job.music_media_info,
        )
        self.session.commit()

        self.service = OrganizeService(
            session=self.session,
            resolver=CapturingPreviewResolver(self.preview_result),
            strategy_service=OrganizeStrategyService(self.settings),
            path_handoff_service=RepairingPathHandoffService(),
            music_media_chain=DummyMusicMediaChain(),
        )
        app.dependency_overrides[get_organize_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_organize_service, None)
        self.session.close()

    def test_list_jobs_filters_by_multiple_fields(self) -> None:
        self.repository.update_organize_record(
            self.record,
            result=self.preview_result.model_copy(update={"organize_status": OrganizeStatus.FAILED}),
            music_media_input=self.job.music_media_input,
            music_meta_base=self.job.music_meta_base,
            music_media_info=self.job.music_media_info,
        )
        self.session.add(
            OrganizeRecordModel(
                id="org-other",
                subscription_run_id="run-002",
                search_job_id=self.job.id,
                candidate_id=self.candidate.id,
                binding_id=None,
                organizeable=True,
                organize_backend="mock",
                strategy="music_default_layout",
                library_type="music",
                root_path="/library/music",
                organize_status="failed",
                target_library_path="/library/music",
                target_relative_path="other.flac",
                conflict_policy="skip_existing",
                strategy_note="other",
                integration_point="test",
                capability_source="test",
                failure_reason=None,
                verification_state="placeholder",
                mock=False,
                music_media_input={},
                music_meta_base={},
                music_recognition_assessment={},
                music_media_info={},
                raw_payload={},
                note="other",
            )
        )
        self.session.commit()

        response = self.client.get(
            "/api/v1/plugin/musicpilot/organize/jobs",
            params={
                "status": "failed",
                "organize_backend": "host",
                "verification_state": "verified",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["total"], 1)
        self.assertEqual(body["data"]["items"][0]["id"], self.record.id)

    def test_rebuild_preview_replays_preview_for_existing_record(self) -> None:
        response = self.client.post(f"/api/v1/plugin/musicpilot/organize/jobs/{self.record.id}/rebuild-preview")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["mock"])
        self.assertEqual(body["data"]["id"], self.record.id)
        self.assertEqual(body["data"]["organize_status"], "preview_ready")
        self.assertEqual(body["data"]["integration_point"], "TestResolver.preview")
        self.assertEqual(len(self.service.resolver.preview_calls), 1)
        self.assertEqual(self.service.resolver.preview_calls[0]["binding_id"], self.binding.id)

    def test_repair_source_path_persists_repaired_source_context(self) -> None:
        response = self.client.post(f"/api/v1/plugin/musicpilot/organize/jobs/{self.record.id}/repair-source-path")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["mock"])
        self.assertEqual(body["data"]["id"], self.record.id)
        self.assertEqual(body["data"]["organize_status"], "preview_ready")
        self.assertEqual(len(self.service.resolver.preview_calls), 1)

        refreshed_candidate = self.session.get(SearchCandidateModel, self.candidate.id)
        refreshed_binding = self.session.get(DownloadBindingModel, self.binding.id)
        self.assertEqual(
            refreshed_candidate.raw_payload["host_transfer_source_path"],
            "/downloads/Adele/2015 - 25/01 - Hello.flac",
        )
        self.assertEqual(
            refreshed_binding.raw_payload["path_handoff"]["source_path"],
            "/downloads/Adele/2015 - 25/01 - Hello.flac",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
