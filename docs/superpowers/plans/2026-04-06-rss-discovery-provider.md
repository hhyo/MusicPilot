# RSS Discovery Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把结构化 settings 中配置的 RSS feeds 接入为正式 `rss_feed` discovery provider，并让网易云/YouTube family 条目统一通过 `search_lookup` 进入现有 metadata drawer。

**Architecture:** 保持现有 `ChartProviderAdapter -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView` 主链不变，只新增 `RssFeedChartProviderAdapter`、family parser 和 RSS settings 解析。RSS 条目统一走 `DiscoveryTarget.resolution_mode = search_lookup`，前端继续复用现有 discovery 页面和 metadata drawer，不新增 RSS 专属页面。

**Tech Stack:** Python 3.12、FastAPI、Pydantic、httpx、XML parsing、Vue 3、TypeScript、Vitest、unittest

---

## File Structure

- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py`
  - 增加 RSS discovery settings 字段与解析入口
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/rss_feed_parser.py`
  - 负责 family 识别、RSS XML 提取和 item 标准化
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py`
  - 新增 `RssFeedChartProviderAdapter`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
  - 接入 `rss_feed` mode
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/schemas/orchestration.py`
  - 扩展 `ChartEntryInfo` / `DiscoveryTarget` 承载 RSS lookup hints
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/discovery.py`
  - 为 RSS family 生成 `search_lookup` 目标
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/metadata.py`
  - 增加基于 lookup hints 的 metadata 解析入口
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/api/routes/search.py`
  - 增加或复用 metadata lookup 接口
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`
  - 增加 RSS provider tests
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_rss_feed_parser.py`
  - 覆盖 5 个 family 的 RSS 解析
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py`
  - 覆盖 RSS entries 的 `search_lookup`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_metadata_provider.py`
  - 覆盖 metadata lookup by hints
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/types/orchestration.ts`
  - 同步 RSS lookup 相关类型
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/discovery-metadata.ts`
  - 让 `search_lookup` 走真实 metadata lookup，而不是直接抛错
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/metadata.ts`
  - 增加 metadata lookup 请求
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue`
  - 正常渲染 RSS charts / entries
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/__tests__/discovery-metadata.spec.ts`
  - 覆盖 RSS search_lookup 行为
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/__tests__/ChartsView.spec.ts`
  - 覆盖 RSS charts 渲染和 drawer 打开
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`
  - 增加 RSS discovery settings 示例
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
  - 记录 RSS discovery 现状
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
  - 记录 RSS settings 和 family 范围
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`
  - 更新 discovery 路线状态
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/static/index.html`
  - 打包后同步前端产物

## Task 1: 定义 RSS settings 和 family parser 的红测

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_rss_feed_parser.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_rss_feed_parser.py`

- [ ] **Step 1: 先写 family 识别与 feed 解析的 failing tests**

```python
from app.adapters.rss_feed_parser import (
    RssFeedConfigEntry,
    detect_rss_feed_family,
    parse_rss_feed,
)


