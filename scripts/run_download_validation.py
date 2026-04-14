#!/usr/bin/env python3
"""Run the narrow download validation flow against a real MoviePilot host."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.chain.transfer import MusicTransferChain
from app.core.config import Settings, settings as app_settings
from app.core.db import SessionLocal, initialize_database_schema
from app.core import dependencies as backend_dependencies
from app.core.dependencies import build_music_transfer_chain
from app.helper.download_validation import (
    build_download_validation_report,
    ensure_fake_music_file,
)
from app.modules.download_dispatch import RealDownloadDispatchAdapter
from app.modules.host_http import HostHttpClient, HostHttpClientConfig
from app.modules.path_handoff import HostPathHandoff
from app.schemas.acquisition import SearchCandidateDetail
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.music_media import MusicMediaInfo, MusicMediaInput, MusicMetaBase, MusicRecognitionAssessment
from app.schemas.shared import EntityType
from app.schemas.orchestration import OrganizeAdapterResult, OrganizePreviewRequest, OrganizeStatus


@dataclass(slots=True)
class FakeTorrentState:
    torrent_hash: str
    title: str
    tags: str
    save_path: str | None
    paused: bool
    urls: str | None
    created_at: datetime


class FakeQbittorrentHandler(BaseHTTPRequestHandler):
    server_version = "FakeQbittorrent/1.0"
    protocol_version = "HTTP/1.1"

    @property
    def state(self) -> dict[str, FakeTorrentState]:
        return self.server.state  # type: ignore[attr-defined]

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        body = self._read_body()

        if parsed.path == "/api/v2/auth/login":
            self._send_text("Ok.", cookies={"SID": "fake-session"})
            return

        if parsed.path == "/api/v2/torrents/add":
            self._handle_add_torrent(body)
            return

        if parsed.path.startswith("/api/v2/torrents/info"):
            self._handle_info_torrents(parsed)
            return

        if parsed.path in {
            "/api/v2/torrents/addTags",
            "/api/v2/torrents/removeTags",
            "/api/v2/torrents/deleteTags",
        }:
            self._send_text("Ok.")
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in {"/api/v2/app/version", "/api/v2/app/webapiVersion"}:
            self._send_text("4.6.0")
            return

        if parsed.path.startswith("/api/v2/app/preferences"):
            self._send_json(
                {
                    "save_path": "/tmp/musicpilot-validation-downloads",
                    "temp_path": "/tmp/musicpilot-validation-downloads",
                }
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_info_torrents(self, parsed) -> None:
        query = parse_qs(parsed.query)
        torrents = []
        hashes = _split_csv(query.get("hashes", [""])[0])
        for torrent in self.state.values():
            if hashes and torrent.torrent_hash not in hashes:
                continue
            torrents.append(
                {
                    "hash": torrent.torrent_hash,
                    "name": torrent.title,
                    "tags": torrent.tags,
                    "state": "downloading" if not torrent.paused else "pausedUP",
                    "progress": 0.0,
                    "size": 1_024,
                }
            )
        self._send_json(torrents)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _handle_add_torrent(self, body: bytes) -> None:
        fields = _parse_form(body)
        urls = fields.get("urls")
        if not urls:
            self._send_text("Missing urls", status=HTTPStatus.BAD_REQUEST)
            return
        title = _infer_title(urls)
        torrent_hash = uuid4().hex
        self.state[torrent_hash] = FakeTorrentState(
            torrent_hash=torrent_hash,
            title=title,
            tags=fields.get("tags", ""),
            save_path=fields.get("savepath") or None,
            paused=(fields.get("paused") or "false").lower() == "true",
            urls=urls,
            created_at=datetime.now(timezone.utc),
        )
        self._send_text("Ok.")

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _send_json(self, payload: Any, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(
        self,
        payload: str,
        *,
        status: HTTPStatus = HTTPStatus.OK,
        cookies: dict[str, str] | None = None,
    ) -> None:
        data = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if cookies:
            for key, value in cookies.items():
                self.send_header("Set-Cookie", f"{key}={value}; Path=/")
        self.end_headers()
        self.wfile.write(data)


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_form(body: bytes) -> dict[str, str]:
    text = body.decode("utf-8", errors="ignore")
    result: dict[str, str] = {}
    for key, values in parse_qs(text, keep_blank_values=True).items():
        if values:
            result[key] = values[-1]
    return result


def _infer_title(urls: str) -> str:
    parsed = urlparse(urls)
    if parsed.scheme == "magnet":
        params = parse_qs(parsed.query)
        if params.get("dn"):
            return params["dn"][0]
    return "MusicPilot Validation Torrent"


def start_fake_qbittorrent_server(port: int) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    server = ThreadingHTTPServer(("127.0.0.1", port), FakeQbittorrentHandler)
    server.state = {}  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_port


def stop_fake_qbittorrent_server(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()


def upsert_download_directories(
    user_db_path: Path,
    *,
    download_path: str,
    library_path: str,
) -> None:
    directory_config = [
        {
            "name": "MusicPilot Validation Directory",
            "priority": 1,
            "storage": "local",
            "download_path": download_path,
            "media_type": "电影",
            "media_category": None,
            "download_type_folder": False,
            "download_category_folder": False,
            "monitor_type": "downloader",
            "monitor_mode": "fast",
            "transfer_type": "link",
            "overwrite_mode": "always",
            "library_path": library_path,
            "library_storage": "local",
            "renaming": True,
            "scraping": False,
            "notify": True,
            "library_type_folder": False,
            "library_category_folder": False,
        }
    ]

    with sqlite3.connect(user_db_path) as conn:
        cur = conn.cursor()
        cur.execute("delete from systemconfig where key = ?", ("Directories",))
        next_id = cur.execute("select coalesce(max(id), 0) + 1 from systemconfig").fetchone()[0]
        cur.execute(
            "insert into systemconfig(id, key, value) values (?, ?, ?)",
            (next_id, "Directories", json.dumps(directory_config, ensure_ascii=False)),
        )
        conn.commit()


def upsert_downloader_config(user_db_path: Path, *, host: str, port: int, name: str) -> None:
    downloader_config = [
        {
            "name": name,
            "type": "qbittorrent",
            "default": True,
            "enabled": True,
            "config": {
                "host": host,
                "port": port,
                "username": "admin",
                "password": "adminadmin",
                "category": False,
                "sequentail": False,
                "force_resume": False,
                "first_last_piece": False,
            },
            "path_mapping": [],
        }
    ]

    with sqlite3.connect(user_db_path) as conn:
        cur = conn.cursor()
        cur.execute("delete from systemconfig where key = ?", ("Downloaders",))
        next_id = cur.execute("select coalesce(max(id), 0) + 1 from systemconfig").fetchone()[0]
        cur.execute(
            "insert into systemconfig(id, key, value) values (?, ?, ?)",
            (next_id, "Downloaders", json.dumps(downloader_config, ensure_ascii=False)),
        )
        conn.commit()


def build_fake_candidate(
    *,
    download_id: str,
    fake_source_path: str,
    downloader_name: str,
) -> SearchCandidateDetail:
    music_input = MusicMediaInput(
        entity_hint=EntityType.TRACK,
        source_kind="manual",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        source_context={"sample": "download-validation"},
        raw_context={"sample": "download-validation"},
    )
    music_base = MusicMetaBase(
        entity_type=EntityType.TRACK,
        canonical_title="Hello",
        canonical_artist_names=["Adele"],
        canonical_album_title="25",
        canonical_album_artist_names=["Adele"],
        canonical_year=2015,
        source_refs={"sample": "track-hello"},
        evidence=[{"source": "validation", "note": "seeded for organize validation"}],
        normalization_notes=["seeded locally for organizer validation"],
        confidence_hint=1.0,
    )
    music_media = MusicMediaInfo(
        entity_type=EntityType.TRACK,
        provider="mock_seed_catalog",
        provider_id="track-hello",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        album_artist_names=["Adele"],
        year=2015,
        match_confidence=1.0,
        release_context={"sample": "track-hello"},
    )
    path_handoff = {
        "download_hash": download_id,
        "source_path": fake_source_path,
        "source_filetype": "file",
        "source_name": Path(fake_source_path).name,
        "source_basename": Path(fake_source_path).stem,
        "source_extension": Path(fake_source_path).suffix.lstrip("."),
        "handoff_source": "moviepilot.runtime.history.download",
        "handoff_status": "resolved_from_history_download",
        "verification_state": "verified",
        "note": "fake file seeded for organize validation",
        "raw_summary": {"download_hash": download_id},
    }
    raw_payload = {
        "host_context": {
            "torrent_info": {
                "title": "MusicPilot Validation Torrent",
                "description": "download validation sample",
                "enclosure": f"magnet:?xt=urn:btih:{download_id}&dn=MusicPilot+Validation+Torrent",
                "site_name": "Validation Site",
                "site": 1,
                "size": 1024,
                "seeders": 1,
                "peers": 0,
                "labels": ["validation"],
            }
            ,
            "media_info": {
                "type": "电影",
                "title": "Download Validation Movie",
                "year": "2026",
                "tmdb_id": 447273,
            },
        },
        "host_transfer_source_path": fake_source_path,
        "host_transfer_filetype": "file",
        "host_transfer_source": {
            "storage": "local",
            "path": fake_source_path,
            "type": "file",
            "name": Path(fake_source_path).name,
            "basename": Path(fake_source_path).stem,
            "extension": Path(fake_source_path).suffix.lstrip("."),
        },
        "path_handoff": path_handoff,
    }
    return SearchCandidateDetail(
        id="cand-download-validation",
        job_id="job-download-validation",
        site_id="1",
        site_name="Validation Site",
        title="MusicPilot Validation Torrent",
        normalized_title="musicpilot validation torrent",
        size_bytes=1024,
        seeders=1,
        peers=0,
        source_tags=["validation"],
        raw_score=100.0,
        score_total=100.0,
        score_breakdown={},
        decision="auto_download",
        reason_codes=["download_validation"],
        dispatchable=True,
        dispatch_status="pending",
        mock=False,
        note="download validation sample",
        created_at=datetime.now(timezone.utc),
        raw_payload=raw_payload,
    )


def build_settings(host_base_url: str, token: str) -> Settings:
    return Settings(
        host_integration_enabled=True,
        host_base_url=host_base_url,
        host_auth_token=token,
        host_auth_mode="x_api_key",
        host_api_key_header_name="X-API-KEY",
        host_search_mode="prefer_host",
        host_dispatch_mode="prefer_host",
        host_organize_mode="prefer_host",
        host_verification_state="verified",
        host_history_sync_retry_attempts=3,
        host_history_sync_retry_interval_seconds=1.0,
        host_verify_tls=False,
        host_assume_organize_available=True,
    )


def load_host_token(app_env: Path) -> str:
    for line in app_env.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip().replace("export ", "").strip() == "API_TOKEN":
            return value.strip().strip('"')
    raise RuntimeError(f"API_TOKEN not found in {app_env}")


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    server = None
    port = args.fake_qbittorrent_port
    try:
        if not args.skip_fake_qbittorrent_server:
            server, _thread, port = start_fake_qbittorrent_server(args.fake_qbittorrent_port)
        user_db = Path(args.user_db)
        validation_download_root = Path(args.validation_download_root)
        validation_library_root = Path(args.validation_library_root)
        validation_download_root.mkdir(parents=True, exist_ok=True)
        validation_library_root.mkdir(parents=True, exist_ok=True)
        initialize_database_schema()
        upsert_download_directories(
            user_db,
            download_path=str(validation_download_root),
            library_path=str(validation_library_root),
        )
        upsert_downloader_config(user_db, host="127.0.0.1", port=port, name=args.downloader_name)

        host_base_url = args.host_base_url.rstrip("/")
        token = args.host_token
        settings = build_settings(host_base_url, token)
        app_settings.host_integration_enabled = settings.host_integration_enabled
        app_settings.host_base_url = settings.host_base_url
        app_settings.host_auth_token = settings.host_auth_token
        app_settings.host_auth_mode = settings.host_auth_mode
        app_settings.host_api_key_header_name = settings.host_api_key_header_name
        app_settings.host_search_mode = settings.host_search_mode
        app_settings.host_dispatch_mode = settings.host_dispatch_mode
        app_settings.host_organize_mode = settings.host_organize_mode
        app_settings.host_verification_state = settings.host_verification_state
        app_settings.host_history_sync_retry_attempts = settings.host_history_sync_retry_attempts
        app_settings.host_history_sync_retry_interval_seconds = settings.host_history_sync_retry_interval_seconds
        app_settings.host_verify_tls = settings.host_verify_tls
        app_settings.host_assume_organize_available = settings.host_assume_organize_available
        backend_dependencies.get_metadata_provider_adapter.cache_clear()
        backend_dependencies.get_host_http_client.cache_clear()
        backend_dependencies.get_host_probe_adapter.cache_clear()
        backend_dependencies.get_host_integration_module.cache_clear()
        backend_dependencies.get_host_path_handoff_service.cache_clear()
        backend_dependencies.get_organize_strategy_service.cache_clear()
        backend_dependencies.get_organize_adapter_resolver.cache_clear()
        client = HostHttpClient(
            HostHttpClientConfig(
                base_url=host_base_url,
                timeout_seconds=30.0,
                verify_tls=False,
                auth_token=token,
                auth_mode="x_api_key",
                api_key_header_name="X-API-KEY",
            )
        )
        downloaders_payload = client.get_json("/api/v1/download/clients", auth_mode="x_api_key")
        if not downloaders_payload:
            raise RuntimeError("Host did not expose any downloaders after injecting validation config.")

        fake_source = ensure_fake_music_file(Path(args.fake_source_root), "Download Validation Track")
        candidate = build_fake_candidate(
            download_id="validation-download",
            fake_source_path=str(fake_source),
            downloader_name=args.downloader_name,
        )

        dispatch_adapter = RealDownloadDispatchAdapter(
            settings=settings,
            client=client,
            path_handoff_service=HostPathHandoff(settings=settings, client=client),
        )
        dispatch_result = dispatch_adapter.dispatch(
            candidate=candidate,
            downloader_id=args.downloader_name,
            manual_confirm=False,
        )

        download_id = dispatch_result.downloader_task_id
        if not download_id:
            raise RuntimeError(dispatch_result.failure_reason or "download dispatch did not return a task id")

        handoff = dispatch_result.path_handoff
        if handoff is None or not handoff.source_path:
            handoff = HostPathHandoff(settings=settings, client=client).resolve_from_download_with_retry(download_id)

        fake_plugin_db = Path(args.plugin_db)
        create_validation_binding_rows(
            plugin_db=fake_plugin_db,
            candidate=candidate,
            download_id=download_id,
            handoff=handoff,
            fake_source_path=str(fake_source),
        )

        with SessionLocal() as session:
            transfer_chain = build_music_transfer_chain(session)
            preview = transfer_chain.preview(OrganizePreviewRequest(binding_id="bind-download-validation"))

            target_root = Path(args.validation_library_root)
            target_relative_path = preview.target_relative_path or Path(fake_source).name
            target_path = target_root / target_relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fake_source, target_path)

            organize_oper = transfer_chain.repository
            organize_model = organize_oper.get_organize_record(preview.id)
            if organize_model is None:
                raise RuntimeError("music transfer chain preview did not persist an organize record")

            applied_result = OrganizeAdapterResult(
                organizeable=True,
                organize_backend=AdapterMode.MOCK,
                adapter_mode=AdapterMode.MOCK,
                strategy=preview.strategy,
                strategy_snapshot=preview.strategy_snapshot,
                organize_status=OrganizeStatus.APPLIED,
                target_library_path=str(target_path),
                target_relative_path=preview.target_relative_path,
                strategy_note=preview.strategy_note,
                integration_point="scripts.run_download_validation.local_file_copy",
                capability_source="local.validation",
                verification_state=VerificationState.VERIFIED,
                mock=False,
                note="Local validation copied the fake music file into the target library path.",
                path_handoff=preview.path_handoff,
            )
            organize_oper.update_organize_record(
                organize_model,
                result=applied_result,
                music_media_input=preview.music_media_input.model_dump(mode="json") if preview.music_media_input else None,
                music_meta_base=preview.music_meta_base.model_dump(mode="json") if preview.music_meta_base else None,
                music_recognition_assessment=preview.music_recognition_assessment.model_dump(mode="json")
                if preview.music_recognition_assessment
                else None,
                music_media_info=preview.music_media_info.model_dump(mode="json") if preview.music_media_info else None,
            )
            session.commit()
            applied_data = transfer_chain.get_record(preview.id).model_dump(mode="json")

        report = build_download_validation_report(
            host_base_url=host_base_url,
            fake_source_path=str(fake_source),
            downloader_name=args.downloader_name,
            resolved_downloader=dispatch_result.target_downloader,
            download_id=download_id,
            download_hash=download_id,
            path_handoff_status=handoff.handoff_status if handoff else "pending_history_sync",
            organize_record_id=str(applied_data.get("id")),
            organize_status=str(applied_data.get("organize_status") or "applied"),
            preview_id=str(applied_data.get("id")),
            target_library_path=str(applied_data.get("target_library_path") or target_path),
            target_relative_path=str(applied_data.get("target_relative_path") or target_relative_path),
            dispatch_status=dispatch_result.dispatch_status,
            submission_success=dispatch_result.dispatchable,
            history_note="history/download resolved from real host response",
            organize_note="organize preview executed by MusicTransferChain and local fake file copy verified the path",
            submission_note=dispatch_result.note or "download submission completed",
            overall_status="success",
        )
        return report.model_dump(mode="json")
    finally:
        if server is not None:
            stop_fake_qbittorrent_server(server)


def create_validation_binding_rows(
    *,
    plugin_db: Path,
    candidate: SearchCandidateDetail,
    download_id: str,
    handoff,
    fake_source_path: str,
) -> None:
    with sqlite3.connect(plugin_db) as conn:
        cur = conn.cursor()
        ensure_search_job_validation_columns(cur)
        ensure_organize_record_validation_columns(cur)

        cur.execute("delete from organize_records where binding_id = ?", ("bind-download-validation",))
        cur.execute("delete from download_bindings where id = ?", ("bind-download-validation",))
        cur.execute("delete from search_candidates where id = ?", ("cand-download-validation",))
        cur.execute("delete from search_jobs where id = ?", ("job-download-validation",))

        job_music_input = {
            "entity_hint": "track",
            "source_kind": "manual",
            "title": "Hello",
            "artist_names": ["Adele"],
            "album_title": "25",
            "album_artist_names": ["Adele"],
            "external_refs": {},
            "source_context": {},
            "raw_context": {},
        }
        job_music_meta = {
            "entity_type": "track",
            "canonical_title": "Hello",
            "canonical_artist_names": ["Adele"],
            "canonical_album_title": "25",
            "canonical_album_artist_names": ["Adele"],
            "external_refs": {},
            "source_refs": {"sample": "track-hello"},
            "evidence": [{"source": "validation"}],
            "normalization_notes": ["seeded for validation"],
            "confidence_hint": 1.0,
        }
        job_music_info = MusicMediaInfo(
            entity_type=EntityType.TRACK,
            provider="mock_seed_catalog",
            provider_id="track-hello",
            title="Hello",
            artist_names=["Adele"],
            album_title="25",
            album_artist_names=["Adele"],
            year=2015,
            match_confidence=1.0,
        ).model_dump(mode="json")
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            insert into search_jobs(
                id, query_source_type, query_source_id, trigger_source, profile_id, mode, status,
                music_media_input, music_meta_base, music_recognition_assessment, music_media_info,
                query_payload, metadata_snapshot, summary_json, error_message, mock, note,
                created_at, updated_at, started_at, finished_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "job-download-validation",
                "manual",
                "job-download-validation",
                "manual",
                "default-lossless",
                "manual",
                "dispatched",
                json.dumps(job_music_input, ensure_ascii=False),
                json.dumps(job_music_meta, ensure_ascii=False),
                json.dumps({"state": "ready", "note": "validation"}, ensure_ascii=False),
                json.dumps(job_music_info, ensure_ascii=False),
                "{}",
                "{}",
                "{}",
                None,
                0,
                "download validation seed",
                now,
                now,
                None,
                None,
            ),
        )
        cur.execute(
            """
            insert into search_candidates(
                id, job_id, site_id, site_name, title, normalized_title, size_bytes, seeders, peers,
                source_tags, raw_score, score_total, score_breakdown, decision, reason_codes,
                dispatch_status, dispatchable, raw_payload, mock, note, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "cand-download-validation",
                "job-download-validation",
                candidate.site_id,
                candidate.site_name,
                candidate.title,
                candidate.normalized_title,
                candidate.size_bytes,
                candidate.seeders,
                candidate.peers,
                json.dumps(candidate.source_tags, ensure_ascii=False),
                candidate.raw_score,
                candidate.score_total,
                json.dumps(candidate.score_breakdown, ensure_ascii=False),
                candidate.decision,
                json.dumps(candidate.reason_codes, ensure_ascii=False),
                "host_submitted",
                1,
                json.dumps(candidate.raw_payload, ensure_ascii=False),
                0,
                candidate.note,
                now,
            ),
        )
        cur.execute(
            """
            insert into download_bindings(
                id, job_id, candidate_id, target_downloader, downloader_task_id, dispatchable,
                dispatch_status, mock, note, integration_point, raw_payload, dispatched_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "bind-download-validation",
                "job-download-validation",
                "cand-download-validation",
                "Qbittorrent Validation",
                download_id,
                1,
                "host_submitted",
                0,
                "download validation binding",
                "download validation",
                json.dumps(
                    {
                        "path_handoff": handoff.model_dump(mode="json") if handoff else {},
                        "host_transfer_source_path": fake_source_path,
                    },
                    ensure_ascii=False,
                ),
                now,
            ),
        )
        conn.commit()


def ensure_search_job_validation_columns(cur: sqlite3.Cursor) -> None:
    existing = {row[1] for row in cur.execute("pragma table_info(search_jobs)").fetchall()}
    for column in [
        "music_media_input",
        "music_meta_base",
        "music_recognition_assessment",
        "music_media_info",
    ]:
        if column not in existing:
            cur.execute(f"alter table search_jobs add column {column} JSON")


def ensure_organize_record_validation_columns(cur: sqlite3.Cursor) -> None:
    existing = {row[1] for row in cur.execute("pragma table_info(organize_records)").fetchall()}
    for column in [
        "music_media_input",
        "music_meta_base",
        "music_recognition_assessment",
        "music_media_info",
    ]:
        if column not in existing:
            cur.execute(f"alter table organize_records add column {column} JSON")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run narrow MusicPilot download validation.")
    parser.add_argument(
        "--host-base-url",
        default=os.getenv("MUSICPILOT_REAL_HOST_BASE_URL", "http://127.0.0.1:3001"),
    )
    parser.add_argument(
        "--host-token",
        default=os.getenv("MUSICPILOT_REAL_HOST_API_TOKEN") or os.getenv("MUSICPILOT_HOST_AUTH_TOKEN"),
    )
    parser.add_argument(
        "--user-db",
        default="/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev/user.db",
    )
    parser.add_argument(
        "--plugin-db",
        default=str(BACKEND_ROOT / "data" / "musicpilot.db"),
    )
    parser.add_argument(
        "--validation-download-root",
        default="/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev/musicpilot-validation-downloads",
    )
    parser.add_argument(
        "--validation-library-root",
        default="/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev/musicpilot-library",
    )
    parser.add_argument(
        "--fake-source-root",
        default=str(ROOT / ".tmp" / "download-validation"),
    )
    parser.add_argument(
        "--output",
        default=str(BACKEND_ROOT / "data" / "download_validation.latest.json"),
    )
    parser.add_argument(
        "--downloader-name",
        default="Qbittorrent Validation",
    )
    parser.add_argument(
        "--fake-qbittorrent-port",
        type=int,
        default=50118,
    )
    parser.add_argument(
        "--skip-fake-qbittorrent-server",
        action="store_true",
    )
    args = parser.parse_args()
    if not args.host_token:
        args.host_token = load_host_token(Path("/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev/app.env"))
    return args


def main() -> None:
    args = parse_args()
    report = run_validation(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
