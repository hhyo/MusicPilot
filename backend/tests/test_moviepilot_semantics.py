"""Tests for Phase 7A MoviePilot semantic alignment."""

from __future__ import annotations

import unittest

from app.adapters.download_dispatch import RealDownloadDispatchAdapter
from app.adapters.host_http import HostTransportError
from app.adapters.host_search import RealHostSearchAdapter
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
        target_library_path="/library/music",
        target_relative_path="Adele/2015 - 25/01 - Hello.flac",
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

    def test_apply_maps_transfer_manual_failure(self) -> None:
        candidate = build_candidate(
            raw_payload={"host_transfer_source_path": "/downloads/nonexistent-file.flac", "host_transfer_filetype": "file"}
        )
        client = FakeHostClient(
            post_responses={
                "/api/v1/transfer/manual": {
                    "success": False,
                    "message": "nonexistent-file.flac 没有找到可整理的媒体文件",
                    "data": {},
                }
            }
        )
        adapter = RealOrganizeAdapter(settings=build_settings(), client=client)  # type: ignore[arg-type]

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
        payload = client.calls[0][3]["payload"]
        self.assertEqual(payload["fileitem"]["path"], "/downloads/nonexistent-file.flac")
        self.assertEqual(payload["fileitem"]["storage"], "local")
        self.assertEqual(payload["fileitem"]["type"], "file")


if __name__ == "__main__":
    unittest.main()
