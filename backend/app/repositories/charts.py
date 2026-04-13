"""Repository layer for persisted charts and chart items."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.charts import ChartItemModel, ChartModel
from ..schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo, ChartRuntimeStatus
from ..schemas.shared import EntityType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChartRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_charts(
        self,
        *,
        provider: str | None = None,
        chart_type: EntityType | None = None,
        region: str | None = None,
        refresh_interval_minutes: int = 60,
    ) -> list[ChartInfo]:
        statement = select(ChartModel).order_by(ChartModel.chart_name.asc())
        if provider:
            statement = statement.where(ChartModel.chart_source == provider)
        if chart_type:
            statement = statement.where(ChartModel.chart_type == chart_type.value)
        if region:
            statement = statement.where(ChartModel.region == region)
        return [
            self._build_chart_info(model, refresh_interval_minutes=refresh_interval_minutes)
            for model in self.session.scalars(statement).all()
        ]

    def get_chart_detail(
        self,
        chart_id: str,
        *,
        refresh_interval_minutes: int = 60,
    ) -> ChartDetailData | None:
        statement = (
            select(ChartModel)
            .options(selectinload(ChartModel.items))
            .where(ChartModel.id == chart_id)
        )
        model = self.session.scalars(statement).first()
        if model is None:
            return None
        chart = self._build_chart_info(model, refresh_interval_minutes=refresh_interval_minutes)
        items = [self._build_chart_item(item) for item in sorted(model.items, key=lambda value: value.rank)]
        return ChartDetailData(
            chart=chart,
            items=items,
            item_count=len(items),
            mock=chart.mock,
            note=chart.note,
            integration_point=model.integration_point or "",
        )

    def upsert_chart_detail(
        self,
        detail: ChartDetailData,
        *,
        last_refreshed_at: datetime,
        last_refresh_status: str,
        last_error: str | None,
        stale: bool,
    ) -> ChartDetailData:
        chart = detail.chart
        model = self.session.get(ChartModel, detail.chart.id)
        if model is None:
            model = ChartModel(
                id=chart.id,
                chart_source=chart.chart_source,
                chart_name=chart.chart_name,
                chart_type=chart.chart_type.value,
                region=chart.region,
                category=chart.category,
                refresh_hint=chart.refresh_hint,
                item_count=detail.item_count,
                source_updated_at=chart.updated_at,
                last_refreshed_at=last_refreshed_at,
                last_refresh_status=last_refresh_status,
                last_error=last_error,
                stale=stale,
                mock=detail.mock,
                note=detail.note,
                summary=chart.summary,
                chart_group=chart.chart_group,
                chart_scope=chart.chart_scope,
                freshness_label=chart.freshness_label,
                supports_subscription=chart.supports_subscription,
                integration_point=detail.integration_point,
            )
            self.session.add(model)
        model.chart_source = chart.chart_source
        model.chart_name = chart.chart_name
        model.chart_type = chart.chart_type.value
        model.region = chart.region
        model.category = chart.category
        model.refresh_hint = chart.refresh_hint
        model.item_count = detail.item_count
        model.source_updated_at = chart.updated_at
        model.last_refreshed_at = last_refreshed_at
        model.last_refresh_status = last_refresh_status
        model.last_error = last_error
        model.stale = stale
        model.mock = detail.mock
        model.note = detail.note
        model.summary = chart.summary
        model.chart_group = chart.chart_group
        model.chart_scope = chart.chart_scope
        model.freshness_label = chart.freshness_label
        model.supports_subscription = chart.supports_subscription
        model.integration_point = detail.integration_point

        self.session.query(ChartItemModel).filter(ChartItemModel.chart_id == chart.id).delete()
        for item in detail.items:
            self.session.add(
                ChartItemModel(
                    id=item.item_id,
                    chart_id=chart.id,
                    chart_source=item.chart_source,
                    chart_name=item.chart_name,
                    rank=item.rank,
                    item_type=item.item_type.value,
                    target_id=item.target_id,
                    target_name=item.target_name,
                    subtitle=item.subtitle,
                    provider=item.provider,
                    source_type=item.source_type,
                    target_payload=item.target_payload,
                    mock=item.mock,
                    note=item.note,
                )
            )
        self.session.flush()
        return self.get_chart_detail(chart.id, refresh_interval_minutes=60)  # type: ignore[return-value]

    def mark_refresh_failure(
        self,
        chart_id: str,
        *,
        error_message: str,
        refreshed_at: datetime,
    ) -> None:
        model = self.session.get(ChartModel, chart_id)
        if model is None:
            return
        model.last_refreshed_at = refreshed_at
        model.last_refresh_status = "failed"
        model.last_error = error_message
        model.stale = True

    def remove_missing_charts(self, *, provider: str, active_chart_ids: set[str]) -> list[str]:
        statement = select(ChartModel.id).where(ChartModel.chart_source == provider)
        existing_ids = set(self.session.scalars(statement).all())
        obsolete_ids = sorted(existing_ids - active_chart_ids)
        if not obsolete_ids:
            return []
        self.session.query(ChartItemModel).filter(ChartItemModel.chart_id.in_(obsolete_ids)).delete(synchronize_session=False)
        self.session.query(ChartModel).filter(ChartModel.id.in_(obsolete_ids)).delete(synchronize_session=False)
        return obsolete_ids

    def _build_chart_info(self, model: ChartModel, *, refresh_interval_minutes: int) -> ChartInfo:
        runtime = self._build_runtime_status(model, refresh_interval_minutes=refresh_interval_minutes)
        return ChartInfo(
            id=model.id,
            chart_source=model.chart_source,
            chart_name=model.chart_name,
            chart_type=EntityType(model.chart_type),
            region=model.region,
            category=model.category,
            refresh_hint=model.refresh_hint,
            item_count=model.item_count,
            updated_at=self._normalize_timestamp(model.source_updated_at),
            mock=model.mock,
            note=model.note,
            summary=model.summary,
            chart_group=model.chart_group,
            chart_scope=model.chart_scope,
            freshness_label=model.freshness_label,
            supports_subscription=model.supports_subscription,
            runtime=runtime,
        )

    def _build_chart_item(self, model: ChartItemModel) -> ChartEntryInfo:
        return ChartEntryInfo(
            item_id=model.id,
            chart_id=model.chart_id,
            chart_source=model.chart_source,
            chart_name=model.chart_name,
            rank=model.rank,
            item_type=EntityType(model.item_type),
            target_id=model.target_id,
            target_name=model.target_name,
            subtitle=model.subtitle,
            provider=model.provider,
            source_type=model.source_type,
            target_payload=model.target_payload or {},
            mock=model.mock,
            note=model.note,
        )

    def _build_runtime_status(self, model: ChartModel, *, refresh_interval_minutes: int) -> ChartRuntimeStatus:
        last_refreshed_at = self._normalize_timestamp(model.last_refreshed_at) if model.last_refreshed_at else None
        stale = True
        if model.last_refresh_status == "success" and last_refreshed_at is not None:
            stale = utc_now() - last_refreshed_at > timedelta(minutes=max(1, refresh_interval_minutes))
        elif model.last_refresh_status == "failed":
            stale = True
        else:
            stale = model.stale
        return ChartRuntimeStatus(
            last_refreshed_at=last_refreshed_at,
            last_refresh_status=model.last_refresh_status,
            last_error=model.last_error,
            stale=stale,
        )

    @staticmethod
    def _normalize_timestamp(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
