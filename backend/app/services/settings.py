"""Service layer for provider settings persistence."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from ..core.config import settings
from ..repositories.settings import SettingsRepository
from ..schemas.mvp import (
    ChartRssFeedSettings,
    ChartProviderMode,
    ProviderSettingsResponse,
    ProviderSettingsUpdatePayload,
)

logger = logging.getLogger(__name__)


class SettingsService:
    def __init__(self, session: Session, env_settings: Any = settings):
        self.session = session
        self.env_settings = env_settings
        self.repository = SettingsRepository(session)

    def get_provider_settings(self) -> ProviderSettingsResponse:
        chart_provider_mode = self.repository.get_value("chart_provider_mode")
        chart_provider_mode = self._resolve_chart_provider_mode(chart_provider_mode)

        chart_rss_feeds = self.repository.get_value("chart_rss_feeds")
        chart_rss_feeds = self._resolve_chart_rss_feeds(chart_rss_feeds)

        return ProviderSettingsResponse(
            chart_provider_mode=chart_provider_mode,
            chart_rss_feeds=chart_rss_feeds,
            metadata_provider_mode=getattr(self.env_settings, "metadata_provider_mode", None),
        )

    def update_provider_settings(
        self, payload: ProviderSettingsUpdatePayload
    ) -> ProviderSettingsResponse:
        self.repository.set_value("chart_provider_mode", payload.chart_provider_mode.value)
        self.repository.set_value(
            "chart_rss_feeds",
            [feed.model_dump(mode="json") for feed in payload.chart_rss_feeds],
        )
        self.session.commit()
        return self.get_provider_settings()

    def _resolve_chart_provider_mode(self, stored_value: Any) -> ChartProviderMode:
        fallback_value = getattr(self.env_settings, "chart_provider_mode", "mock")
        try:
            return ChartProviderMode(stored_value) if stored_value is not None else ChartProviderMode(fallback_value)
        except ValueError:
            logger.warning("Invalid stored chart_provider_mode %r, falling back to env value %r.", stored_value, fallback_value)
            try:
                return ChartProviderMode(fallback_value)
            except ValueError:
                logger.warning("Invalid env chart_provider_mode %r, falling back to mock.", fallback_value)
                return ChartProviderMode.MOCK

    def _resolve_chart_rss_feeds(
        self,
        stored_feeds: list[dict[str, Any]] | list[ChartRssFeedSettings] | None,
    ) -> list[ChartRssFeedSettings]:
        persisted = self._coerce_valid_chart_rss_feeds(stored_feeds)
        if persisted:
            return persisted

        env_feeds = getattr(self.env_settings, "chart_rss_feeds", [])
        return self._coerce_valid_chart_rss_feeds(env_feeds)

    def _coerce_valid_chart_rss_feeds(
        self,
        feeds: list[dict[str, Any]] | list[ChartRssFeedSettings] | None,
    ) -> list[ChartRssFeedSettings]:
        if not isinstance(feeds, list):
            logger.warning("Ignoring non-list chart_rss_feeds value from settings store: %r", feeds)
            return []

        parsed: list[ChartRssFeedSettings] = []
        for item in feeds:
            try:
                parsed.append(item if isinstance(item, ChartRssFeedSettings) else ChartRssFeedSettings.model_validate(item))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid chart RSS feed entry %r: %s", item, exc)
        return parsed
