"""Chart discovery service for Phase 4 mock subscriptions."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from ..adapters.chart_provider import CHART_INTEGRATION_POINT, ChartProviderAdapter
from ..schemas.shared import EntityType
from ..schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartInfo,
    ChartListData,
    ChartProviderInfo,
    ChartRuntimeStatus,
    DiscoveryEntryView,
)
from .discovery import DiscoveryAssembler
from .settings import SettingsService


class ChartService:
    def __init__(
        self,
        adapter: ChartProviderAdapter,
        discovery_assembler: DiscoveryAssembler,
        settings_service: SettingsService,
    ):
        self.adapter = adapter
        self.discovery_assembler = discovery_assembler
        self.settings_service = settings_service

    def list_providers(self) -> list[ChartProviderInfo]:
        return self.adapter.list_providers()

    def list_charts(
        self,
        *,
        provider: str | None = None,
        chart_type: EntityType | None = None,
        region: str | None = None,
    ) -> ChartListData:
        items = [self._attach_runtime_to_chart(self.discovery_assembler.build_chart_info(item)) for item in self.adapter.list_charts()]
        if provider:
            items = [item for item in items if item.chart_source == provider]
        if chart_type:
            items = [item for item in items if item.chart_type == chart_type]
        if region:
            items = [item for item in items if item.region == region]
        return ChartListData(
            items=items,
            total=len(items),
            mock=self.adapter.mock,
            note=self.adapter.note,
            integration_point=self.adapter.integration_point,
        )

    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        return self._load_chart_detail(chart_id)

    def get_chart_runtime(self, chart_id: str) -> ChartInfo:
        return self.get_chart_detail(chart_id).chart

    def refresh_chart(self, chart_id: str) -> ChartDetailData:
        try:
            detail = self.discovery_assembler.build_detail(self.adapter.get_chart_detail(chart_id))
        except KeyError as exc:
            self.settings_service.update_chart_runtime_snapshot(
                chart_id,
                ChartRuntimeStatus(
                    last_refreshed_at=datetime.now(timezone.utc),
                    last_refresh_status="failed",
                    last_error=str(exc),
                    stale=True,
                ),
            )
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            self.settings_service.update_chart_runtime_snapshot(
                chart_id,
                ChartRuntimeStatus(
                    last_refreshed_at=datetime.now(timezone.utc),
                    last_refresh_status="failed",
                    last_error=f"{type(exc).__name__}: {exc}",
                    stale=True,
                ),
            )
            raise HTTPException(status_code=502, detail=f"Chart refresh failed for {chart_id}.") from exc

        runtime = self.settings_service.update_chart_runtime_snapshot(
            chart_id,
            ChartRuntimeStatus(
                last_refreshed_at=datetime.now(timezone.utc),
                last_refresh_status="success",
                last_error=None,
                stale=False,
            ),
        )
        return self._attach_runtime_to_detail(detail, runtime=runtime)

    def get_chart_entry(self, chart_id: str, item_id: str) -> ChartEntryInfo:
        try:
            return self.adapter.get_chart_entry(chart_id, item_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def get_discovery_entry(self, chart_id: str, item_id: str) -> DiscoveryEntryView:
        detail = self.get_chart_detail(chart_id)
        if detail.hero_entry and detail.hero_entry.entry.item_id == item_id:
            return detail.hero_entry
        for group in detail.entry_groups:
            for item in group.items:
                if item.entry.item_id == item_id:
                    return item
        raise HTTPException(status_code=404, detail=f"Chart entry {item_id} was not found in {chart_id}.")

    def _load_chart_detail(self, chart_id: str) -> ChartDetailData:
        try:
            detail = self.discovery_assembler.build_detail(self.adapter.get_chart_detail(chart_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return self._attach_runtime_to_detail(detail)

    def _attach_runtime_to_detail(
        self,
        detail: ChartDetailData,
        *,
        runtime: ChartRuntimeStatus | None = None,
    ) -> ChartDetailData:
        chart = self._attach_runtime_to_chart(detail.chart, runtime=runtime)
        return detail.model_copy(update={"chart": chart})

    def _attach_runtime_to_chart(
        self,
        chart: ChartInfo,
        *,
        runtime: ChartRuntimeStatus | None = None,
    ) -> ChartInfo:
        chart_runtime = runtime or self.settings_service.get_chart_runtime_snapshot(chart.id)
        return chart.model_copy(update={"runtime": chart_runtime})
