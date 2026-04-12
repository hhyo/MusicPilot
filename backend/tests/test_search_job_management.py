from __future__ import annotations

import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_downloads_workspace_service, get_search_job_service
from app.main import app
from app.models import Base, DownloadBindingModel, SearchCandidateModel, SearchJobModel
from app.schemas.acquisition import (
    DownloadBindingDetail,
    DownloadTaskDetail,
    DownloadTaskListData,
    DispatchAdapterResult,
    PathHandoffInfo,
    SearchCandidateActionResult,
    SearchCandidateConfirmRequest,
    SearchCandidateDetail,
    SearchCandidateRejectRequest,
    SearchCandidateListData,
    SearchJobSummary,
)
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.music_media import MusicMediaInfo, MusicMediaInput, MusicMetaBase, MusicRecognitionAssessment
from app.schemas.shared import DecisionStatus, JobStatus
from app.services.dispatch import DispatchService
from app.services.downloads_workspace import DownloadsWorkspaceService
from app.services.query_builder import QueryBuilderService
from app.services.search_job import SearchJobService


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def build_media_input() -> MusicMediaInput:
    return MusicMediaInput(
        entity_hint="track",
        source_kind="manual",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
    )


def build_media_base() -> MusicMetaBase:
    return MusicMetaBase(
        entity_type="track",
        canonical_title="Hello",
        canonical_artist_names=["Adele"],
        canonical_album_title="25",
        canonical_album_artist_names=["Adele"],
        alias_titles=[],
        alias_artist_names=[],
        alias_album_titles=[],
        featuring_artist_names=[],
        external_refs={},
        source_refs={},
        evidence=[],
        normalization_notes=[],
        confidence_hint=0.9,
    )


def build_media_info() -> MusicMediaInfo:
    return MusicMediaInfo(
        entity_type="track",
        provider="musicbrainz",
        provider_id="recording-hello",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        album_artist_names=["Adele"],
        release_date="2015-10-23",
        year=2015,
        track_number=1,
        disc_number=1,
        related_artist_ids=[],
        related_album_id="release-group-25",
        related_track_ids=[],
        external_refs={},
        match_confidence=0.98,
        match_strategy="strong_ref",
        match_evidence=[],
        diagnostics=[],
    )


class DummyMusicMediaChain:
    def resolve_response(self, payload):  # noqa: ANN001
        return SimpleNamespace(
            base=build_media_base(),
            media=build_media_info(),
            assessment=MusicRecognitionAssessment(state="ready", note="resolved"),
        )


class DummyHostSearchResolver:
    def search(self, **kwargs):  # noqa: ANN003, ANN001
        raise AssertionError("search should not be called in management tests")


class DummyScorer:
    pass


class DummyDispatchResolver:
    def __init__(self, *, task_id: str = "task-002", dispatchable: bool = True):
        self.calls: list[tuple[str, str, bool]] = []
        self.task_id = task_id
        self.dispatchable = dispatchable

    def dispatch(self, *, candidate, downloader_id: str, manual_confirm: bool):  # noqa: ANN001
        self.calls.append((candidate.id, downloader_id, manual_confirm))
        return SimpleNamespace(
            result=DispatchAdapterResult(
                dispatchable=self.dispatchable,
                dispatch_status="host_submitted" if self.dispatchable else "host_rejected",
                target_downloader=downloader_id,
                downloader_task_id=self.task_id if self.dispatchable else None,
                note="dispatched",
                integration_point="DummyDispatchResolver.dispatch",
                mock=False,
                dispatch_backend=AdapterMode.HOST,
                capability_source="tests.dispatch",
                verification_state=VerificationState.VERIFIED,
                path_handoff=PathHandoffInfo(
                    download_hash=self.task_id,
                    source_path="/downloads/Adele - Hello.flac" if self.dispatchable else None,
                    source_filetype="file" if self.dispatchable else None,
                    source_name="Adele - Hello.flac" if self.dispatchable else None,
                    source_basename="Adele - Hello" if self.dispatchable else None,
                    source_extension=".flac" if self.dispatchable else None,
                    handoff_source="moviepilot.runtime.history.download",
                    handoff_status="resolved_from_history_download" if self.dispatchable else "handoff_unresolved",
                    verification_state=VerificationState.VERIFIED if self.dispatchable else VerificationState.UNVERIFIED,
                    note="resolved" if self.dispatchable else "unresolved",
                    raw_summary={},
                ),
                host_response_summary={"download_id": self.task_id} if self.dispatchable else {},
            )
        )


