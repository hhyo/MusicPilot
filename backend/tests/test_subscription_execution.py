"""Tests for minimal auto-dispatch behavior in subscription execution."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.repositories.orchestration import OrchestrationRepository
from app.schemas.acquisition import (
    DispatchResult,
    PathHandoffInfo,
    SearchCandidateDetail,
    SearchCandidateListData,
    SearchJobCreateRequest,
    SearchJobSummary,
)
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.music_media import MusicMediaInfo, MusicMediaInput, MusicMetaBase, MusicRecognitionAssessment
from app.schemas.mvp import DecisionStatus, EntityType, JobStatus, TriggerSource
from app.schemas.orchestration import (
    OrganizeApplyRequest,
    OrganizeConflictPolicy,
    OrganizePreviewRequest,
    OrganizePreviewResult,
    OrganizeStatus,
    OrganizeStrategySnapshot,
    SubscriptionRunStatus,
    SubscriptionType,
)
from app.services.subscription_execution import SubscriptionExecutionService

from test_query_builder import build_artist_detail, build_artist_media


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_search_job_summary(*, status: JobStatus) -> SearchJobSummary:
    media = build_artist_media()
    media_input = MusicMediaInput(
        entity_hint=EntityType.ARTIST,
        source_kind="subscription",
        title=media.title,
        artist_names=list(media.artist_names),
        album_title=None,
        album_artist_names=[],
        external_refs=dict(media.external_refs),
        source_context={},
        raw_context={},
    )
    return SearchJobSummary(
        id="job-001",
        music_media_input=media_input,
        music_meta_base=MusicMetaBase(
            entity_type=EntityType.ARTIST,
            canonical_title=media.title,
            canonical_artist_names=list(media.artist_names),
            canonical_album_title=None,
            canonical_album_artist_names=[],
            external_refs=dict(media.external_refs),
            evidence=[],
        ),
        music_recognition_assessment=MusicRecognitionAssessment(state="direct"),
        music_media_info=media,
        trigger_source=TriggerSource.SUBSCRIPTION,
        profile_id="default-lossless",
        mode="auto",
        status=status,
        created_at=utc_now(),
        updated_at=utc_now(),
        mock=False,
        note="job",
        summary={},
    )


def build_candidate(
    *,
    candidate_id: str,
    decision: DecisionStatus,
    score_total: float,
) -> SearchCandidateDetail:
    return SearchCandidateDetail(
        id=candidate_id,
        job_id="job-001",
        site_id="site-1",
        site_name="Mock Site",
        title=f"Candidate {candidate_id}",
        normalized_title=f"candidate {candidate_id}",
        size_bytes=123,
        seeders=10,
        peers=1,
        format_tag="flac",
        bitrate_kbps=1000,
        source_tags=["lossless"],
        raw_score=score_total,
        score_total=score_total,
        score_breakdown={},
        decision=decision,
        reason_codes=[],
        dispatchable=True,
        dispatch_status="pending",
        mock=False,
        note="candidate",
        created_at=utc_now(),
        raw_payload={},
    )


def build_organize_preview(
    *,
    record_id: str,
    status: OrganizeStatus,
    path_handoff: PathHandoffInfo | None = None,
) -> OrganizePreviewResult:
    return OrganizePreviewResult(
        id=record_id,
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
        organize_status=status,
        target_library_path="/library/music",
        target_relative_path="adele/2015 - 25/hello.flac",
        strategy_note="preview",
        integration_point="DummyOrganizeService.preview",
        capability_source="test",
        verification_state=VerificationState.VERIFIED,
        path_handoff=path_handoff,
        mock=False,
        note="organize",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


class DummyMetadataService:
    def get_detail(self, entity_type, entity_id):  # noqa: ANN001
        raise AssertionError(f"get_detail should not be called for {entity_type}:{entity_id}")


class DummySearchJobService:
    def __init__(self, *, executed_job: SearchJobSummary, candidates: list[SearchCandidateDetail]):
        self.metadata_service = DummyMetadataService()
        self.executed_job = executed_job
        self.candidates = candidates
        self.created_payloads: list[SearchJobCreateRequest] = []

    def create_job(self, payload):  # noqa: ANN001
        self.created_payloads.append(payload)
        return build_search_job_summary(status=JobStatus.QUEUED)

    def execute_job(self, job_id: str) -> SearchJobSummary:
        return self.executed_job

    def list_candidates(self, job_id: str) -> SearchCandidateListData:
        return SearchCandidateListData(
            job_id=job_id,
            items=self.candidates,
            total=len(self.candidates),
            mock=False,
            note="candidates",
        )

    def get_job(self, job_id: str) -> SearchJobSummary:
        return self.executed_job


class DummyDispatchService:
    def __init__(self, *, result: DispatchResult):
        self.result = result
        self.calls: list[tuple[str, str, bool]] = []

    def dispatch(self, payload) -> DispatchResult:  # noqa: ANN001
        self.calls.append((payload.result_id, payload.downloader_id, payload.manual_confirm))
        return self.result


class DummyOrganizeService:
    def __init__(self) -> None:
        self.preview_calls: list[tuple[str | None, str | None, str | None]] = []
        self.preview_candidate_calls: list[str] = []
        self.apply_calls: list[str] = []
        self.records = {
            "org-binding": build_organize_preview(record_id="org-binding", status=OrganizeStatus.PREVIEW_READY),
            "org-candidate": build_organize_preview(record_id="org-candidate", status=OrganizeStatus.PREVIEW_READY),
            "org-applied": build_organize_preview(record_id="org-binding", status=OrganizeStatus.APPLIED),
        }

    def preview(self, payload: OrganizePreviewRequest, *, subscription_run_id: str | None = None):
        self.preview_calls.append((payload.candidate_id, payload.binding_id, subscription_run_id))
        return self.records["org-binding"]

    def preview_for_candidate(self, *, candidate_id: str, subscription_run_id: str | None = None):
        self.preview_candidate_calls.append(candidate_id)
        return self.records["org-candidate"]

    def apply(self, payload: OrganizeApplyRequest):
        self.apply_calls.append(payload.organize_job_id)
        return self.records["org-applied"]

    def get_record(self, record_id: str):
        if record_id == "org-binding" and self.apply_calls:
            return self.records["org-applied"]
        return self.records[record_id]


class DummyMusicMediaChain:
    def __init__(self, resolved_media: MusicMediaInfo | None = None) -> None:
        self.resolved_media = resolved_media or build_artist_media()
        self.calls: list[MusicMediaInput] = []

    def input_from_music_media_info(
        self,
        payload: MusicMediaInfo,
        *,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return MusicMediaInput(
            entity_hint=payload.entity_type,
            source_kind=source_kind,
            title=payload.title,
            artist_names=list(payload.artist_names),
            album_title=payload.album_title,
            album_artist_names=list(payload.album_artist_names),
            release_date=payload.release_date,
            year=payload.year,
            track_number=payload.track_number,
            disc_number=payload.disc_number,
            external_refs=dict(payload.external_refs),
            source_context=source_context or {},
            raw_context=raw_context or {},
        )

    def input_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        external_refs = {}
        if provider == "musicbrainz":
            if entity_type == EntityType.ARTIST:
                external_refs["musicbrainz_artist_id"] = provider_id
            elif entity_type == EntityType.ALBUM:
                external_refs["musicbrainz_release_group_id"] = provider_id
            elif entity_type == EntityType.TRACK:
                external_refs["musicbrainz_recording_id"] = provider_id
        else:
            external_refs[f"{provider}_id"] = provider_id
        return MusicMediaInput(
            entity_hint=entity_type,
            source_kind=source_kind,
            artist_names=[],
            album_artist_names=[],
            external_refs=external_refs,
            source_context=source_context or {},
            raw_context=raw_context or {},
        )

    def input_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        payload = target_payload or {}
        provider = "musicbrainz"
        provider_id = target_id
        provider_ref = payload.get("provider_ref") if isinstance(payload, dict) else None
        if isinstance(provider_ref, dict):
            provider = provider_ref.get("provider") or provider
            provider_id = provider_ref.get("provider_id") or provider_id
        return self.input_from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def resolve(self, payload: MusicMediaInput) -> MusicMediaInfo:
        self.calls.append(payload)
        return self.resolved_media

    def resolve_detail(self, payload: MusicMediaInput):
        self.calls.append(payload)
        return SimpleNamespace(detail=build_artist_detail())


class SubscriptionExecutionServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        self.repository = OrchestrationRepository(self.session)
        self.subscription = self.repository.create_subscription(
            subscription_type=SubscriptionType.ARTIST.value,
            target_id="artist-adele",
            target_name="Adele",
            target_entity_type=EntityType.ARTIST.value,
            chart_source=None,
            chart_name=None,
            mode="scheduled",
            preference_json={},
            target_payload_json={},
            note="subscription",
        )
        self.session.commit()
        self.session.refresh(self.subscription)

    def tearDown(self) -> None:
        self.session.close()

    def test_execute_auto_download_dispatches_best_candidate_and_previews_binding(self) -> None:
        search_job_service = DummySearchJobService(
            executed_job=build_search_job_summary(status=JobStatus.MANUAL_PENDING),
            candidates=[
                build_candidate(candidate_id="cand-auto", decision=DecisionStatus.AUTO_DOWNLOAD, score_total=95.0),
                build_candidate(candidate_id="cand-manual", decision=DecisionStatus.MANUAL_CONFIRM, score_total=75.0),
            ],
        )
        dispatch_service = DummyDispatchService(
            result=DispatchResult(
                candidate_id="cand-auto",
                job_id="job-001",
                dispatchable=True,
                dispatch_status="mock_submitted",
                target_downloader="mock-downloader",
                downloader_task_id="task-001",
                note="dispatched",
                integration_point="DummyDispatchService.dispatch",
                mock=False,
                binding_id="bind-001",
                dispatch_backend=AdapterMode.MOCK,
                capability_source="test",
                verification_state=VerificationState.VERIFIED,
            )
        )
        organize_service = DummyOrganizeService()
        service = SubscriptionExecutionService(
            self.session,
            search_job_service=search_job_service,
            organize_service=organize_service,
            music_media_chain=DummyMusicMediaChain(),
            dispatch_service=dispatch_service,
        )

        result = service.execute(self.subscription.id)

        self.assertEqual(dispatch_service.calls, [("cand-auto", "mock-downloader", True)])
        self.assertEqual(organize_service.preview_calls, [(None, "bind-001", result.id)])
        self.assertEqual(organize_service.preview_candidate_calls, [])
        self.assertEqual(result.execution_status, SubscriptionRunStatus.DISPATCHED)
        self.assertEqual(result.organize_preview.id, "org-binding")

    def test_execute_manual_confirm_keeps_candidate_preview_without_dispatch(self) -> None:
        search_job_service = DummySearchJobService(
            executed_job=build_search_job_summary(status=JobStatus.MANUAL_PENDING),
            candidates=[
                build_candidate(candidate_id="cand-manual", decision=DecisionStatus.MANUAL_CONFIRM, score_total=75.0),
            ],
        )
        dispatch_service = DummyDispatchService(
            result=DispatchResult(
                candidate_id="cand-manual",
                job_id="job-001",
                dispatchable=True,
                dispatch_status="mock_submitted",
                target_downloader="mock-downloader",
                note="dispatched",
                integration_point="DummyDispatchService.dispatch",
                mock=False,
                binding_id="bind-001",
                dispatch_backend=AdapterMode.MOCK,
                capability_source="test",
                verification_state=VerificationState.VERIFIED,
            )
        )
        organize_service = DummyOrganizeService()
        service = SubscriptionExecutionService(
            self.session,
            search_job_service=search_job_service,
            organize_service=organize_service,
            music_media_chain=DummyMusicMediaChain(),
            dispatch_service=dispatch_service,
        )

        result = service.execute(self.subscription.id)

        self.assertEqual(dispatch_service.calls, [])
        self.assertEqual(organize_service.preview_calls, [])
        self.assertEqual(organize_service.preview_candidate_calls, ["cand-manual"])
        self.assertEqual(result.execution_status, SubscriptionRunStatus.MANUAL_PENDING)
        self.assertEqual(result.organize_preview.id, "org-candidate")

    def test_build_subscription_provider_input_prefers_provider_ref_snapshot(self) -> None:
        self.subscription.target_payload_json = {
            "provider_ref": {
                "provider": "rss_catalog",
                "provider_id": "artist-rss-adele",
            }
        }
        self.session.commit()
        self.session.refresh(self.subscription)

        music_media_chain = DummyMusicMediaChain()
        service = SubscriptionExecutionService(
            self.session,
            search_job_service=DummySearchJobService(
                executed_job=build_search_job_summary(status=JobStatus.QUEUED),
                candidates=[],
            ),
            organize_service=DummyOrganizeService(),
            music_media_chain=music_media_chain,
            dispatch_service=DummyDispatchService(
                result=DispatchResult(
                    candidate_id="cand-1",
                    job_id="job-001",
                    dispatchable=False,
                    dispatch_status="skipped",
                    target_downloader="mock-downloader",
                    downloader_task_id=None,
                    note="noop",
                    integration_point="DummyDispatchService.dispatch",
                    mock=False,
                    binding_id=None,
                    dispatch_backend=AdapterMode.MOCK,
                    capability_source="test",
                    verification_state=VerificationState.VERIFIED,
                )
            ),
        )

        media_input = service._build_subscription_provider_input(
            self.subscription,
            source_kind="subscription_detail",
        )

        self.assertEqual(media_input.external_refs["rss_catalog_id"], "artist-rss-adele")

    def test_execute_auto_download_applies_when_preview_has_local_source(self) -> None:
        search_job_service = DummySearchJobService(
            executed_job=build_search_job_summary(status=JobStatus.MANUAL_PENDING),
            candidates=[
                build_candidate(candidate_id="cand-auto", decision=DecisionStatus.AUTO_DOWNLOAD, score_total=95.0),
            ],
        )
        dispatch_service = DummyDispatchService(
            result=DispatchResult(
                candidate_id="cand-auto",
                job_id="job-001",
                dispatchable=True,
                dispatch_status="mock_submitted",
                target_downloader="mock-downloader",
                downloader_task_id="task-001",
                note="dispatched",
                integration_point="DummyDispatchService.dispatch",
                mock=False,
                binding_id="bind-001",
                dispatch_backend=AdapterMode.MOCK,
                capability_source="test",
                verification_state=VerificationState.VERIFIED,
            )
        )
        organize_service = DummyOrganizeService()
        organize_service.records["org-binding"] = build_organize_preview(
            record_id="org-binding",
            status=OrganizeStatus.PREVIEW_READY,
            path_handoff=PathHandoffInfo(
                download_hash="task-001",
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
            ),
        )
        service = SubscriptionExecutionService(
            self.session,
            search_job_service=search_job_service,
            organize_service=organize_service,
            music_media_chain=DummyMusicMediaChain(),
            dispatch_service=dispatch_service,
        )

        result = service.execute(self.subscription.id)

        self.assertEqual(dispatch_service.calls, [("cand-auto", "mock-downloader", True)])
        self.assertEqual(organize_service.preview_calls, [(None, "bind-001", result.id)])
        self.assertEqual(organize_service.apply_calls, ["org-binding"])
        self.assertEqual(result.execution_status, SubscriptionRunStatus.APPLIED)
        self.assertEqual(result.organize_preview.organize_status, OrganizeStatus.APPLIED)

    def test_execute_no_result_records_real_host_search_reason(self) -> None:
        executed_job = build_search_job_summary(status=JobStatus.NO_RESULT)
        executed_job.summary = {
            "active_search_adapter": "real_host_search",
            "candidate_count": 0,
        }
        search_job_service = DummySearchJobService(executed_job=executed_job, candidates=[])
        organize_service = DummyOrganizeService()
        service = SubscriptionExecutionService(
            self.session,
            search_job_service=search_job_service,
            organize_service=organize_service,
            music_media_chain=DummyMusicMediaChain(),
            dispatch_service=None,
        )

        result = service.execute(self.subscription.id)

        self.assertEqual(result.execution_status, SubscriptionRunStatus.NO_RESULT)
        self.assertEqual(result.summary_json.get("search_outcome_reason"), "host_search_no_result")

    def test_execute_chart_entry_subscription_resolves_music_media_input_before_search(self) -> None:
        subscription = self.repository.create_subscription(
            subscription_type=SubscriptionType.CHART_ENTRY.value,
            target_id="rss-entry-001",
            target_name="Hello",
            target_entity_type=EntityType.TRACK.value,
            chart_source="rss_feed",
            chart_name="网易云热歌榜",
            mode="manual",
            preference_json={},
            target_payload_json={
                "music_media_input": {
                    "entity_hint": EntityType.TRACK.value,
                    "source_kind": "discovery",
                    "title": "Hello",
                    "artist_names": ["Adele"],
                    "album_title": "25",
                    "external_refs": {
                        "source_id": "song-123",
                        "source_url": "https://music.163.com/#/song?id=123",
                    },
                    "source_context": {
                        "provider": "rss_feed",
                        "family": "netease_playlist_tracks",
                    },
                    "raw_context": {},
                }
            },
            note="rss-subscription",
        )
        self.session.commit()
        self.session.refresh(subscription)

        search_job_service = DummySearchJobService(
            executed_job=build_search_job_summary(status=JobStatus.NO_RESULT),
            candidates=[],
        )
        organize_service = DummyOrganizeService()
        chain = DummyMusicMediaChain(
            MusicMediaInfo(
                entity_type=EntityType.TRACK,
                provider="musicbrainz",
                provider_id="recording-hello",
                title="Hello",
                artist_names=["Adele"],
                album_title="25",
                album_artist_names=[],
                related_artist_ids=[],
                related_track_ids=[],
                external_refs={},
                match_evidence=[],
                diagnostics=[],
                release_context={},
            )
        )
        service = SubscriptionExecutionService(
            self.session,
            search_job_service=search_job_service,
            organize_service=organize_service,
            music_media_chain=chain,
            dispatch_service=None,
        )

        result = service.execute(subscription.id)

        self.assertEqual(result.execution_status, SubscriptionRunStatus.NO_RESULT)
        self.assertEqual(len(chain.calls), 1)
        self.assertEqual(search_job_service.created_payloads[0].input.entity_hint, EntityType.TRACK)
        self.assertEqual(search_job_service.created_payloads[0].input.title, "Hello")
        self.assertEqual(search_job_service.created_payloads[0].input.artist_names, ["Adele"])

    def test_build_job_request_prefers_music_media_info_snapshot_for_search(self) -> None:
        service = SubscriptionExecutionService.__new__(SubscriptionExecutionService)
        service.music_media_chain = DummyMusicMediaChain()
        media = MusicMediaInfo(
            entity_type=EntityType.TRACK,
            provider="musicbrainz",
            provider_id="recording-hello",
            title="Hello",
            artist_names=["Adele"],
            album_title="25",
            album_artist_names=[],
            related_artist_ids=[],
            related_track_ids=[],
            external_refs={},
            match_evidence=[],
            diagnostics=[],
            release_context={},
            match_strategy="strong_ref",
        )
        subscription = type(
            "SubscriptionStub",
            (),
            {
                "id": "sub-001",
                "subscription_type": SubscriptionType.CHART_ENTRY.value,
                "target_entity_type": EntityType.TRACK.value,
                "target_id": "legacy-target",
                "mode": "manual",
                "preference_json": {},
                "target_payload_json": {
                    "music_media_info": media.model_dump(mode="json"),
                },
            },
        )()

        payload = service._build_job_request(subscription)

        self.assertEqual(payload.input.entity_hint, EntityType.TRACK)
        self.assertEqual(payload.input.title, "Hello")
        self.assertEqual(payload.input.artist_names, ["Adele"])
        self.assertEqual(payload.input.album_title, "25")

    def test_resolve_or_build_music_media_info_uses_snapshot_when_present(self) -> None:
        service = SubscriptionExecutionService.__new__(SubscriptionExecutionService)
        service.session = SimpleNamespace(flush=lambda: None)
        service.music_media_chain = DummyMusicMediaChain()
        subscription = type(
            "SubscriptionStub",
            (),
            {
                "subscription_type": SubscriptionType.CHART_ENTRY.value,
                "target_entity_type": EntityType.TRACK.value,
                "target_id": "legacy-target",
                "target_payload_json": {
                    "music_media_info": {
                        "entity_type": EntityType.TRACK.value,
                        "provider": "musicbrainz",
                        "provider_id": "recording-hello",
                        "title": "Hello",
                        "artist_names": ["Adele"],
                        "album_title": "25",
                        "album_artist_names": [],
                        "related_artist_ids": [],
                        "related_track_ids": [],
                        "external_refs": {},
                        "match_evidence": [],
                        "diagnostics": [],
                        "release_context": {},
                    }
                },
            },
        )()

        media = service._resolve_or_build_music_media_info(subscription)

        self.assertIsNotNone(media)
        self.assertEqual(media.entity_type, EntityType.TRACK)
        self.assertEqual(media.provider_id, "recording-hello")

    def test_resolve_or_build_music_media_info_builds_from_music_media_input_snapshot(self) -> None:
        service = SubscriptionExecutionService.__new__(SubscriptionExecutionService)
        service.session = SimpleNamespace(flush=lambda: None)
        service.music_media_chain = DummyMusicMediaChain(
            MusicMediaInfo(
                entity_type=EntityType.TRACK,
                provider="musicbrainz",
                provider_id="recording-hello",
                title="Hello",
                artist_names=["Adele"],
                album_title="25",
                album_artist_names=[],
                related_artist_ids=[],
                related_track_ids=[],
                external_refs={},
                match_evidence=[],
                diagnostics=[],
                release_context={},
            )
        )
        subscription = type(
            "SubscriptionStub",
            (),
            {
                "subscription_type": SubscriptionType.CHART_ENTRY.value,
                "target_entity_type": EntityType.TRACK.value,
                "target_id": "legacy-target",
                "target_payload_json": {
                    "music_media_input": {
                        "entity_hint": EntityType.TRACK.value,
                        "source_kind": "discovery",
                        "title": "Hello",
                        "artist_names": ["Adele"],
                        "album_title": "25",
                        "external_refs": {},
                        "source_context": {},
                        "raw_context": {},
                    }
                },
            },
        )()

        media = service._resolve_or_build_music_media_info(subscription)

        self.assertIsNotNone(media)
        self.assertEqual(media.entity_type, EntityType.TRACK)
        self.assertEqual(media.provider_id, "recording-hello")
        self.assertEqual(len(service.music_media_chain.calls), 1)
        self.assertEqual(
            subscription.target_payload_json["music_media_info"]["provider_id"],
            "recording-hello",
        )


if __name__ == "__main__":
    unittest.main()
