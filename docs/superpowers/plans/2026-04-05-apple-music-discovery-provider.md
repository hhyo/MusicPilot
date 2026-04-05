# Apple Music Discovery Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 discovery 产品化结构上接入 Apple Music 官方 songs/albums 榜单，并把 `DiscoveryTarget` 升级成可同时支持 `direct_id` 与 `search_lookup` 的稳定转化契约。

**Architecture:** 保持现有 `ChartProviderAdapter -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView` 主链不变，只新增 Apple Music provider、最小配置和 `DiscoveryTarget` 解析模式扩展。Apple Music 榜单项先通过 `search_lookup` 模式进入统一 discovery 视图，不在这一轮实现 metadata drawer 的 lookup 落地。

**Tech Stack:** Python 3.12、FastAPI、Pydantic、httpx、Vue 3、TypeScript、Vitest、unittest

---

## File Structure

- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py`
  - 增加 Apple Music chart provider 配置项
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py`
  - 新增 `AppleMusicChartProviderAdapter`
  - 复用现有 runtime cache
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
  - 在 chart provider 选择逻辑中接入 Apple Music
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/schemas/orchestration.py`
  - 扩展 `DiscoveryTarget` 契约
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/discovery.py`
  - 支持 `direct_id` / `search_lookup`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`
  - 增加 Apple Music provider tests
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py`
  - 增加 discovery target resolution mode tests
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/types/orchestration.ts`
  - 同步 `DiscoveryTarget` 新字段
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/discovery-metadata.ts`
  - 为后续 lookup 模式预留显式错误/分支
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue`
  - 展示 Apple Music chart 和 lookup-ready 提示
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/__tests__/discovery-metadata.spec.ts`
  - 增加 resolution mode 行为测试
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/__tests__/ChartsView.spec.ts`
  - 增加 Apple chart 渲染测试
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`
  - 增加 Apple Music chart provider 配置示例
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
  - 更新 discovery provider 状态
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
  - 更新 backend provider 配置说明
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`
  - 更新 discovery 阶段状态
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/static/index.html`
  - 打包后同步前端产物

## Task 1: 先把 Apple Music provider 的后端测试写红

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`

- [ ] **Step 1: 写 Apple Music chart provider 的 failing tests**

```python
class AppleMusicFakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class AppleMusicFakeClient:
    def __init__(self, payloads: dict[str, dict]):
        self.payloads = payloads
        self.calls: list[tuple[str, dict | None, dict | None]] = []

    def get(self, path: str, params: dict | None = None, headers: dict | None = None) -> AppleMusicFakeResponse:
        self.calls.append((path, params, headers))
        return AppleMusicFakeResponse(self.payloads[path])


class AppleMusicChartProviderAdapterTest(unittest.TestCase):
    def test_list_charts_returns_song_and_album_chart(self) -> None:
        adapter = AppleMusicChartProviderAdapter(
            storefront="us",
            developer_token="token",
            client=AppleMusicFakeClient(
                payloads={
                    "/v1/catalog/us/charts": {
                        "results": {
                            "songs": [{"data": [{"id": "song-chart", "type": "charts", "attributes": {"name": "Top Songs"}}]}],
                            "albums": [{"data": [{"id": "album-chart", "type": "charts", "attributes": {"name": "Top Albums"}}]}],
                        }
                    },
                    "/v1/catalog/us/charts/song-chart": {
                        "data": [{"id": "song-chart", "type": "charts", "attributes": {"name": "Top Songs"}, "relationships": {"songs": {"data": [{"id": "apple-song-1", "type": "songs"}]}}}],
                        "included": [{"id": "apple-song-1", "type": "songs", "attributes": {"name": "Hello", "artistName": "Adele", "albumName": "25", "isrc": "GBBKS1500210"}}],
                    },
                    "/v1/catalog/us/charts/album-chart": {
                        "data": [{"id": "album-chart", "type": "charts", "attributes": {"name": "Top Albums"}, "relationships": {"albums": {"data": [{"id": "apple-album-1", "type": "albums"}]}}}],
                        "included": [{"id": "apple-album-1", "type": "albums", "attributes": {"name": "25", "artistName": "Adele", "upc": "888430999999"}}],
                    },
                }
            ),
        )

        charts = adapter.list_charts()

        self.assertEqual([item.chart_type for item in charts], [EntityType.TRACK, EntityType.ALBUM])
        self.assertEqual([item.chart_source for item in charts], ["apple_music", "apple_music"])

    def test_song_chart_detail_maps_search_lookup_hints(self) -> None:
        adapter = AppleMusicChartProviderAdapter(
            storefront="us",
            developer_token="token",
            client=AppleMusicFakeClient(
                payloads={
                    "/v1/catalog/us/charts": {
                        "results": {
                            "songs": [{"data": [{"id": "song-chart", "type": "charts", "attributes": {"name": "Top Songs"}}]}],
                            "albums": [],
                        }
                    },
                    "/v1/catalog/us/charts/song-chart": {
                        "data": [{"id": "song-chart", "type": "charts", "attributes": {"name": "Top Songs"}, "relationships": {"songs": {"data": [{"id": "apple-song-1", "type": "songs"}]}}}],
                        "included": [{"id": "apple-song-1", "type": "songs", "attributes": {"name": "Hello", "artistName": "Adele", "albumName": "25", "isrc": "GBBKS1500210"}}],
                    },
                }
            ),
        )

        detail = adapter.get_chart_detail("chart-apple-music-top-songs-us")

        self.assertEqual(detail.items[0].target_id, "apple-song-1")
        self.assertEqual(detail.items[0].item_type, EntityType.TRACK)
        self.assertEqual(detail.items[0].target_name, "Hello")
        self.assertEqual(detail.items[0].subtitle, "Adele")
