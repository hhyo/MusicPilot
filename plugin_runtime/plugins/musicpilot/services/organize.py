"""Host-aware organize preview/apply service for Phase 6."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.acquisition import AcquisitionRepository
from ..repositories.orchestration import OrchestrationRepository
from ..schemas.integration import AdapterMode, AdapterResolution, VerificationState
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeApplyRequest,
    OrganizePlan,
    OrganizePreviewRequest,
    OrganizePreviewResult,
    OrganizeRecordListData,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)
from .host_integration import OrganizeAdapterResolver
from .host_path_handoff import HostPathHandoffService
from .organize_strategy import OrganizeStrategyService
from .search_job import serialize_candidate


class OrganizeService:
    def __init__(
        self,
        session: Session,
        *,
        resolver: OrganizeAdapterResolver,
        strategy_service: OrganizeStrategyService,
        path_handoff_service: HostPathHandoffService,
    ):
        self.session = session
        self.resolver = resolver
        self.strategy_service = strategy_service
        self.path_handoff_service = path_handoff_service
        self.acquisition_repository = AcquisitionRepository(session)
        self.repository = OrchestrationRepository(session)

    def preview(
        self,
        payload: OrganizePreviewRequest,
        *,
        subscription_run_id: str | None = None,
    ) -> OrganizePreviewResult:
        context = self._resolve_context(candidate_id=payload.candidate_id, binding_id=payload.binding_id)
        plan = self.strategy_service.build_plan(
            candidate=context["candidate"],
            metadata_detail=context["metadata_detail"],
        )
        organize_execution = self.resolver.preview(
            candidate=context["candidate"],
            metadata_detail=context["metadata_detail"],
            binding_id=context["binding_id"],
            plan=plan,
        )

        record = self.repository.create_organize_record(
            subscription_run_id=subscription_run_id,
            search_job_id=context["candidate_model"].job_id,
            candidate_id=context["candidate_model"].id,
            binding_id=context["binding_id"],
            result=organize_execution.result,
        )
        self.session.commit()
        self.session.refresh(record)
        return serialize_organize_record(record)

    def apply(self, payload: OrganizeApplyRequest) -> OrganizePreviewResult:
        record = self.repository.get_organize_record(payload.organize_job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Organize job {payload.organize_job_id} was not found.")

        context = self._resolve_context(candidate_id=record.candidate_id, binding_id=record.binding_id)
        plan = self._plan_from_record(record) or self.strategy_service.build_plan(
            candidate=context["candidate"],
            metadata_detail=context["metadata_detail"],
        )

        self.repository.mark_organize_apply_pending(record)
        self.session.commit()
        self.session.refresh(record)

        try:
            organize_execution = self.resolver.apply(
                organize_job_id=record.id,
                candidate=context["candidate"],
                metadata_detail=context["metadata_detail"],
                binding_id=context["binding_id"],
                plan=plan,
            )
            self.repository.update_organize_record(record, result=organize_execution.result)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_record = self.repository.get_organize_record(payload.organize_job_id)
            if failed_record is not None:
                failed_result = self._build_failed_result(
                    record=failed_record,
                    failure_reason=str(exc),
                )
                self.repository.update_organize_record(failed_record, result=failed_result)
                self.session.commit()
                self.session.refresh(failed_record)
            raise

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

    def list_records(self) -> OrganizeRecordListData:
        items = [serialize_organize_record(record) for record in self.repository.list_organize_records()]
        return OrganizeRecordListData(
            items=items,
            total=len(items),
            mock=all(item.mock for item in items) if items else True,
            note="当前 organize records 会显示 backend、status、verification state 与 fallback 信息。",
        )

    def get_record(self, record_id: str) -> OrganizePreviewResult:
        record = self.repository.get_organize_record(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Organize job {record_id} was not found.")
        return serialize_organize_record(record)

    def _resolve_context(self, *, candidate_id: str | None, binding_id: str | None) -> dict:
        candidate_model = None
        binding_model = None

        if binding_id:
            binding_model = self.acquisition_repository.get_binding(binding_id)
            if binding_model is None:
                raise HTTPException(status_code=404, detail=f"Binding {binding_id} was not found.")
            candidate_model = binding_model.candidate
        elif candidate_id:
            candidate_model = self.acquisition_repository.get_candidate(candidate_id)

        if candidate_model is None:
            raise HTTPException(status_code=404, detail="Candidate for organize request was not found.")

        metadata_detail = None
        if candidate_model.job and candidate_model.job.metadata_snapshot:
            metadata_detail = MetadataDetail.model_validate(candidate_model.job.metadata_snapshot)

        candidate_payload = dict(candidate_model.raw_payload or {})
        binding_payload = dict(binding_model.raw_payload or {}) if binding_model else {}
        if not self._has_source_payload(candidate_payload):
            resolved_payload = self._hydrate_path_handoff_payload(
                candidate_payload=candidate_payload,
                binding_payload=binding_payload,
                binding_model=binding_model,
            )
            if resolved_payload is not None:
                candidate_payload = resolved_payload
                candidate_model.raw_payload = candidate_payload
                if binding_model is not None:
                    binding_model.raw_payload = {
                        **binding_payload,
                        **self._binding_payload_patch_from_candidate(candidate_payload),
                    }
        candidate = serialize_candidate(candidate_model)
        if candidate_payload:
            candidate.raw_payload = candidate_payload

        return {
            "candidate_model": candidate_model,
            "binding_model": binding_model,
            "binding_id": binding_model.id if binding_model else None,
            "candidate": candidate,
            "metadata_detail": metadata_detail,
        }

    def _plan_from_record(self, record) -> OrganizePlan | None:
        raw_payload = record.raw_payload or {}
        strategy_snapshot = raw_payload.get("strategy_snapshot")
        if not strategy_snapshot:
            return None
        return OrganizePlan(
            strategy=str(raw_payload.get("strategy") or record.strategy or "music_default_layout"),
            strategy_snapshot=OrganizeStrategySnapshot.model_validate(strategy_snapshot),
            target_library_path=str(raw_payload.get("target_library_path") or record.target_library_path),
            target_relative_path=str(raw_payload.get("target_relative_path") or record.target_relative_path or ""),
            strategy_note=str(raw_payload.get("strategy_note") or record.strategy_note or ""),
        )

    def _build_failed_result(
        self,
        *,
        record,
        failure_reason: str,
    ) -> OrganizeAdapterResult:
        current = serialize_organize_record(record)
        return OrganizeAdapterResult(
            organizeable=current.organizeable,
            organize_backend=current.organize_backend,
            adapter_mode=current.adapter_mode,
            strategy=current.strategy,
            strategy_snapshot=current.strategy_snapshot,
            organize_status=OrganizeStatus.FAILED,
            target_library_path=current.target_library_path,
            target_relative_path=current.target_relative_path,
            strategy_note=current.strategy_note,
            integration_point="OrganizeService.apply",
            capability_source=current.capability_source,
            fallback_reason=current.fallback_reason,
            failure_reason=failure_reason,
            path_handoff=current.path_handoff,
            verification_state=current.verification_state,
            adapter_resolution=current.adapter_resolution,
            mock=current.mock,
            note="Organize apply failed before a verified result could be recorded.",
        )

    def _has_source_payload(self, payload: dict) -> bool:
        return bool(
            payload.get("host_transfer_source_path")
            or payload.get("host_transfer_source")
            or payload.get("source_fileitem")
        )

    def _hydrate_path_handoff_payload(
        self,
        *,
        candidate_payload: dict,
        binding_payload: dict,
        binding_model,
    ) -> dict | None:
        payload = {**candidate_payload}
        if isinstance(binding_payload.get("path_handoff"), dict):
            payload["path_handoff"] = binding_payload["path_handoff"]
        if self._has_source_payload(payload):
            return payload

        download_hash = None
        path_handoff = payload.get("path_handoff")
        if isinstance(path_handoff, dict):
            download_hash = path_handoff.get("download_hash")
        if not download_hash and isinstance(binding_payload.get("path_handoff"), dict):
            download_hash = binding_payload["path_handoff"].get("download_hash")
        if not download_hash and binding_model is not None:
            download_hash = binding_model.downloader_task_id
        if not download_hash:
            return payload

        resolved = self.path_handoff_service.resolve(str(download_hash))
        if resolved is None:
            return payload

        payload["path_handoff"] = resolved.model_dump(mode="json")
        if resolved.source_path:
            payload["host_transfer_source_path"] = resolved.source_path
            payload["host_transfer_filetype"] = resolved.source_filetype or "file"
            payload["host_transfer_source"] = {
                "storage": "local",
                "path": resolved.source_path,
                "type": resolved.source_filetype or "file",
                "name": resolved.source_name,
                "basename": resolved.source_basename,
                "extension": resolved.source_extension,
            }
        return payload

    def _binding_payload_patch_from_candidate(self, candidate_payload: dict) -> dict:
        patch: dict = {}
        if candidate_payload.get("path_handoff"):
            patch["path_handoff"] = candidate_payload["path_handoff"]
        if candidate_payload.get("host_transfer_source"):
            patch["host_transfer_source"] = candidate_payload["host_transfer_source"]
        if candidate_payload.get("host_transfer_source_path"):
            patch["host_transfer_source_path"] = candidate_payload["host_transfer_source_path"]
        if candidate_payload.get("host_transfer_filetype"):
            patch["host_transfer_filetype"] = candidate_payload["host_transfer_filetype"]
        return patch


def serialize_organize_record(record) -> OrganizePreviewResult:
    raw_payload = record.raw_payload or {}
    strategy_snapshot = raw_payload.get("strategy_snapshot") or {
        "strategy_name": record.strategy or "music_default_layout",
        "library_type": record.library_type or "music",
        "root_path": record.root_path or record.target_library_path.rsplit("/", 1)[0],
        "artist_dir_template": "{artist_name}",
        "album_dir_template": "{artist_name}/{year} - {album_title}",
        "track_file_template": "{track_title}.{format_ext}",
        "conflict_policy": record.conflict_policy or "skip_existing",
        "template_note": "Recovered from persisted organize record.",
    }
    resolution_payload = raw_payload.get("adapter_resolution")

    organize_backend = record.organize_backend or raw_payload.get("organize_backend") or "mock"
    verification_state = record.verification_state or raw_payload.get("verification_state") or "placeholder"

    return OrganizePreviewResult(
        id=record.id,
        subscription_run_id=record.subscription_run_id,
        search_job_id=record.search_job_id,
        candidate_id=record.candidate_id,
        binding_id=record.binding_id,
        organizeable=record.organizeable,
        organize_backend=AdapterMode(organize_backend),
        adapter_mode=AdapterMode(organize_backend),
        strategy=record.strategy or raw_payload.get("strategy") or "music_default_layout",
        strategy_snapshot=OrganizeStrategySnapshot.model_validate(strategy_snapshot),
        organize_status=OrganizeStatus(record.organize_status),
        target_library_path=record.target_library_path,
        target_relative_path=record.target_relative_path or raw_payload.get("target_relative_path") or "",
        strategy_note=record.strategy_note,
        integration_point=record.integration_point,
        capability_source=record.capability_source or raw_payload.get("capability_source") or "mock.adapter",
        fallback_reason=record.fallback_reason or raw_payload.get("fallback_reason"),
        failure_reason=record.failure_reason or raw_payload.get("failure_reason"),
        path_handoff=raw_payload.get("path_handoff"),
        verification_state=VerificationState(verification_state),
        adapter_resolution=AdapterResolution.model_validate(resolution_payload) if resolution_payload else None,
        mock=record.mock,
        note=record.note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
