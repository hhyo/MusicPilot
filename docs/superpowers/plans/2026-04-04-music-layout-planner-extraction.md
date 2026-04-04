# Music Layout Planner Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract relative-path selection and template rendering from `OrganizeStrategyService` into a dedicated `MusicLayoutPlanner` while keeping preview/apply behavior unchanged.

**Architecture:** Introduce `MusicLayoutPlanner` as the unit responsible for entity-aware layout selection and template rendering. `OrganizeStrategyService` remains the thin shell that builds the snapshot, resolves metadata, and assembles the final `OrganizePlan`.

**Tech Stack:** Python, FastAPI, Pydantic, unittest

---

### Task 1: Lock Layout Planning Behavior with Failing Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Add a failing test for artist path selection**

Add a planner test that proves artist entities render the artist template only:

```python
def test_music_layout_planner_uses_artist_template_for_artist_entity(self) -> None:
    planner = MusicLayoutPlanner()
    snapshot = build_strategy_snapshot()
    context = build_music_context()

    path = planner.build_relative_path(
        snapshot=snapshot,
        context=context,
        metadata_detail=build_artist_detail(),
    )

    self.assertEqual(path, "adele")
```

- [ ] **Step 2: Add a failing test for album path selection**

```python
def test_music_layout_planner_uses_album_template_for_album_entity(self) -> None:
    planner = MusicLayoutPlanner()

    path = planner.build_relative_path(
        snapshot=build_strategy_snapshot(),
        context=build_music_context(),
        metadata_detail=build_album_detail(),
    )

    self.assertEqual(path, "adele/2015 - 25")
```

- [ ] **Step 3: Add a failing test for track path selection**

```python
def test_music_layout_planner_uses_album_plus_track_for_track_entity(self) -> None:
    planner = MusicLayoutPlanner()

    path = planner.build_relative_path(
        snapshot=build_strategy_snapshot(),
        context=build_music_context(),
        metadata_detail=build_track_detail(),
    )

    self.assertEqual(path, "adele/2015 - 25/hello.flac")
```

- [ ] **Step 4: Add a failing test for missing metadata fallback**

```python
def test_music_layout_planner_falls_back_to_artist_template_when_metadata_missing(self) -> None:
    planner = MusicLayoutPlanner()

    path = planner.build_relative_path(
        snapshot=build_strategy_snapshot(),
        context=build_music_context(),
        metadata_detail=None,
    )

    self.assertEqual(path, "adele")
```

- [ ] **Step 5: Run tests to verify red**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New planner tests fail because `MusicLayoutPlanner` does not exist yet

### Task 2: Implement `MusicLayoutPlanner`

**Files:**
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/music_layout.py`

- [ ] **Step 1: Create the planner with the extracted rendering logic**

Add the new file:

```python
from __future__ import annotations

import re
from pathlib import PurePosixPath

from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeStrategySnapshot


class MusicLayoutPlanner:
    def build_relative_path(
        self,
        *,
        snapshot: OrganizeStrategySnapshot,
        context: dict[str, str],
        metadata_detail: MetadataDetail | None,
    ) -> str:
        if metadata_detail is None or metadata_detail.entity_type == "artist":
            return self.render_template(snapshot.artist_dir_template, context)
        if metadata_detail.entity_type == "album":
            return self.render_template(snapshot.album_dir_template, context)

        album_dir = self.render_template(snapshot.album_dir_template, context)
        track_file = self.render_template(snapshot.track_file_template, context)
        return str(PurePosixPath(album_dir) / track_file)

    def render_template(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        rendered = re.sub(r"/{2,}", "/", rendered).strip("/")
        return rendered or "unknown"
```

- [ ] **Step 2: Run targeted tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- Planner tests still fail until `OrganizeStrategyService` is wired to the new planner or helper fixtures are added

### Task 3: Refactor `OrganizeStrategyService` into a Planner Shell

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/organize_strategy.py`

- [ ] **Step 1: Inject and use `MusicLayoutPlanner`**

Refactor the service:

```python
from .music_layout import MusicLayoutPlanner


class OrganizeStrategyService:
    def __init__(
        self,
        settings: Settings,
        *,
        metadata_resolver: MusicMetadataResolver | None = None,
        layout_planner: MusicLayoutPlanner | None = None,
    ):
        self.settings = settings
        self.metadata_resolver = metadata_resolver or MusicMetadataResolver()
        self.layout_planner = layout_planner or MusicLayoutPlanner()

    def build_plan(...):
        ...
        target_relative_path = self.layout_planner.build_relative_path(
            snapshot=snapshot,
            context=context,
            metadata_detail=metadata_detail,
        )
```

- [ ] **Step 2: Remove extracted helpers from `OrganizeStrategyService`**

Delete:

```python
def _resolve_relative_path(...)
def _render_template(...)
```

- [ ] **Step 3: Run targeted tests to verify green**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- Planner tests pass
- Existing plan tests still pass

### Task 4: Update Docs and Run Full Verification

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`

- [ ] **Step 1: Update docs to note planner extraction status**

Add a short note that:

- `MusicLayoutPlanner` is now split out
- `OrganizeStrategyService` is only the shell that assembles `OrganizePlan`

- [ ] **Step 2: Repackage runtime mirror**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
python3 scripts/package_plugin.py
```

Expected:
- `plugin_runtime/plugins/musicpilot/services/music_layout.py` appears

- [ ] **Step 3: Run full backend verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests
```

Expected:
- All backend tests pass

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Expected:
- Build succeeds
