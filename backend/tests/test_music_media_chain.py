from __future__ import annotations

import unittest

from app.schemas.metadata import MetadataDetail
from app.schemas.mvp import EntityType


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
        from app.schemas.music_media import MusicMediaInfo

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

        self.assertEqual(info.provider_id, "recording-1")
        self.assertEqual(info.match_strategy, "strong_ref")

    def test_resolve_detail_request_wraps_music_media_input(self) -> None:
        from app.schemas.music_media import MusicResolveDetailRequest

        request = MusicResolveDetailRequest(
            input={
                "entity_hint": "artist",
                "source_kind": "detail",
                "artist_names": ["Adele"],
            }
        )

        self.assertEqual(request.input.source_kind, "detail")


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


class FakeMetadataAdapter:
    provider = "musicbrainz"
    source_type = "musicbrainz"
    supports_live_queries = True

    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
        return FakeMetadataService().get_detail(entity_type, entity_id)

    def search(self, payload: object) -> None:
        raise AssertionError("search should not run in strong-ref test")


class MusicMediaChainTests(unittest.TestCase):
    def test_chain_resolves_strong_ref_track_without_search(self) -> None:
        from app.schemas.music_media import MusicMediaInput
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
        self.assertEqual(resolved.match_strategy, "strong_ref")

    def test_chain_resolve_detail_hydrates_metadata_detail(self) -> None:
        from app.schemas.music_media import MusicMediaInput
        from app.services.music_media_chain import MusicMediaChain

        chain = MusicMediaChain(
            metadata_service=FakeMetadataService(),
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


if __name__ == "__main__":
    unittest.main()
