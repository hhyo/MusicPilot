"""Tests for automatic pending path handoff reconciliation."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.acquisition import DownloadBindingModel, SearchCandidateModel, SearchJobModel
from app.models.base import Base
from app.models.orchestration import OrganizeRecordModel, SubscriptionModel, SubscriptionRunModel
from app.schemas.acquisition import PathHandoffInfo
from app.schemas.music_media import MusicMediaInput
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.orchestration import (
    OrganizeConflictPolicy,
    OrganizePreviewResult,
    OrganizeStatus,
    OrganizeStrategySnapshot,
    SubscriptionRunStatus,
)
from app.services.pending_handoff import PendingHandoffReconcileService
from tests.test_query_builder import build_track_media


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_pending_handoff(*, download_hash: str = "task-001") -> PathHandoffInfo:
    return PathHandoffInfo(
        download_hash=download_hash,
        source_path=None,
        source_filetype=None,
        source_name=None,
        source_basename=None,
        source_extension=None,
        handoff_source="moviepilot.runtime.history.download",
        handoff_status="pending_history_sync",
        verification_state=VerificationState.UNVERIFIED,
        note="pending",
        raw_summary={},
    )


def build_resolved_handoff(*, download_hash: str = "task-001") -> PathHandoffInfo:
    return PathHandoffInfo(
        download_hash=download_hash,
        source_path="/downloads/Adele/25/01 - Hello.flac",
        source_filetype="file",
        source_name="01 - Hello.flac",
        source_basename="01 - Hello",
        source_extension=".flac",
        handoff_source="moviepilot.runtime.history.download",
        handoff_status="resolved_from_history_download",
        verification_state=VerificationState.VERIFIED,
        note="resolved",
        raw_summary={},
    )


def build_unresolved_handoff(*, download_hash: str = "task-001") -> PathHandoffInfo:
    return PathHandoffInfo(
        download_hash=download_hash,
        source_path=None,
        source_filetype=None,
        source_name=None,
        source_basename=None,
        source_extension=None,
        handoff_source="moviepilot.runtime.history.download",
        handoff_status="handoff_unresolved",
        verification_state=VerificationState.UNVERIFIED,
        note="unresolved",
        raw_summary={},
    )


def build_applied_record(record_id: str) -> OrganizePreviewResult:
    return OrganizePreviewResult(
        id=record_id,
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
        organize_status=OrganizeStatus.APPLIED,
        target_library_path="/library/music",
        target_relative_path="adele/2015 - 25/hello.flac",
        strategy_note="applied",
        integration_point="DummyOrganizeService.apply",
        capability_source="test",
        verification_state=VerificationState.VERIFIED,
        path_handoff=build_resolved_handoff(),
        mock=False,
        note="applied",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


class DummyPathHandoffService:
    def __init__(self, *, resolved: PathHandoffInfo | None):
        self.resolved = resolved
        self.resolve_calls: list[str | None] = []
        self.unresolved_build_calls: list[str | None] = []

    def resolve_from_download(self, download_hash: str | None) -> PathHandoffInfo | None:
        self.resolve_calls.append(download_hash)
        return self.resolved

    def build_unresolved(self, *, download_hash: str | None, handoff_source: str) -> PathHandoffInfo:
        self.unresolved_build_calls.append(download_hash)
        return build_unresolved_handoff(download_hash=download_hash or "unknown")


class DummyOrganizeService:
    def __init__(self, *, applied_result: OrganizePreviewResult):
        self.applied_result = applied_result
        self.apply_calls: list[str] = []

    def apply(self, payload):  # noqa: ANN001
        self.apply_calls.append(payload.organize_job_id)
        return self.applied_result


class PendingHandoffReconcileServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        media = build_track_media()
        media_input = MusicMediaInput(
            entity_hint=media.entity_type,
            source_kind="subscription",
            title=media.title,
            artist_names=list(media.artist_names),
            album_title=media.album_title,
            album_artist_names=list(media.album_artist_names),
            external_refs=dict(media.external_refs),
            source_context={},
            raw_context={},
        )
        self.job = SearchJobModel(
            id="job-001",
            trigger_source="subscription",
            profile_id="default-lossless",
            mode="auto",
            status="dispatched",
            music_media_input=media_input.model_dump(mode="json"),
            music_meta_base={
                "entity_type": "track",
                "canonical_title": media.title,
                "canonical_artist_names": list(media.artist_names),
                "canonical_album_title": media.album_title,
                "canonical_album_artist_names": list(media.album_artist_names),
                "external_refs": dict(media.external_refs),
                "source_refs": {},
                "evidence": [],
                "normalization_notes": [],
            },
            music_media_info=media.model_dump(mode="json"),
            query_payload={},
            summary_json={},
            mock=False,
            note="job",
        )
        self.candidate = SearchCandidateModel(
            id="cand-001",
            job_id="job-001",
            site_id="site-1",
            site_name="Mock Site",
            title="Hello",
            normalized_title="hello",
            size_bytes=123,
            seeders=10,
            peers=1,
            format_tag="flac",
            bitrate_kbps=1000,
            source_tags=["lossless"],
            raw_score=95.0,
            score_total=95.0,
            score_breakdown={},
            decision="auto_download",
            reason_codes=[],
            dispatch_status="host_submitted",
            dispatchable=True,
            raw_payload={"path_handoff": build_pending_handoff().model_dump(mode="json")},
            mock=False,
            note="candidate",
        )
        self.binding = DownloadBindingModel(
            id="bind-001",
            job_id="job-001",
            candidate_id="cand-001",
            target_downloader="QB",
            downloader_task_id="task-001",
            dispatchable=True,
            dispatch_status="host_submitted",
            mock=False,
            note="binding",
            integration_point="test",
            raw_payload={"path_handoff": build_pending_handoff().model_dump(mode="json")},
            dispatched_at=utc_now(),
        )
        self.subscription = SubscriptionModel(
            id="sub-001",
            subscription_type="track",
            target_id="track-hello",
            target_name="Hello",
            target_entity_type="track",
            chart_source=None,
            chart_name=None,
            status="active",
            mode="scheduled",
            preference_json={},
            target_payload_json={},
            latest_run_status="dispatched",
            mock=False,
            note="subscription",
        )
        self.run = SubscriptionRunModel(
            id="srun-001",
            subscription_id="sub-001",
            search_job_id="job-001",
            execution_status="dispatched",
            matched_candidates_count=1,
            organize_record_id="org-001",
            summary_json={
                "candidate_count": 1,
                "binding_id": "bind-001",
                "dispatch_status": "host_submitted",
                "organize_preview_id": "org-001",
            },
            mock=False,
            note="run",
        )
        self.record = OrganizeRecordModel(
            id="org-001",
            subscription_run_id="srun-001",
            search_job_id="job-001",
            candidate_id="cand-001",
            binding_id="bind-001",
            organizeable=True,
            organize_backend="host",
            strategy="music_default_layout",
            library_type="music",
            root_path="/library/music",
            organize_status="preview_ready",
            target_library_path="/library/music",
            target_relative_path="adele/2015 - 25/hello.flac",
            conflict_policy="skip_existing",
            strategy_note="preview",
            integration_point="test.preview",
            capability_source="test",
            fallback_reason=None,
            failure_reason=None,
            verification_state="verified",
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
                "path_handoff": build_pending_handoff().model_dump(mode="json"),
            },
            note="preview",
        )
        self.session.add_all([self.job, self.candidate, self.binding, self.subscription, self.run, self.record])
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()

    def test_reconcile_pending_handoff_resolves_and_applies_record(self) -> None:
        service = PendingHandoffReconcileService(
            session=self.session,
            organize_service=DummyOrganizeService(applied_result=build_applied_record("org-001")),
            path_handoff_service=DummyPathHandoffService(resolved=build_resolved_handoff()),
            handoff_pending_ttl_seconds=120,
        )

        result = service.reconcile_pending_once(now=utc_now())

        self.assertEqual(result["summary"]["applied"], 1)
        self.assertEqual(result["applied_run_ids"], ["srun-001"])
        self.assertEqual(result["unresolved_run_ids"], [])
        self.assertEqual(result["diagnostics"][0]["reason"], "applied")
        self.assertEqual(service.organize_service.apply_calls, ["org-001"])

        binding = self.session.get(DownloadBindingModel, "bind-001")
        candidate = self.session.get(SearchCandidateModel, "cand-001")
        run = self.session.get(SubscriptionRunModel, "srun-001")
        record = self.session.get(OrganizeRecordModel, "org-001")

        self.assertEqual(binding.raw_payload["path_handoff"]["handoff_status"], "resolved_from_history_download")
        self.assertEqual(candidate.raw_payload["path_handoff"]["handoff_status"], "resolved_from_history_download")
        self.assertEqual(candidate.raw_payload["host_transfer_source_path"], "/downloads/Adele/25/01 - Hello.flac")
        self.assertEqual(record.organize_status, "applied")
        self.assertEqual(run.execution_status, SubscriptionRunStatus.APPLIED.value)
        self.assertEqual(run.summary_json["path_handoff_status"], "resolved_from_history_download")

    def test_reconcile_marks_stale_handoff_unresolved_without_apply(self) -> None:
        binding = self.session.get(DownloadBindingModel, "bind-001")
        binding.dispatched_at = utc_now() - timedelta(seconds=600)
        self.session.commit()

        service = PendingHandoffReconcileService(
            session=self.session,
            organize_service=DummyOrganizeService(applied_result=build_applied_record("org-001")),
            path_handoff_service=DummyPathHandoffService(resolved=None),
            handoff_pending_ttl_seconds=120,
        )

        result = service.reconcile_pending_once(now=utc_now())

        self.assertEqual(result["summary"]["unresolved"], 1)
        self.assertEqual(result["applied_run_ids"], [])
        self.assertEqual(result["unresolved_run_ids"], ["srun-001"])
        self.assertEqual(result["diagnostics"][0]["reason"], "handoff_unresolved")
        self.assertEqual(service.organize_service.apply_calls, [])

        binding = self.session.get(DownloadBindingModel, "bind-001")
        candidate = self.session.get(SearchCandidateModel, "cand-001")
        run = self.session.get(SubscriptionRunModel, "srun-001")
        record = self.session.get(OrganizeRecordModel, "org-001")

        self.assertEqual(binding.raw_payload["path_handoff"]["handoff_status"], "handoff_unresolved")
        self.assertEqual(candidate.raw_payload["path_handoff"]["handoff_status"], "handoff_unresolved")
        self.assertEqual(record.raw_payload["path_handoff"]["handoff_status"], "handoff_unresolved")
        self.assertEqual(record.organize_status, OrganizeStatus.FAILED.value)
        self.assertIn("TTL expired", record.failure_reason)
        self.assertEqual(run.execution_status, SubscriptionRunStatus.DISPATCHED.value)
        self.assertEqual(run.summary_json["organize_status"], OrganizeStatus.FAILED.value)
        self.assertEqual(run.summary_json["path_handoff_status"], "handoff_unresolved")

        second_result = service.reconcile_pending_once(now=utc_now())
        self.assertEqual(second_result["applied_run_ids"], [])
        self.assertEqual(second_result["unresolved_run_ids"], [])
        self.assertEqual(second_result["summary"]["skipped"], 0)

    def test_reconcile_reports_apply_failure_without_crashing_loop(self) -> None:
        class FailingOrganizeService:
            def __init__(self) -> None:
                self.apply_calls: list[str] = []

            def apply(self, payload):  # noqa: ANN001
                self.apply_calls.append(payload.organize_job_id)
                raise RuntimeError("organize apply failed")

        service = PendingHandoffReconcileService(
            session=self.session,
            organize_service=FailingOrganizeService(),
            path_handoff_service=DummyPathHandoffService(resolved=build_resolved_handoff()),
            handoff_pending_ttl_seconds=120,
        )

        result = service.reconcile_pending_once(now=utc_now())

        self.assertEqual(result["summary"]["failed"], 1)
        self.assertEqual(result["diagnostics"][0]["reason"], "apply_failed")
        self.assertIn("organize apply failed", result["diagnostics"][0]["error_message"])

        run = self.session.get(SubscriptionRunModel, "srun-001")
        record = self.session.get(OrganizeRecordModel, "org-001")
        self.assertEqual(run.execution_status, SubscriptionRunStatus.FAILED.value)
        self.assertEqual(record.organize_status, OrganizeStatus.FAILED.value)
        self.assertIn("organize apply failed", record.failure_reason)


if __name__ == "__main__":
    unittest.main()
