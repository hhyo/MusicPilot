"""Tests for Phase 7A MoviePilot semantic alignment."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.adapters.download_dispatch import RealDownloadDispatchAdapter
from app.adapters.host_http import HostTransportError
from app.adapters.host_search import RealHostSearchAdapter
from app.adapters.host_storage_runtime import HostStorageRuntimeBridge
from app.adapters.organize import RealOrganizeAdapter
from app.core.config import Settings
from app.schemas.acquisition import SearchCandidateDetail
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.orchestration import (
    OrganizeConflictPolicy,
    OrganizePlan,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)
from app.services.host_path_handoff import HostPathHandoffService
from app.services.query_builder import QueryBuilderService

from test_query_builder import build_album_detail


class FakeHostClient:
    def __init__(self, *, get_responses=None, post_responses=None):
        self.get_responses = get_responses or {}
        self.post_responses = post_responses or {}
        self.calls: list[tuple[str, str, dict | None, dict | None]] = []

    def get_json(self, path, *, params=None, auth_mode=None):  # noqa: ANN001
        self.calls.append(("GET", path, params, {"auth_mode": auth_mode}))
        response = self.get_responses.get(path)
        if isinstance(response, Exception):
            raise response
        return response

    def post_json(self, path, payload, *, params=None, auth_mode=None):  # noqa: ANN001
        self.calls.append(("POST", path, params, {"auth_mode": auth_mode, "payload": payload}))
        response = self.post_responses.get(path)
        if isinstance(response, Exception):
            raise response
        return response


class FakeTransferRuntime:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response or {"success": True, "organize_status": "applied", "message": ""}
        self.error = error
        self.calls: list[dict] = []

    def manual_transfer(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeStorageRuntime:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response or {"success": True, "organize_status": "applied", "message": "", "target_path": ""}
        self.error = error
        self.calls: list[dict] = []

    def transfer_file(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeStorageOper:
    def __init__(
        self,
        *,
        existing_paths: set[str] | None = None,
        folder_exists: bool = True,
        transfer_success: bool = True,
    ):
        self.existing_paths = existing_paths or set()
        self.folder_exists = folder_exists
        self.transfer_success = transfer_success
        self.calls: list[tuple[str, tuple]] = []

    def get_item(self, path):  # noqa: ANN001
        normalized = Path(path).as_posix()
        if normalized in self.existing_paths:
            return SimpleNamespace(path=normalized, type="file", storage="local")
        return None

    def get_folder(self, path):  # noqa: ANN001
        normalized = Path(path).as_posix()
        self.calls.append(("get_folder", (normalized,)))
        if self.folder_exists:
            return SimpleNamespace(path=normalized, type="dir", storage="local")
        return None

    def copy(self, source_item, target_parent, target_name):  # noqa: ANN001
        self.calls.append(("copy", (source_item.path, Path(target_parent).as_posix(), target_name)))
        return self.transfer_success

    def move(self, source_item, target_parent, target_name):  # noqa: ANN001
        self.calls.append(("move", (source_item.path, Path(target_parent).as_posix(), target_name)))
        return self.transfer_success

    def link(self, source_item, target_file):  # noqa: ANN001
        self.calls.append(("link", (source_item.path, Path(target_file).as_posix())))
        return self.transfer_success

    def softlink(self, source_item, target_file):  # noqa: ANN001
        self.calls.append(("softlink", (source_item.path, Path(target_file).as_posix())))
        return self.transfer_success


class FakeManagerModule:
    def __init__(
        self,
        *,
        source_item=None,
        supported_types: dict[str, bool] | None = None,
        source_oper: FakeStorageOper | None = None,
        target_oper: FakeStorageOper | None = None,
    ):
        self.source_item = source_item
        self.supported_types = supported_types or {"copy": True, "move": True, "link": True, "softlink": True}
        self.source_oper = source_oper or FakeStorageOper()
        self.target_oper = target_oper or FakeStorageOper()
        self.calls: list[tuple[str, tuple]] = []

    @classmethod
    def for_copy_success(cls, *, source_path: str, target_root: str) -> "FakeManagerModule":
        source_item = SimpleNamespace(path=source_path, type="file", storage="local")
        source_oper = FakeStorageOper()
        target_oper = FakeStorageOper()
        manager = cls(
            source_item=source_item,
            source_oper=source_oper,
            target_oper=target_oper,
        )
        target_oper.get_folder(Path(target_root))
        target_oper.calls.clear()
        return manager

    def get_file_item(self, *, storage, path):  # noqa: ANN001
        normalized = Path(path).as_posix()
        self.calls.append(("get_file_item", (storage, normalized)))
        if self.source_item and storage == self.source_item.storage and normalized == self.source_item.path:
            return self.source_item
        return None

    def support_transtype(self, target_storage):  # noqa: ANN001
        self.calls.append(("support_transtype", (target_storage,)))
        return self.supported_types

    def get_storage_oper(self, storage):  # noqa: ANN001
        self.calls.append(("get_storage_oper", (storage,)))
        if storage == "local":
            if self.source_item and storage == self.source_item.storage:
                return self.source_oper
            return self.target_oper
        return None


def build_settings(**overrides) -> Settings:  # noqa: ANN003
    base = {
        "host_integration_enabled": True,
        "host_base_url": "http://127.0.0.1:19090",
        "host_auth_token": "stub-token",
        "host_search_title_path": "/api/v1/search/title",
        "host_search_media_path": "/api/v1/search/media",
        "host_downloaders_path": "/api/v1/download/clients",
        "host_download_add_path": "/api/v1/download/add",
        "host_transfer_name_path": "/api/v1/transfer/name",
        "host_transfer_manual_path": "/api/v1/transfer/manual",
        "host_history_download_path": "/api/v1/history/download",
        "host_history_transfer_path": "/api/v1/history/transfer",
        "host_history_download_page_size": 50,
        "host_history_download_max_pages": 2,
        "host_history_transfer_page_size": 50,
        "host_history_transfer_max_pages": 2,
        "host_verification_state": "unverified",
    }
    base.update(overrides)
    return Settings(**base)


def build_candidate(**overrides) -> SearchCandidateDetail:  # noqa: ANN003
    payload = {
        "id": "candidate-001",
        "job_id": "job-001",
        "site_id": "1",
        "site_name": "Stub Site",
        "title": "Adele - 25 (2015) FLAC",
        "normalized_title": "adele 25 2015 flac",
        "size_bytes": 734003200,
        "seeders": 42,
        "peers": 8,
        "format_tag": "flac",
        "bitrate_kbps": 1000,
        "source_tags": ["lossless", "album"],
        "raw_score": 100,
        "score_total": 100,
        "score_breakdown": {},
        "decision": "auto_download",
        "reason_codes": [],
        "dispatchable": True,
        "dispatch_status": "pending",
        "mock": False,
        "note": "candidate",
        "created_at": "2026-04-03T00:00:00Z",
        "raw_payload": {},
    }
    payload.update(overrides)
    return SearchCandidateDetail(**payload)  # type: ignore[arg-type]


def build_plan() -> OrganizePlan:
    return OrganizePlan(
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
        target_library_path="/library/music/Adele/2015 - 25/hello.flac",
        target_relative_path="Adele/2015 - 25/hello.flac",
        strategy_note="test plan",
    )


class RealHostSearchAdapterTest(unittest.TestCase):
    def test_search_title_maps_moviepilot_context_shape(self) -> None:
        detail = build_album_detail()
        query_build = QueryBuilderService.build_from_detail(detail)
        client = FakeHostClient(
            get_responses={
                "/api/v1/search/title": {
                    "success": True,
                    "data": [
                        {
                            "meta_info": {"title": "Adele 25"},
                            "media_info": {},
                            "torrent_info": {
                                "site": 1,
                                "site_name": "Stub PT",
                                "title": "Adele - 25 (2015) FLAC",
                                "description": "Lossless",
                                "enclosure": "magnet:?xt=urn:btih:1",
                                "page_url": "https://stub/item/1",
                                "size": 734003200,
                                "seeders": 42,
                                "peers": 8,
                                "labels": ["lossless", "album"],
                            },
                        }
                    ],
                }
            }
        )
        adapter = RealHostSearchAdapter(settings=build_settings(), client=client)  # type: ignore[arg-type]

        results = adapter.search(query_build=query_build, detail=detail)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].site_name, "Stub PT")
        self.assertEqual(results[0].size_bytes, 734003200)
        self.assertEqual(results[0].adapter_resolution.verification_state, VerificationState.VERIFIED)
        self.assertEqual(results[0].adapter_resolution.adapter_mode, AdapterMode.HOST)
        self.assertIn("host_context", results[0].raw_payload)
        self.assertEqual(client.calls[0][0], "GET")
        self.assertEqual(client.calls[0][1], "/api/v1/search/title")

    def test_search_media_positive_sample_is_verified(self) -> None:
        detail = build_album_detail()
        query_build = QueryBuilderService.build_from_detail(detail)
        query_build.query_context.external_ids["moviepilot_tmdb_id"] = "447273"
        client = FakeHostClient(
            get_responses={
                "/api/v1/search/media/": {},
                "/api/v1/search/media/tmdb:447273": {
                    "success": True,
                    "data": [
                        {
                            "media_info": {"title": "白雪公主", "year": "2025", "tmdb_id": 447273},
                            "torrent_info": {
                                "site": 2,
                                "site_name": "馒头",
                                "title": "Snow White 2025 2160p BluRay DoVi x265 10bit 4Audios TrueHD Atmos 7.1-WiKi",
                                "size": 2147483648,
                                "seeders": 30,
                                "peers": 5,
                                "labels": ["movie", "2160p"],
                            },
                        }
                    ],
                },
            }
        )
        adapter = RealHostSearchAdapter(settings=build_settings(), client=client)  # type: ignore[arg-type]

        results = adapter.search(query_build=query_build, detail=detail)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].adapter_resolution.verification_state, VerificationState.VERIFIED)
        self.assertEqual(results[0].raw_payload["host_media_reference"]["tmdbid"], 447273)


class RealDownloadDispatchAdapterTest(unittest.TestCase):
    def test_dispatch_maps_moviepilot_download_add_failure(self) -> None:
        candidate = build_candidate(
            raw_payload={
                "host_context": {
                    "torrent_info": {
                        "site": 1,
                        "site_name": "Stub Site",
                        "title": "MusicPilot Validation Nonexistent Release ABC123XYZ",
                        "description": "validation",
                        "enclosure": "magnet:?xt=urn:btih:1",
                    }
                }
            }
        )
        client = FakeHostClient(
            get_responses={"/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]}},
            post_responses={
                "/api/v1/download/add": {
                    "success": False,
                    "message": "无法识别媒体信息",
                    "data": {},
                }
            },
        )
        adapter = RealDownloadDispatchAdapter(
            settings=build_settings(),
            client=client,  # type: ignore[arg-type]
            path_handoff_service=HostPathHandoffService(settings=build_settings(), client=client),  # type: ignore[arg-type]
        )

        result = adapter.dispatch(candidate=candidate, downloader_id="mock-downloader", manual_confirm=True)

        self.assertEqual(result.dispatch_backend, AdapterMode.HOST)
        self.assertEqual(result.dispatch_status, "host_rejected")
        self.assertEqual(result.target_downloader, "QB")
        self.assertEqual(result.failure_reason, "无法识别媒体信息")
        self.assertIn("downloader_name_remapped", result.fallback_reason or "")

    def test_dispatch_add_includes_tmdb_hint_when_media_payload_missing(self) -> None:
        candidate = build_candidate(
            raw_payload={
                "host_context": {
                    "torrent_info": {
                        "site": 1,
                        "site_name": "Stub Site",
                        "title": "Snow White 2025 2160p BluRay",
                        "description": "validation",
                        "enclosure": "magnet:?xt=urn:btih:1",
                    },
                    "media_info": {},
                },
                "host_media_reference": {"tmdbid": 447273},
            }
        )
        client = FakeHostClient(
            get_responses={"/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]}},
            post_responses={
                "/api/v1/download/add": {
                    "success": False,
                    "message": "任务添加失败",
                    "data": {},
                }
            },
        )
        settings = build_settings()
        adapter = RealDownloadDispatchAdapter(
            settings=settings,
            client=client,  # type: ignore[arg-type]
            path_handoff_service=HostPathHandoffService(settings=settings, client=client),  # type: ignore[arg-type]
        )

        adapter.dispatch(candidate=candidate, downloader_id="QB", manual_confirm=True)

        payload = client.calls[-1][3]["payload"]
        self.assertEqual(client.calls[-1][1], "/api/v1/download/add")
        self.assertEqual(payload["tmdbid"], 447273)

    def test_dispatch_success_resolves_history_download_path(self) -> None:
        candidate = build_candidate(
            raw_payload={
                "host_context": {
                    "torrent_info": {
                        "site": 1,
                        "site_name": "Stub Site",
                        "title": "It Was Just an Accident 2025 BluRay",
                        "description": "validation",
                        "enclosure": "magnet:?xt=urn:btih:1",
                    },
                    "media_info": {
                        "type": "电影",
                        "title": "普通事故",
                        "year": "2025",
                        "tmdb_id": 1456349,
                    },
                }
            }
        )
        client = FakeHostClient(
            get_responses={
                "/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]},
                "/api/v1/history/download": {
                    "items": [
                        {
                            "download_hash": "stub-download-001",
                            "title": "普通事故",
                            "path": "/downloads/movie/Un.Semplice.Incidente.2025.MULTi.COMPLETE.BLURAY-FHC",
                            "torrent_name": "Yek tasadof-e sadeh 2025 1080p ITA Blu-ray AVC DTS-HD MA 5.1-FHC",
                            "date": "2026-04-03 22:36:41",
                        }
                    ]
                },
            },
            post_responses={
                "/api/v1/download/": {
                    "success": True,
                    "message": None,
                    "data": {"download_id": "stub-download-001"},
                }
            },
        )
        settings = build_settings()
        adapter = RealDownloadDispatchAdapter(
            settings=settings,
            client=client,  # type: ignore[arg-type]
            path_handoff_service=HostPathHandoffService(settings=settings, client=client),  # type: ignore[arg-type]
        )

        result = adapter.dispatch(candidate=candidate, downloader_id="QB", manual_confirm=True)

        self.assertTrue(result.dispatchable)
        self.assertEqual(result.dispatch_status, "host_submitted")
        self.assertEqual(result.verification_state, VerificationState.VERIFIED)
        self.assertIsNotNone(result.path_handoff)
        self.assertEqual(result.path_handoff.source_filetype, "dir")
        self.assertEqual(
            result.path_handoff.handoff_status,
            "resolved_from_history_download",
        )
        self.assertEqual(result.host_response_summary["download_id"], "stub-download-001")
        self.assertEqual(result.host_response_summary["endpoint_type"], "download_media")

    def test_download_handoff_and_transfer_history_have_distinct_semantics(self) -> None:
        client = FakeHostClient(
            get_responses={
                "/api/v1/history/download": {"items": []},
                "/api/v1/history/transfer": {
                    "success": True,
                    "data": {
                        "list": [
                            {
                                "download_hash": "stub-download-002",
                                "title": "阿根廷1985",
                                "src": "/downloads/movie/Argentina.1985.2022.WEB-DL.1080p.mkv",
                                "dest": "/downloads/media/movie/阿根廷1985 (2022)/Argentina.1985.2022.WEB-DL.1080p.mkv",
                                "status": True,
                                "date": "2026-04-04 00:00:00",
                            }
                        ],
                        "total": 1,
                    },
                },
            }
        )
        handoff_service = HostPathHandoffService(settings=build_settings(), client=client)  # type: ignore[arg-type]

        self.assertIsNone(handoff_service.resolve_from_download_with_retry("stub-download-002"))
        replay = handoff_service.resolve_from_transfer("stub-download-002")
        self.assertIsNotNone(replay)
        self.assertEqual(replay.handoff_status, "resolved_from_history_transfer")
        self.assertEqual(replay.source_filetype, "file")
        self.assertEqual(replay.source_path, "/downloads/movie/Argentina.1985.2022.WEB-DL.1080p.mkv")


class RealOrganizeAdapterTest(unittest.TestCase):
    def test_preview_requires_source_path(self) -> None:
        adapter = RealOrganizeAdapter(settings=build_settings(), client=FakeHostClient())  # type: ignore[arg-type]

        with self.assertRaises(HostTransportError) as context:
            adapter.preview(
                candidate=build_candidate(),
                metadata_detail=None,
                binding_id=None,
                plan=build_plan(),
            )

        self.assertEqual(context.exception.reason_code, "moviepilot_transfer_source_path_missing")

    def test_preview_maps_transfer_name_success(self) -> None:
        candidate = build_candidate(
            raw_payload={"host_transfer_source_path": "/downloads/Adele-25.flac", "host_transfer_filetype": "file"}
        )
        client = FakeHostClient(
            get_responses={
                "/api/v1/transfer/name": {
                    "success": True,
                    "data": {"name": "Organized-Adele-25.flac"},
                }
            }
        )
        adapter = RealOrganizeAdapter(settings=build_settings(), client=client)  # type: ignore[arg-type]

        result = adapter.preview(
            candidate=candidate,
            metadata_detail=None,
            binding_id=None,
            plan=build_plan(),
        )

        self.assertEqual(result.organize_backend, AdapterMode.HOST)
        self.assertEqual(result.organize_status, OrganizeStatus.PREVIEW_READY)
        self.assertEqual(result.verification_state, VerificationState.VERIFIED)
        self.assertTrue(result.target_relative_path.endswith("Organized-Adele-25.flac"))
        self.assertEqual(client.calls[0][2], {"path": "/downloads/Adele-25.flac", "filetype": "file"})

    def test_apply_maps_music_storage_failure(self) -> None:
        candidate = build_candidate(
            raw_payload={"host_transfer_source_path": "/downloads/nonexistent-file.flac", "host_transfer_filetype": "file"}
        )
        runtime = FakeStorageRuntime(
            response={
                "success": False,
                "organize_status": "failed",
                "message": "nonexistent-file.flac 没有找到可整理的媒体文件",
            }
        )
        adapter = RealOrganizeAdapter(
            settings=build_settings(),
            client=FakeHostClient(),  # type: ignore[arg-type]
            storage_runtime=runtime,
        )

        result = adapter.apply(
            organize_job_id="organize-001",
            candidate=candidate,
            metadata_detail=None,
            binding_id=None,
            plan=build_plan(),
        )

        self.assertEqual(result.organize_backend, AdapterMode.HOST)
        self.assertEqual(result.organize_status, OrganizeStatus.FAILED)
        self.assertEqual(result.verification_state, VerificationState.VERIFIED)
        self.assertIn("没有找到可整理的媒体文件", result.failure_reason or "")
        self.assertEqual(runtime.calls[0]["source_fileitem"]["path"], "/downloads/nonexistent-file.flac")
        self.assertEqual(runtime.calls[0]["source_fileitem"]["storage"], "local")
        self.assertEqual(runtime.calls[0]["source_fileitem"]["type"], "file")
        self.assertEqual(runtime.calls[0]["target_directory"], "/library/music/Adele/2015 - 25")
        self.assertEqual(runtime.calls[0]["target_filename"], "hello.flac")

    def test_apply_maps_music_storage_success(self) -> None:
        candidate = build_candidate(
            raw_payload={"host_transfer_source_path": "/downloads/Adele-25.flac", "host_transfer_filetype": "file"}
        )
        runtime = FakeStorageRuntime(
            response={
                "success": True,
                "organize_status": "applied",
                "message": "",
                "target_path": "/library/music/Adele/2015 - 25/hello.flac",
            }
        )
        adapter = RealOrganizeAdapter(
            settings=build_settings(),
            client=FakeHostClient(),  # type: ignore[arg-type]
            storage_runtime=runtime,
        )

        result = adapter.apply(
            organize_job_id="organize-002",
            candidate=candidate,
            metadata_detail=None,
            binding_id=None,
            plan=build_plan(),
        )

        self.assertEqual(result.organize_backend, AdapterMode.HOST)
        self.assertEqual(result.organize_status, OrganizeStatus.APPLIED)
        self.assertEqual(result.verification_state, VerificationState.VERIFIED)
        self.assertEqual(
            result.integration_point,
            "RealOrganizeAdapter.apply.music_storage_runtime_transfer",
        )
        self.assertEqual(result.target_library_path, "/library/music/Adele/2015 - 25/hello.flac")

    def test_apply_passes_storage_runtime_payload_when_available(self) -> None:
        candidate = build_candidate(
            raw_payload={
                "host_transfer_source_path": "/downloads/The.Matrix.1999.1080p.WEB-DL.mkv",
                "host_transfer_filetype": "file",
                "host_media_reference": {
                    "tmdbid": 603,
                    "doubanid": "1291843",
                },
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
                "host_transfer_downloader": "QB",
            }
        )
        runtime = FakeStorageRuntime()
        adapter = RealOrganizeAdapter(
            settings=build_settings(),
            client=FakeHostClient(),  # type: ignore[arg-type]
            storage_runtime=runtime,
        )

        adapter.apply(
            organize_job_id="organize-003",
            candidate=candidate,
            metadata_detail=None,
            binding_id="bind-001",
            plan=build_plan(),
        )

        self.assertEqual(runtime.calls[0]["source_fileitem"]["path"], "/downloads/The.Matrix.1999.1080p.WEB-DL.mkv")
        self.assertEqual(runtime.calls[0]["target_directory"], "/library/music/Adele/2015 - 25")
        self.assertEqual(runtime.calls[0]["target_filename"], "hello.flac")
        self.assertEqual(runtime.calls[0]["transfer_type"], "copy")

    def test_apply_keeps_current_behavior_when_enhancement_fields_missing(self) -> None:
        candidate = build_candidate(
            raw_payload={"host_transfer_source_path": "/downloads/Adele-25.flac", "host_transfer_filetype": "file"}
        )
        runtime = FakeStorageRuntime()
        adapter = RealOrganizeAdapter(
            settings=build_settings(),
            client=FakeHostClient(),  # type: ignore[arg-type]
            storage_runtime=runtime,
        )

        adapter.apply(
            organize_job_id="organize-004",
            candidate=candidate,
            metadata_detail=None,
            binding_id=None,
            plan=build_plan(),
        )

        self.assertEqual(runtime.calls[0]["source_fileitem"]["path"], "/downloads/Adele-25.flac")
        self.assertEqual(runtime.calls[0]["target_filename"], "hello.flac")


class HostStorageRuntimeBridgeTest(unittest.TestCase):
    def test_transfer_file_uses_in_process_manager(self) -> None:
        bridge = HostStorageRuntimeBridge()
        source_oper = FakeStorageOper()
        target_oper = FakeStorageOper()
        fake_manager = FakeManagerModule(
            source_item=SimpleNamespace(
                path="/downloads/Adele/25/01 - Hello.flac",
                type="file",
                storage="local",
            ),
            source_oper=source_oper,
            target_oper=target_oper,
        )

        with patch.object(HostStorageRuntimeBridge, "_build_manager", return_value=fake_manager):
            result = bridge.transfer_file(
                source_fileitem={
                    "storage": "local",
                    "path": "/downloads/Adele/25/01 - Hello.flac",
                    "type": "file",
                    "name": "01 - Hello.flac",
                    "basename": "01 - Hello",
                    "extension": ".flac",
                    "size": 1024,
                },
                target_storage="local",
                target_directory="/library/music/Adele/2015 - 25",
                target_filename="hello.flac",
                transfer_type="copy",
                conflict_policy="skip_existing",
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["organize_status"], "applied")
        self.assertEqual(result["target_path"], "/library/music/Adele/2015 - 25/hello.flac")
        self.assertEqual(fake_manager.calls[0], ("get_file_item", ("local", "/downloads/Adele/25/01 - Hello.flac")))
        self.assertIn(("support_transtype", ("local",)), fake_manager.calls)
        self.assertIn(("copy", ("/downloads/Adele/25/01 - Hello.flac", "/library/music/Adele/2015 - 25", "hello.flac")), source_oper.calls)

    def test_transfer_file_forwards_conflict_policy_to_target_resolution(self) -> None:
        bridge = HostStorageRuntimeBridge()
        source_oper = FakeStorageOper(existing_paths={"/library/music/Adele/2015 - 25/hello.flac"})
        target_oper = FakeStorageOper(existing_paths={"/library/music/Adele/2015 - 25/hello.flac"})
        fake_manager = FakeManagerModule(
            source_item=SimpleNamespace(
                path="/downloads/Adele/25/01 - Hello.flac",
                type="file",
                storage="local",
            ),
            source_oper=source_oper,
            target_oper=target_oper,
        )

        with patch.object(HostStorageRuntimeBridge, "_build_manager", return_value=fake_manager):
            result = bridge.transfer_file(
                source_fileitem={
                    "storage": "local",
                    "path": "/downloads/Adele/25/01 - Hello.flac",
                    "type": "file",
                    "name": "01 - Hello.flac",
                    "basename": "01 - Hello",
                    "extension": ".flac",
                    "size": 1024,
                },
                target_storage="local",
                target_directory="/library/music/Adele/2015 - 25",
                target_filename="hello.flac",
                transfer_type="copy",
                conflict_policy="append_suffix",
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["target_path"], "/library/music/Adele/2015 - 25/hello (1).flac")


class HostPathHandoffServiceTest(unittest.TestCase):
    def test_build_unresolved_marks_explicit_unresolved_state(self) -> None:
        service = HostPathHandoffService(settings=build_settings(), client=FakeHostClient())  # type: ignore[arg-type]

        handoff = service.build_unresolved(
            download_hash="hash-missing-001",
            handoff_source="moviepilot.runtime.history.download",
        )

        self.assertEqual(handoff.handoff_status, "handoff_unresolved")
        self.assertEqual(handoff.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(handoff.download_hash, "hash-missing-001")


if __name__ == "__main__":
    unittest.main()
