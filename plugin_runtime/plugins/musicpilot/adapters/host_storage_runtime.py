"""Thin in-process host-runtime bridge for MusicPilot music file organize operations."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from .host_http import HostTransportError


class HostStorageRuntimeBridge:
    """Execute MoviePilot file/storage operations from the host plugin process."""

    def __init__(self) -> None:
        self._manager = None

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
        manager = self._build_manager()

        source_storage = str(source_fileitem.get("storage") or "local")
        source_path_raw = source_fileitem.get("path")
        if not source_path_raw:
            return {
                "success": False,
                "organize_status": "failed",
                "message": "缺少源文件路径",
            }
        source_path = Path(str(source_path_raw))
        source_item = manager.get_file_item(storage=source_storage, path=source_path)
        if not source_item:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"文件不存在：{source_path.as_posix()}",
            }
        if source_item.type != "file":
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"当前音乐整理 MVP 仅支持单文件输入：{source_item.path}",
            }
        if source_item.storage != "local" or target_storage != "local":
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"当前音乐整理 MVP 仅支持本地到本地整理：{source_item.storage} -> {target_storage}",
            }

        supported = manager.support_transtype(target_storage) or {}
        if transfer_type not in supported:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"存储 {target_storage} 不支持整理方式：{transfer_type}",
            }

        source_oper = self._get_storage_oper(manager, source_item.storage)
        target_oper = self._get_storage_oper(manager, target_storage)
        if not source_oper or not target_oper:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"未找到可用存储操作对象：{source_item.storage} -> {target_storage}",
            }

        target_dir = Path(target_directory)
        target_diritem = target_oper.get_folder(target_dir)
        if not target_diritem:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"目标目录获取失败：{target_dir.as_posix()}",
            }

        target_file, resolve_error = self._resolve_target_path(
            target_oper=target_oper,
            target_dir=target_dir,
            target_name=target_filename,
            conflict_policy=conflict_policy,
        )
        if resolve_error:
            return {
                "success": False,
                "organize_status": "skipped" if "已存在" in resolve_error else "failed",
                "message": resolve_error,
                "target_path": (target_dir / target_filename).as_posix(),
            }

        state = self._execute_transfer(
            source_oper=source_oper,
            source_item=source_item,
            transfer_type=transfer_type,
            target_file=target_file,
        )
        if not state:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"{source_item.path} {transfer_type} 失败",
                "target_path": target_file.as_posix(),
            }

        return {
            "success": True,
            "organize_status": "applied",
            "message": "",
            "target_path": target_file.as_posix(),
        }

    def _build_manager(self):
        if self._manager is not None:
            return self._manager
        try:
            module = import_module("app.modules.filemanager")
        except Exception as exc:  # pragma: no cover - depends on host runtime
            raise HostTransportError(
                f"MoviePilot file/storage runtime is only available inside the host plugin process: {exc}",
                reason_code="moviepilot_storage_runtime_unavailable",
            ) from exc

        manager_cls = getattr(module, "FileManagerModule")
        manager = manager_cls()
        init_module = getattr(manager, "init_module", None)
        if callable(init_module):
            init_module()
        self._manager = manager
        return manager

    def _get_storage_oper(self, manager, storage: str):
        getter = getattr(manager, "get_storage_oper", None)
        if callable(getter):
            return getter(storage)
        private_name = f"_{type(manager).__name__}__get_storage_oper"
        private_getter = getattr(manager, private_name, None)
        if callable(private_getter):
            return private_getter(storage)
        return None

    def _resolve_target_path(self, *, target_oper, target_dir: Path, target_name: str, conflict_policy: str):
        candidate = target_dir / target_name
        existing = target_oper.get_item(candidate)
        if not existing:
            return candidate, None

        if conflict_policy == "skip_existing":
            return None, f"目标文件已存在：{candidate.as_posix()}"
        if conflict_policy == "overwrite":
            if not target_oper.delete(existing):
                return None, f"删除目标文件失败：{candidate.as_posix()}"
            return candidate, None
        if conflict_policy == "append_suffix":
            stem = candidate.stem
            suffix = candidate.suffix
            parent = candidate.parent
            index = 1
            while True:
                renamed = parent / f"{stem} ({index}){suffix}"
                if not target_oper.get_item(renamed):
                    return renamed, None
                index += 1
        return None, f"不支持的冲突策略：{conflict_policy}"

    def _execute_transfer(self, *, source_oper, source_item, transfer_type: str, target_file: Path) -> bool:
        if transfer_type == "copy":
            return bool(source_oper.copy(source_item, target_file.parent, target_file.name))
        if transfer_type == "move":
            return bool(source_oper.move(source_item, target_file.parent, target_file.name))
        if transfer_type == "link":
            return bool(source_oper.link(source_item, target_file))
        if transfer_type == "softlink":
            return bool(source_oper.softlink(source_item, target_file))
        return False
