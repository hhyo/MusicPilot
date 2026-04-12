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

from app.core.dependencies import get_chart_service
from app.main import app
from app.models import AppSettingModel, Base
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo, ChartRuntimeStatus
from app.schemas.shared import EntityType
from app.services.charts import ChartService
from app.services.discovery import DiscoveryAssembler
from app.services.music_media_chain import MusicMediaChain
from app.services.settings import SettingsService


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def build_discovery_assembler() -> DiscoveryAssembler:
    chain = MusicMediaChain(metadata_service=object(), metadata_adapter=object())
    return DiscoveryAssembler(music_media_chain=chain)


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
        self.settings_service = SettingsService(session=self.session, env_settings=self.env_settings)
        self.detail = build_chart_detail()
        self.service = ChartService(
            adapter=FakeChartAdapter(self.detail),
            discovery_assembler=build_discovery_assembler(),
            settings_service=self.settings_service,
        )
        app.dependency_overrides[get_chart_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_chart_service, None)

    def test_get_chart_runtime_returns_persisted_snapshot_and_marks_old_status_stale(self) -> None:
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        self.session.add(
            AppSettingModel(
                key="chart_runtime_snapshots",
                value_json={
                    self.detail.chart.id: {
                        "last_refreshed_at": old_timestamp.isoformat(),
                        "last_refresh_status": "success",
                        "last_error": None,
                        "stale": False,
                    }
                },
            )
        )
        self.session.commit()

        response = self.client.get(f"/api/v1/plugin/musicpilot/charts/{self.detail.chart.id}/runtime")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["id"], self.detail.chart.id)
        self.assertEqual(data["runtime"]["last_refresh_status"], "success")
        self.assertTrue(data["runtime"]["stale"])

    def test_refresh_chart_updates_runtime_snapshot_without_touching_feed_config(self) -> None:
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
        self.assertEqual(
            self.session.get(AppSettingModel, "chart_runtime_snapshots").value_json[self.detail.chart.id]["last_refresh_status"],
            "success",
        )

    def test_refresh_chart_failure_records_last_error_snapshot(self) -> None:
        failing_service = ChartService(
            adapter=FakeChartAdapter(self.detail, raise_error=RuntimeError("boom")),
            discovery_assembler=build_discovery_assembler(),
            settings_service=self.settings_service,
        )

        with self.assertRaises(HTTPException):
            failing_service.refresh_chart(self.detail.chart.id)

        snapshot = self.session.get(AppSettingModel, "chart_runtime_snapshots").value_json[self.detail.chart.id]
        self.assertEqual(snapshot["last_refresh_status"], "failed")
        self.assertIn("RuntimeError: boom", snapshot["last_error"])
        self.assertTrue(snapshot["stale"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
