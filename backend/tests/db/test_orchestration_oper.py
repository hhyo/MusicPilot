from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.orchestration_oper import OrchestrationOper
from app.schemas.orchestration import (
    OrganizeAdapterResult,
    OrganizeConflictPolicy,
    OrganizeStatus,
    OrganizeStrategySnapshot,
)


class OrchestrationOperTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        self.oper = OrchestrationOper(self.session)

    def tearDown(self) -> None:
        self.session.close()

    def test_create_subscription_and_organize_record(self) -> None:
        subscription = self.oper.create_subscription(
            subscription_type="artist",
            target_id="artist-adele",
            target_name="Adele",
            target_entity_type="artist",
            chart_source=None,
            chart_name=None,
            mode="manual",
            preference_json={},
            target_payload_json={"source": "manual"},
            music_media_input={"entity_hint": "artist"},
            music_meta_base={"entity_type": "artist"},
            music_recognition_assessment={"state": "direct"},
            music_media_info={"entity_type": "artist", "provider": "musicbrainz", "provider_id": "artist-adele"},
            note="test",
        )
        run = self.oper.create_run(subscription, note="run")
        record = self.oper.create_organize_record(
            subscription_run_id=run.id,
            search_job_id=None,
            candidate_id=None,
            binding_id=None,
            result=OrganizeAdapterResult(
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
            ),
        )
        self.session.commit()

        loaded = self.oper.get_subscription(subscription.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, subscription.id)
        self.assertEqual(self.oper.get_run(run.id).id, run.id)
        self.assertEqual(self.oper.get_organize_record(record.id).id, record.id)


if __name__ == "__main__":
    unittest.main()
