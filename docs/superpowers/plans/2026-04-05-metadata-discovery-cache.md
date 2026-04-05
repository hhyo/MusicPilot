# Metadata / Discovery Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal provider-level cache for MusicBrainz metadata and ListenBrainz chart responses while preferring MoviePilot's unified plugin cache in runtime.

**Architecture:** Introduce a tiny runtime cache wrapper that prefers `app.core.cache.TTLCache` and falls back to local `cachetools.TTLCache`. Use it only inside provider adapters so service and API layers stay unchanged.

**Tech Stack:** Python 3.12, FastAPI, httpx, cachetools, MoviePilot plugin runtime cache

---

### Task 1: Add failing cache-behavior tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_metadata_provider.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_chart_provider.py`

- [ ] Add a failing test that calls identical MusicBrainz search twice and expects only one upstream call.
- [ ] Add a failing test that calls identical MusicBrainz detail twice and expects only one upstream call.
- [ ] Add a failing test that calls ListenBrainz `list_charts()` then `get_chart_detail()` and expects endpoint payload reuse.
- [ ] Run the targeted tests and confirm they fail for repeated upstream calls.

### Task 2: Add runtime cache wrapper and config

**Files:**
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/runtime_cache.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/pyproject.toml`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/requirements.txt`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`

- [ ] Add `cachetools` dependency aligned with host usage.
- [ ] Add a thin `RuntimeTTLCache` wrapper that prefers host `TTLCache` and falls back to local `cachetools.TTLCache`.
- [ ] Add minimal settings:
  - metadata cache enabled / maxsize / search ttl / detail ttl
  - chart cache enabled / maxsize / ttl

### Task 3: Cache metadata provider output

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/metadata_provider.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`

- [ ] Inject cache settings into `MusicBrainzMetadataProviderAdapter`.
- [ ] Cache `search(...)` by normalized request key.
- [ ] Cache `get_detail(...)` by entity type and id.
- [ ] Re-run metadata provider tests and confirm the new tests pass.

### Task 4: Cache chart provider payloads

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`

- [ ] Add payload cache to `ListenBrainzChartProviderAdapter._get(...)`.
- [ ] Keep `get_chart_entry()` delegating through cached detail behavior.
- [ ] Re-run chart provider tests and confirm repeated payload fetches no longer happen.

### Task 5: Verify and document

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`

- [ ] Document the new cache behavior and env vars.
- [ ] Run full backend tests.
- [ ] Run frontend build.
- [ ] Run `python3 scripts/package_plugin.py`.
