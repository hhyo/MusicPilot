# Plugin Runtime Host Defaults Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable real host search / dispatch by default when MusicPilot runs as an installed MoviePilot plugin, without changing local backend defaults.

**Architecture:** Add plugin-runtime-aware defaults in `core/config.py`, cover them with focused tests, then verify the installed plugin in a real host runtime without manually exporting `MUSICPILOT_HOST_*`. The adapters themselves stay unchanged.

**Tech Stack:** Python, Pydantic Settings, FastAPI TestClient, MoviePilot host runtime

---

### Task 1: Add failing tests for plugin-runtime-derived defaults

**Files:**
- Modify: `backend/tests/test_moviepilot_semantics.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Write the failing tests**

Add tests that exercise pure helper functions rather than the cached global settings object:

```python
def test_plugin_runtime_defaults_enable_host_integration_from_host_settings():
    class HostSettings:
        PORT = 3001
        API_TOKEN = "host-token"

    defaults = _derive_plugin_runtime_host_defaults(
        module_name="app.plugins.musicpilot.core.config",
        host_settings=HostSettings(),
    )

    assert defaults["host_integration_enabled"] is True
    assert defaults["host_base_url"] == "http://127.0.0.1:3001"
    assert defaults["host_auth_token"] == "host-token"
    assert defaults["host_search_mode"] == "prefer_host"
    assert defaults["host_dispatch_mode"] == "prefer_host"
```

```python
def test_local_backend_module_name_does_not_enable_plugin_runtime_defaults():
    class HostSettings:
        PORT = 3001
        API_TOKEN = "host-token"

    defaults = _derive_plugin_runtime_host_defaults(
        module_name="app.core.config",
        host_settings=HostSettings(),
    )

    assert defaults == {}
```

```python
def test_plugin_runtime_defaults_require_host_token():
    class HostSettings:
        PORT = 3001
        API_TOKEN = None

    defaults = _derive_plugin_runtime_host_defaults(
        module_name="app.plugins.musicpilot.core.config",
        host_settings=HostSettings(),
    )

    assert defaults == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected: FAIL because `_derive_plugin_runtime_host_defaults` does not exist yet.

- [ ] **Step 3: Implement the minimal helper**

Add a pure helper in `backend/app/core/config.py`:

```python
def _derive_plugin_runtime_host_defaults(*, module_name: str, host_settings: object | None) -> dict[str, object]:
    ...
```

It should:

- only activate for module names starting with `app.plugins.musicpilot.`
- require `host_settings.PORT`
- require `host_settings.API_TOKEN`
- return the derived host defaults dict

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected: PASS


### Task 2: Wire plugin-runtime defaults into Settings

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `plugin_runtime/plugins/musicpilot/core/config.py` (via packaging sync)

- [ ] **Step 1: Add plugin-runtime detection and host-settings import wrapper**

Implement small helpers such as:

```python
def _is_plugin_runtime_module(module_name: str) -> bool:
    return module_name.startswith("app.plugins.musicpilot.")

def _load_host_settings_for_plugin_runtime(module_name: str) -> object | None:
    if not _is_plugin_runtime_module(module_name):
        return None
    try:
        from app.core.config import settings as host_settings
    except Exception:
        return None
    return host_settings
```

- [ ] **Step 2: Apply derived defaults to host-related settings fields**

Use `default_factory` or equivalent helper wrappers so these fields pick up plugin-runtime defaults:

- `host_integration_enabled`
- `host_base_url`
- `host_auth_token`
- `host_search_mode`
- `host_dispatch_mode`
- `host_organize_mode`

The environment must still override the defaults.

- [ ] **Step 3: Run focused tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
```

Expected: PASS


### Task 3: Verify real host runtime without manual `MUSICPILOT_HOST_*`

**Files:**
- Modify: `docs/32_真实宿主_subscription_主链运行态验证.md`
- Modify: `docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`

- [ ] **Step 1: Sync the current runtime package into host plugins**

Run:

```bash
rsync -a --delete /Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/ /Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/plugins/musicpilot/
```

- [ ] **Step 2: Verify health/runtime state in a real host process**

Run a host-side TestClient session with:

```bash
CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev \
MUSICPILOT_DATABASE_URL=sqlite:////tmp/musicpilot-host-defaults-check.db \
MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz \
MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz \
MUSICPILOT_SUBSCRIPTION_SCHEDULER_ENABLED=false \
.venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from app.factory import app
with TestClient(app) as client:
    data = client.get('/api/v1/plugin/musicpilot/health', headers={'X-API-KEY': 'moviepilot-dev-token'}).json()['data']
    print(data['host_integration'])
PY
```

Expected:

- `host_integration_enabled=true`
- `active_search_adapter=real_host_search`
- `active_dispatch_adapter=real_download_dispatch`

- [ ] **Step 3: Re-run `track chart entry -> subscription -> run`**

Use the same host-side TestClient style as before and capture:

- `execution_status`
- `summary_json`
- adapter/backends

Expected:

- no longer `mock_host_search`
- no longer `mock_download_dispatch`

- [ ] **Step 4: Update verification docs**

Document what changed:

- plugin runtime now self-derives host defaults
- real host acquisition path can activate without manual `MUSICPILOT_HOST_*`


### Task 4: Full regression and runtime sync

**Files:**
- Modify: `plugin_runtime/plugins/musicpilot/core/config.py` (packaging output)

- [ ] **Step 1: Run backend full test suite**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests
```

Expected: PASS

- [ ] **Step 2: Rebuild frontend**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Expected: PASS

- [ ] **Step 3: Re-package runtime**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/32_真实宿主_subscription_主链运行态验证.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md \
        /Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/core/config.py
git commit -m "feat: derive host defaults in plugin runtime"
```
