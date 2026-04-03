#!/usr/bin/env python3
"""Local host integration stub for Phase 5 resolver and fallback validation."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


SEARCH_ITEMS = [
    {
        "site_id": "stub-site-001",
        "site_name": "Local Stub PT",
        "title": "Adele - 25 (2015) FLAC",
        "size_bytes": 734003200,
        "seeders": 42,
        "peers": 8,
        "format": "FLAC",
        "bitrate_kbps": 1000,
        "tags": ["lossless", "album", "stub"],
    },
    {
        "site_id": "stub-site-002",
        "site_name": "Local Stub PT",
        "title": "Daft Punk - Random Access Memories (2013) FLAC",
        "size_bytes": 943718400,
        "seeders": 35,
        "peers": 11,
        "format": "FLAC",
        "bitrate_kbps": 1000,
        "tags": ["lossless", "album", "stub"],
    },
    {
        "site_id": "stub-site-003",
        "site_name": "Local Stub PT",
        "title": "Taylor Swift - Anti-Hero (2022) WEB-DL AAC",
        "size_bytes": 12582912,
        "seeders": 18,
        "peers": 4,
        "format": "AAC",
        "bitrate_kbps": 256,
        "tags": ["track", "web", "stub"],
    },
]


class HostIntegrationStubHandler(BaseHTTPRequestHandler):
    server_version = "MusicPilotHostStub/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write_json(
                {
                    "status": "ok",
                    "plugin_api_registered": True,
                    "note": "Local host stub only. This is not a verified MoviePilot host.",
                }
            )
            return

        if self.path == "/sites":
            self._write_json(
                {
                    "items": [
                        {
                            "id": "stub-site-001",
                            "name": "Local Stub PT",
                            "enabled": True,
                        }
                    ]
                }
            )
            return

        if self.path == "/downloaders":
            self._write_json(
                {
                    "items": [
                        {
                            "id": "host-qbittorrent",
                            "name": "Host Stub qBittorrent",
                            "is_default": True,
                        }
                    ]
                }
            )
            return

        self._write_json({"error": "not_found", "path": self.path}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read_json()

        if self.path == "/search":
            query_text = " ".join(
                [
                    str(payload.get("keyword") or "").lower(),
                    *[str(item.get("query", "")).lower() for item in payload.get("queries", []) if isinstance(item, dict)],
                ]
            ).strip()
            items = [item for item in SEARCH_ITEMS if not query_text or query_text.split()[0] in item["title"].lower()]
            self._write_json(
                {
                    "items": items or SEARCH_ITEMS[:1],
                    "note": "Local host-backed stub result. Mapping is verified only against this stub.",
                }
            )
            return

        if self.path == "/dispatch":
            candidate = payload.get("candidate") or {}
            target_downloader = payload.get("target_downloader") or "host-qbittorrent"
            accepted = bool(candidate)
            self._write_json(
                {
                    "accepted": accepted,
                    "dispatchable": accepted,
                    "dispatch_status": "host_stub_submitted" if accepted else "rejected",
                    "target_downloader": target_downloader,
                    "downloader_task_id": "stub-task-001" if accepted else None,
                    "note": "Local host-backed dispatch stub only. Real MoviePilot semantics remain unverified.",
                }
            )
            return

        if self.path == "/notify":
            self._write_json({"sent": True, "echo": payload})
            return

        if self.path == "/config":
            self._write_json(
                {
                    "persisted": payload.get("operation") == "write",
                    "value": payload.get("value"),
                    "echo": payload,
                }
            )
            return

        self._write_json({"error": "not_found", "path": self.path}, status=404)

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

    def _write_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MusicPilot Phase 5 host integration stub.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=19090, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), HostIntegrationStubHandler)
    print(f"MusicPilot host integration stub listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
