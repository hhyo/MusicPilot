"""Chart discovery service for Phase 4 mock subscriptions."""

from __future__ import annotations

from fastapi import HTTPException

from ..adapters.chart_provider import CHART_INTEGRATION_POINT, ChartProviderAdapter
from ..schemas.mvp import EntityType
from ..schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartListData,
    ChartProviderInfo,
    DiscoveryEntryView,
)
from .discovery import DiscoveryAssembler


class ChartService:
    def __init__(self, adapter: ChartProviderAdapter, discovery_assembler: DiscoveryAssembler):
        self.adapter = adapter
        self.discovery_assembler = discovery_assembler

    def list_providers(self) -> list[ChartProviderInfo]:
        return self.adapter.list_providers()

    def list_charts(
        self,
        *,
        provider: str | None = None,
        chart_type: EntityType | None = None,
        region: str | None = None,
    ) -> ChartListData:
        items = [self.discovery_assembler.build_chart_info(item) for item in self.adapter.list_charts()]
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
        try:
            return self.discovery_assembler.build_detail(self.adapter.get_chart_detail(chart_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