```

- [ ] **Step 2: 跑后端定向测试，确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected:
- FAIL
- 报 `AppleMusicChartProviderAdapter` 未定义，或 Apple Music chart 映射未实现

- [ ] **Step 3: 写最小 Apple provider 测试基线**

```python
# 在现有 test_chart_provider.py 中追加 AppleMusicFakeResponse / AppleMusicFakeClient
# 再追加 AppleMusicChartProviderAdapterTest 两个用例：
# 1. list_charts 返回 song + album
# 2. get_chart_detail 能输出标准 ChartDetailData
```

- [ ] **Step 4: 再跑一次定向测试，确认仍然是红测且失败点聚焦在实现缺失**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected:
- FAIL
- 失败点集中在 provider 未实现，不是测试环境错误

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py
git commit -m "test: add apple music chart provider coverage"
```

## Task 2: 实现 Apple Music chart provider 和配置接入

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`

- [ ] **Step 1: 在配置层先写 Apple Music 字段的 failing smoke**

```python
def test_get_chart_provider_adapter_returns_apple_provider_when_mode_is_apple_music(self) -> None:
    with patch("app.core.dependencies.settings.chart_provider_mode", "apple_music"), \
         patch("app.core.dependencies.settings.chart_apple_music_storefront", "us"), \
         patch("app.core.dependencies.settings.chart_apple_music_developer_token", "token"):
        adapter = get_chart_provider_adapter.__wrapped__()
        self.assertEqual(adapter.provider, "apple_music")
```

- [ ] **Step 2: 跑 chart/provider 相关测试，确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected:
- FAIL
- 缺少 Apple mode/config/provider 分支

- [ ] **Step 3: 实现最小 Apple Music provider**

```python
class AppleMusicChartProviderAdapter(ChartProviderAdapter):
    def __init__(
        self,
        *,
        storefront: str,
        developer_token: str,
        base_url: str = "https://api.music.apple.com",
        user_agent: str = "MusicPilot/0.1.0 (local)",
        timeout_seconds: float = 15.0,
        count: int = 20,
        cache_enabled: bool = True,
        cache_maxsize: int = 256,
        cache_ttl_seconds: int = 900,
        client: httpx.Client | None = None,
    ) -> None:
        self.storefront = storefront
        self.developer_token = developer_token
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.count = count
        self._client = client or httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds, headers={
            "Authorization": f"Bearer {self.developer_token}",
            "User-Agent": self.user_agent,
        })
        self._cache = RuntimeTTLCache(maxsize=cache_maxsize, ttl_seconds=cache_ttl_seconds, enabled=cache_enabled)
```

```python
def list_providers(self) -> list[ChartProviderInfo]:
    return [
        ChartProviderInfo(
            id="apple_music",
            chart_source="apple_music",
            display_name="Apple Music",
            enabled=bool(self.developer_token and self.storefront),
            mock=False,
            note="当前榜单数据来自 Apple Music 官方 charts。",
            integration_point="AppleMusicChartProviderAdapter",
        )
    ]
```

```python
# config.py
chart_apple_music_base_url: str = Field(default="https://api.music.apple.com")
chart_apple_music_storefront: str | None = Field(default=None)
chart_apple_music_developer_token: str | None = Field(default=None)
chart_apple_music_count: int = Field(default=20, ge=1, le=100)
```

```python
# dependencies.py
if settings.chart_provider_mode == "apple_music":
    return AppleMusicChartProviderAdapter(
        base_url=settings.chart_apple_music_base_url,
        storefront=settings.chart_apple_music_storefront or "",
        developer_token=settings.chart_apple_music_developer_token or "",
        user_agent=settings.chart_provider_user_agent,
        timeout_seconds=settings.chart_provider_timeout_seconds,
        count=settings.chart_apple_music_count,
        cache_enabled=settings.chart_cache_enabled,
        cache_maxsize=settings.chart_cache_maxsize,
        cache_ttl_seconds=settings.chart_cache_ttl_seconds,
    )