class DummyPathHandoffService:
    def __init__(self, *, source_path: str | None):
        self.source_path = source_path
        self.calls: list[str | None] = []

    def resolve_from_download(self, download_hash: str | None) -> PathHandoffInfo | None:
        self.calls.append(download_hash)
        if not self.source_path:
            return None
        return PathHandoffInfo(
            download_hash=download_hash,
            source_path=self.source_path,
            source_filetype="file",
            source_name=self.source_path.rsplit("/", 1)[-1],
            source_basename=self.source_path.rsplit("/", 1)[-1].rsplit(".", 1)[0],
            source_extension=".flac",
            handoff_source="moviepilot.runtime.history.download",
            handoff_status="resolved_from_history_download",
            verification_state=VerificationState.VERIFIED,
            note="resolved",
            raw_summary={},
        )


class SearchJobManagementServiceTest(unittest.TestCase):
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
                status="manual_pending",
                music_media_input=build_media_input().model_dump(mode="json"),
                music_meta_base=build_media_base().model_dump(mode="json"),
                music_recognition_assessment=MusicRecognitionAssessment(state="ready", note="ok").model_dump(mode="json"),
                music_media_info=build_media_info().model_dump(mode="json"),
                query_payload={},
                summary_json={},
                mock=False,
                note="job",
            )
        )
        self.session.add(
            SearchCandidateModel(
                id="cand-001",
                job_id="job-001",
                site_id="site-001",
                site_name="Site",
                title="Adele - Hello",
                normalized_title="adele hello",
                decision="manual_confirm",
                dispatch_status="pending",
                dispatchable=True,
                raw_payload={},
                mock=False,
                note="candidate",
            )
        )
        self.session.commit()

        self.dispatch_resolver = DummyDispatchResolver()
        self.dispatch_service = DispatchService(session=self.session, resolver=self.dispatch_resolver)
        self.service = SearchJobService(
            self.session,
            query_builder=QueryBuilderService(music_media_chain=DummyMusicMediaChain()),
            music_media_chain=DummyMusicMediaChain(),
            host_search_resolver=DummyHostSearchResolver(),
            scorer=DummyScorer(),
            dispatch_service=self.dispatch_service,
        )

    def tearDown(self) -> None:
        self.session.close()

    def test_confirm_candidate_dispatches_and_creates_binding(self) -> None:
        result = self.service.confirm_candidate(
            "job-001",
            "cand-001",
            SearchCandidateConfirmRequest(downloader_id="QB", manual_confirm=False, reason="user confirmed"),
        )

        self.assertEqual(self.dispatch_resolver.calls, [("cand-001", "QB", False)])
        self.assertEqual(result.candidate.decision, DecisionStatus.AUTO_DOWNLOAD)
        self.assertIsNotNone(result.binding)
        self.assertEqual(result.binding.target_downloader, "QB")
        self.assertEqual(result.job.status, JobStatus.DISPATCHED)

    def test_reject_candidate_marks_rejected_with_reason(self) -> None:
        result = self.service.reject_candidate(
            "job-001",
            "cand-001",
            SearchCandidateRejectRequest(reason="wrong edition"),
        )

        self.assertEqual(result.candidate.decision, DecisionStatus.REJECT)
        self.assertIn("wrong edition", result.candidate.reason_codes)
        self.assertEqual(result.job.status, JobStatus.NO_RESULT)

    def test_cancel_running_job_marks_cancelled(self) -> None:
        job = self.session.get(SearchJobModel, "job-001")
        job.status = "running"
        self.session.commit()

        result = self.service.cancel_job("job-001")

        self.assertEqual(result.status, JobStatus.CANCELLED)

    def test_list_jobs_supports_has_dispatch_and_decision_filters(self) -> None:
        self.service.confirm_candidate(
            "job-001",
            "cand-001",
            SearchCandidateConfirmRequest(downloader_id="QB", manual_confirm=False, reason="user confirmed"),
        )

        dispatched = self.service.list_jobs(has_dispatch=True)
        rejected = self.service.list_jobs(decision="reject")
        auto_download = self.service.list_jobs(decision="auto_download")

        self.assertEqual([job.id for job in dispatched], ["job-001"])
        self.assertEqual(rejected, [])
        self.assertEqual([job.id for job in auto_download], ["job-001"])