class RssFeedParserTest(unittest.TestCase):
    def test_detect_netease_playlist_family(self) -> None:
        family = detect_rss_feed_family(
            "https://rsshub.rssforever.com/163/music/playlist/3778678"
        )
        self.assertEqual(family, "netease_playlist_tracks")

    def test_detect_youtube_top_artists_family(self) -> None:
        family = detect_rss_feed_family(
            "https://rsshub.rssforever.com/youtube/charts/TopArtists"
        )
        self.assertEqual(family, "youtube_top_artists")

    def test_parse_netease_playlist_track_feed(self) -> None:
        xml = \"\"\"<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel>
          <title>热歌榜</title>
          <link>https://music.163.com/#/playlist?id=3778678</link>
          <description>网易云音乐歌单 - 热歌榜 - Powered by RSSHub</description>
          <ttl>5</ttl>
          <item>
            <title>拉过勾的 - 陆虎</title>
            <description>歌手：陆虎&lt;br&gt;专辑：花吃泡面男&lt;br&gt; 发行日期：5/7/2013&lt;br&gt; &lt;img src=&quot;https://img&quot;&gt;</description>
            <link>https://music.163.com/song?id=26387325</link>
            <pubDate>Mon, 06 Apr 2026 00:26:49 GMT</pubDate>
            <author>陆虎</author>
          </item>
        </channel></rss>\"\"\"
        config = RssFeedConfigEntry(
            id="netease-hot-tracks",
            label="网易云热歌榜",
            url="https://rsshub.rssforever.com/163/music/playlist/3778678",
            category="hot",
            region="CN",
            enabled=True,
        )

        detail = parse_rss_feed(config, xml)

        self.assertEqual(detail.chart.chart_type, EntityType.TRACK)
        self.assertEqual(detail.chart.chart_source, "rss_feed")
        self.assertEqual(detail.items[0].target_name, "拉过勾的")
        self.assertEqual(detail.items[0].subtitle, "陆虎")
        self.assertEqual(detail.items[0].target_payload["album_title"], "花吃泡面男")
```

- [ ] **Step 2: 跑定向测试确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_rss_feed_parser.py'`

Expected:
- FAIL
- 提示 `rss_feed_parser` 尚不存在或函数未定义

- [ ] **Step 3: 把 RSS provider 红测追加到 chart provider suite**

```python
class RssFeedChartProviderAdapterTest(unittest.TestCase):
    def test_list_charts_returns_configured_rss_charts(self) -> None:
        adapter = RssFeedChartProviderAdapter(
            feeds=[
                RssFeedConfigEntry(
                    id="youtube-top-songs-global",
                    label="YouTube 热门歌曲榜",
                    url="https://rsshub.rssforever.com/youtube/charts/TopSongs",
                    category="hot",
                    region="Global",
                    enabled=True,
                )
            ],
            client=FakeRssClient(
                payloads={
                    "https://rsshub.rssforever.com/youtube/charts/TopSongs": YOUTUBE_TOP_SONGS_XML,
                }
            ),
        )

        result = adapter.list_charts()

        self.assertEqual(result[0].chart_source, "rss_feed")
        self.assertEqual(result[0].chart_type, EntityType.TRACK)
```

- [ ] **Step 4: 跑 chart provider 定向测试确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected:
- FAIL
- 失败点聚焦在 RSS parser/provider 未实现

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_rss_feed_parser.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py
git commit -m "test: add rss discovery provider coverage"
```

## Task 2: 实现 RSS settings、family parser 和 provider

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py`
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/rss_feed_parser.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_rss_feed_parser.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`

- [ ] **Step 1: 增加 settings 红测**

```python
def test_rss_feed_settings_parse_json_entries(self) -> None:
    settings = Settings(
        rss_discovery_feeds_json='[{"id":"netease-hot-tracks","label":"网易云热歌榜","url":"https://rsshub.rssforever.com/163/music/playlist/3778678","category":"hot","region":"CN","enabled":true}]'
    )
    self.assertEqual(settings.rss_discovery_feeds[0].id, "netease-hot-tracks")
```

- [ ] **Step 2: 跑 parser/provider 定向测试确认仍然失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_rss_feed_parser.py'`

Expected:
- FAIL
- 缺少 settings 解析和 parser 实现

- [ ] **Step 3: 实现最小 RSS settings 和 family parser**

```python
# config.py
class RssFeedSettingsEntry(BaseModel):
    id: str
    label: str
    url: str
    category: str | None = None
    region: str | None = None
    enabled: bool = True


class Settings(BaseSettings):
    rss_discovery_feeds_json: str | None = Field(default=None)

    @property
    def rss_discovery_feeds(self) -> list[RssFeedSettingsEntry]:
        if not self.rss_discovery_feeds_json:
            return []
        return [RssFeedSettingsEntry.model_validate(item) for item in json.loads(self.rss_discovery_feeds_json)]
```

