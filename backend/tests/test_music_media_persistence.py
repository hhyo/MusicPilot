from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models.base import Base
from app.db.acquisition_oper import AcquisitionOper
from app.db.orchestration_oper import OrchestrationOper
from app.schemas.acquisition import QueryPreferences, SearchJobCreateRequest
from app.schemas.music_media import MusicMediaInfo, MusicMediaInput, MusicMetaBase, MusicRecognitionAssessment
from app.schemas.shared import EntityType, TriggerSource
from app.schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeConflictPolicy,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)


class MusicMediaPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        self.acquisition_repository = AcquisitionOper(self.session)
        self.orchestration_repository = OrchestrationOper(self.session)

    def tearDown(self) -> None:
        self.session.close()

    def test_search_job_persists_recognition_assessment_in_explicit_field(self) -> None:
        job = self.acquisition_repository.create_job(
            payload=SearchJobCreateRequest(
                input=MusicMediaInput(
                    entity_hint=EntityType.ARTIST,
                    source_kind="subscription",
                    artist_names=["Adele"],
                ),
                trigger_source=TriggerSource.SUBSCRIPTION,
                preferences=QueryPreferences(),
            ),
            music_media_input={"entity_hint": "artist", "source_kind": "subscription", "artist_names": ["Adele"]},
            music_meta_base={"entity_type": "artist", "canonical_artist_names": ["Adele"]},
            music_recognition_assessment={"state": "direct"},
            music_media_info={"entity_type": "artist", "provider": "musicbrainz", "provider_id": "artist-adele"},
            query_payload={"provider": "musicbrainz", "provider_id": "artist-adele"},
            note="test",
        )

        self.assertEqual(job.music_recognition_assessment["state"], "direct")
        self.assertNotIn("music_recognition_assessment", job.summary_json)

    def test_subscription_persists_chain_snapshots_outside_target_payload(self) -> None:
        subscription = self.orchestration_repository.create_subscription(
            subscription_type="artist",
            target_id="artist-adele",
            target_name="Adele",
            target_entity_type="artist",
            chart_source=None,
            chart_name=None,
            mode="manual",
            preference_json={},
            target_payload_json={"source": "manual-detail"},
            music_media_input={"entity_hint": "artist", "source_kind": "subscription"},
            music_meta_base={"entity_type": "artist", "canonical_artist_names": ["Adele"]},
            music_recognition_assessment={"state": "direct"},
            music_media_info={"entity_type": "artist", "provider": "musicbrainz", "provider_id": "artist-adele"},
            note="test",
        )

        self.assertEqual(subscription.target_payload_json, {"source": "manual-detail"})
        self.assertEqual(subscription.music_media_input["entity_hint"], "artist")
        self.assertEqual(subscription.music_recognition_assessment["state"], "direct")

    def test_organize_record_persists_media_snapshot_outside_raw_payload(self) -> None:
        result = OrganizeAdapterResult(
            organizeable=True,
            strategy="music_default_layout",
            strategy_snapshot=OrganizeStrategySnapshot(
                strategy_name="music_default_layout",
                library_type="music",
                root_path="/library/music",
                artist_dir_template="{artist_name}",
                album_dir_template="{artist_name}/{year} - {album_title}",
                track_file_template="{track_title}.{format_ext}",
                conflict_policy=OrganizeConflictPolicy.SKIP_EXISTING,
                template_note="test",
            ),
            organize_status=OrganizeStatus.PREVIEW_READY,
            target_library_path="/library/music",
            target_relative_path="Adele/25/01 - Hello.flac",
            strategy_note="test",
            integration_point="test",
            note="test",
        )
        media_info = MusicMediaInfo(
            entity_type=EntityType.TRACK,
            provider="musicbrainz",
            provider_id="recording-hello",
            title="Hello",
            artist_names=["Adele"],
            album_title="25",
            match_strategy="strong_ref",
        )

        record = self.orchestration_repository.create_organize_record(
            subscription_run_id=None,
            search_job_id="job-1",
            candidate_id="cand-1",
            binding_id="bind-1",
            result=result,
            music_media_info=media_info.model_dump(mode="json"),
        )

        self.assertEqual(record.music_media_info["provider_id"], "recording-hello")
        self.assertNotIn("music_media_info", record.raw_payload)


if __name__ == "__main__":
    unittest.main()
