# RSS Family Hints Quality Design

## Goal
Improve RSS-driven `search_lookup` hit quality by enriching `resolution_hints` with family-specific candidate fields, while preserving the existing discovery UI, provider list, and `/metadata/lookup` contract.

## Scope
Focus only on the RSS discovery families already supported:

- `netease_playlist_tracks`
- `netease_artist_songs`
- `netease_artist_albums`
- `youtube_top_songs`
- `youtube_top_artists`

### In scope
- Enrich RSS parser output with additional structured lookup candidates for the supported families.
- Pass those candidate hints through the existing discovery bridge.
- Let metadata lookup consume optional candidate arrays without changing request shape.
- Add focused tests for parser, discovery, and metadata lookup.
- Run a real runtime check against configured RSS feeds after implementation.

### Out of scope
- No new RSS families or providers.
- No frontend contract changes.
- No new settings fields.
- No dispatch / organize / subscription semantic changes.

## Approaches

### 1. Parser-only enrichment
Add richer RSS parser fields and stop there.

Pros:
- Smallest backend surface.

Cons:
- Limited value unless metadata lookup actually consumes the richer hints.

### 2. Recommended: parser + discovery + metadata lookup candidate flow
Add family-specific candidate hints in parser output, pass them through discovery, and let metadata lookup consume candidate arrays in deterministic order.

Pros:
- Stronger real-world benefit.
- Keeps API and UI stable.
- Future RSS family expansion only needs new parser mappings.

Cons:
- Slightly wider change surface than parser-only.

### 3. Family-specific lookup resolvers
Create separate lookup logic for each RSS family.

Pros:
- Maximum control per source.

Cons:
- Too heavy for this stage.
- Harder to maintain and extend.

## Design

### 1. Candidate hint model
RSS entries should continue exposing their current scalar hints, but may additionally include optional candidate arrays such as:

- `title_candidates`
- `artist_name_candidates`
- `album_title_candidates`

These arrays are internal hint expansions, not new API modes.

### 2. Family-specific enrichment rules

#### `netease_playlist_tracks`
- Keep current structured `title`, `artist_name`, `album_title`.
- Add candidate arrays from structured fields plus safe alternates found in raw title/description.

#### `netease_artist_songs`
- Same as track playlist feeds.
- Prefer structured fields from description over synthetic title splitting.

#### `netease_artist_albums`
- Keep current scalar behavior: no fake `album_title` if structured album title is missing.
- When structured album title exists, add candidate arrays that include display title if it differs.
- Do not promote a display-only title into required readiness.

#### `youtube_top_songs`
- Continue treating as track discovery.
- Build stronger artist/title candidate arrays from `title`, `author`, and normalized raw context.
- Preserve the current readiness requirement of `title + artist_name`.

#### `youtube_top_artists`
- Continue treating as artist discovery.
- Add artist candidate variants from visible title and normalized raw context.

### 3. Metadata lookup behavior
`MetadataService.lookup_detail()` should remain request-compatible, but when candidate arrays are present, it should derive ordered lookup attempts from them before falling back to scalar-only attempts.

This should stay deterministic:
- keep current strict winner selection
- preserve album-hint strictness
- preserve 400 / 404 / 502 semantics

### 4. Discovery/UI behavior
No frontend contract changes:
- chart entries still open metadata drawer
- RSS entries still use `resolution_mode = search_lookup`
- readiness text remains driven by required scalar hints

### 5. Runtime validation
After implementation, verify against the configured RSS feeds that:
- charts still load
- RSS entries still open metadata drawer
- the generated hints now include family-specific candidates
- at least one real RSS entry shows a better lookup path than before

## Success criteria
- Existing RSS discovery flows remain intact.
- Family-specific candidate hints are present where expected.
- Metadata lookup can consume candidate arrays without changing request shape.
- No regression in direct-id discovery flows.
- Backend tests and packaging continue to pass.
