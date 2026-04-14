from __future__ import annotations

import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.chain.transfer import MusicTransferChain
from app.db.models import Base, DownloadBindingModel, SearchCandidateModel, SearchJobModel
from app.db.orchestration_oper import OrchestrationOper
from app.schemas.acquisition import PathHandoffInfo
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeConflictPolicy,
    OrganizePlan,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)
from app.modules.host_integration import OrganizeExecutionResult
from app.helper.organize_strategy import MusicOrganizeStrategy

from tests.test_query_builder import build_track_detail, build_track_media


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class DummyMusicMediaChain:
    def hydrate(self, media):  # noqa: ANN001
        return build_track_detail()


class DummyResolver:
    def __init__(self, preview_result: OrganizeAdapterResult, apply_result: OrganizeAdapterResult):
        self.preview_result = preview_result
        self.apply_result = apply_result
        self.preview_calls: list[str] = []
        self.apply_calls: list[str] = []

    def preview(self, *, candidate, metadata_detail, binding_id=None, plan: OrganizePlan):  # noqa: ANN001
        self.preview_calls.append(binding_id or "candidate")
        return OrganizeExecutionResult(result=self.preview_result, resolution=self.preview_result.adapter_resolution)

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan: OrganizePlan):  # noqa: ANN001
        self.apply_calls.append(organize_job_id)
        return OrganizeExecutionResult(result=self.apply_result, resolution=self.apply_result.adapter_resolution)


class DummyPathHandoffService:
    def __init__(self, *, resolved: PathHandoffInfo | None):
        self.resolved = resolved

    def resolve_from_download(self, download_hash: str | None):  # noqa: ANN001
        return self.resolved

    def resolve_from_download_with_retry(self, download_hash: str | None):  # noqa: ANN001
        return self.resolved

    def build_pending(self, *, download_hash: str | None, handoff_source: str) -> PathHandoffInfo:
        return PathHandoffInfo(
            download_hash=download_hash,
            source_path=None,
            source_filetype=None,
            source_name=None,
            source_basename=None,
            source_extension=None,
            handoff_source=handoff_source,
            handoff_status="pending_history_sync",
            verification_state=VerificationState.UNVERIFIED,
            note="pending",
            raw_summary={},
        )

    def build_unresolved(self, *, download_hash: str | None, handoff_source: str) -> PathHandoffInfo:
        return PathHandoffInfo(
            download_hash=download_hash,
            source_path=None,
            source_filetype=None,
            source_name=None,
            source_basename=None,
            source_extension=None,
            handoff_source=handoff_source,
            handoff_status="handoff_unresolved",
            verification_state=VerificationState.UNVERIFIED,
            note="unresolved",
            raw_summary={},
        )


class MusicTransferChainProcessTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.repository = OrchestrationOper(self.session)
        self.media = build_track_media()
        self.detail = build_track_detail()

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
        self.apply_result = self.preview_result.model_copy(
            update={"organize_status": OrganizeStatus.APPLIED, "strategy_note": "applied"}
        )

    def tearDown(self) -> None:
        self.session.close()

    def _seed_job_candidate_binding(
        self,
        *,
        binding_id: str,
        task_id: str,
        path_handoff: dict,
    ) -> DownloadBindingModel:
        job = SearchJobModel(
            id="job-001",
            trigger_source="manual",
            profile_id="default-lossless",
            mode="manual",
            status="dispatched",
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
        candidate = SearchCandidateModel(
            id="cand-001",
            job_id=job.id,
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
            decision="auto_download",
            dispatch_status="host_submitted",
            dispatchable=True,
            raw_payload={"path_handoff": path_handoff},
        )
        binding = DownloadBindingModel(
            id=binding_id,
            job_id=job.id,
            candidate_id=candidate.id,
            target_downloader="QB",
            downloader_task_id=task_id,
            dispatchable=True,
            dispatch_status="host_submitted",
            mock=False,
            note="binding",
            integration_point="test.binding",
            raw_payload={"path_handoff": path_handoff},
            dispatched_at=utc_now(),
        )
        self.session.add_all([job, candidate, binding])
        self.session.commit()
        return binding

    def test_process_creates_preview_for_new_binding(self) -> None:
        pending_handoff = PathHandoffInfo(
            download_hash="task-001",
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
        self._seed_job_candidate_binding(
            binding_id="bind-001",
            task_id="task-001",
            path_handoff=pending_handoff.model_dump(mode="json"),
        )
        resolver = DummyResolver(self.preview_result, self.apply_result)
        service = MusicTransferChain(
            session=self.session,
            resolver=resolver,
            strategy_service=MusicOrganizeStrategy(self.settings),
            path_handoff_service=DummyPathHandoffService(resolved=None),
            music_media_chain=DummyMusicMediaChain(),
        )

        result = service.process(now=utc_now())

        records = self.repository.list_organize_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].organize_status, "preview_ready")
        self.assertEqual(result["summary"]["created"], 1)
        self.assertEqual(result["summary"]["pending"], 1)
        self.assertEqual(len(resolver.preview_calls), 1)
        self.assertEqual(len(resolver.apply_calls), 0)

    def test_process_auto_applies_when_path_ready(self) -> None:
        resolved_handoff = PathHandoffInfo(
            download_hash="task-002",
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
        self._seed_job_candidate_binding(
            binding_id="bind-002",
            task_id="task-002",
            path_handoff=resolved_handoff.model_dump(mode="json"),
        )
        resolver = DummyResolver(self.preview_result, self.apply_result)
        service = MusicTransferChain(
            session=self.session,
            resolver=resolver,
            strategy_service=MusicOrganizeStrategy(self.settings),
            path_handoff_service=DummyPathHandoffService(resolved=resolved_handoff),
            music_media_chain=DummyMusicMediaChain(),
        )

        result = service.process(now=utc_now())

        records = self.repository.list_organize_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].organize_status, "applied")
        self.assertEqual(result["summary"]["created"], 1)
        self.assertEqual(result["summary"]["applied"], 1)
        self.assertEqual(len(resolver.preview_calls), 1)
        self.assertEqual(len(resolver.apply_calls), 1)


if __name__ == "__main__":
    unittest.main()
