"""Tests for RSS feed family detection and feed parsing."""

from __future__ import annotations

import unittest

from app.helper.rss_feed_parser import detect_rss_feed_family, parse_rss_feed
from app.schemas.shared import EntityType


NETEASE_PLAYLIST_XML = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Wonderful Tonight - Eric Clapton</title>
      <link>https://music.163.com/#/song?id=100001</link>
      <description><![CDATA[歌曲：Wonderful Tonight<br/>歌手：Eric Clapton<br/>专辑：Slowhand]]></description>
      <pubDate>Mon, 31 Mar 2026 10:30:00 GMT</pubDate>
      <guid>song-100001</guid>
      <enclosure url="https://p1.music.126.net/cover-a.jpg" type="image/jpeg"/>
    </item>
  </channel>
</rss>
"""


class RssFeedParserTest(unittest.TestCase):
    def test_detect_rss_feed_family_maps_netease_playlist(self) -> None:
        family = detect_rss_feed_family("https://rsshub.app/163/music/playlist/9345476")

        self.assertEqual(family, "netease_playlist_tracks")

    def test_detect_rss_feed_family_maps_youtube_top_artists(self) -> None:
        family = detect_rss_feed_family("https://rsshub.app/youtube/charts/TopArtists/us")

        self.assertEqual(family, "youtube_top_artists")

    def test_detect_rss_feed_family_maps_netease_artist_route_to_albums(self) -> None:
        family = detect_rss_feed_family("https://rsshub.app/163/music/artist/6452")

        self.assertEqual(family, "netease_artist_albums")

    def test_parse_netease_playlist_feed_normalizes_track_entry(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/163/music/playlist/9345476",
            NETEASE_PLAYLIST_XML,
        )

        self.assertEqual(parsed["family"], "netease_playlist_tracks")
        self.assertEqual(parsed["chart_type"], EntityType.TRACK)
        self.assertEqual(len(parsed["items"]), 1)
        item = parsed["items"][0]
        self.assertEqual(item["target_name"], "Wonderful Tonight")
        self.assertEqual(item["subtitle"], "Eric Clapton")
        self.assertEqual(item["album_title"], "Slowhand")

    def test_parse_netease_fragment_link_extracts_provider_origin_id_from_link_not_guid(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/163/music/playlist/9345476",
            """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Song A - Artist A</title>
      <link>https://music.163.com/#/song?id=188888</link>
      <description><![CDATA[歌曲：Song A<br/>歌手：Artist A]]></description>
      <guid>guid-should-not-win</guid>
    </item>
  </channel>
</rss>""",
        )

        self.assertEqual(parsed["items"][0]["provider_origin_id"], "188888")

    def test_parse_netease_description_img_extracts_cover_url(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/163/music/playlist/9345476",
            """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>网易云音乐 - 我喜欢的音乐</title>
    <item>
      <title>Song B - Artist B</title>
      <link>https://music.163.com/#/song?id=100002</link>
      <description><![CDATA[<img src="https://p3.music.126.net/cover-from-description.jpg"/><br/>歌曲：Song B<br/>歌手：Artist B]]></description>
    </item>
  </channel>
</rss>""",
        )

        self.assertEqual(
            parsed["items"][0]["cover_url"],
            "https://p3.music.126.net/cover-from-description.jpg",
        )

    def test_parse_youtube_top_songs_preserves_author_as_subtitle_and_raw_context(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/youtube/charts/TopSongs/us",
            """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>YouTube Top Songs</title>
    <item>
      <title>APT.</title>
      <link>https://www.youtube.com/watch?v=abc123xyz00</link>
      <author>ROSÉ &amp; Bruno Mars</author>
    </item>
  </channel>
</rss>""",
        )

        item = parsed["items"][0]
        self.assertEqual(item["subtitle"], "ROSÉ & Bruno Mars")
        self.assertEqual(item["raw_context"]["author"], "ROSÉ & Bruno Mars")

    def test_parse_youtube_top_songs_adds_candidate_hints_from_title_and_author(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/youtube/charts/TopSongs",
            """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>YouTube Top Songs</title>
    <item>
      <title>Lady Gaga, Bruno Mars - Die With A Smile (Official Video)</title>
      <link>https://www.youtube.com/watch?v=abc123xyz00</link>
      <author>Lady Gaga &amp; Bruno Mars</author>
    </item>
  </channel>
</rss>""",
        )

        item = parsed["items"][0]
        self.assertEqual(item["target_name"], "Die With A Smile (Official Video)")
        self.assertEqual(item["subtitle"], "Lady Gaga & Bruno Mars")
        self.assertEqual(
            item["title_candidates"],
            ["Die With A Smile (Official Video)", "Die With A Smile"],
        )
        self.assertEqual(
            item["artist_name_candidates"],
            ["Lady Gaga & Bruno Mars", "Lady Gaga, Bruno Mars"],
        )

    def test_parse_youtube_top_songs_enriches_candidates_for_credit_and_video_noise_variants(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/youtube/charts/TopSongs",
            """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>YouTube Top Songs</title>
    <item>
      <title>Lady Gaga x Bruno Mars - Die With A Smile [Official Lyric Video]</title>
      <link>https://www.youtube.com/watch?v=abc123xyz00</link>
      <author>Lady Gaga feat. Bruno Mars</author>
    </item>
  </channel>
</rss>""",
        )

        item = parsed["items"][0]
        self.assertEqual(
            item["title_candidates"],
            ["Die With A Smile [Official Lyric Video]", "Die With A Smile"],
        )
        self.assertEqual(
            item["artist_name_candidates"],
            ["Lady Gaga feat. Bruno Mars", "Lady Gaga x Bruno Mars", "Lady Gaga & Bruno Mars", "Lady Gaga, Bruno Mars", "Lady Gaga"],
        )

    def test_parse_netease_artist_albums_adds_album_title_candidates_without_promoting_display_only_title(self) -> None:
        parsed = parse_rss_feed(
            "https://rsshub.app/163/music/artist/6452",
            """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>周杰伦</title>
    <item>
      <title>十一月的萧邦 (典藏版)</title>
      <link>https://music.163.com/#/album?id=200002</link>
      <description><![CDATA[专辑：十一月的萧邦<br/>歌手：周杰伦]]></description>
    </item>
  </channel>
</rss>""",
        )

        item = parsed["items"][0]
        self.assertEqual(item["album_title"], "十一月的萧邦")
        self.assertEqual(item["album_title_candidates"], ["十一月的萧邦", "十一月的萧邦 (典藏版)"])
