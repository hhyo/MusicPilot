"""RSS feed family detection and item normalization helpers."""

from __future__ import annotations

import re
from datetime import timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET

from ..schemas.shared import EntityType


SUPPORTED_RSS_FEED_FAMILIES = {
    "netease_playlist_tracks",
    "netease_artist_songs",
    "netease_artist_albums",
    "youtube_top_songs",
    "youtube_top_artists",
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_NETEASE_FIELD_RE = re.compile(r"^\s*(歌曲|歌手|专辑)\s*[：:]\s*(.+?)\s*$")
_IMG_SRC_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.IGNORECASE)


class UnsupportedRssFeedError(ValueError):
    """Raised when feed URL does not match supported RSS families."""


class RssFeedParseError(ValueError):
    """Raised when RSS XML shape is invalid for supported feeds."""


def detect_rss_feed_family(feed_url: str) -> str:
    normalized_path = urlparse(feed_url).path.lower().rstrip("/")
    if "/163/music/playlist" in normalized_path:
        return "netease_playlist_tracks"
    if "/163/music/artist/songs" in normalized_path or "/163/music/artist/song" in normalized_path:
        return "netease_artist_songs"
    if re.match(r"^/163/music/artist/\d+$", normalized_path):
        return "netease_artist_albums"
    if "/163/music/artist/albums" in normalized_path or "/163/music/artist/album" in normalized_path:
        return "netease_artist_albums"
    if "/youtube/charts/topsongs" in normalized_path:
        return "youtube_top_songs"
    if "/youtube/charts/topartists" in normalized_path:
        return "youtube_top_artists"
    raise UnsupportedRssFeedError(f"Unsupported RSS feed URL family: {feed_url}")


def parse_rss_feed(feed_url: str, feed_xml: str) -> dict[str, Any]:
    family = detect_rss_feed_family(feed_url)
    chart_type = _family_chart_type(family)
    root = ET.fromstring(feed_xml)
    channel = root.find("./channel")
    if channel is None:
        raise RssFeedParseError("Invalid RSS payload: missing channel node.")

    chart_name = _text_or_none(channel.find("title")) or family
    normalized_items: list[dict[str, Any]] = []

    for item in channel.findall("item"):
        title = _text_or_none(item.find("title")) or ""
        link = _text_or_none(item.find("link"))
        guid = _text_or_none(item.find("guid"))
        author = _text_or_none(item.find("author"))
        description_raw = _text_or_none(item.find("description")) or ""
        description_text = _normalize_description(description_raw)
        parsed_fields = _extract_description_fields(description_text)
        published_at = _parse_published_at(_text_or_none(item.find("pubDate")))
        cover_url = _extract_cover_url(item, description_raw)

        target_name, subtitle, album_title = _derive_target_fields(
            family=family,
            title=title,
            author=author,
            parsed_fields=parsed_fields,
        )
        candidate_hints = _build_candidate_hints(
            family=family,
            title=title,
            author=author,
            target_name=target_name,
            subtitle=subtitle,
            album_title=album_title,
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
                    "author": author,
                    "album_title": album_title,
                    "parsed_fields": parsed_fields,
                },
                **candidate_hints,
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
    author: str | None,
    parsed_fields: dict[str, str],
) -> tuple[str, str | None, str | None]:
    if family in {"netease_playlist_tracks", "netease_artist_songs"}:
        track_title, artist_name = _split_title_track_artist(title)
        target_name = parsed_fields.get("track_title") or track_title or title
        subtitle = parsed_fields.get("artist_name") or artist_name
        album_title = parsed_fields.get("album_title")
        return target_name, subtitle, album_title

    if family == "netease_artist_albums":
        target_name = title or parsed_fields.get("album_title") or "Unknown Album"
        return target_name, parsed_fields.get("artist_name"), parsed_fields.get("album_title")

    if family == "youtube_top_songs":
        track_title, artist_name = _derive_youtube_song_fields(title=title, author=author)
        return track_title or title, artist_name, None

    if family == "youtube_top_artists":
        return title or "Unknown Artist", None, None

    raise ValueError(f"Unsupported RSS feed family: {family}")


def _split_title_track_artist(title: str) -> tuple[str, str | None]:
    if " - " not in title:
        return title.strip(), None
    left, right = title.split(" - ", 1)
    return left.strip(), right.strip() or None


def _derive_youtube_song_fields(*, title: str, author: str | None) -> tuple[str, str | None]:
    track_title, split_artist = _split_title_track_artist(title)
    if " - " not in title:
        return title.strip(), author or split_artist

    left, right = title.split(" - ", 1)
    left = left.strip()
    right = right.strip()
    author_clean = (author or "").strip()

    if author_clean and _normalized_artist_credit_text(left) == _normalized_artist_credit_text(author_clean):
        return right or title.strip(), author_clean
    if author_clean and _normalized_artist_credit_text(right) == _normalized_artist_credit_text(author_clean):
        return left or title.strip(), author_clean
    return track_title or title.strip(), author or split_artist


def _derive_origin_id(*, link: str | None, guid: str | None) -> str:
    if link:
        linked_id = _extract_origin_id_from_link(link)
        if linked_id:
            return linked_id
    if guid:
        return guid.strip()
    return ""


