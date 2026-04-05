# Discovery Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Productize discovery charts while defining a stable `discovery -> metadata` conversion layer that future chart expansion can reuse without schema redesign.

**Architecture:** Keep provider adapters focused on source normalization, add a new discovery assembler layer for product-facing shaping, enrich chart response models with a stable `DiscoveryTarget`, and update the charts page to consume the richer discovery view model without changing route paths or subscription behavior.

**Tech Stack:** FastAPI, Pydantic, Vue 3, Element Plus, unittest, pnpm, MoviePilot plugin runtime packaging.

---

### Task 1: Establish discovery response models and assembler tests

**Files:**
- Create: `backend/tests/test_discovery_service.py`
- Modify: `backend/app/schemas/orchestration.py`
- Modify: `frontend/src/types/orchestration.ts`

- [ ] **Step 1: Write the failing backend tests for discovery view shaping**

```python
from datetime import datetime, timezone
from unittest import TestCase

from app.schemas.mvp import EntityType
from app.schemas.orchestration import ChartDetailData, ChartEntryInfo, ChartInfo
from app.services.discovery import DiscoveryAssembler


class DiscoveryAssemblerTests(TestCase):
    def test_builds_metadata_ready_track_target(self):
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

        self.assertEqual(result.hero_entry.target.target_kind, EntityType.TRACK)
        self.assertEqual(result.hero_entry.target.provider, "musicbrainz")
        self.assertEqual(result.hero_entry.target.provider_id, "recording-mbid-001")
        self.assertTrue(result.hero_entry.target.conversion_ready)
        self.assertEqual(result.conversion_summary["ready"], 1)

    def test_builds_not_ready_target_when_entry_has_no_target_id(self):
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

        self.assertFalse(result.hero_entry.target.conversion_ready)
        self.assertEqual(result.hero_entry.target.conversion_note, "Missing provider target id.")
        self.assertEqual(result.conversion_summary["not_ready"], 1)
```

- [ ] **Step 2: Run the new test file and verify it fails**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/backend
PYTHONPATH=. .venv/bin/python -m unittest tests.test_discovery_service -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.services.discovery` and missing enriched discovery fields on chart schemas.

- [ ] **Step 3: Add the new discovery-facing schema types**

```python
class DiscoverySourceContext(BaseModel):
    chart_source: str
    chart_id: str
    chart_name: str
    rank: int
    chart_type: EntityType


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


class DiscoveryEntryView(BaseModel):
    entry: ChartEntryInfo
    target: DiscoveryTarget
    entry_summary: str
    badges: list[str] = Field(default_factory=list)
    highlight_reason: str | None = None


class DiscoveryEntryGroup(BaseModel):
    group_key: str
    group_label: str
    items: list[DiscoveryEntryView] = Field(default_factory=list)
```

Also enrich `ChartInfo` with:

```python
summary: str | None = None
chart_group: str | None = None
chart_scope: str | None = None
freshness_label: str | None = None
supports_subscription: bool = True
```

And enrich `ChartDetailData` with:

```python
hero_entry: DiscoveryEntryView | None = None
summary_stats: dict[str, str | int] = Field(default_factory=dict)
entry_groups: list[DiscoveryEntryGroup] = Field(default_factory=list)
conversion_summary: dict[str, int] = Field(default_factory=dict)
```

Mirror the same shape in `frontend/src/types/orchestration.ts`.

- [ ] **Step 4: Create the new assembler with minimal deterministic shaping**

```python
from app.schemas.orchestration import (
    ChartDetailData,
    ChartInfo,
    DiscoveryEntryGroup,
    DiscoveryEntryView,
    DiscoverySourceContext,
    DiscoveryTarget,
)


