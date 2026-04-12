# Unified Music Media Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current discovery-to-metadata transitional bridge with a single upper-layer music media parsing architecture centered on `MusicMediaInput -> MusicMetaBase -> MusicMediaInfo`, with breaking changes accepted and no compatibility layer.

**Architecture:** Introduce a new backend music media chain (`InputAdapter -> MetaBaseBuilder -> Recognizer -> Hydrator`) and make discovery/detail/search/subscription/organize upstream identification consume that chain instead of `DiscoveryTarget + resolution_hints`. Replace `/metadata/lookup` with unified media resolve endpoints, switch frontend discovery detail opening to the new API, and delete old direct-id/search-lookup bridging semantics rather than preserving them.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Vue 3, TypeScript, Element Plus, Vite, unittest, pnpm, plugin runtime packaging.

---

## File map

### Backend

- Create: `backend/app/schemas/music_media.py`
  - Core backend domain models for `MusicMediaInput`, `MusicMetaBase`, `MusicMediaInfo`, resolve request/response payloads.
- Create: `backend/app/services/music_media_chain.py`
  - Unified orchestration entrypoint for input adaptation, base building, recognition, and detail hydration.
- Create: `backend/app/services/music_media_input_adapter.py`
  - Scenario-specific input builders (`from_discovery_entry`, `from_search_request`, `from_subscription_target`, `from_organize_context`).
- Create: `backend/app/services/music_meta_base_builder.py`
  - Normalize titles, artists, albums, refs, and evidence into `MusicMetaBase`.
- Create: `backend/app/services/music_media_recognizer.py`
  - Build `MusicMediaInfo` from `MusicMetaBase` via strong-ref direct resolution or weak-clue recognition.
- Create: `backend/app/services/music_media_info_hydrator.py`
  - Convert `MusicMediaInfo` into `MetadataDetail`.
- Create: `backend/app/api/routes/media.py`
  - New HTTP endpoints: `POST /media/resolve`, `POST /media/resolve/detail`.
- Modify: `backend/app/api/router.py`
  - Register new media routes and remove old lookup route wiring.
- Modify: `backend/app/api/routes/search.py`
  - Remove `/metadata/lookup`; keep metadata search/detail provider APIs only.
- Modify: `backend/app/core/dependencies.py`
  - Provide `MusicMediaChain` and any sub-services.
- Modify: `backend/app/schemas/orchestration.py`
  - Remove `DiscoveryTarget` semantics and replace discovery-facing payloads with chain-oriented output.
- Modify: `backend/app/services/discovery.py`
  - Stop building `DiscoveryTarget`; emit discovery views that carry source/display data plus `MusicMediaInput` summaries or resolve-ready payloads.
- Modify: `backend/app/services/metadata.py`
  - Remove `lookup_detail()` bridge responsibility and keep provider search/detail responsibilities only.
- Modify: `backend/app/api/routes/subscriptions.py`
  - Shift subscription target detail resolution to unified chain output where needed.
- Modify: `backend/app/services/subscription_execution.py`
  - Consume `MusicMediaInfo` snapshots instead of loose payloads where upstream identification is needed.
- Modify: `backend/app/services/organize.py`
  - Introduce chain-based upstream recognition hook for organize-side metadata entry.

### Frontend

- Create: `frontend/src/types/music-media.ts`
  - TS types for `MusicMediaInput`, `MusicMetaBase`, `MusicMediaInfo`, resolve request/response payloads.
- Create: `frontend/src/services/music-media.ts`
  - HTTP client for `/media/resolve` and `/media/resolve/detail`.
- Modify: `frontend/src/types/orchestration.ts`
  - Remove `DiscoveryTarget`, `resolution_mode`, `resolution_hints`.
- Modify: `frontend/src/services/discovery-metadata.ts`
  - Replace old direct-id/search-lookup branching with unified media resolve call.
- Modify: `frontend/src/views/ChartsView.vue`
  - Open metadata drawer via unified media resolve payloads.
- Modify: `frontend/src/components/MetadataDetailDrawer.vue`
  - Accept chain-backed detail loading and updated diagnostics wording.

### Runtime mirror

- Modify mirrored files under `plugin_runtime/plugins/musicpilot/...` corresponding to all backend/frontend runtime-exported code touched above.

### Tests

- Create: `backend/tests/test_music_media_chain.py`
- Create: `backend/tests/test_music_media_api.py`
- Modify: `backend/tests/test_discovery_service.py`
- Modify: `backend/tests/test_rss_feed_parser.py`
- Modify: `backend/tests/test_metadata_provider.py`
- Modify: `frontend/src/services/__tests__/discovery-metadata.spec.ts`
- Modify: `frontend/src/views/__tests__/ChartsView.spec.ts`

### Docs

- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
- Modify: `docs/14_架构收缩与语义归一说明.md`
- Modify: `docs/architecture/2026-04-12_统一音乐媒体解析链设计基线.md`
- Create: `docs/40_统一音乐媒体解析链_运行态验证.md`

---

### Task 1: Define the core backend music media models

**Files:**
- Create: `backend/app/schemas/music_media.py`
- Test: `backend/tests/test_music_media_chain.py`

- [ ] **Step 1: Write the failing schema tests**

```python
from app.schemas.music_media import (
    MusicMediaInput,
    MusicMetaBase,
    MusicMediaInfo,
    MusicResolveDetailRequest,
)
from app.schemas.mvp import EntityType


def test_music_media_input_accepts_discovery_track_clues():
    payload = MusicMediaInput(
        entity_hint=EntityType.TRACK,
        source_kind="discovery",
        title="Die With A Smile",
        artist_names=["Lady Gaga", "Bruno Mars"],
        album_title="Die With A Smile",
        external_refs={"source_url": "https://example.test/item"},
        source_context={"provider": "rss_feed", "family": "youtube_top_songs"},
        raw_context={"rank": 1},
    )
    assert payload.entity_hint == EntityType.TRACK
    assert payload.artist_names == ["Lady Gaga", "Bruno Mars"]


def test_music_meta_base_requires_entity_type_and_canonical_fields():
    base = MusicMetaBase(
        entity_type=EntityType.ALBUM,
        canonical_title="25",
        canonical_artist_names=["Adele"],
        canonical_album_title="25",
        canonical_album_artist_names=["Adele"],
        evidence=[{"field": "title", "value": "25", "source": "structured"}],
    )
    assert base.canonical_title == "25"
    assert base.canonical_artist_names == ["Adele"]


def test_music_media_info_tracks_match_diagnostics():
    info = MusicMediaInfo(
        entity_type=EntityType.TRACK,
        provider="musicbrainz",
        provider_id="recording-1",
        title="Hello",
        artist_names=["Adele"],
        match_confidence=0.98,
        match_strategy="strong_ref",
        match_evidence=[{"field": "recording_id", "value": "recording-1"}],
        diagnostics=[],
    )
    assert info.provider_id == "recording-1"
    assert info.match_strategy == "strong_ref"


def test_resolve_detail_request_wraps_music_media_input():
    request = MusicResolveDetailRequest(
        input={
            "entity_hint": "artist",
            "source_kind": "detail",
            "artist_names": ["Adele"],
        }
    )
    assert request.input.source_kind == "detail"
```

- [ ] **Step 2: Run the new backend schema test file and confirm import failure**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_music_media_chain.py'
```

Expected:
- FAIL with `ModuleNotFoundError` or missing symbol errors for `app.schemas.music_media`.

- [ ] **Step 3: Write the minimal new schema module**

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .metadata import MetadataDetail
from .mvp import EntityType


class MusicMediaInput(BaseModel):
    entity_hint: EntityType | None = None
    source_kind: str
    title: str | None = None
    subtitle: str | None = None
    artist_names: list[str] = Field(default_factory=list)
    album_title: str | None = None
    album_artist_names: list[str] = Field(default_factory=list)
    release_date: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    external_refs: dict[str, str] = Field(default_factory=dict)
    source_context: dict[str, Any] = Field(default_factory=dict)
    raw_context: dict[str, Any] = Field(default_factory=dict)


class MusicMetaBase(BaseModel):
    entity_type: EntityType
    canonical_title: str | None = None
    canonical_artist_names: list[str] = Field(default_factory=list)
    canonical_album_title: str | None = None
    canonical_album_artist_names: list[str] = Field(default_factory=list)
    canonical_release_date: str | None = None
    canonical_year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    alias_titles: list[str] = Field(default_factory=list)
    alias_artist_names: list[str] = Field(default_factory=list)
    alias_album_titles: list[str] = Field(default_factory=list)
    featuring_artist_names: list[str] = Field(default_factory=list)
    external_refs: dict[str, str] = Field(default_factory=dict)
    source_refs: dict[str, str] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    normalization_notes: list[str] = Field(default_factory=list)
    confidence_hint: float | None = None


class MusicMediaInfo(BaseModel):
    entity_type: EntityType
    provider: str
    provider_id: str
    title: str | None = None
    artist_names: list[str] = Field(default_factory=list)
    album_title: str | None = None
    album_artist_names: list[str] = Field(default_factory=list)
    release_date: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    related_artist_ids: list[str] = Field(default_factory=list)
    related_album_id: str | None = None
    related_track_ids: list[str] = Field(default_factory=list)
    external_refs: dict[str, str] = Field(default_factory=dict)
    match_confidence: float | None = None
    match_strategy: str | None = None
    match_evidence: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    cover_url: str | None = None
    disambiguation: str | None = None
    release_context: dict[str, Any] = Field(default_factory=dict)


class MusicResolveRequest(BaseModel):
    input: MusicMediaInput


class MusicResolveDetailRequest(BaseModel):
    input: MusicMediaInput


class MusicResolveDetailResponse(BaseModel):
    media: MusicMediaInfo
    detail: MetadataDetail
```

