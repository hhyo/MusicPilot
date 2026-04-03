"""Dispatch boundary for Phase 3."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..adapters.download_dispatch import DownloadDispatchAdapter
from ..repositories.acquisition import AcquisitionRepository
from ..schemas.acquisition import DispatchRequest, DispatchResult, SearchCandidateDetail
from .search_job import serialize_candidate


class DispatchService:
    def __init__(self, session: Session, adapter: DownloadDispatchAdapter):
        self.session = session
        self.adapter = adapter
        self.repository = AcquisitionRepository(session)

    def dispatch(self, payload: DispatchRequest) -> DispatchResult:
        candidate_model = self.repository.get_candidate(payload.result_id)
        if candidate_model is None:
            raise HTTPException(status_code=404, detail=f"Candidate {payload.result_id} was not found.")

        candidate = serialize_candidate(candidate_model)
        adapter_result = self.adapter.dispatch(
            candidate=candidate,
            downloader_id=payload.downloader_id,
            manual_confirm=payload.manual_confirm,
        )

        binding_id = None
        if adapter_result.dispatchable:
            binding = self.repository.create_binding(
                candidate=candidate_model,
                dispatch_result=adapter_result,
            )
            candidate_model.job.status = "dispatched"
            candidate_model.job.summary_json = {
                **(candidate_model.job.summary_json or {}),
                "dispatch_recommendation": "mock_submitted",
                "last_dispatched_candidate_id": candidate_model.id,
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
        )
