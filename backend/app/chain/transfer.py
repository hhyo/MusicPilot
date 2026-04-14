"""MoviePilot-aligned music transfer chain."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from . import MusicChainBase
from .search import serialize_candidate
from ..db.acquisition_oper import AcquisitionOper
from ..db.orchestration_oper import OrchestrationOper
from ..schemas.acquisition import PathHandoffInfo
from ..schemas.integration import AdapterMode, AdapterResolution, VerificationState
from ..schemas.music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMetaBase,
    MusicRecognitionAssessment,
)
from ..schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeApplyRequest,
    OrganizePlan,
    OrganizePreviewRequest,
    OrganizePreviewResult,
    OrganizeRecordListData,
    OrganizeStatus,
    OrganizeStrategySnapshot,
    PendingHandoffDiagnostic,
    PendingHandoffReconcileResult,
    PendingHandoffSummary,
    SubscriptionRunStatus,
)
from ..schemas.shared import utc_now


class MusicTransferChain(MusicChainBase):
    def __init__(
        self,
        session,
        *,
        resolver,
        strategy_service,
        path_handoff_service,
        music_media_chain,
        handoff_pending_ttl_seconds: int = 300,
    ):
        super().__init__(cache_region="music_transfer_chain")
        self.session = session
        self.resolver = resolver
        self.strategy_service = strategy_service
        self.path_handoff_service = path_handoff_service
        self.music_media_chain = music_media_chain
        self.handoff_pending_ttl_seconds = handoff_pending_ttl_seconds
        self.acquisition_repository = AcquisitionOper(session)
        self.repository = OrchestrationOper(session)

    def process(self, *, now: datetime | None = None) -> dict:
        current_time = now or utc_now()
        summary = PendingHandoffSummary()
        processed_binding_ids: list[str] = []
        created_record_ids: list[str] = []
        applied_record_ids: list[str] = []
        pending_record_ids: list[str] = []
        skipped_binding_ids: list[str] = []
        diagnostics: list[PendingHandoffDiagnostic] = []

        for binding in self.acquisition_repository.list_transfer_bindings():
            if not binding.id:
                continue
            if self.repository.get_organize_record_by_binding(binding.id):
                continue
            try:
                preview = self.preview(OrganizePreviewRequest(binding_id=binding.id))
            except HTTPException:
                skipped_binding_ids.append(binding.id)
                summary.skipped += 1
                continue

            processed_binding_ids.append(binding.id)
            created_record_ids.append(preview.id)
            summary.created += 1

            if self._handoff_ready(preview=preview, binding=binding):
                applied = self.apply(OrganizeApplyRequest(organize_job_id=preview.id))
                applied_record_ids.append(applied.id)
                summary.applied += 1
                diagnostics.append(
                    PendingHandoffDiagnostic(
                        record_id=applied.id,
                        binding_id=binding.id,
                        subscription_run_id=None,
                        reason="applied",
                        handoff_status=applied.path_handoff.handoff_status if applied.path_handoff else None,
                        age_seconds=0,
                        ttl_seconds=self.handoff_pending_ttl_seconds,
                    )
                )
            else:
                pending_record_ids.append(preview.id)
                summary.pending += 1

        pending_result = self.reconcile_pending_once(now=current_time, skip_record_ids=set(created_record_ids))
        pending_summary = pending_result.get("summary") or {}
        summary.applied += int(pending_summary.get("applied", 0))
        summary.unresolved += int(pending_summary.get("unresolved", 0))
        summary.failed += int(pending_summary.get("failed", 0))
        summary.pending += int(pending_summary.get("pending", 0))
        summary.skipped += int(pending_summary.get("skipped", 0))
        diagnostics.extend(
            [PendingHandoffDiagnostic.model_validate(item) for item in pending_result.get("diagnostics", [])]
        )

        return {
            "summary": summary.model_dump(mode="json"),
            "processed_binding_ids": processed_binding_ids,
            "created_record_ids": created_record_ids,
            "applied_record_ids": applied_record_ids,
            "pending_record_ids": pending_record_ids,
            "unresolved_record_ids": [],
            "failed_record_ids": [],
            "skipped_binding_ids": skipped_binding_ids,
            "diagnostics": [item.model_dump(mode="json") for item in diagnostics],
        }

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
            music_media_input=context["music_media_input"].model_dump(mode="json")
            if context["music_media_input"]
            else None,
            music_meta_base=context["music_meta_base"].model_dump(mode="json")
            if context["music_meta_base"]
            else None,
            music_recognition_assessment=context["music_recognition_assessment"].model_dump(mode="json")
            if context["music_recognition_assessment"]
            else None,
            music_media_info=context["music_media_info"].model_dump(mode="json")
            if context["music_media_info"]
            else None,
        )
        self.session.commit()
        self.session.refresh(record)
        return serialize_organize_record(record)

    def apply(self, payload: OrganizeApplyRequest) -> OrganizePreviewResult:
        return self._apply_record(payload.organize_job_id)

    def rebuild_preview(self, record_id: str) -> OrganizePreviewResult:
        return self._preview_record(record_id, persist_repaired_context=False)

    def repair_source_path(self, record_id: str) -> OrganizePreviewResult:
        return self._preview_record(record_id, persist_repaired_context=True)

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

    def list_records(
        self,
        *,
        status: str | None = None,
        organize_backend: str | None = None,
        verification_state: str | None = None,
        candidate_id: str | None = None,
        binding_id: str | None = None,
        search_job_id: str | None = None,
        subscription_run_id: str | None = None,
    ) -> OrganizeRecordListData:
        items = [
            serialize_organize_record(record)
            for record in self.repository.list_organize_records(
                organize_status=status,
                organize_backend=organize_backend,
                verification_state=verification_state,
                candidate_id=candidate_id,
                binding_id=binding_id,
                search_job_id=search_job_id,
                subscription_run_id=subscription_run_id,
            )
        ]
        return OrganizeRecordListData(
            items=items,
            total=len(items),
            mock=all(item.mock for item in items) if items else True,
            note="当前 organize records 会显示 backend、status、verification state、handoff source 与 fallback 信息。",
        )

    def get_record(self, record_id: str) -> OrganizePreviewResult:
        record = self.repository.get_organize_record(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Organize job {record_id} was not found.")
        return serialize_organize_record(record)

    def retry(self, record_id: str) -> OrganizePreviewResult:
        return self.apply(OrganizeApplyRequest(organize_job_id=record_id))

    def reconcile_pending_once(
        self,
        *,
        now: datetime | None = None,
        skip_record_ids: set[str] | None = None,
    ) -> dict:
        current_time = now or utc_now()
        applied_run_ids: list[str] = []
        unresolved_run_ids: list[str] = []
        skipped_record_ids: list[str] = []
        diagnostics: list[PendingHandoffDiagnostic] = []
        summary = PendingHandoffSummary()
        skip_record_ids = skip_record_ids or set()

        for record in self.repository.list_pending_handoff_records():
            if record.id in skip_record_ids:
                continue
            age_seconds = self._record_age_seconds(record=record, now=current_time)
            if not record.binding_id:
                skipped_record_ids.append(record.id)
                summary.skipped += 1
                diagnostics.append(
                    PendingHandoffDiagnostic(
                        record_id=record.id,
                        subscription_run_id=record.subscription_run_id,
                        reason="missing_binding",
                        age_seconds=age_seconds,
                        ttl_seconds=self.handoff_pending_ttl_seconds,
                    )
                )
                continue

            binding = self.acquisition_repository.get_binding(record.binding_id)
            if binding is None or not binding.downloader_task_id:
                skipped_record_ids.append(record.id)
                summary.skipped += 1
                diagnostics.append(
                    PendingHandoffDiagnostic(
                        record_id=record.id,
                        binding_id=record.binding_id,
                        subscription_run_id=record.subscription_run_id,
                        reason="missing_download_task",
                        age_seconds=age_seconds,
                        ttl_seconds=self.handoff_pending_ttl_seconds,
                    )
                )
                continue

            resolved = self.path_handoff_service.resolve_from_download(binding.downloader_task_id)
            if resolved is not None:
                self._store_handoff_state(record=record, binding=binding, handoff=resolved, now=current_time)
                try:
                    applied = self.apply(OrganizeApplyRequest(organize_job_id=record.id))
                    self._apply_result_to_record(record=record, applied=applied, now=current_time)
                    self._update_run_after_apply(
                        record=record,
                        organize_status=applied.organize_status,
                        handoff=resolved,
                        now=current_time,
                    )
                    if record.subscription_run_id:
                        applied_run_ids.append(record.subscription_run_id)
                    summary.applied += 1
                    diagnostics.append(
                        PendingHandoffDiagnostic(
                            record_id=record.id,
                            binding_id=record.binding_id,
                            subscription_run_id=record.subscription_run_id,
                            reason="applied",
                            handoff_status=resolved.handoff_status,
                            age_seconds=age_seconds,
                            ttl_seconds=self.handoff_pending_ttl_seconds,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    self._mark_apply_failed(record=record, handoff=resolved, error_message=str(exc), now=current_time)
                    self._update_run_apply_failed(
                        record=record,
                        handoff=resolved,
                        error_message=str(exc),
                        now=current_time,
                    )
                    summary.failed += 1
                    diagnostics.append(
                        PendingHandoffDiagnostic(
                            record_id=record.id,
                            binding_id=record.binding_id,
                            subscription_run_id=record.subscription_run_id,
                            reason="apply_failed",
                            handoff_status=resolved.handoff_status,
                            age_seconds=age_seconds,
                            ttl_seconds=self.handoff_pending_ttl_seconds,
                            error_message=str(exc),
                        )
                    )
                continue

            if self._is_stale(binding=binding, now=current_time):
                unresolved = self.path_handoff_service.build_unresolved(
                    download_hash=binding.downloader_task_id,
                    handoff_source="moviepilot.runtime.history.download",
                )
                self._store_handoff_state(record=record, binding=binding, handoff=unresolved, now=current_time)
                self._mark_record_handoff_unresolved(record=record, handoff=unresolved, now=current_time)
                self._update_run_handoff_status(record=record, handoff=unresolved, now=current_time)
                if record.subscription_run_id:
                    unresolved_run_ids.append(record.subscription_run_id)
                summary.unresolved += 1
                diagnostics.append(
                    PendingHandoffDiagnostic(
                        record_id=record.id,
                        binding_id=record.binding_id,
                        subscription_run_id=record.subscription_run_id,
                        reason="handoff_unresolved",
                        handoff_status=unresolved.handoff_status,
                        age_seconds=age_seconds,
                        ttl_seconds=self.handoff_pending_ttl_seconds,
                    )
                )
                continue

            skipped_record_ids.append(record.id)
            summary.pending += 1
            diagnostics.append(
                PendingHandoffDiagnostic(
                    record_id=record.id,
                    binding_id=record.binding_id,
                    subscription_run_id=record.subscription_run_id,
                    reason="pending_retry_window",
                    handoff_status="pending_history_sync",
                    age_seconds=age_seconds,
                    ttl_seconds=self.handoff_pending_ttl_seconds,
                )
            )

        self.session.commit()
        return PendingHandoffReconcileResult(
            summary=summary,
            applied_run_ids=applied_run_ids,
            unresolved_run_ids=unresolved_run_ids,
            skipped_record_ids=skipped_record_ids,
            diagnostics=diagnostics,
        ).model_dump(mode="json")

    def _apply_record(self, record_id: str) -> OrganizePreviewResult:
        record = self.repository.get_organize_record(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Organize job {record_id} was not found.")

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
            self.repository.update_organize_record(
                record,
                result=organize_execution.result,
                music_media_input=record.music_media_input or {},
                music_meta_base=record.music_meta_base or {},
                music_recognition_assessment=record.music_recognition_assessment or {},
                music_media_info=record.music_media_info or {},
            )
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_record = self.repository.get_organize_record(record_id)
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

    def _preview_record(self, record_id: str, *, persist_repaired_context: bool) -> OrganizePreviewResult:
        record = self.repository.get_organize_record(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Organize job {record_id} was not found.")

        context = self._resolve_context(
            candidate_id=record.candidate_id,
            binding_id=record.binding_id,
            persist_repaired_context=persist_repaired_context,
        )
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
        self.repository.update_organize_record(
            record,
            result=organize_execution.result,
            music_media_input=context["music_media_input"].model_dump(mode="json")
            if context["music_media_input"]
            else record.music_media_input or {},
            music_meta_base=context["music_meta_base"].model_dump(mode="json")
            if context["music_meta_base"]
            else record.music_meta_base or {},
            music_recognition_assessment=context["music_recognition_assessment"].model_dump(mode="json")
            if context["music_recognition_assessment"]
            else record.music_recognition_assessment or {},
            music_media_info=context["music_media_info"].model_dump(mode="json")
            if context["music_media_info"]
            else record.music_media_info or {},
        )
        self.session.commit()
        self.session.refresh(record)
        return serialize_organize_record(record)

    def _resolve_context(
        self,
        *,
        candidate_id: str | None,
        binding_id: str | None,
        persist_repaired_context: bool = True,
    ) -> dict:
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

        candidate_payload = dict(candidate_model.raw_payload or {})
        binding_payload = dict(binding_model.raw_payload or {}) if binding_model else {}
        metadata_detail = None
        music_media_input = None
        music_meta_base = None
        recognition_assessment = None
        music_media_info = None

        if candidate_model.job is not None:
            music_media_input = _parse_optional_music_media_input(candidate_model.job.music_media_input)
            music_meta_base = _parse_optional_music_meta_base(candidate_model.job.music_meta_base)
            recognition_assessment = _parse_optional_music_recognition_assessment(
                candidate_model.job.music_recognition_assessment
            )
            music_media_info = _parse_optional_music_media_info(candidate_model.job.music_media_info)

        if music_media_info is not None:
            metadata_detail = self.music_media_chain.hydrate(music_media_info)

        if "path_handoff" not in candidate_payload and isinstance(binding_payload.get("path_handoff"), dict):
            candidate_payload["path_handoff"] = binding_payload["path_handoff"]
        if "host_transfer_downloader" not in candidate_payload:
            host_transfer_downloader = self._resolve_binding_downloader(
                binding_payload=binding_payload,
                binding_model=binding_model,
            )
            if host_transfer_downloader:
                candidate_payload["host_transfer_downloader"] = host_transfer_downloader
        if not self._has_source_payload(candidate_payload):
            resolved_payload = self._hydrate_path_handoff_payload(
                candidate_payload=candidate_payload,
                binding_payload=binding_payload,
                binding_model=binding_model,
            )
            if resolved_payload is not None:
                candidate_payload = resolved_payload
                if persist_repaired_context:
                    candidate_model.raw_payload = candidate_payload
                    if binding_model is not None:
                        binding_model.raw_payload = {
                            **binding_payload,
                            **self._binding_payload_patch_from_candidate(candidate_payload),
                        }
        if "host_response_summary" not in candidate_payload and isinstance(binding_payload.get("host_response_summary"), dict):
            candidate_payload["host_response_summary"] = binding_payload["host_response_summary"]
        candidate = serialize_candidate(candidate_model)
        if candidate_payload:
            candidate.raw_payload = candidate_payload
            candidate.path_handoff = _extract_candidate_path_handoff(candidate_payload)

        return {
            "candidate_model": candidate_model,
            "binding_model": binding_model,
            "binding_id": binding_model.id if binding_model else None,
            "candidate": candidate,
            "metadata_detail": metadata_detail,
            "music_media_input": music_media_input,
            "music_meta_base": music_meta_base,
            "music_recognition_assessment": recognition_assessment,
            "music_media_info": music_media_info,
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

    def _store_handoff_state(self, *, record, binding, handoff: PathHandoffInfo, now: datetime) -> None:
        handoff_payload = handoff.model_dump(mode="json")
        binding.raw_payload = self._merge_handoff_payload(binding.raw_payload or {}, handoff_payload)
        binding.candidate.raw_payload = self._merge_handoff_payload(binding.candidate.raw_payload or {}, handoff_payload)
        record.raw_payload = {
            **(record.raw_payload or {}),
            "path_handoff": handoff_payload,
        }
        record.updated_at = now

    @staticmethod
    def _merge_handoff_payload(raw_payload: dict, handoff_payload: dict) -> dict:
        merged = {**raw_payload, "path_handoff": handoff_payload}
        source_path = handoff_payload.get("source_path")
        if source_path:
            source_name = handoff_payload.get("source_name") or source_path.rsplit("/", 1)[-1]
            source_basename = handoff_payload.get("source_basename") or source_name.rsplit(".", 1)[0]
            source_extension = handoff_payload.get("source_extension") or (
                f".{source_name.rsplit('.', 1)[-1]}" if "." in source_name else ""
            )
            merged["host_transfer_source_path"] = source_path
            merged["host_transfer_filetype"] = handoff_payload.get("source_filetype") or "file"
            merged["host_transfer_source"] = {
                "storage": "local",
                "path": source_path,
                "type": handoff_payload.get("source_filetype") or "file",
                "name": source_name,
                "basename": source_basename,
                "extension": source_extension,
            }
        else:
            merged.pop("host_transfer_source_path", None)
            merged.pop("host_transfer_filetype", None)
            merged.pop("host_transfer_source", None)
        return merged

    def _apply_result_to_record(self, *, record, applied, now: datetime) -> None:
        record.organizeable = applied.organizeable
        record.organize_backend = applied.organize_backend.value
        record.organize_status = applied.organize_status.value
        record.target_library_path = applied.target_library_path
        record.target_relative_path = applied.target_relative_path
        record.strategy = applied.strategy
        record.strategy_note = applied.strategy_note
        record.integration_point = applied.integration_point
        record.capability_source = applied.capability_source
        record.fallback_reason = applied.fallback_reason
        record.failure_reason = applied.failure_reason
        record.verification_state = applied.verification_state.value
        record.mock = applied.mock
        record.note = applied.note
        record.raw_payload = applied.model_dump(mode="json")
        record.updated_at = now

    def _mark_record_handoff_unresolved(self, *, record, handoff: PathHandoffInfo, now: datetime) -> None:
        raw_payload = dict(record.raw_payload or {})
        raw_payload["path_handoff"] = handoff.model_dump(mode="json")
        record.organize_status = OrganizeStatus.FAILED.value
        record.failure_reason = (
            "Pending host path handoff did not resolve before "
            f"{self.handoff_pending_ttl_seconds}s TTL expired."
        )
        record.note = "automatic path handoff retry timed out; organize apply stopped"
        record.raw_payload = raw_payload
        record.updated_at = now

    def _mark_apply_failed(self, *, record, handoff: PathHandoffInfo, error_message: str, now: datetime) -> None:
        raw_payload = dict(record.raw_payload or {})
        raw_payload["path_handoff"] = handoff.model_dump(mode="json")
        raw_payload["error_message"] = error_message
        record.organize_status = OrganizeStatus.FAILED.value
        record.failure_reason = error_message
        record.note = "automatic path handoff resolved but organize apply failed"
        record.raw_payload = raw_payload
        record.updated_at = now

    def _update_run_after_apply(self, *, record, organize_status: OrganizeStatus, handoff: PathHandoffInfo, now: datetime) -> None:
        if not record.subscription_run_id:
            return
        run = self.repository.get_run(record.subscription_run_id)
        if run is None:
            return
        summary = dict(run.summary_json or {})
        summary.update(
            {
                "organize_preview_id": record.id,
                "organize_status": organize_status.value,
                "path_handoff_status": handoff.handoff_status,
                "path_handoff_source": handoff.handoff_source,
                "resolved_source_path": handoff.source_path,
            }
        )
        next_status = (
            SubscriptionRunStatus.APPLIED.value
            if organize_status in {OrganizeStatus.APPLIED, OrganizeStatus.FALLBACK_APPLIED}
            else run.execution_status
        )
        self.repository.mark_run_finished(
            run,
            execution_status=next_status,
            matched_candidates_count=run.matched_candidates_count,
            summary_json=summary,
            search_job_id=run.search_job_id,
            organize_record_id=record.id,
            error_message=run.error_message,
        )
        run.updated_at = now

    def _update_run_handoff_status(self, *, record, handoff: PathHandoffInfo, now: datetime) -> None:
        if not record.subscription_run_id:
            return
        run = self.repository.get_run(record.subscription_run_id)
        if run is None:
            return
        summary = dict(run.summary_json or {})
        summary.update(
            {
                "organize_preview_id": record.id,
                "organize_status": OrganizeStatus.FAILED.value,
                "path_handoff_status": handoff.handoff_status,
                "path_handoff_source": handoff.handoff_source,
                "error_message": "path handoff unresolved after pending TTL",
            }
        )
        run.summary_json = summary
        run.updated_at = now

    def _update_run_apply_failed(self, *, record, handoff: PathHandoffInfo, error_message: str, now: datetime) -> None:
        if not record.subscription_run_id:
            return
        run = self.repository.get_run(record.subscription_run_id)
        if run is None:
            return
        summary = dict(run.summary_json or {})
        summary.update(
            {
                "organize_preview_id": record.id,
                "organize_status": OrganizeStatus.FAILED.value,
                "path_handoff_status": handoff.handoff_status,
                "path_handoff_source": handoff.handoff_source,
                "error_message": error_message,
            }
        )
        self.repository.mark_run_finished(
            run,
            execution_status=SubscriptionRunStatus.FAILED.value,
            matched_candidates_count=run.matched_candidates_count,
            summary_json=summary,
            search_job_id=run.search_job_id,
            organize_record_id=record.id,
            error_message=error_message,
        )
        run.updated_at = now

    @staticmethod
    def _record_age_seconds(*, record, now: datetime) -> int:
        baseline = getattr(record, "updated_at", None) or getattr(record, "created_at", None) or now
        normalized = baseline if baseline.tzinfo is not None else baseline.replace(tzinfo=timezone.utc)
        current = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        return max(0, int((current - normalized).total_seconds()))

    def _is_stale(self, *, binding, now: datetime) -> bool:
        baseline = getattr(binding, "dispatched_at", None) or getattr(binding, "updated_at", None) or now
        normalized = baseline if baseline.tzinfo is not None else baseline.replace(tzinfo=timezone.utc)
        current = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        return (current - normalized).total_seconds() >= self.handoff_pending_ttl_seconds

    def _has_source_payload(self, payload: dict) -> bool:
        return bool(
            payload.get("host_transfer_source_path")
            or payload.get("host_transfer_source")
            or payload.get("source_fileitem")
        )

    def _handoff_ready(self, *, preview: OrganizePreviewResult, binding) -> bool:
        if preview.path_handoff and preview.path_handoff.source_path:
            return True
        binding_payload = dict(binding.raw_payload or {})
        if self._has_source_payload(binding_payload):
            return True
        path_handoff = binding_payload.get("path_handoff")
        if isinstance(path_handoff, dict) and path_handoff.get("source_path"):
            return True
        return False

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

        if self._skip_host_handoff_lookup(binding_payload=binding_payload):
            return payload

        resolved = self.path_handoff_service.resolve_from_download_with_retry(str(download_hash))
        if resolved is None:
            if binding_model is not None and self._binding_handoff_stale(binding_model):
                payload["path_handoff"] = self.path_handoff_service.build_unresolved(
                    download_hash=str(download_hash),
                    handoff_source="moviepilot.runtime.history.download",
                ).model_dump(mode="json")
            elif binding_model is not None:
                payload["path_handoff"] = self.path_handoff_service.build_pending(
                    download_hash=str(download_hash),
                    handoff_source="moviepilot.runtime.history.download",
                ).model_dump(mode="json")
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

    def _skip_host_handoff_lookup(self, *, binding_payload: dict) -> bool:
        if not self.strategy_service.settings.host_integration_enabled:
            return True
        if not self.strategy_service.settings.host_base_url:
            return True

        dispatch_backend = binding_payload.get("dispatch_backend")
        if isinstance(dispatch_backend, str) and dispatch_backend.lower() == "mock":
            return True

        adapter_resolution = binding_payload.get("adapter_resolution")
        if isinstance(adapter_resolution, dict):
            adapter_mode = adapter_resolution.get("adapter_mode")
            if isinstance(adapter_mode, str) and adapter_mode.lower() == "mock":
                return True

        return False

    def _binding_handoff_stale(self, binding_model) -> bool:
        if binding_model is None or binding_model.dispatched_at is None:
            return False
        dispatched_at = binding_model.dispatched_at
        if dispatched_at.tzinfo is None:
            dispatched_at = dispatched_at.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - dispatched_at).total_seconds()
        return age_seconds >= self.strategy_service.settings.host_handoff_pending_ttl_seconds

    def _resolve_binding_downloader(self, *, binding_payload: dict, binding_model) -> str | None:
        if binding_payload.get("target_downloader"):
            return str(binding_payload["target_downloader"])
        if binding_model is not None and binding_model.target_downloader:
            return str(binding_model.target_downloader)
        return None


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
        music_media_input=_parse_optional_music_media_input(record.music_media_input),
        music_meta_base=_parse_optional_music_meta_base(record.music_meta_base),
        music_recognition_assessment=_parse_optional_music_recognition_assessment(
            record.music_recognition_assessment
        ),
        music_media_info=_parse_optional_music_media_info(record.music_media_info),
        mock=record.mock,
        note=record.note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _extract_candidate_path_handoff(payload: dict) -> PathHandoffInfo | None:
    handoff = payload.get("path_handoff")
    if not handoff:
        return None
    return PathHandoffInfo.model_validate(handoff)


def _parse_optional_music_media_input(payload: dict | None) -> MusicMediaInput | None:
    if not payload:
        return None
    return MusicMediaInput.model_validate(payload)


def _parse_optional_music_meta_base(payload: dict | None) -> MusicMetaBase | None:
    if not payload:
        return None
    return MusicMetaBase.model_validate(payload)


def _parse_optional_music_recognition_assessment(
    payload: dict | None,
) -> MusicRecognitionAssessment | None:
    if not payload:
        return None
    return MusicRecognitionAssessment.model_validate(payload)


def _parse_optional_music_media_info(payload: dict | None) -> MusicMediaInfo | None:
    if not payload:
        return None
    return MusicMediaInfo.model_validate(payload)