- [ ] **Step 4: Re-run the schema tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_music_media_chain.py'
```

Expected:
- PASS for the four schema tests above.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/music_media.py backend/tests/test_music_media_chain.py
git commit -m "feat: add music media chain schemas"
```

### Task 2: Implement the backend chain services

**Files:**
- Create: `backend/app/services/music_media_input_adapter.py`
- Create: `backend/app/services/music_meta_base_builder.py`
- Create: `backend/app/services/music_media_recognizer.py`
- Create: `backend/app/services/music_media_info_hydrator.py`
- Create: `backend/app/services/music_media_chain.py`
- Modify: `backend/app/services/metadata.py`
- Test: `backend/tests/test_music_media_chain.py`

- [ ] **Step 1: Extend the failing test file with chain behavior tests**

```python
from app.schemas.metadata import MetadataDetail
from app.schemas.music_media import MusicMediaInput
from app.schemas.mvp import EntityType
from app.services.music_media_chain import MusicMediaChain


class FakeMetadataService:
    def get_detail(self, entity_type, entity_id):
        return MetadataDetail(
            entity_type=entity_type,
            id=entity_id,
            title="Hello",
            artist_name="Adele",
            provider="musicbrainz",
            source_type="musicbrainz",
            mock=False,
            note="detail",
            integration_point="test",
        )


class FakeMetadataAdapter:
    provider = "musicbrainz"
    source_type = "musicbrainz"
    supports_live_queries = True

    def get_detail(self, entity_type, entity_id):
        return FakeMetadataService().get_detail(entity_type, entity_id)

    def search(self, payload):
        raise AssertionError("search should not run in strong-ref test")


def test_chain_resolves_strong_ref_track_without_search():
    chain = MusicMediaChain(metadata_service=FakeMetadataService(), metadata_adapter=FakeMetadataAdapter())
    resolved = chain.resolve(
        MusicMediaInput(
            entity_hint=EntityType.TRACK,
            source_kind="discovery",
            title="Hello",
            artist_names=["Adele"],
            external_refs={"musicbrainz_recording_id": "recording-hello"},
        )
    )
    assert resolved.provider_id == "recording-hello"
    assert resolved.match_strategy == "strong_ref"


def test_chain_resolve_detail_hydrates_metadata_detail():
    chain = MusicMediaChain(metadata_service=FakeMetadataService(), metadata_adapter=FakeMetadataAdapter())
    result = chain.resolve_detail(
        MusicMediaInput(
            entity_hint=EntityType.TRACK,
            source_kind="detail",
            title="Hello",
            artist_names=["Adele"],
            external_refs={"musicbrainz_recording_id": "recording-hello"},
        )
    )
    assert result.detail.id == "recording-hello"
    assert result.media.provider_id == "recording-hello"
```

- [ ] **Step 2: Run the targeted chain tests and confirm missing service failures**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_music_media_chain.py'
```

Expected:
- FAIL with import errors for chain services or missing methods like `resolve`.

- [ ] **Step 3: Implement the minimal chain modules**

```python
# backend/app/services/music_media_input_adapter.py
from app.schemas.music_media import MusicMediaInput


class MusicMediaInputAdapter:
    def from_input(self, payload: MusicMediaInput) -> MusicMediaInput:
        return payload
```

```python
# backend/app/services/music_meta_base_builder.py
from app.schemas.music_media import MusicMediaInput, MusicMetaBase
from app.schemas.mvp import EntityType


class MusicMetaBaseBuilder:
    def build(self, payload: MusicMediaInput) -> MusicMetaBase:
        entity_type = payload.entity_hint or EntityType.TRACK
        return MusicMetaBase(
            entity_type=entity_type,
            canonical_title=payload.title or payload.album_title or (payload.artist_names[0] if payload.artist_names else None),
            canonical_artist_names=payload.artist_names,
            canonical_album_title=payload.album_title,
            canonical_album_artist_names=payload.album_artist_names,
            canonical_year=payload.year,
            track_number=payload.track_number,
            disc_number=payload.disc_number,
            external_refs=payload.external_refs,
            evidence=[{"field": "source_kind", "value": payload.source_kind, "source": "input"}],
        )
```

```python
# backend/app/services/music_media_recognizer.py
from app.schemas.music_media import MusicMediaInfo, MusicMetaBase


