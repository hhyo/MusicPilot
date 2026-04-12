"""Unit tests for organize plan building and explicit host failure behavior."""

from __future__ import annotations

import unittest
from unittest.mock import patch
from tempfile import NamedTemporaryFile
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.organize import OrganizeAdapter
from app.models.acquisition import DownloadBindingModel, SearchCandidateModel, SearchJobModel
from app.models.base import Base
from app.schemas.integration import AdapterMode
from app.schemas.mvp import EntityType
from app.schemas.music_media import MusicMediaInfo
from app.schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeApplyRequest,
    OrganizeConflictPolicy,
    OrganizePreviewRequest,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)
from app.services.host_integration import HostIntegrationService, OrganizeAdapterResolver, OrganizeExecutionResult
from app.services.host_path_handoff import HostPathHandoffService
from app.services.organize import OrganizeService
from app.services.organize_strategy import OrganizeStrategyService
from app.repositories.orchestration import OrchestrationRepository

from tests.test_host_integration import DummyProbeAdapter, build_candidate, build_settings
from tests.test_moviepilot_semantics import (
    FakeHostClient,
    RealOrganizeAdapter,
    build_settings as build_moviepilot_settings,
)
from tests.test_query_builder import (
    build_album_detail,
    build_album_media,
    build_artist_detail,
    build_track_detail,
    build_track_media,
)


class DummyMusicMediaChain:
    def __init__(self) -> None:
        self.hydrate_calls: list[MusicMediaInfo] = []

    def hydrate(self, media: MusicMediaInfo):
        self.hydrate_calls.append(media)
        if media.entity_type == EntityType.TRACK:
            return build_track_detail()
        if media.entity_type == EntityType.ALBUM:
            return build_album_detail()
        return build_artist_detail()


class DummyMockOrganizeAdapter(OrganizeAdapter):
    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        return OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=OrganizeStatus.PREVIEW_READY,
            target_library_path=plan.target_library_path,
            target_relative_path=plan.target_relative_path,
            strategy_note=plan.strategy_note,
            integration_point="DummyMockOrganizeAdapter.preview",
            mock=True,
            note="mock preview",
        )

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        return OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=OrganizeStatus.APPLIED,
            target_library_path=plan.target_library_path,
            target_relative_path=plan.target_relative_path,
            strategy_note=plan.strategy_note,
            integration_point="DummyMockOrganizeAdapter.apply",
            mock=True,
            note="mock apply",
        )


class DummyBrokenHostOrganizeAdapter(OrganizeAdapter):
    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        raise RuntimeError("host organize preview boom")

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        raise RuntimeError("host organize apply boom")


class DummyApplyResolver:
    def __init__(self, result: OrganizeAdapterResult):
        self.result = result

    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):  # pragma: no cover - not used
        raise NotImplementedError

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):
        return OrganizeExecutionResult(result=self.result, resolution=self.result.adapter_resolution)


class CapturingApplyResolver:
    def __init__(self, result: OrganizeAdapterResult):
        self.result = result
        self.captured_candidate = None
        self.captured_binding_id = None

    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):  # pragma: no cover - not used
        raise NotImplementedError

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):
        self.captured_candidate = candidate
        self.captured_binding_id = binding_id
        return OrganizeExecutionResult(result=self.result, resolution=self.result.adapter_resolution)


class RaisingPathHandoffService:
    def resolve_from_download_with_retry(self, download_hash: str | None):  # noqa: ANN001
        raise AssertionError(f"host handoff lookup should not run for download_hash={download_hash}")

    def build_pending(self, *, download_hash: str | None, handoff_source: str):  # pragma: no cover - not used
        raise AssertionError("build_pending should not run in this test")

    def build_unresolved(self, *, download_hash: str | None, handoff_source: str):  # pragma: no cover - not used
        raise AssertionError("build_unresolved should not run in this test")


