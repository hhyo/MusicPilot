# ListenBrainz Chart Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one real chart/discovery source using ListenBrainz sitewide artists and recordings while preserving the existing charts API and frontend flow.

**Architecture:** Keep the current chart adapter boundary, add a live `ListenBrainzChartProviderAdapter`, make chart service/route mock semantics dynamic, and keep `mock` mode as the default fallback for development.

**Tech Stack:** FastAPI, Pydantic, httpx, unittest, Vue 3 frontend shell

---

### Task 1: Write failing chart provider tests

**Files:**
- Create: `backend/tests/test_chart_provider.py`
- Modify: `backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Write failing adapter mapping tests**

```python
import unittest

from app.adapters.chart_provider import ListenBrainzChartProviderAdapter
from app.schemas.mvp import EntityType


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return FakeResponse(self.payloads[path])


class ListenBrainzChartProviderAdapterTest(unittest.TestCase):
    def test_list_charts_returns_artist_and_track_chart(self):
        client = FakeClient(payloads={})
        adapter = ListenBrainzChartProviderAdapter(client=client)

        charts = adapter.list_charts()

        self.assertEqual([item.chart_type for item in charts], [EntityType.ARTIST, EntityType.TRACK])

    def test_track_chart_detail_maps_recording_mbid_as_target_id(self):
        client = FakeClient(
            payloads={
                "/1/stats/sitewide/recordings": {
                    "payload": {
                        "recordings": [
                            {
                                "recording_mbid": "rec-1",
                                "track_name": "Hello",
                                "artist_name": "Adele",
                                "listen_count": 10,
                            }
                        ]
                    }
                }
            }
        )
        adapter = ListenBrainzChartProviderAdapter(client=client)

        detail = adapter.get_chart_detail("chart-listenbrainz-top-tracks-week")

        self.assertEqual(detail.items[0].target_id, "rec-1")
        self.assertEqual(detail.items[0].item_type, EntityType.TRACK)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected: FAIL because `ListenBrainzChartProviderAdapter` does not exist yet.

- [ ] **Step 3: Write failing service semantics test**

```python
def test_chart_service_live_mode_is_not_mock(self):
    service = ChartService(adapter=FakeLiveChartAdapter())

    result = service.list_charts()

    self.assertFalse(result.mock)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'`

Expected: FAIL because `ChartService` still hardcodes `mock=True`.

### Task 2: Implement live chart provider and dynamic chart semantics

**Files:**
- Modify: `backend/app/adapters/chart_provider.py`
- Modify: `backend/app/services/charts.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/dependencies.py`
- Modify: `backend/app/api/routes/charts.py`

- [ ] **Step 1: Add adapter metadata and live adapter**

Implement:

```python
class ChartProviderAdapter(ABC):
    @property
    @abstractmethod
    def provider(self) -> str:
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        ...

    @property
    def mock(self) -> bool:
        return True
```

Add:

```python
class ListenBrainzChartProviderAdapter(ChartProviderAdapter):
    ...
```

with:

- `provider = "listenbrainz"`
- `source_type = "listenbrainz_sitewide_stats"`
- `mock = False`
- artist chart id: `chart-listenbrainz-top-artists-week`
- track chart id: `chart-listenbrainz-top-tracks-week`

- [ ] **Step 2: Add config and dependency wiring**

Implement settings:

```python
chart_provider_mode: str = "mock"
chart_provider_timeout_seconds: float = 15.0
chart_listenbrainz_base_url: str = "https://api.listenbrainz.org"
chart_provider_user_agent: str = "MusicPilot/0.1.0 (local)"
chart_listenbrainz_range: str = "week"
chart_listenbrainz_count: int = 20
```

and dependency:

```python
if settings.chart_provider_mode == "listenbrainz":
    return ListenBrainzChartProviderAdapter(...)
return MockChartProviderAdapter(...)
```

- [ ] **Step 3: Make service semantics dynamic**

Change `ChartService.list_charts()` to emit dynamic `mock/note/integration_point` based on adapter properties rather than hardcoded mock strings.

- [ ] **Step 4: Make routes dynamic**

Update `/charts/providers`, `/charts`, `/charts/{chart_id}`, `/charts/{chart_id}/subscribe` route `mock/note` values to follow the returned adapter/data semantics.

- [ ] **Step 5: Run targeted tests**

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_chart_provider.py'`

Expected: PASS

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'`

Expected: PASS

### Task 3: Update docs and validate runtime

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
- Create: `docs/30_ListenBrainz_榜单运行态验证.md`

- [ ] **Step 1: Document new chart provider mode**

Add env examples:

```env
MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz
MUSICPILOT_CHART_LISTENBRAINZ_BASE_URL=https://api.listenbrainz.org
MUSICPILOT_CHART_PROVIDER_TIMEOUT_SECONDS=15
MUSICPILOT_CHART_PROVIDER_USER_AGENT=MusicPilot/0.1.0 (local)
MUSICPILOT_CHART_LISTENBRAINZ_RANGE=week
MUSICPILOT_CHART_LISTENBRAINZ_COUNT=20
```

- [ ] **Step 2: Write runtime smoke-check doc**

Document:
- env used
- endpoints checked
- returned provider/source_type/mock semantics
- current scope limits (artist + track only)

- [ ] **Step 3: Run full verification**

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected: all backend tests pass

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected: build succeeds

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected: runtime packaging succeeds
