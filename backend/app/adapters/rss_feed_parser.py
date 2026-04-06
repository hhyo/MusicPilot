"""RSS feed family detection and item normalization helpers."""

from __future__ import annotations

import re
from datetime import timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET

from ..schemas.mvp import EntityType


SUPPORTED_RSS_FEED_FAMILIES = {
    "netease_playlist_tracks",
    "netease_artist_songs",
    "netease_artist_albums",
    "youtube_top_songs",
    "youtube_top_artists",
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_NETEASE_FIELD_RE = re.compile(r"^\s*(歌曲|歌手|专辑)\s*[：:]\s*(.+?)\s*$")


def detect_rss_feed_family(feed_url: str) -> str:
    normalized_path = urlparse(feed_url).path.lower().rstrip("/")
    if "/163/music/playlist" in normalized_path:
        return "netease_playlist_tracks"
    if "/163/music/artist/songs" in normalized_path or "/163/music/artist/song" in normalized_path:
        return "netease_artist_songs"
    if "/163/music/artist/albums" in normalized_path or "/163/music/artist/album" in normalized_path:
        return "netease_artist_albums"
    if "/youtube/charts/topsongs" in normalized_path:
        return "youtube_top_songs"
    if "/youtube/charts/topartists" in normalized_path:
        return "youtube_top_artists"
    raise ValueError(f"Unsupported RSS feed URL family: {feed_url}")


def parse_rss_feed(feed_url: str, feed_xml: str) -> dict[str, Any]:
    family = detect_rss_feed_family(feed_url)
    chart_type = _family_chart_type(family)
    root = ET.fromstring(feed_xml)
    channel = root.find("./channel")
    if channel is None:
        raise ValueError("Invalid RSS payload: missing channel node.")

    chart_name = _text_or_none(channel.find("title")) or family
    normalized_items: list[dict[str, Any]] = []

    for item in channel.findall("item"):
        title = _text_or_none(item.find("title")) or ""
        link = _text_or_none(item.find("link"))
        guid = _text_or_none(item.find("guid"))
        description_raw = _text_or_none(item.find("description")) or ""
        description_text = _normalize_description(description_raw)
        parsed_fields = _extract_description_fields(description_text)
        published_at = _parse_published_at(_text_or_none(item.find("pubDate")))
        cover_url = _extract_cover_url(item)

        target_name, subtitle, album_title = _derive_target_fields(
            family=family,
            title=title,
            parsed_fields=parsed_fields,
        )
        origin_id = _derive_origin_id(link=link, guid=guid)

        normalized_items.append(
            {
                "target_name": target_name,
                "subtitle": subtitle,
                "album_title": album_title,
                "provider_origin_url": link,
                "provider_origin_id": origin_id,
                "cover_url": cover_url,
                "published_at": published_at,
                "family": family,
                "raw_context": {
                    "title": title,
                    "description_text": description_text,
                    "guid": guid,
                    "link": link,
                    "album_title": album_title,
                    "parsed_fields": parsed_fields,
                },
            }
        )

    return {
        "family": family,
        "chart_type": chart_type,
        "chart_name": chart_name,
        "items": normalized_items,
    }


def _family_chart_type(family: str) -> EntityType:
    if family in {"netease_playlist_tracks", "netease_artist_songs", "youtube_top_songs"}:
        return EntityType.TRACK
    if family == "netease_artist_albums":
        return EntityType.ALBUM
    if family == "youtube_top_artists":
        return EntityType.ARTIST
    raise ValueError(f"Unsupported RSS feed family: {family}")


def _normalize_description(raw: str) -> str:
    text = raw.replace("<br/>", "\n").replace("<br />", "\n").replace("<br>", "\n")
    text = _HTML_TAG_RE.sub("", text)
    return unescape(text).strip()


def _extract_description_fields(description_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in description_text.splitlines():
        match = _NETEASE_FIELD_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1)
        value = match.group(2).strip()
        if key == "歌曲":
            fields["track_title"] = value
        elif key == "歌手":
            fields["artist_name"] = value
        elif key == "专辑":
            fields["album_title"] = value
    return fields


def _derive_target_fields(
    *,
    family: str,
    title: str,
    parsed_fields: dict[str, str],
) -> tuple[str, str | None, str | None]:
    if family in {"netease_playlist_tracks", "netease_artist_songs"}:
        track_title, artist_name = _split_title_track_artist(title)
        target_name = parsed_fields.get("track_title") or track_title or title
        subtitle = parsed_fields.get("artist_name") or artist_name
        album_title = parsed_fields.get("album_title")
        return target_name, subtitle, album_title

    if family == "netease_artist_albums":
        return title or parsed_fields.get("album_title") or "Unknown Album", parsed_fields.get("artist_name"), None

    if family == "youtube_top_songs":
        track_title, artist_name = _split_title_track_artist(title)
        return track_title or title, artist_name, None

    if family == "youtube_top_artists":
        return title or "Unknown Artist", None, None

    raise ValueError(f"Unsupported RSS feed family: {family}")


def _split_title_track_artist(title: str) -> tuple[str, str | None]:
    if " - " not in title:
        return title.strip(), None
    left, right = title.split(" - ", 1)
    return left.strip(), right.strip() or None


def _derive_origin_id(*, link: str | None, guid: str | None) -> str:
    if guid:
        return guid.strip()
    if link:
        parsed = urlparse(link)
        query = parse_qs(parsed.query)
        for key in ("id", "v", "list"):
            values = query.get(key)
            if values and values[0]:
                return values[0]
        if parsed.path and parsed.path != "/":
            return parsed.path.strip("/")
        return link
    return ""


def _extract_cover_url(item: ET.Element) -> str | None:
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.attrib.get("url"):
        return enclosure.attrib["url"]

    media_content = item.find("{http://search.yahoo.com/mrss/}content")
    if media_content is not None and media_content.attrib.get("url"):
        return media_content.attrib["url"]

    media_thumbnail = item.find("{http://search.yahoo.com/mrss/}thumbnail")
    if media_thumbnail is not None and media_thumbnail.attrib.get("url"):
        return media_thumbnail.attrib["url"]

    return None


def _parse_published_at(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _text_or_none(node: ET.Element | None) -> str | None:
    if node is None or node.text is None:
        return None
    text = node.text.strip()
    return text or None
