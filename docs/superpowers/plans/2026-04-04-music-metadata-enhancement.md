# Music Metadata Resolver Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve music organize metadata recovery using existing context plus source-path parsing, while keeping preview/apply behavior and runtime boundaries unchanged.

**Architecture:** Extend `MusicMetadataResolver` to preserve current precedence and add path-derived hints from `host_transfer_source_path` / `local_file_path`. Keep the parser lightweight and local to `music_metadata.py`. Update the current-state docs so README text matches the actual music preview/apply implementation.

**Tech Stack:** Python, FastAPI, Pydantic, unittest

---

### Task 1: Lock Source-Path Metadata Recovery with Failing Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Add a failing resolver test for source-path-derived hints**

Add a test that proves a source path can recover artist, album, year, and title without `MetadataDetail`:

```python
def test_music_metadata_resolver_uses_source_path_hints_when_metadata_missing(self) -> None:
    from app.services.music_metadata import MusicMetadataResolver

    candidate = build_candidate().model_copy(
        update={
            "title": "Fallback Title",
            "site_name": "Fallback Site",
            "format_tag": "flac",
            "raw_payload": {
                "host_transfer_source_path": "/downloads/Adele/2015 - 25/01 - Hello.flac",
            },
        }
    )

    result = MusicMetadataResolver().resolve(candidate=candidate, metadata_detail=None)

    self.assertEqual(result.artist_name, "adele")
    self.assertEqual(result.album_title, "25")
    self.assertEqual(result.track_title, "hello")
    self.assertEqual(result.year, "2015")
    self.assertEqual(result.format_ext, "flac")
```

- [ ] **Step 2: Add a failing resolver test that metadata still overrides path hints**

```python
def test_music_metadata_resolver_prefers_metadata_detail_over_source_path_hints(self) -> None:
    from app.services.music_metadata import MusicMetadataResolver

    candidate = build_candidate().model_copy(
        update={
            "raw_payload": {
                "host_transfer_source_path": "/downloads/Someone Else/2001 - Wrong Album/02 - Wrong Song.mp3",
            },
            "format_tag": "mp3",
        }
    )

    result = MusicMetadataResolver().resolve(candidate=candidate, metadata_detail=build_track_detail())

    self.assertEqual(result.artist_name, "adele")
    self.assertEqual(result.album_title, "25")
    self.assertEqual(result.track_title, "hello")
    self.assertEqual(result.year, "2015")
    self.assertEqual(result.format_ext, "mp3")
```

- [ ] **Step 3: Add a failing planner regression test**

```python
def test_strategy_service_builds_track_path_from_source_path_hints_when_metadata_missing(self) -> None:
    candidate = build_candidate().model_copy(
        update={
            "title": "Fallback Title",
            "site_name": "Fallback Site",
            "format_tag": "flac",
            "raw_payload": {
                "host_transfer_source_path": "/downloads/Adele/2015 - 25/01 - Hello.flac",
            },
        }
    )
    service = OrganizeStrategyService(build_settings())

    plan = service.build_plan(candidate=candidate, metadata_detail=None)

    self.assertEqual(plan.target_relative_path, "adele")
```
```

Then add a second regression that uses track metadata to preserve track-path behavior:

```python
def test_strategy_service_still_builds_track_path_with_track_metadata(self) -> None:
    candidate = build_candidate().model_copy(
        update={
            "format_tag": "flac",
            "raw_payload": {
                "host_transfer_source_path": "/downloads/Adele/2015 - 25/01 - Hello.flac",
            },
        }
    )
    service = OrganizeStrategyService(build_settings())

    plan = service.build_plan(candidate=candidate, metadata_detail=build_track_detail())

    self.assertEqual(plan.target_relative_path, "adele/2015 - 25/hello.flac")
```

- [ ] **Step 4: Run targeted tests to verify red**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New source-path tests fail

### Task 2: Implement Source-Path Parsing in `MusicMetadataResolver`

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/music_metadata.py`

- [ ] **Step 1: Add helpers to extract the best source path**

Add a helper that checks, in order:

```python
raw_payload = candidate.raw_payload or {}
source_path = raw_payload.get("host_transfer_source_path") or raw_payload.get("local_file_path")
```

- [ ] **Step 2: Add path-derived hint parsing**

Implement small private helpers inside `music_metadata.py` for:

- basename/stem parsing
- `YYYY - Album` parsing from parent dir
- grandparent dir artist hint
- `NN - Title` parsing from filename stem

Keep them internal and lightweight. Do not add new dataclasses or parser frameworks.

- [ ] **Step 3: Merge path hints into current precedence**

Update `resolve(...)` so precedence becomes:

1. `metadata_detail`
2. existing candidate-level fields
3. source-path-derived hints
4. current title/site fallback

The resulting `MusicOrganizeMetadata` shape stays unchanged.

- [ ] **Step 4: Run targeted tests to verify green**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New resolver tests pass
- Existing planner tests still pass

### Task 3: Clean Up Current-State Docs

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`

- [ ] **Step 1: Update current organize semantics in README**

Change current-state text so it reflects:

- `preview` = MusicPilot local music plan preview
- `apply` = MusicPilot music path planning + host file/storage execution

Do not rewrite the historical docs section.

- [ ] **Step 2: Update backend README current-state wording**

Remove or reword stale lines that still describe current preview/apply as `transfer/name` / `transfer/manual` semantics.

- [ ] **Step 3: Update architecture/current-state docs**

Add or edit short notes in `docs/14` and `docs/23` so they align with the now-current preview/apply and metadata/layout split.

### Task 4: Run Full Verification and Repackage Runtime Mirror

**Files:**
- Modify via packaging: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/services/music_metadata.py`
- Modify via packaging: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/services/organize_strategy.py`

- [ ] **Step 1: Repackage runtime mirror**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
python3 scripts/package_plugin.py
```

Expected:
- plugin runtime mirror includes updated `music_metadata.py`

- [ ] **Step 2: Run full backend verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests
```

Expected:
- All backend tests pass

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Expected:
- Build succeeds

- [ ] **Step 4: Check API shell endpoints**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
print("OPENAPI", client.get("/openapi.json").status_code)
print("DOCS", client.get("/docs").status_code)
PY
```

Expected:
- `OPENAPI 200`
- `DOCS 200`
