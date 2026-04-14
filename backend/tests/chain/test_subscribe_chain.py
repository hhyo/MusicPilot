from __future__ import annotations

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.chain.subscribe import MusicSubscribeChain
from app.db.models.base import Base
from app.schemas.orchestration import CreateSubscriptionRequest, SubscriptionType
from tests.test_subscriptions import DummyMusicMediaChain
from tests.test_subscription_execution import (
    DummyDispatchService,
    DummyMusicMediaChain as ExecutionMusicMediaChain,
    DummyOrganizeService,
    DummySearchJobService,
    build_candidate,
    build_search_job_summary,
)
from app.schemas.acquisition import DispatchResult
from app.schemas.integration import AdapterMode, VerificationState
from app.schemas.shared import DecisionStatus, JobStatus


class MusicSubscribeChainTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)
        self.session = Session()

    def tearDown(self) -> None:
        self.session.close()

    def test_create_subscription_persists_music_media_snapshots(self) -> None:
        chain = MusicSubscribeChain(
            session=self.session,
            music_media_chain=DummyMusicMediaChain(),
        )

        result = chain.create_subscription(
            CreateSubscriptionRequest(
                subscription_type=SubscriptionType.ARTIST,
                target_id="artist-adele",
                target_name="Adele",
                target_entity_type="artist",
                target_payload={"source": "manual-detail"},
            )
        )

        self.assertEqual(result.music_media_input.entity_hint, "artist")
        self.assertEqual(result.music_recognition_assessment.state, "direct")
        self.assertEqual(result.music_media_info.provider_id, "artist-adele")

    def test_execute_dispatches_auto_download_candidate(self) -> None:
        music_media_chain = DummyMusicMediaChain()
        search_job_chain = DummySearchJobService(
            executed_job=build_search_job_summary(status=JobStatus.MANUAL_PENDING),
            candidates=[
                build_candidate(candidate_id="cand-auto", decision=DecisionStatus.AUTO_DOWNLOAD, score_total=95.0),
            ],
        )
        download_chain = DummyDispatchService(
            result=DispatchResult(
                candidate_id="cand-auto",
                job_id="job-001",
                dispatchable=True,
                dispatch_status="mock_submitted",
                target_downloader="mock-downloader",
                downloader_task_id="task-001",
                note="dispatched",
                integration_point="DummyDispatchService.dispatch",
                mock=False,
                binding_id="bind-001",
                dispatch_backend=AdapterMode.MOCK,
                capability_source="test",
                verification_state=VerificationState.VERIFIED,
            )
        )
        transfer_chain = DummyOrganizeService()
        chain = MusicSubscribeChain(
            session=self.session,
            music_media_chain=music_media_chain,
            search_chain=search_job_chain,
            download_chain=download_chain,
            transfer_chain=transfer_chain,
        )
        subscription = chain.create_subscription(
            CreateSubscriptionRequest(
                subscription_type=SubscriptionType.ARTIST,
                target_id="artist-adele",
                target_name="Adele",
                target_entity_type="artist",
            )
        )

        result = chain.execute(subscription.id)

        self.assertEqual(result.execution_status.value, "dispatched")
        self.assertEqual(download_chain.calls, [("cand-auto", "mock-downloader", True)])


if __name__ == "__main__":
    unittest.main()