class DiscoveryAssembler:
    def build_chart_info(self, chart: ChartInfo) -> ChartInfo:
        chart.summary = self._build_chart_summary(chart)
        chart.chart_group = self._build_chart_group(chart)
        chart.chart_scope = chart.category or "discovery"
        chart.freshness_label = self._build_freshness_label(chart)
        chart.supports_subscription = True
        return chart

    def build_detail(self, detail: ChartDetailData) -> ChartDetailData:
        enriched_chart = self.build_chart_info(detail.chart)
        entry_views = [self._build_entry_view(enriched_chart, item) for item in detail.items]
        detail.chart = enriched_chart
        detail.hero_entry = entry_views[0] if entry_views else None
        detail.entry_groups = self._group_entries(entry_views)
        detail.summary_stats = {
            "items": len(entry_views),
            "ready": sum(1 for item in entry_views if item.target.conversion_ready),
            "group_count": len(detail.entry_groups),
        }
        detail.conversion_summary = {
            "ready": sum(1 for item in entry_views if item.target.conversion_ready),
            "not_ready": sum(1 for item in entry_views if not item.target.conversion_ready),
        }
        return detail
```

- [ ] **Step 5: Run the new discovery tests and verify they pass**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/backend
PYTHONPATH=. .venv/bin/python -m unittest tests.test_discovery_service -v
```

Expected: PASS

- [ ] **Step 6: Commit the schema and assembler base**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization
git add backend/app/schemas/orchestration.py backend/app/services/discovery.py backend/tests/test_discovery_service.py frontend/src/types/orchestration.ts
git commit -m "feat: add discovery view models"
```

### Task 2: Integrate discovery assembler into chart service and provider-facing summaries

**Files:**
- Modify: `backend/app/services/charts.py`
- Modify: `backend/app/core/dependencies.py`
- Modify: `backend/app/adapters/chart_provider.py`
- Test: `backend/tests/test_chart_provider.py`
- Test: `backend/tests/test_discovery_service.py`

- [ ] **Step 1: Write a failing integration test for enriched chart detail and list output**

```python
def test_chart_service_enriches_list_and_detail(self):
    service = ChartService(adapter=FakeChartAdapter(), discovery_assembler=DiscoveryAssembler())

    listing = service.list_charts()
    detail = service.get_chart_detail("chart-listenbrainz-top-tracks-week")

    self.assertEqual(listing.items[0].chart_group, "tracks")
    self.assertIsNotNone(listing.items[0].summary)
    self.assertIsNotNone(detail.hero_entry)
    self.assertGreaterEqual(len(detail.entry_groups), 1)
```

- [ ] **Step 2: Run targeted chart/discovery tests and verify failure**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/backend
PYTHONPATH=. .venv/bin/python -m unittest tests.test_chart_provider tests.test_discovery_service -v
```

Expected: FAIL because `ChartService` does not yet accept or use a `DiscoveryAssembler`.

- [ ] **Step 3: Thread the assembler through chart service and dependency wiring**

```python
class ChartService:
    def __init__(self, adapter: ChartProviderAdapter, discovery_assembler: DiscoveryAssembler):
        self.adapter = adapter
        self.discovery_assembler = discovery_assembler

    def list_charts(self, *, provider=None, chart_type=None, region=None) -> ChartListData:
        items = [self.discovery_assembler.build_chart_info(item) for item in self.adapter.list_charts()]
        ...

    def get_chart_detail(self, chart_id: str) -> ChartDetailData:
        detail = self.adapter.get_chart_detail(chart_id)
        return self.discovery_assembler.build_detail(detail)
```

Update dependency wiring to instantiate `DiscoveryAssembler`.

- [ ] **Step 4: Add provider-level chart summaries that the assembler can reuse**

```python
def _build_chart_summary(self, chart: ChartInfo) -> str:
    if chart.chart_type == EntityType.ARTIST:
        return "Browse high-signal artists from the current chart source."
    if chart.chart_type == EntityType.ALBUM:
        return "Browse notable releases ready for deeper metadata inspection."
    return "Browse standout tracks that can later flow into metadata and acquisition."
```

Keep these descriptions lightweight and provider-neutral.

- [ ] **Step 5: Re-run targeted backend tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/backend
PYTHONPATH=. .venv/bin/python -m unittest tests.test_chart_provider tests.test_discovery_service -v
```

Expected: PASS

- [ ] **Step 6: Commit chart-service discovery integration**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization
git add backend/app/services/charts.py backend/app/core/dependencies.py backend/app/adapters/chart_provider.py backend/tests/test_chart_provider.py backend/tests/test_discovery_service.py
git commit -m "feat: enrich discovery chart responses"
```

