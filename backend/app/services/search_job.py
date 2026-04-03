"""Search job orchestration for Phase 5 host-aware acquisition."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.acquisition import SearchCandidateModel, SearchJobModel
from ..repositories.acquisition import AcquisitionRepository
from ..schemas.acquisition import (
    PathHandoffInfo,
    QueryBuildRequest,
    QueryBuildResult,
    SearchCandidateDetail,
    SearchCandidateListData,
    SearchJobCreateRequest,
    SearchJobSummary,
)
from ..schemas.integration import AdapterMode, AdapterResolution
from ..schemas.metadata import MetadataDetail
from ..schemas.mvp import DecisionStatus, EntityType, JobStatus, TriggerSource
from .host_integration import HostSearchAdapterResolver
from .metadata import MetadataService
from .query_builder import QueryBuilderService
from .scoring import MusicCandidateScorer


JOB_NOTE = (
    "SearchJob 现在通过 host-aware resolver 选择 search adapter。"
    "当宿主能力存在时可走 host-backed 骨架；当能力缺失或不稳定时会按策略降级回 mock。"
)


class SearchJobService:
    def __init__(
        self,
        session: Session,
        *,
        metadata_service: MetadataService,
        query_builder: QueryBuilderService,
        host_search_resolver: HostSearchAdapterResolver,
        scorer: MusicCandidateScorer,
    ):
        self.session = session
        self.metadata_service = metadata_service
        self.query_builder = query_builder
        self.host_search_resolver = host_search_resolver
        self.scorer = scorer
        self.repository = AcquisitionRepository(session)

    def create_job(self, payload: SearchJobCreateRequest) -> SearchJobSummary:
        metadata_detail = self.metadata_service.get_detail(payload.query_source_type, payload.query_source_id)
        query_build = self.query_builder.build(
            QueryBuildRequest(
                query_source_type=payload.query_source_type,
                query_source_id=payload.query_source_id,
                preferences=payload.preferences,
            )
        )
        job = self.repository.create_job(
            payload=payload,
            query_payload=query_build.model_dump(mode="json"),
            metadata_snapshot=metadata_detail.model_dump(mode="json"),
            note=JOB_NOTE,
        )
        self.session.commit()
        self.session.refresh(job)
        return serialize_job(job)

    def list_jobs(self) -> list[SearchJobSummary]:
        return [serialize_job(job) for job in self.repository.list_jobs()]

    def get_job(self, job_id: str) -> SearchJobSummary:
        job = self.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")
        return serialize_job(job)

    def execute_job(self, job_id: str) -> SearchJobSummary:
        job = self.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")

        metadata_detail = MetadataDetail.model_validate(job.metadata_snapshot)
        query_build = QueryBuildResult.model_validate(job.query_payload)
        preferences = query_build.preferences

        self.repository.mark_job_running(job)
        self.repository.reset_job_candidates(job)
        self.session.flush()

        try:
            search_execution = self.host_search_resolver.search(query_build=query_build, detail=metadata_detail)
            raw_candidates = search_execution.candidates
            persisted_candidates: list[SearchCandidateModel] = []

            for raw_candidate in raw_candidates:
                score = self.scorer.score(
                    detail=metadata_detail,
                    query_build=query_build,
                    candidate=raw_candidate,
                    preferences=preferences,
                )
                persisted_candidates.append(
                    self.repository.add_candidate(
                        job=job,
                        raw_candidate=raw_candidate,
                        score=score,
                    )
                )

            if not persisted_candidates:
                status = JobStatus.NO_RESULT.value
                recommendation = "no_result"
            elif any(candidate.decision == DecisionStatus.AUTO_DOWNLOAD.value for candidate in persisted_candidates):
                status = JobStatus.MATCHED.value
                recommendation = "auto_ready"
            elif any(candidate.decision == DecisionStatus.MANUAL_CONFIRM.value for candidate in persisted_candidates):
                status = JobStatus.MANUAL_PENDING.value
                recommendation = "manual_review"
            else:
                status = JobStatus.MATCHED.value
                recommendation = "review_rejected"

            effective_resolution = (
                raw_candidates[0].adapter_resolution
                if raw_candidates and raw_candidates[0].adapter_resolution is not None
                else search_execution.resolution
            )
            summary = {
                "candidate_count": len(persisted_candidates),
                "dispatch_recommendation": recommendation,
                "best_score": max((candidate.score_total for candidate in persisted_candidates), default=0.0),
                "mock_host_search": effective_resolution.adapter_mode == AdapterMode.MOCK,
                "adapter_resolution": effective_resolution.model_dump(mode="json"),
                "active_search_adapter": effective_resolution.adapter_key,
            }
            job.mock = effective_resolution.adapter_mode == AdapterMode.MOCK
            self.repository.mark_job_finished(job, status=status, summary_json=summary)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_job = self.repository.get_job(job_id)
            if failed_job is not None:
                self.repository.mark_job_finished(
                    failed_job,
                    status=JobStatus.FAILED.value,
                    summary_json={"candidate_count": 0, "dispatch_recommendation": "failed"},
                    error_message=str(exc),
                )
                self.session.commit()
            raise

        self.session.refresh(job)
        return serialize_job(job)

    def list_candidates(self, job_id: str) -> SearchCandidateListData:
        job = self.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} was not found.")

        items = [serialize_candidate(candidate) for candidate in self.repository.list_candidates(job_id)]
        return SearchCandidateListData(
            job_id=job_id,
            items=items,
            total=len(items),
            mock=_is_mock_resolution(_extract_resolution(job.summary_json or {})),
            note="当前候选列表会显示 search adapter mode、capability source 和 fallback reason。",
            adapter_resolution=_extract_resolution(job.summary_json or {}),
        )


def serialize_job(job: SearchJobModel) -> SearchJobSummary:
    return SearchJobSummary(
        id=job.id,
        query_source_type=EntityType(job.query_source_type),
        query_source_id=job.query_source_id,
        trigger_source=TriggerSource(job.trigger_source),
        profile_id=job.profile_id,
        strategy=job.strategy,
        mode=job.mode,
        status=JobStatus(job.status),
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        mock=job.mock,
        note=job.note,
        query_build=QueryBuildResult.model_validate(job.query_payload) if job.query_payload else None,
        metadata_snapshot=MetadataDetail.model_validate(job.metadata_snapshot) if job.metadata_snapshot else None,
        summary=job.summary_json or {},
        error_message=job.error_message,
        adapter_resolution=_extract_resolution(job.summary_json or {}),
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
    return AdapterResolution.model_validate(resolution)


def _is_mock_resolution(resolution: AdapterResolution | None) -> bool:
    if resolution is None:
        return True
    return resolution.adapter_mode == AdapterMode.MOCK


def _extract_path_handoff(payload: dict) -> PathHandoffInfo | None:
    handoff = payload.get("path_handoff")
    if not handoff:
        return None
    return PathHandoffInfo.model_validate(handoff)
