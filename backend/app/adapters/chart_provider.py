"""Adapter boundary for chart and discovery providers used in Phase 4."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from hashlib import sha1
import logging
from time import monotonic, sleep
from typing import Any, Callable
from xml.etree import ElementTree as ET

import httpx

from ..core.runtime_cache import RuntimeTTLCache, stable_cache_key
from .rss_feed_parser import (
    RssFeedParseError,
    UnsupportedRssFeedError,
    detect_rss_feed_family,
    parse_rss_feed,
)
from ..schemas.metadata import MetadataSeedCatalog
from ..schemas.mvp import EntityType
from ..schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo, ChartProviderInfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


CHART_INTEGRATION_POINT = (
    "Replace MockChartProviderAdapter with verified chart provider adapters after the host and external "
    "chart source contracts are validated."
)
CHART_NOTE = "当前榜单数据来自 local seed / mock chart source，不代表已接入真实榜单抓取。"
LISTENBRAINZ_CHART_NOTE = "当前榜单数据来自真实 ListenBrainz sitewide stats。"
LISTENBRAINZ_CHART_INTEGRATION_POINT = "ListenBrainzChartProviderAdapter"
RSS_FEED_CHART_NOTE = "当前榜单数据来自已配置 RSS feed（按 URL family 自动识别）。"
RSS_FEED_CHART_INTEGRATION_POINT = "RssFeedChartProviderAdapter"
logger = logging.getLogger(__name__)


class ChartProviderAdapter(ABC):
    @property
    @abstractmethod
    def provider(self) -> str:
        """Logical provider id."""

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Descriptor for source provenance."""

    @property
    def mock(self) -> bool:
        return True

    @property
    def note(self) -> str:
        return CHART_NOTE

    @property
    def integration_point(self) -> str:
        return CHART_INTEGRATION_POINT

    @abstractmethod
    def list_providers(self) -> list[ChartProviderInfo]:
        """Return available chart sources."""

    @abstractmethod
    def list_charts(self) -> list[ChartInfo]:
        """Return chart catalog."""

    @abstractmethod
    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        """Return a chart with its items."""

    @abstractmethod
    def get_chart_entry(self, chart_id: str, item_id: str) -> ChartEntryInfo:
        """Return a single chart entry for subscription creation."""


