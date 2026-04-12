"""Tests for provider settings persistence service."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from pydantic import ValidationError

from app.adapters.chart_provider import RssFeedChartProviderAdapter
from app.core.dependencies import get_chart_provider_adapter
from app.models import AppSettingModel, Base
from app.schemas.shared import (
    ChartRssFeedSettings,
    ChartProviderMode,
    ProviderSettingsUpdatePayload,
)
from app.services.settings import SettingsService


class SettingsServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        self.session = Session(engine)

    def tearDown(self) -> None:
        self.session.close()

    def test_update_payload_rejects_metadata_provider_mode_and_legacy_feed_shape(self) -> None:
        with self.assertRaises(ValidationError):
            ProviderSettingsUpdatePayload.model_validate(
                {
                    "chart_provider_mode": "bogus_mode",
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
                    "metadata_provider_mode": "musicbrainz",
                }
            )

    def test_get_provider_settings_falls_back_to_env_settings_when_store_empty(self) -> None:
        service = SettingsService(
            session=self.session,
            env_settings=SimpleNamespace(
                chart_provider_mode="rss_feed",
                chart_rss_feeds=[
                    {
                        "id": "netease-hot-tracks",
                        "label": "网易云热歌榜",
                        "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
                        "category": "hot",
                        "region": "CN",
                        "enabled": True,
                    }
                ],
                metadata_provider_mode="seed",
            ),
        )

        result = service.get_provider_settings()

        self.assertEqual(result.chart_provider_mode, ChartProviderMode.RSS_FEED)
        self.assertEqual(result.chart_rss_feeds[0].id, "netease-hot-tracks")
        self.assertEqual(result.chart_rss_feeds[0].label, "网易云热歌榜")
        self.assertEqual(result.metadata_provider_mode, "seed")

    def test_get_provider_settings_falls_back_to_builtin_default_feeds_when_store_and_env_empty(self) -> None:
        service = SettingsService(
            session=self.session,
            env_settings=SimpleNamespace(
                chart_provider_mode="mock",
                chart_rss_feeds=[],
                metadata_provider_mode="seed",
            ),
        )

        result = service.get_provider_settings()

        self.assertEqual(result.chart_provider_mode, ChartProviderMode.MOCK)
        self.assertEqual(
            [feed.id for feed in result.chart_rss_feeds],
            [
                "netease-hot-tracks",
                "netease-new-tracks",
                "netease-original-tracks",
                "youtube-top-songs",
                "youtube-top-artists",
            ],
        )
        self.assertEqual(result.chart_rss_feeds[0].label, "网易云热歌榜")
        self.assertEqual(result.chart_rss_feeds[-1].label, "YouTube 热门歌手榜")

    def test_get_provider_settings_falls_back_to_env_mode_for_invalid_persisted_mode(self) -> None:
        self.session.add(
            AppSettingModel(key="chart_provider_mode", value_json="bogus_mode")
        )
        self.session.commit()

        service = SettingsService(
            session=self.session,
            env_settings=SimpleNamespace(
                chart_provider_mode="listenbrainz",
                chart_rss_feeds=[],
                metadata_provider_mode="seed",
            ),
        )

        result = service.get_provider_settings()

        self.assertEqual(result.chart_provider_mode, ChartProviderMode.LISTENBRAINZ)

    def test_get_provider_settings_skips_invalid_persisted_feeds_and_falls_back_when_all_invalid(self) -> None:
        self.session.add(
            AppSettingModel(
                key="chart_rss_feeds",
                value_json=[
                    {
                        "name": "Legacy Track",
                        "url": "not-a-url",
                        "chart_type": "track",
                    },
                    {
                        "id": "netease-hot-tracks",
                        "label": "网易云热歌榜",
                        "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
                        "category": "hot",
                        "region": "CN",
                        "enabled": True,
                    },
                ],
            )
        )
        self.session.commit()

        service = SettingsService(
            session=self.session,
            env_settings=SimpleNamespace(
                chart_provider_mode="rss_feed",
                chart_rss_feeds=[
                    {
                        "id": "youtube-top-artists",
                        "label": "YouTube 热门艺人",
                        "url": "https://rsshub.rssforever.com/youtube/charts/TopArtists",
                        "category": "hot",
                        "region": "Global",
                        "enabled": True,
                    }
                ],
                metadata_provider_mode="seed",
            ),
        )

        result = service.get_provider_settings()

        self.assertEqual([feed.id for feed in result.chart_rss_feeds], ["netease-hot-tracks"])
        self.assertEqual(result.chart_rss_feeds[0].label, "网易云热歌榜")

        self.session.query(AppSettingModel).filter_by(key="chart_rss_feeds").delete()
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

        fallback_result = service.get_provider_settings()

        self.assertEqual([feed.id for feed in fallback_result.chart_rss_feeds], ["youtube-top-artists"])

    def test_update_provider_settings_persists_chart_fields_in_app_settings_table(self) -> None:
        service = SettingsService(
            session=self.session,
            env_settings=SimpleNamespace(
                chart_provider_mode="mock",
                chart_rss_feeds=[],
                metadata_provider_mode="seed",
            ),
        )
        payload = ProviderSettingsUpdatePayload(
            chart_provider_mode="rss_feed",
            chart_rss_feeds=[
                ChartRssFeedSettings(
                    id="netease-hot-tracks",
                    label="网易云热歌榜",
                    url="https://rsshub.rssforever.com/163/music/playlist/3778678",
                    category="hot",
                    region="CN",
                    enabled=True,
                )
            ],
        )

        result = service.update_provider_settings(payload)

        self.assertEqual(result.chart_provider_mode, ChartProviderMode.RSS_FEED)
        self.assertEqual(result.chart_rss_feeds[0].id, "netease-hot-tracks")
        self.assertEqual(self.session.get(AppSettingModel, "chart_provider_mode").value_json, "rss_feed")
        self.assertEqual(
            self.session.get(AppSettingModel, "chart_rss_feeds").value_json,
            [payload.chart_rss_feeds[0].model_dump(mode="json")],
        )
        self.assertEqual(service.get_provider_settings().metadata_provider_mode, "seed")

    def test_chart_provider_adapter_prefers_persisted_project_settings_over_env(self) -> None:
        service = SettingsService(
            session=self.session,
            env_settings=SimpleNamespace(
                chart_provider_mode="mock",
                chart_rss_feeds=[],
                metadata_provider_mode="seed",
            ),
        )
        service.update_provider_settings(
            ProviderSettingsUpdatePayload(
                chart_provider_mode="rss_feed",
                chart_rss_feeds=[
                    ChartRssFeedSettings(
                        id="netease-hot-tracks",
                        label="网易云热歌榜",
                        url="https://rsshub.rssforever.com/163/music/playlist/3778678",
                        category="hot",
                        region="CN",
                        enabled=True,
                    )
                ],
            )
        )

        adapter = get_chart_provider_adapter(session=self.session, settings_service=service)
        same_adapter = get_chart_provider_adapter(session=self.session, settings_service=service)

        service.update_provider_settings(
            ProviderSettingsUpdatePayload(
                chart_provider_mode="listenbrainz",
                chart_rss_feeds=[],
            )
        )
        updated_adapter = get_chart_provider_adapter(session=self.session, settings_service=service)

        self.assertIsInstance(adapter, RssFeedChartProviderAdapter)
        self.assertEqual(adapter.feeds[0]["id"], "netease-hot-tracks")
        self.assertEqual(adapter.feeds[0]["label"], "网易云热歌榜")
        self.assertIs(adapter, same_adapter)
        self.assertIsNot(adapter, updated_adapter)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
