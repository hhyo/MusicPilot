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

    def test_builds_rss_track_target_with_search_lookup_hints(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-n1",
                chart_source="rss_feed",
                chart_name="网易云喜欢",
                chart_type=EntityType.TRACK,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
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
                        "title": "Wonderful Tonight",
                        "artist_name": "Eric Clapton",
                        "album_title": "Slowhand",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertTrue(target.conversion_ready)
        self.assertEqual(target.resolution_mode, "search_lookup")
        self.assertEqual(target.resolution_hints["title"], "Wonderful Tonight")
        self.assertEqual(target.resolution_hints["artist_name"], "Eric Clapton")
        self.assertEqual(target.resolution_hints["album_title"], "Slowhand")
        self.assertEqual(target.resolution_hints["provider_origin_url"], "https://music.163.com/#/song?id=100001")
        self.assertEqual(target.resolution_hints["provider_origin_id"], "100001")
        self.assertEqual(target.resolution_hints["family"], "netease_playlist_tracks")

    def test_builds_rss_album_target_with_search_lookup_hints(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-n2",
                chart_source="rss_feed",
                chart_name="网易云艺人专辑",
                chart_type=EntityType.ALBUM,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
                    item_id="rss-item-002",
                    chart_id="rss-feed-n2",
                    chart_source="rss_feed",
                    chart_name="网易云艺人专辑",
                    rank=1,
                    item_type=EntityType.ALBUM,
                    target_id="",
                    target_name="Slowhand",
                    subtitle="Eric Clapton",
                    provider="rss_feed",
                    source_type="rss_feed/netease_artist_albums",
                    target_payload={
                        "family": "netease_artist_albums",
                        "provider_origin_url": "https://music.163.com/#/album?id=200002",
                        "provider_origin_id": "200002",
                        "album_title": "Slowhand",
                        "artist_name": "Eric Clapton",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertTrue(target.conversion_ready)
        self.assertEqual(target.resolution_mode, "search_lookup")
        self.assertEqual(target.resolution_hints["album_title"], "Slowhand")
        self.assertEqual(target.resolution_hints["artist_name"], "Eric Clapton")
        self.assertEqual(target.resolution_hints["provider_origin_url"], "https://music.163.com/#/album?id=200002")
        self.assertEqual(target.resolution_hints["provider_origin_id"], "200002")
        self.assertEqual(target.resolution_hints["family"], "netease_artist_albums")

    def test_builds_rss_artist_target_with_search_lookup_hints(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-y1",
                chart_source="rss_feed",
                chart_name="YouTube Top Artists",
                chart_type=EntityType.ARTIST,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
                    item_id="rss-item-003",
                    chart_id="rss-feed-y1",
                    chart_source="rss_feed",
                    chart_name="YouTube Top Artists",
                    rank=1,
                    item_type=EntityType.ARTIST,
                    target_id="",
                    target_name="Bruno Mars",
                    subtitle=None,
                    provider="rss_feed",
                    source_type="rss_feed/youtube_top_artists",
                    target_payload={
                        "family": "youtube_top_artists",
                        "provider_origin_url": "https://www.youtube.com/channel/UCabc123",
                        "provider_origin_id": "UCabc123",
                        "artist_name": "Bruno Mars",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertTrue(target.conversion_ready)
        self.assertEqual(target.resolution_mode, "search_lookup")
        self.assertEqual(target.resolution_hints["artist_name"], "Bruno Mars")
        self.assertEqual(target.resolution_hints["provider_origin_url"], "https://www.youtube.com/channel/UCabc123")
        self.assertEqual(target.resolution_hints["provider_origin_id"], "UCabc123")
        self.assertEqual(target.resolution_hints["family"], "youtube_top_artists")

    def test_non_rss_entry_keeps_direct_id_resolution_mode(self) -> None:
        detail = ChartDetailData(
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

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertEqual(target.resolution_mode, "direct_id")
        self.assertEqual(target.provider_id, "rec-1")

    def test_rss_track_uses_payload_artist_name_not_subtitle_album_fallback(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-n3",
                chart_source="rss_feed",
                chart_name="网易云喜欢",
                chart_type=EntityType.TRACK,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
                    item_id="rss-item-004",
                    chart_id="rss-feed-n3",
                    chart_source="rss_feed",
                    chart_name="网易云喜欢",
                    rank=1,
                    item_type=EntityType.TRACK,
                    target_id="",
                    target_name="Wonderful Tonight",
                    subtitle="Slowhand",
                    provider="rss_feed",
                    source_type="rss_feed/netease_playlist_tracks",
                    target_payload={
                        "family": "netease_playlist_tracks",
                        "title": "Wonderful Tonight",
                        "artist_name": "Eric Clapton",
                        "album_title": "Slowhand",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertTrue(target.conversion_ready)
        self.assertEqual(target.resolution_hints["artist_name"], "Eric Clapton")
        self.assertNotEqual(target.resolution_hints["artist_name"], "Slowhand")

    def test_rss_entry_missing_minimum_hints_is_not_lookup_ready(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-missing",
                chart_source="rss_feed",
                chart_name="Broken RSS",
                chart_type=EntityType.TRACK,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
                    item_id="rss-item-005",
                    chart_id="rss-feed-missing",
                    chart_source="rss_feed",
                    chart_name="Broken RSS",
                    rank=1,
                    item_type=EntityType.TRACK,
                    target_id="",
                    target_name="Unknown",
                    subtitle="Unknown",
                    provider="rss_feed",
                    source_type="rss_feed/netease_playlist_tracks",
                    target_payload={
                        "family": "netease_playlist_tracks",
                        "title": "Unknown",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertFalse(target.conversion_ready)
        self.assertEqual(target.resolution_mode, "search_lookup")
        self.assertIn("title + artist_name", target.conversion_note or "")

    def test_rss_album_missing_album_title_is_not_lookup_ready(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-album-missing",
                chart_source="rss_feed",
                chart_name="Album RSS",
                chart_type=EntityType.ALBUM,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
                    item_id="rss-item-album-missing",
                    chart_id="rss-feed-album-missing",
                    chart_source="rss_feed",
                    chart_name="Album RSS",
                    rank=1,
                    item_type=EntityType.ALBUM,
                    target_id="",
                    target_name="Display Only Album",
                    subtitle="Eric Clapton",
                    provider="rss_feed",
                    source_type="rss_feed/netease_artist_albums",
                    target_payload={
                        "family": "netease_artist_albums",
                        "artist_name": "Eric Clapton",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertFalse(target.conversion_ready)
        self.assertEqual(target.resolution_mode, "search_lookup")
        self.assertIn("album_title + artist_name", target.conversion_note or "")

    def test_rss_artist_missing_artist_name_is_not_lookup_ready(self) -> None:
        detail = ChartDetailData(
            chart=ChartInfo(
                id="rss-feed-artist-missing",
                chart_source="rss_feed",
                chart_name="Artist RSS",
                chart_type=EntityType.ARTIST,
                updated_at=datetime.now(timezone.utc),
                mock=False,
                note="rss",
            ),
            items=[
                ChartEntryInfo(
                    item_id="rss-item-artist-missing",
                    chart_id="rss-feed-artist-missing",
                    chart_source="rss_feed",
                    chart_name="Artist RSS",
                    rank=1,
                    item_type=EntityType.ARTIST,
                    target_id="",
                    target_name="Display Only Artist",
                    subtitle=None,
                    provider="rss_feed",
                    source_type="rss_feed/youtube_top_artists",
                    target_payload={
                        "family": "youtube_top_artists",
                        "provider_origin_id": "UCabc123",
                    },
                    mock=False,
                    note="rss",
                )
            ],
            item_count=1,
            mock=False,
            note="rss",
            integration_point="RssFeedChartProviderAdapter",
        )

        result = DiscoveryAssembler().build_detail(detail)
        target = result.hero_entry.target

        self.assertFalse(target.conversion_ready)
        self.assertEqual(target.resolution_mode, "search_lookup")
        self.assertIn("artist_name", target.conversion_note or "")