def _extract_origin_id_from_link(link: str) -> str | None:
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    fragment_query: dict[str, list[str]] = {}
    if parsed.fragment and "?" in parsed.fragment:
        _, _, frag_query = parsed.fragment.partition("?")
        fragment_query = parse_qs(frag_query)

    for params in (query, fragment_query):
        for key in ("id", "v", "list"):
            values = params.get(key)
            if values and values[0]:
                return values[0]

    if parsed.path and parsed.path != "/":
        return parsed.path.strip("/")
    if parsed.fragment and parsed.fragment != "/":
        fragment_path = parsed.fragment.split("?", 1)[0].strip("/")
        if fragment_path:
            return fragment_path
    return None


def _build_candidate_hints(
    *,
    family: str,
    title: str,
    author: str | None,
    target_name: str,
    subtitle: str | None,
    album_title: str | None,
    parsed_fields: dict[str, str],
) -> dict[str, list[str]]:
    if family in {"netease_playlist_tracks", "netease_artist_songs"}:
        return {
            "title_candidates": _dedupe_candidates(parsed_fields.get("track_title"), target_name),
            "artist_name_candidates": _dedupe_candidates(parsed_fields.get("artist_name"), subtitle, author),
            "album_title_candidates": _dedupe_candidates(parsed_fields.get("album_title"), album_title),
        }

    if family == "netease_artist_albums":
        structured_album = parsed_fields.get("album_title")
        candidates = _dedupe_candidates(structured_album)
        if structured_album and target_name and target_name != structured_album:
            candidates = _dedupe_candidates(*candidates, target_name)
        return {
            "album_title_candidates": candidates,
            "artist_name_candidates": _dedupe_candidates(parsed_fields.get("artist_name"), subtitle, author),
        }

    if family == "youtube_top_songs":
        left, right = _split_title_track_artist(title)
        author_clean = (author or "").strip()
        artist_candidates = _build_artist_credit_candidates(subtitle, author_clean, left)
        return {
            "title_candidates": _build_title_candidates(target_name, right if right != target_name else None),
            "artist_name_candidates": artist_candidates,
        }

    if family == "youtube_top_artists":
        return {
            "artist_name_candidates": _dedupe_candidates(target_name, author),
        }

    return {}


def _dedupe_candidates(*values: str | None) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if not normalized:
            continue
        key = _normalized_music_text(normalized)
        if not key or key in seen:
            continue
        candidates.append(normalized)
        seen.add(key)
    return candidates


def _build_title_candidates(*values: str | None) -> list[str]:
    candidates: list[str] = []
    for value in values:
        if not value:
            continue
        stripped = _strip_video_suffix(value)
        candidates.extend(_dedupe_candidates(value, stripped))
    return _dedupe_candidates(*candidates)


def _build_artist_credit_candidates(*values: str | None) -> list[str]:
    candidates: list[str] = []
    tokens: list[str] = []
    allow_primary_fallback = False
    for value in values:
        if not value:
            continue
        normalized_value = value.strip()
        if normalized_value:
            candidates.append(normalized_value)
        if re.search(r"\b(featuring|feat\.?|ft\.?|with)\b|\sx\s", normalized_value, flags=re.IGNORECASE):
            allow_primary_fallback = True
        parts = _split_artist_credit_parts_display(normalized_value)
        for part in parts:
            if _normalized_music_text(part) not in {_normalized_music_text(token) for token in tokens}:
                tokens.append(part)

    if len(tokens) >= 2:
        candidates.extend(
            [
                " & ".join(tokens),
                ", ".join(tokens),
            ]
        )
        if allow_primary_fallback:
            candidates.append(tokens[0])
    elif tokens:
        candidates.append(tokens[0])
    return _dedupe_candidates(*candidates)


def _split_artist_credit_parts_display(value: str | None) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []
    text = re.sub(r"\b(featuring|feat\.?|ft\.?|with)\b", ",", text, flags=re.IGNORECASE)
    text = text.replace("&", ",")
    text = re.sub(r"\band\b", ",", text, flags=re.IGNORECASE)
    text = text.replace("/", ",")
    text = re.sub(r"\sx\s", ",", text, flags=re.IGNORECASE)
    parts = [part.strip(" .-_") for part in text.split(",")]
    return [part for part in parts if part]


def _normalized_music_text(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[‐‑‒–—−]+", " ", text)
    text = re.sub(r"[“”\"'`]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalized_artist_credit_text(value: str) -> str:
    text = _normalized_music_text(value)
    text = re.sub(r"\b(featuring|feat\.?|ft\.?|with)\b", ",", text)
    text = text.replace("&", ",")
    text = re.sub(r"\band\b", ",", text)
    text = text.replace("/", ",").replace(" x ", ",")
    parts = [part.strip(" .-_") for part in text.split(",")]
    parts = [part for part in parts if part]
    return ",".join(parts)


def _strip_video_suffix(value: str) -> str | None:
    if not value:
        return None
    stripped = re.sub(
        r"\s*[\(\[]\s*(?:official\s+)?(?:video|audio|mv|lyrics?|lyric video|performance)\s*[\)\]]\s*$",
        "",
        value,
        flags=re.IGNORECASE,
    ).strip()
    return stripped or None


def _extract_cover_url(item: ET.Element, description_raw: str) -> str | None:
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.attrib.get("url"):
        return enclosure.attrib["url"]

    img_match = _IMG_SRC_RE.search(description_raw or "")
    if img_match:
        return img_match.group(1)

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
