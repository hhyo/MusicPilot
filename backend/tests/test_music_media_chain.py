from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.schemas.metadata import MetadataDetail
from app.schemas.shared import EntityType


class MusicMediaSchemaTests(unittest.TestCase):
    def test_music_media_input_accepts_discovery_track_clues(self) -> None:
        from app.schemas.music_media import MusicMediaInput

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

        self.assertEqual(payload.entity_hint, EntityType.TRACK)
        self.assertEqual(payload.artist_names, ["Lady Gaga", "Bruno Mars"])

    def test_music_meta_base_requires_entity_type_and_canonical_fields(self) -> None:
        from app.schemas.music_media import MusicMetaBase

        base = MusicMetaBase(
            entity_type=EntityType.ALBUM,
            canonical_title="25",
            canonical_artist_names=["Adele"],
            canonical_album_title="25",
            canonical_album_artist_names=["Adele"],
            evidence=[{"field": "title", "value": "25", "source": "structured"}],
        )

        self.assertEqual(base.canonical_title, "25")
        self.assertEqual(base.canonical_artist_names, ["Adele"])

    def test_music_media_info_tracks_match_diagnostics(self) -> None:
        from app.schemas.music_media import MusicMediaInfo, MusicMediaMatchStrategy

        info = MusicMediaInfo(
            entity_type=EntityType.TRACK,
            provider="musicbrainz",
            provider_id="recording-1",
            title="Hello",
            artist_names=["Adele"],
            match_confidence=0.98,
            match_strategy=MusicMediaMatchStrategy.STRONG_REF,
            match_evidence=[{"field": "recording_id", "value": "recording-1"}],
            diagnostics=[],
        )

        self.assertEqual(info.provider_id, "recording-1")
        self.assertEqual(info.match_strategy, MusicMediaMatchStrategy.STRONG_REF)

    def test_resolve_detail_request_wraps_music_media_input(self) -> None:
        from app.schemas.music_media import MusicMediaSourceKind, MusicResolveDetailRequest

        request = MusicResolveDetailRequest(
            input={
                "entity_hint": "artist",
                "source_kind": "detail",
                "artist_names": ["Adele"],
            }
        )

        self.assertEqual(request.input.source_kind, MusicMediaSourceKind.DETAIL)


class FakeMetadataService:
    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
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

    def get_detail_by_provider_ref(
        self,
        *,
        entity_type: EntityType,
        provider: str,
        provider_id: str,
    ) -> MetadataDetail:
        self.last_provider_ref = {
            "entity_type": entity_type,
            "provider": provider,
            "provider_id": provider_id,
        }
        return self.get_detail(entity_type, provider_id)


class FakeMetadataAdapter:
    provider = "musicbrainz"
    source_type = "musicbrainz"
    supports_live_queries = True

    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
        return FakeMetadataService().get_detail(entity_type, entity_id)

    def search(self, payload: object) -> None:
        raise AssertionError("search should not run in strong-ref test")


class FakeExternalProviderAdapter:
    provider = "external_feed"
    source_type = "external_feed"
    supports_live_queries = True

    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
        return FakeMetadataService().get_detail(entity_type, entity_id)

    def search(self, payload: object) -> None:
        raise AssertionError("search should not run in generic direct-ref test")