class MusicMediaRecognizer:
    def __init__(self, metadata_service, metadata_adapter):
        self.metadata_service = metadata_service
        self.metadata_adapter = metadata_adapter

    def recognize(self, base: MusicMetaBase) -> MusicMediaInfo:
        recording_id = base.external_refs.get("musicbrainz_recording_id")
        album_id = base.external_refs.get("musicbrainz_release_group_id")
        artist_id = base.external_refs.get("musicbrainz_artist_id")
        provider_id = recording_id or album_id or artist_id or ""
        strategy = "strong_ref" if provider_id else "not_implemented"
        return MusicMediaInfo(
            entity_type=base.entity_type,
            provider="musicbrainz",
            provider_id=provider_id,
            title=base.canonical_title,
            artist_names=base.canonical_artist_names,
            album_title=base.canonical_album_title,
            match_strategy=strategy,
            match_confidence=1.0 if provider_id else 0.0,
            match_evidence=[{"field": "provider_id", "value": provider_id}] if provider_id else [],
            diagnostics=[] if provider_id else ["recognition_not_implemented"],
            external_refs=base.external_refs,
        )
```

```python
# backend/app/services/music_media_info_hydrator.py
class MusicMediaInfoHydrator:
    def __init__(self, metadata_service):
        self.metadata_service = metadata_service

    def hydrate(self, media):
        return self.metadata_service.get_detail(media.entity_type, media.provider_id)
```

```python
# backend/app/services/music_media_chain.py
from app.schemas.music_media import MusicResolveDetailResponse
from app.services.music_media_info_hydrator import MusicMediaInfoHydrator
from app.services.music_media_input_adapter import MusicMediaInputAdapter
from app.services.music_media_recognizer import MusicMediaRecognizer
from app.services.music_meta_base_builder import MusicMetaBaseBuilder


class MusicMediaChain:
    def __init__(self, metadata_service, metadata_adapter):
        self.input_adapter = MusicMediaInputAdapter()
        self.base_builder = MusicMetaBaseBuilder()
        self.recognizer = MusicMediaRecognizer(metadata_service=metadata_service, metadata_adapter=metadata_adapter)
        self.hydrator = MusicMediaInfoHydrator(metadata_service=metadata_service)

    def resolve(self, input):
        normalized = self.input_adapter.from_input(input)
        base = self.base_builder.build(normalized)
        return self.recognizer.recognize(base)

    def resolve_detail(self, input):
        media = self.resolve(input)
        detail = self.hydrator.hydrate(media)
        return MusicResolveDetailResponse(media=media, detail=detail)
```

- [ ] **Step 4: Strip lookup responsibility out of `MetadataService`**

```python
# backend/app/services/metadata.py
# remove:
# def lookup_detail(...)
#
# keep:
# - search()
# - get_artist_detail()
# - get_album_detail()
# - get_track_detail()
# - get_detail()
```

Expected code direction:
- `MetadataService` only owns provider-backed search/detail behavior.
- Recognition orchestration is moved into `MusicMediaChain`.

- [ ] **Step 5: Run the targeted backend chain tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_music_media_chain.py'
```

Expected:
- PASS for schema + strong-ref chain tests.

- [ ] **Step 6: Commit**

```bash
git add \
  backend/app/services/music_media_input_adapter.py \
  backend/app/services/music_meta_base_builder.py \
  backend/app/services/music_media_recognizer.py \
  backend/app/services/music_media_info_hydrator.py \
  backend/app/services/music_media_chain.py \
  backend/app/services/metadata.py \
  backend/tests/test_music_media_chain.py
git commit -m "feat: add unified music media chain services"
```

### Task 3: Replace the old metadata lookup HTTP path

**Files:**
- Create: `backend/app/api/routes/media.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/app/api/routes/search.py`
- Modify: `backend/app/core/dependencies.py`
- Test: `backend/tests/test_music_media_api.py`

