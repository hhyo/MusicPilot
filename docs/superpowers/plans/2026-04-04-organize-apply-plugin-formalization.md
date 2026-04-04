# Organize Apply Plugin Formalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current local-workspace bridge used by music `organize apply` with an in-process MoviePilot plugin runtime integration, while keeping the plugin API, preview flow, path handoff, and record semantics unchanged.

**Architecture:** Keep `OrganizeService` and `RealOrganizeAdapter.apply()` as the MusicPilot-side shell, but replace the internals of `HostStorageRuntimeBridge` so it imports and calls host file/storage modules directly from the running plugin process instead of guessing a local host repo path and launching a subprocess. After that, remove the now-obsolete `host_transfer_runtime` validation bridge and update docs/runtime mirrors to reflect the formalized boundary.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, MoviePilot plugin runtime, unittest, Vue/Vite build verification

---

## File Structure

### Files to modify

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_storage_runtime.py`
  - Replace `_resolve_host_root()` + `subprocess` bridge with in-process host module access.
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py`
  - Keep API surface stable; only adjust wording or capability strings if needed after runtime formalization.
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`
  - Replace subprocess-oriented bridge tests with in-process bridge tests.
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md`
  - Update current apply semantics wording.
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
  - Remove stale `/transfer/manual` language from current organize apply description.
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`
  - Mark the formalized runtime boundary as implemented.
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/24_插件正式化遗留清理TODO.md`
  - Mark the storage bridge cleanup item done and narrow remaining TODOs.

### Files to delete

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_transfer_runtime.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/host_transfer_runtime.py`

### Runtime mirror files to sync

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/host_storage_runtime.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/organize.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/core/dependencies.py`

### Files explicitly out of scope

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/host_path_handoff.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_search.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/download_dispatch.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py` preview path
- Any file under `/Users/lihuanhuan/PycharmProjects/MoviePilot*`

---

### Task 1: Replace the storage runtime bridge with in-process host module access

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_storage_runtime.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Write the failing test for “no subprocess / no host root lookup”**

Add a test like this:

```python
class HostStorageRuntimeBridgeTest(unittest.TestCase):
    def test_transfer_file_uses_in_process_manager_instead_of_subprocess(self) -> None:
        bridge = HostStorageRuntimeBridge()
        fake_manager = FakeManagerModule.for_copy_success(
            source_path="/downloads/Adele/25/01 - Hello.flac",
            target_root="/library/music",
        )

        with (
            patch.object(HostStorageRuntimeBridge, "_build_manager", return_value=fake_manager),
            patch("app.adapters.host_storage_runtime.subprocess.run", side_effect=AssertionError("subprocess should not be used")),
        ):
            result = bridge.transfer_file(
                source_fileitem={
                    "storage": "local",
                    "path": "/downloads/Adele/25/01 - Hello.flac",
                    "type": "file",
                    "name": "01 - Hello.flac",
                    "basename": "01 - Hello",
                    "extension": ".flac",
                    "size": 1024,
                },
                target_storage="local",
                target_directory="/library/music/Adele/2015 - 25",
                target_filename="hello.flac",
                transfer_type="copy",
                conflict_policy="skip_existing",
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["organize_status"], "applied")
        self.assertEqual(result["target_path"], "/library/music/Adele/2015 - 25/hello.flac")
```

- [ ] **Step 2: Run the target test and confirm it fails for the right reason**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected:

- FAIL because `HostStorageRuntimeBridge` still calls `subprocess.run`
- or FAIL because `_build_manager` does not exist yet

- [ ] **Step 3: Implement the in-process bridge**

Replace the current bridge body with direct imports and host module calls. The target structure is:

```python
from pathlib import Path
from typing import Any

from app.modules.filemanager import FileManagerModule
from app.schemas.file import FileItem


