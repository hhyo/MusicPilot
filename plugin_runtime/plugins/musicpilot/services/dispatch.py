"""Dispatch boundary for Phase 3."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.acquisition import AcquisitionRepository
from ..schemas.acquisition import DispatchRequest, DispatchResult
from .host_integration import DispatchAdapterResolver
from .search_job import serialize_candidate


class DispatchService:
    def __init__(self, session: Session, resolver: DispatchAdapterResolver):
        self.session = session
        self.resolver = resolver
        self.repository = AcquisitionRepository(session)

    def dispatch(self, payload: DispatchRequest) -> DispatchResult:
        candidate_model = self.repository.get_candidate(payload.result_id)
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
        if adapter_result.dispatchable:
            if adapter_result.path_handoff is not None:
                candidate_model.raw_payload = self._merge_path_handoff_payload(
                    candidate_model.raw_payload or {},
                    adapter_result.path_handoff.model_dump(mode="json"),
                )
            binding = self.repository.create_binding(
                candidate=candidate_model,
                dispatch_result=adapter_result,
            )
            candidate_model.job.status = "dispatched"
            candidate_model.job.summary_json = {
                **(candidate_model.job.summary_json or {}),
                "dispatch_recommendation": adapter_result.dispatch_status,
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

    def _merge_path_handoff_payload(
        self,
        raw_payload: dict,
        handoff: dict,
    ) -> dict:
        merged = {**raw_payload, "path_handoff": handoff}
        source_path = handoff.get("source_path")
        source_filetype = handoff.get("source_filetype")
        if source_path:
            source_name = handoff.get("source_name") or source_path.rsplit("/", 1)[-1]
            source_basename = handoff.get("source_basename") or source_name.rsplit(".", 1)[0]
            source_extension = handoff.get("source_extension") or (
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
