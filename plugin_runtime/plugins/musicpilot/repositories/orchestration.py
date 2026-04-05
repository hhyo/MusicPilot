"""Repository layer for Phase 6 subscriptions and organize records."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from ..models.orchestration import OrganizeRecordModel, SubscriptionModel, SubscriptionRunModel
from ..schemas.orchestration import OrganizeAdapterResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OrchestrationRepository:
    def __init__(self, session: Session):
        self.session = session

    def clear_all(self) -> None:
        self.session.execute(delete(OrganizeRecordModel))
        self.session.execute(delete(SubscriptionRunModel))
        self.session.execute(delete(SubscriptionModel))

    def create_subscription(
        self,
        *,
        subscription_type: str,
        target_id: str,
        target_name: str,
        target_entity_type: str | None,
        chart_source: str | None,
        chart_name: str | None,
        mode: str,
        preference_json: dict,
        target_payload_json: dict,
        note: str,
    ) -> SubscriptionModel:
        subscription = SubscriptionModel(
            id=f"sub-{uuid4().hex[:12]}",
            subscription_type=subscription_type,
            target_id=target_id,
            target_name=target_name,
            target_entity_type=target_entity_type,
            chart_source=chart_source,
            chart_name=chart_name,
            status="active",
            mode=mode,
            preference_json=preference_json,
            target_payload_json=target_payload_json,
            mock=False,
            note=note,
        )
        self.session.add(subscription)
        return subscription

    def list_subscriptions(
        self,
        *,
        subscription_type: str | None = None,
        status: str | None = None,
    ) -> list[SubscriptionModel]:
        statement = (
            select(SubscriptionModel)
            .options(selectinload(SubscriptionModel.runs))
            .order_by(SubscriptionModel.updated_at.desc())
        )
        if subscription_type:
            statement = statement.where(SubscriptionModel.subscription_type == subscription_type)
        if status:
            statement = statement.where(SubscriptionModel.status == status)
        return list(self.session.scalars(statement).all())

    def get_subscription(self, subscription_id: str) -> SubscriptionModel | None:
        statement = (
            select(SubscriptionModel)
            .options(selectinload(SubscriptionModel.runs))
            .where(SubscriptionModel.id == subscription_id)
        )
        return self.session.scalar(statement)

    def has_running_run(self, subscription_id: str) -> bool:
        statement = (
            select(SubscriptionRunModel.id)
            .where(SubscriptionRunModel.subscription_id == subscription_id)
            .where(SubscriptionRunModel.execution_status == "running")
            .limit(1)
        )
        return self.session.scalar(statement) is not None

    def create_run(self, subscription: SubscriptionModel, *, note: str) -> SubscriptionRunModel:
        run = SubscriptionRunModel(
            id=f"srun-{uuid4().hex[:12]}",
            subscription_id=subscription.id,
            execution_status="queued",
            matched_candidates_count=0,
            mock=False,
            note=note,
        )
        self.session.add(run)
        return run

    def mark_run_running(self, run: SubscriptionRunModel) -> None:
        run.execution_status = "running"
        run.started_at = utc_now()
        run.error_message = None

    def mark_run_finished(
        self,
        run: SubscriptionRunModel,
        *,
        execution_status: str,
        matched_candidates_count: int,
        summary_json: dict,
        search_job_id: str | None = None,
        organize_record_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        run.search_job_id = search_job_id
        run.execution_status = execution_status
        run.matched_candidates_count = matched_candidates_count
        run.summary_json = summary_json
        run.organize_record_id = organize_record_id
        run.error_message = error_message
        run.finished_at = utc_now()

        subscription = run.subscription or self.session.get(SubscriptionModel, run.subscription_id)
        if subscription is not None:
            subscription.latest_run_status = execution_status
            subscription.last_run_at = run.finished_at

    def list_runs(self, subscription_id: str) -> list[SubscriptionRunModel]:
        statement = (
            select(SubscriptionRunModel)
            .options(selectinload(SubscriptionRunModel.subscription))
            .where(SubscriptionRunModel.subscription_id == subscription_id)
            .order_by(SubscriptionRunModel.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_run(self, run_id: str) -> SubscriptionRunModel | None:
        statement = (
            select(SubscriptionRunModel)
            .options(selectinload(SubscriptionRunModel.subscription))
            .where(SubscriptionRunModel.id == run_id)
        )
        return self.session.scalar(statement)

    def create_organize_record(
        self,
        *,
        subscription_run_id: str | None,
        search_job_id: str | None,
        candidate_id: str | None,
        binding_id: str | None,
        result: OrganizeAdapterResult,
    ) -> OrganizeRecordModel:
        record = OrganizeRecordModel(
            id=f"org-{uuid4().hex[:12]}",
            subscription_run_id=subscription_run_id,
            search_job_id=search_job_id,
            candidate_id=candidate_id,
            binding_id=binding_id,
            organizeable=result.organizeable,
            organize_backend=result.organize_backend.value,
            strategy=result.strategy,
            library_type=result.strategy_snapshot.library_type,
            root_path=result.strategy_snapshot.root_path,
            organize_status=result.organize_status.value,
            target_library_path=result.target_library_path,
            target_relative_path=result.target_relative_path,
            conflict_policy=result.strategy_snapshot.conflict_policy.value,
            strategy_note=result.strategy_note,
            integration_point=result.integration_point,
            capability_source=result.capability_source,
            fallback_reason=result.fallback_reason,
            failure_reason=result.failure_reason,
            verification_state=result.verification_state.value,
            mock=result.mock,
            raw_payload=result.model_dump(mode="json"),
            note=result.note,
        )
        self.session.add(record)
        return record

    def mark_organize_apply_pending(self, record: OrganizeRecordModel) -> None:
        record.organize_status = "apply_pending"
        record.failure_reason = None

    def update_organize_record(self, record: OrganizeRecordModel, *, result: OrganizeAdapterResult) -> OrganizeRecordModel:
        record.organizeable = result.organizeable
        record.organize_backend = result.organize_backend.value
        record.strategy = result.strategy
        record.library_type = result.strategy_snapshot.library_type
        record.root_path = result.strategy_snapshot.root_path
        record.organize_status = result.organize_status.value
        record.target_library_path = result.target_library_path
        record.target_relative_path = result.target_relative_path
        record.conflict_policy = result.strategy_snapshot.conflict_policy.value
        record.strategy_note = result.strategy_note
        record.integration_point = result.integration_point
        record.capability_source = result.capability_source
        record.fallback_reason = result.fallback_reason
        record.failure_reason = result.failure_reason
        record.verification_state = result.verification_state.value
        record.mock = result.mock
        record.raw_payload = result.model_dump(mode="json")
        record.note = result.note
        record.updated_at = utc_now()
        return record

    def list_organize_records(self) -> list[OrganizeRecordModel]:
        statement = select(OrganizeRecordModel).order_by(OrganizeRecordModel.created_at.desc())
        return list(self.session.scalars(statement).all())

    def get_organize_record(self, record_id: str) -> OrganizeRecordModel | None:
        statement = select(OrganizeRecordModel).where(OrganizeRecordModel.id == record_id)
        return self.session.scalar(statement)