class OrganizeIntegrationTest(unittest.TestCase):
    def _build_strategy_snapshot(self) -> OrganizeStrategySnapshot:
        return OrganizeStrategySnapshot(
            strategy_name="music_default_layout",
            library_type="music",
            root_path="/library/music",
            artist_dir_template="{artist_name}",
            album_dir_template="{artist_name}/{year} - {album_title}",
            track_file_template="{track_title}.{format_ext}",
            conflict_policy=OrganizeConflictPolicy.SKIP_EXISTING,
            template_note="test",
        )

    def _build_music_context(self) -> dict[str, str]:
        return {
            "artist_name": "adele",
            "album_title": "25",
            "track_title": "hello",
            "title": "hello",
            "year": "2015",
            "format_ext": "flac",
        }

    def test_music_metadata_recognizer_prefers_track_detail_fields(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(update={"title": "Fallback Title", "format_tag": "flac"})
        detail = build_track_detail()

        result = MusicMetadataRecognizer().recognize(candidate=candidate, metadata_detail=detail)

        self.assertEqual(result.artist_name, "adele")
        self.assertEqual(result.album_title, "25")
        self.assertEqual(result.track_title, "hello")
        self.assertEqual(result.title, "hello")
        self.assertEqual(result.year, "2015")
        self.assertEqual(result.format_ext, "flac")

    def test_music_metadata_recognizer_falls_back_to_candidate_fields(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(
            update={
                "title": "Adele Live",
                "site_name": "Tracker Artist",
                "format_tag": "mp3",
            }
        )

        result = MusicMetadataRecognizer().recognize(candidate=candidate, metadata_detail=None)

        self.assertEqual(result.title, "adele-live")
        self.assertEqual(result.artist_name, "tracker-artist")
        self.assertEqual(result.album_title, "adele-live")
        self.assertEqual(result.track_title, "adele-live")
        self.assertEqual(result.year, "unknown")
        self.assertEqual(result.format_ext, "mp3")

    def test_music_metadata_recognizer_uses_artist_detail_title_for_artist_entity(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(
            update={
                "title": "Fallback Album",
                "site_name": "Fallback Site",
                "format_tag": "aac",
            }
        )
        detail = build_artist_detail()

        result = MusicMetadataRecognizer().recognize(candidate=candidate, metadata_detail=detail)

        self.assertEqual(result.artist_name, "adele")
        self.assertEqual(result.album_title, "adele")
        self.assertEqual(result.track_title, "adele")
        self.assertEqual(result.title, "adele")
        self.assertEqual(result.year, "2008")
        self.assertEqual(result.format_ext, "aac")

    def test_music_metadata_recognizer_uses_source_path_hints_when_metadata_missing(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(
            update={
                "title": "Fallback Title",
                "site_name": "Fallback Site",
                "format_tag": "flac",
                "raw_payload": {
                    "host_transfer_source_path": "/downloads/Adele/2015 - 25/01 - Hello.flac",
                },
            }
        )

        result = MusicMetadataRecognizer().recognize(candidate=candidate, metadata_detail=None)

        self.assertEqual(result.title, "hello")
        self.assertEqual(result.artist_name, "adele")
        self.assertEqual(result.album_title, "25")
        self.assertEqual(result.track_title, "hello")
        self.assertEqual(result.year, "2015")
        self.assertEqual(result.format_ext, "flac")

    def test_music_metadata_recognizer_prefers_metadata_detail_over_source_path_hints(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(
            update={
                "format_tag": "mp3",
                "raw_payload": {
                    "host_transfer_source_path": "/downloads/Someone Else/2001 - Wrong Album/02 - Wrong Song.mp3",
                },
            }
        )

        result = MusicMetadataRecognizer().recognize(candidate=candidate, metadata_detail=build_track_detail())

        self.assertEqual(result.title, "hello")
        self.assertEqual(result.artist_name, "adele")
        self.assertEqual(result.album_title, "25")
        self.assertEqual(result.track_title, "hello")
        self.assertEqual(result.year, "2015")
        self.assertEqual(result.format_ext, "mp3")

    def test_music_metadata_recognizer_uses_embedded_tags_before_source_path_hints(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(
            update={
                "title": "Fallback Title",
                "site_name": "Fallback Site",
                "format_tag": "flac",
                "raw_payload": {
                    "host_transfer_source_path": "/downloads/Adele/2015 - Wrong Album/01 - Wrong Song.flac",
                },
            }
        )
        recognizer = MusicMetadataRecognizer()

        with patch.object(
            recognizer,
            "_read_embedded_tag_hints",
            return_value={
                "title": "Hello",
                "artist_name": "Adele",
                "album_title": "25",
                "year": "2015",
                "format_ext": "flac",
            },
            create=True,
        ):
            result = recognizer.recognize(candidate=candidate, metadata_detail=None)

        self.assertEqual(result.title, "hello")
        self.assertEqual(result.artist_name, "adele")
        self.assertEqual(result.album_title, "25")
        self.assertEqual(result.track_title, "hello")
        self.assertEqual(result.year, "2015")
        self.assertEqual(result.format_ext, "flac")

    def test_music_metadata_recognizer_reads_embedded_tag_hints_with_mutagen_mapping(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        recognizer = MusicMetadataRecognizer()
        with NamedTemporaryFile(suffix=".flac") as handle:
            with patch("app.services.music_metadata.MutagenFile") as mock_mutagen_file:
                mock_mutagen_file.return_value = SimpleNamespace(
                    tags={
                        "title": ["Hello"],
                        "artist": ["Adele"],
                        "album": ["25"],
                        "date": ["2015-11-20"],
                    }
                )

                hints = recognizer._read_embedded_tag_hints(handle.name)

        self.assertEqual(hints.title, "Hello")
        self.assertEqual(hints.track_title, "Hello")
        self.assertEqual(hints.artist_name, "Adele")
        self.assertEqual(hints.album_title, "25")
        self.assertEqual(hints.year, "2015")
        self.assertEqual(hints.format_ext, "flac")

    def test_music_metadata_recognizer_prefers_metadata_detail_over_embedded_tags(self) -> None:
        from app.services.music_metadata import MusicMetadataRecognizer

        candidate = build_candidate().model_copy(
            update={
                "format_tag": "flac",
                "raw_payload": {
                    "host_transfer_source_path": "/downloads/file.flac",
                },
            }
        )
        recognizer = MusicMetadataRecognizer()

        with patch.object(
            recognizer,
            "_read_embedded_tag_hints",
            return_value={
                "title": "Wrong Song",
                "artist_name": "Wrong Artist",
                "album_title": "Wrong Album",
                "year": "2001",
                "format_ext": "flac",
            },
            create=True,
        ):
            result = recognizer.recognize(candidate=candidate, metadata_detail=build_track_detail())

        self.assertEqual(result.title, "hello")
        self.assertEqual(result.artist_name, "adele")
        self.assertEqual(result.album_title, "25")
        self.assertEqual(result.track_title, "hello")
        self.assertEqual(result.year, "2015")
        self.assertEqual(result.format_ext, "flac")

    def test_strategy_service_builds_track_path_from_source_path_hints_when_track_metadata_is_partial(self) -> None:
        candidate = build_candidate().model_copy(
            update={
                "format_tag": "flac",
                "raw_payload": {
                    "host_transfer_source_path": "/downloads/Adele/2015 - 25/01 - Hello.flac",
                },
            }
        )
        detail = build_track_detail().model_copy(
            update={
                "artist_name": None,
                "album_title": None,
                "track_title": None,
                "year": None,
            }
        )
        service = OrganizeStrategyService(build_settings())

        plan = service.build_plan(candidate=candidate, metadata_detail=detail)

        self.assertEqual(plan.target_relative_path, "adele/2015 - 25/hello.flac")

    def test_strategy_service_builds_track_path_from_embedded_tags_when_track_metadata_is_partial(self) -> None:
        candidate = build_candidate().model_copy(
            update={
                "format_tag": "flac",
                "raw_payload": {
                    "host_transfer_source_path": "/downloads/unknown.flac",
                },
            }
        )
        service = OrganizeStrategyService(build_settings())
        detail = build_track_detail().model_copy(
            update={
                "artist_name": None,
                "album_title": None,
                "track_title": None,
                "year": None,
            }
        )

        with patch.object(
            service.metadata_recognizer,
            "_read_embedded_tag_hints",
            return_value={
                "title": "Hello",
                "artist_name": "Adele",
                "album_title": "25",
                "year": "2015",
                "format_ext": "flac",
            },
            create=True,
        ):
            plan = service.build_plan(candidate=candidate, metadata_detail=detail)

        self.assertEqual(plan.target_relative_path, "adele/2015 - 25/hello.flac")

    def test_music_layout_planner_uses_artist_template_for_artist_entity(self) -> None:
        from app.services.music_layout import MusicLayoutPlanner

        planner = MusicLayoutPlanner()

        path = planner.build_relative_path(
            snapshot=self._build_strategy_snapshot(),
            context=self._build_music_context(),
            metadata_detail=build_artist_detail(),
        )

        self.assertEqual(path, "adele")

    def test_music_layout_planner_uses_album_template_for_album_entity(self) -> None:
        from app.services.music_layout import MusicLayoutPlanner

        planner = MusicLayoutPlanner()

        path = planner.build_relative_path(
            snapshot=self._build_strategy_snapshot(),
            context=self._build_music_context(),
            metadata_detail=build_album_detail(),
        )

        self.assertEqual(path, "adele/2015 - 25")

    def test_music_layout_planner_uses_album_plus_track_for_track_entity(self) -> None:
        from app.services.music_layout import MusicLayoutPlanner

        planner = MusicLayoutPlanner()

        path = planner.build_relative_path(
            snapshot=self._build_strategy_snapshot(),
            context=self._build_music_context(),
            metadata_detail=build_track_detail(),
        )

        self.assertEqual(path, "adele/2015 - 25/hello.flac")

    def test_music_layout_planner_falls_back_to_artist_template_when_metadata_missing(self) -> None:
        from app.services.music_layout import MusicLayoutPlanner

        planner = MusicLayoutPlanner()

        path = planner.build_relative_path(
            snapshot=self._build_strategy_snapshot(),
            context=self._build_music_context(),
            metadata_detail=None,
        )

        self.assertEqual(path, "adele")

    def test_strategy_service_builds_album_relative_path(self) -> None:
        candidate = build_candidate()
        detail = build_album_detail()
        service = OrganizeStrategyService(build_settings())

        plan = service.build_plan(candidate=candidate, metadata_detail=detail)

        self.assertIn("adele", plan.target_relative_path)
        self.assertIn("2015", plan.target_relative_path)
        self.assertIn("25", plan.target_relative_path)
        self.assertTrue(plan.target_library_path.endswith(plan.target_relative_path))

    def test_runtime_state_reports_strict_host_organize_blocking_reason(self) -> None:
        service = HostIntegrationService(
            settings=build_settings(
                host_organize_mode="strict_host",
            ),
            probe_adapter=DummyProbeAdapter(),
        )

        runtime = service.runtime_state()

        self.assertEqual(runtime.active_organize_adapter, "real_organize")
        self.assertEqual(runtime.organize_fallback_reason, "strict_host_required:host_capability_unavailable")

    def test_prefer_host_organize_preview_raises_on_runtime_error(self) -> None:
        detail = build_album_detail()
        candidate = build_candidate()
        plan = OrganizeStrategyService(build_settings()).build_plan(candidate=candidate, metadata_detail=detail)
        service = HostIntegrationService(
            settings=build_settings(
                host_organize_mode="prefer_host",
                host_assume_organize_available=True,
            ),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = OrganizeAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockOrganizeAdapter(),
            host_adapter=DummyBrokenHostOrganizeAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.preview(candidate=candidate, metadata_detail=detail, binding_id=None, plan=plan)

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_organize_preview_runtime_error:RuntimeError", str(ctx.exception.detail))

    def test_prefer_host_organize_apply_raises_on_runtime_error(self) -> None:
        detail = build_album_detail()
        candidate = build_candidate()
        plan = OrganizeStrategyService(build_settings()).build_plan(candidate=candidate, metadata_detail=detail)
        service = HostIntegrationService(
            settings=build_settings(
                host_organize_mode="prefer_host",
                host_assume_organize_available=True,
            ),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = OrganizeAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockOrganizeAdapter(),
            host_adapter=DummyBrokenHostOrganizeAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.apply(
                organize_job_id="org-001",
                candidate=candidate,
                metadata_detail=detail,
                binding_id=None,
                plan=plan,
            )

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_organize_apply_runtime_error:RuntimeError", str(ctx.exception.detail))

    def test_strict_host_organize_preview_raises_when_capability_missing(self) -> None:
        detail = build_album_detail()
        candidate = build_candidate()
        plan = OrganizeStrategyService(build_settings()).build_plan(candidate=candidate, metadata_detail=detail)
        service = HostIntegrationService(
            settings=build_settings(host_organize_mode="strict_host"),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = OrganizeAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockOrganizeAdapter(),
            host_adapter=DummyBrokenHostOrganizeAdapter(),
        )

        with self.assertRaises(HTTPException):
            resolver.preview(candidate=candidate, metadata_detail=detail, binding_id=None, plan=plan)

    def test_organize_service_preview_returns_local_plan_preview_for_music_sources(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            detail = build_album_detail()
            media = build_album_media()
            settings = build_moviepilot_settings(
                host_organize_mode="prefer_host",
                host_assume_organize_available=True,
            )
            plan = OrganizeStrategyService(settings).build_plan(
                candidate=build_candidate(),
                metadata_detail=detail,
            )
            job = SearchJobModel(
                id="job-preview-001",
                trigger_source="manual",
                profile_id="default-lossless",
                mode="manual",
                status="queued",
                music_media_input={
                    "entity_hint": "album",
                    "source_kind": "manual",
                    "title": detail.title,
                    "artist_names": [detail.artist_name],
                    "album_title": detail.album_title,
                    "album_artist_names": [],
                    "external_refs": {},
                    "source_context": {},
                    "raw_context": {},
                },
                music_meta_base={
                    "entity_type": "album",
                    "canonical_title": detail.title,
                    "canonical_artist_names": [detail.artist_name],
                    "canonical_album_title": detail.album_title,
                    "canonical_album_artist_names": [],
                    "external_refs": {},
                    "source_refs": {},
                    "evidence": [],
                    "normalization_notes": [],
                },
                music_media_info=media.model_dump(mode="json"),
                query_payload={},
                summary_json={},
            )
            candidate = SearchCandidateModel(
                id="cand-preview-001",
                job_id=job.id,
                site_id="site-1",
                site_name="Stub PT",
                title="Adele - 25",
                normalized_title="adele 25",
                size_bytes=1024,
                seeders=1,
                peers=0,
                source_tags=[],
                score_breakdown={},
                reason_codes=[],
                raw_payload={
                    "host_transfer_source_path": "/downloads/Adele-25.flac",
                    "host_transfer_filetype": "file",
                },
            )
            session.add(job)
            session.add(candidate)
            session.commit()

            host_client = FakeHostClient(
                get_responses={
                    "/api/v1/transfer/name": {
                        "success": True,
                        "data": {"name": "Host-Only-Adele-25.flac"},
                    }
                }
            )
            service = OrganizeService(
                session=session,
                resolver=OrganizeAdapterResolver(
                    integration_service=HostIntegrationService(
                        settings=settings,
                        probe_adapter=DummyProbeAdapter(),
                    ),
                    mock_adapter=DummyMockOrganizeAdapter(),
                    host_adapter=RealOrganizeAdapter(settings=settings, client=host_client),  # type: ignore[arg-type]
                ),
                strategy_service=OrganizeStrategyService(settings),
                path_handoff_service=HostPathHandoffService(
                    settings=settings,
                    client=FakeHostClient(),  # type: ignore[arg-type]
                ),
                music_media_chain=DummyMusicMediaChain(),
            )

            result = service.preview_for_candidate(candidate_id=candidate.id)

            self.assertEqual(result.organize_status, OrganizeStatus.PREVIEW_READY)
            self.assertIn("preview", result.integration_point)
            self.assertNotIn("transfer_name", result.integration_point)
            self.assertEqual(result.target_library_path, plan.target_library_path)
            self.assertEqual(result.target_relative_path, plan.target_relative_path)
            self.assertEqual(host_client.calls, [])
        finally:
            session.close()

    def test_organize_service_preview_with_binding_keeps_local_plan_when_host_handoff_unavailable(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            detail = build_track_detail()
            media = build_track_media()
            settings = build_moviepilot_settings(
                host_base_url=None,
                host_organize_mode="prefer_host",
                host_assume_organize_available=True,
            )
            job = SearchJobModel(
                id="job-preview-binding-001",
                trigger_source="manual",
                profile_id="default-lossless",
                mode="manual",
                status="queued",
                music_media_input={
                    "entity_hint": "track",
                    "source_kind": "manual",
                    "title": detail.track_title,
                    "artist_names": [detail.artist_name],
                    "album_title": detail.album_title,
                    "album_artist_names": [],
                    "external_refs": {},
                    "source_context": {},
                    "raw_context": {},
                },
                music_meta_base={
                    "entity_type": "album",
                    "canonical_title": detail.title,
                    "canonical_artist_names": [detail.artist_name],
                    "canonical_album_title": detail.album_title,
                    "canonical_album_artist_names": [],
                    "external_refs": {},
                    "source_refs": {},
                    "evidence": [],
                    "normalization_notes": [],
                },
                music_media_info=media.model_dump(mode="json"),
                query_payload={},
                summary_json={},
            )
            candidate = SearchCandidateModel(
                id="cand-preview-binding-001",
                job_id=job.id,
                site_id="site-1",
                site_name="Stub PT",
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
            binding = DownloadBindingModel(
                id="bind-preview-binding-001",
                job_id=job.id,
                candidate_id=candidate.id,
                target_downloader="mock-downloader",
                downloader_task_id="mock-task-001",
                dispatchable=True,
                dispatch_status="mock_submitted",
                mock=False,
                note="binding",
                integration_point="test.binding",
                raw_payload={
                    "path_handoff": {
                        "download_hash": "mock-task-001",
                        "source_path": None,
                        "source_filetype": None,
                        "handoff_source": "moviepilot.runtime.history.download",
                        "handoff_status": "pending_history_sync",
                        "verification_state": "unverified",
                        "note": "pending",
                        "raw_summary": {"download_hash": "mock-task-001"},
                    }
                },
            )
            session.add(job)
            session.add(candidate)
            session.add(binding)
            session.commit()

            service = OrganizeService(
                session=session,
                resolver=OrganizeAdapterResolver(
                    integration_service=HostIntegrationService(
                        settings=settings,
                        probe_adapter=DummyProbeAdapter(),
                    ),
                    mock_adapter=DummyMockOrganizeAdapter(),
                    host_adapter=RealOrganizeAdapter(settings=settings, client=FakeHostClient()),  # type: ignore[arg-type]
                ),
                strategy_service=OrganizeStrategyService(settings),
                path_handoff_service=RaisingPathHandoffService(),  # type: ignore[arg-type]
                music_media_chain=DummyMusicMediaChain(),
            )

            result = service.preview(OrganizePreviewRequest(binding_id=binding.id))

            self.assertEqual(result.organize_status, OrganizeStatus.PREVIEW_READY)
            self.assertEqual(result.binding_id, binding.id)
            self.assertEqual(result.path_handoff.download_hash, "mock-task-001")
            self.assertEqual(result.path_handoff.handoff_status, "pending_history_sync")
            self.assertIn("local_music_plan_preview", result.integration_point)
        finally:
            session.close()

    def test_organize_service_apply_updates_record_after_direct_host_result(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            detail = build_album_detail()
            media = build_album_media()
            job = SearchJobModel(
                id="job-apply-001",
                trigger_source="manual",
                profile_id="default-lossless",
                mode="manual",
                status="queued",
                music_media_input={
                    "entity_hint": "album",
                    "source_kind": "manual",
                    "title": "25",
                    "artist_names": ["Adele"],
                    "album_title": "25",
                    "album_artist_names": [],
                    "external_refs": {},
                    "source_context": {},
                    "raw_context": {},
                },
                music_meta_base={
                    "entity_type": "album",
                    "canonical_title": detail.title,
                    "canonical_artist_names": [detail.artist_name],
                    "canonical_album_title": detail.album_title,
                    "canonical_album_artist_names": [],
                    "external_refs": {},
                    "source_refs": {},
                    "evidence": [],
                    "normalization_notes": [],
                },
                music_media_info=media.model_dump(mode="json"),
                query_payload={},
                summary_json={},
            )
            candidate = SearchCandidateModel(
                id="cand-apply-001",
                job_id=job.id,
                site_id="site-1",
                site_name="Stub PT",
                title="Adele - 25",
                normalized_title="adele 25",
                size_bytes=1024,
                seeders=1,
                peers=0,
                source_tags=[],
                score_breakdown={},
                reason_codes=[],
                raw_payload={
                    "host_transfer_source_path": "/downloads/Adele-25.flac",
                    "host_transfer_filetype": "file",
                },
            )
            session.add(job)
            session.add(candidate)
            session.commit()

            repository = OrchestrationRepository(session)
            preview_result = OrganizeAdapterResult(
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
                target_relative_path="Adele/2015 - 25/01 - Hello.flac",
                strategy_note="preview",
                integration_point="DummyPreview",
                capability_source="test",
                mock=False,
                note="preview",
            )
            record = repository.create_organize_record(
                subscription_run_id=None,
                search_job_id=job.id,
                candidate_id=candidate.id,
                binding_id=None,
                result=preview_result,
            )
            session.commit()
            session.refresh(record)

            apply_result = preview_result.model_copy(
                update={
                    "organize_status": OrganizeStatus.APPLIED,
                    "integration_point": "DummyDirectResolver.apply",
                    "note": "applied",
                }
            )
            service = OrganizeService(
                session=session,
                resolver=DummyApplyResolver(apply_result),  # type: ignore[arg-type]
                strategy_service=OrganizeStrategyService(build_settings()),
                path_handoff_service=HostPathHandoffService(
                    settings=build_settings(),
                    client=FakeHostClient(),  # type: ignore[arg-type]
                ),
                music_media_chain=DummyMusicMediaChain(),
            )

            result = service.apply(OrganizeApplyRequest(organize_job_id=record.id))

            self.assertEqual(result.organize_status, OrganizeStatus.APPLIED)
            self.assertEqual(result.integration_point, "DummyDirectResolver.apply")
            refreshed = repository.get_organize_record(record.id)
            self.assertIsNotNone(refreshed)
            self.assertEqual(refreshed.organize_status, "applied")
            self.assertEqual(refreshed.integration_point, "DummyDirectResolver.apply")
        finally:
            session.close()

    def test_organize_service_apply_injects_binding_download_context_into_candidate_payload(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            detail = build_album_detail()
            media = build_album_media()
            job = SearchJobModel(
                id="job-apply-ctx-001",
                trigger_source="manual",
                profile_id="default-lossless",
                mode="manual",
                status="queued",
                music_media_input={
                    "entity_hint": "album",
                    "source_kind": "manual",
                    "title": "25",
                    "artist_names": ["Adele"],
                    "album_title": "25",
                    "album_artist_names": [],
                    "external_refs": {},
                    "source_context": {},
                    "raw_context": {},
                },
                music_meta_base={
                    "entity_type": "album",
                    "canonical_title": detail.title,
                    "canonical_artist_names": [detail.artist_name],
                    "canonical_album_title": detail.album_title,
                    "canonical_album_artist_names": [],
                    "external_refs": {},
                    "source_refs": {},
                    "evidence": [],
                    "normalization_notes": [],
                },
                music_media_info=media.model_dump(mode="json"),
                query_payload={},
                summary_json={},
            )
            candidate = SearchCandidateModel(
                id="cand-apply-ctx-001",
                job_id=job.id,
                site_id="site-1",
                site_name="Stub PT",
                title="The Matrix",
                normalized_title="the matrix",
                size_bytes=1024,
                seeders=1,
                peers=0,
                source_tags=[],
                score_breakdown={},
                reason_codes=[],
                raw_payload={
                    "host_transfer_source_path": "/downloads/The.Matrix.1999.1080p.WEB-DL.mkv",
                    "host_transfer_filetype": "file",
                },
            )
            binding = DownloadBindingModel(
                id="bind-apply-ctx-001",
                job_id=job.id,
                candidate_id=candidate.id,
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
                        "source_path": "/downloads/The.Matrix.1999.1080p.WEB-DL.mkv",
                        "source_filetype": "file",
                        "handoff_source": "moviepilot.runtime.history.download",
                        "handoff_status": "resolved_from_history_download",
                        "verification_state": "verified",
                        "note": "resolved",
                        "raw_summary": {},
                    },
                    "target_downloader": "QB",
                },
            )
            session.add(job)
            session.add(candidate)
            session.add(binding)
            session.commit()

            repository = OrchestrationRepository(session)
            preview_result = OrganizeAdapterResult(
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
                target_relative_path="Matrix/1999 - The Matrix/The.Matrix.1999.1080p.WEB-DL.mkv",
                strategy_note="preview",
                integration_point="DummyPreview",
                capability_source="test",
                mock=False,
                note="preview",
            )
            record = repository.create_organize_record(
                subscription_run_id=None,
                search_job_id=job.id,
                candidate_id=candidate.id,
                binding_id=binding.id,
                result=preview_result,
            )
            session.commit()
            session.refresh(record)

            apply_result = preview_result.model_copy(
                update={
                    "organize_status": OrganizeStatus.APPLIED,
                    "integration_point": "CapturingApplyResolver.apply",
                    "note": "applied",
                }
            )
            resolver = CapturingApplyResolver(apply_result)
            music_media_chain = DummyMusicMediaChain()
            service = OrganizeService(
                session=session,
                resolver=resolver,  # type: ignore[arg-type]
                strategy_service=OrganizeStrategyService(build_settings()),
                path_handoff_service=HostPathHandoffService(
                    settings=build_settings(),
                    client=FakeHostClient(),  # type: ignore[arg-type]
                ),
                music_media_chain=music_media_chain,
            )

            service.apply(OrganizeApplyRequest(organize_job_id=record.id))

            self.assertIsNotNone(resolver.captured_candidate)
            self.assertEqual(resolver.captured_binding_id, binding.id)
            self.assertEqual(resolver.captured_candidate.raw_payload["host_transfer_downloader"], "QB")
            self.assertEqual(
                resolver.captured_candidate.raw_payload["path_handoff"]["download_hash"],
                "stub-download-001",
            )
            self.assertEqual(len(music_media_chain.hydrate_calls), 1)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
