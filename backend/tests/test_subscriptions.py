"""Tests for subscription creation on the unified music media chain."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.schemas.metadata import MetadataDetail
from app.schemas.music_media import MusicMediaInfo, MusicMetaBase, MusicRecognitionAssessment, MusicResolveResponse
from app.schemas.orchestration import CreateSubscriptionRequest, SubscriptionType
from app.services.subscriptions import SubscriptionService
from test_query_builder import build_artist_detail, build_artist_media


class DummyMetadataService:
    def get_detail(self, entity_type, entity_id):  # noqa: ANN001, ARG002
        return build_artist_detail()


class DummyMusicMediaChain:
    def __init__(self) -> None:
        self.calls = []

    def input_from_metadata_detail(
        self,
        payload: MetadataDetail,
        *,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ):
        return SimpleNamespace(
            entity_hint=payload.entity_type,
            source_kind=source_kind,
            title=payload.track_title or payload.title,
            artist_names=[payload.artist_name] if payload.artist_name else [],
            album_title=payload.album_title,
            album_artist_names=[],
            external_refs=dict(payload.external_ids),
            source_context=source_context or {},
            raw_context=raw_context or {},
            model_dump=lambda mode="json": {
                "entity_hint": payload.entity_type.value,
                "source_kind": source_kind,
                "title": payload.track_title or payload.title,
                "artist_names": [payload.artist_name] if payload.artist_name else [],
                "album_title": payload.album_title,
                "album_artist_names": [],
                "external_refs": dict(payload.external_ids),
                "source_context": source_context or {},
                "raw_context": raw_context or {},
            },
        )

    def resolve(self, payload):
        self.calls.append(payload)
        return build_artist_media()

    def resolve_response(self, payload):
        media = self.resolve(payload)
        return MusicResolveResponse(
            base=MusicMetaBase(
                entity_type=payload.entity_hint,
                canonical_title=payload.title,
                canonical_artist_names=list(payload.artist_names),
                canonical_album_title=payload.album_title,
                canonical_album_artist_names=list(payload.album_artist_names),
                external_refs=dict(payload.external_refs),
                evidence=[],
            ),
            assessment=MusicRecognitionAssessment(state="direct"),
            media=media,
        )


class SubscriptionServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        self.music_media_chain = DummyMusicMediaChain()
        self.service = SubscriptionService(
            self.session,
            metadata_service=DummyMetadataService(),
            music_media_chain=self.music_media_chain,
        )

    def tearDown(self) -> None:
        self.session.close()

    def test_create_subscription_persists_music_media_snapshots(self) -> None:
        result = self.service.create_subscription(
            CreateSubscriptionRequest(
                subscription_type=SubscriptionType.ARTIST,
                target_id="artist-adele",
                target_name="Adele",
                target_entity_type="artist",
                target_payload={"source": "manual-detail"},
            )
        )

        self.assertEqual(result.target_payload["source"], "manual-detail")
        self.assertEqual(result.target_payload["music_media_input"]["entity_hint"], "artist")
        self.assertEqual(result.target_payload["music_meta_base"]["entity_type"], "artist")
        self.assertEqual(result.target_payload["music_recognition_assessment"]["state"], "direct")
        self.assertEqual(result.target_payload["music_media_info"]["provider_id"], "artist-adele")
        self.assertEqual(len(self.music_media_chain.calls), 1)

    def test_create_subscription_prefers_detail_title_when_target_name_missing(self) -> None:
        result = self.service.create_subscription(
            CreateSubscriptionRequest(
                subscription_type=SubscriptionType.ARTIST,
                target_id="artist-adele",
                target_entity_type="artist",
            )
        )

        self.assertEqual(result.target_name, "Adele")
        self.assertEqual(result.target_payload["music_media_info"]["title"], "Adele")


if __name__ == "__main__":
    unittest.main()
