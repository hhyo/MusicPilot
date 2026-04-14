from __future__ import annotations

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base


def build_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class FakeMediaServerRuntime:
    def __init__(self, *, response=None):
        self.response = response or {
            "success": True,
            "sync_status": "synced",
            "message": "",
            "libraries_synced": None,
        }
        self.calls: list[dict] = []

    def sync(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        return self.response


class MusicMediaServerChainTest(unittest.TestCase):
    def setUp(self) -> None:
        from app.chain.mediaserver import MusicMediaServerChain

        engine = build_engine()
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.runtime = FakeMediaServerRuntime()
        self.chain = MusicMediaServerChain(
            session=self.session,
            runtime=self.runtime,
        )

    def tearDown(self) -> None:
        self.session.close()

    def test_sync_records_runtime_state(self) -> None:
        from app.db.settings_oper import SettingsOper

        result = self.chain.sync()

        self.assertTrue(result["success"])
        self.assertEqual(result["sync_status"], "synced")
        self.assertEqual(len(self.runtime.calls), 1)
        stored = SettingsOper(self.session).get_value("mediaserver_sync_runtime")
        self.assertEqual(stored["sync_status"], "synced")
        self.assertTrue(stored["success"])
