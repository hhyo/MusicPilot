# Music Metadata Tag Parsing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add embedded audio-tag parsing to `MusicMetadataResolver` so local music files can recover better organize metadata without changing preview/apply boundaries.

**Architecture:** Keep `MusicMetadataResolver` as the single metadata recovery entry point. Add a thin `mutagen`-based tag reader inside `music_metadata.py`, merge tag-derived hints into the existing precedence, and keep `MusicLayoutPlanner` plus organize execution unchanged.

**Tech Stack:** Python, FastAPI, unittest, mutagen

---

### Task 1: Lock Tag Parsing Behavior with Failing Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Add a failing resolver test for embedded tags**

Add a test that creates a temporary audio file and patches the tag reader entry point to return real tag hints:

```python
def test_music_metadata_resolver_uses_embedded_tags_before_source_path_hints(self) -> None:
    from app.services.music_metadata import MusicMetadataResolver

    candidate = build_candidate().model_copy(
        update={
            "title": "Fallback Title",
            "site_name": "Fallback Site",
            "format_tag": "flac",
            "raw_payload": {
                "host_transfer_source_path": "/downloads/Adele/2015 - Wrong Album/01 - Wrong Song.flac",
            },
        }
    )

    resolver = MusicMetadataResolver()
    with patch.object(
        resolver,
        "_read_embedded_tag_hints",
        return_value=resolver._build_tag_hints(
            title="Hello",
            artist_name="Adele",
            album_title="25",
            year="2015",
            format_ext="flac",
        ),
    ):
        result = resolver.resolve(candidate=candidate, metadata_detail=None)

    self.assertEqual(result.artist_name, "adele")
    self.assertEqual(result.album_title, "25")
    self.assertEqual(result.track_title, "hello")
    self.assertEqual(result.year, "2015")
```

- [ ] **Step 2: Add a failing resolver test that explicit metadata still wins**

```python
def test_music_metadata_resolver_prefers_metadata_detail_over_embedded_tags(self) -> None:
    from app.services.music_metadata import MusicMetadataResolver

    candidate = build_candidate().model_copy(
        update={"raw_payload": {"host_transfer_source_path": "/downloads/file.flac"}}
    )
    resolver = MusicMetadataResolver()

    with patch.object(
        resolver,
        "_read_embedded_tag_hints",
        return_value=resolver._build_tag_hints(
            title="Wrong Song",
            artist_name="Wrong Artist",
            album_title="Wrong Album",
            year="2001",
            format_ext="flac",
        ),
    ):
        result = resolver.resolve(candidate=candidate, metadata_detail=build_track_detail())

    self.assertEqual(result.artist_name, "adele")
    self.assertEqual(result.album_title, "25")
    self.assertEqual(result.track_title, "hello")
    self.assertEqual(result.year, "2015")
```

- [ ] **Step 3: Add a failing planner test for tag-driven path recovery**

```python
def test_strategy_service_builds_track_path_from_embedded_tags_when_metadata_missing(self) -> None:
    candidate = build_candidate().model_copy(
        update={
            "format_tag": "flac",
            "raw_payload": {"host_transfer_source_path": "/downloads/unknown.flac"},
        }
    )
    service = OrganizeStrategyService(build_settings())

    with patch.object(
        service.metadata_resolver,
        "_read_embedded_tag_hints",
        return_value=service.metadata_resolver._build_tag_hints(
            title="Hello",
            artist_name="Adele",
            album_title="25",
            year="2015",
            format_ext="flac",
        ),
    ):
        plan = service.build_plan(candidate=candidate, metadata_detail=None)

    self.assertEqual(plan.target_relative_path, "adele/2015 - 25/hello.flac")
```

- [ ] **Step 4: Run the targeted test file and confirm red**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New tag tests fail because tag hints are not yet merged into resolver precedence

### Task 2: Implement Minimal Tag Parsing in `music_metadata.py`

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/music_metadata.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/pyproject.toml`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/requirements.txt`

- [ ] **Step 1: Add `mutagen` dependency**

Add `mutagen>=1.47.0,<2.0.0` to backend dependencies and requirements.

- [ ] **Step 2: Add a lightweight embedded-tag hint reader**

Inside `music_metadata.py`, add:

- soft import of `mutagen`
- `_read_embedded_tag_hints(source_path: str | None) -> _MusicPathHints`
- extraction helpers for `title`, `artist`, `album`, `date/year`

Use minimal normalization only. Do not create a new module yet.

- [ ] **Step 3: Merge tag hints into precedence**

Update `resolve(...)` so order becomes:

1. `MetadataDetail`
2. explicit raw payload
3. embedded tag hints
4. source-path hints
5. candidate fallback

- [ ] **Step 4: Run targeted tests and confirm green**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- New tag tests pass
- Existing organize integration tests still pass

### Task 3: Update Current-State Docs

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`

- [ ] **Step 1: Update README current-state wording**

Mention that organize metadata recovery now uses:

- explicit metadata
- source-path hints
- embedded audio tags when local files are available

- [ ] **Step 2: Update backend README**

Describe the resolver/layout split and note that tag parsing is now part of metadata recovery.

- [ ] **Step 3: Update the music organize design doc**

Record this as the second-round metadata enhancement and keep historical behavior notes intact.

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
- runtime mirror receives updated metadata resolver code

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

- [ ] **Step 4: Verify API shell remains intact**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
print("/openapi.json", client.get("/openapi.json").status_code)
print("/docs", client.get("/docs").status_code)
schema = client.get("/openapi.json").json()
print("preview_route", "/api/v1/plugin/musicpilot/organize/preview" in schema["paths"])
print("apply_route", "/api/v1/plugin/musicpilot/organize/apply" in schema["paths"])
PY
```

Expected:
- 200 for `/openapi.json` and `/docs`
- organize routes remain present