- [ ] **Step 1: Write failing API tests for the new endpoints**

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_media_resolve_detail_returns_detail_payload():
    response = client.post(
        "/api/v1/plugin/musicpilot/media/resolve/detail",
        json={
            "input": {
                "entity_hint": "track",
                "source_kind": "detail",
                "title": "Hello",
                "artist_names": ["Adele"],
                "external_refs": {"musicbrainz_recording_id": "recording-hello"},
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["media"]["provider_id"] == "recording-hello"
    assert body["data"]["detail"]["id"] == "recording-hello"


def test_old_metadata_lookup_route_is_gone():
    response = client.post(
        "/api/v1/plugin/musicpilot/metadata/lookup",
        json={"entity_type": "track", "hints": {"title": "Hello"}},
    )
    assert response.status_code == 404
```

- [ ] **Step 2: Run the API tests and confirm route failures**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_music_media_api.py'
```

Expected:
- FAIL because `/media/resolve/detail` does not exist yet.

- [ ] **Step 3: Add dependencies and new media routes**

```python
# backend/app/core/dependencies.py
from app.services.music_media_chain import MusicMediaChain


def get_music_media_chain() -> MusicMediaChain:
    metadata_service = get_metadata_service()
    session = SessionLocal()
    try:
        adapter = build_metadata_provider_adapter()
        return MusicMediaChain(metadata_service=metadata_service, metadata_adapter=adapter)
    finally:
        session.close()
```

```python
# backend/app/api/routes/media.py
from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_music_media_chain
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.music_media import MusicResolveDetailRequest, MusicResolveRequest

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/resolve", summary="Resolve music media")
async def resolve_media(payload: MusicResolveRequest, request: Request, chain=Depends(get_music_media_chain)) -> ApiResponse:
    media = chain.resolve(payload.input)
    return success_response(request, data=media, message="Music media resolved.", code="MUSIC_MEDIA_RESOLVE_OK")


@router.post("/resolve/detail", summary="Resolve music media detail")
async def resolve_media_detail(
    payload: MusicResolveDetailRequest,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    result = chain.resolve_detail(payload.input)
    return success_response(request, data=result, message="Music media detail resolved.", code="MUSIC_MEDIA_DETAIL_OK")
```

```python
# backend/app/api/router.py
from .routes import media

plugin_api_router.include_router(media.router)
```

- [ ] **Step 4: Delete old lookup route wiring**

```python
# backend/app/api/routes/search.py
# remove:
# class MetadataLookupRequest
# @router.post("/lookup")
# @router.post("/metadata/lookup")
# async def metadata_lookup(...)
#
# keep metadata search and direct artist/album/track detail routes only.
```

- [ ] **Step 5: Run the targeted API tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_music_media_api.py'
```

Expected:
- PASS with `200` for `/media/resolve/detail`
- PASS with `404` for removed `/metadata/lookup`

- [ ] **Step 6: Commit**

```bash
git add \
  backend/app/api/routes/media.py \
  backend/app/api/router.py \
  backend/app/api/routes/search.py \
  backend/app/core/dependencies.py \
  backend/tests/test_music_media_api.py
git commit -m "feat: replace metadata lookup with media resolve api"
```

### Task 4: Replace discovery backend output semantics

**Files:**
- Modify: `backend/app/schemas/orchestration.py`
- Modify: `backend/app/services/discovery.py`
- Modify: `backend/tests/test_discovery_service.py`

- [ ] **Step 1: Write failing discovery assembler tests for chain-based outputs**

```python
from app.schemas.mvp import EntityType
from app.schemas.orchestration import ChartEntryInfo, ChartInfo, ChartDetailData
from app.services.discovery import DiscoveryAssembler


def test_discovery_entry_exposes_music_media_input_payload_not_discovery_target():
    assembler = DiscoveryAssembler()
    chart = ChartInfo(
        id="rss-feed-youtube-top-songs",
        chart_source="rss_feed",
        chart_name="YouTube Top Songs",
        chart_type=EntityType.TRACK,
        item_count=1,
        updated_at="2026-04-12T00:00:00Z",
        mock=False,
        note="test",
    )
    entry = ChartEntryInfo(
        item_id="song-1",
        chart_id=chart.id,
        chart_source=chart.chart_source,
        chart_name=chart.chart_name,
        rank=1,
        item_type=EntityType.TRACK,
        target_id="",
        target_name="Hello",
        subtitle="Adele",
        provider="rss_feed",
        source_type="rss_feed/youtube_top_songs",
        target_payload={"title": "Hello", "artist_name": "Adele"},
        mock=False,
        note="test",
    )
    detail = assembler.build_detail(
        ChartDetailData(chart=chart, items=[entry], item_count=1, mock=False, note="test", integration_point="test")
    )
    assert "media_input" in detail.hero_entry
    assert "target" not in detail.hero_entry
```

- [ ] **Step 2: Run the discovery test and confirm old schema mismatch**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_discovery_service.py'
```

Expected:
- FAIL because `hero_entry` still exposes `target`.

- [ ] **Step 3: Replace `DiscoveryTarget` with chain-oriented discovery entry payloads**

```python
# backend/app/schemas/orchestration.py
class DiscoveryEntryView(BaseModel):
    entry: ChartEntryInfo
    media_input: dict[str, Any]
    entry_summary: str
    badges: list[str] = Field(default_factory=list)
    highlight_reason: str | None = None
    conversion_state: str = "ready"
    conversion_note: str | None = None
```

```python
# backend/app/services/discovery.py
def _build_entry_view(self, chart: ChartInfo, entry: ChartEntryInfo) -> DiscoveryEntryView:
    media_input = self._build_media_input_payload(chart, entry)
    return DiscoveryEntryView(
        entry=entry,
        media_input=media_input,
        entry_summary=self._entry_summary(entry),
        badges=self._build_badges(chart, entry),
        highlight_reason=self._highlight_reason(chart, entry),
        conversion_state="ready" if media_input else "insufficient",
        conversion_note=None if media_input else "Missing media input fields.",
    )


def _build_media_input_payload(self, chart: ChartInfo, entry: ChartEntryInfo) -> dict[str, Any]:
    payload = dict(entry.target_payload or {})
    return {
        "entity_hint": entry.item_type.value,
        "source_kind": "discovery",
        "title": payload.get("title") or entry.target_name,
        "artist_names": [payload.get("artist_name")] if payload.get("artist_name") else [],
        "album_title": payload.get("album_title"),
        "external_refs": {
            "musicbrainz_artist_id": payload.get("musicbrainz_artist_id"),
            "musicbrainz_release_group_id": payload.get("musicbrainz_release_group_id"),
            "musicbrainz_recording_id": payload.get("musicbrainz_recording_id"),
            "source_url": payload.get("provider_origin_url"),
            "source_id": payload.get("provider_origin_id"),
        },
        "source_context": {
            "chart_id": entry.chart_id,
            "chart_source": entry.chart_source,
            "chart_name": entry.chart_name,
            "rank": entry.rank,
            "family": payload.get("family"),
        },
        "raw_context": payload.get("raw_context") or {},
    }
```

- [ ] **Step 4: Update summary counts to use `conversion_state` instead of `target.conversion_ready`**

```python
# backend/app/services/discovery.py
ready_count = sum(1 for item in entry_views if item.conversion_state == "ready")
```

- [ ] **Step 5: Re-run the discovery tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_discovery_service.py'
```

Expected:
- PASS with `media_input`-backed discovery entry views.

- [ ] **Step 6: Commit**

```bash
git add \
  backend/app/schemas/orchestration.py \
  backend/app/services/discovery.py \
  backend/tests/test_discovery_service.py
git commit -m "feat: replace discovery target with media input payloads"
```

### Task 5: Replace frontend discovery-to-detail flow

**Files:**
- Create: `frontend/src/types/music-media.ts`
- Create: `frontend/src/services/music-media.ts`
- Modify: `frontend/src/types/orchestration.ts`
- Modify: `frontend/src/services/discovery-metadata.ts`
- Modify: `frontend/src/views/ChartsView.vue`
- Modify: `frontend/src/services/__tests__/discovery-metadata.spec.ts`
- Modify: `frontend/src/views/__tests__/ChartsView.spec.ts`

- [ ] **Step 1: Write failing frontend service tests for the new media resolve API**

```ts
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/services/http', () => ({
  http: {
    post: vi.fn().mockResolvedValue({
      data: {
        success: true,
        data: {
          media: { provider_id: 'recording-hello', entity_type: 'track' },
          detail: { id: 'recording-hello', title: 'Hello', entity_type: 'track' },
        },
      },
    }),
  },
}));