```python
# rss_feed_parser.py
def detect_rss_feed_family(url: str) -> str:
    if "/163/music/playlist/" in url:
        return "netease_playlist_tracks"
    if "/163/music/artist/songs/" in url:
        return "netease_artist_songs"
    if "/163/music/artist/" in url:
        return "netease_artist_albums"
    if "/youtube/charts/TopSongs" in url:
        return "youtube_top_songs"
    if "/youtube/charts/TopArtists" in url:
        return "youtube_top_artists"
    raise ValueError(f"Unsupported RSS discovery feed: {url}")
```

```python
def extract_music_163_song_id(url: str) -> str | None:
    match = re.search(r"[?&]id=(\\d+)", url)
    return match.group(1) if match else None
```

```python
def parse_rss_feed(config: RssFeedConfigEntry, xml_text: str) -> ChartDetailData:
    # parse channel/title/description/item
    # family-specific extraction into ChartEntryInfo(target_payload=...)
```

```python
# chart_provider.py
class RssFeedChartProviderAdapter(ChartProviderAdapter):
    provider = "rss_feed"
    source_type = "rss_discovery_feed"
```

- [ ] **Step 4: 跑 parser 和 provider 定向测试确认转绿**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_rss_feed_parser.py'`

Expected:
- PASS

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/rss_feed_parser.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py /Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_rss_feed_parser.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py
git commit -m "feat: add rss discovery chart provider"
```

## Task 3: 让 RSS entries 统一生成 `search_lookup` DiscoveryTarget

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/schemas/orchestration.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/discovery.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py`

- [ ] **Step 1: 先写 RSS discovery target 的 failing tests**

```python
def test_build_target_uses_search_lookup_for_rss_track_entry(self) -> None:
    chart = ChartInfo(
        id="rss-feed-netease-hot-tracks",
        chart_source="rss_feed",
        chart_name="网易云热歌榜",
        chart_type=EntityType.TRACK,
        item_count=1,
        updated_at=datetime.now(timezone.utc),
        mock=False,
        note="rss",
    )
    entry = ChartEntryInfo(
        item_id="entry-1",
        chart_id=chart.id,
        chart_source="rss_feed",
        chart_name=chart.chart_name,
        rank=1,
        item_type=EntityType.TRACK,
        target_id="26387325",
        target_name="拉过勾的",
        subtitle="陆虎",
        provider="rss_feed",
        source_type="rss_discovery_feed",
        mock=False,
        note="rss",
        target_payload={
            "family": "netease_playlist_tracks",
            "album_title": "花吃泡面男",
            "provider_origin_url": "https://music.163.com/song?id=26387325",
            "provider_origin_id": "26387325",
        },
    )

    target = DiscoveryAssembler()._build_target(chart, entry)

    self.assertEqual(target.resolution_mode, "search_lookup")
    self.assertEqual(target.resolution_hints["title"], "拉过勾的")
    self.assertEqual(target.resolution_hints["artist_name"], "陆虎")
    self.assertEqual(target.resolution_hints["album_title"], "花吃泡面男")
```

- [ ] **Step 2: 跑 discovery service 定向测试确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_discovery_service.py'`

Expected:
- FAIL
- 缺少 RSS search_lookup target 构造

- [ ] **Step 3: 实现最小 RSS target 生成**

```python
# orchestration.py
class ChartEntryInfo(BaseModel):
    ...
    target_payload: dict[str, str] = Field(default_factory=dict)


class DiscoveryTarget(BaseModel):
    ...
    resolution_mode: str = "direct_id"
    resolution_hints: dict[str, str] = Field(default_factory=dict)
```

