"""Tests for real chart provider integration."""

from __future__ import annotations

import unittest

from app.adapters.chart_provider import ListenBrainzChartProviderAdapter
from app.schemas.mvp import EntityType
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo
from app.services.charts import ChartService
from app.services.discovery import DiscoveryAssembler


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeClient:
    def __init__(self, payloads: dict[str, dict]):
        self.payloads = payloads
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, path: str, params: dict | None = None) -> FakeResponse:
        self.calls.append((path, params))
        return FakeResponse(self.payloads[path])


class ListenBrainzChartProviderAdapterTest(unittest.TestCase):
    def test_list_charts_and_detail_reuse_cached_payload(self) -> None:
        client = FakeClient(
            payloads={
                "/1/stats/sitewide/artists": {
                    "payload": {
                        "last_updated": 1_775_500_000,
                        "artists": [{"artist_mbid": "artist-1", "artist_name": "Adele", "listen_count": 99}],
                    }
                },
                "/1/stats/sitewide/recordings": {
                    "payload": {
                        "last_updated": 1_775_500_000,
                        "recordings": [
                            {
                                "recording_mbid": "rec-1",
                                "track_name": "Hello",
                                "artist_name": "Adele",
                                "listen_count": 10,
                            }
                        ],
                    }
                },
            }
        )
        adapter = ListenBrainzChartProviderAdapter(client=client)

        adapter.list_charts()
        adapter.get_chart_detail("chart-listenbrainz-top-tracks-week")
        adapter.get_chart_entry("chart-listenbrainz-top-tracks-week", "chart-listenbrainz-top-tracks-week-item-001")

        self.assertEqual(client.calls.count(("/1/stats/sitewide/recordings", {"count": 20, "range": "week"})), 1)
        self.assertEqual(client.calls.count(("/1/stats/sitewide/artists", {"count": 20, "range": "week"})), 1)

    def test_list_charts_returns_artist_and_track_chart(self) -> None:
        adapter = ListenBrainzChartProviderAdapter(
            client=FakeClient(
                payloads={
                    "/1/stats/sitewide/artists": {
                        "payload": {
                            "last_updated": 1_775_500_000,
                            "artists": [{"artist_mbid": "artist-1", "artist_name": "Adele", "listen_count": 99}],
                        }
                    },
                    "/1/stats/sitewide/recordings": {
                        "payload": {
                            "last_updated": 1_775_500_000,
                            "recordings": [
                                {
                                    "recording_mbid": "rec-1",
                                    "track_name": "Hello",
                                    "artist_name": "Adele",
                                    "listen_count": 10,
                                }
                            ],
                        }
                    },
                }
            )
        )

        charts = adapter.list_charts()

        self.assertEqual([item.id for item in charts], [
            "chart-listenbrainz-top-artists-week",
            "chart-listenbrainz-top-tracks-week",
        ])
        self.assertEqual([item.chart_type for item in charts], [EntityType.ARTIST, EntityType.TRACK])
        self.assertTrue(all(not item.mock for item in charts))

    def test_track_chart_detail_maps_recording_mbid_as_target_id(self) -> None:
        adapter = ListenBrainzChartProviderAdapter(
            client=FakeClient(
                payloads={
                    "/1/stats/sitewide/recordings": {
                        "payload": {
                            "last_updated": 1_775_500_000,
                            "recordings": [
                                {
                                    "recording_mbid": "rec-1",
                                    "track_name": "Hello",
                                    "artist_name": "Adele",
                                    "listen_count": 10,
                                }
                            ],
                        }
                    }
                }
            )
        )

        detail = adapter.get_chart_detail("chart-listenbrainz-top-tracks-week")

        self.assertFalse(detail.mock)
        self.assertEqual(detail.items[0].target_id, "rec-1")
        self.assertEqual(detail.items[0].target_name, "Hello")
        self.assertEqual(detail.items[0].subtitle, "Adele")
        self.assertEqual(detail.items[0].item_type, EntityType.TRACK)

    def test_track_chart_detail_dedupes_duplicate_recording_ids(self) -> None:
        adapter = ListenBrainzChartProviderAdapter(
            client=FakeClient(
                payloads={
                    "/1/stats/sitewide/recordings": {
                        "payload": {
                            "last_updated": 1_775_500_000,
                            "recordings": [
                                {
                                    "recording_mbid": "rec-1",
                                    "track_name": "SWIM",
                                    "artist_name": "BTS",
                                    "listen_count": 10,
                                },
                                {
                                    "recording_mbid": "rec-1",
                                    "track_name": "SWIM",
                                    "artist_name": "BTS",
                                    "listen_count": 9,
                                },
                                {
                                    "recording_mbid": "rec-2",
                                    "track_name": "Dracula",
                                    "artist_name": "Tame Impala",
                                    "listen_count": 8,
                                },
                            ],
                        }
                    }
                }
            )
        )

        detail = adapter.get_chart_detail("chart-listenbrainz-top-tracks-week")

        self.assertEqual(detail.item_count, 2)
        self.assertEqual([item.target_id for item in detail.items], ["rec-1", "rec-2"])
        self.assertEqual([item.rank for item in detail.items], [1, 2])

    def test_artist_chart_detail_maps_artist_mbid_as_target_id(self) -> None:
        adapter = ListenBrainzChartProviderAdapter(
            client=FakeClient(
                payloads={
                    "/1/stats/sitewide/artists": {
                        "payload": {
                            "last_updated": 1_775_500_000,
                            "artists": [
                                {
                                    "artist_mbid": "artist-1",
                                    "artist_name": "Adele",
                                    "listen_count": 99,
                                }
                            ],
                        }
                    }
                }
            )
        )

        detail = adapter.get_chart_detail("chart-listenbrainz-top-artists-week")

        self.assertEqual(detail.items[0].target_id, "artist-1")
        self.assertEqual(detail.items[0].target_name, "Adele")
        self.assertEqual(detail.items[0].item_type, EntityType.ARTIST)


