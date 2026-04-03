"""Download dispatch adapter boundary for Phase 3."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .host_http import HostHttpClient
from ..core.config import Settings
from ..schemas.acquisition import DispatchAdapterResult, SearchCandidateDetail
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterStrategy, VerificationState


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
    """Host-backed dispatch skeleton for Phase 5."""

    def __init__(self, *, settings: Settings, client: HostHttpClient):
        self.settings = settings
        self.client = client

    def dispatch(
        self,
        *,
        candidate: SearchCandidateDetail,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DispatchAdapterResult:
        payload = {
            "candidate": {
                "id": candidate.id,
                "job_id": candidate.job_id,
                "title": candidate.title,
                "site_id": candidate.site_id,
                "site_name": candidate.site_name,
                "size_bytes": candidate.size_bytes,
                "seeders": candidate.seeders,
                "peers": candidate.peers,
                "format_tag": candidate.format_tag,
                "bitrate_kbps": candidate.bitrate_kbps,
                "source_tags": candidate.source_tags,
                "decision": candidate.decision,
            },
            "candidate_id": candidate.id,
            "job_id": candidate.job_id,
            "title": candidate.title,
            "site_id": candidate.site_id,
            "size_bytes": candidate.size_bytes,
            "seeders": candidate.seeders,
            "peers": candidate.peers,
            "format_tag": candidate.format_tag,
            "bitrate_kbps": candidate.bitrate_kbps,
            "source_tags": candidate.source_tags,
            "decision": candidate.decision,
            "downloader_id": downloader_id,
            "manual_confirm": manual_confirm,
        }
        data = self.client.post_json(self.settings.host_dispatch_path, payload)
        accepted = bool(data.get("accepted", data.get("dispatchable", False)))
        dispatch_status = str(
            data.get(
                "dispatch_status",
                "host_submitted" if accepted else "host_rejected",
            )
        )
        return DispatchAdapterResult(
            dispatchable=accepted,
            dispatch_status=dispatch_status,
            target_downloader=str(data.get("target_downloader") or downloader_id),
            downloader_task_id=data.get("downloader_task_id"),
            note=(
                "当前派发结果来自 configured host dispatch endpoint。请求构造与响应解析已落为可联调骨架，"
                "但真实 MoviePilot 下载器语义仍需联调确认。"
            ),
            integration_point="RealDownloadDispatchAdapter.dispatch",
            mock=False,
            dispatch_backend=AdapterMode.HOST,
            capability_source="host.endpoint",
            verification_state=VerificationState(self.settings.host_verification_state),
            adapter_resolution=AdapterResolution(
                adapter_key="real_download_dispatch",
                adapter_mode=AdapterMode.HOST,
                strategy=AdapterStrategy.PREFER_HOST,
                capability_source="host.endpoint",
                verification_state=VerificationState(self.settings.host_verification_state),
                integration_point="RealDownloadDispatchAdapter.dispatch",
                host_integration_enabled=self.settings.host_integration_enabled,
            ),
        )