class DownloadsWorkspaceManagementServiceTest(unittest.TestCase):
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
                music_media_input=build_media_input().model_dump(mode="json"),
                music_meta_base=build_media_base().model_dump(mode="json"),
                music_recognition_assessment=MusicRecognitionAssessment(state="ready", note="ok").model_dump(mode="json"),
                music_media_info=build_media_info().model_dump(mode="json"),
                query_payload={},
                summary_json={},
                mock=False,
                note="job",
            )
        )
        self.session.add(
            SearchCandidateModel(
                id="cand-001",
                job_id="job-001",
                site_id="site-001",
                site_name="Site",
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
                    "path_handoff": PathHandoffInfo(
                        download_hash="task-001",
                        source_path="/downloads/Adele - Hello.flac",
                        source_filetype="file",
                        source_name="Adele - Hello.flac",
                        source_basename="Adele - Hello",
                        source_extension=".flac",
                        handoff_source="moviepilot.runtime.history.download",
                        handoff_status="pending_history_sync",
                        verification_state=VerificationState.UNVERIFIED,
                        note="pending",
                        raw_summary={},
                    ).model_dump(mode="json"),
                    "host_response_summary": {"download_id": "task-001"},
                },
            )
        )
        self.session.commit()

        self.dispatch_resolver = DummyDispatchResolver(task_id="task-002")
        self.service = DownloadsWorkspaceService(
            session=self.session,
            dispatch_service=DispatchService(session=self.session, resolver=self.dispatch_resolver),
            path_handoff_service=DummyPathHandoffService(source_path="/downloads/Adele - Hello.flac"),
        )

    def tearDown(self) -> None:
        self.session.close()

    def test_list_tasks_groups_bindings_by_downloader_task(self) -> None:
        result = self.service.list_tasks()

        self.assertEqual(result.total, 1)
        self.assertEqual(result.items[0].task_id, "task-001")

    def test_retry_dispatch_creates_new_binding(self) -> None:
        result = self.service.retry_dispatch("bind-001", downloader_id="QB", manual_confirm=False)

        self.assertEqual(self.dispatch_resolver.calls, [("cand-001", "QB", False)])
        self.assertEqual(result.id[:5], "bind-")
        self.assertNotEqual(result.id, "bind-001")
        self.assertEqual(result.downloader_task_id, "task-002")

    def test_retry_handoff_updates_binding_handoff_snapshot(self) -> None:
        result = self.service.retry_handoff("bind-001")

        self.assertTrue(result.resolved)
        self.assertEqual(result.binding.path_handoff.download_hash, "task-001")
        self.assertEqual(result.binding.path_handoff.source_path, "/downloads/Adele - Hello.flac")


def build_job_summary() -> SearchJobSummary:
    return SearchJobSummary(
        id="job-001",
        music_media_input=build_media_input(),
        music_meta_base=build_media_base(),
        music_recognition_assessment=MusicRecognitionAssessment(state="ready", note="ok"),
        music_media_info=build_media_info(),
        trigger_source="manual",
        profile_id="default-lossless",
        mode="manual",
        status="manual_pending",
        created_at="2026-04-12T00:00:00Z",
        updated_at="2026-04-12T00:00:00Z",
        mock=False,
        note="job",
        summary={},
    )


def build_candidate_detail() -> SearchCandidateDetail:
    return SearchCandidateDetail(
        id="cand-001",
        job_id="job-001",
        site_id="site-001",
        site_name="Site",
        title="Adele - Hello",
        normalized_title="adele hello",
        size_bytes=1024,
        seeders=10,
        peers=1,
        raw_score=95.0,
        score_total=95.0,
        decision="auto_download",
        reason_codes=["user confirmed"],
        dispatchable=True,
        dispatch_status="host_submitted",
        mock=False,
        created_at="2026-04-12T00:00:00Z",
        raw_payload={},
    )


