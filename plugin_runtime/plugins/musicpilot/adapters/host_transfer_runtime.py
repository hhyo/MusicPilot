"""Thin host-runtime bridge for MoviePilot ``TransferChain.manual_transfer``."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

from .host_http import HostTransportError


_RESULT_MARKER = "__MUSICPILOT_TRANSFER_RESULT__="

_MANUAL_TRANSFER_BRIDGE = textwrap.dedent(
    f"""
    import json
    import sys
    import types
    from pathlib import Path

    RESULT_MARKER = {_RESULT_MARKER!r}

    def emit(payload, *, exit_code=0):
        print(RESULT_MARKER + json.dumps(payload, ensure_ascii=False, default=str))
        raise SystemExit(exit_code)

    request = json.loads(sys.stdin.read())
    host_root = request["host_root"]
    sys.path.insert(0, host_root)

    sites_helper = types.ModuleType("app.helper.sites")
    sites_helper.SitesHelper = type("SitesHelper", (), {{}})
    sys.modules.setdefault("app.helper.sites", sites_helper)

    try:
        from app.chain.transfer import TransferChain
        from app.schemas.file import FileItem
    except Exception as exc:  # pragma: no cover - exercised through parent bridge
        emit(
            {{
                "success": False,
                "organize_status": "failed",
                "message": f"manual_transfer_import_error:{{type(exc).__name__}}:{{exc}}",
                "runtime_error": True,
            }},
            exit_code=1,
        )

    try:
        fileitem = FileItem(**request["fileitem"])
        target_path = Path(request["target_path"]) if request.get("target_path") else None
        state, message = TransferChain().manual_transfer(
            fileitem=fileitem,
            target_path=target_path,
            tmdbid=request.get("tmdbid"),
            doubanid=request.get("doubanid"),
            transfer_type=request.get("transfer_type"),
            scrape=request.get("scrape"),
            background=request.get("background"),
            downloader=request.get("downloader"),
            download_hash=request.get("download_hash"),
        )
    except Exception as exc:  # pragma: no cover - exercised through parent bridge
        emit(
            {{
                "success": False,
                "organize_status": "failed",
                "message": f"manual_transfer_runtime_error:{{type(exc).__name__}}:{{exc}}",
                "runtime_error": True,
            }},
            exit_code=1,
        )

    if not state and isinstance(message, list):
        rendered_message = f"整理完成，{{len(message)}} 个文件转移失败！"
    else:
        rendered_message = str(message or "")

    emit(
        {{
            "success": bool(state),
            "organize_status": "applied" if state else "failed",
            "message": rendered_message,
        }}
    )
    """
)


class HostTransferRuntimeBridge:
    """Execute MoviePilot transfer code in an isolated interpreter."""

    def __init__(self, *, python_executable: str | None = None):
        self.python_executable = python_executable or sys.executable

    def manual_transfer(
        self,
        *,
        fileitem: dict[str, Any],
        target_path: str | None,
        transfer_type: str | None,
        scrape: bool = False,
        background: bool = False,
        tmdbid: int | None = None,
        doubanid: str | None = None,
        downloader: str | None = None,
        download_hash: str | None = None,
    ) -> dict[str, Any]:
        host_root = self._resolve_host_root()
        if host_root is None:
            raise HostTransportError(
                "MoviePilot source root could not be resolved for direct TransferChain.manual_transfer invocation.",
                reason_code="moviepilot_source_root_missing",
            )

        request = {
            "host_root": str(host_root),
            "fileitem": fileitem,
            "target_path": target_path,
            "transfer_type": transfer_type,
            "scrape": scrape,
            "background": background,
        }
        if tmdbid is not None:
            request["tmdbid"] = tmdbid
        if doubanid:
            request["doubanid"] = doubanid
        if downloader:
            request["downloader"] = downloader
        if download_hash:
            request["download_hash"] = download_hash

        try:
            completed = subprocess.run(
                [self.python_executable, "-c", _MANUAL_TRANSFER_BRIDGE],
                input=json.dumps(request, ensure_ascii=False),
                text=True,
                capture_output=True,
                cwd=str(host_root),
                check=False,
            )
        except OSError as exc:  # pragma: no cover - environment dependent
            raise HostTransportError(
                f"MoviePilot direct manual_transfer runtime failed to start: {exc}",
                reason_code="moviepilot_transfer_runtime_unavailable",
            ) from exc

        payload = self._extract_result_payload(completed.stdout)
        if completed.returncode != 0:
            detail = (
                payload.get("message")
                or completed.stderr.strip()
                or "MoviePilot manual_transfer runtime exited with a non-zero code."
            )
            raise HostTransportError(
                f"MoviePilot direct manual_transfer runtime failed: {detail}",
                reason_code="moviepilot_transfer_runtime_failed",
            )
        return payload

    def _resolve_host_root(self) -> Path | None:
        repo_root = Path(__file__).resolve().parents[3]
        candidates = [
            repo_root.parent / "MoviePilot",
            repo_root.parent / "MoviePilotPkg" / "MoviePilot",
        ]
        for candidate in candidates:
            if (candidate / "app" / "chain" / "transfer.py").exists():
                return candidate
        return None

    def _extract_result_payload(self, stdout: str) -> dict[str, Any]:
        for line in reversed(stdout.splitlines()):
            if line.startswith(_RESULT_MARKER):
                try:
                    return json.loads(line[len(_RESULT_MARKER) :])
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                    raise HostTransportError(
                        "MoviePilot direct manual_transfer runtime returned invalid JSON.",
                        reason_code="moviepilot_transfer_runtime_invalid_payload",
                    ) from exc
        raise HostTransportError(
            "MoviePilot direct manual_transfer runtime did not emit a result payload.",
            reason_code="moviepilot_transfer_runtime_missing_result",
        )