import { fetchResolvedMediaDetail } from '@/services/music-media';

describe('fetchResolvedMediaDetail', () => {
  it('posts MusicMediaInput payloads to /media/resolve/detail', async () => {
    const response = await fetchResolvedMediaDetail({
      entity_hint: 'track',
      source_kind: 'discovery',
      title: 'Hello',
      artist_names: ['Adele'],
    });
    expect(response.data.detail.id).toBe('recording-hello');
  });
});
```

- [ ] **Step 2: Run the frontend service test and confirm missing module failure**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
pnpm test -- --run src/services/__tests__/discovery-metadata.spec.ts
```

Expected:
- FAIL because `music-media.ts` and types do not exist yet.

- [ ] **Step 3: Add the new frontend music-media types and service**

```ts
// frontend/src/types/music-media.ts
import type { ApiResponse, EntityType, MetadataDetail } from '@/types/metadata';

export interface MusicMediaInput {
  entity_hint?: EntityType | null;
  source_kind: string;
  title?: string | null;
  subtitle?: string | null;
  artist_names: string[];
  album_title?: string | null;
  album_artist_names: string[];
  release_date?: string | null;
  year?: number | null;
  track_number?: number | null;
  disc_number?: number | null;
  external_refs: Record<string, string>;
  source_context: Record<string, unknown>;
  raw_context: Record<string, unknown>;
}

export interface MusicMediaInfo {
  entity_type: EntityType;
  provider: string;
  provider_id: string;
  title?: string | null;
  artist_names: string[];
  album_title?: string | null;
}

export interface MusicResolveDetailData {
  media: MusicMediaInfo;
  detail: MetadataDetail;
}

export type MusicResolveDetailResponse = ApiResponse<MusicResolveDetailData>;
```

