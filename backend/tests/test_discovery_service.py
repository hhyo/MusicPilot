from __future__ import annotations

from datetime import datetime, timezone
from unittest import TestCase

from app.schemas.mvp import EntityType
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo
from app.services.discovery import DiscoveryAssembler
from app.services.music_media_chain import MusicMediaChain


def build_discovery_assembler() -> DiscoveryAssembler:
    chain = MusicMediaChain(metadata_service=object(), metadata_adapter=object())
    return DiscoveryAssembler(music_media_chain=chain)


class DiscoveryAssemblerTests(TestCase):
    def test_non_rss_entry_exposes_direct_music_media_input(self) -> None:
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

        result = build_discovery_assembler().build_detail(detail)

        self.assertIsNotNone(result.hero_entry)
        self.assertTrue(hasattr(result.hero_entry, "media_input"))
        self.assertFalse(hasattr(result.hero_entry, "target"))
        self.assertEqual(
            result.hero_entry.media_input.external_refs["musicbrainz_recording_id"],
            "recording-mbid-001",
        )
        self.assertEqual(result.hero_entry.recognition_assessment.state, "direct")
        self.assertEqual(result.hero_entry.meta_base.entity_type, EntityType.TRACK)
        self.assertEqual(result.recognition_summary["ready"], 1)
        self.assertEqual(result.entry_groups[0].group_key, "tracks")

    def test_rss_track_entry_builds_ready_media_input_payload(self) -> None:
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

        result = build_discovery_assembler().build_detail(detail)
        media_input = result.hero_entry.media_input

        self.assertEqual(result.hero_entry.recognition_assessment.state, "ready")
        self.assertEqual(result.hero_entry.meta_base.canonical_title, "Wonderful Tonight")
        self.assertEqual(media_input.title, "Wonderful Tonight")
        self.assertEqual(media_input.artist_names, ["Eric Clapton"])
        self.assertEqual(media_input.album_title, "Slowhand")
        self.assertEqual(media_input.external_refs["source_url"], "https://music.163.com/#/song?id=100001")
        self.assertEqual(media_input.external_refs["source_id"], "100001")
        self.assertEqual(media_input.source_context["family"], "netease_playlist_tracks")

    def test_rss_album_missing_album_title_is_insufficient(self) -> None:
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
                    target_name="",
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

        result = build_discovery_assembler().build_detail(detail)

        self.assertEqual(result.hero_entry.recognition_assessment.state, "insufficient")
        self.assertIn(
            "canonical_album_title + canonical_artist_names",
            result.hero_entry.recognition_assessment.note or "",
        )
        self.assertEqual(result.recognition_summary["not_ready"], 1)

    def test_rss_artist_entry_builds_ready_media_input_payload(self) -> None:
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

        result = build_discovery_assembler().build_detail(detail)
        media_input = result.hero_entry.media_input

        self.assertEqual(result.hero_entry.recognition_assessment.state, "ready")
        self.assertEqual(result.hero_entry.meta_base.canonical_artist_names, ["Bruno Mars"])
        self.assertEqual(media_input.artist_names, ["Bruno Mars"])
        self.assertEqual(media_input.external_refs["source_id"], "UCabc123")
        self.assertEqual(media_input.external_refs["source_url"], "https://www.youtube.com/channel/UCabc123")
