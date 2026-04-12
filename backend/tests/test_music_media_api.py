from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.dependencies import get_music_media_chain
from app.main import app
from app.schemas.metadata import MetadataDetail
from app.schemas.music_media import (
    MusicMediaInfo,
    MusicMetaBase,
    MusicRecognitionAssessment,
    MusicResolveDetailResponse,
    MusicResolveResponse,
)
from app.schemas.mvp import EntityType


class FakeMusicMediaChain:
    def build_base(self, payload):
        return MusicMetaBase(
            entity_type=payload.entity_hint or EntityType.TRACK,
            canonical_title=payload.title,
            canonical_artist_names=list(payload.artist_names),
            canonical_album_title=payload.album_title,
            canonical_album_artist_names=[],
            evidence=[],
        )

    def resolve(self, payload):
        return MusicMediaInfo(
            entity_type=payload.entity_hint or EntityType.TRACK,
            provider="musicbrainz",
            provider_id="recording-hello",
            title="Hello",
            artist_names=["Adele"],
            match_strategy="strong_ref",
            match_confidence=1.0,
        )

    def resolve_response(self, payload):
        return MusicResolveResponse(
            base=self.build_base(payload),
            assessment=MusicRecognitionAssessment(state="direct"),
            media=self.resolve(payload),
        )

    def resolve_detail(self, payload):
        media = self.resolve(payload)
        base = self.build_base(payload)
        detail = MetadataDetail(
            entity_type=EntityType.TRACK,
            id="recording-hello",
            title="Hello",
            artist_name="Adele",
            provider="musicbrainz",
            source_type="musicbrainz",
            mock=False,
            note="detail",
            integration_point="test",
        )
        return MusicResolveDetailResponse(
            base=base,
            assessment=MusicRecognitionAssessment(state="direct"),
            media=media,
            detail=detail,
        )


class MusicMediaApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_music_media_chain] = lambda: FakeMusicMediaChain()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_music_media_chain, None)

    def test_media_resolve_detail_returns_detail_payload(self) -> None:
        response = self.client.post(
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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["base"]["canonical_title"], "Hello")
        self.assertEqual(body["data"]["media"]["provider_id"], "recording-hello")
        self.assertEqual(body["data"]["detail"]["id"], "recording-hello")

    def test_old_metadata_lookup_route_is_gone(self) -> None:
        response = self.client.post(
            "/api/v1/plugin/musicpilot/metadata/lookup",
            json={"entity_type": "track", "hints": {"title": "Hello"}},
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