class HostStorageRuntimeBridge:
    def __init__(self) -> None:
        self._manager: FileManagerModule | None = None

    def transfer_file(
        self,
        *,
        source_fileitem: dict[str, Any],
        target_storage: str,
        target_directory: str,
        target_filename: str,
        transfer_type: str,
        conflict_policy: str = "skip_existing",
    ) -> dict[str, Any]:
        manager = self._build_manager()
        source_request = FileItem(**source_fileitem)
        source_item = manager.get_file_item(storage=source_request.storage, path=Path(source_request.path))
        if not source_item:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"文件不存在：{source_request.path}",
            }

        if source_item.type != "file":
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"当前音乐整理 MVP 仅支持单文件输入：{source_item.path}",
            }

        supported = manager.support_transtype(target_storage) or {}
        if transfer_type not in supported:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"存储 {target_storage} 不支持整理方式：{transfer_type}",
            }

        source_oper = self._get_storage_oper(manager, source_item.storage)
        target_oper = self._get_storage_oper(manager, target_storage)
        if not source_oper or not target_oper:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"未找到可用存储操作对象：{source_item.storage} -> {target_storage}",
            }

        if source_item.storage != "local" or target_storage != "local":
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"当前音乐整理 MVP 仅支持本地到本地整理：{source_item.storage} -> {target_storage}",
            }

        target_dir = Path(target_directory)
        target_diritem = target_oper.get_folder(target_dir)
        if not target_diritem:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"目标目录获取失败：{target_dir.as_posix()}",
            }

        target_file, resolve_error = self._resolve_target_path(
            target_oper=target_oper,
            target_dir=target_dir,
            target_name=target_filename,
            conflict_policy=conflict_policy,
        )
        if resolve_error:
            return {
                "success": False,
                "organize_status": "skipped" if "已存在" in resolve_error else "failed",
                "message": resolve_error,
                "target_path": (target_dir / target_filename).as_posix(),
            }

        state = self._execute_transfer(
            source_oper=source_oper,
            source_item=source_item,
            transfer_type=transfer_type,
            target_file=target_file,
        )
        if not state:
            return {
                "success": False,
                "organize_status": "failed",
                "message": f"{source_item.path} {transfer_type} 失败",
                "target_path": target_file.as_posix(),
            }

        return {
            "success": True,
            "organize_status": "applied",
            "message": "",
            "target_path": target_file.as_posix(),
        }
```

Required cleanups in the same file:

- Delete `_STORAGE_TRANSFER_BRIDGE`
- Delete `_RESULT_MARKER`
- Delete `_resolve_host_root()`
- Delete `_extract_result_payload()`
- Delete all `subprocess`, `json`, `sys`, `textwrap` imports

- [ ] **Step 4: Run the bridge test again**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected:

- PASS for the new in-process bridge tests

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_storage_runtime.py \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py
git commit -m "refactor: replace storage subprocess bridge with in-process runtime"
```

### Task 2: Keep apply API semantics stable while formalizing the runtime

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Add a failing test that verifies current outward semantics remain unchanged**

Add or update a test like:

```python
def test_apply_keeps_host_backend_and_record_semantics_with_storage_runtime(self) -> None:
    candidate = build_candidate(
        raw_payload={"host_transfer_source_path": "/downloads/Adele-25.flac", "host_transfer_filetype": "file"}
    )
    runtime = FakeStorageRuntime(
        response={
            "success": True,
            "organize_status": "applied",
            "message": "",
            "target_path": "/library/music/Adele/2015 - 25/hello.flac",
        }
    )
    adapter = RealOrganizeAdapter(
        settings=build_settings(),
        client=FakeHostClient(),
        storage_runtime=runtime,
    )

    result = adapter.apply(
        organize_job_id="organize-002",
        candidate=candidate,
        metadata_detail=None,
        binding_id=None,
        plan=build_plan(),
    )

    self.assertEqual(result.organize_backend, AdapterMode.HOST)
    self.assertEqual(result.organize_status, OrganizeStatus.APPLIED)
    self.assertEqual(result.integration_point, "RealOrganizeAdapter.apply.music_storage_runtime_transfer")
    self.assertEqual(result.target_library_path, "/library/music/Adele/2015 - 25/hello.flac")
```

- [ ] **Step 2: Run targeted organize tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:

- PASS if no outward behavior changed
- FAIL if record serialization or apply integration point drifted

- [ ] **Step 3: Make the smallest adjustments in `organize.py` only if needed**

Allowed changes:

