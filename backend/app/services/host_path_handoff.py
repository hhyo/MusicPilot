"""Resolve real MoviePilot download/transfer history into stable local organize inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..adapters.host_http import HostHttpClient
from ..core.config import Settings
from ..schemas.acquisition import PathHandoffInfo
from ..schemas.integration import VerificationState

KNOWN_FILE_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".ts",
    ".m2ts",
    ".flac",
    ".ape",
    ".wav",
    ".aac",
    ".mp3",
    ".m4a",
    ".cue",
    ".srt",
    ".ass",
    ".ssa",
    ".sub",
}


class HostPathHandoffService:
    def __init__(self, *, settings: Settings, client: HostHttpClient):
        self.settings = settings
        self.client = client

    def resolve(self, download_hash: str | None) -> PathHandoffInfo | None:
        if not download_hash:
            return None

        download_record = self._find_download_history(download_hash)
        if download_record and download_record.get("path"):
            return self._build_handoff(
                source_path=str(download_record["path"]),
                download_hash=download_hash,
                handoff_source="moviepilot.runtime.history.download",
                handoff_status="resolved_from_history_download",
                note=(
                    "当前本地源路径来自真实 MoviePilot `/api/v1/history/download`。"
                    "宿主源码显示 `DownloadChain.download_single` 在成功添加下载后会登记该路径。"
                ),
                raw_summary={
                    "title": download_record.get("title"),
                    "torrent_name": download_record.get("torrent_name"),
                    "date": download_record.get("date"),
                },
            )

        transfer_record = self._find_transfer_history(download_hash)
        if transfer_record and transfer_record.get("src"):
            return self._build_handoff(
                source_path=str(transfer_record["src"]),
                download_hash=download_hash,
                handoff_source="moviepilot.runtime.history.transfer",
                handoff_status="resolved_from_history_transfer",
                note=(
                    "当前本地源路径来自真实 MoviePilot `/api/v1/history/transfer` 的成功整理记录。"
                    "这是 `history/download` 尚未可用时的兼容回灌来源。"
                ),
                raw_summary={
                    "title": transfer_record.get("title"),
                    "dest": transfer_record.get("dest"),
                    "status": transfer_record.get("status"),
                    "date": transfer_record.get("date"),
                },
            )

        return None

    def build_pending(self, *, download_hash: str | None, handoff_source: str) -> PathHandoffInfo:
        return PathHandoffInfo(
            download_hash=download_hash,
            source_path=None,
            source_filetype=None,
            source_name=None,
            source_basename=None,
            source_extension=None,
            handoff_source=handoff_source,
            handoff_status="pending_history_sync",
            verification_state=VerificationState.UNVERIFIED,
            note=(
                "真实下载任务已经被宿主接受，但 MusicPilot 暂未从宿主 history API 读回本地路径。"
                "这通常表示宿主下载历史尚未同步到可读取状态。"
            ),
            raw_summary={"download_hash": download_hash},
        )

    def _find_download_history(self, download_hash: str) -> dict[str, Any] | None:
        for page in range(1, self.settings.host_history_download_max_pages + 1):
            payload = self.client.get_json(
                self.settings.host_history_download_path,
                params={
                    "page": page,
                    "count": self.settings.host_history_download_page_size,
                },
                auth_mode="x_api_key",
            )
            items = payload.get("items") if isinstance(payload.get("items"), list) else payload
            if not isinstance(items, list):
                return None
            for item in items:
                if isinstance(item, dict) and str(item.get("download_hash") or "") == download_hash:
                    return item
            if len(items) < self.settings.host_history_download_page_size:
                break
        return None

    def _find_transfer_history(self, download_hash: str) -> dict[str, Any] | None:
        for page in range(1, self.settings.host_history_transfer_max_pages + 1):
            payload = self.client.get_json(
                self.settings.host_history_transfer_path,
                params={
                    "page": page,
                    "count": self.settings.host_history_transfer_page_size,
                },
                auth_mode="x_api_key",
            )
            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            items = data.get("list") if isinstance(data.get("list"), list) else []
            for item in items:
                if isinstance(item, dict) and str(item.get("download_hash") or "") == download_hash:
                    return item
            if len(items) < self.settings.host_history_transfer_page_size:
                break
        return None

    def _build_handoff(
        self,
        *,
        source_path: str,
        download_hash: str,
        handoff_source: str,
        handoff_status: str,
        note: str,
        raw_summary: dict[str, Any],
    ) -> PathHandoffInfo:
        normalized_path = source_path.rstrip("/") if source_path != "/" else source_path
        name = Path(normalized_path).name
        suffix = Path(name).suffix.lower()
        is_file = suffix in KNOWN_FILE_EXTENSIONS
        extension = Path(name).suffix if is_file else ""
        return PathHandoffInfo(
            download_hash=download_hash,
            source_path=source_path,
            source_filetype="file" if is_file else "dir",
            source_name=name,
            source_basename=Path(name).stem if is_file else name,
            source_extension=extension,
            handoff_source=handoff_source,
            handoff_status=handoff_status,
            verification_state=VerificationState.VERIFIED,
            note=note,
            raw_summary=raw_summary,
        )
