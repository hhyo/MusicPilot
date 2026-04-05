"""Tests for metadata provider adapters and live provider integration."""

from __future__ import annotations

import unittest

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base
from app.schemas.metadata import MetadataDetail, MetadataSearchData, MetadataSearchRequest
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


class MusicBrainzMetadataProviderAdapterTest(unittest.TestCase):
    def test_artist_search_maps_musicbrainz_result(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/ws/2/artist")
            self.assertEqual(request.url.params["fmt"], "json")
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

    def test_album_detail_maps_release_group_result(self) -> None:
        from app.adapters.metadata_provider import MusicBrainzMetadataProviderAdapter

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/ws/2/release-group/mb-album-25")
            self.assertEqual(request.url.params["fmt"], "json")
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
                "releases": [
                    {
                        "id": "release-25-1",
                        "title": "25",
                    }
                ],
            }
            return httpx.Response(200, json=body)

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://musicbrainz.test/ws/2",
        )
        adapter = MusicBrainzMetadataProviderAdapter(client=client, user_agent="MusicPilot-Test/1.0")

        detail = adapter.get_detail(EntityType.ALBUM, "mb-album-25")

        self.assertEqual(detail.provider, "musicbrainz")
        self.assertEqual(detail.source_type, "musicbrainz_ws2")
        self.assertEqual(detail.entity_type, EntityType.ALBUM)
        self.assertEqual(detail.album_title, "25")
        self.assertEqual(detail.artist_name, "Adele")
        self.assertEqual(detail.year, 2015)
        self.assertEqual(detail.release_type, ReleaseType.ALBUM)
        self.assertEqual(detail.external_ids["musicbrainz"], "mb-album-25")
        self.assertEqual(detail.related_artists[0].title, "Adele")


if __name__ == "__main__":
    unittest.main()
