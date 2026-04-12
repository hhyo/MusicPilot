"""Repository layer for Phase 3 acquisition data."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from ..models.acquisition import DownloadBindingModel, SearchCandidateModel, SearchJobModel
from ..schemas.acquisition import CandidateScoreResult, DispatchAdapterResult, HostSearchCandidate, SearchJobCreateRequest


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AcquisitionRepository:
    def __init__(self, session: Session):
        self.session = session

    def clear_all(self) -> None:
        self.session.execute(delete(DownloadBindingModel))
        self.session.execute(delete(SearchCandidateModel))
        self.session.execute(delete(SearchJobModel))

    def create_job(
        self,
        *,
        payload: SearchJobCreateRequest,
        music_media_input: dict,
        music_media_info: dict,
        query_payload: dict,
        note: str,
    ) -> SearchJobModel:
        job = SearchJobModel(
            id=f"job-{uuid4().hex[:12]}",
            trigger_source=payload.trigger_source.value,
            profile_id=payload.profile_id,
            mode=payload.mode,
            status="queued",
            music_media_input=music_media_input,
            music_media_info=music_media_info,
            query_payload=query_payload,
            note=note,
            mock=True,
            summary_json={
                "candidate_count": 0,
                "execution_mode": payload.mode,
            },
        )
        self.session.add(job)
        return job

    def list_jobs(self) -> list[SearchJobModel]:
        statement = select(SearchJobModel).order_by(SearchJobModel.created_at.desc())
        return list(self.session.scalars(statement).all())

    def get_job(self, job_id: str) -> SearchJobModel | None:
        statement = (
            select(SearchJobModel)
            .options(
                selectinload(SearchJobModel.candidates),
                selectinload(SearchJobModel.bindings),
            )
            .where(SearchJobModel.id == job_id)
        )
        return self.session.scalar(statement)

    def mark_job_running(self, job: SearchJobModel) -> None:
        job.status = "running"
        job.started_at = utc_now()
        job.error_message = None

    def mark_job_finished(
        self,
        job: SearchJobModel,
        *,
        status: str,
        summary_json: dict,
        error_message: str | None = None,
    ) -> None:
        job.status = status
        job.summary_json = summary_json
        job.error_message = error_message
        job.finished_at = utc_now()

    def reset_job_candidates(self, job: SearchJobModel) -> None:
        self.session.execute(delete(DownloadBindingModel).where(DownloadBindingModel.job_id == job.id))
        self.session.execute(delete(SearchCandidateModel).where(SearchCandidateModel.job_id == job.id))

    def add_candidate(
        self,
        *,
        job: SearchJobModel,
        raw_candidate: HostSearchCandidate,
        score: CandidateScoreResult,
    ) -> SearchCandidateModel:
        candidate = SearchCandidateModel(
            id=f"cand-{uuid4().hex[:12]}",
            job_id=job.id,
            site_id=raw_candidate.site_id,
            site_name=raw_candidate.site_name,
            title=raw_candidate.title,
            normalized_title=raw_candidate.normalized_title,
            size_bytes=raw_candidate.size_bytes,
            seeders=raw_candidate.seeders,
            peers=raw_candidate.peers,
            format_tag=raw_candidate.format_tag,
            bitrate_kbps=raw_candidate.bitrate_kbps,
            source_tags=raw_candidate.source_tags,
            raw_score=score.raw_score,
            score_total=score.score_total,
            score_breakdown={
                key: value.model_dump(mode="json") for key, value in score.score_breakdown.items()
            },
            decision=score.decision.value,
            reason_codes=score.reason_codes,
            dispatch_status="pending",
            dispatchable=score.dispatchable,
            raw_payload=raw_candidate.raw_payload,
            mock=raw_candidate.mock,
            note=raw_candidate.note,
        )
        self.session.add(candidate)
        return candidate

    def list_candidates(self, job_id: str) -> list[SearchCandidateModel]:
        statement = (
            select(SearchCandidateModel)
            .where(SearchCandidateModel.job_id == job_id)
            .order_by(SearchCandidateModel.score_total.desc(), SearchCandidateModel.seeders.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_candidate(self, candidate_id: str) -> SearchCandidateModel | None:
        statement = (
            select(SearchCandidateModel)
            .options(selectinload(SearchCandidateModel.job), selectinload(SearchCandidateModel.bindings))
            .where(SearchCandidateModel.id == candidate_id)
        )
        return self.session.scalar(statement)

    def get_binding(self, binding_id: str) -> DownloadBindingModel | None:
        statement = (
            select(DownloadBindingModel)
            .options(
                selectinload(DownloadBindingModel.candidate).selectinload(SearchCandidateModel.job),
                selectinload(DownloadBindingModel.job),
            )
            .where(DownloadBindingModel.id == binding_id)
        )
        return self.session.scalar(statement)

    def create_binding(
        self,
        *,
        candidate: SearchCandidateModel,
        dispatch_result: DispatchAdapterResult,
    ) -> DownloadBindingModel:
        binding = DownloadBindingModel(
            id=f"bind-{uuid4().hex[:12]}",
            job_id=candidate.job_id,
            candidate_id=candidate.id,
            target_downloader=dispatch_result.target_downloader,
            downloader_task_id=dispatch_result.downloader_task_id,
            dispatchable=dispatch_result.dispatchable,
            dispatch_status=dispatch_result.dispatch_status,
            mock=dispatch_result.mock,
            note=dispatch_result.note,
            integration_point=dispatch_result.integration_point,
            raw_payload=dispatch_result.model_dump(mode="json"),
        )
        candidate.dispatch_status = dispatch_result.dispatch_status
        self.session.add(binding)
        return binding