class FakeLiveChartAdapter:
    provider = "listenbrainz"
    source_type = "listenbrainz_sitewide_stats"
    mock = False
    integration_point = "ListenBrainzChartProviderAdapter"
    note = "当前榜单来自真实 ListenBrainz sitewide stats。"

    def list_providers(self):  # noqa: ANN201
        return []

    def list_charts(self):  # noqa: ANN201
        from datetime import datetime, timezone

        from app.schemas.orchestration import ChartInfo

        return [
            ChartInfo(
                id="chart-1",
                chart_source="listenbrainz",
                chart_name="Top Tracks",
                chart_type=EntityType.TRACK,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note=self.note,
            )
        ]

    def get_chart_detail(self, chart_id: str):  # noqa: ANN201, ARG002
        raise NotImplementedError

    def get_chart_entry(self, chart_id: str, item_id: str):  # noqa: ANN201, ARG002
        raise NotImplementedError


class ChartServiceLiveModeTest(unittest.TestCase):
    def test_chart_service_live_mode_is_not_mock(self) -> None:
        service = ChartService(adapter=FakeLiveChartAdapter(), discovery_assembler=DiscoveryAssembler())

        result = service.list_charts()

        self.assertFalse(result.mock)
        self.assertIn("ListenBrainz", result.note)
        self.assertEqual(result.items[0].chart_group, "tracks")
        self.assertIsNotNone(result.items[0].summary)


class FakeDetailChartAdapter(FakeLiveChartAdapter):
    def get_chart_detail(self, chart_id: str):  # noqa: ANN201, ARG002
        from datetime import datetime, timezone

        return ChartDetailData(
            chart=ChartInfo(
                id="chart-listenbrainz-top-tracks-week",
                chart_source="listenbrainz",
                chart_name="Top Tracks",
                chart_type=EntityType.TRACK,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="live",
            ),
            items=[
                ChartEntryInfo(
                    item_id="chart-item-001",
                    chart_id="chart-listenbrainz-top-tracks-week",
                    chart_source="listenbrainz",
                    chart_name="Top Tracks",
                    rank=1,
                    item_type=EntityType.TRACK,
                    target_id="rec-1",
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


class ChartServiceDiscoveryEnrichmentTest(unittest.TestCase):
    def test_chart_service_enriches_detail(self) -> None:
        service = ChartService(adapter=FakeDetailChartAdapter(), discovery_assembler=DiscoveryAssembler())

        detail = service.get_chart_detail("chart-listenbrainz-top-tracks-week")

        self.assertIsNotNone(detail.hero_entry)
        self.assertEqual(detail.hero_entry.target.provider_id, "rec-1")
        self.assertGreaterEqual(len(detail.entry_groups), 1)
