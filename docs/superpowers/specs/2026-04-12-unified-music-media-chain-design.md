# Unified Music Media Chain Design

## Goal
Replace MusicPilot's current discovery-to-metadata transitional lookup model with a single, explicit music media parsing architecture modeled on MoviePilot's design method:

`MusicMediaInput -> MusicMetaBase -> MusicMediaInfo`

The goal is not to incrementally improve `DiscoveryTarget + resolution_hints`, but to remove that transitional model and make a unified music media chain the only upper-layer recognition path for discovery, detail, search, subscription, acquisition, and organize upstream identification.

## Scope
This is a full upper-layer architecture refactor. It accepts breaking changes and does not preserve compatibility with the current discovery contract.

### In scope
- Replace the current discovery recognition contract centered on:
  - `DiscoveryTarget`
  - `resolution_mode`
  - `resolution_hints`
- Introduce the three core domain layers:
  - `MusicMediaInput`
  - `MusicMetaBase`
  - `MusicMediaInfo`
- Define a unified service chain:
  - `MusicMediaInputAdapter`
  - `MusicMetaBaseBuilder`
  - `MusicMediaRecognizer`
  - `MusicMediaInfoHydrator`
  - `MusicMediaChain`
- Make discovery detail, metadata lookup, search-side upstream identification, subscription-side target recognition, and organize upstream recognition converge on the same chain.
- Replace `/metadata/lookup` with unified media resolve API endpoints.
- Redefine frontend discovery detail opening to consume unified chain outputs instead of `direct_id | search_lookup`.

### Out of scope
- No changes to MoviePilot host bottom-layer API semantics.
- No redesign of downloader runtime, path handoff, organize preview/apply bottom-layer execution, or plugin entry forms.
- No new metadata provider or chart provider source in this refactor itself.
- No visual settings CRUD redesign in this refactor itself.

## Current problems
The current architecture is functional but transitional:

1. Discovery recognition is still driven by `DiscoveryTarget + resolution_hints`.
2. RSS family parsing, discovery assembly, metadata lookup, and frontend detail-opening each carry part of the recognition logic.
3. `discovery -> detail` behaves like a localized lookup bridge instead of consuming a single project-wide media parsing chain.
4. Search, subscription, acquisition, and organize upstream identification still do not reliably reuse the same normalized music entity model.
5. Continuing to improve hit quality on the existing contract would deepen a transitional design instead of removing it.

## Design

### 1. Core domain model

#### `MusicMediaInput`
Raw music clues collected from one upstream scenario.

Required design intent:
- Represent source input, not recognition output.
- Support discovery, detail, search, subscription, acquisition, organize, library, and manual inputs.

Representative fields:
- `entity_hint`
- `source_kind`
- `title`
- `subtitle`
- `artist_names`
- `album_title`
- `album_artist_names`
- `release_date`
- `year`
- `track_number`
- `disc_number`
- `external_refs`
- `source_context`
- `raw_context`

#### `MusicMetaBase`
Normalized intermediate music metadata, equivalent in design role to MoviePilot's `MetaBase`.

Required design intent:
- The only canonical pre-recognition music metadata object.
- Hold normalization, aliases, evidence, and source refs.

Representative fields:
- `entity_type`
- `canonical_title`
- `canonical_artist_names`
- `canonical_album_title`
- `canonical_album_artist_names`
- `canonical_release_date`
- `canonical_year`
- `track_number`
- `disc_number`
- `alias_titles`
- `alias_artist_names`
- `alias_album_titles`
- `featuring_artist_names`
- `external_refs`
- `source_refs`
- `evidence`
- `normalization_notes`
- `confidence_hint`

#### `MusicMediaInfo`
Recognized formal music media object, equivalent in design role to MoviePilot's `MediaInfo`.

Required design intent:
- The canonical post-recognition music object for downstream business reuse.
- More stable than `MetadataDetail`, which should become a hydrated detail view.

Representative fields:
- `entity_type`
- `provider`
- `provider_id`
- `title`
- `artist_names`
- `album_title`
- `album_artist_names`
- `release_date`
- `year`
- `track_number`
- `disc_number`
- `related_artist_ids`
- `related_album_id`
- `related_track_ids`
- `external_refs`
- `match_confidence`
- `match_strategy`
- `match_evidence`
- `diagnostics`
- `cover_url`
- `disambiguation`
- `release_context`

### 2. Unified service chain

#### `MusicMediaInputAdapter`
Maps scenario-specific inputs into `MusicMediaInput`.

