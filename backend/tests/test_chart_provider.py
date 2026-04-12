"""Tests for real chart provider integration."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from fastapi import HTTPException

from app.adapters.chart_provider import ListenBrainzChartProviderAdapter, RssFeedChartProviderAdapter
from app.schemas.shared import EntityType
from app.schemas.orchestration import (
    ChartDetailData,
    ChartEntryInfo,
    ChartInfo,
    CreateChartEntrySubscriptionRequest,
    DiscoveryEntryView,
    SubscriptionType,
)
from app.services.charts import ChartService
from app.services.discovery import DiscoveryAssembler
from app.services.music_media_chain import MusicMediaChain
from app.services.subscriptions import SubscriptionService


def build_discovery_assembler() -> DiscoveryAssembler:
    chain = MusicMediaChain(metadata_service=object(), metadata_adapter=object())
    return DiscoveryAssembler(music_media_chain=chain)


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
        service = ChartService(adapter=FakeLiveChartAdapter(), discovery_assembler=build_discovery_assembler())

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
        service = ChartService(adapter=FakeDetailChartAdapter(), discovery_assembler=build_discovery_assembler())

        detail = service.get_chart_detail("chart-listenbrainz-top-tracks-week")

        self.assertIsNotNone(detail.hero_entry)
        self.assertEqual(detail.hero_entry.media_input.external_refs["musicbrainz_recording_id"], "rec-1")
        self.assertEqual(detail.hero_entry.recognition_assessment.state, "direct")
        self.assertGreaterEqual(len(detail.entry_groups), 1)


class RssFeedChartProviderAdapterTest(unittest.TestCase):
    def test_list_charts_returns_rss_feed_chart(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/playlist/9345476": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Wonderful Tonight - Eric Clapton</title>
      <link>https://music.163.com/#/song?id=100001</link>
      <description><![CDATA[歌曲：Wonderful Tonight<br/>歌手：Eric Clapton<br/>专辑：Slowhand]]></description>
      <pubDate>Mon, 31 Mar 2026 10:30:00 GMT</pubDate>
      <guid>song-100001</guid>
    </item>
  </channel>
</rss>"""
        }
        adapter = RssFeedChartProviderAdapter(
            feeds=[
                {
                    "id": "feed-netease-playlist",
                    "label": "网易云喜欢榜单",
                    "category": "liked",
                    "region": "CN",
                    "enabled": True,
                    "url": "https://rsshub.app/163/music/playlist/9345476",
                }
            ],
            fetcher=lambda url: feed_xml_by_url[url],
        )

        charts = adapter.list_charts()

        self.assertEqual(len(charts), 1)
        self.assertEqual(charts[0].chart_source, "rss_feed")
        self.assertEqual(charts[0].chart_type, EntityType.TRACK)
        self.assertEqual(charts[0].id, "rss-feed-feed-netease-playlist")
        self.assertEqual(charts[0].chart_name, "网易云喜欢榜单")
        self.assertEqual(charts[0].category, "liked")
        self.assertEqual(charts[0].region, "CN")

    def test_rss_entry_does_not_look_like_metadata_direct_id(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/playlist/9345476": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Wonderful Tonight - Eric Clapton</title>
      <link>https://music.163.com/#/song?id=100001</link>
      <description><![CDATA[歌曲：Wonderful Tonight<br/>歌手：Eric Clapton<br/>专辑：Slowhand]]></description>
      <pubDate>Mon, 31 Mar 2026 10:30:00 GMT</pubDate>
      <guid>song-100001</guid>
    </item>
  </channel>
</rss>"""
        }
        service = ChartService(
            adapter=RssFeedChartProviderAdapter(
                feeds=[
                    {
                        "id": "feed-netease-playlist",
                        "label": "网易云喜欢榜单",
                        "enabled": True,
                        "url": "https://rsshub.app/163/music/playlist/9345476",
                    }
                ],
                fetcher=lambda url: feed_xml_by_url[url],
            ),
            discovery_assembler=build_discovery_assembler(),
        )

        detail = service.get_chart_detail("rss-feed-feed-netease-playlist")

        self.assertEqual(detail.items[0].target_id, "")
        self.assertIsNotNone(detail.hero_entry)
        self.assertEqual(detail.hero_entry.recognition_assessment.state, "ready")
        self.assertEqual(detail.hero_entry.media_input.source_kind, "discovery")

    def test_rss_entry_keeps_structured_music_clues_in_target_payload(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/playlist/9345476": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Wonderful Tonight - Eric Clapton</title>
      <link>https://music.163.com/#/song?id=100001</link>
      <description><![CDATA[歌曲：Wonderful Tonight<br/>歌手：Eric Clapton<br/>专辑：Slowhand]]></description>
      <pubDate>Mon, 31 Mar 2026 10:30:00 GMT</pubDate>
      <guid>song-100001</guid>
    </item>
  </channel>
</rss>"""
        }
        adapter = RssFeedChartProviderAdapter(
            feeds=[
                {
                    "id": "feed-netease-playlist",
                    "label": "网易云喜欢榜单",
                    "enabled": True,
                    "url": "https://rsshub.app/163/music/playlist/9345476",
                }
            ],
            fetcher=lambda url: feed_xml_by_url[url],
        )

        detail = adapter.get_chart_detail("rss-feed-feed-netease-playlist")
        item = detail.items[0]

        self.assertEqual(item.target_payload["family"], "netease_playlist_tracks")
        self.assertEqual(item.target_payload["provider_origin_url"], "https://music.163.com/#/song?id=100001")
        self.assertEqual(item.target_payload["provider_origin_id"], "100001")
        self.assertEqual(item.target_payload["title"], "Wonderful Tonight")
        self.assertEqual(item.target_payload["artist_name"], "Eric Clapton")
        self.assertEqual(item.target_payload["album_title"], "Slowhand")
        self.assertEqual(item.target_payload["title_candidates"], ["Wonderful Tonight"])
        self.assertEqual(item.target_payload["artist_name_candidates"], ["Eric Clapton"])
        self.assertEqual(item.target_payload["album_title_candidates"], ["Slowhand"])
        self.assertIn("raw_context", item.target_payload)
        self.assertEqual(item.note, adapter.note)

    def test_rss_album_and_artist_entries_include_normalized_music_clue_fields(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/artist/6452": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云艺人专辑</title>
    <item>
      <title>Slowhand</title>
      <link>https://music.163.com/#/album?id=200002</link>
      <description><![CDATA[专辑：Slowhand<br/>歌手：Eric Clapton]]></description>
    </item>
  </channel>
</rss>""",
            "https://rsshub.app/youtube/charts/TopArtists/us": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>YouTube Top Artists</title>
    <item>
      <title>Bruno Mars</title>
      <link>https://www.youtube.com/channel/UCabc123</link>
    </item>
  </channel>
</rss>""",
        }
        adapter = RssFeedChartProviderAdapter(
            feeds=[
                {"id": "feed-album", "enabled": True, "url": "https://rsshub.app/163/music/artist/6452"},
                {"id": "feed-artist", "enabled": True, "url": "https://rsshub.app/youtube/charts/TopArtists/us"},
            ],
            fetcher=lambda url: feed_xml_by_url[url],
            cache_enabled=False,
        )

        album_item = adapter.get_chart_detail("rss-feed-feed-album").items[0]
        artist_item = adapter.get_chart_detail("rss-feed-feed-artist").items[0]

        self.assertEqual(album_item.target_payload["album_title"], "Slowhand")
        self.assertEqual(album_item.target_payload["artist_name"], "Eric Clapton")
        self.assertEqual(album_item.target_payload["album_title_candidates"], ["Slowhand"])
        self.assertEqual(artist_item.target_payload["artist_name"], "Bruno Mars")

    def test_rss_album_entry_without_structured_album_title_does_not_fallback_to_target_name(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/artist/6452": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云艺人专辑</title>
    <item>
      <title>Display Album Name</title>
      <link>https://music.163.com/#/album?id=200099</link>
      <description><![CDATA[歌手：Eric Clapton]]></description>
    </item>
  </channel>
</rss>"""
        }
        adapter = RssFeedChartProviderAdapter(
            feeds=[{"id": "feed-album-no-structured", "enabled": True, "url": "https://rsshub.app/163/music/artist/6452"}],
            fetcher=lambda url: feed_xml_by_url[url],
            cache_enabled=False,
        )

        item = adapter.get_chart_detail("rss-feed-feed-album-no-structured").items[0]

        self.assertEqual(item.target_name, "Display Album Name")
        self.assertIsNone(item.target_payload.get("album_title"))
        self.assertNotEqual(item.target_payload.get("album_title"), item.target_name)

    def test_rss_track_entry_without_structured_title_does_not_fallback_to_synthetic_target_name(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/playlist/9345476": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云喜欢</title>
    <item>
      <link>https://music.163.com/#/song?id=100777</link>
      <description><![CDATA[歌手：Unknown Artist]]></description>
    </item>
  </channel>
</rss>"""
        }
        adapter = RssFeedChartProviderAdapter(
            feeds=[{"id": "feed-track-no-structured-title", "enabled": True, "url": "https://rsshub.app/163/music/playlist/9345476"}],
            fetcher=lambda url: feed_xml_by_url[url],
            cache_enabled=False,
        )

        item = adapter.get_chart_detail("rss-feed-feed-track-no-structured-title").items[0]

        self.assertEqual(item.target_name, "feed-track-no-structured-title-rank-001")
        self.assertEqual(item.target_payload.get("title"), "")
        self.assertNotEqual(item.target_payload.get("title"), item.target_name)

    def test_rss_artist_entry_without_real_artist_name_does_not_backfill_payload_and_not_ready(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/youtube/charts/TopArtists/us": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>YouTube Top Artists</title>
    <item>
      <link>https://www.youtube.com/channel/UCmissingtitle</link>
    </item>
  </channel>
</rss>"""
        }
        service = ChartService(
            adapter=RssFeedChartProviderAdapter(
                feeds=[{"id": "feed-artist-no-name", "enabled": True, "url": "https://rsshub.app/youtube/charts/TopArtists/us"}],
                fetcher=lambda url: feed_xml_by_url[url],
                cache_enabled=False,
            ),
            discovery_assembler=build_discovery_assembler(),
        )

        detail = service.get_chart_detail("rss-feed-feed-artist-no-name")
        item = detail.items[0]

        self.assertEqual(item.target_name, "Unknown Artist")
        self.assertNotIn("artist_name", item.target_payload)
        self.assertEqual(detail.hero_entry.recognition_assessment.state, "insufficient")

    def test_list_charts_skips_disabled_and_unsupported_feeds(self) -> None:
        feed_xml_by_url = {
            "https://rsshub.app/163/music/playlist/9345476": """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Wonderful Tonight - Eric Clapton</title>
      <link>https://music.163.com/#/song?id=100001</link>
      <description><![CDATA[歌曲：Wonderful Tonight<br/>歌手：Eric Clapton<br/>专辑：Slowhand]]></description>
    </item>
  </channel>
</rss>"""
        }
        adapter = RssFeedChartProviderAdapter(
            feeds=[
                {
                    "id": "feed-disabled",
                    "label": "Disabled Feed",
                    "enabled": False,
                    "url": "https://rsshub.app/163/music/playlist/9345476",
                },
                {
                    "id": "feed-unsupported",
                    "label": "Unsupported Feed",
                    "enabled": True,
                    "url": "https://rsshub.app/foo/bar",
                },
                {
                    "id": "feed-enabled",
                    "label": "Enabled Feed",
                    "enabled": True,
                    "category": "liked",
                    "region": "CN",
                    "url": "https://rsshub.app/163/music/playlist/9345476",
                },
            ],
            fetcher=lambda url: feed_xml_by_url[url],
        )

        with self.assertLogs("app.adapters.chart_provider", level="WARNING") as logs:
            charts = adapter.list_charts()

        self.assertEqual(len(charts), 1)
        self.assertEqual(charts[0].id, "rss-feed-feed-enabled")
        self.assertIn("Skipping RSS feed", "\n".join(logs.output))

    def test_constructor_does_not_fetch_feed(self) -> None:
        calls: list[str] = []

        def fetcher(url: str) -> str:
            calls.append(url)
            return "<rss version='2.0'><channel><title>x</title></channel></rss>"

        RssFeedChartProviderAdapter(
            feeds=[
                {
                    "id": "feed-enabled",
                    "label": "Enabled Feed",
                    "enabled": True,
                    "url": "https://rsshub.app/163/music/playlist/9345476",
                }
            ],
            fetcher=fetcher,
        )

        self.assertEqual(calls, [])

    def test_list_charts_uses_cache_but_is_not_permanent_snapshot_when_disabled(self) -> None:
        calls: list[str] = []
        feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>x</title><item><title>a - b</title></item></channel></rss>"""

        def fetcher(url: str) -> str:
            calls.append(url)
            return feed_xml

        cached = RssFeedChartProviderAdapter(
            feeds=[{"id": "feed-enabled", "enabled": True, "url": "https://rsshub.app/163/music/playlist/9345476"}],
            fetcher=fetcher,
            cache_enabled=True,
            cache_ttl_seconds=900,
        )
        cached.list_charts()
        cached.list_charts()
        self.assertEqual(len(calls), 1)

        uncached = RssFeedChartProviderAdapter(
            feeds=[{"id": "feed-enabled", "enabled": True, "url": "https://rsshub.app/163/music/playlist/9345476"}],
            fetcher=fetcher,
            cache_enabled=False,
        )
        uncached.list_charts()
        uncached.list_charts()
        self.assertEqual(len(calls), 3)

    def test_parse_error_is_isolated_with_warning_and_unknown_errors_are_not_silenced(self) -> None:
        def fetcher(url: str) -> str:
            if "badxml" in url:
                return "<rss><channel><title>bad"
            if "boom" in url:
                raise RuntimeError("boom")
            return """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>x</title><item><title>a - b</title></item></channel></rss>"""

        with self.assertLogs("app.adapters.chart_provider", level="WARNING") as logs:
            adapter = RssFeedChartProviderAdapter(
                feeds=[
                    {"id": "badxml", "enabled": True, "url": "https://rsshub.app/163/music/playlist/badxml"},
                    {"id": "good", "enabled": True, "url": "https://rsshub.app/163/music/playlist/9345476"},
                ],
                fetcher=fetcher,
            )
            charts = adapter.list_charts()
        self.assertEqual(len(charts), 1)
        self.assertIn("Skipping RSS feed", "\n".join(logs.output))

        adapter_with_bug = RssFeedChartProviderAdapter(
            feeds=[{"id": "boom", "enabled": True, "url": "https://rsshub.app/163/music/playlist/boom"}],
            fetcher=fetcher,
            cache_enabled=False,
        )
        with self.assertRaises(RuntimeError):
            adapter_with_bug.list_charts()


class SubscriptionServiceChartEntryPayloadTest(unittest.TestCase):
    def test_create_from_chart_entry_preserves_entry_target_payload(self) -> None:
        class FakeMusicMediaChain:
            def resolve(self, payload):  # noqa: ANN001
                return SimpleNamespace(
                    model_dump=lambda mode="json": {
                        "entity_type": payload.entity_hint.value,
                        "provider": "musicbrainz",
                        "provider_id": "recording-wonderful-tonight",
                        "title": payload.title,
                        "artist_names": payload.artist_names,
                        "album_title": payload.album_title,
                        "album_artist_names": payload.album_artist_names,
                        "related_artist_ids": [],
                        "related_track_ids": [],
                        "external_refs": payload.external_refs,
                        "match_evidence": [],
                        "diagnostics": [],
                        "release_context": {},
                    }
                )

            def resolve_response_from_base(self, base):  # noqa: ANN001
                return SimpleNamespace(
                    base=base,
                    assessment=SimpleNamespace(state="direct", note=None),
                    media=SimpleNamespace(
                        model_dump=lambda mode="json": {
                            "entity_type": base.entity_type.value,
                            "provider": "musicbrainz",
                            "provider_id": "recording-wonderful-tonight",
                            "title": base.canonical_title,
                            "artist_names": base.canonical_artist_names,
                            "album_title": base.canonical_album_title,
                            "album_artist_names": base.canonical_album_artist_names,
                            "related_artist_ids": [],
                            "related_track_ids": [],
                            "external_refs": base.external_refs,
                            "match_evidence": [],
                            "diagnostics": [],
                            "release_context": {},
                        }
                    ),
                )

        service = SubscriptionService(
            session=SimpleNamespace(),
            music_media_chain=FakeMusicMediaChain(),
        )
        captured: dict = {}

        class FakeRepository:
            def create_subscription(self, **kwargs):  # noqa: ANN003
                captured.update(kwargs)
                now = datetime.now(timezone.utc)
                return SimpleNamespace(
                    id="sub-1",
                    subscription_type=SubscriptionType.CHART_ENTRY.value,
                    target_id=kwargs["target_id"],
                    target_name=kwargs["target_name"],
                    target_entity_type=kwargs["target_entity_type"],
                    chart_source=kwargs["chart_source"],
                    chart_name=kwargs["chart_name"],
                    status="active",
                    mode=kwargs["mode"],
                    preference_json=kwargs["preference_json"],
                    target_payload_json=kwargs["target_payload_json"],
                    music_media_input=kwargs["music_media_input"],
                    music_meta_base=kwargs["music_meta_base"],
                    music_recognition_assessment=kwargs["music_recognition_assessment"],
                    music_media_info=kwargs["music_media_info"],
                    latest_run_status=None,
                    last_run_at=None,
                    mock=False,
                    note=kwargs["note"],
                    created_at=now,
                    updated_at=now,
                )

        class FakeSession:
            def commit(self):  # noqa: ANN201
                return None

            def refresh(self, _obj):  # noqa: ANN001
                return None

        service.repository = FakeRepository()
        service.session = FakeSession()

        entry = DiscoveryEntryView(
            entry=ChartEntryInfo(
                item_id="rss-item-001",
                chart_id="rss-feed-n1",
                chart_source="rss_feed",
                chart_name="网易云喜欢",
                rank=1,
                item_type=EntityType.TRACK,
                target_id="",
                target_name="Wonderful Tonight",
                subtitle="Eric Clapton",
                provider="rss_feed",
                source_type="rss_feed/netease_playlist_tracks",
                target_payload={
                    "family": "netease_playlist_tracks",
                    "provider_origin_url": "https://music.163.com/#/song?id=100001",
                    "provider_origin_id": "100001",
                    "album_title": "Slowhand",
                },
                mock=False,
                note="rss",
            ),
            media_input={
                "entity_hint": "track",
                "source_kind": "discovery",
                "title": "Wonderful Tonight",
                "artist_names": ["Eric Clapton"],
                "album_title": "Slowhand",
                "external_refs": {
                    "source_id": "100001",
                    "source_url": "https://music.163.com/#/song?id=100001",
                },
                "source_context": {
                    "provider": "rss_feed",
                    "family": "netease_playlist_tracks",
                },
                "raw_context": {},
            },
            entry_summary="Wonderful Tonight · Eric Clapton",
            badges=["rss_feed", "tracks"],
            meta_base={
                "entity_type": "track",
                "canonical_title": "Wonderful Tonight",
                "canonical_artist_names": ["Eric Clapton"],
                "canonical_album_title": "Slowhand",
                "canonical_album_artist_names": [],
                "canonical_release_date": None,
                "canonical_year": None,
                "track_number": None,
                "disc_number": None,
                "alias_titles": [],
                "alias_artist_names": [],
                "alias_album_titles": [],
                "featuring_artist_names": [],
                "external_refs": {
                    "source_id": "100001",
                    "source_url": "https://music.163.com/#/song?id=100001",
                },
                "source_refs": {},
                "evidence": [],
                "normalization_notes": [],
                "confidence_hint": None,
            },
            recognition_assessment={"state": "ready"},
        )

        service.create_from_chart_entry(
            entry=entry,
            payload=CreateChartEntrySubscriptionRequest(chart_item_id="rss-item-001"),
        )

        self.assertEqual(captured["target_payload_json"]["family"], "netease_playlist_tracks")
        self.assertEqual(captured["target_payload_json"]["provider_origin_id"], "100001")
        self.assertEqual(captured["target_payload_json"]["entry_target_payload"]["album_title"], "Slowhand")
        self.assertEqual(captured["music_media_input"]["title"], "Wonderful Tonight")
        self.assertEqual(captured["music_meta_base"]["canonical_title"], "Wonderful Tonight")
        self.assertEqual(captured["music_recognition_assessment"]["state"], "ready")
        self.assertEqual(
            captured["music_media_info"]["provider_id"],
            "recording-wonderful-tonight",
        )

    def test_create_from_chart_entry_rejects_insufficient_media_input(self) -> None:
        class FakeMusicMediaChain:
            def resolve(self, payload):  # noqa: ANN001
                raise AssertionError("resolve should not run for insufficient entries")

        service = SubscriptionService(
            session=SimpleNamespace(),
            music_media_chain=FakeMusicMediaChain(),
        )

        entry = DiscoveryEntryView(
            entry=ChartEntryInfo(
                item_id="rss-item-bad",
                chart_id="rss-feed-n1",
                chart_source="rss_feed",
                chart_name="网易云喜欢",
                rank=9,
                item_type=EntityType.TRACK,
                target_id="",
                target_name="Unknown",
                subtitle=None,
                provider="rss_feed",
                source_type="rss_feed/netease_playlist_tracks",
                target_payload={"family": "netease_playlist_tracks"},
                mock=False,
                note="rss",
            ),
            media_input={
                "entity_hint": "track",
                "source_kind": "discovery",
                "artist_names": [],
                "external_refs": {},
                "source_context": {},
                "raw_context": {},
            },
            entry_summary="Unknown",
            badges=["rss_feed", "tracks"],
            meta_base={
                "entity_type": "track",
                "canonical_title": None,
                "canonical_artist_names": [],
                "canonical_album_title": None,
                "canonical_album_artist_names": [],
                "canonical_release_date": None,
                "canonical_year": None,
                "track_number": None,
                "disc_number": None,
                "alias_titles": [],
                "alias_artist_names": [],
                "alias_album_titles": [],
                "featuring_artist_names": [],
                "external_refs": {},
                "source_refs": {},
                "evidence": [],
                "normalization_notes": [],
                "confidence_hint": None,
            },
            recognition_assessment={
                "state": "insufficient",
                "note": "Missing music meta base fields: requires canonical_title + canonical_artist_names.",
            },
        )

        with self.assertRaises(HTTPException) as context:
            service.create_from_chart_entry(
                entry=entry,
                payload=CreateChartEntrySubscriptionRequest(chart_item_id="rss-item-bad"),
            )

        self.assertEqual(context.exception.status_code, 400)
