# Music Dispatch Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace music dispatch's current MoviePilot video-oriented HTTP download path with a thin in-process host downloader runtime path that submits torrents directly to the configured downloader.

**Architecture:** Keep MusicPilot's metadata, search, subscription, organize, and plugin API boundaries unchanged. Only replace the host-backed dispatch adapter path for music candidates: build a thin host downloader bridge, switch `RealDownloadDispatchAdapter` to prefer that bridge for torrent-only music candidates, and preserve existing response/result shapes so downstream binding and handoff logic stay stable.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, MoviePilot downloader modules, unittest

---

### Task 1: Add Failing Dispatch Semantics Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Write the failing test for runtime-based music dispatch success**

```python
def test_dispatch_music_candidate_uses_runtime_downloader_bridge(self) -> None:
    runtime = FakeDownloaderRuntime(
        response={
            "success": True,
            "dispatch_status": "host_submitted",
            "download_id": "torrent-hash-001",
            "message": "添加下载任务成功",
        }
    )
    candidate = build_candidate(
        raw_payload={
            "host_context": {
                "torrent_info": {
                    "site": 1,
                    "site_name": "Stub Site",
                    "title": "Adele - 25 (2015) FLAC",
                    "description": "lossless",
                    "enclosure": "magnet:?xt=urn:btih:1",
                }
            }
        }
    )
    client = FakeHostClient(get_responses={"/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]}})
    adapter = RealDownloadDispatchAdapter(
        settings=build_settings(),
        client=client,  # type: ignore[arg-type]
        path_handoff_service=HostPathHandoffService(settings=build_settings(), client=client),  # type: ignore[arg-type]
        downloader_runtime=runtime,
    )

    result = adapter.dispatch(candidate=candidate, downloader_id="QB", manual_confirm=True)

    self.assertEqual(result.dispatch_status, "host_submitted")
    self.assertEqual(result.downloader_task_id, "torrent-hash-001")
    self.assertEqual(runtime.calls[-1]["downloader"], "QB")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest backend.tests.test_moviepilot_semantics.RealDownloadDispatchAdapterTest.test_dispatch_music_candidate_uses_runtime_downloader_bridge`

Expected: FAIL because `RealDownloadDispatchAdapter` does not yet accept or use a downloader runtime bridge.

- [ ] **Step 3: Write the failing test for runtime failure mapping**

```python
def test_dispatch_music_candidate_maps_runtime_failure_without_http_fallback(self) -> None:
    runtime = FakeDownloaderRuntime(
        response={
            "success": False,
            "dispatch_status": "host_rejected",
            "download_id": None,
            "message": "下载器拒绝任务",
        }
    )
    candidate = build_candidate(
        raw_payload={
            "host_context": {
                "torrent_info": {
                    "site": 1,
                    "site_name": "Stub Site",
                    "title": "Adele - 25 (2015) FLAC",
                    "description": "lossless",
                    "enclosure": "magnet:?xt=urn:btih:1",
                }
            }
        }
    )
    client = FakeHostClient(get_responses={"/api/v1/download/clients": {"items": [{"name": "QB", "type": "qbittorrent"}]}})
    adapter = RealDownloadDispatchAdapter(
        settings=build_settings(),
        client=client,  # type: ignore[arg-type]
        path_handoff_service=HostPathHandoffService(settings=build_settings(), client=client),  # type: ignore[arg-type]
        downloader_runtime=runtime,
    )

    result = adapter.dispatch(candidate=candidate, downloader_id="QB", manual_confirm=True)

    self.assertEqual(result.dispatch_status, "host_rejected")
    self.assertEqual(result.failure_reason, "下载器拒绝任务")
    self.assertEqual([call[1] for call in client.calls if call[0] == "POST"], [])
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest backend.tests.test_moviepilot_semantics.RealDownloadDispatchAdapterTest.test_dispatch_music_candidate_maps_runtime_failure_without_http_fallback`

Expected: FAIL because runtime failure is not yet mapped and the adapter still posts to MoviePilot `/api/v1/download/add`.

