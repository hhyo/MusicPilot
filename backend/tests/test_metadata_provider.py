"""Tests for metadata provider adapters and live provider integration."""

from __future__ import annotations

import unittest

import httpx
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base
from app.schemas.metadata import MetadataDetail, MetadataSearchData, MetadataSearchRequest, MetadataSummary
from app.schemas.mvp import EntityType, ReleaseType
from app.services.metadata import MetadataService


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


class MetadataServiceLookupDetailTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)

    def tearDown(self) -> None:
        self.session.close()

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
        service = MetadataService(session=self.session, adapter=adapter)

        detail = service.lookup_detail(
            EntityType.TRACK,
            {"artist_name": "Adele", "title": "Hello", "album_title": "25"},
        )

        self.assertEqual(adapter.last_keyword, "Adele Hello 25")
        self.assertEqual(detail.id, "track-1")

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
        service = MetadataService(session=self.session, adapter=adapter)

        service.lookup_detail(EntityType.ALBUM, {"artist_name": "Adele", "album_title": "25"})
        service.lookup_detail(EntityType.ARTIST, {"artist_name": "Adele"})

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

        service = MetadataService(session=self.session, adapter=EmptyLiveAdapter())

        with self.assertRaises(HTTPException) as ctx_missing:
            service.lookup_detail(EntityType.TRACK, {})
        self.assertEqual(ctx_missing.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx_not_found:
            service.lookup_detail(EntityType.ARTIST, {"artist_name": "NotFound Artist"})
        self.assertEqual(ctx_not_found.exception.status_code, 404)


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
