# RSS Metadata Lookup Quality Design

## Goal
Improve discovery RSS entries' `search_lookup` hit quality without changing discovery contracts, providers, or frontend interaction flow.

## Scope
Focus only on backend metadata lookup quality for RSS-driven `search_lookup` targets.

### In scope
- Normalize RSS lookup hints for track / album / artist entities.
- Build a small fallback keyword sequence for metadata lookup instead of a single keyword.
- Keep winner selection strict-first, but more tolerant of normalized artist/title variants.
- Preserve existing `DiscoveryTarget` contract and `/metadata/lookup` API shape.

### Out of scope
- No new discovery providers or RSS families.
- No frontend contract changes.
- No new metadata providers.
- No changes to dispatch, organize, or subscription semantics.

## Design
1. `MetadataService.lookup_detail()` should derive multiple candidate keywords from normalized hints and try them in order until one search returns a valid winner.
2. Normalization should remove low-signal suffix noise from titles, normalize artist credits, and collapse whitespace/punctuation differences.
3. Winner selection remains deterministic and prefers exact normalized matches, with album hints still acting as a strict narrowing condition when present.
4. The existing `/metadata/lookup` behavior remains unchanged for callers: same input shape, same detail response, same 400/404/502 semantics.

## Fallback strategy
- Track lookup attempts:
  1. `artist + title + album`
  2. `artist + title`
  3. `title + artist`
- Album lookup attempts:
  1. `artist + album`
  2. `album + artist`
  3. `album`
- Artist lookup attempts:
  1. `artist`

Each attempt reuses the same winner-selection rules against returned summaries.

## Success criteria
- RSS track lookup still prefers exact album matches when album is present.
- Title variants like live/version noise do not prevent correct lookup when the base title matches.
- Artist credit normalization continues to support `&`, `feat.`, `ft.`, `with`, and similar variants.
- Existing direct-id discovery flow remains untouched.
