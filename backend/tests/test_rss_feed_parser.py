"""Tests for RSS feed family detection and feed parsing."""

from __future__ import annotations

import unittest

from app.adapters.rss_feed_parser import detect_rss_feed_family, parse_rss_feed
from app.schemas.mvp import EntityType


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

