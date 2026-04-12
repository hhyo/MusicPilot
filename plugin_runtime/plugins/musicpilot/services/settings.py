"""Service layer for provider settings persistence."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..core.config import DEFAULT_CHART_RSS_FEEDS, settings
from ..repositories.settings import SettingsRepository
from ..schemas.shared import (
    AudioProfile,
    ChartRssFeedSettings,
    ChartProviderMode,
    ProviderSettingsResponse,
    ProviderSettingsUpdatePayload,
    RuleProfile,
)
from ..schemas.orchestration import ChartRuntimeStatus

logger = logging.getLogger(__name__)


DEFAULT_RULE_PROFILES = [
    RuleProfile(
        id="default-lossless",
        name="Default Lossless",
        audio_profiles=[AudioProfile.FLAC],
        allow_live=False,
        allow_remaster=False,
        auto_download_threshold=92.0,
        manual_confirm_threshold=75.0,
    )
]


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

    def get_chart_runtime_snapshots(self) -> dict[str, ChartRuntimeStatus]:
        stored_snapshots = self.repository.get_value("chart_runtime_snapshots")
        return self._coerce_valid_chart_runtime_snapshots(stored_snapshots)

    def get_chart_runtime_snapshot(self, chart_id: str) -> ChartRuntimeStatus:
        snapshot = self.get_chart_runtime_snapshots().get(chart_id)
        if snapshot is None:
            return self._resolve_chart_runtime_status(ChartRuntimeStatus())
        return self._resolve_chart_runtime_status(snapshot)

    def update_chart_runtime_snapshot(self, chart_id: str, snapshot: ChartRuntimeStatus) -> ChartRuntimeStatus:
        snapshots = self.get_chart_runtime_snapshots()
        resolved_snapshot = self._resolve_chart_runtime_status(snapshot)
        snapshots[chart_id] = resolved_snapshot
        self.repository.set_value(
            "chart_runtime_snapshots",
            {key: value.model_dump(mode="json") for key, value in snapshots.items()},
        )
        self.session.commit()
        return resolved_snapshot

    def get_rule_profiles(self) -> list[RuleProfile]:
        stored_profiles = self.repository.get_value("rule_profiles")
        profiles = self._coerce_valid_rule_profiles(stored_profiles)
        if profiles:
            return profiles
        return [profile.model_copy(deep=True) for profile in DEFAULT_RULE_PROFILES]

    def update_rule_profile(self, payload: RuleProfile) -> RuleProfile:
        profiles = self.get_rule_profiles()
        updated = False
        next_profiles: list[RuleProfile] = []
        for profile in profiles:
            if profile.id == payload.id:
                next_profiles.append(payload)
                updated = True
            else:
                next_profiles.append(profile)
        if not updated:
            next_profiles.append(payload)
        self.repository.set_value(
            "rule_profiles",
            [profile.model_dump(mode="json") for profile in next_profiles],
        )
        self.session.commit()
        return payload

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
        configured = self._coerce_valid_chart_rss_feeds(env_feeds)
        if configured:
            return configured

        return self._coerce_valid_chart_rss_feeds(DEFAULT_CHART_RSS_FEEDS)

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

    def _coerce_valid_rule_profiles(
        self,
        profiles: list[dict[str, Any]] | list[RuleProfile] | None,
    ) -> list[RuleProfile]:
        if not isinstance(profiles, list):
            return []

        parsed: list[RuleProfile] = []
        for item in profiles:
            try:
                parsed.append(item if isinstance(item, RuleProfile) else RuleProfile.model_validate(item))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid rule profile entry %r: %s", item, exc)
        return parsed

    def _coerce_valid_chart_runtime_snapshots(
        self,
        snapshots: dict[str, dict[str, Any]] | dict[str, ChartRuntimeStatus] | None,
    ) -> dict[str, ChartRuntimeStatus]:
        if not isinstance(snapshots, dict):
            return {}

        parsed: dict[str, ChartRuntimeStatus] = {}
        for chart_id, item in snapshots.items():
            try:
                parsed[chart_id] = item if isinstance(item, ChartRuntimeStatus) else ChartRuntimeStatus.model_validate(item)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid chart runtime snapshot for %s: %s", chart_id, exc)
        return parsed

    def _resolve_chart_runtime_status(self, snapshot: ChartRuntimeStatus) -> ChartRuntimeStatus:
        last_refresh_status = snapshot.last_refresh_status or "unknown"
        last_refreshed_at = snapshot.last_refreshed_at
        stale = True
        if last_refresh_status == "success" and last_refreshed_at is not None:
            if last_refreshed_at.tzinfo is None:
                last_refreshed_at = last_refreshed_at.replace(tzinfo=timezone.utc)
            max_age_seconds = self._resolve_chart_runtime_ttl_seconds()
            age_seconds = (datetime.now(timezone.utc) - last_refreshed_at).total_seconds()
            stale = age_seconds > max_age_seconds
        return snapshot.model_copy(
            update={
                "last_refresh_status": last_refresh_status,
                "last_refreshed_at": last_refreshed_at,
                "stale": stale,
            }
        )

    def _resolve_chart_runtime_ttl_seconds(self) -> int:
        ttl_seconds = getattr(self.env_settings, "chart_cache_ttl_seconds", 900)
        try:
            ttl_value = int(ttl_seconds)
        except (TypeError, ValueError):
            return 900
        return ttl_value if ttl_value > 0 else 900
