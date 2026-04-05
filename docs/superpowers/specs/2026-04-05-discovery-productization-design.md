# Discovery Productization Design

Date: 2026-04-05

## Context

MusicPilot already has a working discovery baseline:

- `ListenBrainz` is the current real discovery provider.
- chart providers, chart list, chart detail, and chart-entry subscription creation already work.
- chart cache is already verified in real MoviePilot plugin runtime.

However, discovery is still shaped like an integration surface rather than a finished product surface:

- chart pages mostly render raw provider-normalized data
- chart detail is a flat entry list with limited narrative value
- discovery entries do not yet expose a stable bridge to `metadata`
- future chart expansion would currently push more adapter-specific logic into service and UI layers

The next step is to productize discovery first, while defining a stable `discovery -> metadata` conversion layer up front. Search conversion itself is intentionally deferred to a later phase.

## Goals

1. Make discovery feel like a product entry point rather than a thin chart API viewer.
2. Define a stable conversion boundary from discovery entries into metadata targets.
3. Keep chart-provider expansion cheap by making the conversion layer provider-agnostic.
4. Preserve current subscription creation behavior.
5. Avoid coupling this phase to search conversion, chart snapshot persistence, or refresh automation.

## Non-Goals

This phase does not:

- add new discovery providers
- add chart snapshot persistence or diff tracking
- add scheduled chart refresh
- implement discovery-to-metadata navigation behavior
- implement discovery-to-search conversion behavior
- change subscription execution semantics
- change metadata provider behavior

## Product Direction

Discovery should first serve browsing and curation.

That means the first optimization target is:

- better chart presentation
- better chart-entry storytelling
- better visibility into whether an entry is ready to become a metadata target later

This phase intentionally stops short of automatic search conversion. The purpose is to ensure the discovery surface becomes stable and extensible before downstream automation depends on it.

## Design Overview

### Existing Layers

Today the chain is roughly:

`ChartProviderAdapter -> ChartService -> /charts API -> ChartsView`

The provider adapter already performs source normalization, but the service and UI still consume mostly provider-shaped chart objects.

### New Layers

The new chain becomes:

`ChartProviderAdapter -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView`

`ChartProviderAdapter` remains responsible for provider-specific fetching and provider-level normalization.

`DiscoveryAssembler` becomes responsible for product-facing discovery shaping:

- build `DiscoveryTarget`
- build chart summary text
- choose hero entry
- group entries for display
- surface discovery-specific badges and readiness state

`ChartService` becomes a thin orchestration layer that delegates discovery presentation shaping to the assembler.

## Data Model

### 1. DiscoveryTarget

Add a new backend/frontend model that acts as the stable bridge between discovery and metadata.

Fields:

- `target_kind`
  - one of `artist`, `album`, `track`
- `provider`
  - current value will be `musicbrainz`
- `provider_id`
  - MBID or stable provider identifier used by the metadata layer
- `display_title`
- `display_subtitle`
- `source_context`
  - includes chart provider, chart id, chart name, rank, chart type
- `conversion_ready`
  - whether the entry can already be converted into a metadata request without further provider-specific guessing
- `conversion_note`
  - explicit explanation for ready/not-ready state
- `discovery_badges`
  - product-facing descriptors such as `sitewide`, `weekly`, `top-artist`, `top-track`

Constraints:

- `DiscoveryTarget` is provider-agnostic from the discovery layer’s point of view.
- all current and future chart providers must eventually map entries into one of the supported `target_kind` values
- the rest of the product must not depend on provider-specific chart payload fields once `DiscoveryTarget` is built

### 2. Discovery Entry View Model

Keep the current `ChartEntryInfo` contract for compatibility, but enrich chart detail with a discovery-facing entry shape that wraps the current entry and the new target bridge.

Proposed structure:

- `entry`
  - the current normalized `ChartEntryInfo`
- `target`
  - the new `DiscoveryTarget`
- `entry_summary`
  - short product-facing line for list rendering
- `badges`
  - rendered labels derived from chart context
- `highlight_reason`
  - concise explanation of why this entry is featured in the chart

This allows current consumers to remain compatible while the discovery page moves to the richer model.

### 3. Discovery Detail View Model

Extend `ChartDetailData` with product-facing sections:

- `hero_entry`
  - one selected representative item for the chart
- `summary_stats`
  - compact counts and tags for quick scanning
- `entry_groups`
  - grouped display model
- `conversion_summary`
  - summary of how many entries are already metadata-ready

`items[]` remains in place for compatibility during the transition.

### 4. Chart Summary Fields

Extend `ChartInfo` with discovery-facing summary fields:

- `summary`
  - short user-facing chart description
- `chart_group`
  - product grouping bucket such as `artists`, `albums`, `tracks`
- `chart_scope`
  - provider-level scope such as `sitewide`, `editorial`, `regional`
