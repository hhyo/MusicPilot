"""Search job orchestration for Phase 3."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..adapters.host_search import HostSearchAdapter
from ..models.acquisition import SearchCandidateModel, SearchJobModel
from ..repositories.acquisition import AcquisitionRepository
from ..schemas.acquisition import (
    QueryBuildRequest,
    QueryBuildResult,
    SearchCandidateDetail,
    SearchCandidateListData,
    SearchJobCreateRequest,
    SearchJobSummary,
)
from ..schemas.metadata import MetadataDetail
from ..schemas.mvp import DecisionStatus, EntityType, JobStatus, TriggerSource
from .metadata import MetadataService
from .query_builder import QueryBuilderService
from .scoring import MusicCandidateScorer


JOB_NOTE = "当前 SearchJob 调用 mock host search adapter，同步执行一次最小链路，不代表已接入真实 PT 搜索。"


class SearchJobService:
    def __init__(
        self,
        session: Session,
        *,
        metadata_service: MetadataService,
        query_builder: QueryBuilderService,
        host_search_adapter: HostSearchAdapter,
        scorer: MusicCandidateScorer,
    ):
        self.session = session
        self.metadata_service = metadata_service
        self.query_builder = query_builder
        self.host_search_adapter = host_search_adapter
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
            raw_candidates = self.host_search_adapter.search(query_build=query_build, detail=metadata_detail)
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

            summary = {
                "candidate_count": len(persisted_candidates),
                "dispatch_recommendation": recommendation,
                "best_score": max((candidate.score_total for candidate in persisted_candidates), default=0.0),
                "mock_host_search": True,
            }
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
            mock=True,
            note="当前候选列表来自 mock host search + mock scorer，用于验证人工确认与派发边界。",
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
    )


def serialize_candidate(candidate: SearchCandidateModel) -> SearchCandidateDetail:
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
    )