### Task 3: Productize the charts page around discovery view models

**Files:**
- Modify: `frontend/src/views/ChartsView.vue`
- Modify: `frontend/src/types/orchestration.ts`
- Test: `frontend` build verification

- [ ] **Step 1: Update the page to use chart summaries and hero/group detail states**

Use these UI adjustments:

```vue
<p class="chart-card__summary">{{ chart.summary || chart.note }}</p>
<div class="chart-card__meta-row">
  <el-tag size="small" effect="plain">{{ chart.chart_group || chart.chart_type }}</el-tag>
  <el-tag size="small" effect="plain">{{ chart.freshness_label || chart.refresh_hint || 'live' }}</el-tag>
</div>
```

And in detail:

```vue
<section v-if="selectedChart?.hero_entry" class="hero-entry-card">
  <p class="hero-entry-card__eyebrow">Featured Entry</p>
  <h4>{{ selectedChart.hero_entry.target.display_title }}</h4>
  <p>{{ selectedChart.hero_entry.entry_summary }}</p>
  <div class="entry-card__tags">
    <el-tag
      v-for="badge in selectedChart.hero_entry.badges"
      :key="badge"
      size="small"
      effect="plain"
    >
      {{ badge }}
    </el-tag>
  </div>
</section>
```

- [ ] **Step 2: Render grouped entries and conversion readiness**

Use group rendering like:

```vue
<section v-for="group in selectedChart.entry_groups" :key="group.group_key" class="entry-group">
  <header class="entry-group__header">
    <h4>{{ group.group_label }}</h4>
  </header>
  <article v-for="item in group.items" :key="item.entry.item_id" class="entry-card">
    <div class="entry-card__body">
      <h4>{{ item.target.display_title }}</h4>
      <p>{{ item.entry_summary }}</p>
      <p class="entry-card__conversion">
        {{ item.target.conversion_ready ? 'metadata ready' : item.target.conversion_note || 'metadata pending' }}
      </p>
    </div>
  </article>
</section>
```

- [ ] **Step 3: Preserve current subscribe action without changing route usage**

Keep `handleSubscribe(item.entry)` semantics by passing the underlying `ChartEntryInfo`.

- [ ] **Step 4: Run frontend build verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Expected: PASS

- [ ] **Step 5: Commit the discovery page productization**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization
git add frontend/src/views/ChartsView.vue frontend/src/types/orchestration.ts
git commit -m "feat: productize discovery charts page"
```

### Task 4: Documentation, runtime sync, and full verification

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
- Modify: `docs/30_ListenBrainz_榜单运行态验证.md`
- Modify: `plugin_runtime/plugins/musicpilot/...` via packaging sync

- [ ] **Step 1: Update docs to describe discovery as a productized browsing layer**

Add concise factual updates:

- discovery now exposes a stable `discovery -> metadata` bridge
- chart detail now includes hero/group/readiness structures
- this phase still does not implement metadata jump or search conversion

- [ ] **Step 2: Run backend full verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/backend
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests
```

Expected: PASS

- [ ] **Step 3: Re-run frontend build**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Expected: PASS

- [ ] **Step 4: Sync plugin runtime**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization
python3 scripts/package_plugin.py
```

Expected: PASS

- [ ] **Step 5: Smoke-check API shell**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization/backend
PYTHONPATH=. .venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
for path in ["/openapi.json", "/docs", "/api/v1/plugin/musicpilot/charts"]:
    response = client.get(path)
    print(path, response.status_code)
PY
```

Expected:

- `/openapi.json 200`
- `/docs 200`
- `/api/v1/plugin/musicpilot/charts 200`

- [ ] **Step 6: Commit docs and runtime sync**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/.worktrees/discovery-productization
git add README.md backend/README.md docs/28_项目整体任务盘点与执行路线.md docs/30_ListenBrainz_榜单运行态验证.md plugin_runtime
git commit -m "docs: describe discovery productization"
```
