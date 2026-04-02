"""Host probe adapter boundary definitions for future MoviePilot integration."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas.probe import (
    ProbeConfigPayload,
    ProbeConfigRequest,
    ProbeDispatchPayload,
    ProbeDispatchRequest,
    ProbeDownloadersPayload,
    ProbeHealthPayload,
    ProbeNotifyPayload,
    ProbeNotifyRequest,
    ProbeSearchPayload,
    ProbeSearchRequest,
    ProbeSitesPayload,
)


class HostProbeAdapter(ABC):
    """Boundary for host capability probing.

    Phase 1 only provides a mock implementation. Real MoviePilot integration must
    replace this adapter without changing probe route contracts.
    """

    @abstractmethod
    def probe_health(self) -> ProbeHealthPayload:
        raise NotImplementedError

    @abstractmethod
    def list_sites(self) -> ProbeSitesPayload:
        raise NotImplementedError

    @abstractmethod
    def probe_search(self, payload: ProbeSearchRequest) -> ProbeSearchPayload:
        raise NotImplementedError

    @abstractmethod
    def list_downloaders(self) -> ProbeDownloadersPayload:
        raise NotImplementedError

    @abstractmethod
    def probe_dispatch(self, payload: ProbeDispatchRequest) -> ProbeDispatchPayload:
        raise NotImplementedError

    @abstractmethod
    def probe_notify(self, payload: ProbeNotifyRequest) -> ProbeNotifyPayload:
        raise NotImplementedError

    @abstractmethod
    def probe_config(self, payload: ProbeConfigRequest) -> ProbeConfigPayload:
        raise NotImplementedError

    @abstractmethod
    def config_summary(self) -> ProbeConfigPayload:
        raise NotImplementedError

    @abstractmethod
    def search_summary(self) -> ProbeSearchPayload:
        raise NotImplementedError


class MockHostProbeAdapter(HostProbeAdapter):
    """Phase 1 mock adapter.

    This class does not connect to a real host. It only exposes the shape that a
    real adapter must later satisfy.
    """

    def _summary(self, capability: str, integration_point: str, note: str):
        return {
            "capability": capability,
            "status": "mock",
            "host_online": None,
            "capability_available": None,
            "adapter_mode": "mock",
            "integration_point": integration_point,
            "note": note,
            "todo": [
                "Replace MockHostProbeAdapter with a real MoviePilot adapter.",
                "Record real request/response samples during host integration.",
            ],
        }

    def probe_health(self) -> ProbeHealthPayload:
        return ProbeHealthPayload(
            summary=self._summary(
                "health",
                "HostProbeAdapter.probe_health",
                "Phase 1 mock skeleton only. No real host liveness check has been executed.",
            ),
            checks={
                "host_online": None,
                "plugin_api_registered": None,
                "note": "Use this contract to verify real host registration in later phases.",
            },
        )

    def list_sites(self) -> ProbeSitesPayload:
        return ProbeSitesPayload(
            summary=self._summary(
                "sites",
                "HostProbeAdapter.list_sites",
                "Mock site list demonstrates the expected data shape only.",
            ),
            items=[
                {
                    "id": "site-mock-001",
                    "name": "Mock PT Site",
                    "enabled": True,
                    "visibility": "placeholder",
                    "note": "Placeholder row only; not loaded from MoviePilot host settings.",
                }
            ],
        )

    def search_summary(self) -> ProbeSearchPayload:
        payload = ProbeSearchRequest()
        return ProbeSearchPayload(
            summary=self._summary(
                "search",
                "HostProbeAdapter.probe_search",
                "Search capability is represented by a mock boundary, not a real PT call.",
            ),
            query_echo=payload.model_dump(mode="json"),
            sample_result_fields=["site_id", "raw_title", "size_bytes", "seeders"],
            sample_result_count=0,
        )

    def probe_search(self, payload: ProbeSearchRequest) -> ProbeSearchPayload:
        return ProbeSearchPayload(
            summary=self._summary(
                "search",
                "HostProbeAdapter.probe_search",
                "The probe accepts payloads and echoes them back, but does not call a real host search chain.",
            ),
            query_echo=payload.model_dump(mode="json"),
            sample_result_fields=["site_id", "raw_title", "size_bytes", "seeders"],
            sample_result_count=0,
        )

    def list_downloaders(self) -> ProbeDownloadersPayload:
        return ProbeDownloadersPayload(
            summary=self._summary(
                "downloaders",
                "HostProbeAdapter.list_downloaders",
                "Mock downloader list only shows the expected contract for later host integration.",
            ),
            items=[
                {
                    "id": "mock-downloader",
                    "name": "Mock Downloader",
                    "is_default": True,
                    "status": "placeholder",
                    "note": "Placeholder row only; no real downloader connection exists.",
                }
            ],
        )

    def probe_dispatch(self, payload: ProbeDispatchRequest) -> ProbeDispatchPayload:
        return ProbeDispatchPayload(
            summary=self._summary(
                "dispatch",
                "HostProbeAdapter.probe_dispatch",
                "Dispatch probe is dry-run only in Phase 1 and does not create real download tasks.",
            ),
            request_echo=payload.model_dump(mode="json"),
            dispatch_preview={
                "accepted": False,
                "downloader_task_id": None,
                "mode": "mock-dry-run",
            },
        )

    def probe_notify(self, payload: ProbeNotifyRequest) -> ProbeNotifyPayload:
        return ProbeNotifyPayload(
            summary=self._summary(
                "notify",
                "HostProbeAdapter.probe_notify",
                "Notify probe only previews a message and does not send a real host notification.",
            ),
            request_echo=payload.model_dump(mode="json"),
            notification_preview={
                "title": payload.title,
                "body": payload.body,
                "channel": payload.channel,
                "sent": False,
            },
        )

    def config_summary(self) -> ProbeConfigPayload:
        payload = ProbeConfigRequest()
        return ProbeConfigPayload(
            summary=self._summary(
                "config",
                "HostProbeAdapter.probe_config",
                "Config probe boundary is present, but no real host config storage is connected.",
            ),
            operation="summary",
            request_echo=payload.model_dump(mode="json"),
            config_preview={
                "supported_operations": ["read", "write"],
                "storage_connected": False,
            },
        )

    def probe_config(self, payload: ProbeConfigRequest) -> ProbeConfigPayload:
        return ProbeConfigPayload(
            summary=self._summary(
                "config",
                "HostProbeAdapter.probe_config",
                "Config probe echoes the intended operation only. No real config persistence happens in Phase 1.",
            ),
            operation=payload.operation,
            request_echo=payload.model_dump(mode="json"),
            config_preview={
                "key": payload.key,
                "value": payload.value,
                "persisted": False,
            },
        )