- [ ] **Step 5: Commit the red tests**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
git add backend/tests/test_moviepilot_semantics.py docs/superpowers/plans/2026-04-05-music-dispatch-redesign.md
git commit -m "test: lock music dispatch runtime semantics"
```

### Task 2: Add Thin Host Downloader Runtime Bridge

**Files:**
- Create: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/host_downloader_runtime.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/host_downloader_runtime.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Write the failing bridge test**

```python
def test_runtime_bridge_uses_qbittorrent_module_download(self) -> None:
    bridge = HostDownloaderRuntimeBridge(module_factory=fake_module_factory)

    result = bridge.submit_torrent(
        downloader="QB",
        content="magnet:?xt=urn:btih:1",
        title="Adele - 25",
        site_name="Stub Site",
    )

    self.assertTrue(result["success"])
    self.assertEqual(result["download_id"], "torrent-hash-001")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest backend.tests.test_moviepilot_semantics.HostDownloaderRuntimeBridgeTest.test_runtime_bridge_uses_qbittorrent_module_download`

Expected: FAIL because `HostDownloaderRuntimeBridge` does not exist yet.

- [ ] **Step 3: Write the minimal bridge implementation**

```python
class HostDownloaderRuntimeBridge:
    def submit_torrent(self, *, downloader: str, content: str | bytes, title: str, site_name: str, download_dir: str | None = None) -> dict[str, Any]:
        service = DownloaderHelper().get_service(downloader)
        if not service or not service.module:
            raise HostTransportError(...)
        module = service.module
        result = module.download(
            content=content,
            download_dir=Path(download_dir or "."),
            cookie="",
            downloader=downloader,
            category=site_name,
        )
        ...
```

- [ ] **Step 4: Run the bridge test to verify it passes**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest backend.tests.test_moviepilot_semantics.HostDownloaderRuntimeBridgeTest.test_runtime_bridge_uses_qbittorrent_module_download`

Expected: PASS

- [ ] **Step 5: Commit the bridge**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
git add backend/app/adapters/host_downloader_runtime.py plugin_runtime/plugins/musicpilot/adapters/host_downloader_runtime.py backend/tests/test_moviepilot_semantics.py
git commit -m "feat: add host downloader runtime bridge"
```

### Task 3: Switch Real Dispatch Adapter to Music Runtime Path

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/download_dispatch.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/host_integration.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/dependencies.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/download_dispatch.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/services/host_integration.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/core/dependencies.py`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Wire the runtime bridge into the adapter constructor**

```python
def __init__(..., downloader_runtime: HostDownloaderRuntimeBridge | None = None):
    self.downloader_runtime = downloader_runtime or HostDownloaderRuntimeBridge()
```

- [ ] **Step 2: Add a focused helper that decides when a candidate should use music runtime dispatch**

```python
def _should_use_music_runtime_dispatch(self, candidate: SearchCandidateDetail, context_payload: dict[str, Any]) -> bool:
    media_in = self._extract_media_payload(context_payload)
    return media_in is None
```

- [ ] **Step 3: Implement minimal runtime dispatch path**

```python
runtime_result = self.downloader_runtime.submit_torrent(
    downloader=target_downloader,
    content=torrent_in.get("enclosure") or torrent_in.get("content"),
    title=str(torrent_in.get("title") or candidate.title),
    site_name=str(torrent_in.get("site_name") or candidate.site_name),
)
```

- [ ] **Step 4: Map runtime result back into existing `DispatchAdapterResult` shape**

```python
dispatch_status = runtime_result["dispatch_status"]
download_id = self._optional_text(runtime_result.get("download_id"))
message = self._optional_text(runtime_result.get("message"))
```

- [ ] **Step 5: Run the targeted adapter tests**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest backend.tests.test_moviepilot_semantics.RealDownloadDispatchAdapterTest backend.tests.test_moviepilot_semantics.HostDownloaderRuntimeBridgeTest`

Expected: PASS

- [ ] **Step 6: Commit the adapter switch**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
git add backend/app/adapters/download_dispatch.py backend/app/services/host_integration.py backend/app/core/dependencies.py plugin_runtime/plugins/musicpilot/adapters/download_dispatch.py plugin_runtime/plugins/musicpilot/services/host_integration.py plugin_runtime/plugins/musicpilot/core/dependencies.py backend/tests/test_moviepilot_semantics.py
git commit -m "feat: route music dispatch through downloader runtime"
```

### Task 4: Verify End-to-End Runtime Behavior

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`
- Test: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Run full backend test suite**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected: PASS

- [ ] **Step 2: Repackage plugin runtime**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected: PASS and updated runtime mirror under `plugin_runtime/plugins/musicpilot/`

- [ ] **Step 3: Run real host runtime smoke**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot
CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev .venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.factory import app
from app.core.plugin import PluginManager
from app.api.endpoints.plugin import register_plugin_api

PluginManager().start('musicpilot')
register_plugin_api('musicpilot')
client = TestClient(app)
print(client.get('/api/v1/plugin/musicpilot/health').status_code)
PY
```

Expected: plugin loads successfully and health remains available.

- [ ] **Step 4: Run real subscription dispatch smoke**

Run a real `track-hello` subscription run in host runtime and confirm:
- `dispatch_status=host_submitted`
- no `无法识别媒体信息`
- if host history/path handoff is still absent, run may stop after dispatch without treating organize as code failure

- [ ] **Step 5: Update runtime verification docs**

Document the new truth in:
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`

- [ ] **Step 6: Commit the verification/docs update**

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
git add docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md docs/28_项目整体任务盘点与执行路线.md
git commit -m "docs: record music dispatch runtime redesign verification"
```
