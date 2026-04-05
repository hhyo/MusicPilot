from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from app.schemas.mvp import EntityType
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo
from app.services.discovery import DiscoveryAssembler


class DiscoveryAssemblerTests(TestCase):
    def test_builds_metadata_ready_track_target(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="chart-listenbrainz-top-tracks-week",
                chart_source="listenbrainz",
                chart_name="ListenBrainz 热门单曲（week）",
                chart_type=EntityType.TRACK,
                region="Global",
                category="sitewide",
                refresh_hint="sitewide-week",
                item_count=1,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="live",
            ),
            items=[
                ChartEntryInfo(
                    item_id="chart-listenbrainz-top-tracks-week-item-001",
                    chart_id="chart-listenbrainz-top-tracks-week",
                    chart_source="listenbrainz",
                    chart_name="ListenBrainz 热门单曲（week）",
                    rank=1,
                    item_type=EntityType.TRACK,
                    target_id="recording-mbid-001",
                    target_name="Hello",
                    subtitle="Adele",
                    provider="listenbrainz",
                    source_type="listenbrainz_sitewide_stats",
                    mock=False,
                    note="live",
                )
            ],
            item_count=1,
            mock=False,
            note="live",
            integration_point="ListenBrainzChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)

        self.assertIsNotNone(result.hero_entry)
        self.assertEqual(result.hero_entry.target.target_kind, EntityType.TRACK)
        self.assertEqual(result.hero_entry.target.provider, "musicbrainz")
        self.assertEqual(result.hero_entry.target.provider_id, "recording-mbid-001")
        self.assertTrue(result.hero_entry.target.conversion_ready)
        self.assertEqual(result.conversion_summary["ready"], 1)
        self.assertEqual(result.entry_groups[0].group_key, "tracks")

    def test_builds_not_ready_target_when_entry_has_no_target_id(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="chart-editorial-artists",
                chart_source="local_mock",
                chart_name="Editorial Artists",
                chart_type=EntityType.ARTIST,
                region="Global",
                category="editorial",
                refresh_hint="manual-placeholder",
                item_count=1,
                updated_at=datetime.now(timezone.utc),
                mock=True,
                note="mock",
            ),
            items=[
                ChartEntryInfo(
                    item_id="chart-editorial-artists-item-001",
                    chart_id="chart-editorial-artists",
                    chart_source="local_mock",
                    chart_name="Editorial Artists",
                    rank=1,
                    item_type=EntityType.ARTIST,
                    target_id="",
                    target_name="Unknown Artist",
                    subtitle=None,
                    provider="seed",
                    source_type="mock_chart_seed",
                    mock=True,
                    note="mock",
                )
            ],
            item_count=1,
            mock=True,
            note="mock",
            integration_point="MockChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)

        self.assertIsNotNone(result.hero_entry)
        self.assertFalse(result.hero_entry.target.conversion_ready)
        self.assertEqual(result.hero_entry.target.conversion_note, "Missing provider target id.")
        self.assertEqual(result.conversion_summary["not_ready"], 1)
        self.assertEqual(result.entry_groups[0].group_key, "artists")
