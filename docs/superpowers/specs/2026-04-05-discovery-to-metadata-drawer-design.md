# Discovery To Metadata Drawer Design

Date: 2026-04-05

## Context

MusicPilot discovery has completed phase-1 productization:

- chart list and detail now expose product-facing discovery fields
- every chart entry now maps to a stable `DiscoveryTarget`
- the frontend chart page already renders hero entries, grouped entries, and metadata-readiness state

At the same time, the search page already has a mature metadata detail interaction:

- metadata search results can open `MetadataDetailDrawer`
- the drawer already supports:
  - viewing metadata detail
  - creating subscriptions
  - creating and running search jobs

This means the product does not need a second detail interaction for discovery. The missing step is to connect discovery entries to the existing metadata detail experience through the stable `DiscoveryTarget` bridge.

This phase is explicitly about:

- `discovery entry -> metadata detail`

It is not yet about:

- `discovery -> search conversion`
- `discovery -> metadata route page`
- new metadata provider behavior

## Product Goal

Users should be able to treat discovery as a first-class entry into metadata.

Examples:

- clicking an artist chart entry should open artist detail and show albums / singles / other releases
- clicking a track chart entry should open track detail
- clicking an album chart entry should open album detail and real track listing

The interaction should feel consistent with the rest of the product:

- browse in discovery
- drill down into metadata detail
- act from detail

## UX Constraints

This phase must follow the current UI/UX direction documented in:

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/product/MusicPilot_UI&UX产品方案.html`

Relevant constraints from that document:

1. Reuse host-like visual language
   - shallow background
   - large radius
   - light shadow
   - purple active state

2. Preserve familiar interaction patterns
   - right-side drawer / detail drawer
   - card actions
   - low navigation cost

3. Keep action hierarchy clear
   - browsing first
   - then detail understanding
   - then actions such as subscribe or search

4. Make state and reason visible
   - users should understand whether the discovery entry is metadata-ready
   - users should understand what detail they are viewing

Because of these constraints, this phase will reuse the existing drawer rather than introduce a separate detail page or a second parallel detail surface.

## Scope

### In Scope

- clicking discovery hero entry opens metadata detail drawer
- clicking grouped chart entries opens metadata detail drawer
- artist / album / track entries are all supported
- metadata detail loading is driven only by `DiscoveryTarget`
- current drawer actions remain available in discovery context
- the chart page clearly shows which entry is active / opened

### Out of Scope

- dedicated metadata detail route/page from charts
- automatic `discovery -> search` conversion
- search query generation changes
- subscription behavior changes
- chart provider expansion
- chart snapshot persistence or diffing
- full artist discography redesign

## Recommended Approach

### Option Chosen

Reuse the existing `MetadataDetailDrawer` from the search experience.

This is preferred over:

- building a new standalone metadata detail page
- embedding a second full detail panel into the discovery page

### Why

1. It keeps the product interaction consistent.
2. It minimizes new UI complexity.
3. It reuses a detail surface that already supports downstream actions.
4. It lets discovery and search converge on the same metadata experience.

## Interaction Design

### Entry Click Targets

The following elements should open metadata detail:

- chart hero entry card
- grouped discovery entry cards
- title/text region inside those cards

The subscribe button inside an entry card should keep its current behavior and must not be replaced by detail opening.

### Drawer Behavior

When a discovery entry is opened:

1. the metadata drawer opens immediately
2. the drawer enters loading state
3. the app requests metadata detail using the `DiscoveryTarget`
4. on success, the drawer shows the normal metadata detail content
5. on failure, the drawer shows the normal error state

This should feel the same as the search page detail behavior.

### Active State on Discovery Page

The charts page should expose a lightweight “currently opened entry” state:

- the selected entry card receives a visual active state
- closing the drawer clears that active entry state
- changing chart detail clears any stale active entry state from the previous chart

This is to preserve orientation when users drill into detail and then return to scanning the chart.

## Conversion Layer Rules

The discovery page must not fetch metadata detail directly from raw chart fields.

It must use only the `DiscoveryTarget` bridge.

### Mapping Rules

- `target_kind=artist`
  - fetch `/metadata/artists/{provider_id}`
- `target_kind=album`
  - fetch `/metadata/albums/{provider_id}`
- `target_kind=track`
  - fetch `/metadata/tracks/{provider_id}`

### Guard Rules

If `conversion_ready=false`:

- clicking the entry should not fire a metadata request
- instead, the page should show a clear local warning or inline message using `conversion_note`
- the subscribe button can remain available if current behavior allows it

This keeps the interaction honest and prevents hidden failing requests.

### Extensibility Rule

Future chart providers must continue to map into:

- `artist`
- `album`
- `track`

and then into `DiscoveryTarget`.

The chart page must remain ignorant of provider-specific payload shapes.

This is the main mechanism that keeps future chart expansion low-cost.

## Frontend Design

### Existing Components To Reuse

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/components/MetadataDetailDrawer.vue`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/services/metadata.ts`

### Primary Page To Modify

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/frontend/src/views/ChartsView.vue`

