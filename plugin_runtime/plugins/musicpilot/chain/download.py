"""MoviePilot-aligned music download chain."""

from __future__ import annotations

from fastapi import HTTPException

from . import MusicChainBase
from .search import _extract_path_handoff, serialize_candidate
from ..db.acquisition_oper import AcquisitionOper
from ..schemas.acquisition import (
    BindingRetryHandoffResult,
    DispatchRequest,
    DispatchResult,
    DownloadBindingDetail,
    DownloadBindingListData,
    DownloadTaskDetail,
    DownloadTaskListData,
)


RESOLVED_HANDOFF_STATUSES = {
    "resolved_from_history_download",
    "resolved_from_history_transfer",
}

FAILED_HANDOFF_STATUSES = {
    "failed",
    "handoff_unresolved",
}


class MusicDownloadChain(MusicChainBase):
    def __init__(self, session, *, resolver, path_handoff_service=None) -> None:
        super().__init__(cache_region="music_download_chain")
        self.session = session
        self.resolver = resolver
        self.path_handoff_service = path_handoff_service
        self.oper = AcquisitionOper(session)

    def dispatch(self, payload: DispatchRequest) -> DispatchResult:
        candidate_model = self.oper.get_candidate(payload.result_id)
        if candidate_model is None:
            raise HTTPException(status_code=404, detail=f"Candidate {payload.result_id} was not found.")

        candidate = serialize_candidate(candidate_model)
        dispatch_execution = self.resolver.dispatch(
            candidate=candidate,
            downloader_id=payload.downloader_id,
            manual_confirm=payload.manual_confirm,
        )
        adapter_result = dispatch_execution.result

        binding_id = None
        candidate_model.raw_payload = self._merge_dispatch_payload(
            raw_payload=candidate_model.raw_payload or {},
            path_handoff=(
                adapter_result.path_handoff.model_dump(mode="json")
                if adapter_result.path_handoff is not None
                else None
            ),
            host_response_summary=adapter_result.host_response_summary,
        )
        if adapter_result.dispatchable:
            binding = self.oper.create_binding(
                candidate=candidate_model,
                dispatch_result=adapter_result,
            )
            candidate_model.job.status = "dispatched"
            candidate_model.job.summary_json = {
                **(candidate_model.job.summary_json or {}),
                "last_dispatched_candidate_id": candidate_model.id,
                "active_dispatch_adapter": adapter_result.adapter_resolution.adapter_key
                if adapter_result.adapter_resolution
                else None,
            }
            binding_id = binding.id

        self.session.commit()

        return DispatchResult(
            candidate_id=candidate.id,
            job_id=candidate.job_id,
            dispatchable=adapter_result.dispatchable,
            dispatch_status=adapter_result.dispatch_status,
            target_downloader=adapter_result.target_downloader,
            downloader_task_id=adapter_result.downloader_task_id,
            note=adapter_result.note,
            integration_point=adapter_result.integration_point,
            mock=adapter_result.mock,
            binding_id=binding_id,
            dispatch_backend=adapter_result.dispatch_backend,
            capability_source=adapter_result.capability_source,
            fallback_reason=adapter_result.fallback_reason,
            failure_reason=adapter_result.failure_reason,
            verification_state=adapter_result.verification_state,
            path_handoff=adapter_result.path_handoff,
            host_response_summary=adapter_result.host_response_summary,
            adapter_resolution=adapter_result.adapter_resolution,
        )

    def list_bindings(
        self,
        *,
        job_id: str | None = None,
        status: str | None = None,
    ) -> DownloadBindingListData:
        items = [self._serialize_binding(binding) for binding in self.oper.list_bindings(job_id=job_id, dispatch_status=status)]
        return DownloadBindingListData(
            items=items,
            total=len(items),
            mock=all(item.mock for item in items) if items else False,
            note="当前 download bindings 会显示 downloader、dispatch status、path handoff 与候选摘要。",
        )

    def list_tasks(self) -> DownloadTaskListData:
        grouped: dict[str, list] = {}
        for binding in self.oper.list_bindings():
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
        bindings = self.oper.list_bindings_for_task(task_id)
        if not bindings:
            raise HTTPException(status_code=404, detail=f"Download task {task_id} was not found.")
        return self._serialize_task(task_id, bindings, include_bindings=True)

    def get_binding(self, binding_id: str) -> DownloadBindingDetail:
        binding = self.oper.get_binding(binding_id)
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
        binding = self.oper.get_binding(binding_id)
        if binding is None:
            raise HTTPException(status_code=404, detail=f"Binding {binding_id} was not found.")
        result = self.dispatch(
            DispatchRequest(
                result_id=binding.candidate_id,
                downloader_id=downloader_id,
                save_path_policy="auto",
                manual_confirm=manual_confirm,
            )
        )
        retried = self.oper.get_binding(result.binding_id) if result.binding_id else None
        if retried is None:
            raise HTTPException(status_code=409, detail=f"Binding {binding_id} could not be re-dispatched.")
        return self._serialize_binding(retried, include_candidate=True)

    def retry_handoff(self, binding_id: str) -> BindingRetryHandoffResult:
        if self.path_handoff_service is None:
            raise HTTPException(status_code=500, detail="Path handoff service is not configured for downloads workspace.")
        binding = self.oper.get_binding(binding_id)
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
        job_ids: list[str] = []
        candidate_ids: list[str] = []
        dispatch_status_counts: dict[str, int] = {}
        handoff_status_counts: dict[str, int] = {}
        resolved_binding_count = 0
        pending_binding_count = 0
        failed_binding_count = 0

        for binding in ordered:
            if binding.job_id not in job_ids:
                job_ids.append(binding.job_id)
            if binding.candidate_id not in candidate_ids:
                candidate_ids.append(binding.candidate_id)

            dispatch_status_counts[binding.dispatch_status] = dispatch_status_counts.get(binding.dispatch_status, 0) + 1
            binding_handoff = _extract_path_handoff(dict(binding.raw_payload or {}))
            if binding_handoff is None:
                pending_binding_count += 1
                continue
            handoff_status_counts[binding_handoff.handoff_status] = handoff_status_counts.get(binding_handoff.handoff_status, 0) + 1
            if binding_handoff.handoff_status in RESOLVED_HANDOFF_STATUSES:
                resolved_binding_count += 1
            elif binding_handoff.handoff_status in FAILED_HANDOFF_STATUSES:
                failed_binding_count += 1
            else:
                pending_binding_count += 1

        task_status = self._infer_task_status(
            resolved_binding_count=resolved_binding_count,
            pending_binding_count=pending_binding_count,
            failed_binding_count=failed_binding_count,
        )
        binding_summaries = [self._serialize_binding(binding, include_candidate=False) for binding in ordered]
        return DownloadTaskDetail(
            task_id=task_id,
            target_downloader=latest.target_downloader,
            binding_count=len(ordered),
            task_status=task_status,
            latest_dispatch_status=latest.dispatch_status,
            latest_dispatched_at=latest.dispatched_at,
            mock=all(binding.mock for binding in ordered),
            job_ids=job_ids,
            candidate_ids=candidate_ids,
            dispatch_status_counts=dispatch_status_counts,
            handoff_status_counts=handoff_status_counts,
            resolved_binding_count=resolved_binding_count,
            pending_binding_count=pending_binding_count,
            failed_binding_count=failed_binding_count,
            path_handoff=path_handoff,
            host_response_summary=raw_payload.get("host_response_summary") or {},
            bindings=binding_summaries if include_bindings else [],
        )

    @staticmethod
    def _infer_task_status(
        *,
        resolved_binding_count: int,
        pending_binding_count: int,
        failed_binding_count: int,
    ) -> str:
        if failed_binding_count and not resolved_binding_count and not pending_binding_count:
            return "failed"
        if pending_binding_count:
            return "pending_handoff"
        if resolved_binding_count:
            return "handoff_resolved"
        return "dispatched"

    def _merge_dispatch_payload(
        self,
        *,
        raw_payload: dict,
        path_handoff: dict | None,
        host_response_summary: dict,
    ) -> dict:
        merged = {
            **raw_payload,
            "host_response_summary": host_response_summary,
        }
        if path_handoff is None:
            return merged

        merged["path_handoff"] = path_handoff
        source_path = path_handoff.get("source_path")
        source_filetype = path_handoff.get("source_filetype")
        if source_path:
            source_name = path_handoff.get("source_name") or source_path.rsplit("/", 1)[-1]
            source_basename = path_handoff.get("source_basename") or source_name.rsplit(".", 1)[0]
            source_extension = path_handoff.get("source_extension") or (
                f".{source_name.rsplit('.', 1)[-1]}" if "." in source_name else ""
            )
            merged["host_transfer_source_path"] = source_path
            merged["host_transfer_filetype"] = source_filetype or "file"
            merged["host_transfer_source"] = {
                "storage": "local",
                "path": source_path,
                "type": source_filetype or "file",
                "name": source_name,
                "basename": source_basename,
                "extension": source_extension,
            }
        return merged
