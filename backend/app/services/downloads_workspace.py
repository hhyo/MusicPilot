"""Downloads workspace listing/detail service."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.acquisition import AcquisitionRepository
from ..schemas.acquisition import (
    BindingRetryHandoffResult,
    DownloadBindingDetail,
    DownloadBindingListData,
    DownloadBindingSummary,
    DownloadTaskDetail,
    DownloadTaskListData,
    DownloadTaskSummary,
    DispatchRequest,
)
from .search_job import _extract_path_handoff, serialize_candidate


class DownloadsWorkspaceService:
    def __init__(self, session: Session, *, dispatch_service=None, path_handoff_service=None):
        self.session = session
        self.repository = AcquisitionRepository(session)
        self.dispatch_service = dispatch_service
        self.path_handoff_service = path_handoff_service

    def list_bindings(
        self,
        *,
        job_id: str | None = None,
        status: str | None = None,
    ) -> DownloadBindingListData:
        items = [self._serialize_binding(binding) for binding in self.repository.list_bindings(job_id=job_id, dispatch_status=status)]
        return DownloadBindingListData(
            items=items,
            total=len(items),
            mock=all(item.mock for item in items) if items else False,
            note="当前 download bindings 会显示 downloader、dispatch status、path handoff 与候选摘要。",
        )

    def list_tasks(self) -> DownloadTaskListData:
        grouped: dict[str, list] = {}
        for binding in self.repository.list_bindings():
            if not binding.downloader_task_id:
                continue
            grouped.setdefault(binding.downloader_task_id, []).append(binding)
        items = [self._serialize_task(task_id, bindings) for task_id, bindings in grouped.items()]
        items.sort(key=lambda item: item.latest_dispatched_at, reverse=True)
        return DownloadTaskListData(
            items=items,
            total=len(items),
            mock=all(item.mock for item in items) if items else False,
            note="当前 download tasks 按 downloader task 聚合 bindings，并暴露 handoff 与最新 dispatch 状态。",
        )

    def get_task(self, task_id: str) -> DownloadTaskDetail:
        bindings = self.repository.list_bindings_for_task(task_id)
        if not bindings:
            raise HTTPException(status_code=404, detail=f"Download task {task_id} was not found.")
        return self._serialize_task(task_id, bindings, include_bindings=True)

    def get_binding(self, binding_id: str) -> DownloadBindingDetail:
        binding = self.repository.get_binding(binding_id)
        if binding is None:
            raise HTTPException(status_code=404, detail=f"Binding {binding_id} was not found.")
        return self._serialize_binding(binding, include_candidate=True)

    def retry_dispatch(
        self,
        binding_id: str,
        *,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DownloadBindingDetail:
        if self.dispatch_service is None:
            raise HTTPException(status_code=500, detail="Dispatch service is not configured for downloads workspace.")
        binding = self.repository.get_binding(binding_id)
        if binding is None:
            raise HTTPException(status_code=404, detail=f"Binding {binding_id} was not found.")
        result = self.dispatch_service.dispatch(
            DispatchRequest(
                result_id=binding.candidate_id,
                downloader_id=downloader_id,
                manual_confirm=manual_confirm,
            )
        )
        retried = self.repository.get_binding(result.binding_id) if result.binding_id else None
        if retried is None:
            raise HTTPException(status_code=409, detail=f"Binding {binding_id} could not be re-dispatched.")
        return self._serialize_binding(retried, include_candidate=True)

    def retry_handoff(self, binding_id: str) -> BindingRetryHandoffResult:
        if self.path_handoff_service is None:
            raise HTTPException(status_code=500, detail="Path handoff service is not configured for downloads workspace.")
        binding = self.repository.get_binding(binding_id)
        if binding is None:
            raise HTTPException(status_code=404, detail=f"Binding {binding_id} was not found.")
        handoff = self.path_handoff_service.resolve_from_download(binding.downloader_task_id)
        raw_payload = dict(binding.raw_payload or {})
        if handoff is not None:
            raw_payload["path_handoff"] = handoff.model_dump(mode="json")
        binding.raw_payload = raw_payload
        self.session.commit()
        self.session.refresh(binding)
        return BindingRetryHandoffResult(
            binding=self._serialize_binding(binding, include_candidate=True),
            resolved=handoff is not None,
            note="Binding handoff refreshed from host history download.",
        )

    def _serialize_binding(self, binding, *, include_candidate: bool = False) -> DownloadBindingDetail:
        return self.serialize_binding_static(binding, include_candidate=include_candidate)

    @staticmethod
    def serialize_binding_static(binding, *, include_candidate: bool = False) -> DownloadBindingDetail:
        raw_payload = dict(binding.raw_payload or {})
        candidate = serialize_candidate(binding.candidate) if include_candidate and binding.candidate is not None else None
        return DownloadBindingDetail(
            id=binding.id,
            job_id=binding.job_id,
            candidate_id=binding.candidate_id,
            target_downloader=binding.target_downloader,
            downloader_task_id=binding.downloader_task_id,
            dispatchable=binding.dispatchable,
            dispatch_status=binding.dispatch_status,
            mock=binding.mock,
            note=binding.note,
            integration_point=binding.integration_point,
            dispatched_at=binding.dispatched_at,
            path_handoff=_extract_path_handoff(raw_payload),
            host_response_summary=raw_payload.get("host_response_summary") or {},
            candidate=candidate,
            raw_payload=raw_payload,
        )

    def _serialize_task(self, task_id: str, bindings: list, *, include_bindings: bool = False) -> DownloadTaskDetail:
        ordered = sorted(bindings, key=lambda item: item.dispatched_at, reverse=True)
        latest = ordered[0]
        raw_payload = dict(latest.raw_payload or {})
        path_handoff = _extract_path_handoff(raw_payload)
        binding_summaries = [self._serialize_binding(binding, include_candidate=False) for binding in ordered]
        return DownloadTaskDetail(
            task_id=task_id,
            target_downloader=latest.target_downloader,
            binding_count=len(ordered),
            latest_dispatch_status=latest.dispatch_status,
            latest_dispatched_at=latest.dispatched_at,
            mock=all(binding.mock for binding in ordered),
            path_handoff=path_handoff,
            host_response_summary=raw_payload.get("host_response_summary") or {},
            bindings=binding_summaries if include_bindings else [],
        )
