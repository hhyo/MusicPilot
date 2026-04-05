# Apple Music Discovery Provider Design

Date: 2026-04-05

## Context

MusicPilot already has a stable discovery baseline:

- `ListenBrainz` is the current real chart provider.
- discovery productization is already complete for the current chart surface.
- discovery entries can already open `metadata` detail through the existing `DiscoveryTarget` bridge.
- chart responses already pass through a shared discovery assembly layer.
- chart and metadata cache already work in real MoviePilot plugin runtime.

The next product step is to expand discovery breadth with a new real chart source. The user has explicitly chosen to start with `Apple Music` and to defer `Spotify`, `Billboard`, `QQ 音乐`, and `网易云音乐` to later phases.

This phase must do two things at once:

1. Add Apple Music charts as a real discovery provider.
2. Define the `discovery -> metadata` conversion layer in a way that survives future provider expansion without large refactors.

The most important architectural constraint is that Apple Music chart entries do not naturally arrive with MusicBrainz ids. That means the current “direct provider id opens metadata detail” path is insufficient as the only discovery bridge.

## Goals

1. Add Apple Music as a real chart provider using official Apple Music API charts.
2. Support `songs` and `albums` charts in the first round.
3. Preserve current discovery API routes and current chart page structure.
4. Upgrade `DiscoveryTarget` so future providers can convert into metadata through a stable contract.
5. Keep provider-specific mapping logic out of the page layer.
6. Reuse the current runtime TTL cache strategy.
7. Use an externally supplied `developer token` and configured `storefront`; do not generate Apple tokens inside MusicPilot.

## Non-Goals

This phase does not:

- implement Apple Music developer token generation
- add user-token or personalized Apple Music access
- add Apple playlists, music videos, radio, or editorial pages
- add Spotify, Billboard, QQ 音乐, or 网易云音乐 providers
- implement chart snapshot persistence or diff tracking
- implement multi-storefront aggregation
- implement discovery-to-search conversion
- change subscription execution semantics

## Product Direction

The first Apple Music phase is a discovery breadth expansion, not a full provider domain.

That means the product goal is:

- let the charts page surface Apple songs and albums as first-class discovery content
- let each Apple entry carry a stable conversion contract toward metadata
- avoid making the UI aware of Apple-specific payload structure

The page should continue to feel like one unified discovery product, not a set of provider-specific mini apps.

## Official API Assumptions

This design assumes usage of Apple Music official chart endpoints and catalog semantics:

- Apple Music API charts by storefront
- charts resources for songs and albums
- server-side requests authenticated with a developer token

The implementation will treat `developer token + storefront` as deployment-time configuration. Missing configuration disables the provider cleanly.

## Design Overview

### Current Chain

Today the discovery flow is:

`ChartProviderAdapter -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView`

This structure is good enough to absorb Apple Music without changing routes or the page shell.

### New Chain

After this phase the chain becomes:

`AppleMusicChartProviderAdapter -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView -> DiscoveryTarget resolver`

The important change is not only the new provider adapter. The important change is that `DiscoveryTarget` must stop assuming all providers can supply a metadata-ready provider id directly.

## Provider Scope

### First-Round Apple Charts

The provider will expose:

- top songs
- top albums

Each Apple chart becomes a `ChartInfo` item in the same list as existing providers.

The first-round provider characteristics are:

- chart source: `apple_music`
- real data source
- global or configured storefront-specific scope
- single storefront per deployment

### Deferred Apple Capabilities

The following remain explicitly deferred:

- playlists
- videos
- editorial collections
- cross-storefront comparison
- multiple storefronts in one response

## DiscoveryTarget Contract Upgrade

### Problem

Current discovery-to-metadata behavior assumes this shape:

- `target_kind`
- `provider`
- `provider_id`
- `conversion_ready`

This works well for ListenBrainz because chart entries already map to MusicBrainz ids.

Apple Music will not fit that assumption cleanly. Apple chart entries typically have Apple ids and rich metadata hints, but not guaranteed MusicBrainz ids.

### New Contract

`DiscoveryTarget` should grow a resolution contract with two modes:

1. `direct_id`
2. `search_lookup`

Proposed additions:

- `resolution_mode`
  - `direct_id` or `search_lookup`
- `resolution_hints`
  - normalized hint payload used for metadata lookup when no direct id exists

Existing fields remain:

- `target_kind`
- `provider`
- `provider_id`
- `display_title`
- `display_subtitle`
- `source_context`
- `conversion_ready`
- `conversion_note`
- `discovery_badges`

### Resolution Semantics

#### direct_id

Used when the discovery entry can already open metadata detail directly.

Examples:

- ListenBrainz artist entry with MusicBrainz artist MBID
- ListenBrainz track entry with MusicBrainz recording MBID

Rules:

- `provider_id` is required
- `conversion_ready = true`
- current drawer flow keeps working

#### search_lookup

Used when the discovery entry does not have a metadata-native id yet, but has enough structured hints to resolve into metadata.

Examples:

- Apple Music song chart entry
- Apple Music album chart entry

Rules:

- `provider_id` may be Apple-native and not directly usable by metadata detail API
- `resolution_hints` becomes the stable bridge
- `conversion_ready = true` still means “this entry can be converted by supported lookup flow,” not “this entry already has a direct metadata id”

This is the critical compatibility move for future providers.

## Apple-to-Metadata Mapping

### Song Entry Mapping

Apple `song` chart entries should map into:

- `target_kind = track`
- `resolution_mode = search_lookup`

Preferred `resolution_hints`:

