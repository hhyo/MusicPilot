from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.acquisition_oper import AcquisitionOper
from app.db.models import Base
from app.schemas.acquisition import QueryPreferences, SearchJobCreateRequest
from app.schemas.music_media import MusicMediaInput
from app.schemas.shared import EntityType, TriggerSource


class AcquisitionOperTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()
        self.oper = AcquisitionOper(self.session)

    def tearDown(self) -> None:
        self.session.close()

    def test_create_and_delete_job(self) -> None:
        job = self.oper.create_job(
            payload=SearchJobCreateRequest(
                input=MusicMediaInput(
                    entity_hint=EntityType.ARTIST,
                    source_kind="subscription",
                    artist_names=["Adele"],
                ),
                trigger_source=TriggerSource.SUBSCRIPTION,
                preferences=QueryPreferences(),
            ),
            music_media_input={"entity_hint": "artist", "source_kind": "subscription"},
            music_meta_base={"entity_type": "artist"},
            music_recognition_assessment={"state": "direct"},
            music_media_info={"entity_type": "artist", "provider": "musicbrainz", "provider_id": "artist-adele"},
            query_payload={"provider": "musicbrainz", "provider_id": "artist-adele"},
            note="test",
        )
        self.session.commit()

        loaded = self.oper.get_job(job.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, job.id)
        self.assertTrue(self.oper.delete_job(job.id))
        self.session.commit()
        self.assertIsNone(self.oper.get_job(job.id))


if __name__ == "__main__":
    unittest.main()
