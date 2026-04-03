#!/usr/bin/env python3
"""Local MoviePilot-like host integration stub for Phase 7A validation."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse


SEARCH_CONTEXTS = [
    {
        "meta_info": {"title": "Adele 25", "year": "2015"},
        "media_info": {},
        "torrent_info": {
            "site": 1,
            "site_name": "Local Stub PT",
            "title": "Adele - 25 (2015) FLAC",
            "description": "Lossless album release",
            "enclosure": "magnet:?xt=urn:btih:1111111111111111111111111111111111111111",
            "page_url": "https://stub.example/search/adele-25",
            "size": 734003200,
            "seeders": 42,
            "peers": 8,
            "labels": ["lossless", "album", "stub"],
            "volume_factor": "free",
        },
    },
    {
        "meta_info": {"title": "Random Access Memories", "year": "2013"},
        "media_info": {},
        "torrent_info": {
            "site": 2,
            "site_name": "Local Stub PT",
            "title": "Daft Punk - Random Access Memories (2013) FLAC",
            "description": "Lossless album release",
            "enclosure": "magnet:?xt=urn:btih:2222222222222222222222222222222222222222",
            "page_url": "https://stub.example/search/ram",
            "size": 943718400,
            "seeders": 35,
            "peers": 11,
            "labels": ["lossless", "album", "stub"],
            "volume_factor": "free",
        },
    },
    {
        "meta_info": {"title": "Anti-Hero", "year": "2022"},
        "media_info": {},
        "torrent_info": {
            "site": 3,
            "site_name": "Local Stub PT",
            "title": "Taylor Swift - Anti-Hero (2022) AAC 256K",
            "description": "Track release",
            "enclosure": "magnet:?xt=urn:btih:3333333333333333333333333333333333333333",
            "page_url": "https://stub.example/search/anti-hero",
            "size": 12582912,
            "seeders": 18,
            "peers": 4,
            "labels": ["track", "web", "stub"],
            "volume_factor": "free",
        },
    },
]

DOWNLOADER_CLIENTS = [{"name": "QB", "type": "qbittorrent"}]

SITES = [{"id": 1, "name": "Local Stub PT", "enabled": True}]


class HostIntegrationStubHandler(BaseHTTPRequestHandler):
    server_version = "MusicPilotMoviePilotStub/0.2"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in {"/health", "/api/v1/search/last"}:
            if path == "/health":
                self._write_json(
                    {
                        "status": "ok",
                        "plugin_api_registered": True,
                        "note": "Legacy stub health endpoint only.",
                    }
                )
                return
            self._write_json(SEARCH_CONTEXTS)
            return

        if path in {"/sites", "/api/v1/site"}:
            payload = {"items": SITES} if path == "/sites" else SITES
            self._write_json(payload)
            return

        if path in {"/downloaders", "/api/v1/download/clients"}:
            payload = {"items": DOWNLOADER_CLIENTS} if path == "/downloaders" else DOWNLOADER_CLIENTS
            self._write_json(payload)
            return

        if path == "/api/v1/search/title":
            keyword = (query.get("keyword") or [""])[0].lower()
            items = [item for item in SEARCH_CONTEXTS if keyword in json.dumps(item, ensure_ascii=False).lower()]
            self._write_json(
                {
                    "success": True,
                    "data": items or SEARCH_CONTEXTS[:1],
                    "message": None,
                }
            )
            return

        if path.startswith("/api/v1/search/media/"):
            self._write_json({"success": False, "message": "未搜索到任何资源", "data": {}})
            return

        if path == "/api/v1/transfer/name":
            source_path = (query.get("path") or [""])[0]
            file_type = (query.get("filetype") or [""])[0]
            if not source_path or not file_type:
                self._write_json(
                    {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["query", "path" if not source_path else "filetype"],
                                "msg": "Field required",
                                "input": None,
                            }
                        ]
                    },
                    status=422,
                )
                return
            if "nonexistent" in source_path:
                self._write_json({"success": False, "message": "未识别到媒体信息", "data": {}})
                return
            file_name = source_path.rsplit("/", 1)[-1]
            self._write_json({"success": True, "data": {"name": f"Organized-{file_name}"}})
            return

        if path == "/api/v1/transfer/queue":
            self._write_json([])
            return

        if path == "/api/v1/transfer/now":
            token = (query.get("token") or [""])[0]
            if not token:
                self._write_json({"detail": "token 校验不通过"}, status=401)
                return
            self._write_json({"success": True})
            return

        self._write_json({"error": "not_found", "path": path}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        payload = self._read_json()

        if path == "/search":
            keyword = " ".join(
                [
                    str(payload.get("keyword") or "").lower(),
                    *[str(item.get("query", "")).lower() for item in payload.get("queries", []) if isinstance(item, dict)],
                ]
            ).strip()
            items = [item["torrent_info"] | {"site_id": item["torrent_info"]["site"]} for item in SEARCH_CONTEXTS if keyword and keyword.split()[0] in item["torrent_info"]["title"].lower()]
            self._write_json({"items": items or [SEARCH_CONTEXTS[0]["torrent_info"]], "note": "Legacy search stub"})
            return

        if path == "/dispatch":
            candidate = payload.get("candidate") or {}
            accepted = bool(candidate)
            self._write_json(
                {
                    "accepted": accepted,
                    "dispatchable": accepted,
                    "dispatch_status": "host_stub_submitted" if accepted else "rejected",
                    "target_downloader": payload.get("target_downloader") or "QB",
                    "downloader_task_id": "stub-task-001" if accepted else None,
                    "note": "Legacy dispatch stub only.",
                }
            )
            return

        if path == "/api/v1/download/add":
            torrent = payload.get("torrent_in") or {}
            title = str(torrent.get("title") or "")
            if "Nonexistent" in title or "Validation" in title:
                self._write_json({"success": False, "message": "无法识别媒体信息", "data": {}})
                return
            self._write_json({"success": True, "message": None, "data": {"download_id": "stub-download-001"}})
            return

        if path == "/api/v1/download/":
            self._write_json({"success": True, "message": None, "data": {"download_id": "stub-download-002"}})
            return

        if path in {"/organize/preview", "/organize/apply"}:
            plan = payload.get("plan") or {}
            self._write_json(
                {
                    "organizeable": True,
                    "organize_status": "applied" if path.endswith("/apply") else "preview_ready",
                    "target_library_path": plan.get("target_library_path", "/library/musicpilot/library/unknown"),
                    "target_relative_path": plan.get("target_relative_path", "unknown"),
                    "strategy_note": plan.get("strategy_note", "Legacy organize stub."),
                    "note": "Legacy organize stub only.",
                }
            )
            return

        if path == "/api/v1/transfer/manual":
            fileitem = payload.get("fileitem") or {}
            source_path = str(fileitem.get("path") or "")
            if not source_path or "nonexistent" in source_path:
                self._write_json(
                    {
                        "success": False,
                        "message": f"{source_path.rsplit('/', 1)[-1] or 'file'} 没有找到可整理的媒体文件",
                        "data": {},
                    }
                )
                return
            self._write_json({"success": True, "message": None, "data": {}})
            return

        if path == "/notify":
            self._write_json({"sent": True, "echo": payload})
            return

        if path == "/config":
            self._write_json(
                {
                    "persisted": payload.get("operation") == "write",
                    "value": payload.get("value"),
                    "echo": payload,
                }
            )
            return

        self._write_json({"error": "not_found", "path": path}, status=404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _write_json(self, payload: Any, *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MusicPilot Phase 7A MoviePilot-like host stub.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=19090, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), HostIntegrationStubHandler)
    print(f"MusicPilot MoviePilot-like host stub listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