### Suggested Responsibility Split

#### ChartsView

Responsible for:

- storing drawer open state
- storing current metadata detail loading/error/data
- storing currently active discovery entry id
- deciding whether an entry click is allowed
- calling metadata detail fetch via a small mapper/helper

#### MetadataDetailDrawer

Responsible for:

- showing detail data
- showing error state
- exposing current actions

This phase should not fork the drawer into a chart-specific variant unless an absolutely necessary text tweak cannot be made through props.

#### Discovery To Metadata Mapper

Add a very small helper near the charts view or frontend service layer.

Responsibility:

- convert a `DiscoveryTarget` into a metadata detail fetch request

This helper should be pure and tiny.

Example logic:

- validate `conversion_ready`
- read `target_kind`
- call `fetchMetadataDetail(target_kind, provider_id)`

No chart-provider branching belongs here.

## UI Details

### Entry Card Behavior

The discovery card must preserve two distinct actions:

- click card body: open metadata detail
- click subscribe button: create subscription

To avoid ambiguity:

- card body or title area should look clickable
- subscribe button should remain visually separate

### Hero Entry Behavior

Hero entry should also be clickable and open metadata detail.

Because it is the most prominent discovery surface, it should behave as the clearest “open detail” affordance on the page.

### Drawer Title and Context

The existing drawer title may remain, but this phase should ensure the content gives enough context that the user knows they came from discovery.

Recommended minimum:

- keep current metadata detail structure
- add a lightweight context hint in the chart page, not inside the drawer, to avoid making the drawer discovery-specific

That keeps the drawer reusable across search and discovery.

## Error Handling

### Metadata Not Ready

If an entry is not metadata-ready:

- do not call the metadata API
- surface the `conversion_note`
- keep the user on the discovery page

### Metadata Fetch Failure

If the API request fails:

- open drawer with standard error state
- do not clear the active entry until the drawer is closed

This keeps the UI state understandable.

## Testing Strategy

### Frontend

Add coverage for:

- clicking a metadata-ready discovery entry opens the drawer
- correct metadata endpoint is chosen for artist / album / track
- clicking a not-ready entry does not trigger fetch
- subscribe button still triggers subscription flow, not detail opening
- changing selected chart clears stale active entry state

### Backend

No backend behavior change is required in this phase beyond consuming already existing `DiscoveryTarget`.

Backend verification should remain limited to ensuring the discovery payload shape still matches the chart page contract.

### Manual Runtime Verification

After implementation:

- use the real chart page
- open one artist entry
- open one track entry
- if available, open one album entry
- capture real screenshots after the interaction works

These screenshots are part of the expected completion evidence for this phase.

## Success Criteria

This phase is successful when:

- discovery entries can open metadata detail through the existing drawer
- artist / album / track entries all follow the same bridge rule
- the chart page does not depend on provider-specific raw payloads
- the subscribe action still works unchanged
- the UI feels like one continuous product flow instead of two separate modules

## Deferred Follow-Up

This phase intentionally sets up, but does not implement:

- discovery-to-search conversion
- richer artist discography exploration
- dedicated metadata detail pages
- discovery detail screenshots tied to batch subscription flows

Those should build on this drawer-based bridge rather than replace it immediately.