def build_binding_detail() -> DownloadBindingDetail:
    return DownloadBindingDetail(
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
        dispatched_at="2026-04-12T00:00:00Z",
        path_handoff=PathHandoffInfo(
            download_hash="task-001",
            source_path="/downloads/Adele - Hello.flac",
            source_filetype="file",
            source_name="Adele - Hello.flac",
            source_basename="Adele - Hello",
            source_extension=".flac",
            handoff_source="moviepilot.runtime.history.download",
            handoff_status="resolved_from_history_download",
            verification_state=VerificationState.VERIFIED,
            note="resolved",
            raw_summary={},
        ),
        host_response_summary={"download_id": "task-001"},
        raw_payload={},
    )


class FakeSearchJobManagementService:
    def list_jobs(self, **kwargs):  # noqa: ANN003
        return [build_job_summary()]

    def cancel_job(self, job_id: str) -> SearchJobSummary:
        return build_job_summary().model_copy(update={"status": JobStatus.CANCELLED})

    def confirm_candidate(self, job_id: str, candidate_id: str, payload: SearchCandidateConfirmRequest) -> SearchCandidateActionResult:
        return SearchCandidateActionResult(
            job=build_job_summary().model_copy(update={"status": JobStatus.DISPATCHED}),
            candidate=build_candidate_detail(),
            binding=build_binding_detail(),
            note="confirmed",
        )

    def reject_candidate(self, job_id: str, candidate_id: str, payload: SearchCandidateRejectRequest) -> SearchCandidateActionResult:
        return SearchCandidateActionResult(
            job=build_job_summary().model_copy(update={"status": JobStatus.NO_RESULT}),
            candidate=build_candidate_detail().model_copy(
                update={"decision": DecisionStatus.REJECT, "dispatch_status": "rejected"}
            ),
            binding=None,
            note="rejected",
        )

    def list_candidates(self, job_id: str) -> SearchCandidateListData:
        return SearchCandidateListData(job_id=job_id, items=[build_candidate_detail()], total=1, mock=False, note="ok")


class FakeDownloadsWorkspaceService:
    def list_tasks(self) -> DownloadTaskListData:
        return DownloadTaskListData(items=[self.get_task("task-001")], total=1, mock=False, note="ok")

    def get_task(self, task_id: str) -> DownloadTaskDetail:
        return DownloadTaskDetail(
            task_id=task_id,
            target_downloader="QB",
            binding_count=1,
            latest_dispatch_status="host_submitted",
            latest_dispatched_at="2026-04-12T00:00:00Z",
            mock=False,
            path_handoff=build_binding_detail().path_handoff,
            host_response_summary={"download_id": task_id},
            bindings=[build_binding_detail()],
        )

    def retry_dispatch(self, binding_id: str, *, downloader_id: str, manual_confirm: bool) -> DownloadBindingDetail:
        return build_binding_detail().model_copy(update={"id": "bind-002", "downloader_task_id": "task-002"})

    def retry_handoff(self, binding_id: str):
        from app.schemas.acquisition import BindingRetryHandoffResult

        return BindingRetryHandoffResult(binding=build_binding_detail(), resolved=True, note="ok")


class JobsAndDownloadsRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_search_job_service] = lambda: FakeSearchJobManagementService()
        app.dependency_overrides[get_downloads_workspace_service] = lambda: FakeDownloadsWorkspaceService()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_search_job_service, None)
        app.dependency_overrides.pop(get_downloads_workspace_service, None)

    def test_confirm_candidate_route_is_available(self) -> None:
        response = self.client.post(
            "/api/v1/plugin/musicpilot/jobs/job-001/candidates/cand-001/confirm",
            json={"downloader_id": "QB", "manual_confirm": False},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["binding"]["id"], "bind-001")

    def test_cancel_job_route_is_available(self) -> None:
        response = self.client.post("/api/v1/plugin/musicpilot/jobs/job-001/cancel")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "cancelled")

    def test_list_download_tasks_route_is_available(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/downloads/tasks")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["items"][0]["task_id"], "task-001")

    def test_retry_dispatch_route_is_available(self) -> None:
        response = self.client.post(
            "/api/v1/plugin/musicpilot/downloads/bindings/bind-001/retry-dispatch",
            json={"downloader_id": "QB", "manual_confirm": False},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], "bind-002")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