- `isrc`
- `title`
- `artist_name`
- `album_title`
- `apple_music_id`
- `storefront`

### Album Entry Mapping

Apple `album` chart entries should map into:

- `target_kind = album`
- `resolution_mode = search_lookup`

Preferred `resolution_hints`:

- `upc`
- `album_title`
- `artist_name`
- `apple_music_id`
- `storefront`

### Future-Proofing Rule

The resolver contract must not assume Apple-specific fields are universally present.

That means `resolution_hints` should be normalized into generic names such as:

- `title`
- `artist_name`
- `album_title`
- `isrc`
- `upc`
- `provider_origin_id`
- `provider_origin_name`
- `storefront`

Future providers can populate the same contract with different underlying data.

## Backend Responsibilities

### AppleMusicChartProviderAdapter

Add a new adapter alongside the existing chart adapters in:

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/chart_provider.py`

Responsibilities:

- call Apple Music charts API with configured developer token
- normalize songs and albums into `ChartInfo`, `ChartEntryInfo`, and `ChartDetailData`
- keep Apple payload knowledge inside the adapter
- expose provider metadata through `list_providers()`

Non-responsibilities:

- no metadata lookup
- no provider-specific UI shaping
- no subscription logic

### DiscoveryAssembler

Keep `DiscoveryAssembler` as the single place that turns provider-normalized entries into product-facing discovery views.

New responsibilities for this phase:

- build `DiscoveryTarget.resolution_mode`
- build `DiscoveryTarget.resolution_hints`
- distinguish between `direct_id` and `search_lookup`
- expose conversion notes that remain provider-agnostic from the UI point of view

### ChartService

Keep route behavior unchanged.

Responsibilities:

- include Apple provider in list output when configured and enabled
- return Apple charts inside the existing chart list/detail flow
- continue delegating all product shaping to `DiscoveryAssembler`

### Config

Add minimum configuration in:

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/config.py`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/.env.example`

Proposed settings:

- `chart_apple_music_base_url`
- `chart_apple_music_storefront`
- `chart_apple_music_developer_token`
- `chart_apple_music_count`
- `chart_apple_music_timeout_seconds` if a provider-specific timeout is needed; otherwise reuse shared timeout

Provider enablement rule:

- if `developer token` or `storefront` is missing, Apple provider is disabled
- disabled state should be explicit in `list_providers()`

### Cache

Apple charts should reuse the current runtime TTL cache:

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/core/runtime_cache.py`

Do not create a parallel cache system.

The cache key should include:

- provider
- storefront
- chart type
- count

## Frontend Responsibilities

### ChartsView

The page should treat Apple charts as first-class discovery content without any provider-specific page branch.

UI expectations for this phase:

- Apple charts appear in the same list/grid as other charts
- chart cards show Apple-specific source label naturally through the existing chart model
- chart detail shows songs/albums entries using the same discovery view model
- entries that use `search_lookup` resolution should visually remain “metadata ready,” but the note should make the conversion mode explicit

### Drawer Flow

This phase does not yet require finishing the `search_lookup` drawer resolution path.

The front-end must, however, be able to distinguish:

- `direct_id`
- `search_lookup`

That distinction should be represented in the shared discovery-to-metadata bridge, not in ad-hoc template logic.

This keeps the page ready for the next step without another structural rewrite.

## API Compatibility

Routes remain unchanged:

- `GET /charts/providers`
- `GET /charts`
- `GET /charts/{chart_id}`
- `GET /charts/{chart_id}/items/{item_id}`

Response payloads get richer through `DiscoveryTarget` contract expansion, but existing fields remain available.

Backward compatibility rule:

- existing ListenBrainz flow must continue to behave as `direct_id`
- existing discovery drawer behavior must remain intact for currently supported entries

## Error Handling

### Missing Apple Config

Behavior:

- provider listed as disabled, or omitted according to current provider-list conventions
- no runtime crash
- existing providers continue to work

### Apple API Failure

Behavior:

- fail only the Apple provider path
- preserve current discovery API behavior for other providers
- return clear provider-specific note in error or degraded response path

### Partial Entry Data

If Apple chart items miss stronger hints such as `isrc` or `upc`:

- still emit `search_lookup` target when title/artist context is sufficient
- mark `conversion_note` accordingly
- do not pretend the target is `direct_id`

## Testing Strategy

This phase should add tests for:

1. Apple provider list integration
2. Apple chart list mapping for songs and albums
3. Apple chart detail mapping for songs and albums
4. `DiscoveryTarget` resolution-mode behavior
5. config-missing provider disabled behavior
6. cache reuse for repeated Apple chart payload requests
7. existing ListenBrainz `direct_id` flow remains unchanged

Frontend should add minimal tests for:

- Apple charts rendering inside the existing charts view
- `DiscoveryTarget` resolution mode being preserved in front-end bridge types/state

## Rollout Notes

This phase intentionally stops one step before “Apple chart entry opens metadata drawer through lookup.”

That next step should be a separate, smaller phase:

- implement `search_lookup` resolution in the discovery-to-metadata bridge
- keep `direct_id` behavior unchanged

By splitting the work this way, Apple provider expansion remains contained, and the bridge design becomes reusable for Spotify, QQ 音乐, 网易云音乐, or other providers later.

## Recommendation

Implement Apple Music discovery in two small phases:

1. This phase:
   - Apple provider
   - `DiscoveryTarget` resolution contract upgrade
   - unified discovery rendering
2. Next phase:
   - actual `search_lookup` metadata drawer resolution

This gives MusicPilot immediate discovery breadth while preserving a stable architecture for future provider expansion.