```python
# discovery.py
if entry.provider == "rss_feed":
    payload = dict(entry.target_payload or {})
    hints = {
        "provider_origin_url": payload.get("provider_origin_url", ""),
        "provider_origin_id": payload.get("provider_origin_id", provider_id),
        "family": payload.get("family", ""),
    }
    if entry.item_type == EntityType.TRACK:
        hints["title"] = entry.target_name
        if entry.subtitle:
            hints["artist_name"] = entry.subtitle
        if payload.get("album_title"):
            hints["album_title"] = payload["album_title"]
    elif entry.item_type == EntityType.ALBUM:
        hints["album_title"] = entry.target_name
        if entry.subtitle:
            hints["artist_name"] = entry.subtitle
    else:
        hints["artist_name"] = entry.target_name

    return DiscoveryTarget(
        ...,
        resolution_mode="search_lookup",
        resolution_hints={k: v for k, v in hints.items() if v},
    )
```

- [ ] **Step 4: 跑定向测试确认转绿**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_discovery_service.py'`

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/schemas/orchestration.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/discovery.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py
git commit -m "feat: add rss discovery search lookup targets"
```

## Task 4: 让 metadata drawer 真正支持 RSS `search_lookup`

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/metadata.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/api/routes/search.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_metadata_provider.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/metadata.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/discovery-metadata.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/__tests__/discovery-metadata.spec.ts`

- [ ] **Step 1: 写 lookup API 的 failing tests**

```python
def test_lookup_track_detail_by_hints_uses_metadata_search(self) -> None:
    adapter = FakeMetadataAdapter(...)
    service = MetadataService(session=session, adapter=adapter)

    result = service.lookup_detail(
        entity_type=EntityType.TRACK,
        hints={"title": "Hello", "artist_name": "Adele", "album_title": "25"},
    )

    self.assertEqual(result.entity_type, EntityType.TRACK)
```

```ts
it('uses metadata lookup for search_lookup targets', async () => {
  const target: DiscoveryTarget = {
    target_kind: 'track',
    provider: 'rss_feed',
    provider_id: '26387325',
    display_title: '拉过勾的',
    display_subtitle: '陆虎',
    source_context: {
      chart_source: 'rss_feed',
      chart_id: 'rss-feed-netease-hot-tracks',
      chart_name: '网易云热歌榜',
      rank: 1,
      chart_type: 'track',
    },
    conversion_ready: true,
    conversion_note: null,
    discovery_badges: ['hot', 'tracks'],
    resolution_mode: 'search_lookup',
    resolution_hints: {
      title: '拉过勾的',
      artist_name: '陆虎',
      album_title: '花吃泡面男',
    },
  };

  await fetchDiscoveryTargetDetail(target);
  expect(fetchMetadataDetailByLookup).toHaveBeenCalled();
});
```

- [ ] **Step 2: 跑 backend/frontend 定向测试确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_metadata_provider.py'`

Expected:
- FAIL

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run src/services/__tests__/discovery-metadata.spec.ts`

Expected:
- FAIL

- [ ] **Step 3: 实现最小 lookup 路径**

```python
# metadata.py
def lookup_detail(self, *, entity_type: EntityType, hints: dict[str, str]) -> MetadataDetail:
    keyword = " ".join(
        part for part in [
            hints.get("artist_name"),
            hints.get("album_title") if entity_type == EntityType.ALBUM else None,
            hints.get("title") if entity_type == EntityType.TRACK else None,
        ] if part
    ).strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="Metadata lookup requires at least one hint.")
    result = self.search(MetadataSearchRequest(keyword=keyword, type=entity_type, page=1, page_size=1))
    if not result.items:
        raise HTTPException(status_code=404, detail="Metadata lookup found no matching item.")
    return self.get_detail(entity_type, result.items[0].id)
```

```python
# search.py
@router.post("/metadata/lookup", summary="Metadata lookup by discovery hints")
def metadata_lookup(...):
    detail = service.lookup_detail(entity_type=payload.entity_type, hints=payload.hints)
