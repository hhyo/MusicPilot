"""Chart discovery service for Phase 4 mock subscriptions."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from ..adapters.chart_provider import ChartProviderAdapter
from ..repositories.charts import ChartRepository
from ..schemas.shared import EntityType
from ..schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartInfo,
    ChartListData,
    ChartProviderInfo,
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
        chart_repository: ChartRepository,
    ):
        self.adapter = adapter
        self.discovery_assembler = discovery_assembler
        self.settings_service = settings_service
        self.chart_repository = chart_repository

    def list_providers(self) -> list[ChartProviderInfo]:
        return self.adapter.list_providers()

    def list_charts(
        self,
        *,
        provider: str | None = None,
        chart_type: EntityType | None = None,
        region: str | None = None,
    ) -> ChartListData:
        provider_filter = provider or self.adapter.provider
        items = self.chart_repository.list_charts(
            provider=provider_filter,
            chart_type=chart_type,
            region=region,
            refresh_interval_minutes=self._refresh_interval_minutes(),
        )
        if not items and provider_filter == self.adapter.provider:
            self.refresh_all_charts()
            items = self.chart_repository.list_charts(
                provider=provider_filter,
                chart_type=chart_type,
                region=region,
                refresh_interval_minutes=self._refresh_interval_minutes(),
            )
        return ChartListData(
            items=items,
            total=len(items),
            mock=self.adapter.mock,
            note=self.adapter.note,
            integration_point=self.adapter.integration_point,
        )

    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        persisted = self.chart_repository.get_chart_detail(
            chart_id,
            refresh_interval_minutes=self._refresh_interval_minutes(),
        )
        if persisted is not None:
            return self.discovery_assembler.build_detail(persisted)
        return self.refresh_chart(chart_id)

    def get_chart_runtime(self, chart_id: str) -> ChartInfo:
        persisted = self.chart_repository.get_chart_detail(
            chart_id,
            refresh_interval_minutes=self._refresh_interval_minutes(),
        )
        if persisted is not None:
            return persisted.chart
        return self.refresh_chart(chart_id).chart

    def refresh_chart(self, chart_id: str) -> ChartDetailData:
        refreshed_at = datetime.now(timezone.utc)
        try:
            detail = self.adapter.get_chart_detail(chart_id)
        except KeyError as exc:
            self.chart_repository.mark_refresh_failure(chart_id, error_message=str(exc), refreshed_at=refreshed_at)
            self._commit_chart_repository()
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            self.chart_repository.mark_refresh_failure(
                chart_id,
                error_message=f"{type(exc).__name__}: {exc}",
                refreshed_at=refreshed_at,
            )
            self._commit_chart_repository()
            raise HTTPException(status_code=502, detail=f"Chart refresh failed for {chart_id}.") from exc

        persisted = self.chart_repository.upsert_chart_detail(
            detail,
            last_refreshed_at=refreshed_at,
            last_refresh_status="success",
            last_error=None,
            stale=False,
        )
        self._commit_chart_repository()
        return self.discovery_assembler.build_detail(
            self.chart_repository.get_chart_detail(
                chart_id,
                refresh_interval_minutes=self._refresh_interval_minutes(),
            )
            or persisted
        )

    def refresh_all_charts(self) -> dict[str, object]:
        refreshed_at = datetime.now(timezone.utc)
        refreshed_ids: list[str] = []
        failed: dict[str, str] = {}
        active_chart_ids: set[str] = set()

        try:
            catalog = self.adapter.list_charts()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail="Chart catalog refresh failed.") from exc

        for chart in catalog:
            active_chart_ids.add(chart.id)
            try:
                detail = self.adapter.get_chart_detail(chart.id)
                self.chart_repository.upsert_chart_detail(
                    detail,
                    last_refreshed_at=refreshed_at,
                    last_refresh_status="success",
                    last_error=None,
                    stale=False,
                )
                refreshed_ids.append(chart.id)
            except Exception as exc:  # noqa: BLE001
                self.chart_repository.mark_refresh_failure(
                    chart.id,
                    error_message=f"{type(exc).__name__}: {exc}",
                    refreshed_at=refreshed_at,
                )
                failed[chart.id] = str(exc)

        removed_ids = self.chart_repository.remove_missing_charts(
            provider=self.adapter.provider,
            active_chart_ids=active_chart_ids,
        )
        self._commit_chart_repository()
        return {
            "refreshed_ids": refreshed_ids,
            "failed": failed,
            "removed_ids": removed_ids,
            "provider": self.adapter.provider,
        }

    def get_chart_entry(self, chart_id: str, item_id: str) -> ChartEntryInfo:
        detail = self.get_chart_detail(chart_id)
        for item in detail.items:
            if item.item_id == item_id:
                return item
        raise HTTPException(status_code=404, detail=f"Chart entry {item_id} was not found in {chart_id}.")

    def get_discovery_entry(self, chart_id: str, item_id: str) -> DiscoveryEntryView:
        detail = self.get_chart_detail(chart_id)
        if detail.hero_entry and detail.hero_entry.entry.item_id == item_id:
            return detail.hero_entry
        for group in detail.entry_groups:
            for item in group.items:
                if item.entry.item_id == item_id:
                    return item
        raise HTTPException(status_code=404, detail=f"Chart entry {item_id} was not found in {chart_id}.")

    def _refresh_interval_minutes(self) -> int:
        value = getattr(self.settings_service.env_settings, "chart_refresh_interval_minutes", 60)
        try:
            minutes = int(value)
        except (TypeError, ValueError):
            return 60
        return minutes if minutes > 0 else 60

    def _commit_chart_repository(self) -> None:
        session = getattr(self.chart_repository, "session", None)
        if session is None:
            return
        session.commit()