class MockChartProviderAdapter(ChartProviderAdapter):
    def __init__(self, catalog: MetadataSeedCatalog):
        self.catalog = catalog
        self._charts = self._build_charts()

    @property
    def provider(self) -> str:
        return self.catalog.provider

    @property
    def source_type(self) -> str:
        return "mock_chart_seed"

    def list_providers(self) -> list[ChartProviderInfo]:
        return [
            ChartProviderInfo(
                id="qq",
                chart_source="qq",
                display_name="QQ Music",
                enabled=True,
                mock=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
            ChartProviderInfo(
                id="netease",
                chart_source="netease",
                display_name="NetEase Cloud Music",
                enabled=True,
                mock=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
            ChartProviderInfo(
                id="bilibili",
                chart_source="bilibili",
                display_name="Bilibili Music",
                enabled=True,
                mock=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
            ChartProviderInfo(
                id="local_mock",
                chart_source="local_mock",
                display_name="Local Mock Discovery",
                enabled=True,
                mock=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
        ]

    def list_charts(self) -> list[ChartInfo]:
        return [detail.chart for detail in self._charts.values()]

    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        try:
            return self._charts[chart_id]
        except KeyError as exc:
            raise KeyError(f"Chart {chart_id} was not found in the mock catalog.") from exc

    def get_chart_entry(self, chart_id: str, item_id: str) -> ChartEntryInfo:
        detail = self.get_chart_detail(chart_id)
        for item in detail.items:
            if item.item_id == item_id:
                return item
        raise KeyError(f"Chart entry {item_id} was not found in chart {chart_id}.")

    def _build_charts(self) -> dict[str, ChartDetailData]:
        artist_map = {artist.id: artist for artist in self.catalog.artists}
        album_map = {album.id: album for album in self.catalog.albums}
        track_map = {track.id: track for track in self.catalog.tracks}

        def chart_detail(
            *,
            chart_id: str,
            source: str,
            name: str,
            chart_type: EntityType,
            region: str,
            category: str,
            refresh_hint: str,
            items: list[ChartEntryInfo],
        ) -> ChartDetailData:
            return ChartDetailData(
                chart=ChartInfo(
                    id=chart_id,
                    chart_source=source,
                    chart_name=name,
                    chart_type=chart_type,
                    region=region,
                    category=category,
                    refresh_hint=refresh_hint,
                    item_count=len(items),
                    updated_at=utc_now(),
                    note=CHART_NOTE,
                ),
                items=items,
                item_count=len(items),
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            )

        charts: dict[str, ChartDetailData] = {}
        charts["chart-qq-hot-tracks"] = chart_detail(
            chart_id="chart-qq-hot-tracks",
            source="qq",
            name="QQ 热门单曲",
            chart_type=EntityType.TRACK,
            region="CN",
            category="hot",
            refresh_hint="daily-placeholder",
            items=[
                ChartEntryInfo(
                    item_id="chartitem-qq-hot-001",
                    chart_id="chart-qq-hot-tracks",
                    chart_source="qq",
                    chart_name="QQ 热门单曲",
                    rank=1,
                    item_type=EntityType.TRACK,
                    target_id="track-hello",
                    target_name=track_map["track-hello"].title,
                    subtitle=track_map["track-hello"].artist_name,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
                ChartEntryInfo(
                    item_id="chartitem-qq-hot-002",
                    chart_id="chart-qq-hot-tracks",
                    chart_source="qq",
                    chart_name="QQ 热门单曲",
                    rank=2,
                    item_type=EntityType.TRACK,
                    target_id="track-anti-hero",
                    target_name=track_map["track-anti-hero"].title,
                    subtitle=track_map["track-anti-hero"].artist_name,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
            ],
        )
        charts["chart-netease-new-albums"] = chart_detail(
            chart_id="chart-netease-new-albums",
            source="netease",
            name="网易云新专上架",
            chart_type=EntityType.ALBUM,
            region="Global",
            category="new",
            refresh_hint="daily-placeholder",
            items=[
                ChartEntryInfo(
                    item_id="chartitem-netease-new-001",
                    chart_id="chart-netease-new-albums",
                    chart_source="netease",
                    chart_name="网易云新专上架",
                    rank=1,
                    item_type=EntityType.ALBUM,
                    target_id="album-hit-me-hard-and-soft",
                    target_name=album_map["album-hit-me-hard-and-soft"].title,
                    subtitle=album_map["album-hit-me-hard-and-soft"].artist_name,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
                ChartEntryInfo(
                    item_id="chartitem-netease-new-002",
                    chart_id="chart-netease-new-albums",
                    chart_source="netease",
                    chart_name="网易云新专上架",
                    rank=2,
                    item_type=EntityType.ALBUM,
                    target_id="album-1989-tv",
                    target_name=album_map["album-1989-tv"].title,
                    subtitle=album_map["album-1989-tv"].artist_name,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
            ],
        )
        charts["chart-bilibili-rising-artists"] = chart_detail(
            chart_id="chart-bilibili-rising-artists",
            source="bilibili",
            name="Bilibili 热门艺人",
            chart_type=EntityType.ARTIST,
            region="Global",
            category="rising",
            refresh_hint="daily-placeholder",
            items=[
                ChartEntryInfo(
                    item_id="chartitem-bilibili-rising-001",
                    chart_id="chart-bilibili-rising-artists",
                    chart_source="bilibili",
                    chart_name="Bilibili 热门艺人",
                    rank=1,
                    item_type=EntityType.ARTIST,
                    target_id="artist-billie-eilish",
                    target_name=artist_map["artist-billie-eilish"].name,
                    subtitle=artist_map["artist-billie-eilish"].country,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
                ChartEntryInfo(
                    item_id="chartitem-bilibili-rising-002",
                    chart_id="chart-bilibili-rising-artists",
                    chart_source="bilibili",
                    chart_name="Bilibili 热门艺人",
                    rank=2,
                    item_type=EntityType.ARTIST,
                    target_id="artist-daft-punk",
                    target_name=artist_map["artist-daft-punk"].name,
                    subtitle=artist_map["artist-daft-punk"].country,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
            ],
        )
        charts["chart-local-editor-picks"] = chart_detail(
            chart_id="chart-local-editor-picks",
            source="local_mock",
            name="Local Mock Editor Picks",
            chart_type=EntityType.TRACK,
            region="Studio",
            category="editor",
            refresh_hint="manual-placeholder",
            items=[
                ChartEntryInfo(
                    item_id="chartitem-local-editor-001",
                    chart_id="chart-local-editor-picks",
                    chart_source="local_mock",
                    chart_name="Local Mock Editor Picks",
                    rank=1,
                    item_type=EntityType.TRACK,
                    target_id="track-get-lucky",
                    target_name=track_map["track-get-lucky"].title,
                    subtitle=track_map["track-get-lucky"].artist_name,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
                ChartEntryInfo(
                    item_id="chartitem-local-editor-002",
                    chart_id="chart-local-editor-picks",
                    chart_source="local_mock",
                    chart_name="Local Mock Editor Picks",
                    rank=2,
                    item_type=EntityType.TRACK,
                    target_id="track-birds-of-a-feather",
                    target_name=track_map["track-birds-of-a-feather"].title,
                    subtitle=track_map["track-birds-of-a-feather"].artist_name,
                    provider=self.catalog.provider,
                    source_type="mock_chart_seed",
                    note=CHART_NOTE,
                ),
            ],
        )
        return charts


class ListenBrainzChartProviderAdapter(ChartProviderAdapter):
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        base_url: str = "https://api.listenbrainz.org",
        user_agent: str = "MusicPilot/0.1.0 (local)",
        timeout_seconds: float = 15.0,
        stats_range: str = "week",
        count: int = 20,
        cache_enabled: bool = True,
        cache_maxsize: int = 256,
        cache_ttl_seconds: int = 900,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"User-Agent": user_agent},
            timeout=timeout_seconds,
        )
        self.stats_range = stats_range
        self.count = count
        self._last_request_at = 0.0
        self._payload_cache = (
            RuntimeTTLCache(
                region="musicpilot_chart_payload",
                maxsize=cache_maxsize,
                ttl=cache_ttl_seconds,
            )
            if cache_enabled
            else None
        )

    @property
    def provider(self) -> str:
        return "listenbrainz"

    @property
    def source_type(self) -> str:
        return "listenbrainz_sitewide_stats"

    @property
    def mock(self) -> bool:
        return False

    @property
    def note(self) -> str:
        return LISTENBRAINZ_CHART_NOTE

    @property
    def integration_point(self) -> str:
        return LISTENBRAINZ_CHART_INTEGRATION_POINT

    def list_providers(self) -> list[ChartProviderInfo]:
        return [
            ChartProviderInfo(
                id=self.provider,
                chart_source=self.provider,
                display_name="ListenBrainz",
                enabled=True,
                mock=False,
                note=self.note,
                integration_point=self.integration_point,
            )
        ]

    def list_charts(self) -> list[ChartInfo]:
        artist_payload = self._get("/1/stats/sitewide/artists")
        track_payload = self._get("/1/stats/sitewide/recordings")
        return [
            self._build_artist_chart(payload=artist_payload),
            self._build_track_chart(payload=track_payload),
        ]

    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        if chart_id == self._artist_chart_id:
            payload = self._get("/1/stats/sitewide/artists")
            return self._build_artist_detail(payload)
        if chart_id == self._track_chart_id:
            payload = self._get("/1/stats/sitewide/recordings")
            return self._build_track_detail(payload)
        raise KeyError(f"Chart {chart_id} was not found in ListenBrainz sitewide stats.")

    def get_chart_entry(self, chart_id: str, item_id: str) -> ChartEntryInfo:
        detail = self.get_chart_detail(chart_id)
        for item in detail.items:
            if item.item_id == item_id:
                return item
        raise KeyError(f"Chart entry {item_id} was not found in chart {chart_id}.")

    @property
    def _artist_chart_id(self) -> str:
        return f"chart-listenbrainz-top-artists-{self.stats_range}"

    @property
    def _track_chart_id(self) -> str:
        return f"chart-listenbrainz-top-tracks-{self.stats_range}"

    def _build_artist_chart(self, payload: dict | None) -> ChartInfo:
        artists = self._dedupe_items((payload or {}).get("artists") or [], id_key="artist_mbid")
        return ChartInfo(
            id=self._artist_chart_id,
            chart_source=self.provider,
            chart_name=f"ListenBrainz 热门艺人（{self.stats_range}）",
            chart_type=EntityType.ARTIST,
            region="Global",
            category="sitewide",
            refresh_hint=f"sitewide-{self.stats_range}",
            item_count=len([item for item in artists if item.get("artist_mbid")]),
            updated_at=self._updated_at(payload),
            mock=False,
            note=self.note,
        )

    def _build_track_chart(self, payload: dict | None) -> ChartInfo:
        recordings = self._dedupe_items((payload or {}).get("recordings") or [], id_key="recording_mbid")
        return ChartInfo(
            id=self._track_chart_id,
            chart_source=self.provider,
            chart_name=f"ListenBrainz 热门单曲（{self.stats_range}）",
            chart_type=EntityType.TRACK,
            region="Global",
            category="sitewide",
            refresh_hint=f"sitewide-{self.stats_range}",
            item_count=len([item for item in recordings if item.get("recording_mbid")]),
            updated_at=self._updated_at(payload),
            mock=False,
            note=self.note,
        )

    def _build_artist_detail(self, payload: dict) -> ChartDetailData:
        items: list[ChartEntryInfo] = []
        for index, item in enumerate(self._dedupe_items(payload.get("artists") or [], id_key="artist_mbid"), start=1):
            artist_mbid = item.get("artist_mbid")
            if not artist_mbid:
                continue
            listen_count = item.get("listen_count")
            subtitle = f"{listen_count} listens" if listen_count is not None else None
            items.append(
                ChartEntryInfo(
                    item_id=f"{self._artist_chart_id}-item-{index:03d}",
                    chart_id=self._artist_chart_id,
                    chart_source=self.provider,
                    chart_name=f"ListenBrainz 热门艺人（{self.stats_range}）",
                    rank=index,
                    item_type=EntityType.ARTIST,
                    target_id=artist_mbid,
                    target_name=item.get("artist_name", artist_mbid),
                    subtitle=subtitle,
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note=self.note,
                )
            )
        return ChartDetailData(
            chart=self._build_artist_chart(payload),
            items=items,
            item_count=len(items),
            mock=False,
            note=self.note,
            integration_point=self.integration_point,
        )

    def _build_track_detail(self, payload: dict) -> ChartDetailData:
        items: list[ChartEntryInfo] = []
        for index, item in enumerate(self._dedupe_items(payload.get("recordings") or [], id_key="recording_mbid"), start=1):
            recording_mbid = item.get("recording_mbid")
            if not recording_mbid:
                continue
            items.append(
                ChartEntryInfo(
                    item_id=f"{self._track_chart_id}-item-{index:03d}",
                    chart_id=self._track_chart_id,
                    chart_source=self.provider,
                    chart_name=f"ListenBrainz 热门单曲（{self.stats_range}）",
                    rank=index,
                    item_type=EntityType.TRACK,
                    target_id=recording_mbid,
                    target_name=item.get("track_name", recording_mbid),
                    subtitle=item.get("artist_name"),
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note=self.note,
                )
            )
        return ChartDetailData(
            chart=self._build_track_chart(payload),
            items=items,
            item_count=len(items),
            mock=False,
            note=self.note,
            integration_point=self.integration_point,
        )

    def _get(self, path: str) -> dict:
        cache_key = stable_cache_key(
            "listenbrainz_payload",
            path=path,
            stats_range=self.stats_range,
            count=self.count,
        )
        if self._payload_cache is not None:
            cached_payload = self._payload_cache.get(cache_key)
            if cached_payload is not None:
                return cached_payload

        self._respect_rate_limit()
        response = self._client.get(
            path,
            params={"count": self.count, "range": self.stats_range},
        )
        response.raise_for_status()
        payload = response.json().get("payload", {})
        normalized_payload = payload if isinstance(payload, dict) else {}
        if self._payload_cache is not None:
            self._payload_cache.set(cache_key, normalized_payload)
        return normalized_payload

    def _respect_rate_limit(self) -> None:
        elapsed = monotonic() - self._last_request_at
        if self._last_request_at and elapsed < 1.0:
            sleep(1.0 - elapsed)
        self._last_request_at = monotonic()

    @staticmethod
    def _updated_at(payload: dict | None) -> datetime:
        last_updated = (payload or {}).get("last_updated")
        if isinstance(last_updated, (int, float)):
            return datetime.fromtimestamp(last_updated, tz=timezone.utc)
        return utc_now()

    @staticmethod
    def _dedupe_items(items: list[dict], *, id_key: str) -> list[dict]:
        deduped: list[dict] = []
        seen: set[str] = set()
        for item in items:
            item_id = item.get(id_key)
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            deduped.append(item)
        return deduped


class RssFeedChartProviderAdapter(ChartProviderAdapter):
    def __init__(
        self,
        *,
        feeds: list[dict[str, Any]] | None = None,
        fetcher: Callable[[str], str] | None = None,
        client: httpx.Client | None = None,
        user_agent: str = "MusicPilot/0.1.0 (local)",
        timeout_seconds: float = 15.0,
        cache_enabled: bool = True,
        cache_maxsize: int = 256,
        cache_ttl_seconds: int = 900,
    ) -> None:
        self.feeds = list(feeds or [])
        self._fetcher = fetcher
        self._client = client or httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=timeout_seconds,
        )
        self._chart_cache = (
            RuntimeTTLCache(
                region="musicpilot_rss_feed_chart_cache",
                maxsize=cache_maxsize,
                ttl=cache_ttl_seconds,
            )
            if cache_enabled
            else None
        )

    @property
    def provider(self) -> str:
        return "rss_feed"

    @property
    def source_type(self) -> str:
        return "rss_feed"

    @property
    def mock(self) -> bool:
        return False

    @property
    def note(self) -> str:
        return RSS_FEED_CHART_NOTE

    @property
    def integration_point(self) -> str:
        return RSS_FEED_CHART_INTEGRATION_POINT

    def list_providers(self) -> list[ChartProviderInfo]:
        return [
            ChartProviderInfo(
                id=self.provider,
                chart_source=self.provider,
                display_name="RSS Feed",
                enabled=True,
                mock=False,
                note=self.note,
                integration_point=self.integration_point,
            )
        ]

    def list_charts(self) -> list[ChartInfo]:
        return [detail.chart for detail in self._load_chart_cache().values()]

    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        chart_cache = self._load_chart_cache()
        try:
            return chart_cache[chart_id]
        except KeyError as exc:
            raise KeyError(f"Chart {chart_id} was not found in configured RSS feeds.") from exc

    def get_chart_entry(self, chart_id: str, item_id: str) -> ChartEntryInfo:
        detail = self.get_chart_detail(chart_id)
        for item in detail.items:
            if item.item_id == item_id:
                return item
        raise KeyError(f"Chart entry {item_id} was not found in chart {chart_id}.")

    def _load_chart_cache(self) -> dict[str, ChartDetailData]:
        cache_key = stable_cache_key("rss_feed_chart_catalog", feeds=self.feeds)
        if self._chart_cache is not None:
            cached = self._chart_cache.get(cache_key)
            if cached is not None:
                return cached

        charts = self._build_chart_cache()
        if self._chart_cache is not None:
            self._chart_cache.set(cache_key, charts)
        return charts

    def _build_chart_cache(self) -> dict[str, ChartDetailData]:
        charts: dict[str, ChartDetailData] = {}
        for feed in self.feeds:
            if not self._feed_enabled(feed):
                continue
            try:
                feed_id = self._feed_id(feed)
                if not feed_id:
                    logger.warning("Skipping RSS feed without id: %s", feed)
                    continue
                url = self._feed_str(feed, "url")
                if not url:
                    logger.warning("Skipping RSS feed %s without url", feed_id)
                    continue
                family = detect_rss_feed_family(url)
                payload = parse_rss_feed(url, self._fetch_feed(url))
                chart_id = self._chart_id(feed_id=feed_id)
                chart_name = self._feed_str(feed, "label") or payload["chart_name"]
                chart_region = self._feed_str(feed, "region") or "Global"
                chart_category = self._feed_str(feed, "category") or family
                items = self._build_entries(
                    feed=feed,
                    chart_id=chart_id,
                    chart_name=chart_name,
                    parsed_items=payload["items"],
                    family=family,
                    chart_type=payload["chart_type"],
                )
                charts[chart_id] = ChartDetailData(
                    chart=ChartInfo(
                        id=chart_id,
                        chart_source=self.provider,
                        chart_name=chart_name,
                        chart_type=payload["chart_type"],
                        region=chart_region,
                        category=chart_category,
                        refresh_hint="rss-feed",
                        item_count=len(items),
                        updated_at=utc_now(),
                        mock=False,
                        note=self.note,
                    ),
                    items=items,
                    item_count=len(items),
                    mock=False,
                    note=self.note,
                    integration_point=self.integration_point,
                )
            except (UnsupportedRssFeedError, RssFeedParseError, ET.ParseError, httpx.HTTPError) as exc:
                logger.warning(
                    "Skipping RSS feed due to parse/fetch issue. feed_id=%s url=%s error=%s",
                    self._feed_id(feed),
                    self._feed_str(feed, "url"),
                    exc,
                )
                continue
        return charts

    def _build_entries(
        self,
        *,
        feed: dict[str, Any],
        chart_id: str,
        chart_name: str,
        parsed_items: list[dict[str, Any]],
        family: str,
        chart_type: EntityType,
    ) -> list[ChartEntryInfo]:
        explicit_seed = self._feed_str(feed, "id")
        if explicit_seed:
            chart_id_seed = explicit_seed
        else:
            url_seed = self._feed_str(feed, "url")
            chart_id_seed = f"rss-{sha1(url_seed.encode('utf-8')).hexdigest()[:10]}"
        entries: list[ChartEntryInfo] = []
        for rank, item in enumerate(parsed_items, start=1):
            target_name = item.get("target_name") or f"{chart_id_seed}-rank-{rank:03d}"
            subtitle = item.get("subtitle")
            if not subtitle and item.get("album_title"):
                subtitle = str(item["album_title"])
            rss_hints: dict[str, Any] = {
                "family": item.get("family"),
                "provider_origin_url": item.get("provider_origin_url"),
                "provider_origin_id": item.get("provider_origin_id"),
                "album_title": item.get("album_title"),
                "cover_url": item.get("cover_url"),
                "published_at": item.get("published_at"),
                "raw_context": item.get("raw_context"),
            }
            if chart_type == EntityType.TRACK:
                rss_hints["title"] = item.get("target_name")
                rss_hints["artist_name"] = item.get("subtitle")
                rss_hints["album_title"] = item.get("album_title")
            elif chart_type == EntityType.ALBUM:
                rss_hints["album_title"] = item.get("album_title")
                rss_hints["artist_name"] = item.get("subtitle")
            elif chart_type == EntityType.ARTIST:
                rss_hints["artist_name"] = target_name
            entries.append(
                ChartEntryInfo(
                    item_id=f"{chart_id_seed}-item-{rank:03d}",
                    chart_id=chart_id,
                    chart_source=self.provider,
                    chart_name=chart_name,
                    rank=rank,
                    item_type=chart_type,
                    target_id="",
                    target_name=target_name,
                    subtitle=subtitle,
                    provider=self.provider,
                    source_type=f"rss_feed/{family}",
                    target_payload=rss_hints,
                    mock=False,
                    note=self.note,
                )
            )
        return entries

    def _fetch_feed(self, url: str) -> str:
        if self._fetcher is not None:
            return self._fetcher(url)
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _feed_str(feed: dict[str, Any], key: str) -> str:
        value = feed.get(key)
        if value is None:
            return ""
        return str(value).strip()

    def _feed_enabled(self, feed: dict[str, Any]) -> bool:
        value = feed.get("enabled")
        if value is None:
            return True
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() not in {"0", "false", "no", "off"}

    def _feed_id(self, feed: dict[str, Any]) -> str:
        return self._feed_str(feed, "id")

    @staticmethod
    def _chart_id(*, feed_id: str) -> str:
        return f"rss-feed-{feed_id}"
