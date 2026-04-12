"""Downloads workspace listing/detail service."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.acquisition import AcquisitionRepository
from ..schemas.acquisition import DownloadBindingDetail, DownloadBindingListData, DownloadBindingSummary
from .search_job import _extract_path_handoff, serialize_candidate


class DownloadsWorkspaceService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = AcquisitionRepository(session)

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

    def get_binding(self, binding_id: str) -> DownloadBindingDetail:
        binding = self.repository.get_binding(binding_id)
        if binding is None:
            raise HTTPException(status_code=404, detail=f"Binding {binding_id} was not found.")
        return self._serialize_binding(binding, include_candidate=True)

    def _serialize_binding(self, binding, *, include_candidate: bool = False) -> DownloadBindingDetail:
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
