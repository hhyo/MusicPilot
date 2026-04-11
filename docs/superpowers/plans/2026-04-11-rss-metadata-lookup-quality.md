# RSS Metadata Lookup Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve RSS `search_lookup` hit quality by normalizing hints and trying a small ordered keyword fallback sequence before giving up.

**Architecture:** Keep discovery contracts unchanged and concentrate the quality improvement inside `MetadataService.lookup_detail()`. Add deterministic normalization helpers, ordered keyword candidates, and focused tests for track/album/artist lookup behavior.

**Tech Stack:** FastAPI, SQLAlchemy, unittest, existing metadata provider adapters.

---

### Task 1: Add failing lookup-quality tests

**Files:**
- Modify: `backend/tests/test_metadata_provider.py`

- [ ] Add failing tests for track title noise normalization, album fallback keyword order, and artist-only lookup stability.
- [ ] Run `cd backend && .venv/bin/python -m unittest discover -s tests -p 'test_metadata_provider.py'` and verify the new tests fail for the expected reason.

### Task 2: Implement normalized lookup keyword building

**Files:**
- Modify: `backend/app/services/metadata.py`

- [ ] Add helper functions to normalize titles and build ordered keyword candidates for track/album/artist lookup.
- [ ] Update `lookup_detail()` to try keyword candidates in order until one produces a valid winner.
- [ ] Re-run the targeted metadata tests and verify they pass.

### Task 3: Tighten winner selection without changing API behavior

**Files:**
- Modify: `backend/app/services/metadata.py`
- Test: `backend/tests/test_metadata_provider.py`

- [ ] Extend winner selection tests to cover normalized title matching and album strictness.
- [ ] Implement the minimal scoring/normalization needed to satisfy the new tests.
- [ ] Re-run targeted tests until green.

### Task 4: Documentation and regression verification

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

- [ ] Update docs to mention RSS `search_lookup` now uses normalized ordered lookup fallback.
- [ ] Run `cd backend && .venv/bin/python -m unittest discover -s tests`.
- [ ] If green, commit the work.