```ts
// frontend/src/services/music-media.ts
import { http } from '@/services/http';
import type { MusicMediaInput, MusicResolveDetailResponse } from '@/types/music-media';

export async function fetchResolvedMediaDetail(input: MusicMediaInput): Promise<MusicResolveDetailResponse> {
  const { data } = await http.post<MusicResolveDetailResponse>('/media/resolve/detail', { input });
  return data;
}
```

- [ ] **Step 4: Replace the old discovery metadata bridge**

```ts
// frontend/src/services/discovery-metadata.ts
import { fetchResolvedMediaDetail } from '@/services/music-media';

export async function fetchDiscoveryTargetDetail(mediaInput: Record<string, unknown>) {
  return fetchResolvedMediaDetail(mediaInput as never);
}
```

```ts
// frontend/src/types/orchestration.ts
export interface DiscoveryEntryView {
  entry: ChartEntryInfo;
  media_input: Record<string, unknown>;
  entry_summary: string;
  badges: string[];
  highlight_reason?: string | null;
  conversion_state: string;
  conversion_note?: string | null;
}
```

- [ ] **Step 5: Update `ChartsView.vue` to use `media_input`**

```ts
// inside ChartsView.vue
async function openEntryDetail(item: DiscoveryEntryView) {
  if (item.conversion_state !== 'ready') {
    detailErrorMessage.value = item.conversion_note || '当前榜单项暂不支持 metadata detail。';
    detailDrawerOpen.value = true;
    return;
  }

  detailLoading.value = true;
  try {
    const response = await fetchDiscoveryTargetDetail(item.media_input);
    activeDetail.value = response.data.detail;
    detailErrorMessage.value = '';
  } catch (error) {
    detailErrorMessage.value = error instanceof Error ? error.message : 'Metadata detail 加载失败。';
  } finally {
    detailLoading.value = false;
    detailDrawerOpen.value = true;
  }
}
```

- [ ] **Step 6: Run frontend tests and build**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
pnpm test -- --run
pnpm build
```

Expected:
- PASS for updated service and chart view tests
- build succeeds with no `DiscoveryTarget` type references left.

- [ ] **Step 7: Commit**

```bash
git add \
  frontend/src/types/music-media.ts \
  frontend/src/services/music-media.ts \
  frontend/src/types/orchestration.ts \
  frontend/src/services/discovery-metadata.ts \
  frontend/src/views/ChartsView.vue \
  frontend/src/services/__tests__/discovery-metadata.spec.ts \
  frontend/src/views/__tests__/ChartsView.spec.ts
git commit -m "feat: switch discovery detail flow to media resolve"
```

### Task 6: Reconnect subscription, search, and organize upstream recognition

**Files:**
- Modify: `backend/app/services/subscription_execution.py`
- Modify: `backend/app/services/query_builder.py`
- Modify: `backend/app/services/organize.py`
- Modify: `backend/tests/test_subscription_execution.py`
- Modify: `backend/tests/test_query_builder.py`
- Modify: `backend/tests/test_organize_integration.py`

- [ ] **Step 1: Write failing tests that assert upstream logic consumes formal media objects**

```python
from app.schemas.music_media import MusicMediaInfo
from app.schemas.mvp import EntityType


def test_query_builder_accepts_music_media_info_track_input():
    service = QueryBuilderService()
    media = MusicMediaInfo(
        entity_type=EntityType.TRACK,
        provider="musicbrainz",
        provider_id="recording-hello",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        match_strategy="strong_ref",
    )
    queries = service.build_queries_from_music_media_info(media)
    assert queries[:3] == [
        "Adele Hello FLAC",
        "Adele 25 FLAC",
        "Adele Hello",
    ]


def test_subscription_execution_prefers_music_media_info_snapshot_for_search():
    service = SubscriptionExecutionService.__new__(SubscriptionExecutionService)
    media = MusicMediaInfo(
        entity_type=EntityType.TRACK,
        provider="musicbrainz",
        provider_id="recording-hello",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        match_strategy="strong_ref",
    )
    search_input = service._build_search_input_from_media_info(media)
    assert search_input["title"] == "Hello"
    assert search_input["artist_names"] == ["Adele"]
    assert search_input["album_title"] == "25"


def test_organize_can_build_upstream_context_from_music_media_info_snapshot():
    service = OrganizeService.__new__(OrganizeService)
    media = MusicMediaInfo(
        entity_type=EntityType.TRACK,
        provider="musicbrainz",
        provider_id="recording-hello",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        track_number=1,
        match_strategy="strong_ref",
    )
    context = service._build_metadata_context_from_media_info(media)
    assert context["track_title"] == "Hello"
    assert context["artist_name"] == "Adele"
    assert context["album_title"] == "25"
    assert context["track_number"] == 1
