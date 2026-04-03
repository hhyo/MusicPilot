"""Application service for host capability probes."""

from __future__ import annotations

from ..adapters.host_probe import HostProbeAdapter
from ..services.host_integration import HostIntegrationService
from ..services.validation_matrix import HostValidationMatrixService
from ..schemas.probe import (
    ProbeConfigRequest,
    ProbeDispatchRequest,
    ProbeNotifyRequest,
    ProbeSearchRequest,
)


class HostCapabilitiesService:
    def __init__(
        self,
        adapter: HostProbeAdapter,
        integration_service: HostIntegrationService,
        validation_matrix_service: HostValidationMatrixService | None = None,
    ) -> None:
        self.adapter = adapter
        self.integration_service = integration_service
        self.validation_matrix_service = validation_matrix_service

    def probe_health(self) -> dict:
        payload = self.adapter.probe_health()
        payload.runtime_state = self.integration_service.runtime_state()
        data = payload.model_dump(mode="json")
        if self.validation_matrix_service is not None:
            summary = self.validation_matrix_service.summary()
            data["validation_matrix_summary"] = summary.model_dump(mode="json") if summary else None
        return data

    def list_sites(self) -> dict:
        return self.adapter.list_sites().model_dump(mode="json")

    def search_summary(self) -> dict:
        return self.adapter.search_summary().model_dump(mode="json")

    def probe_search(self, payload: ProbeSearchRequest) -> dict:
        return self.adapter.probe_search(payload).model_dump(mode="json")

    def list_downloaders(self) -> dict:
        return self.adapter.list_downloaders().model_dump(mode="json")

    def probe_dispatch(self, payload: ProbeDispatchRequest) -> dict:
        return self.adapter.probe_dispatch(payload).model_dump(mode="json")

    def probe_notify(self, payload: ProbeNotifyRequest) -> dict:
        return self.adapter.probe_notify(payload).model_dump(mode="json")

    def config_summary(self) -> dict:
        return self.adapter.config_summary().model_dump(mode="json")

    def probe_config(self, payload: ProbeConfigRequest) -> dict:
        return self.adapter.probe_config(payload).model_dump(mode="json")

    def runtime_state(self) -> dict:
        return self.integration_service.runtime_state().model_dump(mode="json")

    def validation_matrix(self) -> dict | None:
        if self.validation_matrix_service is None:
            return None
        report = self.validation_matrix_service.load_report()
        return report.model_dump(mode="json") if report else None
