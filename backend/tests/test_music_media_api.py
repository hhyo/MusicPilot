from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.dependencies import get_music_media_chain
from app.main import app
from app.schemas.metadata import MetadataDetail
from app.schemas.music_media import (
    MusicMediaInfo,
    MusicMetaBase,
    MusicPrepareResponse,
    MusicRecognitionAssessment,
    MusicResolveDetailResponse,
    MusicResolveResponse,
)
from app.schemas.shared import EntityType


class FakeMusicMediaChain:
    def __init__(self) -> None:
        self.last_input = None

    def build_base(self, payload):
        return MusicMetaBase(
            entity_type=payload.entity_hint or EntityType.TRACK,
            canonical_title=payload.title,
            canonical_artist_names=list(payload.artist_names),
            canonical_album_title=payload.album_title,
            canonical_album_artist_names=[],
            evidence=[],
        )

    def input_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ):
        from app.schemas.music_media import MusicMediaInput

        external_refs: dict[str, str] = {}
        if provider == "musicbrainz":
            if entity_type == EntityType.ARTIST:
                external_refs["musicbrainz_artist_id"] = provider_id
            elif entity_type == EntityType.ALBUM:
                external_refs["musicbrainz_release_group_id"] = provider_id
            else:
                external_refs["musicbrainz_recording_id"] = provider_id
        else:
            external_refs["provider"] = provider
            external_refs["provider_id"] = provider_id

        return MusicMediaInput(
            entity_hint=entity_type,
            source_kind=source_kind,
            external_refs=external_refs,
            source_context=source_context or {},
            raw_context=raw_context or {},
        )

    def resolve_detail_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ):
        payload = self.input_from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_detail(payload)

    def resolve_detail_from_active_provider_ref(
        self,
        *,
        entity_type,
        provider_id: str,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ):
        return self.resolve_detail_from_provider_ref(
            entity_type=entity_type,
            provider="musicbrainz",
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def input_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ):
        return self.input_from_provider_ref(
            entity_type=entity_type,
            provider="musicbrainz",
            provider_id=target_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def resolve(self, payload):
        self.last_input = payload
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
        self.last_input = payload
        return MusicResolveResponse(
            base=self.build_base(payload),
            assessment=MusicRecognitionAssessment(state="direct"),
            media=self.resolve(payload),
        )

    def prepare(self, payload):
        self.last_input = payload
        return MusicPrepareResponse(
            input=payload,
            base=self.build_base(payload),
            assessment=MusicRecognitionAssessment(state="direct"),
        )

    def resolve_detail(self, payload):
        self.last_input = payload
        media = self.resolve(payload)
        base = self.build_base(payload)
        detail = MetadataDetail(
            entity_type=payload.entity_hint or EntityType.TRACK,
            id=(payload.external_refs.get("musicbrainz_recording_id") or payload.external_refs.get("musicbrainz_release_group_id") or payload.external_refs.get("musicbrainz_artist_id") or "recording-hello"),
            title=payload.title or "Hello",
            artist_name=(payload.artist_names[0] if payload.artist_names else "Adele"),
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
        self.fake_chain = FakeMusicMediaChain()
        app.dependency_overrides[get_music_media_chain] = lambda: self.fake_chain
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

    def test_media_prepare_returns_base_and_assessment(self) -> None:
        response = self.client.post(
            "/api/v1/plugin/musicpilot/media/prepare",
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
        self.assertEqual(body["data"]["assessment"]["state"], "direct")

    def test_removed_metadata_lookup_route_returns_404(self) -> None:
        response = self.client.post(
            "/api/v1/plugin/musicpilot/metadata/lookup",
            json={"entity_type": "track", "hints": {"title": "Hello"}},
        )
        self.assertEqual(response.status_code, 404)

    def test_track_detail_route_uses_unified_music_media_chain(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/metadata/tracks/recording-hello")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["id"], "recording-hello")
        self.assertEqual(self.fake_chain.last_input.source_kind, "detail")
        self.assertEqual(self.fake_chain.last_input.external_refs["musicbrainz_recording_id"], "recording-hello")

    def test_album_detail_route_uses_unified_music_media_chain(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/metadata/albums/release-group-25")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["id"], "release-group-25")
        self.assertEqual(self.fake_chain.last_input.external_refs["musicbrainz_release_group_id"], "release-group-25")


if __name__ == "__main__":
    unittest.main()
