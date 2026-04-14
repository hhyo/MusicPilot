"""MoviePilot-aligned music search chain."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from . import MusicChainBase
from ..db.acquisition_oper import AcquisitionOper
from ..db.models.acquisition import SearchCandidateModel, SearchJobModel
from ..schemas.acquisition import (
    DispatchRequest,
    MutationResult,
    PathHandoffInfo,
    QueryBuildRequest,
    QueryBuildResult,
    SearchCandidateActionResult,
    SearchCandidateConfirmRequest,
    SearchCandidateDetail,
    SearchCandidateListData,
    SearchCandidateRejectRequest,
    SearchJobCreateRequest,
    SearchJobSummary,
)
from ..schemas.integration import AdapterMode, AdapterResolution
from ..schemas.music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMetaBase,
    MusicRecognitionAssessment,
    MusicRecognitionState,
)
from ..schemas.shared import DecisionStatus, JobStatus, TriggerSource
from ..helper.query_builder import MusicQueryBuilder


JOB_NOTE = (
    "SearchJob 现在通过 host-aware resolver 选择 search adapter。"
    "执行阶段只暴露真实采用的 search 语义和 adapter。"
)


class MusicSearchChain(MusicChainBase):
    def __init__(
        self,
        session,
        *,
        query_builder: MusicQueryBuilder,
        music_media_chain,
        host_search_resolver,
        scorer,
        dispatch_service=None,
    ) -> None:
        super().__init__(cache_region="music_search_chain")
        self.session = session
        self.query_builder = query_builder
        self.music_media_chain = music_media_chain
        self.host_search_resolver = host_search_resolver
        self.scorer = scorer
        self.dispatch_service = dispatch_service
        self.oper = AcquisitionOper(session)

    def build_query(self, payload: QueryBuildRequest) -> QueryBuildResult:
        return self.query_builder.build(payload)

    def create_job(self, payload: SearchJobCreateRequest) -> SearchJobSummary:
        resolved = self.music_media_chain.resolve_response(payload.input)
        music_meta_base = resolved.base
        music_media_info = resolved.media
        query_build = self.query_builder.build_from_music_media_info(
            music_media_info,
            payload.preferences,
        )
        job = self.oper.create_job(
            payload=payload,
            music_media_input=payload.input.model_dump(mode="json"),
            music_meta_base=music_meta_base.model_dump(mode="json"),
            music_recognition_assessment=resolved.assessment.model_dump(mode="json"),
            music_media_info=music_media_info.model_dump(mode="json"),
            query_payload=query_build.model_dump(mode="json"),
            note=JOB_NOTE,
        )
        self.session.commit()
        self.session.refresh(job)
        return serialize_job(job)

    def list_jobs(
        self,
        *,
        status: str | None = None,
        trigger_source: str | None = None,
        decision: str | None = None,
        has_dispatch: bool | None = None,
    ) -> list[SearchJobSummary]:
        return [
            serialize_job(job)
            for job in self.oper.list_jobs(
                status=status,
                trigger_source=trigger_source,
                decision=decision,
                has_dispatch=has_dispatch,
            )
        ]

    def get_job(self, job_id: str) -> SearchJobSummary:
        job = self.oper.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")
        return serialize_job(job)

    def execute_job(self, job_id: str) -> SearchJobSummary:
        job = self.oper.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")

        media_info = MusicMediaInfo.model_validate(job.music_media_info)
        query_build = QueryBuildResult.model_validate(job.query_payload)
        preferences = query_build.preferences

        self.oper.mark_job_running(job)
        self.oper.reset_job_candidates(job)
        self.session.flush()

        try:
            search_execution = self.host_search_resolver.search(query_build=query_build, media=media_info)
            raw_candidates = search_execution.candidates
            persisted_candidates: list[SearchCandidateModel] = []

            for raw_candidate in raw_candidates:
                score = self.scorer.score(
                    media=media_info,
                    query_build=query_build,
                    candidate=raw_candidate,
                    preferences=preferences,
                )
                persisted_candidates.append(
                    self.oper.add_candidate(
                        job=job,
                        raw_candidate=raw_candidate,
                        score=score,
                    )
                )

            if not persisted_candidates:
                status = JobStatus.NO_RESULT.value
            elif any(candidate.decision == DecisionStatus.MANUAL_CONFIRM.value for candidate in persisted_candidates):
                status = JobStatus.MANUAL_PENDING.value
            else:
                status = JobStatus.MATCHED.value

            effective_resolution = (
                raw_candidates[0].adapter_resolution
                if raw_candidates and raw_candidates[0].adapter_resolution is not None
                else search_execution.resolution
            )
            summary = {
                "candidate_count": len(persisted_candidates),
                "best_score": max((candidate.score_total for candidate in persisted_candidates), default=0.0),
                "mock_host_search": effective_resolution.adapter_mode == AdapterMode.MOCK,
                "adapter_resolution": effective_resolution.model_dump(mode="json"),
                "active_search_adapter": effective_resolution.adapter_key,
            }
            job.mock = effective_resolution.adapter_mode == AdapterMode.MOCK
            self.oper.mark_job_finished(job, status=status, summary_json=summary)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_job = self.oper.get_job(job_id)
            if failed_job is not None:
                self.oper.mark_job_finished(
                    failed_job,
                    status=JobStatus.FAILED.value,
                    summary_json={"candidate_count": 0},
                    error_message=str(exc),
                )
                self.session.commit()
            raise

        self.session.refresh(job)
        return serialize_job(job)

    def retry_job(self, job_id: str) -> SearchJobSummary:
        return self.execute_job(job_id)

    def cancel_job(self, job_id: str) -> SearchJobSummary:
        job = self.oper.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")
        if job.status not in {JobStatus.QUEUED.value, JobStatus.RUNNING.value}:
            raise HTTPException(status_code=409, detail=f"Job {job_id} is not cancellable from status {job.status}.")
        self.oper.mark_job_finished(
            job,
            status=JobStatus.CANCELLED.value,
            summary_json={**(job.summary_json or {}), "cancelled": True},
            error_message=None,
        )
        self.session.commit()
        self.session.refresh(job)
        return serialize_job(job)

    def delete_job(self, job_id: str) -> MutationResult:
        deleted = self.oper.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")
        self.session.commit()
        return MutationResult(id=job_id, deleted=True)

    def confirm_candidate(
        self,
        job_id: str,
        candidate_id: str,
        payload: SearchCandidateConfirmRequest,
    ) -> SearchCandidateActionResult:
        job = self.oper.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")
        candidate = self.oper.get_candidate(candidate_id)
        if candidate is None or candidate.job_id != job_id:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} was not found for job {job_id}.")
        if not candidate.dispatchable:
            raise HTTPException(status_code=409, detail=f"Candidate {candidate_id} is not dispatchable.")
        if self.dispatch_service is None:
            raise HTTPException(status_code=500, detail="Dispatch service is not configured for candidate confirmation.")

        reason_codes = list(candidate.reason_codes or [])
        if payload.reason:
            reason_codes.append(payload.reason)
        self.oper.update_candidate_decision(
            candidate,
            decision=DecisionStatus.AUTO_DOWNLOAD.value,
            reason_codes=reason_codes,
            dispatch_status="confirming",
            note="candidate confirmed for dispatch",
        )
        self.session.flush()

        dispatch_result = self.dispatch_service.dispatch(
            DispatchRequest(
                result_id=candidate.id,
                downloader_id=payload.downloader_id,
                save_path_policy=payload.save_path_policy,
                manual_confirm=payload.manual_confirm,
            )
        )
        self.session.refresh(job)
        binding = self.oper.get_binding(dispatch_result.binding_id) if dispatch_result.binding_id else None
        return SearchCandidateActionResult(
            job=serialize_job(job),
            candidate=serialize_candidate(candidate),
            binding=DownloadsWorkspaceBridge.serialize_binding(binding, include_candidate=False) if binding else None,
            note="Candidate confirmed and dispatched.",
        )

    def reject_candidate(
        self,
        job_id: str,
        candidate_id: str,
        payload: SearchCandidateRejectRequest,
    ) -> SearchCandidateActionResult:
        job = self.oper.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")
        candidate = self.oper.get_candidate(candidate_id)
        if candidate is None or candidate.job_id != job_id:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} was not found for job {job_id}.")
        if candidate.dispatch_status not in {"pending", "rejected"}:
            raise HTTPException(status_code=409, detail=f"Candidate {candidate_id} can no longer be rejected.")

        self.oper.update_candidate_decision(
            candidate,
            decision=DecisionStatus.REJECT.value,
            reason_codes=list(dict.fromkeys([*(candidate.reason_codes or []), payload.reason])),
            dispatchable=False,
            dispatch_status="rejected",
            note="candidate rejected by operator",
        )
        job.status = self._infer_job_status(job).value
        self.session.commit()
        self.session.refresh(job)
        self.session.refresh(candidate)
        return SearchCandidateActionResult(
            job=serialize_job(job),
            candidate=serialize_candidate(candidate),
            binding=None,
            note="Candidate rejected.",
        )

    def list_candidates(self, job_id: str) -> SearchCandidateListData:
        job = self.oper.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")

        items = [serialize_candidate(candidate) for candidate in self.oper.list_candidates(job_id)]
        return SearchCandidateListData(
            job_id=job_id,
            items=items,
            total=len(items),
            mock=_is_mock_resolution(_extract_resolution(job.summary_json or {})),
            note="当前候选列表会显示 search adapter、capability source、path handoff 与 fallback reason。",
            adapter_resolution=_extract_resolution(job.summary_json or {}),
        )

    def _infer_job_status(self, job: SearchJobModel) -> JobStatus:
        if job.bindings:
            return JobStatus.DISPATCHED
        decisions = {candidate.decision for candidate in job.candidates}
        if not decisions or decisions == {DecisionStatus.REJECT.value}:
            return JobStatus.NO_RESULT
        if DecisionStatus.MANUAL_CONFIRM.value in decisions or DecisionStatus.PENDING.value in decisions:
            return JobStatus.MANUAL_PENDING
        return JobStatus.MATCHED


class DownloadsWorkspaceBridge:
    @staticmethod
    def serialize_binding(binding, *, include_candidate: bool = False):
        from .download import MusicDownloadChain

        return MusicDownloadChain.serialize_binding_static(binding, include_candidate=include_candidate)


def serialize_job(job: SearchJobModel) -> SearchJobSummary:
    decision_counts: dict[str, int] = {}
    handoff_status_counts: dict[str, int] = {}
    active_download_task_ids: list[str] = []

    for candidate in job.candidates:
        decision_counts[candidate.decision] = decision_counts.get(candidate.decision, 0) + 1

    for binding in job.bindings:
        if binding.downloader_task_id and binding.downloader_task_id not in active_download_task_ids:
            active_download_task_ids.append(binding.downloader_task_id)
        path_handoff = _extract_path_handoff(binding.raw_payload or {})
        if path_handoff is not None:
            handoff_status_counts[path_handoff.handoff_status] = handoff_status_counts.get(path_handoff.handoff_status, 0) + 1

    summary = job.summary_json or {}
    return SearchJobSummary(
        id=job.id,
        music_media_input=MusicMediaInput.model_validate(job.music_media_input),
        music_meta_base=MusicMetaBase.model_validate(job.music_meta_base),
        music_recognition_assessment=MusicRecognitionAssessment.model_validate(
            job.music_recognition_assessment or {"state": MusicRecognitionState.INSUFFICIENT.value}
        ),
        music_media_info=MusicMediaInfo.model_validate(job.music_media_info),
        trigger_source=TriggerSource(job.trigger_source),
        profile_id=job.profile_id,
        mode=job.mode,
        status=JobStatus(job.status),
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        mock=job.mock,
        note=job.note,
        query_build=QueryBuildResult.model_validate(job.query_payload) if job.query_payload else None,
        summary=summary,
        candidate_decision_counts=decision_counts,
        binding_count=len(job.bindings),
        active_download_task_ids=active_download_task_ids,
        handoff_status_counts=handoff_status_counts,
        query_trace=dict(summary.get("query_trace") or {}),
        error_message=job.error_message,
        adapter_resolution=_extract_resolution(summary),
    )


def serialize_candidate(candidate: SearchCandidateModel) -> SearchCandidateDetail:
    raw_payload = candidate.raw_payload or {}
    return SearchCandidateDetail(
        id=candidate.id,
        job_id=candidate.job_id,
        site_id=candidate.site_id,
        site_name=candidate.site_name,
        title=candidate.title,
        normalized_title=candidate.normalized_title,
        size_bytes=candidate.size_bytes,
        seeders=candidate.seeders,
        peers=candidate.peers,
        format_tag=candidate.format_tag,
        bitrate_kbps=candidate.bitrate_kbps,
        source_tags=list(candidate.source_tags or []),
        raw_score=candidate.raw_score,
        score_total=candidate.score_total,
        score_breakdown=candidate.score_breakdown or {},
        decision=DecisionStatus(candidate.decision),
        reason_codes=list(candidate.reason_codes or []),
        dispatchable=candidate.dispatchable,
        dispatch_status=candidate.dispatch_status,
        mock=candidate.mock,
        note=candidate.note,
        created_at=candidate.created_at,
        adapter_resolution=_extract_resolution(raw_payload),
        path_handoff=_extract_path_handoff(raw_payload),
        raw_payload=raw_payload,
    )


def _extract_resolution(payload: dict) -> AdapterResolution | None:
    resolution = payload.get("adapter_resolution")
    if not resolution:
        return None
    try:
        return AdapterResolution.model_validate(resolution)
    except Exception:  # noqa: BLE001
        return None


def _is_mock_resolution(resolution: AdapterResolution | None) -> bool:
    if resolution is None:
        return True
    return resolution.adapter_mode == AdapterMode.MOCK


def _extract_path_handoff(payload: dict) -> PathHandoffInfo | None:
    handoff = payload.get("path_handoff")
    if not handoff:
        return None
    return PathHandoffInfo.model_validate(handoff)
