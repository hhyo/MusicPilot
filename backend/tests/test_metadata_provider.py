"""Tests for metadata provider adapters and live provider integration."""

from __future__ import annotations

import unittest

import httpx
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base
from app.schemas.metadata import MetadataDetail, MetadataSearchData, MetadataSearchRequest, MetadataSummary
from app.schemas.music_media import MusicMediaInput
from app.schemas.mvp import EntityType, ReleaseType
from app.services.metadata import MetadataService
from app.services.music_media_chain import MusicMediaChain


class MetadataServiceLiveProviderTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)

    def tearDown(self) -> None:
        self.session.close()

    def test_service_uses_live_provider_search_when_adapter_supports_live_queries(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class FakeLiveAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover - not used in this test
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=1,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:  # pragma: no cover - not used
                raise NotImplementedError

        service = MetadataService(session=self.session, adapter=FakeLiveAdapter())

        result = service.search(
            MetadataSearchRequest(keyword="Adele", type=EntityType.ARTIST, page=1, page_size=10)
        )

        self.assertEqual(result.provider, "fake_live")
        self.assertEqual(result.source_type, "live_api")
        self.assertEqual(result.integration_point, "fake.live.search")
        self.assertEqual(service.repository.summary()["search_history"], 1)


class MusicMediaChainRecognitionTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)

    def tearDown(self) -> None:
        self.session.close()

    def build_chain(self, adapter) -> MusicMediaChain:
        service = MetadataService(session=self.session, adapter=adapter)
        return MusicMediaChain(metadata_service=service, metadata_adapter=adapter)

    def build_input(
        self,
        entity_type: EntityType,
        *,
        artist_name: str | None = None,
        title: str | None = None,
        album_title: str | None = None,
        title_candidates: list[str] | None = None,
        artist_name_candidates: list[str] | None = None,
        album_title_candidates: list[str] | None = None,
    ) -> MusicMediaInput:
        return MusicMediaInput(
            entity_hint=entity_type,
            source_kind="discovery",
            title=title,
            artist_names=[artist_name] if artist_name else [],
            album_title=album_title,
            raw_context={
                "title_candidates": title_candidates or [],
                "artist_name_candidates": artist_name_candidates or [],
                "album_title_candidates": album_title_candidates or [],
            },
        )

    def test_track_lookup_builds_artist_title_album_keyword_and_returns_detail(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class FakeLiveAdapter(MetadataProviderAdapter):
            def __init__(self) -> None:
                self.last_keyword: str | None = None

            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                self.last_keyword = payload.keyword
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=1,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-1",
                            title="Hello",
                            artist_name="Adele",
                            album_title="25",
                            track_title="Hello",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Hello",
                    artist_name="Adele",
                    album_title="25",
                    track_title="Hello",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        adapter = FakeLiveAdapter()
        chain = self.build_chain(adapter)

        result = chain.resolve_detail(self.build_input(EntityType.TRACK, artist_name="Adele", title="Hello", album_title="25"))

        self.assertEqual(adapter.last_keyword, "Adele Hello 25")
        self.assertEqual(result.detail.id, "track-1")

    def test_album_and_artist_lookup_keyword_shapes(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class FakeLiveAdapter(MetadataProviderAdapter):
            def __init__(self) -> None:
                self.keywords: list[str] = []

            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                self.keywords.append(payload.keyword)
                entity_type = payload.type
                summary_id = "album-1" if entity_type == EntityType.ALBUM else "artist-1"
                summary_title = "25" if entity_type == EntityType.ALBUM else "Adele"
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=entity_type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=1,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=entity_type,
                            id=summary_id,
                            title=summary_title,
                            artist_name="Adele",
                            album_title="25" if entity_type == EntityType.ALBUM else None,
                            track_title=None,
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="ok",
                    artist_name="Adele",
                    album_title="25" if entity_type == EntityType.ALBUM else None,
                    track_title=None,
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        adapter = FakeLiveAdapter()
        chain = self.build_chain(adapter)

        chain.resolve_detail(self.build_input(EntityType.ALBUM, artist_name="Adele", album_title="25"))
        chain.resolve_detail(self.build_input(EntityType.ARTIST, artist_name="Adele"))

        self.assertEqual(adapter.keywords, ["Adele 25", "Adele"])

    def test_lookup_requires_hints_and_raises_404_when_no_result(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class EmptyLiveAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=0,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:  # pragma: no cover
                raise NotImplementedError

        chain = self.build_chain(EmptyLiveAdapter())

        with self.assertRaises(HTTPException) as ctx_missing:
            chain.resolve_detail(MusicMediaInput(entity_hint=EntityType.TRACK, source_kind="discovery"))
        self.assertEqual(ctx_missing.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx_not_found:
            chain.resolve_detail(self.build_input(EntityType.ARTIST, artist_name="NotFound Artist"))
        self.assertEqual(ctx_not_found.exception.status_code, 404)

    def test_lookup_prefers_precise_match_over_first_item(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class RankedLiveAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=2,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-wrong-first",
                            title="Hello (Live)",
                            artist_name="Adele",
                            album_title="25",
                            track_title="Hello (Live)",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="wrong",
                        ),
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-best-second",
                            title="Hello",
                            artist_name="Adele",
                            album_title="25",
                            track_title="Hello",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="best",
                        ),
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Hello",
                    artist_name="Adele",
                    album_title="25",
                    track_title="Hello",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        chain = self.build_chain(RankedLiveAdapter())

        result = chain.resolve_detail(self.build_input(EntityType.TRACK, artist_name="Adele", title="Hello", album_title="25"))

        self.assertEqual(result.detail.id, "track-best-second")

    def test_track_lookup_requires_album_match_when_album_hint_is_provided(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class AlbumMismatchAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=1,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-live-version",
                            title="Hello",
                            artist_name="Adele",
                            album_title="Live at Royal Albert Hall",
                            track_title="Hello",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="mismatch",
                        )
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:  # pragma: no cover
                raise NotImplementedError

        chain = self.build_chain(AlbumMismatchAdapter())

        with self.assertRaises(HTTPException) as ctx:
            chain.resolve_detail(self.build_input(EntityType.TRACK, artist_name="Adele", title="Hello", album_title="25"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_track_lookup_normalizes_title_noise_before_searching(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class NoisyTitleAdapter(MetadataProviderAdapter):
            def __init__(self) -> None:
                self.keywords: list[str] = []

            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                self.keywords.append(payload.keyword)
                items: list[MetadataSummary] = []
                if payload.keyword == "Adele Hello 25":
                    items = [
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-clean-title",
                            title="Hello",
                            artist_name="Adele",
                            album_title="25",
                            track_title="Hello",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ]
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=len(items),
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=items,
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Hello",
                    artist_name="Adele",
                    album_title="25",
                    track_title="Hello",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        adapter = NoisyTitleAdapter()
        chain = self.build_chain(adapter)

        result = chain.resolve_detail(
            self.build_input(EntityType.TRACK, artist_name="Adele", title="Hello - Remastered 2015", album_title="25")
        )

        self.assertEqual(result.detail.id, "track-clean-title")
        self.assertEqual(adapter.keywords, ["Adele Hello 25"])

    def test_album_lookup_tries_fallback_keyword_order_until_match(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class AlbumFallbackAdapter(MetadataProviderAdapter):
            def __init__(self) -> None:
                self.keywords: list[str] = []

            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                self.keywords.append(payload.keyword)
                items: list[MetadataSummary] = []
                if payload.keyword == "25 Adele":
                    items = [
                        MetadataSummary(
                            entity_type=EntityType.ALBUM,
                            id="album-fallback-match",
                            title="25",
                            artist_name="Adele",
                            album_title="25",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ]
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=len(items),
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=items,
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="25",
                    artist_name="Adele",
                    album_title="25",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        adapter = AlbumFallbackAdapter()
        chain = self.build_chain(adapter)

        result = chain.resolve_detail(self.build_input(EntityType.ALBUM, artist_name="Adele", album_title="25"))

        self.assertEqual(result.detail.id, "album-fallback-match")
        self.assertEqual(adapter.keywords, ["Adele 25", "25 Adele"])

    def test_lookup_raises_404_when_search_has_items_but_none_match_minimum_criteria(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class NonMatchingLiveAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=2,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.ALBUM,
                            id="album-1",
                            title="21",
                            artist_name="Adele",
                            album_title="21",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="wrong",
                        ),
                        MetadataSummary(
                            entity_type=EntityType.ALBUM,
                            id="album-2",
                            title="19",
                            artist_name="Adele",
                            album_title="19",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="wrong2",
                        ),
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:  # pragma: no cover
                raise NotImplementedError

        chain = self.build_chain(NonMatchingLiveAdapter())

        with self.assertRaises(HTTPException) as ctx:
            chain.resolve_detail(self.build_input(EntityType.ALBUM, artist_name="Adele", album_title="25"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_lookup_converts_provider_http_failures_to_502(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class FailingSearchAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                raise httpx.ReadTimeout("search timeout")

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:  # pragma: no cover
                raise NotImplementedError

        with self.assertRaises(HTTPException) as ctx_search:
            self.build_chain(FailingSearchAdapter()).resolve_detail(self.build_input(EntityType.ARTIST, artist_name="Adele"))
        self.assertEqual(ctx_search.exception.status_code, 502)

        class FailingDetailAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=1,
                    page_size=10,
                    total=1,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.ARTIST,
                            id="artist-1",
                            title="Adele",
                            artist_name="Adele",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                raise httpx.ConnectError("detail connect error")

        with self.assertRaises(HTTPException) as ctx_detail:
            self.build_chain(FailingDetailAdapter()).resolve_detail(self.build_input(EntityType.ARTIST, artist_name="Adele"))
        self.assertEqual(ctx_detail.exception.status_code, 502)

    def test_lookup_artist_credit_matches_common_connectors_and_featuring_forms(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class ArtistCreditAdapter(MetadataProviderAdapter):
            def __init__(self) -> None:
                self._items = [
                    MetadataSummary(
                        entity_type=EntityType.TRACK,
                        id="track-1",
                        title="Collab Song",
                        artist_name="Artist A, Artist B",
                        album_title="Collab Album",
                        track_title="Collab Song",
                        provider="fake_live",
                        source_type="live_api",
                        mock=False,
                        note="ok",
                    ),
                    MetadataSummary(
                        entity_type=EntityType.TRACK,
                        id="track-2",
                        title="Collab Song",
                        artist_name="Artist A & Artist B",
                        album_title="Collab Album",
                        track_title="Collab Song",
                        provider="fake_live",
                        source_type="live_api",
                        mock=False,
                        note="ok",
                    ),
                ]

            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=len(self._items),
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=self._items,
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Collab Song",
                    artist_name="Artist A & Artist B",
                    album_title="Collab Album",
                    track_title="Collab Song",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        chain = self.build_chain(ArtistCreditAdapter())

        detail_amp = chain.resolve_detail(self.build_input(EntityType.TRACK, artist_name="Artist A & Artist B", title="Collab Song"))
        self.assertEqual(detail_amp.detail.id, "track-1")

        detail_feat = chain.resolve_detail(
            self.build_input(EntityType.TRACK, artist_name="Artist A feat. Artist B", title="Collab Song")
        )
        self.assertEqual(detail_feat.detail.id, "track-1")

    def test_artist_lookup_normalizes_single_artist_punctuation_variants(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class ArtistPunctuationAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=1,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.ARTIST,
                            id="artist-tyler",
                            title="Tyler The Creator",
                            artist_name="Tyler The Creator",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Tyler The Creator",
                    artist_name="Tyler The Creator",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        chain = self.build_chain(ArtistPunctuationAdapter())

        detail = chain.resolve_detail(self.build_input(EntityType.ARTIST, artist_name="Tyler, The Creator"))

        self.assertEqual(detail.detail.id, "artist-tyler")

    def test_track_lookup_uses_candidate_arrays_when_primary_rss_hints_are_weaker(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class CandidateArrayAdapter(MetadataProviderAdapter):
            def __init__(self) -> None:
                self.keywords: list[str] = []

            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                self.keywords.append(payload.keyword)
                items: list[MetadataSummary] = []
                if payload.keyword == "Lady Gaga Bruno Mars Die With A Smile":
                    items = [
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-die-with-a-smile",
                            title="Die With A Smile",
                            artist_name="Lady Gaga Bruno Mars",
                            album_title="Die With A Smile",
                            track_title="Die With A Smile",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="ok",
                        )
                    ]
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=len(items),
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=items,
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Die With A Smile",
                    artist_name="Lady Gaga Bruno Mars",
                    album_title="Die With A Smile",
                    track_title="Die With A Smile",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        adapter = CandidateArrayAdapter()
        chain = self.build_chain(adapter)

        detail = chain.resolve_detail(
            self.build_input(
                EntityType.TRACK,
                artist_name="Lady Gaga & Bruno Mars",
                title="Die With A Smile (Official Video)",
                title_candidates=["Die With A Smile (Official Video)", "Die With A Smile"],
                artist_name_candidates=["Lady Gaga & Bruno Mars", "Lady Gaga Bruno Mars"],
            )
        )

        self.assertEqual(detail.detail.id, "track-die-with-a-smile")
        self.assertIn("Lady Gaga & Bruno Mars Die With A Smile", adapter.keywords)
        self.assertIn("Lady Gaga Bruno Mars Die With A Smile", adapter.keywords)

    def test_track_lookup_prefers_full_artist_credit_match_over_weaker_primary_artist_fallback(self) -> None:
        from app.adapters.metadata_provider import MetadataProviderAdapter

        class ArtistFallbackAdapter(MetadataProviderAdapter):
            @property
            def provider(self) -> str:
                return "fake_live"

            @property
            def source_type(self) -> str:
                return "live_api"

            @property
            def supports_live_queries(self) -> bool:
                return True

            def load_seed_catalog(self):  # pragma: no cover
                raise NotImplementedError

            def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
                return MetadataSearchData(
                    keyword=payload.keyword,
                    entity_type=payload.type,
                    page=payload.page,
                    page_size=payload.page_size,
                    total=2,
                    provider=self.provider,
                    source_type=self.source_type,
                    integration_point="fake.live.search",
                    items=[
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-solo",
                            title="Die With A Smile",
                            artist_name="Lady Gaga",
                            album_title="Solo Single",
                            track_title="Die With A Smile",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="solo",
                        ),
                        MetadataSummary(
                            entity_type=EntityType.TRACK,
                            id="track-duet",
                            title="Die With A Smile",
                            artist_name="Lady Gaga & Bruno Mars",
                            album_title="Duet Single",
                            track_title="Die With A Smile",
                            provider=self.provider,
                            source_type=self.source_type,
                            mock=False,
                            note="duet",
                        ),
                    ],
                )

            def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
                artist_name = "Lady Gaga" if entity_id == "track-solo" else "Lady Gaga & Bruno Mars"
                return MetadataDetail(
                    entity_type=entity_type,
                    id=entity_id,
                    title="Die With A Smile",
                    artist_name=artist_name,
                    album_title="Duet Single" if entity_id == "track-duet" else "Solo Single",
                    track_title="Die With A Smile",
                    provider=self.provider,
                    source_type=self.source_type,
                    mock=False,
                    note="ok",
                    integration_point="fake.live.detail",
                )

        chain = self.build_chain(ArtistFallbackAdapter())

        detail = chain.resolve_detail(
            self.build_input(
                EntityType.TRACK,
                artist_name="Lady Gaga feat. Bruno Mars",
                title="Die With A Smile [Official Lyric Video]",
                artist_name_candidates=["Lady Gaga feat. Bruno Mars", "Lady Gaga"],
            )
        )

        self.assertEqual(detail.detail.id, "track-duet")


class MusicBrainzMetadataProviderAdapterTest(unittest.TestCase):
    def test_search_reuses_cached_result_for_identical_payload(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            body = {
                "count": 1,
                "offset": 0,
                "artists": [
                    {
                        "id": "mb-artist-1",
                        "name": "Adele",
                        "country": "GB",
                        "aliases": [{"name": "阿黛尔"}],
                        "life-span": {"begin": "2008-01-01"},
                        "tags": [{"name": "pop"}],
                    }
                ],
            }
            return httpx.Response(200, json=body)

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")
        payload = MetadataSearchRequest(keyword="Adele", type=EntityType.ARTIST, page=1, page_size=10)

        first = adapter.search(payload)
        second = adapter.search(payload)

        self.assertEqual(call_count, 1)
        self.assertEqual(first.items[0].title, second.items[0].title)

    def test_detail_reuses_cached_result_for_identical_entity(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if request.url.path == "/ws/2/release-group/mb-album-25":
                body = {
                    "id": "mb-album-25",
                    "title": "25",
                    "primary-type": "Album",
                    "first-release-date": "2015-11-20",
                    "aliases": [{"name": "二十五"}],
                    "tags": [{"name": "pop"}],
                    "artist-credit": [
                        {
                            "name": "Adele",
                            "artist": {
                                "id": "mb-artist-1",
                                "name": "Adele",
                            },
                        }
                    ],
                    "releases": [{"id": "release-25-1", "title": "25", "status": "Official"}],
                }
                return httpx.Response(200, json=body)
            if request.url.path == "/ws/2/release/release-25-1":
                return httpx.Response(200, json={"id": "release-25-1", "media": []})
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        first = adapter.get_detail(EntityType.ALBUM, "mb-album-25")
        second = adapter.get_detail(EntityType.ALBUM, "mb-album-25")

        self.assertEqual(call_count, 2)
        self.assertEqual(first.album_title, second.album_title)

    def test_artist_search_maps_musicbrainz_result(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/ws/2/artist")
            self.assertEqual(request.url.params["fmt"], "json")
            self.assertEqual(request.url.params["dismax"], "true")
            body = {
                "count": 1,
                "offset": 0,
                "artists": [
                    {
                        "id": "mb-artist-1",
                        "name": "Adele",
                        "country": "GB",
                        "aliases": [{"name": "阿黛尔"}],
                        "life-span": {"begin": "2008-01-01"},
                        "tags": [{"name": "pop"}, {"name": "soul"}],
                    }
                ],
            }
            return httpx.Response(200, json=body)

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        result = adapter.search(
            MetadataSearchRequest(keyword="Adele", type=EntityType.ARTIST, page=1, page_size=10)
        )

        self.assertEqual(result.total, 1)
        self.assertEqual(result.provider, "musicbrainz")
        self.assertEqual(result.source_type, "musicbrainz_ws2")
        self.assertFalse(result.items[0].mock)
        self.assertEqual(result.items[0].title, "Adele")
        self.assertEqual(result.items[0].artist_name, "Adele")
        self.assertEqual(result.items[0].year, 2008)
        self.assertEqual(result.items[0].external_ids["musicbrainz"], "mb-artist-1")

    def test_search_skips_dismax_for_advanced_query(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/ws/2/artist")
            self.assertNotIn("dismax", request.url.params)
            return httpx.Response(200, json={"count": 0, "offset": 0, "artists": []})

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        result = adapter.search(
            MetadataSearchRequest(
                keyword='artist:"Adele" AND country:GB',
                type=EntityType.ARTIST,
                page=1,
                page_size=10,
            )
        )

        self.assertEqual(result.total, 0)

    def test_artist_detail_exposes_discovery_context(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/ws/2/artist/mb-artist-adele")
            return httpx.Response(
                200,
                json={
                    "id": "mb-artist-adele",
                    "name": "Adele",
                    "sort-name": "Adele",
                    "type": "Person",
                    "country": "GB",
                    "area": {"name": "United Kingdom"},
                    "begin-area": {"name": "Tottenham"},
                    "life-span": {"begin": "1988-05-05", "ended": False},
                    "disambiguation": "English singer-songwriter",
                    "aliases": [{"name": "阿黛尔"}],
                    "tags": [{"name": "pop"}, {"name": "soul"}],
                    "release-groups": [
                        {
                            "id": "album-30",
                            "title": "30",
                            "primary-type": "Album",
                            "first-release-date": "2021-11-19",
                        },
                        {
                            "id": "album-25",
                            "title": "25",
                            "primary-type": "Album",
                            "first-release-date": "2015-11-20",
                        },
                        {
                            "id": "single-easy-on-me",
                            "title": "Easy on Me",
                            "primary-type": "Single",
                            "first-release-date": "2021-10-15",
                        },
                    ],
                },
            )

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.ARTIST, "mb-artist-adele")

        self.assertEqual(detail.sort_name, "Adele")
        self.assertEqual(detail.artist_type, "Person")
        self.assertEqual(detail.country, "GB")
        self.assertEqual(detail.area_name, "United Kingdom")
        self.assertEqual(detail.begin_area_name, "Tottenham")
        self.assertEqual(detail.ended, False)
        self.assertEqual(detail.disambiguation, "English singer-songwriter")
        self.assertEqual(detail.release_group_count, 3)
        self.assertEqual(detail.primary_release_types, ["Album", "Single"])
        self.assertEqual([item.id for item in detail.related_albums], ["album-30", "album-25", "single-easy-on-me"])
        self.assertEqual(detail.related_albums[0].subtitle, "Album · 2021")
        self.assertEqual([item.id for item in detail.featured_albums], ["album-30", "album-25"])
        self.assertEqual([item.id for item in detail.featured_singles], ["single-easy-on-me"])
        self.assertEqual(detail.featured_other_releases, [])
        self.assertEqual(
            detail.featured_release_group_counts,
            {"album": 2, "single": 1, "other": 0, "total": 3},
        )

    def test_album_detail_maps_release_group_result(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            self.assertEqual(request.url.params["fmt"], "json")
            if request.url.path == "/ws/2/release-group/mb-album-25":
                return httpx.Response(
                    200,
                    json={
                        "id": "mb-album-25",
                        "title": "25",
                        "primary-type": "Album",
                        "first-release-date": "2015-11-20",
                        "aliases": [{"name": "二十五"}],
                        "tags": [{"name": "pop"}],
                        "artist-credit": [
                            {
                                "name": "Adele",
                                "artist": {
                                    "id": "mb-artist-1",
                                    "name": "Adele",
                                },
                            }
                        ],
                        "releases": [
                            {
                                "id": "release-25-1",
                                "title": "25",
                                "status": "Official",
                            }
                        ],
                    },
                )
            if request.url.path == "/ws/2/release/release-25-1":
                return httpx.Response(
                    200,
                    json={
                        "id": "release-25-1",
                        "media": [
                            {
                                "tracks": [
                                    {
                                        "id": "release-track-1",
                                        "title": "Hello",
                                        "number": "1",
                                        "position": 1,
                                        "recording": {"id": "recording-hello", "title": "Hello"},
                                    }
                                ]
                            }
                        ],
                    },
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.ALBUM, "mb-album-25")

        self.assertEqual(calls, ["/ws/2/release-group/mb-album-25", "/ws/2/release/release-25-1"])
        self.assertEqual(detail.provider, "musicbrainz")
        self.assertEqual(detail.source_type, "musicbrainz_ws2")
        self.assertEqual(detail.entity_type, EntityType.ALBUM)
        self.assertEqual(detail.album_title, "25")
        self.assertEqual(detail.artist_name, "Adele")
        self.assertEqual(detail.year, 2015)
        self.assertEqual(detail.release_type, ReleaseType.ALBUM)
        self.assertEqual(detail.external_ids["musicbrainz"], "mb-album-25")
        self.assertEqual(detail.related_artists[0].title, "Adele")
        self.assertEqual(detail.tracks[0].id, "recording-hello")

    def test_album_detail_uses_release_tracks_instead_of_release_list(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == "/ws/2/release-group/mb-album-25":
                return httpx.Response(
                    200,
                    json={
                        "id": "mb-album-25",
                        "title": "25",
                        "primary-type": "Album",
                        "disambiguation": "studio album",
                        "first-release-date": "2015-11-20",
                        "artist-credit": [
                            {
                                "name": "Adele",
                                "artist": {"id": "mb-artist-1", "name": "Adele"},
                            }
                        ],
                        "releases": [
                            {
                                "id": "release-25-official",
                                "title": "25",
                                "date": "2015-11-20",
                                "status": "Official",
                            },
                            {
                                "id": "release-25-bootleg",
                                "title": "25 (Bootleg)",
                                "date": "2015-11-21",
                                "status": "Bootleg",
                            },
                        ],
                    },
                )
            if request.url.path == "/ws/2/release/release-25-official":
                return httpx.Response(
                    200,
                    json={
                        "id": "release-25-official",
                        "title": "25",
                        "media": [
                            {
                                "tracks": [
                                    {
                                        "id": "release-track-1",
                                        "title": "Hello",
                                        "number": "1",
                                        "position": 1,
                                        "recording": {"id": "recording-hello", "title": "Hello"},
                                    },
                                    {
                                        "id": "release-track-2",
                                        "title": "Send My Love",
                                        "number": "2",
                                        "position": 2,
                                        "recording": {"id": "recording-send-my-love", "title": "Send My Love"},
                                    },
                                ]
                            }
                        ],
                    },
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.ALBUM, "mb-album-25")

        self.assertEqual(
            calls,
            ["/ws/2/release-group/mb-album-25", "/ws/2/release/release-25-official"],
        )
        self.assertEqual(detail.disambiguation, "studio album")
        self.assertEqual(detail.release_count, 2)
        self.assertEqual([track.id for track in detail.tracks], ["recording-hello", "recording-send-my-love"])
        self.assertEqual(detail.tracks[0].title, "Hello")
        self.assertEqual(detail.tracks[0].track_number, 1)

    def test_album_detail_exposes_release_context(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/ws/2/release-group/mb-album-25":
                return httpx.Response(
                    200,
                    json={
                        "id": "mb-album-25",
                        "title": "25",
                        "primary-type": "Album",
                        "secondary-types": ["Live"],
                        "artist-credit": [
                            {
                                "name": "Adele",
                                "artist": {"id": "mb-artist-1", "name": "Adele"},
                            }
                        ],
                        "releases": [
                            {
                                "id": "release-25-official",
                                "title": "25",
                                "status": "Official",
                                "date": "2015-11-20",
                                "country": "GB",
                                "barcode": "1234567890123",
                            }
                        ],
                    },
                )
            if request.url.path == "/ws/2/release/release-25-official":
                return httpx.Response(
                    200,
                    json={
                        "id": "release-25-official",
                        "country": "GB",
                        "status": "Official",
                        "barcode": "1234567890123",
                        "label-info": [
                            {"label": {"name": "XL Recordings"}},
                            {"label": {"name": "Columbia"}},
                        ],
                        "media": [
                            {
                                "position": 1,
                                "format": "Digital Media",
                                "tracks": [
                                    {
                                        "id": "release-track-1",
                                        "title": "Hello",
                                        "number": "1",
                                        "position": 1,
                                        "recording": {"id": "recording-hello", "title": "Hello"},
                                    },
                                    {
                                        "id": "release-track-2",
                                        "title": "Send My Love",
                                        "number": "2",
                                        "position": 2,
                                        "recording": {"id": "recording-send-my-love", "title": "Send My Love"},
                                    },
                                ],
                            }
                        ],
                    },
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.ALBUM, "mb-album-25")

        self.assertEqual(detail.country, "GB")
        self.assertEqual(detail.status, "Official")
        self.assertEqual(detail.barcode, "1234567890123")
        self.assertEqual(detail.label_names, ["XL Recordings", "Columbia"])
        self.assertEqual(detail.media_format, "Digital Media")
        self.assertEqual(detail.track_count, 2)
        self.assertEqual(detail.disc_count, 1)
        self.assertEqual(detail.secondary_types, ["Live"])

    def test_track_detail_related_album_points_to_release_group(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == "/ws/2/recording/mb-track-hello":
                self.assertEqual(
                    request.url.params["inc"],
                    "artist-credits+releases+release-groups",
                )
                return httpx.Response(
                    200,
                    json={
                        "id": "mb-track-hello",
                        "title": "Hello",
                        "artist-credit": [
                            {
                                "name": "Adele",
                                "artist": {"id": "mb-artist-1", "name": "Adele"},
                            }
                        ],
                        "releases": [
                            {
                                "id": "release-25-official",
                                "title": "25",
                                "date": "2015-11-20",
                                "release-group": {
                                    "id": "mb-album-25",
                                    "title": "25",
                                },
                            }
                        ],
                        "length": 295000,
                        "disambiguation": "album version",
                    },
                )
            if request.url.path == "/ws/2/release/release-25-official":
                return httpx.Response(
                    200,
                    json={
                        "id": "release-25-official",
                        "media": [],
                    },
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.TRACK, "mb-track-hello")

        self.assertEqual(
            calls,
            ["/ws/2/recording/mb-track-hello", "/ws/2/release/release-25-official"],
        )
        self.assertEqual(detail.disambiguation, "album version")
        self.assertIsNotNone(detail.related_album)
        self.assertEqual(detail.related_album.id, "mb-album-25")
        self.assertEqual(detail.related_album.title, "25")

    def test_track_detail_fetches_release_when_release_group_missing(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == "/ws/2/recording/mb-track-hello":
                return httpx.Response(
                    200,
                    json={
                        "id": "mb-track-hello",
                        "title": "Hello",
                        "artist-credit": [
                            {
                                "name": "Adele",
                                "artist": {"id": "mb-artist-1", "name": "Adele"},
                            }
                        ],
                        "releases": [
                            {
                                "id": "release-25-official",
                                "title": "25",
                                "date": "2015-11-20",
                            }
                        ],
                    },
                )
            if request.url.path == "/ws/2/release/release-25-official":
                return httpx.Response(
                    200,
                    json={
                        "id": "release-25-official",
                        "title": "25",
                        "release-group": {
                            "id": "mb-album-25",
                            "title": "25",
                        },
                    },
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.TRACK, "mb-track-hello")

        self.assertEqual(
            calls,
            ["/ws/2/recording/mb-track-hello", "/ws/2/release/release-25-official"],
        )
        self.assertIsNotNone(detail.related_album)
        self.assertEqual(detail.related_album.id, "mb-album-25")

    def test_track_detail_exposes_release_context(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/ws/2/recording/mb-track-hello":
                return httpx.Response(
                    200,
                    json={
                        "id": "mb-track-hello",
                        "title": "Hello",
                        "artist-credit": [
                            {
                                "name": "Adele",
                                "artist": {"id": "mb-artist-1", "name": "Adele"},
                            }
                        ],
                        "releases": [
                            {
                                "id": "release-25-official",
                                "title": "25",
                                "date": "2015-11-20",
                                "country": "GB",
                                "status": "Official",
                                "barcode": "1234567890123",
                                "release-group": {
                                    "id": "mb-album-25",
                                    "title": "25",
                                    "secondary-types": ["Live"],
                                },
                            }
                        ],
                    },
                )
            if request.url.path == "/ws/2/release/release-25-official":
                return httpx.Response(
                    200,
                    json={
                        "id": "release-25-official",
                        "country": "GB",
                        "status": "Official",
                        "barcode": "1234567890123",
                        "label-info": [{"label": {"name": "XL Recordings"}}],
                        "media": [
                            {
                                "position": 1,
                                "format": "Digital Media",
                                "tracks": [
                                    {
                                        "id": "release-track-1",
                                        "title": "Hello",
                                        "number": "1",
                                        "position": 1,
                                        "recording": {"id": "mb-track-hello", "title": "Hello"},
                                    }
                                ],
                            }
                        ],
                    },
                )
            raise AssertionError(f"Unexpected path: {request.url.path}")

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.TRACK, "mb-track-hello")

        self.assertEqual(detail.country, "GB")
        self.assertEqual(detail.status, "Official")
        self.assertEqual(detail.barcode, "1234567890123")
        self.assertEqual(detail.label_names, ["XL Recordings"])
        self.assertEqual(detail.media_format, "Digital Media")
        self.assertEqual(detail.track_count, 1)
        self.assertEqual(detail.disc_count, 1)
        self.assertEqual(detail.secondary_types, ["Live"])


if __name__ == "__main__":
    unittest.main()
