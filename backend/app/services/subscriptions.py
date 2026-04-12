"""Subscription CRUD service for Phase 6."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.orchestration import OrchestrationRepository
from ..schemas.shared import EntityType
from ..schemas.orchestration import (
    ChartEntryInfo,
    CreateChartEntrySubscriptionRequest,
    CreateSubscriptionRequest,
    DiscoveryEntryView,
    SubscriptionDetail,
    SubscriptionListData,
    SubscriptionSummary,
    SubscriptionType,
    UpdateSubscriptionRequest,
)
from ..schemas.music_media import MusicRecognitionState
from .subscription_scheduler import normalize_subscription_mode


SUBSCRIPTION_NOTE = (
    "当前订阅模型已落库，可切换手动执行或最小应用内 scheduler；"
    "production 级 cron、失败重试和增量检测仍待后续补齐。"
)


class SubscriptionService:
    def __init__(self, session: Session, music_media_chain):
        self.session = session
        self.music_media_chain = music_media_chain
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
            mock=False,
            note="当前订阅列表反映的是手动 run 与最小应用内 scheduler 的真实状态。",
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
        resolved = self.music_media_chain.resolve_detail_from_target_payload_ref(
            entity_type=resolved_type,
            target_id=payload.target_id,
            target_payload=payload.target_payload,
            source_kind="subscription",
            source_context={
                "subscription_type": payload.subscription_type.value,
                "target_id": payload.target_id,
            },
            raw_context={"target_payload": payload.target_payload},
        )
        media_input = self.music_media_chain.input_from_target_payload_ref(
            entity_type=resolved_type,
            target_id=payload.target_id,
            target_payload=payload.target_payload,
            source_kind="subscription",
            source_context={
                "subscription_type": payload.subscription_type.value,
                "target_id": payload.target_id,
            },
            raw_context={"target_payload": payload.target_payload},
        )
        target_payload = dict(payload.target_payload)
        subscription = self.repository.create_subscription(
            subscription_type=payload.subscription_type.value,
            target_id=payload.target_id,
            target_name=payload.target_name or resolved.detail.title,
            target_entity_type=resolved.detail.entity_type.value,
            chart_source=None,
            chart_name=None,
            mode=normalize_subscription_mode(payload.mode.value),
            preference_json=payload.preference_json,
            target_payload_json=target_payload,
            music_media_input=media_input.model_dump(mode="json"),
            music_meta_base=resolved.base.model_dump(mode="json"),
            music_recognition_assessment=resolved.assessment.model_dump(mode="json"),
            music_media_info=resolved.media.model_dump(mode="json"),
            note=SUBSCRIPTION_NOTE,
        )
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def create_from_chart_entry(
        self,
        *,
        entry: DiscoveryEntryView,
        payload: CreateChartEntrySubscriptionRequest,
    ) -> SubscriptionSummary:
        if entry.recognition_assessment.state not in {MusicRecognitionState.DIRECT, MusicRecognitionState.READY}:
            raise HTTPException(
                status_code=400,
                detail=entry.recognition_assessment.note
                or "Chart entry does not have enough music media clues for subscription.",
            )

        resolved = self.music_media_chain.resolve_response_from_base(entry.meta_base)
        chart_entry = entry.entry
        entry_hints = dict(chart_entry.target_payload or {})
        subscription = self.repository.create_subscription(
            subscription_type=SubscriptionType.CHART_ENTRY.value,
            target_id=chart_entry.item_id,
            target_name=chart_entry.target_name,
            target_entity_type=chart_entry.item_type.value,
            chart_source=chart_entry.chart_source,
            chart_name=chart_entry.chart_name,
            mode=normalize_subscription_mode(payload.mode.value),
            preference_json=payload.preference_json,
            target_payload_json={
                "chart_id": chart_entry.chart_id,
                "chart_item_id": chart_entry.item_id,
                "chart_source": chart_entry.chart_source,
                "chart_name": chart_entry.chart_name,
                "rank": chart_entry.rank,
                "target_id": chart_entry.target_id,
                "target_name": chart_entry.target_name,
                "target_entity_type": chart_entry.item_type.value,
                "subtitle": chart_entry.subtitle,
                "entry_target_payload": entry_hints,
                **entry_hints,
            },
            music_media_input=entry.media_input.model_dump(mode="json"),
            music_meta_base=entry.meta_base.model_dump(mode="json"),
            music_recognition_assessment=entry.recognition_assessment.model_dump(mode="json"),
            music_media_info=resolved.media.model_dump(mode="json"),
            note=(
                "当前榜单订阅来自 mock chart entry，并已在创建时固化统一音乐媒体链识别结果；"
                "后续真实榜单接入后，可在此结构上接入增量刷新、命中检测与调度器。"
                if chart_entry.mock
                else "当前榜单订阅来自真实 chart entry，并已在创建时固化统一音乐媒体链识别结果；"
                "已可手动 run 或进入最小应用内 scheduler，自动刷新、增量命中检测与 production 级调度仍待后续补齐。"
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
            subscription.mode = normalize_subscription_mode(payload.mode.value)
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
        mode=normalize_subscription_mode(subscription.mode),
        preference_json=subscription.preference_json or {},
        target_payload=subscription.target_payload_json or {},
        music_media_input=_parse_optional_music_media_input(subscription.music_media_input),
        music_meta_base=_parse_optional_music_meta_base(subscription.music_meta_base),
        music_recognition_assessment=_parse_optional_music_recognition_assessment(
            subscription.music_recognition_assessment
        ),
        music_media_info=_parse_optional_music_media_info(subscription.music_media_info),
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
        organize_record_id=run.organize_record_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        summary_json=run.summary_json or {},
        music_media_input=_parse_optional_music_media_input(run.music_media_input),
        music_meta_base=_parse_optional_music_meta_base(run.music_meta_base),
        music_recognition_assessment=_parse_optional_music_recognition_assessment(
            run.music_recognition_assessment
        ),
        music_media_info=_parse_optional_music_media_info(run.music_media_info),
        mock=run.mock,
        note=run.note,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _parse_optional_music_media_input(payload):
    if not payload:
        return None
    from ..schemas.music_media import MusicMediaInput

    return MusicMediaInput.model_validate(payload)


def _parse_optional_music_meta_base(payload):
    if not payload:
        return None
    from ..schemas.music_media import MusicMetaBase

    return MusicMetaBase.model_validate(payload)


def _parse_optional_music_recognition_assessment(payload):
    if not payload:
        return None
    from ..schemas.music_media import MusicRecognitionAssessment

    return MusicRecognitionAssessment.model_validate(payload)


def _parse_optional_music_media_info(payload):
    if not payload:
        return None
    from ..schemas.music_media import MusicMediaInfo

    return MusicMediaInfo.model_validate(payload)
