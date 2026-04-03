"""Adapter boundary for chart and discovery providers used in Phase 4."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

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


class ChartProviderAdapter(ABC):
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

    def list_providers(self) -> list[ChartProviderInfo]:
        return [
            ChartProviderInfo(
                id="qq",
                chart_source="qq",
                display_name="QQ Music",
                enabled=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
            ChartProviderInfo(
                id="netease",
                chart_source="netease",
                display_name="NetEase Cloud Music",
                enabled=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
            ChartProviderInfo(
                id="bilibili",
                chart_source="bilibili",
                display_name="Bilibili Music",
                enabled=True,
                note=CHART_NOTE,
                integration_point=CHART_INTEGRATION_POINT,
            ),
            ChartProviderInfo(
                id="local_mock",
                chart_source="local_mock",
                display_name="Local Mock Discovery",
                enabled=True,
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
