"""Tests for chart runtime refresh and discovery source health."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.chain.chart import MusicChartChain
from app.core.dependencies import get_music_chart_chain
from app.helper.discovery import MusicDiscoveryBuilder
from app.helper.settings import SettingsHelper
from app.main import app
from app.db.models import AppSettingModel, Base, ChartItemModel, ChartModel
from app.db.charts_oper import ChartsOper
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo
from app.schemas.shared import EntityType
from app.chain.media import MusicMediaChain


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def build_discovery_builder() -> MusicDiscoveryBuilder:
    chain = MusicMediaChain(metadata_module=object(), metadata_provider=object())
    return MusicDiscoveryBuilder(music_media_chain=chain)


def build_chart_detail(chart_id: str = "chart-001") -> ChartDetailData:
    updated_at = datetime(2026, 4, 13, 10, 30, tzinfo=timezone.utc)
    return ChartDetailData(
        chart=ChartInfo(
            id=chart_id,
            chart_source="rss_feed",
            chart_name="Demo Chart",
            chart_type=EntityType.TRACK,
            region="Global",
            category="demo",
            refresh_hint="daily",
            item_count=1,
            updated_at=updated_at,
            mock=False,
            note="live",
        ),
        items=[
            ChartEntryInfo(
                item_id=f"{chart_id}-item-001",
                chart_id=chart_id,
                chart_source="rss_feed",
                chart_name="Demo Chart",
                rank=1,
                item_type=EntityType.TRACK,
                target_id="track-001",
                target_name="Hello",
                subtitle="Adele",
                provider="rss_feed",
                source_type="rss_feed",
                mock=False,
                note="live",
            )
        ],
        item_count=1,
        mock=False,
        note="live",
        integration_point="FakeChartAdapter",
    )


class FakeChartAdapter:
    provider = "rss_feed"
    source_type = "rss_feed"
    mock = False
    note = "live"
    integration_point = "FakeChartAdapter"

    def __init__(self, detail: ChartDetailData, *, raise_error: Exception | None = None):
        self.detail = detail
        self.raise_error = raise_error

    def list_providers(self):  # noqa: ANN201
        return []

    def list_charts(self):  # noqa: ANN201
        return [self.detail.chart]

    def get_chart_detail(self, chart_id: str):  # noqa: ANN201
        if self.raise_error is not None:
            raise self.raise_error
        if chart_id != self.detail.chart.id:
            raise KeyError(f"Chart {chart_id} was not found in the demo catalog.")
        return self.detail

    def get_chart_entry(self, chart_id: str, item_id: str):  # noqa: ANN201
        if chart_id != self.detail.chart.id:
            raise KeyError(f"Chart {chart_id} was not found in the demo catalog.")
        for item in self.detail.items:
            if item.item_id == item_id:
                return item
        raise KeyError(f"Chart entry {item_id} was not found in chart {chart_id}.")


class ChartRuntimeRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.env_settings = SimpleNamespace(chart_cache_ttl_seconds=900)
        self.settings_service = SettingsHelper(session=self.session, env_settings=self.env_settings)
        self.chart_repository = ChartsOper(self.session)
        self.detail = build_chart_detail()
        self.service = MusicChartChain(
            adapter=FakeChartAdapter(self.detail),
            discovery_assembler=build_discovery_builder(),
            settings_oper=None,
            charts_oper=self.chart_repository,
            env_settings=self.env_settings,
        )
        app.dependency_overrides[get_music_chart_chain] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_music_chart_chain, None)

    def test_get_chart_runtime_returns_persisted_snapshot_and_marks_old_status_stale(self) -> None:
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        self.session.add(
            ChartModel(
                id=self.detail.chart.id,
                chart_source=self.detail.chart.chart_source,
                chart_name=self.detail.chart.chart_name,
                chart_type=self.detail.chart.chart_type.value,
                region=self.detail.chart.region,
                category=self.detail.chart.category,
                refresh_hint=self.detail.chart.refresh_hint,
                item_count=self.detail.item_count,
                source_updated_at=self.detail.chart.updated_at,
                last_refreshed_at=old_timestamp,
                last_refresh_status="success",
                last_error=None,
                stale=False,
                mock=self.detail.mock,
                note=self.detail.note,
                integration_point=self.detail.integration_point,
            )
        )
        self.session.commit()

        response = self.client.get(f"/api/v1/plugin/musicpilot/charts/{self.detail.chart.id}/runtime")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["id"], self.detail.chart.id)
        self.assertEqual(data["runtime"]["last_refresh_status"], "success")
        self.assertTrue(data["runtime"]["stale"])

    def test_refresh_chart_updates_persisted_chart_runtime_without_touching_feed_config(self) -> None:
        self.session.add(
            AppSettingModel(
                key="chart_rss_feeds",
                value_json=[
                    {
                        "id": "netease-hot-tracks",
                        "label": "网易云热歌榜",
                        "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
                        "category": "hot",
                        "region": "CN",
                        "enabled": True,
                    }
                ],
            )
        )
        self.session.commit()

        response = self.client.post(f"/api/v1/plugin/musicpilot/charts/{self.detail.chart.id}/refresh")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        runtime = data["chart"]["runtime"]
        self.assertEqual(runtime["last_refresh_status"], "success")
        self.assertIsNone(runtime["last_error"])
        self.assertFalse(runtime["stale"])
        self.assertIsNotNone(runtime["last_refreshed_at"])
        self.assertEqual(
            self.session.get(AppSettingModel, "chart_rss_feeds").value_json,
            [
                {
                    "id": "netease-hot-tracks",
                    "label": "网易云热歌榜",
                    "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
                    "category": "hot",
                    "region": "CN",
                    "enabled": True,
                }
            ],
        )
        persisted_chart = self.session.get(ChartModel, self.detail.chart.id)
        self.assertIsNotNone(persisted_chart)
        self.assertEqual(persisted_chart.last_refresh_status, "success")

    def test_refresh_chart_failure_records_last_error_on_persisted_chart(self) -> None:
        self.service.refresh_chart(self.detail.chart.id)
        failing_service = MusicChartChain(
            adapter=FakeChartAdapter(self.detail, raise_error=RuntimeError("boom")),
            discovery_assembler=build_discovery_builder(),
            settings_oper=None,
            charts_oper=self.chart_repository,
            env_settings=self.env_settings,
        )

        with self.assertRaises(HTTPException):
            failing_service.refresh_chart(self.detail.chart.id)

        persisted_chart = self.session.get(ChartModel, self.detail.chart.id)
        self.assertIsNotNone(persisted_chart)
        self.assertEqual(persisted_chart.last_refresh_status, "failed")
        self.assertIn("RuntimeError: boom", persisted_chart.last_error)
        self.assertTrue(persisted_chart.stale)

    def test_refresh_chart_persists_chart_and_items_for_cached_reads(self) -> None:
        self.service.refresh_chart(self.detail.chart.id)

        persisted_chart = self.session.get(ChartModel, self.detail.chart.id)
        persisted_item = self.session.query(ChartItemModel).filter(ChartItemModel.chart_id == self.detail.chart.id).first()

        self.assertIsNotNone(persisted_chart)
        self.assertEqual(persisted_chart.id, self.detail.chart.id)
        self.assertEqual(persisted_chart.chart_name, "Demo Chart")
        self.assertEqual(persisted_chart.item_count, 1)
        self.assertIsNotNone(persisted_item)
        self.assertEqual(persisted_item.chart_id, self.detail.chart.id)
        self.assertEqual(persisted_item.target_name, "Hello")

    def test_get_chart_detail_uses_persisted_chart_when_provider_is_unavailable(self) -> None:
        self.service.refresh_chart(self.detail.chart.id)
        failing_service = MusicChartChain(
            adapter=FakeChartAdapter(self.detail, raise_error=RuntimeError("boom")),
            discovery_assembler=build_discovery_builder(),
            settings_oper=None,
            charts_oper=self.chart_repository,
            env_settings=self.env_settings,
        )

        detail = failing_service.get_chart_detail(self.detail.chart.id)

        self.assertEqual(detail.chart.id, self.detail.chart.id)
        self.assertEqual(detail.item_count, 1)
        self.assertEqual(detail.items[0].target_name, "Hello")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
