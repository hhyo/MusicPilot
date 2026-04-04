"""Thin host-runtime bridge for MusicPilot music file organize operations."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

from .host_http import HostTransportError


_RESULT_MARKER = "__MUSICPILOT_STORAGE_RESULT__="

_STORAGE_TRANSFER_BRIDGE = textwrap.dedent(
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
        from app.modules.filemanager import FileManagerModule
        from app.schemas.file import FileItem
    except Exception as exc:
        emit(
            {{
                "success": False,
                "organize_status": "failed",
                "message": f"storage_runtime_import_error:{{type(exc).__name__}}:{{exc}}",
                "runtime_error": True,
            }},
            exit_code=1,
        )

    def resolve_target_path(target_oper, target_dir: Path, target_name: str, conflict_policy: str):
        candidate = target_dir / target_name
        existing = target_oper.get_item(candidate)
        if not existing:
            return candidate, None

        if conflict_policy == "skip_existing":
            return None, f"目标文件已存在：{{candidate.as_posix()}}"
        if conflict_policy == "overwrite":
            if not target_oper.delete(existing):
                return None, f"删除目标文件失败：{{candidate.as_posix()}}"
            return candidate, None
        if conflict_policy == "append_suffix":
            stem = candidate.stem
            suffix = candidate.suffix
            parent = candidate.parent
            index = 1
            while True:
                renamed = parent / f"{{stem}} ({{index}}){{suffix}}"
                if not target_oper.get_item(renamed):
                    return renamed, None
                index += 1
        return None, f"不支持的冲突策略：{{conflict_policy}}"

    try:
        manager = FileManagerModule()
        manager.init_module()

        source_request = FileItem(**request["source_fileitem"])
        source_item = manager.get_file_item(storage=source_request.storage, path=Path(source_request.path))
        if not source_item:
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"文件不存在：{{source_request.path}}",
                }}
            )
        if source_item.type != "file":
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"当前音乐整理 MVP 仅支持单文件输入：{{source_item.path}}",
                }}
            )

        target_storage = request.get("target_storage") or "local"
        transfer_type = request.get("transfer_type")
        supported = manager.support_transtype(target_storage) or {{}}
        if transfer_type not in supported:
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"存储 {{target_storage}} 不支持整理方式：{{transfer_type}}",
                }}
            )

        source_oper = manager._FileManagerModule__get_storage_oper(source_item.storage)
        target_oper = manager._FileManagerModule__get_storage_oper(target_storage)
        if not source_oper or not target_oper:
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"未找到可用存储操作对象：{{source_item.storage}} -> {{target_storage}}",
                }}
            )

        if source_item.storage != "local" or target_storage != "local":
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"当前音乐整理 MVP 仅支持本地到本地整理：{{source_item.storage}} -> {{target_storage}}",
                }}
            )

        target_dir = Path(request["target_directory"])
        target_name = request["target_filename"]
        target_diritem = target_oper.get_folder(target_dir)
        if not target_diritem:
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"目标目录获取失败：{{target_dir.as_posix()}}",
                }}
            )

        target_file, resolve_error = resolve_target_path(
            target_oper=target_oper,
            target_dir=target_dir,
            target_name=target_name,
            conflict_policy=request.get("conflict_policy") or "skip_existing",
        )
        if resolve_error:
            emit(
                {{
                    "success": False,
                    "organize_status": "skipped" if "已存在" in resolve_error else "failed",
                    "message": resolve_error,
                    "target_path": (target_dir / target_name).as_posix(),
                }}
            )

        if transfer_type == "copy":
            state = source_oper.copy(source_item, target_file.parent, target_file.name)
        elif transfer_type == "move":
            state = source_oper.move(source_item, target_file.parent, target_file.name)
        elif transfer_type == "link":
            state = source_oper.link(source_item, target_file)
        elif transfer_type == "softlink":
            state = source_oper.softlink(source_item, target_file)
        else:
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"不支持的整理方式：{{transfer_type}}",
                }}
            )

        if not state:
            emit(
                {{
                    "success": False,
                    "organize_status": "failed",
                    "message": f"{{source_item.path}} {{transfer_type}} 失败",
                    "target_path": target_file.as_posix(),
                }}
            )

        emit(
            {{
                "success": True,
                "organize_status": "applied",
                "message": "",
                "target_path": target_file.as_posix(),
            }}
        )
    except Exception as exc:
        emit(
            {{
                "success": False,
                "organize_status": "failed",
                "message": f"storage_runtime_error:{{type(exc).__name__}}:{{exc}}",
                "runtime_error": True,
            }},
            exit_code=1,
        )
    """
)


class HostStorageRuntimeBridge:
    """Execute MoviePilot storage/filemanager code in an isolated interpreter."""

    def __init__(self, *, python_executable: str | None = None):
        self.python_executable = python_executable or sys.executable

    def transfer_file(
        self,
        *,
        source_fileitem: dict[str, Any],
        target_storage: str,
        target_directory: str,
        target_filename: str,
        transfer_type: str,
        conflict_policy: str = "skip_existing",
    ) -> dict[str, Any]:
        host_root = self._resolve_host_root()
        if host_root is None:
            raise HostTransportError(
                "MoviePilot source root could not be resolved for direct music storage transfer invocation.",
                reason_code="moviepilot_source_root_missing",
            )

        request = {
            "host_root": str(host_root),
            "source_fileitem": source_fileitem,
            "target_storage": target_storage,
            "target_directory": target_directory,
            "target_filename": target_filename,
            "transfer_type": transfer_type,
            "conflict_policy": conflict_policy,
        }

        try:
            completed = subprocess.run(
                [self.python_executable, "-c", _STORAGE_TRANSFER_BRIDGE],
                input=json.dumps(request, ensure_ascii=False),
                text=True,
                capture_output=True,
                cwd=str(host_root),
                check=False,
            )
        except OSError as exc:  # pragma: no cover - environment dependent
            raise HostTransportError(
                f"MoviePilot direct storage runtime failed to start: {exc}",
                reason_code="moviepilot_storage_runtime_unavailable",
            ) from exc

        payload = self._extract_result_payload(completed.stdout)
        if completed.returncode != 0:
            detail = (
                payload.get("message")
                or completed.stderr.strip()
                or "MoviePilot storage runtime exited with a non-zero code."
            )
            raise HostTransportError(
                f"MoviePilot direct storage runtime failed: {detail}",
                reason_code="moviepilot_storage_runtime_failed",
            )
        return payload

    def _resolve_host_root(self) -> Path | None:
        repo_root = Path(__file__).resolve().parents[3]
        candidates = [
            repo_root.parent / "MoviePilot",
            repo_root.parent / "MoviePilotPkg" / "MoviePilot",
        ]
        for candidate in candidates:
            if (candidate / "app" / "modules" / "filemanager" / "__init__.py").exists():
                return candidate
        return None

    def _extract_result_payload(self, stdout: str) -> dict[str, Any]:
        for line in reversed(stdout.splitlines()):
            if line.startswith(_RESULT_MARKER):
                try:
                    return json.loads(line[len(_RESULT_MARKER) :])
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                    raise HostTransportError(
                        "MoviePilot direct storage runtime returned invalid JSON.",
                        reason_code="moviepilot_storage_runtime_invalid_payload",
                    ) from exc
        raise HostTransportError(
            "MoviePilot direct storage runtime did not emit a result payload.",
            reason_code="moviepilot_storage_runtime_missing_result",
        )
