# Music Organize Metadata Resolver Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract music metadata recovery from `OrganizeStrategyService` into a dedicated resolver while keeping preview/apply behavior and path rendering unchanged.

**Architecture:** Introduce a small `MusicMetadataResolver` that returns the existing template context fields from `SearchCandidateDetail` and `MetadataDetail`. Refactor `OrganizeStrategyService` into a thin planner shell that consumes this resolver, keeps snapshot creation and template rendering, and preserves the current relative-path behavior.

**Tech Stack:** Python, FastAPI, Pydantic, unittest, SQLAlchemy

---

### Task 1: Lock Metadata Recovery Behavior with Failing Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Add a failing unit test for track metadata resolution**

Add a small resolver-oriented test case that asserts track metadata keeps current priority:

```python
def test_music_metadata_resolver_prefers_track_detail_fields(self) -> None:
    candidate = build_candidate(title="Fallback Title", format_tag="flac")
    detail = MetadataDetail(
        entity_type="track",
        id="trk-1",
        title="Hello",
        track_title="Hello",
        aliases=[],
        artist_name="Adele",
        album_title="25",
        year=2015,
        release_type=None,
        genres=[],
        external_ids={},
        provider="seed",
        source_type="catalog",
        mock=False,
        note="detail",
        integration_point="test",
    )

    result = MusicMetadataResolver().resolve(candidate=candidate, metadata_detail=detail)

    self.assertEqual(result.artist_name, "adele")
    self.assertEqual(result.album_title, "25")
    self.assertEqual(result.track_title, "hello")
    self.assertEqual(result.year, "2015")
    self.assertEqual(result.format_ext, "flac")
```

- [ ] **Step 2: Add a failing unit test for candidate fallback behavior**

Add a test that proves missing metadata still falls back to existing candidate behavior:

```python
def test_music_metadata_resolver_falls_back_to_candidate_fields(self) -> None:
    candidate = build_candidate(
        title="Adele Live",
        site_name="Tracker Artist",
        format_tag="mp3",
    )

    result = MusicMetadataResolver().resolve(candidate=candidate, metadata_detail=None)

    self.assertEqual(result.title, "adele-live")
    self.assertEqual(result.artist_name, "tracker-artist")
    self.assertEqual(result.album_title, "adele-live")
    self.assertEqual(result.track_title, "adele-live")
    self.assertEqual(result.year, "unknown")
    self.assertEqual(result.format_ext, "mp3")
```

- [ ] **Step 3: Add a failing regression test that `build_plan()` output stays unchanged**

Add a regression test around the existing planner:

```python
def test_strategy_service_build_plan_uses_extracted_music_metadata_without_changing_output(self) -> None:
    candidate = build_candidate()
    detail = build_album_detail()
    service = OrganizeStrategyService(build_settings())

    plan = service.build_plan(candidate=candidate, metadata_detail=detail)

    self.assertIn("adele", plan.target_relative_path)
    self.assertIn("2015", plan.target_relative_path)
    self.assertIn("25", plan.target_relative_path)
```

- [ ] **Step 4: Run tests to verify red**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New resolver tests fail because `MusicMetadataResolver` does not exist yet

- [ ] **Step 5: Commit red-state checkpoint**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py
git commit -m "test: lock music metadata resolver behavior"
```

### Task 2: Implement `MusicMetadataResolver`

**Files:**
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/music_metadata.py`

- [ ] **Step 1: Create the resolver value object and class**

Add the new file with the minimal implementation:

```python
from __future__ import annotations

from dataclasses import dataclass

from ..schemas.acquisition import SearchCandidateDetail
from ..schemas.metadata import MetadataDetail
from .organize_strategy import slugify


@dataclass(frozen=True)
class MusicOrganizeMetadata:
    title: str
    artist_name: str
    album_title: str
    track_title: str
    year: str
    format_ext: str


class MusicMetadataResolver:
    def resolve(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
    ) -> MusicOrganizeMetadata:
        title = metadata_detail.title if metadata_detail else candidate.title
        artist_name = (
            metadata_detail.artist_name
            if metadata_detail and metadata_detail.artist_name
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "artist" else candidate.site_name)
        )
        album_title = (
            metadata_detail.album_title
            if metadata_detail and metadata_detail.album_title
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "album" else title)
        )
        track_title = (
            metadata_detail.track_title
            if metadata_detail and metadata_detail.track_title
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "track" else title)
        )
        year = str(metadata_detail.year) if metadata_detail and metadata_detail.year else "unknown"
        format_ext = slugify(candidate.format_tag or "bin")

        return MusicOrganizeMetadata(
            title=slugify(title),
            artist_name=slugify(artist_name),
            album_title=slugify(album_title),
            track_title=slugify(track_title),
            year=year,
            format_ext=format_ext,
        )
```

- [ ] **Step 2: Run the targeted tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New resolver tests still fail because planner has not been refactored to use the resolver yet, or imports need adjustment

- [ ] **Step 3: Commit the new unit skeleton**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/music_metadata.py
git commit -m "feat: add music metadata resolver"
```

### Task 3: Refactor `OrganizeStrategyService` into a Thin Planner Shell

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/organize_strategy.py`

- [ ] **Step 1: Inject and use `MusicMetadataResolver`**

Refactor the service so it no longer owns metadata recovery:

```python
from .music_metadata import MusicMetadataResolver


class OrganizeStrategyService:
    def __init__(self, settings: Settings, *, metadata_resolver: MusicMetadataResolver | None = None):
        self.settings = settings
        self.metadata_resolver = metadata_resolver or MusicMetadataResolver()

    def build_plan(...):
        snapshot = OrganizeStrategySnapshot(...)
        metadata = self.metadata_resolver.resolve(candidate=candidate, metadata_detail=metadata_detail)
        context = {
            "artist_name": metadata.artist_name,
            "album_title": metadata.album_title,
            "track_title": metadata.track_title,
            "title": metadata.title,
            "year": metadata.year,
            "format_ext": metadata.format_ext,
        }
        ...
```

- [ ] **Step 2: Remove dead `_build_context(...)` logic**

Delete the old `_build_context(...)` method entirely after the new resolver is wired in. Keep `slugify(...)`, `_resolve_relative_path(...)`, and `_render_template(...)`.

- [ ] **Step 3: Run targeted tests to verify green**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- Resolver tests pass
- Existing plan tests still pass

- [ ] **Step 4: Commit the planner refactor**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/organize_strategy.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/music_metadata.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py
git commit -m "refactor: extract music metadata resolver"
```

### Task 4: Run Full Verification and Update Docs

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`

- [ ] **Step 1: Update the design doc to record what is now implemented**

Add a short note to `docs/23_音乐文件整理技术设计与实现方案.md` stating that:

- `MusicMetadataResolver` has now been split out
- `OrganizeStrategyService` remains the thin planner shell
- `MusicLayoutPlanner` is still the next optional split, not part of this task

- [ ] **Step 2: Run full backend verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests
```

Expected:
- All backend tests pass

- [ ] **Step 3: Run frontend build to ensure no accidental breakage**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Expected:
- Build succeeds

- [ ] **Step 4: Commit docs + final verification state**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md
git commit -m "docs: record music metadata resolver extraction"
```