```

- [ ] **Step 4: 跑定向测试，确认 provider 实现转绿**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected:
- PASS
- Apple Music provider tests 通过

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py /Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py
git commit -m "feat: add apple music chart provider"
```

## Task 3: 升级 DiscoveryTarget 契约并保持 ListenBrainz 兼容

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/schemas/orchestration.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/discovery.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py`

- [ ] **Step 1: 先写 discovery target resolution-mode 的 failing tests**

```python
def test_build_target_uses_direct_id_for_musicbrainz_entries(self) -> None:
    chart = ChartInfo(
        id="chart-listenbrainz-top-tracks-week",
        chart_source="listenbrainz",
        chart_name="Top Tracks",
        chart_type=EntityType.TRACK,
        item_count=1,
        updated_at=datetime.now(timezone.utc),
        mock=False,
        note="live",
    )
    entry = ChartEntryInfo(
        item_id="entry-1",
        chart_id=chart.id,
        chart_source="listenbrainz",
        chart_name=chart.chart_name,
        rank=1,
        item_type=EntityType.TRACK,
        target_id="recording-123",
        target_name="Hello",
        subtitle="Adele",
        provider="musicbrainz",
        source_type="listenbrainz_sitewide_stats",
        mock=False,
        note="live",
    )

    target = DiscoveryAssembler()._build_target(chart, entry)

    self.assertEqual(target.resolution_mode, "direct_id")
    self.assertEqual(target.provider_id, "recording-123")
```

```python
def test_build_target_uses_search_lookup_for_apple_entries(self) -> None:
    chart = ChartInfo(
        id="chart-apple-music-top-songs-us",
        chart_source="apple_music",
        chart_name="Top Songs",
        chart_type=EntityType.TRACK,
        item_count=1,
        updated_at=datetime.now(timezone.utc),
        mock=False,
        note="live",
    )
    entry = ChartEntryInfo(
        item_id="entry-apple-song-1",
        chart_id=chart.id,
        chart_source="apple_music",
        chart_name=chart.chart_name,
        rank=1,
        item_type=EntityType.TRACK,
        target_id="apple-song-1",
        target_name="Hello",
        subtitle="Adele",
        provider="apple_music",
        source_type="apple_music_charts",
        mock=False,
        note="live",
        target_payload={"isrc": "GBBKS1500210", "album_title": "25", "storefront": "us"},
    )

    target = DiscoveryAssembler()._build_target(chart, entry)

    self.assertEqual(target.resolution_mode, "search_lookup")
    self.assertEqual(target.resolution_hints["isrc"], "GBBKS1500210")
    self.assertEqual(target.resolution_hints["provider_origin_id"], "apple-song-1")
```

- [ ] **Step 2: 跑定向测试，确认当前失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_discovery_service.py'`

Expected:
- FAIL
- 缺少 `resolution_mode` / `resolution_hints` 字段

- [ ] **Step 3: 实现最小契约升级**

```python
# orchestration.py
class DiscoveryTarget(BaseModel):
    target_kind: EntityType
    provider: str
    provider_id: str
    display_title: str
    display_subtitle: str | None = None
    source_context: DiscoverySourceContext
    conversion_ready: bool
    conversion_note: str | None = None
    discovery_badges: list[str] = Field(default_factory=list)
    resolution_mode: str = "direct_id"
    resolution_hints: dict[str, str] = Field(default_factory=dict)
```

```python
# discovery.py
if entry.provider == "musicbrainz" and provider_id:
    return DiscoveryTarget(
        ...,
        resolution_mode="direct_id",
        resolution_hints={},
    )

return DiscoveryTarget(
    ...,
    resolution_mode="search_lookup",
    resolution_hints={
        "title": entry.target_name,
        "artist_name": entry.subtitle or "",
        "provider_origin_id": provider_id,
        "provider_origin_name": entry.provider,
        **{key: str(value) for key, value in (entry.target_payload or {}).items() if value is not None},
    },
)
```

- [ ] **Step 4: 跑定向测试，确认转绿**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_discovery_service.py'`

