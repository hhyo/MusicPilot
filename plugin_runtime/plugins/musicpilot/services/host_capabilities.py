"""Application service for host capability probes."""

from __future__ import annotations

from ..adapters.host_probe import HostProbeAdapter
from ..schemas.probe import (
    ProbeConfigRequest,
    ProbeDispatchRequest,
    ProbeNotifyRequest,
    ProbeSearchRequest,
)


class HostCapabilitiesService:
    def __init__(self, adapter: HostProbeAdapter) -> None:
        self.adapter = adapter

    def probe_health(self) -> dict:
        return self.adapter.probe_health().model_dump(mode="json")

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