class MusicMediaChainTests(unittest.TestCase):
    def test_chain_resolves_strong_ref_track_without_search(self) -> None:
        from app.schemas.music_media import MusicMediaInput, MusicMediaMatchStrategy
        from app.services.music_media_chain import MusicMediaChain

        chain = MusicMediaChain(
            metadata_service=FakeMetadataService(),
            metadata_adapter=FakeMetadataAdapter(),
        )
        resolved = chain.resolve(
            MusicMediaInput(
                entity_hint=EntityType.TRACK,
                source_kind="discovery",
                title="Hello",
                artist_names=["Adele"],
                external_refs={"musicbrainz_recording_id": "recording-hello"},
            )
        )

        self.assertEqual(resolved.provider_id, "recording-hello")
        self.assertEqual(resolved.match_strategy, MusicMediaMatchStrategy.STRONG_REF)

    def test_chain_resolve_detail_hydrates_metadata_detail(self) -> None:
        from app.schemas.music_media import MusicMediaInput
        from app.services.music_media_chain import MusicMediaChain

        metadata_service = FakeMetadataService()
        chain = MusicMediaChain(
            metadata_service=metadata_service,
            metadata_adapter=FakeMetadataAdapter(),
        )
        result = chain.resolve_detail(
            MusicMediaInput(
                entity_hint=EntityType.TRACK,
                source_kind="detail",
                title="Hello",
                artist_names=["Adele"],
                external_refs={"musicbrainz_recording_id": "recording-hello"},
            )
        )

        self.assertEqual(result.detail.id, "recording-hello")
        self.assertEqual(result.media.provider_id, "recording-hello")
        self.assertEqual(metadata_service.last_provider_ref["provider"], "musicbrainz")

    def test_chain_prepare_from_provider_ref_returns_input_base_and_assessment(self) -> None:
        from app.schemas.music_media import MusicRecognitionState
        from app.services.music_media_chain import MusicMediaChain

        chain = MusicMediaChain(
            metadata_service=FakeMetadataService(),
            metadata_adapter=FakeMetadataAdapter(),
        )

        prepared = chain.prepare_from_provider_ref(
            entity_type=EntityType.ARTIST,
            provider="musicbrainz",
            provider_id="artist-adele",
            source_kind="detail",
            source_context={"entrypoint": "artist_detail_route"},
            raw_context={},
        )

        self.assertEqual(prepared.input.external_refs["musicbrainz_artist_id"], "artist-adele")
        self.assertEqual(prepared.base.entity_type, EntityType.ARTIST)
        self.assertEqual(prepared.assessment.state, MusicRecognitionState.DIRECT)

    def test_chain_resolves_generic_provider_ref_without_search(self) -> None:
        from app.schemas.music_media import MusicMediaInput
        from app.services.music_media_chain import MusicMediaChain

        metadata_service = FakeMetadataService()
        chain = MusicMediaChain(
            metadata_service=metadata_service,
            metadata_adapter=FakeExternalProviderAdapter(),
        )

        result = chain.resolve_detail(
            MusicMediaInput(
                entity_hint=EntityType.ALBUM,
                source_kind="detail",
                external_refs={
                    "provider": "external_feed",
                    "provider_id": "album-42",
                },
            )
        )

        self.assertEqual(result.media.provider, "external_feed")
        self.assertEqual(result.media.provider_id, "album-42")
        self.assertEqual(metadata_service.last_provider_ref["provider"], "external_feed")
        self.assertEqual(metadata_service.last_provider_ref["provider_id"], "album-42")

    def test_chain_resolve_detail_from_provider_ref_uses_chain_convenience_entrypoint(self) -> None:
        from app.services.music_media_chain import MusicMediaChain

        metadata_service = FakeMetadataService()
        chain = MusicMediaChain(
            metadata_service=metadata_service,
            metadata_adapter=FakeMetadataAdapter(),
        )

        result = chain.resolve_detail_from_provider_ref(
            entity_type=EntityType.TRACK,
            provider="musicbrainz",
            provider_id="recording-hello",
            source_kind="detail",
            source_context={"entrypoint": "metadata_detail_route"},
            raw_context={},
        )

        self.assertEqual(result.base.entity_type, EntityType.TRACK)
        self.assertEqual(result.detail.id, "recording-hello")
        self.assertEqual(metadata_service.last_provider_ref["provider_id"], "recording-hello")

    def test_chain_resolve_from_target_payload_ref_uses_explicit_provider_ref(self) -> None:
        from app.services.music_media_chain import MusicMediaChain

        chain = MusicMediaChain(
            metadata_service=FakeMetadataService(),
            metadata_adapter=FakeExternalProviderAdapter(),
        )

        result = chain.resolve_from_target_payload_ref(
            entity_type=EntityType.ALBUM,
            target_id="fallback-id",
            target_payload={
                "provider_ref": {
                    "provider": "external_feed",
                    "provider_id": "album-99",
                }
            },
            source_kind="subscription_resolution",
            source_context={"subscription_id": "sub-1"},
            raw_context={},
        )

        self.assertEqual(result.provider, "external_feed")
        self.assertEqual(result.provider_id, "album-99")

    def test_chain_resolve_from_target_payload_ref_uses_structured_music_clues_without_provider_assumption(self) -> None:
        from app.services.music_media_chain import MusicMediaChain

        chain = MusicMediaChain(
            metadata_service=FakeMetadataService(),
            metadata_adapter=FakeExternalProviderAdapter(),
        )

        prepared = chain.prepare_from_target_payload_ref(
            entity_type=EntityType.TRACK,
            target_id="",
            target_payload={
                "title": "Die With A Smile",
                "artist_name": "Lady Gaga",
                "album_title": "Die With A Smile",
            },
            source_kind="subscription",
            source_context={"subscription_id": "sub-2"},
            raw_context={},
        )

        self.assertEqual(prepared.input.title, "Die With A Smile")
        self.assertEqual(prepared.input.artist_names, ["Lady Gaga"])
        self.assertEqual(prepared.input.external_refs, {})

    def test_chain_prepare_from_target_payload_ref_rejects_empty_legacy_payload(self) -> None:
        from app.services.music_media_chain import MusicMediaChain

        chain = MusicMediaChain(
            metadata_service=FakeMetadataService(),
            metadata_adapter=FakeExternalProviderAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            chain.prepare_from_target_payload_ref(
                entity_type=EntityType.ALBUM,
                target_id="",
                target_payload={},
                source_kind="subscription",
                source_context={"subscription_id": "sub-3"},
                raw_context={},
            )

        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
