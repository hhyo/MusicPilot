"""Subscription CRUD service for Phase 6."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.orchestration import OrchestrationRepository
from ..schemas.metadata import MetadataDetail
from ..schemas.mvp import EntityType
from ..schemas.orchestration import (
    ChartEntryInfo,
    CreateChartEntrySubscriptionRequest,
    CreateSubscriptionRequest,
    SubscriptionDetail,
    SubscriptionListData,
    SubscriptionSummary,
    SubscriptionType,
    UpdateSubscriptionRequest,
)
from .metadata import MetadataService


SUBSCRIPTION_NOTE = (
    "当前订阅模型已落库，但执行模式仍是 Phase 6 的同步最小闭环；"
    "scheduled_placeholder 仅保留后续调度器接入点。"
)


class SubscriptionService:
    def __init__(self, session: Session, metadata_service: MetadataService):
        self.session = session
        self.metadata_service = metadata_service
        self.repository = OrchestrationRepository(session)

    def list_subscriptions(
        self,
        *,
        subscription_type: SubscriptionType | None = None,
        status: str | None = None,
    ) -> SubscriptionListData:
        items = [
            serialize_subscription(subscription)
            for subscription in self.repository.list_subscriptions(
                subscription_type=subscription_type.value if subscription_type else None,
                status=status,
            )
        ]
        return SubscriptionListData(
            items=items,
            total=len(items),
            mock=True,
            note="当前订阅列表反映的是 Phase 6 最小闭环，未接入真实自动调度。",
        )

    def get_subscription(self, subscription_id: str) -> SubscriptionDetail:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")

        recent_runs = [
            serialize_run_summary(run)
            for run in sorted(subscription.runs, key=lambda item: item.created_at, reverse=True)[:5]
        ]
        return SubscriptionDetail(**serialize_subscription(subscription).model_dump(), recent_runs=recent_runs)

    def create_subscription(self, payload: CreateSubscriptionRequest) -> SubscriptionSummary:
        if payload.subscription_type == SubscriptionType.CHART_ENTRY:
            raise HTTPException(
                status_code=400,
                detail="Use the chart subscription route for chart_entry subscriptions.",
            )

        resolved_type = payload.target_entity_type or EntityType(payload.subscription_type.value)
        detail = self.metadata_service.get_detail(resolved_type, payload.target_id)
        subscription = self.repository.create_subscription(
            subscription_type=payload.subscription_type.value,
            target_id=payload.target_id,
            target_name=payload.target_name or detail.title,
            target_entity_type=detail.entity_type.value,
            chart_source=None,
            chart_name=None,
            mode=payload.mode.value,
            preference_json=payload.preference_json,
            target_payload_json=payload.target_payload,
            note=SUBSCRIPTION_NOTE,
        )
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def create_from_chart_entry(
        self,
        *,
        entry: ChartEntryInfo,
        payload: CreateChartEntrySubscriptionRequest,
    ) -> SubscriptionSummary:
        subscription = self.repository.create_subscription(
            subscription_type=SubscriptionType.CHART_ENTRY.value,
            target_id=entry.item_id,
            target_name=entry.target_name,
            target_entity_type=entry.item_type.value,
            chart_source=entry.chart_source,
            chart_name=entry.chart_name,
            mode=payload.mode.value,
            preference_json=payload.preference_json,
            target_payload_json={
                "chart_id": entry.chart_id,
                "chart_item_id": entry.item_id,
                "chart_source": entry.chart_source,
                "chart_name": entry.chart_name,
                "rank": entry.rank,
                "target_id": entry.target_id,
                "target_name": entry.target_name,
                "target_entity_type": entry.item_type.value,
                "subtitle": entry.subtitle,
            },
            note=(
                "当前榜单订阅来自 mock chart entry。后续真实榜单接入后，可在此结构上接入增量刷新、"
                "命中检测与调度器。"
            ),
        )
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def update_subscription(
        self,
        subscription_id: str,
        payload: UpdateSubscriptionRequest,
    ) -> SubscriptionSummary:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")

        if payload.status is not None:
            subscription.status = payload.status.value
        if payload.mode is not None:
            subscription.mode = payload.mode.value
        if payload.preference_json is not None:
            subscription.preference_json = payload.preference_json

        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def archive_subscription(self, subscription_id: str) -> SubscriptionSummary:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")

        subscription.status = "archived"
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)


def serialize_subscription_detail(detail: MetadataDetail) -> tuple[str, str]:
    return detail.title, detail.entity_type.value


def serialize_subscription(subscription) -> SubscriptionSummary:
    target_entity_type = subscription.target_entity_type
    return SubscriptionSummary(
        id=subscription.id,
        subscription_type=SubscriptionType(subscription.subscription_type),
        target_id=subscription.target_id,
        target_name=subscription.target_name,
        target_entity_type=target_entity_type,
        chart_source=subscription.chart_source,
        chart_name=subscription.chart_name,
        status=subscription.status,
        mode=subscription.mode,
        preference_json=subscription.preference_json or {},
        target_payload=subscription.target_payload_json or {},
        latest_run_status=subscription.latest_run_status,
        last_run_at=subscription.last_run_at,
        mock=subscription.mock,
        note=subscription.note,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


def serialize_run_summary(run) -> "SubscriptionRunSummary":
    from ..schemas.orchestration import SubscriptionRunStatus, SubscriptionRunSummary

    return SubscriptionRunSummary(
        id=run.id,
        subscription_id=run.subscription_id,
        search_job_id=run.search_job_id,
        execution_status=SubscriptionRunStatus(run.execution_status),
        matched_candidates_count=run.matched_candidates_count,
        dispatch_recommendation=run.dispatch_recommendation,
        organize_record_id=run.organize_record_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        summary_json=run.summary_json or {},
        mock=run.mock,
        note=run.note,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )
