# PT Query Builder Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorder and minimally expand query generation so the first queries consumed by host PT search better match common music release titles.

**Architecture:** Keep `host_search` unchanged and optimize only `QueryBuilderService` output. Use TDD to lock the new track/album query ordering and alias demotion, then implement the smallest changes in `query_builder.py`.

**Tech Stack:** Python, FastAPI backend services, unittest

---

### Task 1: Lock the new track query order

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_query_builder.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/query_builder.py`

- [ ] **Step 1: Write the failing test**

Add a test asserting that track queries prioritize PT-shaped release forms before aliases and year-heavy variants:

```python
def test_track_ordered_queries_prioritize_pt_release_shapes(self) -> None:
    result = QueryBuilderService.build_from_detail(build_track_detail())
    top_sources = [query.source for query in result.ordered_queries[:4]]
    self.assertEqual(
        top_sources,
        [
            "canonical_title",
            "canonical_album_release",
            "canonical_track_album",
            "relaxed_primary",
        ],
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'`

Expected: FAIL because current query order still puts `canonical_year` and/or alias queries ahead of PT-friendly relaxed queries.

- [ ] **Step 3: Write minimal implementation**

Update `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/query_builder.py` to:

- insert `canonical_album_release` for track queries
- lower track `canonical_year` priority behind relaxed primary queries
- move alias query priorities after relaxed query priorities

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'`

Expected: PASS

### Task 2: Lock the new album query order

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_query_builder.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/query_builder.py`

- [ ] **Step 1: Write the failing test**

Add a test asserting album queries stay PT-friendly and keep album title focused:

```python
def test_album_ordered_queries_prioritize_release_title_before_aliases(self) -> None:
    result = QueryBuilderService.build_from_detail(build_album_detail())
    top_sources = [query.source for query in result.ordered_queries[:4]]
    self.assertEqual(
        top_sources,
        [
            "canonical_title",
            "canonical_year",
            "relaxed_primary",
            "relaxed_album_only",
        ],
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'`

Expected: FAIL because alias queries currently appear before relaxed album fallbacks.

- [ ] **Step 3: Write minimal implementation**

Adjust alias priority generation so album relaxed queries appear before alias queries in `ordered_queries`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'`

Expected: PASS

### Task 3: Regression verification and docs touch-up

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`

- [ ] **Step 1: Add a small verification note**

Document that query optimization now prioritizes PT-style `artist + title/album + format` shapes and demotes aliases/year-heavy variants.

- [ ] **Step 2: Run focused tests**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'`

Expected: PASS

- [ ] **Step 3: Run full backend suite**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected: PASS

- [ ] **Step 4: Run frontend build**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected: PASS
