"""Organize preview service for Phase 4."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..adapters.organize import OrganizeAdapter
from ..repositories.acquisition import AcquisitionRepository
from ..repositories.orchestration import OrchestrationRepository
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizePreviewRequest, OrganizePreviewResult
from .search_job import serialize_candidate


class OrganizeService:
    def __init__(self, session: Session, adapter: OrganizeAdapter):
        self.session = session
        self.adapter = adapter
        self.acquisition_repository = AcquisitionRepository(session)
        self.repository = OrchestrationRepository(session)

    def preview(
        self,
        payload: OrganizePreviewRequest,
        *,
        subscription_run_id: str | None = None,
    ) -> OrganizePreviewResult:
        candidate_model = None
        binding_model = None

        if payload.binding_id:
            binding_model = self.acquisition_repository.get_binding(payload.binding_id)
            if binding_model is None:
                raise HTTPException(status_code=404, detail=f"Binding {payload.binding_id} was not found.")
            candidate_model = binding_model.candidate
        elif payload.candidate_id:
            candidate_model = self.acquisition_repository.get_candidate(payload.candidate_id)

        if candidate_model is None:
            raise HTTPException(status_code=404, detail="Candidate for organize preview was not found.")

        metadata_detail = None
        if candidate_model.job and candidate_model.job.metadata_snapshot:
            metadata_detail = MetadataDetail.model_validate(candidate_model.job.metadata_snapshot)

        adapter_result = self.adapter.preview(
            candidate=serialize_candidate(candidate_model),
            metadata_detail=metadata_detail,
            binding_id=binding_model.id if binding_model else None,
        )

        record = self.repository.create_organize_record(
            subscription_run_id=subscription_run_id,
            search_job_id=candidate_model.job_id,
            candidate_id=candidate_model.id,
            binding_id=binding_model.id if binding_model else None,
            result=adapter_result,
        )
        self.session.commit()
        self.session.refresh(record)
        return serialize_organize_record(record)

    def preview_for_candidate(
        self,
        *,
        candidate_id: str,
        subscription_run_id: str | None = None,
    ) -> OrganizePreviewResult:
        return self.preview(
            OrganizePreviewRequest(candidate_id=candidate_id),
            subscription_run_id=subscription_run_id,
        )

    def list_records(self) -> list[OrganizePreviewResult]:
        return [serialize_organize_record(record) for record in self.repository.list_organize_records()]

    def get_record(self, record_id: str) -> OrganizePreviewResult | None:
        record = self.repository.get_organize_record(record_id)
        if record is None:
            return None
        return serialize_organize_record(record)


def serialize_organize_record(record) -> OrganizePreviewResult:
    from ..schemas.orchestration import OrganizeStatus

    return OrganizePreviewResult(
        id=record.id,
        subscription_run_id=record.subscription_run_id,
        search_job_id=record.search_job_id,
        candidate_id=record.candidate_id,
        binding_id=record.binding_id,
        organizeable=record.organizeable,
        organize_status=OrganizeStatus(record.organize_status),
        target_library_path=record.target_library_path,
        strategy_note=record.strategy_note,
        integration_point=record.integration_point,
        mock=record.mock,
        note=record.note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
