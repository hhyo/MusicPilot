"""Download dispatch adapter boundary with MoviePilot runtime mapping."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .host_http import HostHttpClient
from ..core.config import Settings
from ..schemas.acquisition import DispatchAdapterResult, SearchCandidateDetail
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterStrategy, VerificationState
from ..services.host_path_handoff import HostPathHandoffService


class DownloadDispatchAdapter(ABC):
    @abstractmethod
    def dispatch(
        self,
        *,
        candidate: SearchCandidateDetail,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DispatchAdapterResult:
        """Dispatch a candidate to the downstream downloader."""


class MockDownloadDispatchAdapter(DownloadDispatchAdapter):
    """Mock downloader adapter used to preserve the integration boundary."""

    def dispatch(
        self,
        *,
        candidate: SearchCandidateDetail,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DispatchAdapterResult:
        if not candidate.dispatchable:
            return DispatchAdapterResult(
                dispatchable=False,
                dispatch_status="blocked",
                target_downloader=downloader_id,
                note="候选当前不满足派发条件，当前 mock dispatch 不会向真实下载器下发任务。",
                integration_point="Replace MockDownloadDispatchAdapter with a verified MoviePilot downloader adapter in a later phase.",
                dispatch_backend=AdapterMode.MOCK,
                capability_source="mock.adapter",
                verification_state=VerificationState.PLACEHOLDER,
                adapter_resolution=AdapterResolution(
                    adapter_key="mock_download_dispatch",
                    adapter_mode=AdapterMode.MOCK,
                    strategy=AdapterStrategy.MOCK,
                    capability_source="mock.adapter",
                    verification_state=VerificationState.PLACEHOLDER,
                    integration_point="MockDownloadDispatchAdapter.dispatch",
                    host_integration_enabled=False,
                ),
            )

        if candidate.decision == "manual_confirm" and not manual_confirm:
            return DispatchAdapterResult(
                dispatchable=False,
                dispatch_status="awaiting_manual_confirmation",
                target_downloader=downloader_id,
                note="该候选需要人工确认后才允许进入派发流程。",
                integration_point="Keep manual confirmation in frontend/API until a verified downloader adapter is connected.",
                dispatch_backend=AdapterMode.MOCK,
                capability_source="mock.adapter",
                verification_state=VerificationState.PLACEHOLDER,
                adapter_resolution=AdapterResolution(
                    adapter_key="mock_download_dispatch",
                    adapter_mode=AdapterMode.MOCK,
                    strategy=AdapterStrategy.MOCK,
                    capability_source="mock.adapter",
                    verification_state=VerificationState.PLACEHOLDER,
                    integration_point="MockDownloadDispatchAdapter.dispatch",
                    host_integration_enabled=False,
                ),
            )

        return DispatchAdapterResult(
            dispatchable=True,
            dispatch_status="mock_submitted",
            target_downloader=downloader_id,
            downloader_task_id=f"mock-task-{candidate.id}",
            note="当前为 mock dispatch，已返回占位下发结果，待后续真实下载器接入。",
            integration_point="Replace MockDownloadDispatchAdapter with a verified MoviePilot downloader adapter in a later phase.",
            dispatch_backend=AdapterMode.MOCK,
            capability_source="mock.adapter",
            verification_state=VerificationState.PLACEHOLDER,
            adapter_resolution=AdapterResolution(
                adapter_key="mock_download_dispatch",
                adapter_mode=AdapterMode.MOCK,
                strategy=AdapterStrategy.MOCK,
                capability_source="mock.adapter",
                verification_state=VerificationState.PLACEHOLDER,
                integration_point="MockDownloadDispatchAdapter.dispatch",
                host_integration_enabled=False,
            ),
        )


class RealDownloadDispatchAdapter(DownloadDispatchAdapter):
    """MoviePilot-backed download dispatch adapter."""

    def __init__(
        self,
        *,
        settings: Settings,
        client: HostHttpClient,
        path_handoff_service: HostPathHandoffService,
    ):
        self.settings = settings
        self.client = client
        self.path_handoff_service = path_handoff_service

    def dispatch(
        self,
        *,
        candidate: SearchCandidateDetail,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DispatchAdapterResult:
        context_payload = self._extract_host_context(candidate)
        torrent_in = self._build_torrent_payload(candidate, context_payload)
        media_in = self._extract_media_payload(context_payload)
        target_downloader, downloader_fallback = self._resolve_target_downloader(downloader_id)

        if media_in:
            path = self.settings.host_download_media_path or "/api/v1/download/"
            payload = {
                "media_in": media_in,
                "torrent_in": torrent_in,
                "downloader": target_downloader,
            }
        else:
            path = self.settings.host_download_add_path or self.settings.host_dispatch_path
            payload = {
                "torrent_in": torrent_in,
                "downloader": target_downloader,
            }

        data = self.client.post_json(path, payload, auth_mode="x_api_key")
        success = bool(data.get("success"))
        message = self._optional_text(data.get("message"))
        response_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        dispatch_status = "host_submitted" if success else "host_rejected"
        download_id = self._optional_text(response_data.get("download_id") if isinstance(response_data, dict) else None)
        path_handoff = None
        if success:
            path_handoff = self.path_handoff_service.resolve(download_id)
            if path_handoff is None:
                path_handoff = self.path_handoff_service.build_pending(
                    download_hash=download_id,
                    handoff_source="moviepilot.runtime.history.download",
                )

        return DispatchAdapterResult(
            dispatchable=success,
            dispatch_status=dispatch_status,
            target_downloader=target_downloader,
            downloader_task_id=download_id,
            note=(
                "当前派发结果来自真实 MoviePilot `/api/v1/download/add` 或 `/api/v1/download/` 语义。"
                "如果宿主返回 `success=false`，这表示 payload 已被宿主接受并给出明确拒绝原因，而不是本地 mock。"
                "Phase 7B 已拿到真实 `success=true` 的最小下载样例。"
            ),
            integration_point="RealDownloadDispatchAdapter.dispatch.moviepilot",
            mock=False,
            dispatch_backend=AdapterMode.HOST,
            capability_source="moviepilot.runtime.download.add",
            fallback_reason=downloader_fallback,
            failure_reason=message if not success else None,
            verification_state=VerificationState.VERIFIED,
            path_handoff=path_handoff,
            host_response_summary={
                "path": path,
                "success": success,
                "message": message,
                "download_id": download_id,
            },
            adapter_resolution=AdapterResolution(
                adapter_key="real_download_dispatch",
                adapter_mode=AdapterMode.HOST,
                strategy=AdapterStrategy.PREFER_HOST,
                capability_source="moviepilot.runtime.download.add",
                verification_state=VerificationState.VERIFIED,
                fallback_reason=downloader_fallback,
                integration_point="RealDownloadDispatchAdapter.dispatch.moviepilot",
                host_integration_enabled=self.settings.host_integration_enabled,
            ),
        )

    def _resolve_target_downloader(self, requested: str) -> tuple[str, str | None]:
        if not self.settings.host_dispatch_validate_clients:
            return requested, None

        payload = self.client.get_json(
            self.settings.host_downloaders_path,
            auth_mode="x_api_key",
        )
        items = payload.get("items") if isinstance(payload.get("items"), list) else payload
        if not isinstance(items, list):
            return requested, None

        available_names = [str(item.get("name")) for item in items if isinstance(item, dict) and item.get("name")]
        if requested in available_names:
            return requested, None
        if available_names:
            return available_names[0], f"downloader_name_remapped:{requested}->{available_names[0]}"
        return requested, "downloader_clients_empty"

    def _extract_host_context(self, candidate: SearchCandidateDetail) -> dict[str, Any]:
        raw_payload = candidate.raw_payload or {}
        host_context = raw_payload.get("host_context")
        return host_context if isinstance(host_context, dict) else {}

    def _build_torrent_payload(self, candidate: SearchCandidateDetail, context_payload: dict[str, Any]) -> dict[str, Any]:
        torrent = context_payload.get("torrent_info") if isinstance(context_payload.get("torrent_info"), dict) else {}
        payload = {
            "site": self._to_int_or_none(torrent.get("site")) or self._to_int_or_none(candidate.site_id),
            "site_name": str(torrent.get("site_name") or candidate.site_name),
            "title": str(torrent.get("title") or candidate.title),
            "description": str(torrent.get("description") or candidate.note or ""),
            "enclosure": self._optional_text(torrent.get("enclosure")),
            "page_url": self._optional_text(torrent.get("page_url") or context_payload.get("page_url")),
            "size": self._numeric_size(torrent.get("size"), candidate.size_bytes),
            "seeders": self._to_int_or_none(torrent.get("seeders")) or candidate.seeders,
            "peers": self._to_int_or_none(torrent.get("peers")) or candidate.peers,
            "labels": torrent.get("labels") if isinstance(torrent.get("labels"), list) else candidate.source_tags,
            "volume_factor": self._optional_text(torrent.get("volume_factor")),
            "pubdate": self._optional_text(torrent.get("pubdate")),
        }
        return {key: value for key, value in payload.items() if value is not None}

    def _extract_media_payload(self, context_payload: dict[str, Any]) -> dict[str, Any] | None:
        media = context_payload.get("media_info")
        if not isinstance(media, dict):
            return None
        if not any(value not in (None, "", [], {}) for value in media.values()):
            return None
        return media

    def _numeric_size(self, raw_size: Any, fallback: int) -> float:
        if raw_size in (None, ""):
            return float(fallback)
        try:
            return float(raw_size)
        except (TypeError, ValueError):
            return float(fallback)

    def _to_int_or_none(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _optional_text(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
