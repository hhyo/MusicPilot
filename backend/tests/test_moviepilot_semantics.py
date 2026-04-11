"""Tests for Phase 7A MoviePilot semantic alignment."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.adapters.download_dispatch import RealDownloadDispatchAdapter
from app.adapters.host_http import HostTransportError
from app.adapters.host_search import RealHostSearchAdapter
from app.adapters.host_storage_runtime import HostStorageRuntimeBridge
from app.adapters.organize import RealOrganizeAdapter
from app.core.config import Settings, _derive_plugin_runtime_host_defaults
from app.services.subscription_scheduler import normalize_subscription_mode
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


class FakeDownloaderRuntime:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response or {
            "success": True,
            "dispatch_status": "host_submitted",
            "download_id": "torrent-hash-001",
            "message": "添加下载任务成功",
        }
        self.error = error
        self.calls: list[dict] = []

    def submit_torrent(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeDownloaderClient:
    def __init__(self, *, add_result=True, torrent_id="torrent-hash-001", torrents=None):
        self.add_result = add_result
        self.torrent_id = torrent_id
        self.torrents = torrents or []
        self.calls: list[tuple[str, dict]] = []

    def add_torrent(self, **kwargs):  # noqa: ANN003
        self.calls.append(("add_torrent", kwargs))
        return self.add_result

    def get_torrent_id_by_tag(self, tags, status=None):  # noqa: ANN001, ARG002
        self.calls.append(("get_torrent_id_by_tag", {"tags": tags}))
        return self.torrent_id

    def get_torrents(self, ids=None, tags=None):  # noqa: ANN001, ARG002
        self.calls.append(("get_torrents", {"ids": ids, "tags": tags}))
        return self.torrents, False


class FakeTransmissionTorrent:
    def __init__(self, hash_string: str):
        self.hashString = hash_string


class FakeTransmissionClient:
    def __init__(self, *, hash_string="torrent-hash-002"):
        self.hash_string = hash_string
        self.calls: list[tuple[str, dict]] = []

    def add_torrent(self, **kwargs):  # noqa: ANN003
        self.calls.append(("add_torrent", kwargs))
        return FakeTransmissionTorrent(self.hash_string)


class FakeDownloaderService:
    def __init__(self, *, type_name: str, instance):
        self.type = type_name
        self.instance = instance
        self.module = SimpleNamespace()
        self.config = SimpleNamespace(name="QB", type=type_name)


class FakeDownloaderHelper:
    def __init__(self, service):
        self.service = service
        self.calls: list[str | None] = []

    def get_service(self, name=None):  # noqa: ANN001
        self.calls.append(name)
        return self.service


class SubscriptionSchedulerSemanticsTest(unittest.TestCase):
    def test_normalize_scheduled_placeholder_to_scheduled(self) -> None:
        self.assertEqual(normalize_subscription_mode("scheduled_placeholder"), "scheduled")


class PluginRuntimeHostDefaultsTest(unittest.TestCase):
    def test_plugin_runtime_defaults_enable_host_integration_from_host_settings(self) -> None:
        host_settings = SimpleNamespace(PORT=3001, API_TOKEN="host-token")

        defaults = _derive_plugin_runtime_host_defaults(
            module_name="app.plugins.musicpilot.core.config",
            host_settings=host_settings,
        )

        self.assertEqual(
            defaults,
            {
                "host_integration_enabled": True,
                "host_base_url": "http://127.0.0.1:3001",
                "host_auth_token": "host-token",
                "host_auth_mode": "x_api_key",
                "host_api_key_header_name": "X-API-KEY",
                "host_search_mode": "prefer_host",
                "host_dispatch_mode": "prefer_host",
                "host_organize_mode": "prefer_host",
            },
        )

    def test_local_backend_module_name_does_not_enable_plugin_runtime_defaults(self) -> None:
        host_settings = SimpleNamespace(PORT=3001, API_TOKEN="host-token")

        defaults = _derive_plugin_runtime_host_defaults(
            module_name="app.core.config",
            host_settings=host_settings,
        )

        self.assertEqual(defaults, {})


class HostDownloaderRuntimeBridgeTest(unittest.TestCase):
    def test_runtime_bridge_submits_qbittorrent_with_optional_download_dir(self) -> None:
        from app.adapters.host_downloader_runtime import HostDownloaderRuntimeBridge

        client = FakeDownloaderClient()
        helper = FakeDownloaderHelper(FakeDownloaderService(type_name="qbittorrent", instance=client))
        bridge = HostDownloaderRuntimeBridge(helper_factory=lambda: helper, tag_generator=lambda: "dispatch-tag")

        result = bridge.submit_torrent(
            downloader="QB",
            content="magnet:?xt=urn:btih:1",
            title="Adele - 25",
            site_name="Stub Site",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["download_id"], "torrent-hash-001")
        add_call = client.calls[0][1]
        self.assertIsNone(add_call["download_dir"])

    def test_runtime_bridge_fetches_torrent_bytes_before_submitting_url_content(self) -> None:
        from app.adapters.host_downloader_runtime import HostDownloaderRuntimeBridge

        client = FakeDownloaderClient()
        helper = FakeDownloaderHelper(FakeDownloaderService(type_name="qbittorrent", instance=client))
        fetch_calls: list[dict] = []

        def fake_fetcher(**kwargs):  # noqa: ANN003
            fetch_calls.append(kwargs)
            return b"torrent-bytes"

        bridge = HostDownloaderRuntimeBridge(
            helper_factory=lambda: helper,
            tag_generator=lambda: "dispatch-tag",
            torrent_content_fetcher=fake_fetcher,
        )

        result = bridge.submit_torrent(
            downloader="QB",
            content="https://stub/download.php?id=1",
            title="Adele - 25",
            site_name="Stub Site",
            cookie="uid=1;pass=abc",
            site_ua="Mozilla/5.0",
            site_proxy=True,
        )

        self.assertTrue(result["success"])
        self.assertEqual(fetch_calls[0]["url"], "https://stub/download.php?id=1")
        self.assertEqual(fetch_calls[0]["cookie"], "uid=1;pass=abc")
        self.assertEqual(client.calls[0][1]["content"], b"torrent-bytes")

    def test_runtime_bridge_prefers_detail_page_download_link(self) -> None:
        from app.adapters.host_downloader_runtime import HostDownloaderRuntimeBridge

        client = FakeDownloaderClient()
        helper = FakeDownloaderHelper(FakeDownloaderService(type_name="qbittorrent", instance=client))
        fetch_calls: list[dict] = []

        def fake_fetcher(**kwargs):  # noqa: ANN003
            fetch_calls.append(kwargs)
            if kwargs["url"] == "https://stub/download.php?id=1":
                return b"<!DOCTYPE html><html></html>"
            return b"torrent-bytes"

        bridge = HostDownloaderRuntimeBridge(
            helper_factory=lambda: helper,
            tag_generator=lambda: "dispatch-tag",
            torrent_content_fetcher=fake_fetcher,
            detail_download_url_resolver=lambda **_: "https://stub/download.php?id=1&passkey=abc",
        )

        result = bridge.submit_torrent(
            downloader="QB",
            content="https://stub/download.php?id=1",
            page_url="https://stub/plugin_details.php?id=1",
            title="Adele - 25",
            site_name="Stub Site",
            cookie="uid=1;pass=abc",
            site_ua="Mozilla/5.0",
            site_proxy=False,
        )

        self.assertTrue(result["success"])
        self.assertEqual([call["url"] for call in fetch_calls], ["https://stub/download.php?id=1&passkey=abc"])
        self.assertEqual(client.calls[0][1]["content"], b"torrent-bytes")

    def test_runtime_bridge_reuses_existing_qbittorrent_task_when_add_returns_false(self) -> None:
        from app.adapters.host_downloader_runtime import HostDownloaderRuntimeBridge

        client = FakeDownloaderClient(
            add_result=False,
            torrents=[{"hash": "existing-hash-001", "name": "Adele - Hello [single] (2015) FLAC", "total_size": 30513562}],
        )
        helper = FakeDownloaderHelper(FakeDownloaderService(type_name="qbittorrent", instance=client))
        bridge = HostDownloaderRuntimeBridge(
            helper_factory=lambda: helper,
            tag_generator=lambda: "dispatch-tag",
            torrent_signature_resolver=lambda _content: ("Adele - Hello [single] (2015) FLAC", 30513562),
        )

        result = bridge.submit_torrent(
            downloader="QB",
            content=b"torrent-bytes",
            title="Adele - Hello",
            site_name="Stub Site",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["download_id"], "existing-hash-001")
        self.assertEqual(result["message"], "下载任务已存在")

    def test_plugin_runtime_defaults_require_host_token(self) -> None:
        host_settings = SimpleNamespace(PORT=3001, API_TOKEN=None)

        defaults = _derive_plugin_runtime_host_defaults(
            module_name="app.plugins.musicpilot.core.config",
            host_settings=host_settings,
        )

        self.assertEqual(defaults, {})


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
    def test_dispatch_music_candidate_uses_runtime_downloader_bridge(self) -> None:
        candidate = build_candidate(
            raw_payload={
                "host_context": {
                    "torrent_info": {
                        "site": 1,
                        "site_name": "Stub Site",
                        "title": "Adele - 25 (2015) FLAC",
                        "description": "lossless",
                        "enclosure": "magnet:?xt=urn:btih:1",
                        "page_url": "https://stub/item/1",
                        "site_cookie": "uid=1;pass=abc",
                    }
                }
            }
        )
        client = FakeHostClient(
            get_responses={
                "/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]},
                "/api/v1/history/download": {"items": []},
            }
        )
        runtime = FakeDownloaderRuntime(
            response={
                "success": True,
                "dispatch_status": "host_submitted",
                "download_id": "torrent-hash-001",
                "message": "添加下载任务成功",
            }
        )
        settings = build_settings()
        adapter = RealDownloadDispatchAdapter(
            settings=settings,
            client=client,  # type: ignore[arg-type]
            path_handoff_service=HostPathHandoffService(settings=settings, client=client),  # type: ignore[arg-type]
            downloader_runtime=runtime,
        )

        result = adapter.dispatch(candidate=candidate, downloader_id="QB", manual_confirm=True)

        self.assertEqual(result.dispatch_status, "host_submitted")
        self.assertEqual(result.downloader_task_id, "torrent-hash-001")
        self.assertEqual(runtime.calls[-1]["downloader"], "QB")
        self.assertEqual(runtime.calls[-1]["content"], "magnet:?xt=urn:btih:1")
        self.assertEqual(runtime.calls[-1]["page_url"], "https://stub/item/1")
        self.assertEqual(runtime.calls[-1]["cookie"], "uid=1;pass=abc")
        self.assertEqual([call[1] for call in client.calls if call[0] == "POST"], [])

    def test_dispatch_music_candidate_maps_runtime_failure_without_http_fallback(self) -> None:
        candidate = build_candidate(
            raw_payload={
                "host_context": {
                    "torrent_info": {
                        "site": 1,
                        "site_name": "Stub Site",
                        "title": "Adele - 25 (2015) FLAC",
                        "description": "lossless",
                        "enclosure": "magnet:?xt=urn:btih:1",
                    }
                }
            }
        )
        client = FakeHostClient(
            get_responses={"/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]}}
        )
        runtime = FakeDownloaderRuntime(
            response={
                "success": False,
                "dispatch_status": "host_rejected",
                "download_id": None,
                "message": "下载器拒绝任务",
            }
        )
        settings = build_settings()
        adapter = RealDownloadDispatchAdapter(
            settings=settings,
            client=client,  # type: ignore[arg-type]
            path_handoff_service=HostPathHandoffService(settings=settings, client=client),  # type: ignore[arg-type]
            downloader_runtime=runtime,
        )

        result = adapter.dispatch(candidate=candidate, downloader_id="QB", manual_confirm=True)

        self.assertEqual(result.dispatch_status, "host_rejected")
        self.assertEqual(result.failure_reason, "下载器拒绝任务")
        self.assertEqual([call[1] for call in client.calls if call[0] == "POST"], [])

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
                },
                "host_media_reference": {"tmdbid": 1},
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
    def test_preview_uses_local_music_plan_without_source_path(self) -> None:
        adapter = RealOrganizeAdapter(settings=build_settings(), client=FakeHostClient())  # type: ignore[arg-type]

        result = adapter.preview(
            candidate=build_candidate(),
            metadata_detail=None,
            binding_id=None,
            plan=build_plan(),
        )

        self.assertEqual(result.organize_backend, AdapterMode.HOST)
        self.assertEqual(result.organize_status, OrganizeStatus.PREVIEW_READY)
        self.assertEqual(result.verification_state, VerificationState.VERIFIED)
        self.assertIn("preview", result.integration_point)
        self.assertEqual(result.target_relative_path, build_plan().target_relative_path)

    def test_preview_uses_music_local_plan_preview_when_source_path_and_plan_exist(self) -> None:
        candidate = build_candidate(
            raw_payload={"host_transfer_source_path": "/downloads/Adele-25.flac", "host_transfer_filetype": "file"}
        )
        plan = build_plan()
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
            plan=plan,
        )

        self.assertEqual(result.organize_backend, AdapterMode.HOST)
        self.assertEqual(result.organize_status, OrganizeStatus.PREVIEW_READY)
        self.assertEqual(result.verification_state, VerificationState.VERIFIED)
        self.assertIn("preview", result.integration_point)
        self.assertNotIn("transfer_name", result.integration_point)
        self.assertEqual(result.target_library_path, plan.target_library_path)
        self.assertEqual(result.target_relative_path, plan.target_relative_path)
        self.assertEqual(client.calls, [])

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


class HostPluginEntryBootstrapTest(unittest.TestCase):
    def test_init_plugin_bootstraps_metadata_storage_for_host_runtime(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
        fake_plugins_module = type(sys)("app.plugins")

        class FakePluginBase:
            def __init__(self):
                pass

        fake_plugins_module._PluginBase = FakePluginBase  # type: ignore[attr-defined]
        previous_plugins_module = sys.modules.get("app.plugins")
        module_name = "musicpilot_host_entry_bootstrap_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin_module = importlib.util.module_from_spec(spec)

        sys.modules["app.plugins"] = fake_plugins_module
        sys.modules.pop(module_name, None)
        try:
            spec.loader.exec_module(plugin_module)  # type: ignore[union-attr]
            plugin = plugin_module.musicpilot()

            with patch.object(plugin_module, "_bootstrap_plugin_storage", create=True) as bootstrap_storage:
                plugin.init_plugin({"enabled": True})

            bootstrap_storage.assert_called_once_with()
        finally:
            sys.modules.pop(module_name, None)
            if previous_plugins_module is not None:
                sys.modules["app.plugins"] = previous_plugins_module
            else:
                sys.modules.pop("app.plugins", None)

    def test_plugin_entry_uses_vue_remote_render_mode(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
        fake_plugins_module = type(sys)("app.plugins")

        class FakePluginBase:
            def __init__(self):
                pass

        fake_plugins_module._PluginBase = FakePluginBase  # type: ignore[attr-defined]
        previous_plugins_module = sys.modules.get("app.plugins")
        module_name = "musicpilot_host_entry_render_mode_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin_module = importlib.util.module_from_spec(spec)

        sys.modules["app.plugins"] = fake_plugins_module
        sys.modules.pop(module_name, None)
        try:
            spec.loader.exec_module(plugin_module)  # type: ignore[union-attr]
            plugin = plugin_module.musicpilot()

            self.assertIsNone(plugin.get_page())
            with patch.object(plugin_module, "_resolve_remote_dist_path", return_value="static/remotes/test123"):
                self.assertEqual(plugin.get_render_mode(), ("vue", "static/remotes/test123"))
        finally:
            sys.modules.pop(module_name, None)
            if previous_plugins_module is not None:
                sys.modules["app.plugins"] = previous_plugins_module
            else:
                sys.modules.pop("app.plugins", None)

    def test_plugin_entry_declares_vue_remote_render_mode(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
        fake_plugins_module = type(sys)("app.plugins")

        class FakePluginBase:
            def __init__(self):
                pass

        fake_plugins_module._PluginBase = FakePluginBase  # type: ignore[attr-defined]
        previous_plugins_module = sys.modules.get("app.plugins")
        module_name = "musicpilot_host_entry_render_mode_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin_module = importlib.util.module_from_spec(spec)

        sys.modules["app.plugins"] = fake_plugins_module
        sys.modules.pop(module_name, None)
        try:
            spec.loader.exec_module(plugin_module)  # type: ignore[union-attr]
            plugin = plugin_module.musicpilot()

            with patch.object(plugin_module, "_resolve_remote_dist_path", return_value="static/remotes/test123"):
                self.assertEqual(plugin.get_render_mode(), ("vue", "static/remotes/test123"))
            self.assertIsNone(plugin.get_page())
        finally:
            sys.modules.pop(module_name, None)
            if previous_plugins_module is not None:
                sys.modules["app.plugins"] = previous_plugins_module
            else:
                sys.modules.pop("app.plugins", None)

    def test_plugin_entry_exposes_dashboard_meta_and_layout(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
        fake_plugins_module = type(sys)("app.plugins")

        class FakePluginBase:
            def __init__(self):
                pass

        fake_plugins_module._PluginBase = FakePluginBase  # type: ignore[attr-defined]
        previous_plugins_module = sys.modules.get("app.plugins")
        module_name = "musicpilot_host_entry_dashboard_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin_module = importlib.util.module_from_spec(spec)

        sys.modules["app.plugins"] = fake_plugins_module
        sys.modules.pop(module_name, None)
        try:
            spec.loader.exec_module(plugin_module)  # type: ignore[union-attr]
            plugin = plugin_module.musicpilot()

            self.assertEqual(
                plugin.get_dashboard_meta(),
                [{"key": "home", "name": "MusicPilot"}],
            )

            cols, attrs, elements = plugin.get_dashboard("home")
            self.assertEqual(cols, {"cols": 12, "md": 6, "lg": 4})
            self.assertEqual(
                attrs,
                {
                    "border": False,
                    "title": "MusicPilot",
                    "subtitle": "音乐发现、元数据与整理工作台",
                },
            )
            self.assertIsNone(elements)
        finally:
            sys.modules.pop(module_name, None)
            if previous_plugins_module is not None:
                sys.modules["app.plugins"] = previous_plugins_module
            else:
                sys.modules.pop("app.plugins", None)

    def test_plugin_entry_exposes_sidebar_nav(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
        fake_plugins_module = type(sys)("app.plugins")

        class FakePluginBase:
            def __init__(self):
                pass

        fake_plugins_module._PluginBase = FakePluginBase  # type: ignore[attr-defined]
        previous_plugins_module = sys.modules.get("app.plugins")
        module_name = "musicpilot_host_entry_sidebar_nav_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin_module = importlib.util.module_from_spec(spec)

        sys.modules["app.plugins"] = fake_plugins_module
        sys.modules.pop(module_name, None)
        try:
            spec.loader.exec_module(plugin_module)  # type: ignore[union-attr]
            plugin = plugin_module.musicpilot()

            self.assertEqual(
                plugin.get_sidebar_nav(),
                [
                    {
                        "nav_key": "main",
                        "title": "MusicPilot",
                        "icon": "mdi-music-note-outline",
                        "section": "discovery",
                        "permission": "discovery",
                        "order": 90,
                    }
                ],
            )
        finally:
            sys.modules.pop(module_name, None)
            if previous_plugins_module is not None:
                sys.modules["app.plugins"] = previous_plugins_module
            else:
                sys.modules.pop("app.plugins", None)

    def test_resolve_remote_dist_path_prefers_newest_remote_bundle(self) -> None:
        module_path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
        fake_plugins_module = type(sys)("app.plugins")
        fake_plugins_module._PluginBase = type("FakePluginBase", (), {})  # type: ignore[attr-defined]
        previous_plugins_module = sys.modules.get("app.plugins")
        module_name = "musicpilot_remote_dist_path_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin_module = importlib.util.module_from_spec(spec)

        sys.modules["app.plugins"] = fake_plugins_module
        sys.modules.pop(module_name, None)
        try:
            spec.loader.exec_module(plugin_module)  # type: ignore[union-attr]

            with tempfile.TemporaryDirectory() as tmpdir:
                app_dir = Path(tmpdir) / "app"
                remotes_dir = app_dir / "static" / "remotes"
                remotes_dir.mkdir(parents=True)
                older = remotes_dir / "zzzzzzzzzzzz"
                newer = remotes_dir / "111111111111"
                older.mkdir()
                newer.mkdir()
                (older / "remoteEntry.js").write_text("old", encoding="utf-8")
                (newer / "remoteEntry.js").write_text("new", encoding="utf-8")
                older_stat = older.stat()
                newer_stat = newer.stat()
                # 字典序更大的目录不一定是最新构建产物；应按修改时间选择。
                import os
                os.utime(older, (older_stat.st_atime, older_stat.st_mtime))
                os.utime(newer, (newer_stat.st_atime + 10, newer_stat.st_mtime + 10))
                plugin_module.__file__ = str(app_dir / "__init__.py")

                self.assertEqual(
                    plugin_module._resolve_remote_dist_path(),
                    "static/remotes/111111111111",
                )
        finally:
            sys.modules.pop(module_name, None)
            if previous_plugins_module is not None:
                sys.modules["app.plugins"] = previous_plugins_module
            else:
                sys.modules.pop("app.plugins", None)


if __name__ == "__main__":
    unittest.main()