- `freshness_label`
  - user-facing recency description derived from current provider range and refresh hint
- `supports_subscription`
  - explicit flag for whether this chart can create subscriptions from entries

These fields let the frontend stop deriving product meaning from raw provider fields.

## Backend Responsibilities

### ChartProviderAdapter

Keep current responsibilities:

- fetch provider payload
- normalize provider output into current chart primitives
- stay provider-specific

Add only minimal source annotations needed by the assembler. Do not let adapters grow discovery-product logic.

### DiscoveryAssembler

Add a new service, for example:

- `backend/app/services/discovery.py`

Responsibilities:

- convert `ChartInfo` into product-ready chart summaries
- convert `ChartEntryInfo` into `DiscoveryTarget`
- compute `conversion_ready` and `conversion_note`
- build chart-level hero entry
- group entries by stable product groups
- produce detail-level summary stats

Rules:

- no external I/O
- no chart provider fetching
- no metadata provider calls
- deterministic transformation from already-normalized chart data

### ChartService

Responsibilities after this phase:

- ask adapter for raw chart data
- ask assembler for discovery view models
- return enriched chart data to API routes

### API Routes

Current routes remain unchanged:

- `GET /charts/providers`
- `GET /charts`
- `GET /charts/{chart_id}`
- `POST /charts/{chart_id}/subscribe`

This phase must preserve route paths and main usage semantics.

Only the response payload becomes richer.

## Frontend Responsibilities

### ChartsView

The page should evolve from a raw chart browser into a discovery landing surface.

New behavior:

- chart cards show summary and product grouping
- chart detail shows one hero entry
- chart entries render badges and conversion readiness
- grouped sections make artist/album/track semantics explicit
- the UI clearly distinguishes:
  - discovery context
  - metadata conversion readiness
  - subscription action

The current subscribe action remains.

### UI Scope for This Phase

Do:

- improve chart cards
- improve chart detail presentation
- show readiness and badges
- show compact summary stats

Do not:

- add full metadata detail drawer handoff from chart entry
- add search conversion buttons
- add change history / chart diffs

## Extensibility Rules

To avoid repeated rewrites when charts expand:

1. Every chart provider must normalize entries to one of:
   - `artist`
   - `album`
   - `track`

2. Every discovery entry must expose a `DiscoveryTarget`.

3. Future provider-specific quirks must be absorbed either:
   - inside the provider adapter, or
   - inside provider-to-`DiscoveryTarget` mapping rules

4. UI and service layers must not branch on raw provider payload shapes.

5. Search conversion, when implemented later, must consume `DiscoveryTarget`, not provider-specific chart entry fields.

These rules are the main mechanism for keeping future chart expansion low-cost.

## Error Handling

This phase does not introduce new network boundaries.

Expected handling:

- provider fetch failures continue to surface through current chart API errors
- assembler transformation must be pure and non-throwing for valid normalized data
- if an entry cannot produce a metadata-ready target:
  - keep the entry visible
  - set `conversion_ready = false`
  - explain why in `conversion_note`

The product should favor “visible but not ready” over hiding discovery entries.

## Compatibility

Backward compatibility requirements:

- existing chart routes remain unchanged
- subscription creation from chart entry remains unchanged
- current `items[]` field remains available during this phase
- mock and real providers continue to work through the same routes

Intentional forward-looking additions:

- new summary fields on `ChartInfo`
- new discovery-facing detail structure on `ChartDetailData`
- new `DiscoveryTarget` bridge

## Testing Strategy

### Backend

Add tests for:

- `DiscoveryTarget` mapping for artist entries
- `DiscoveryTarget` mapping for track entries
- `conversion_ready` and `conversion_note` rules
- chart summary enrichment
- hero entry selection
- grouped detail output
- compatibility of existing `items[]` access

### Frontend

Add tests or component assertions for:

- chart cards render enriched summary fields
- chart detail renders hero entry and groups
- conversion readiness badges render correctly
- existing subscribe interaction still works

### Runtime Validation

After implementation, validate in both:

- local backend runtime
- real MoviePilot plugin runtime

Focus on:

- current mock chart provider
- current ListenBrainz real provider

## Rollout Plan

This design is only for discovery productization phase 1.

Implementation order should be:

1. add backend discovery models
2. add `DiscoveryAssembler`
3. enrich chart API responses without breaking existing fields
4. update frontend chart page to consume new fields
5. verify mock and real provider behavior
6. document the stable `discovery -> metadata` bridge for later phases

## Success Criteria

This phase is successful when:

- discovery pages feel product-oriented rather than adapter-oriented
- chart entries expose a stable metadata conversion bridge
- future album/artist/track chart expansion can reuse the same bridge without schema redesign
- current subscription creation still works unchanged
- no search conversion logic is required to justify the new structure