```

- [ ] **Step 2: Run the targeted backend tests and confirm missing `MusicMediaInfo` consumption support**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_subscription_execution.py'
.venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- FAIL on missing `MusicMediaInfo` snapshot support.

- [ ] **Step 3: Implement minimal downstream consumption**

```python
# subscription_execution.py
# when a run target already includes a resolved formal media snapshot:
#   use that snapshot as the primary search/build input
# else:
#   resolve through MusicMediaChain first
```

```python
# query_builder.py
def build_queries_from_music_media_info(media_info):
    if media_info.entity_type == EntityType.TRACK:
        return [
            f"{' '.join(media_info.artist_names)} {media_info.title} FLAC",
            f"{' '.join(media_info.artist_names)} {media_info.album_title or media_info.title} FLAC",
            f"{' '.join(media_info.artist_names)} {media_info.title}",
        ]
```

```python
# organize.py
# accept formal media snapshots as upstream metadata context,
# falling back to file/tag recognition only when no formal media info is present
```

- [ ] **Step 4: Re-run the targeted backend tests**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_subscription_execution.py'
.venv/bin/python -m unittest discover -s tests -p 'test_query_builder.py'
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- PASS for the new chain-backed upstream behavior.

- [ ] **Step 5: Commit**

```bash
git add \
  backend/app/services/subscription_execution.py \
  backend/app/services/query_builder.py \
  backend/app/services/organize.py \
  backend/tests/test_subscription_execution.py \
  backend/tests/test_query_builder.py \
  backend/tests/test_organize_integration.py
git commit -m "feat: reuse music media info across downstream flows"
```

### Task 7: Sync runtime mirrors, docs, and run full verification

**Files:**
- Modify mirrored runtime files under `plugin_runtime/plugins/musicpilot/...`
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/14_架构收缩与语义归一说明.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
- Create: `docs/40_统一音乐媒体解析链_运行态验证.md`

- [ ] **Step 1: Mirror the backend/runtime changes**

```text
Sync every backend service and schema change that is part of plugin runtime execution into:
- plugin_runtime/plugins/musicpilot/api/routes/
- plugin_runtime/plugins/musicpilot/services/
- plugin_runtime/plugins/musicpilot/schemas/
```

- [ ] **Step 2: Update docs to remove old discovery bridge language**

Required doc direction:
- remove `DiscoveryTarget` and `resolution_hints` as active-path wording
- describe `/media/resolve` as the new unified recognition entry
- describe `MusicMediaInput -> MusicMetaBase -> MusicMediaInfo` as active implementation, not future baseline

- [ ] **Step 3: Run backend full test suite**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests
```

Expected:
- PASS for all backend tests with old lookup tests removed or rewritten.

- [ ] **Step 4: Run frontend tests and build**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
pnpm test -- --run
pnpm build
```

Expected:
- PASS
- no stale `DiscoveryTarget` references remain

- [ ] **Step 5: Repackage the plugin runtime**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
python3 scripts/package_plugin.py
```

Expected:
- package succeeds
- runtime mirror includes the new media resolve route and new schemas/services

- [ ] **Step 6: Record runtime validation**

Validation checklist:
- `GET /api/v1/plugin/musicpilot/charts` still returns discovery views
- clicking a chart entry resolves via `/media/resolve/detail`
- `POST /api/v1/plugin/musicpilot/metadata/lookup` is no longer part of the active flow
- metadata drawer still opens from discovery

Write results to:

```text
docs/40_统一音乐媒体解析链_运行态验证.md
```

- [ ] **Step 7: Commit**

```bash
git add \
  plugin_runtime \
  README.md \
  backend/README.md \
  docs/14_架构收缩与语义归一说明.md \
  docs/28_项目整体任务盘点与执行路线.md \
  docs/40_统一音乐媒体解析链_运行态验证.md
git commit -m "feat: complete unified music media chain refactor"
```

## Self-review

### Spec coverage
- Core three-layer model: covered in Tasks 1 and 2.
- Unified chain services: covered in Task 2.
- New HTTP API and removal of `/metadata/lookup`: covered in Task 3.
- Discovery and frontend contract replacement: covered in Tasks 4 and 5.
- Downstream reuse across search/subscription/organize: covered in Task 6.
- Runtime mirror, docs, and final verification: covered in Task 7.

### Placeholder scan
- The plan avoids `TODO/TBD` placeholders in the implementation path.
- The Task 6 test sketches have been converted into concrete assertions so execution can proceed without placeholder follow-up work.

### Type consistency
- The plan consistently uses:
  - `MusicMediaInput`
  - `MusicMetaBase`
  - `MusicMediaInfo`
  - `MusicMediaChain`
  - `/media/resolve`
  - `/media/resolve/detail`
- The plan consistently removes:
  - `DiscoveryTarget`
  - `resolution_mode`
  - `resolution_hints`
  - `/metadata/lookup`