- keep `preview()` untouched
- keep `path_handoff` untouched
- keep `OrganizeAdapterResult` structure untouched
- only adjust `integration_point`, `capability_source`, or `target_relative_path` derivation if tests prove drift

Do **not** add any new abstraction here. Keep the shape:

```python
data = self.storage_runtime.transfer_file(**runtime_payload)
success = bool(data.get("success"))
default_status = OrganizeStatus.APPLIED if success else OrganizeStatus.FAILED
...
return self._build_result(...)
```

- [ ] **Step 4: Re-run both organize and semantics tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:

- Both suites PASS

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py
git commit -m "refactor: formalize organize apply runtime semantics"
```

### Task 3: Remove the obsolete transfer runtime validation bridge

**Files:**
- Delete: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_transfer_runtime.py`
- Delete: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/host_transfer_runtime.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Write the failing cleanup expectation**

Remove the `HostTransferRuntimeBridgeTest` block from `test_moviepilot_semantics.py` and update imports so the test suite no longer depends on the deleted bridge.

The test-file import section should end up like:

```python
from app.adapters.host_storage_runtime import HostStorageRuntimeBridge
from app.adapters.organize import RealOrganizeAdapter
```

and no longer include:

```python
from app.adapters.host_transfer_runtime import HostTransferRuntimeBridge
```

- [ ] **Step 2: Delete the obsolete bridge files**

Delete:

```text
/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_transfer_runtime.py
/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/host_transfer_runtime.py
```

- [ ] **Step 3: Run the full backend suite**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests
```

Expected:

- PASS
- no import errors referencing `host_transfer_runtime`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete transfer runtime bridge"
```

### Task 4: Sync docs and plugin runtime mirror

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/README.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/19_organize_apply_运行态验证.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/24_插件正式化遗留清理TODO.md`
- Modify or sync mirror: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/...`

- [ ] **Step 1: Update stale README and architecture wording**

Make these exact content changes:

- In `README.md`, replace the current organize apply sentence that still says:

```md
`apply` 固定映射 `/api/v1/transfer/manual`
```

with:

```md
`apply` 当前通过宿主底层 file/storage transfer runtime 执行音乐文件整理；`preview` 仍固定映射 `/api/v1/transfer/name`。
```

- In `docs/19_organize_apply_运行态验证.md`, move the file into “historical verification” wording and add a note that it documents the earlier `manual_transfer(...)` migration experiment rather than the current apply implementation.

- [ ] **Step 2: Update the cleanup TODO status**

In `docs/24_插件正式化遗留清理TODO.md`, change the storage-bridge item from pending cleanup to done once Task 1 is complete, and narrow the remaining cleanup item to the obsolete transfer bridge only.

- [ ] **Step 3: Rebuild the plugin runtime mirror**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
python3 scripts/package_plugin.py
```

Expected:

- `Packaged MusicPilot placeholder runtime into plugin_runtime/plugins/musicpilot`

- [ ] **Step 4: Verify frontend and public API shell**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build

cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
assert client.get('/openapi.json').status_code == 200
assert client.get('/docs').status_code == 200
assert any(route.path == '/api/v1/plugin/musicpilot/organize/preview' for route in app.routes)
assert any(route.path == '/api/v1/plugin/musicpilot/organize/apply' for route in app.routes)
print('openapi/docs/routes ok')
PY
```

Expected:

- frontend build succeeds
- openapi/docs/routes check prints `openapi/docs/routes ok`

- [ ] **Step 5: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/README.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/19_organize_apply_运行态验证.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/24_插件正式化遗留清理TODO.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot
git commit -m "docs: align organize apply with plugin runtime formalization"
```

## Self-Review

- Spec coverage:
  - remove `_resolve_host_root` / `subprocess` / `sys.path`: covered in Task 1
  - keep apply boundary small: covered in Task 2
  - remove old bridge residue: covered in Task 3
  - sync docs/runtime mirror: covered in Task 4
- Placeholder scan:
  - no TBD/TODO placeholders in task steps
- Type consistency:
  - plan consistently uses `HostStorageRuntimeBridge.transfer_file(...)` as the kept bridge API
  - `RealOrganizeAdapter.apply.music_storage_runtime_transfer` remains the outward integration point

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-04-organize-apply-plugin-formalization.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