#### `MusicMetaBaseBuilder`
Builds `MusicMetaBase` from `MusicMediaInput`.

#### `MusicMediaRecognizer`
Builds `MusicMediaInfo` from `MusicMetaBase`.
Internal recognition can support:
- strong-reference direct resolution
- weak-clue recognition

But callers do not receive separate external modes.

#### `MusicMediaInfoHydrator`
Hydrates `MusicMediaInfo` into `MetadataDetail` when detail output is needed.

#### `MusicMediaChain`
Owns orchestration of the full chain and becomes the only upper-layer recognition entry.

Recommended public service surface:
- `resolve(input: MusicMediaInput) -> MusicMediaInfo`
- `resolve_detail(input: MusicMediaInput) -> MetadataDetail`

### 3. Scenario integration

#### Discovery
- Discovery entries must no longer be treated as long-lived recognition objects.
- Chart entries are adapted into `MusicMediaInput`, then resolved through the chain.

#### Detail
- Detail is not a special-case bypass.
- It is a consumer of the same unified chain and its hydrated output.

#### Search
- Search-side upstream entity confirmation should reuse `MusicMetaBase` / `MusicMediaInfo`.

#### Subscription
- Subscription targets should evolve away from scenario-private payloads and toward formal music media snapshots.

#### Acquisition / dispatch
- Candidate selection and dispatch-side entity confirmation should consume the same formal media object semantics.

#### Organize
- Existing local music metadata recognition should converge into the same chain over time instead of staying as an isolated evolution path.

### 4. API direction

Current `entity_type + hints -> metadata detail` lookup is transitional and should not remain the long-term contract.

Target direction:
- replace `/metadata/lookup` with unified media resolve endpoints

Chosen HTTP entry shape:
- `POST /media/resolve`
- `POST /media/resolve/detail`

Internal semantics:
- `MusicMediaInput -> MusicMediaChain -> MusicMediaInfo`
- `MusicMediaInput -> MusicMediaChain -> MetadataDetail`

### 5. Persistence and cache boundaries

#### `MusicMediaInput`
- transient only by default

#### `MusicMetaBase`
- internal by default
- may be snapshot-persisted in run/search/organize summaries for diagnostics

#### `MusicMediaInfo`
- formal object suitable for downstream snapshots
- replaces loose target payloads in subscription/search/organize upstream state

Cache direction:
- provider cache remains provider-level
- if chain-level cache is added later, it should cache:
  - `MusicMetaBase fingerprint -> MusicMediaInfo`

### 6. Replacement matrix

The following current paths are expected to be replaced, not preserved:

Backend:
- `backend/app/schemas/orchestration.py`
  - `DiscoveryTarget`
  - the `conversion_ready / conversion_note / resolution_mode / resolution_hints` recognition semantics
- `backend/app/services/discovery.py`
  - `_build_target`
  - `_build_rss_lookup_target`
  - `_build_rss_resolution_hints`
  - `_resolve_rss_lookup_readiness`
- `backend/app/services/metadata.py`
  - `lookup_detail`
  - current hints-centered lookup construction

Frontend:
- `frontend/src/types/orchestration.ts`
  - `DiscoveryTarget`
  - `resolution_mode`
  - `resolution_hints`
- `frontend/src/services/discovery-metadata.ts`
  - current `direct_id | search_lookup` bridge

The following remain stable boundaries:
- host HTTP API semantics
- downloader runtime / handoff / organize bottom-layer execution boundaries
- metadata provider search/detail/cache
- chart provider fetch/cache/source adaptation
- plugin center / dashboard / sidebar / plugin-app entry forms

## Breaking change policy
This refactor explicitly does not preserve compatibility.

Accepted consequences:
- backend schema changes
- frontend type changes
- HTTP API shape changes
- removal of `DiscoveryTarget`-driven flows
- rewritten tests
- possible database rebuild or local state rebuild

No dual-track compatibility layer should be introduced.

## Success criteria
The refactor is considered successful when all of the following are true:

1. Discovery detail no longer depends on `DiscoveryTarget + resolution_hints`.
2. Frontend no longer understands `direct_id | search_lookup` as primary discovery-to-detail modes.
3. `/metadata/lookup` no longer implements an independent hints-driven bridge and is replaced by the unified media resolve endpoints.
4. Search, subscription, and organize upstream identification begin reusing `MusicMetaBase` or `MusicMediaInfo`.
5. Hit-quality optimization work moves from source-specific hints toward unified normalization, recognition, and formal media object quality.
6. Documentation and tests describe the unified music media chain as the primary architecture, not the current transitional lookup path.