Expected:
- PASS
- ListenBrainz 仍是 `direct_id`
- Apple Music 进入 `search_lookup`

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/schemas/orchestration.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/discovery.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_discovery_service.py
git commit -m "feat: add discovery target resolution modes"
```

## Task 4: 前端消费 Apple Music discovery 和新的 resolution contract

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/types/orchestration.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/discovery-metadata.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/__tests__/discovery-metadata.spec.ts`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/__tests__/ChartsView.spec.ts`

- [ ] **Step 1: 先写前端 failing tests**

```ts
it('throws a lookup-specific error for search_lookup targets', async () => {
  await expect(
    fetchDiscoveryTargetDetail({
      target_kind: 'track',
      provider: 'apple_music',
      provider_id: 'apple-song-1',
      display_title: 'Hello',
      display_subtitle: 'Adele',
      source_context: {
        chart_source: 'apple_music',
        chart_id: 'chart-apple-music-top-songs-us',
        chart_name: 'Top Songs',
        rank: 1,
        chart_type: 'track',
      },
      conversion_ready: true,
      conversion_note: null,
      discovery_badges: ['songs', 'weekly'],
      resolution_mode: 'search_lookup',
      resolution_hints: {
        title: 'Hello',
        artist_name: 'Adele',
        album_title: '25',
        isrc: 'GBBKS1500210',
      },
    }),
  ).rejects.toThrow('当前榜单项需要 metadata lookup 才能打开详情。');
});
```

```ts
it('renders apple music chart summary and lookup-ready badge', async () => {
  // mock fetchCharts/fetchChartDetail 返回 apple_music chart
  // 断言：
  // 1. chart card 出现 Apple Music
  // 2. entry 上展示 metadata ready / lookup 提示
});
```

- [ ] **Step 2: 跑前端定向测试，确认失败**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run`

Expected:
- FAIL
- 类型缺少 `resolution_mode` / `resolution_hints`
- 现有桥接层没有区分 `search_lookup`

- [ ] **Step 3: 实现最小前端兼容**

```ts
// orchestration.ts
export interface DiscoveryTarget {
  target_kind: EntityType;
  provider: string;
  provider_id: string;
  display_title: string;
  display_subtitle?: string | null;
  source_context: DiscoverySourceContext;
  conversion_ready: boolean;
  conversion_note?: string | null;
  discovery_badges: string[];
  resolution_mode: 'direct_id' | 'search_lookup';
  resolution_hints: Record<string, string>;
}
```

```ts
// discovery-metadata.ts
export async function fetchDiscoveryTargetDetail(target: DiscoveryTarget) {
  if (!target.conversion_ready) {
    throw new Error(target.conversion_note || '当前榜单项暂不支持 metadata detail。');
  }
  if (target.resolution_mode === 'search_lookup') {
    throw new Error('当前榜单项需要 metadata lookup 才能打开详情。');
  }
  return fetchMetadataDetail(target.target_kind, target.provider_id);
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

- [ ] **Step 4: 跑前端测试和构建，确认通过**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run`

Expected:
- PASS
- Apple Music chart view test 通过

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected:
- Build 成功

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/types/orchestration.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/discovery-metadata.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/__tests__/discovery-metadata.spec.ts /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/__tests__/ChartsView.spec.ts
git commit -m "feat: surface apple music discovery targets"
```

## Task 5: 文档、打包与全量验证

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/static/index.html`

- [ ] **Step 1: 先补文档中 Apple Music 的当前真实状态**

```md
# .env.example
MUSICPILOT_CHART_PROVIDER_MODE=apple_music
MUSICPILOT_CHART_APPLE_MUSIC_STOREFRONT=us
MUSICPILOT_CHART_APPLE_MUSIC_DEVELOPER_TOKEN=your_apple_music_developer_token
MUSICPILOT_CHART_APPLE_MUSIC_COUNT=20
```

```md
# README / backend README
- Discovery 现支持 `mock`、`listenbrainz`、`apple_music`
- Apple Music 第一轮仅支持 songs / albums charts
- Apple entries 当前进入 `search_lookup` metadata conversion mode
```

- [ ] **Step 2: 跑后端全量测试**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected:
- PASS

- [ ] **Step 3: 跑前端构建**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected:
- PASS

- [ ] **Step 4: 重新打包 plugin_runtime**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected:
- PASS
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/static/index.html` 更新

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
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example /Users/lihuanhuan/PycharmProjects/MusicPilot/README.md /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md /Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/static/index.html
git commit -m "docs: document apple music discovery support"
```

## Self-Review

### Spec Coverage

- Apple Music songs/albums provider: Task 1 + Task 2
- `DiscoveryTarget` 解析契约升级: Task 3
- 前端 discovery 产品化消费 Apple targets: Task 4
- 配置、缓存复用、文档与打包: Task 2 + Task 5
- 保持现有 ListenBrainz/route 兼容: Task 3 + Task 5

### Placeholder Scan

- 无 `TODO` / `TBD` / “implement later”
- 每个任务都给了具体文件、测试命令和最小代码形态

### Type Consistency

- `resolution_mode` 固定为 `'direct_id' | 'search_lookup'`
- `resolution_hints` 固定为 `dict[str, str]` / `Record<string, string>`
- Apple Music 第一轮 target kind 只覆盖 `track` 和 `album`

