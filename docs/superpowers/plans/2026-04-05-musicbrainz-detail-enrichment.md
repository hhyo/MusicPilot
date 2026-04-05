# MusicBrainz Detail Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正 MusicBrainz album/track detail 的结构化语义，让专辑曲目列表和歌曲所属专辑关系可被当前产品链稳定复用。

**Architecture:** 保持现有 `/metadata/*` API 和 release-group 作为 album detail 主 id 语义不变，只增强 `MusicBrainzMetadataProviderAdapter` 的 detail 组装逻辑。Album detail 采用 `release-group -> best release -> release track listing` 两跳查询；track detail 则把 `related_album` 对齐到 release-group 语义。

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, httpx, unittest

---

### Task 1: Write failing tests for album/track detail enrichment

**Files:**
- Modify: `backend/tests/test_metadata_provider.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:

```python
def test_album_detail_uses_release_tracks_instead_of_release_list(self) -> None:
    ...

def test_track_detail_related_album_points_to_release_group(self) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_metadata_provider.py'`

Expected: FAIL because current adapter still maps release list as tracks and still returns release id as album id.

### Task 2: Implement minimal schema support

**Files:**
- Modify: `backend/app/schemas/metadata.py`
- Modify: `frontend/src/types/metadata.ts`

- [ ] **Step 1: Add optional fields**

Add optional fields:

```python
class MetadataReference(BaseModel):
    ...
    track_number: int | None = None
    disc_number: int | None = None

class MetadataDetail(MetadataSummary):
    ...
    disambiguation: str | None = None
    release_count: int | None = None
```

- [ ] **Step 2: Mirror frontend types**

Add matching optional fields in `frontend/src/types/metadata.ts`.

- [ ] **Step 3: Run targeted tests**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_metadata_provider.py'`

Expected: still FAIL on behavior, but no schema/type errors.

### Task 3: Implement MusicBrainz detail enrichment

**Files:**
- Modify: `backend/app/adapters/metadata_provider.py`

- [ ] **Step 1: Add best-release selection helpers**

Implement small helpers for:

- choosing best release from a release-group
- fetching `release/{id}` with track listing
- mapping release tracks to `MetadataReference`

- [ ] **Step 2: Update album detail**

Make `get_album_detail()`:

- fetch release-group detail
- select best release
- fetch release detail
- build `tracks` from `media[].tracks[]`
- expose `release_count` and `disambiguation`

- [ ] **Step 3: Update track detail**

Make `get_track_detail()`:

- use release-group id for `related_album.id` when available
- fall back to release lookup if recording payload lacks `release-group`
- expose `disambiguation`

- [ ] **Step 4: Run targeted tests**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_metadata_provider.py'`

Expected: PASS

### Task 4: Docs and regression

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

- [ ] **Step 1: Update docs**

Document that MusicBrainz detail now includes:

- real album track listing
- stable track -> album relationship
- richer detail fields for downstream query/discovery use

- [ ] **Step 2: Run backend full suite**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected: PASS

- [ ] **Step 3: Run frontend build**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected: PASS

- [ ] **Step 4: Repackage runtime**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected: PASS
