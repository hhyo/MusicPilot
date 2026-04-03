"""Download dispatch adapter boundary for Phase 3."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas.acquisition import DispatchAdapterResult, SearchCandidateDetail


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
            )

        if candidate.decision == "manual_confirm" and not manual_confirm:
            return DispatchAdapterResult(
                dispatchable=False,
                dispatch_status="awaiting_manual_confirmation",
                target_downloader=downloader_id,
                note="该候选需要人工确认后才允许进入派发流程。",
                integration_point="Keep manual confirmation in frontend/API until a verified downloader adapter is connected.",
            )

        return DispatchAdapterResult(
            dispatchable=True,
            dispatch_status="mock_submitted",
            target_downloader=downloader_id,
            downloader_task_id=f"mock-task-{candidate.id}",
            note="当前为 mock dispatch，已返回占位下发结果，待后续真实下载器接入。",
            integration_point="Replace MockDownloadDispatchAdapter with a verified MoviePilot downloader adapter in a later phase.",
        )
