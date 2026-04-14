from __future__ import annotations

import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.charts_oper import ChartsOper
from app.db.models import Base
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo
from app.schemas.shared import EntityType


class ChartsOperTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        self.oper = ChartsOper(self.session)

    def tearDown(self) -> None:
        self.session.close()

    def test_upsert_and_load_chart_detail(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="chart-001",
                chart_source="rss_feed",
                chart_name="Demo Chart",
                chart_type=EntityType.TRACK,
                region="Global",
                category="demo",
                refresh_hint="daily",
                item_count=1,
                updated_at=datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc),
                mock=False,
                note="live",
            ),
            items=[
                ChartEntryInfo(
                    item_id="chart-001-item-001",
                    chart_id="chart-001",
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
            integration_point="test",
        )

        self.oper.upsert_chart_detail(
            detail,
            last_refreshed_at=datetime(2026, 4, 13, 12, 5, tzinfo=timezone.utc),
            last_refresh_status="success",
            last_error=None,
            stale=False,
        )
        self.session.commit()

        loaded = self.oper.get_chart_detail("chart-001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.chart.id, "chart-001")
        self.assertEqual(loaded.items[0].target_name, "Hello")


if __name__ == "__main__":
    unittest.main()