```

```ts
// metadata.ts
export async function fetchMetadataDetailByLookup(
  entityType: EntityType,
  hints: Record<string, string>,
) {
  return apiPost<ApiResponse<MetadataDetail>>('/metadata/lookup', {
    entity_type: entityType,
    hints,
  });
}
```

```ts
// discovery-metadata.ts
if (target.resolution_mode === 'search_lookup') {
  return fetchMetadataDetailByLookup(target.target_kind, target.resolution_hints);
}
```

- [ ] **Step 4: 跑定向测试确认转绿**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_metadata_provider.py'`

Expected:
- PASS

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run src/services/__tests__/discovery-metadata.spec.ts`

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/metadata.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/api/routes/search.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_metadata_provider.py /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/metadata.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/discovery-metadata.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/__tests__/discovery-metadata.spec.ts
git commit -m "feat: add metadata lookup for rss discovery"
```

## Task 5: 前端渲染 RSS charts，并收口文档与验证

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/types/orchestration.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/__tests__/ChartsView.spec.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`

- [ ] **Step 1: 先写前端 RSS charts 的 failing test**

```ts
it('renders rss discovery chart and opens metadata drawer through lookup', async () => {
  // mock fetchCharts/fetchChartDetail 返回 rss_feed chart + rss entry
  // mock fetchMetadataDetailByLookup 返回 metadata detail
  // 点击条目后断言 drawer 标题出现
});
```

- [ ] **Step 2: 跑前端定向测试确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run src/views/__tests__/ChartsView.spec.ts`

Expected:
- FAIL
- RSS chart 渲染或 lookup drawer 流程未完成

- [ ] **Step 3: 实现最小前端兼容**

```ts
// orchestration.ts
export interface ChartEntryInfo {
  ...
  target_payload: Record<string, string>;
}
```

```vue
<!-- ChartsView.vue -->
<p class="entry-card__conversion">
  {{
    item.target.resolution_mode === 'search_lookup'
      ? 'metadata lookup ready'
      : item.target.conversion_ready
        ? 'metadata ready'
        : item.target.conversion_note || 'metadata pending'
  }}
</p>
```

```md
# README / backend README / .env.example
- discovery 新增 `rss_feed` provider
- 支持 5 个 family
- RSS entries 通过 metadata lookup 下钻
```

- [ ] **Step 4: 跑全量验证**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected:
- PASS

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run`

Expected:
- PASS

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected:
- PASS

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected:
- PASS

- [ ] **Step 5: API smoke**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print("/openapi.json", client.get("/openapi.json").status_code)
print("/docs", client.get("/docs").status_code)
print("/api/v1/plugin/musicpilot/charts", client.get("/api/v1/plugin/musicpilot/charts").status_code)
PY
```

Expected:
- `/openapi.json 200`
- `/docs 200`
- `/api/v1/plugin/musicpilot/charts 200`

- [ ] **Step 6: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/types/orchestration.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/__tests__/ChartsView.spec.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example /Users/lihuanhuan/PycharmProjects/MusicPilot/README.md /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md
git commit -m "feat: add rss discovery provider"
```

## Self-Review

### Spec Coverage

- `rss_feed` 正式 provider：Task 2
- 5 个 family 支持：Task 1 + Task 2
- settings 配置入口：Task 2
- RSS entries 统一 `search_lookup`：Task 3
- metadata drawer 下钻：Task 4
- 前端渲染与文档收口：Task 5

### Placeholder Scan

- 无 `TODO` / `TBD` / “implement later”
- 每个任务都给了具体文件、测试命令和最小代码形态

### Type Consistency

- provider 名称统一为 `rss_feed`
- family 名称统一为：
  - `netease_playlist_tracks`
  - `netease_artist_songs`
  - `netease_artist_albums`
  - `youtube_top_songs`
  - `youtube_top_artists`
- RSS entries 统一走 `resolution_mode = search_lookup`

