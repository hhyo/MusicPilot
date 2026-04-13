"""Background reconciliation for dispatched runs waiting on history-based handoff."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..repositories.acquisition import AcquisitionRepository
from ..repositories.orchestration import OrchestrationRepository
from ..schemas.acquisition import PathHandoffInfo
from ..schemas.orchestration import OrganizeApplyRequest, OrganizeStatus, SubscriptionRunStatus
from ..schemas.orchestration import (
    PendingHandoffDiagnostic,
    PendingHandoffReconcileResult,
    PendingHandoffSummary,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PendingHandoffReconcileService:
    def __init__(
        self,
        *,
        session: Session,
        organize_service,
        path_handoff_service,
        handoff_pending_ttl_seconds: int,
    ) -> None:
        self.session = session
        self.organize_service = organize_service
        self.path_handoff_service = path_handoff_service
        self.handoff_pending_ttl_seconds = handoff_pending_ttl_seconds
        self.acquisition_repository = AcquisitionRepository(session)
        self.orchestration_repository = OrchestrationRepository(session)

    def reconcile_pending_once(self, *, now: datetime | None = None) -> dict[str, Any]:
        current_time = now or utc_now()
        applied_run_ids: list[str] = []
        unresolved_run_ids: list[str] = []
        skipped_record_ids: list[str] = []
        diagnostics: list[PendingHandoffDiagnostic] = []
        summary = PendingHandoffSummary()

        for record in self.orchestration_repository.list_pending_handoff_records():
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
                    applied = self.organize_service.apply(OrganizeApplyRequest(organize_job_id=record.id))
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
                    self._update_run_apply_failed(record=record, handoff=resolved, error_message=str(exc), now=current_time)
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
                self._update_run_handoff_status(
                    record=record,
                    handoff=unresolved,
                    now=current_time,
                )
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

    def _store_handoff_state(self, *, record, binding, handoff: PathHandoffInfo, now: datetime) -> None:
        handoff_payload = handoff.model_dump(mode="json")
        binding.raw_payload = self._merge_payload(binding.raw_payload or {}, handoff_payload)
        binding.candidate.raw_payload = self._merge_payload(binding.candidate.raw_payload or {}, handoff_payload)
        record.raw_payload = {
            **(record.raw_payload or {}),
            "path_handoff": handoff_payload,
        }
        record.updated_at = now

    def _merge_payload(self, raw_payload: dict[str, Any], handoff_payload: dict[str, Any]) -> dict[str, Any]:
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

        run = self.orchestration_repository.get_run(record.subscription_run_id)
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
        self.orchestration_repository.mark_run_finished(
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

        run = self.orchestration_repository.get_run(record.subscription_run_id)
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

        run = self.orchestration_repository.get_run(record.subscription_run_id)
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
        self.orchestration_repository.mark_run_finished(
            run,
            execution_status=SubscriptionRunStatus.FAILED.value,
            matched_candidates_count=run.matched_candidates_count,
            summary_json=summary,
            search_job_id=run.search_job_id,
            organize_record_id=record.id,
            error_message=error_message,
        )
        run.updated_at = now

    def _is_stale(self, *, binding, now: datetime) -> bool:
        dispatched_at = getattr(binding, "dispatched_at", None)
        if dispatched_at is None:
            return False
        if dispatched_at.tzinfo is None:
            dispatched_at = dispatched_at.replace(tzinfo=timezone.utc)
        return (now - dispatched_at).total_seconds() >= self.handoff_pending_ttl_seconds

    def _record_age_seconds(self, *, record, now: datetime) -> int:
        baseline = getattr(record, "updated_at", None) or getattr(record, "created_at", None) or now
        if baseline.tzinfo is None:
            baseline = baseline.replace(tzinfo=timezone.utc)
        return max(0, int((now - baseline).total_seconds()))
