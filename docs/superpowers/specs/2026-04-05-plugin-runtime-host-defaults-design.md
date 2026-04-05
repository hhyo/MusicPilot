# Plugin Runtime Host Defaults Design

## Goal

When MusicPilot runs as a real MoviePilot plugin, it should not require the operator to manually export `MUSICPILOT_HOST_*` variables just to enable the existing real host search / dispatch adapters.

This design adds **plugin-runtime-only defaults** so the installed plugin can derive host integration settings from the host process itself.

## Problem

Current real runtime verification proved:

- real `MusicBrainz` metadata works
- real `ListenBrainz` charts work
- real host plugin API can execute `subscription -> run`

But the same run still falls back to:

- `mock_host_search`
- `mock_download_dispatch`

because `host_integration_enabled=false` unless `MUSICPILOT_HOST_*` is manually injected into the process.

That is fine for local backend development, but it is not a good default for the actual installed plugin.

## Constraints

- Do not change the search / dispatch adapter interfaces.
- Do not change plugin API schemas.
- Do not change organize semantics.
- Do not add a new strategy system.
- Do not require plugin users to duplicate host API token / port configuration unless they want to override defaults.

## Design

### 1. Scope

Only change `MusicPilot` settings defaults.

Local backend behavior stays unchanged.

Installed plugin behavior changes only when the package is imported as:

- `app.plugins.musicpilot.*`

### 2. Runtime detection

Treat the package as “plugin runtime” only when the current module name starts with:

- `app.plugins.musicpilot.`

This keeps local FastAPI development under `backend/app/*` unchanged.

### 3. Derived defaults

When running as an installed plugin, try to import host settings from:

- `app.core.config.settings`

If that import succeeds and yields a usable `API_TOKEN`, derive:

- `host_integration_enabled = true`
- `host_base_url = http://127.0.0.1:{host_settings.PORT}`
- `host_auth_token = host_settings.API_TOKEN`
- `host_auth_mode = x_api_key`
- `host_api_key_header_name = X-API-KEY`
- `host_search_mode = prefer_host`
- `host_dispatch_mode = prefer_host`
- `host_organize_mode = prefer_host`

### 4. Override precedence

Environment variables must continue to win.

So this change only supplies defaults when the user did not explicitly set:

- `MUSICPILOT_HOST_INTEGRATION_ENABLED`
- `MUSICPILOT_HOST_BASE_URL`
- `MUSICPILOT_HOST_AUTH_TOKEN`
- `MUSICPILOT_HOST_*_MODE`

### 5. Failure behavior

If host settings cannot be imported, or `API_TOKEN` is unavailable:

- keep existing local defaults
- do not pretend host integration is enabled

This preserves current failure semantics and avoids fake runtime assumptions.

## Why this is the smallest useful change

This does not introduce:

- direct in-process search chain calls
- direct in-process dispatch chain calls
- new adapters
- new APIs

It simply lets the already-written real host HTTP adapters activate automatically in the one environment where that behavior is obviously desired: the installed MoviePilot plugin runtime.

## Validation target

After this change, a real host runtime should show:

- `host_integration_enabled=true`
- `active_search_adapter=real_host_search`
- `active_dispatch_adapter=real_download_dispatch`

And a real `track chart entry -> subscription -> run` should attempt real host-backed search / dispatch instead of the current mock path.
