"""Tests for real provider settings persistence and API behavior."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_settings_service
from app.main import app
from app.models import AppSettingModel, Base
from app.services.settings import SettingsService


class SettingsProvidersRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)
        self.env_settings = SimpleNamespace(
            chart_provider_mode="mock",
            chart_rss_feeds=[],
            metadata_provider_mode="seed",
        )
        self.service = SettingsService(session=self.session, env_settings=self.env_settings)
        app.dependency_overrides[get_settings_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.session.close()
        app.dependency_overrides.pop(get_settings_service, None)

    def test_put_then_get_provider_settings_round_trips_structured_values(self) -> None:
        payload = {
            "chart_provider_mode": "rss_feed",
            "chart_rss_feeds": [
                {
                    "id": "netease-hot-tracks",
                    "label": "网易云热歌榜",
                    "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
                    "category": "hot",
                    "region": "CN",
                    "enabled": True,
                }
            ],
        }

        update_response = self.client.put(
            "/api/v1/plugin/musicpilot/settings/providers",
            json=payload,
        )
        self.assertEqual(update_response.status_code, 200)

        update_body = update_response.json()
        self.assertTrue(update_body["success"])
        self.assertFalse(update_body["mock"])
        self.assertEqual(update_body["data"]["chart_provider_mode"], "rss_feed")
        self.assertEqual(update_body["data"]["chart_rss_feeds"], payload["chart_rss_feeds"])
        self.assertEqual(update_body["data"]["metadata_provider_mode"], "seed")

        get_response = self.client.get("/api/v1/plugin/musicpilot/settings/providers")
        self.assertEqual(get_response.status_code, 200)

        get_body = get_response.json()
        self.assertTrue(get_body["success"])
        self.assertFalse(get_body["mock"])
        self.assertEqual(get_body["data"]["chart_provider_mode"], "rss_feed")
        self.assertEqual(get_body["data"]["chart_rss_feeds"], payload["chart_rss_feeds"])
        self.assertEqual(get_body["data"]["metadata_provider_mode"], "seed")

    def test_put_rejects_metadata_provider_mode_and_legacy_feed_shape(self) -> None:
        invalid_mode_payload = {
            "chart_provider_mode": "bogus_mode",
            "chart_rss_feeds": [
                {
                    "id": "netease-hot-tracks",
                    "label": "网易云热歌榜",
                    "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
                    "category": "hot",
                    "region": "CN",
                    "enabled": True,
                }
            ],
        }
        invalid_url_payload = {
            "chart_provider_mode": "rss_feed",
            "chart_rss_feeds": [
                {
                    "id": "netease-hot-tracks",
                    "label": "网易云热歌榜",
                    "url": "not-a-url",
                    "category": "hot",
                    "region": "CN",
                    "enabled": True,
                }
            ],
        }

        mode_response = self.client.put("/api/v1/plugin/musicpilot/settings/providers", json=invalid_mode_payload)
        url_response = self.client.put("/api/v1/plugin/musicpilot/settings/providers", json=invalid_url_payload)

        self.assertEqual(mode_response.status_code, 422)
        self.assertEqual(url_response.status_code, 422)

    def test_get_provider_settings_handles_dirty_history_without_500(self) -> None:
        self.session.add(AppSettingModel(key="chart_provider_mode", value_json="bogus_mode"))
        self.session.add(
            AppSettingModel(
                key="chart_rss_feeds",
                value_json=[
                    {
                        "name": "Legacy Track",
                        "url": "not-a-url",
                        "chart_type": "track",
                    }
                ],
            )
        )
        self.session.commit()

        response = self.client.get("/api/v1/plugin/musicpilot/settings/providers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["chart_provider_mode"], "mock")
        self.assertEqual(
            [feed["id"] for feed in response.json()["data"]["chart_rss_feeds"]],
            [
                "netease-hot-tracks",
                "netease-new-tracks",
                "netease-original-tracks",
                "youtube-top-songs",
                "youtube-top-artists",
            ],
        )

    def test_get_provider_settings_returns_builtin_default_rss_feeds_for_fresh_install(self) -> None:
        response = self.client.get("/api/v1/plugin/musicpilot/settings/providers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["chart_provider_mode"], "mock")
        self.assertEqual(
            [feed["id"] for feed in response.json()["data"]["chart_rss_feeds"]],
            [
                "netease-hot-tracks",
                "netease-new-tracks",
                "netease-original-tracks",
                "youtube-top-songs",
                "youtube-top-artists",
            ],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
