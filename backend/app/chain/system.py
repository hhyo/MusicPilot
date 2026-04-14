"""System chain for settings, probe and health payloads."""

from __future__ import annotations

from . import MusicChainBase
from ..core.config import settings
from ..helper.settings import SettingsHelper
from ..helper.validation_matrix import HostValidationMatrixHelper
from ..modules.host_integration import HostIntegrationModule
from ..schemas.probe import (
    ProbeConfigRequest,
    ProbeDispatchRequest,
    ProbeNotifyRequest,
    ProbeSearchRequest,
)


class MusicSystemChain(MusicChainBase):
    def __init__(
        self,
        *,
        settings_helper: SettingsHelper,
        host_probe,
        host_integration: HostIntegrationModule,
        validation_matrix: HostValidationMatrixHelper | None = None,
    ) -> None:
        super().__init__(cache_region="music_system_chain")
        self.settings_helper = settings_helper
        self.host_probe = host_probe
        self.host_integration = host_integration
        self.validation_matrix_helper = validation_matrix

    def provider_settings(self):
        return self.settings_helper.provider_settings()

    def update_provider_settings(self, payload):
        return self.settings_helper.update_provider_settings(payload)

    def rule_profiles(self):
        return self.settings_helper.rule_profiles()

    def update_rule_profile(self, payload):
        return self.settings_helper.update_rule_profile(payload)

    def probe_health(self) -> dict:
        payload = self.host_probe.probe_health()
        data = payload.model_dump(mode="json")
        data["runtime_state"] = self.host_integration.runtime_state().model_dump(mode="json")
        if self.validation_matrix_helper is not None:
            summary = self.validation_matrix_helper.summary()
            data["validation_matrix_summary"] = summary.model_dump(mode="json") if summary else None
        return data

    def validation_matrix(self) -> dict | None:
        if self.validation_matrix_helper is None:
            return None
        report = self.validation_matrix_helper.load_report()
        return report.model_dump(mode="json") if report else None

    def list_sites(self) -> dict:
        return self.host_probe.list_sites().model_dump(mode="json")

    def search_summary(self) -> dict:
        return self.host_probe.search_summary().model_dump(mode="json")

    def probe_search(self, payload: ProbeSearchRequest) -> dict:
        return self.host_probe.probe_search(payload).model_dump(mode="json")

    def list_downloaders(self) -> dict:
        return self.host_probe.list_downloaders().model_dump(mode="json")

    def probe_dispatch(self, payload: ProbeDispatchRequest) -> dict:
        return self.host_probe.probe_dispatch(payload).model_dump(mode="json")

    def probe_notify(self, payload: ProbeNotifyRequest) -> dict:
        return self.host_probe.probe_notify(payload).model_dump(mode="json")

    def config_summary(self) -> dict:
        return self.host_probe.config_summary().model_dump(mode="json")

    def probe_config(self, payload: ProbeConfigRequest) -> dict:
        return self.host_probe.probe_config(payload).model_dump(mode="json")

    def runtime_state(self) -> dict:
        return self.host_integration.runtime_state().model_dump(mode="json")

    def health_payload(self, *, version: str) -> dict:
        summary = self.validation_matrix_helper.summary() if self.validation_matrix_helper else None
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": version,
            "api_prefix": settings.api_prefix,
            "phase": "MoviePilot-aligned backend refactor",
            "host_integration": self.runtime_state(),
            "validation_matrix": summary.model_dump(mode="json") if summary else None,
        }

    def root_payload(self, *, version: str) -> dict:
        return {
            "service": settings.app_name,
            "version": version,
            "phase": "MoviePilot-aligned backend refactor",
            "status": "moviepilot-aligned-runtime",
            "host_integration": self.runtime_state(),
        }
