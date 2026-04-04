# Music Organize Apply MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current movie/TV-oriented organize apply execution with a music-oriented apply path that keeps the existing MusicPilot plugin API, preview boundary, and organize record semantics intact.

**Architecture:** Keep `OrganizeService` and the existing `OrganizeStrategyService` as the outer shell. For apply only, stop calling `TransferChain.manual_transfer(...)`; instead build a music transfer plan from existing metadata/detail context and execute the file operation through a thin host storage runtime bridge. Preview, history, and path handoff stay unchanged.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Python stdlib (`pathlib`, `json`, subprocess), existing MoviePilot storage/filemanager runtime.

---

### Task 1: Lock The Behavior With Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Write the failing bridge test**

Add a test in `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py` that expects a new storage bridge to receive:

```python
{
    "source_fileitem": {
        "storage": "local",
        "path": "/downloads/Adele/25/01 - Hello.flac",
        "type": "file",
        "name": "01 - Hello.flac",
        "basename": "01 - Hello",
        "extension": ".flac",
        "size": 1024,
    },
    "target_storage": "local",
    "target_directory": "/library/music/adele/2015 - 25",
    "target_filename": "hello.flac",
    "transfer_type": "copy",
}
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected: fail because the current adapter still uses `manual_transfer(...)`.

- [ ] **Step 3: Write the failing service compatibility test**

Add a test in `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py` that:

- creates a candidate with `host_transfer_source_path`
- injects a fake host storage runtime result
- calls `OrganizeService.apply(...)`
- asserts:
  - `organize_backend == host`
  - `organize_status == applied`
  - `target_library_path` preserved
  - `target_relative_path` is the music layout path

- [ ] **Step 4: Run the failing integration test**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected: fail because the adapter still returns the old transfer-chain path semantics.

### Task 2: Add The Thin Host Storage Runtime Bridge

**Files:**
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_storage_runtime.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Create the bridge skeleton**

Create `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_storage_runtime.py` with a `HostStorageRuntimeBridge` that mirrors the style of `HostTransferRuntimeBridge`.

- [ ] **Step 2: Implement the isolated runtime call**

Inside the bridge, run a small Python snippet that imports:

```python
from app.chain.storage import StorageChain
from app.modules.filemanager import FileManagerModule
from app.schemas.file import FileItem
```

Then:

1. resolve `source_item = StorageChain().get_item(FileItem(**source_fileitem))`
2. validate `transfer_type` with `StorageChain().support_transtype(target_storage)`
3. resolve `target_diritem = FileManagerModule().get_folder(target_storage, Path(target_directory))` or via storage oper
4. execute copy/move/link/softlink against the target path
5. emit:

```json
{"success": true|false, "organize_status": "applied"|"failed", "message": "...", "target_path": "..."}
```

- [ ] **Step 3: Run the bridge unit test**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected: the new bridge-specific test passes.

### Task 3: Switch Apply To Music Execution

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Inject the new bridge**

Update `RealOrganizeAdapter.__init__` to accept:

```python
storage_runtime: HostStorageRuntimeBridge | None = None
```

and default it like:

```python
self.storage_runtime = storage_runtime or HostStorageRuntimeBridge()
```

- [ ] **Step 2: Replace apply execution**

In `_apply_once(...)`:

1. keep `_resolve_source(candidate)`
2. keep plan generation and result writing
3. remove the `manual_transfer` payload call
4. build:

```python
runtime_payload = {
    "source_fileitem": {...},
    "target_storage": source["storage"] or "local",
    "target_directory": str(PurePosixPath(plan.target_library_path).parent),
    "target_filename": str(PurePosixPath(plan.target_library_path).name),
    "transfer_type": self.settings.organize_transfer_type,
}
```

5. call `self.storage_runtime.transfer_file(**runtime_payload)`

- [ ] **Step 3: Keep outward result semantics stable**

Map runtime payload back into the existing `OrganizeAdapterResult`:

- `success=True` -> `OrganizeStatus.APPLIED`
- `success=False` -> `OrganizeStatus.FAILED`
- keep:
  - `organize_backend`
  - `target_library_path`
  - `target_relative_path`
  - `failure_reason`
  - `integration_point`

- [ ] **Step 4: Run organize tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected: pass.

### Task 4: Wire The MVP Through Dependency Injection And Docs

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/organize.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/core/dependencies.py`
- Create/Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/host_storage_runtime.py`

- [ ] **Step 1: Inject the bridge in dependencies**

Update dependency construction so `RealOrganizeAdapter` receives `HostStorageRuntimeBridge`.

- [ ] **Step 2: Document the MVP boundary**

Update docs to state:

- preview still unchanged
- apply is now music-layout + host-storage execution
- `manual_transfer(...)` is no longer the apply execution path

- [ ] **Step 3: Sync plugin runtime**

Mirror the new adapter/bridge/dependency files into `plugin_runtime`.

- [ ] **Step 4: Run full verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py
```

Expected:

- backend tests all green
- frontend build succeeds
- plugin runtime packages successfully
