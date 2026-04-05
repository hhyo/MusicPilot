"""Subscription execution orchestration for Phase 6."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.orchestration import OrchestrationRepository
from ..schemas.acquisition import QueryPreferences, SearchJobCreateRequest
from ..schemas.metadata import MetadataDetail
from ..schemas.mvp import EntityType, JobStatus, TriggerSource
from ..schemas.orchestration import (
    SubscriptionRunDetail,
    SubscriptionRunListData,
    SubscriptionRunStatus,
    SubscriptionState,
    SubscriptionSummary,
    SubscriptionType,
)
from .organize import OrganizeService
from .search_job import SearchJobService
from .subscriptions import serialize_run_summary, serialize_subscription


RUN_NOTE = (
    "当前订阅执行器会在手动 run 或最小应用内 scheduler 触发下，同步创建并执行一次 SearchJob，"
    "并生成 organize preview。真实 organize apply 仍按 capability 与 adapter 模式选择 host 或 mock。"
)


class SubscriptionExecutionService:
    def __init__(
        self,
        session: Session,
        *,
        search_job_service: SearchJobService,
        organize_service: OrganizeService,
    ):
        self.session = session
        self.search_job_service = search_job_service
        self.organize_service = organize_service
        self.repository = OrchestrationRepository(session)

    def execute(self, subscription_id: str) -> SubscriptionRunDetail:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")
        if subscription.status == SubscriptionState.ARCHIVED.value:
            raise HTTPException(status_code=400, detail="Archived subscription can not be executed.")

        run = self.repository.create_run(subscription, note=RUN_NOTE)
        self.repository.mark_run_running(run)
        self.session.flush()

        try:
            job_payload = self._build_job_request(subscription)
            created_job = self.search_job_service.create_job(job_payload)
            executed_job = self.search_job_service.execute_job(created_job.id)
            candidates_data = self.search_job_service.list_candidates(executed_job.id)

            organize_preview = None
            if candidates_data.items:
                organize_preview = self.organize_service.preview_for_candidate(
                    candidate_id=candidates_data.items[0].id,
                    subscription_run_id=run.id,
                )

            self.repository.mark_run_finished(
                run,
                execution_status=self._map_run_status(executed_job.status).value,
                matched_candidates_count=candidates_data.total,
                summary_json={
                    "best_score": executed_job.summary.get("best_score", 0.0),
                    "candidate_count": candidates_data.total,
                    "mock_host_search": executed_job.mock,
                    "organize_preview_id": organize_preview.id if organize_preview else None,
                    "organize_backend": organize_preview.organize_backend.value if organize_preview else None,
                    "organize_fallback_reason": organize_preview.fallback_reason if organize_preview else None,
                },
                search_job_id=executed_job.id,
                organize_record_id=organize_preview.id if organize_preview else None,
            )
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_run = self.repository.get_run(run.id)
            if failed_run is not None:
                self.repository.mark_run_finished(
                    failed_run,
                    execution_status=SubscriptionRunStatus.FAILED.value,
                    matched_candidates_count=0,
                    summary_json={"candidate_count": 0},
                    error_message=str(exc),
                )
                self.session.commit()
            raise

        return self.get_run_detail(run.id)

    def list_runs(self, subscription_id: str) -> SubscriptionRunListData:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")
        items = [serialize_run_summary(run) for run in self.repository.list_runs(subscription_id)]
        return SubscriptionRunListData(
            subscription_id=subscription_id,
            items=items,
            total=len(items),
            mock=False,
            note="当前 run 记录反映的是手动或最小应用内 scheduler 触发的同步执行结果。",
        )

    def get_run_detail(self, run_id: str) -> SubscriptionRunDetail:
        run = self.repository.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Subscription run {run_id} was not found.")

        subscription_summary = serialize_subscription(run.subscription)
        metadata_target = self._resolve_metadata_target(run.subscription)
        search_job = (
            self.search_job_service.get_job(run.search_job_id) if run.search_job_id else None
        )
        candidates = (
            self.search_job_service.list_candidates(run.search_job_id).items if run.search_job_id else []
        )
        organize_preview = (
            self.organize_service.get_record(run.organize_record_id) if run.organize_record_id else None
        )

        return SubscriptionRunDetail(
            **serialize_run_summary(run).model_dump(),
            subscription=subscription_summary,
            metadata_target=metadata_target,
            search_job=search_job,
            candidates=candidates,
            organize_preview=organize_preview,
        )

    def _build_job_request(self, subscription) -> SearchJobCreateRequest:
        entity_type, entity_id = self._resolve_query_source(subscription)
        preferences = QueryPreferences.model_validate(subscription.preference_json or {})
        return SearchJobCreateRequest(
            query_source_type=entity_type,
            query_source_id=entity_id,
            trigger_source=TriggerSource.SUBSCRIPTION,
            profile_id="default-lossless",
            mode="manual" if subscription.mode == "manual" else "auto",
            preferences=preferences,
        )

    def _resolve_metadata_target(self, subscription) -> MetadataDetail | None:
        entity_type, entity_id = self._resolve_query_source(subscription)
        return self.search_job_service.metadata_service.get_detail(entity_type, entity_id)

    def _resolve_query_source(self, subscription) -> tuple[EntityType, str]:
        if subscription.subscription_type == SubscriptionType.CHART_ENTRY.value:
            payload = subscription.target_payload_json or {}
            target_entity_type = payload.get("target_entity_type")
            target_id = payload.get("target_id")
            if not target_entity_type or not target_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Subscription {subscription.id} does not contain a valid chart entry target payload.",
                )
            return EntityType(target_entity_type), str(target_id)

        target_entity_type = subscription.target_entity_type or subscription.subscription_type
        return EntityType(target_entity_type), subscription.target_id

    def _map_run_status(self, job_status: JobStatus) -> SubscriptionRunStatus:
        if job_status == JobStatus.MANUAL_PENDING:
            return SubscriptionRunStatus.MANUAL_PENDING
        if job_status == JobStatus.NO_RESULT:
            return SubscriptionRunStatus.NO_RESULT
        if job_status == JobStatus.FAILED:
            return SubscriptionRunStatus.FAILED
        return SubscriptionRunStatus.MATCHED
