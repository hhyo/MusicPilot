"""Host probe adapter boundary definitions for future MoviePilot integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .host_http import HostHttpClient, HostTransportError
from ..core.config import Settings
from ..schemas.integration import AdapterMode, AdapterStrategy, VerificationState
from ..schemas.probe import (
    ProbeCapabilitySummary,
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
            "adapter_mode": AdapterMode.MOCK,
            "active_strategy": AdapterStrategy.MOCK,
            "host_integration_enabled": False,
            "capability_source": "mock.probe",
            "verification_state": VerificationState.PLACEHOLDER,
            "fallback_reason": None,
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
                "Config probe echoes the intended operation only. No real config persistence happens in the mock adapter.",
            ),
            operation=payload.operation,
            request_echo=payload.model_dump(mode="json"),
            config_preview={
                "key": payload.key,
                "value": payload.value,
                "persisted": False,
            },
        )


class RealHostProbeAdapter(HostProbeAdapter):
    """Host-backed probe skeleton.

    This adapter is intentionally conservative:
    - it only calls configured endpoints;
    - it never claims full host compatibility automatically;
    - when the host contract is incomplete, it returns unverified/degraded summaries instead of faking success.
    """

    def __init__(self, *, settings: Settings, client: HostHttpClient):
        self.settings = settings
        self.client = client

    def probe_health(self) -> ProbeHealthPayload:
        try:
            payload = self.client.get_json(self.settings.host_health_path)
            checks = self._extract_health_checks(payload)
            summary = self._summary(
                capability="health",
                capability_available=checks.get("host_online"),
                status=self._status_from_availability(checks.get("host_online")),
                integration_point="RealHostProbeAdapter.probe_health",
                note=(
                    "Host health summary was derived from a real MoviePilot endpoint. "
                    "In Phase 7A this defaults to `/api/v1/search/last`, because MoviePilot does not expose a dedicated "
                    "public health endpoint for this integration path."
                ),
            )
        except HostTransportError as exc:
            checks = {
                "host_online": False,
                "plugin_api_registered": None,
                "note": "Host health probe could not be completed through the configured endpoint.",
            }
            summary = self._degraded_summary(
                capability="health",
                integration_point="RealHostProbeAdapter.probe_health",
                note=str(exc),
                fallback_reason=exc.reason_code,
            )

        return ProbeHealthPayload(summary=summary, checks=checks)

    def list_sites(self) -> ProbeSitesPayload:
        try:
            payload = self.client.get_json(self.settings.host_sites_path)
            raw_items = self._extract_items(payload)
            items = [
                {
                    "id": str(item.get("id") or item.get("site_id") or f"site-{index}"),
                    "name": str(item.get("name") or item.get("site_name") or "Unknown Site"),
                    "enabled": bool(item.get("enabled", True)),
                    "visibility": "unverified",
                    "note": "Loaded from configured host site endpoint; field mapping remains unverified.",
                }
                for index, item in enumerate(raw_items, start=1)
            ]
            summary = self._summary(
                capability="sites",
                capability_available=bool(items),
                status=self._status_from_availability(bool(items)),
                integration_point="RealHostProbeAdapter.list_sites",
                note="Sites were loaded through the configured host endpoint. Sensitive field stripping still needs real host verification.",
            )
        except HostTransportError as exc:
            items = []
            summary = self._degraded_summary(
                capability="sites",
                integration_point="RealHostProbeAdapter.list_sites",
                note=str(exc),
                fallback_reason=exc.reason_code,
            )
        return ProbeSitesPayload(summary=summary, items=items)

    def search_summary(self) -> ProbeSearchPayload:
        available = bool(self.settings.host_search_title_path and self.settings.host_base_url)
        summary = self._summary(
            capability="search",
            capability_available=available,
            status=self._status_from_availability(available),
            integration_point="RealHostProbeAdapter.probe_search",
            note=(
                "Search summary is derived from real MoviePilot search endpoint availability. "
                "Use POST /probe/search to validate `/api/v1/search/title` compatibility."
            ),
        )
        return ProbeSearchPayload(
            summary=summary,
            query_echo=ProbeSearchRequest().model_dump(mode="json"),
            sample_result_fields=["meta_info", "media_info", "torrent_info"],
            sample_result_count=0,
        )

    def probe_search(self, payload: ProbeSearchRequest) -> ProbeSearchPayload:
        try:
            data = self.client.get_json(
                self.settings.host_search_title_path,
                params={"keyword": payload.keyword, "page": 0},
                auth_mode="x_api_key",
            )
            items = self._extract_items(data)
            summary = self._summary(
                capability="search",
                capability_available=True,
                status=self._status_from_availability(True),
                integration_point="RealHostProbeAdapter.probe_search",
                note="Probe search called the real MoviePilot `/api/v1/search/title` endpoint.",
            )
            return ProbeSearchPayload(
                summary=summary,
                query_echo=payload.model_dump(mode="json"),
                sample_result_fields=list(items[0].keys())[:6] if items else ["meta_info", "media_info", "torrent_info"],
                sample_result_count=len(items),
            )
        except HostTransportError as exc:
            return ProbeSearchPayload(
                summary=self._degraded_summary(
                    capability="search",
                    integration_point="RealHostProbeAdapter.probe_search",
                    note=str(exc),
                    fallback_reason=exc.reason_code,
                ),
                query_echo=payload.model_dump(mode="json"),
                sample_result_fields=["site_id", "title", "size_bytes", "seeders"],
                sample_result_count=0,
            )

    def list_downloaders(self) -> ProbeDownloadersPayload:
        try:
            payload = self.client.get_json(self.settings.host_downloaders_path)
            raw_items = self._extract_items(payload)
            items = [
                {
                    "id": str(item.get("name") or item.get("id") or f"downloader-{index}"),
                    "name": str(item.get("name") or item.get("display_name") or "Unknown Downloader"),
                    "is_default": bool(item.get("is_default", index == 1)),
                    "status": "unverified",
                    "note": f"Loaded from real MoviePilot downloader endpoint; downloader type={item.get('type')!s}.",
                }
                for index, item in enumerate(raw_items, start=1)
            ]
            summary = self._summary(
                capability="downloaders",
                capability_available=bool(items),
                status=self._status_from_availability(bool(items)),
                integration_point="RealHostProbeAdapter.list_downloaders",
                note="Downloader list was loaded through the real MoviePilot `/api/v1/download/clients` endpoint.",
            )
        except HostTransportError as exc:
            items = []
            summary = self._degraded_summary(
                capability="downloaders",
                integration_point="RealHostProbeAdapter.list_downloaders",
                note=str(exc),
                fallback_reason=exc.reason_code,
            )
        return ProbeDownloadersPayload(summary=summary, items=items)

    def probe_dispatch(self, payload: ProbeDispatchRequest) -> ProbeDispatchPayload:
        try:
            data = self.client.post_json(
                self.settings.host_download_add_path,
                {
                    "torrent_in": {
                        "title": f"MusicPilot Probe {payload.result_id}",
                        "description": "Low-risk dispatch payload compatibility validation",
                        "site": 0,
                        "site_name": "MusicPilot Probe",
                        "size": 1,
                        "seeders": 0,
                        "peers": 0,
                        "enclosure": "magnet:?xt=urn:btih:0000000000000000000000000000000000000000",
                    },
                    "downloader": payload.downloader_id,
                },
                auth_mode="x_api_key",
            )
            preview = {
                "accepted": bool(data.get("success", False)),
                "downloader_task_id": (data.get("data") or {}).get("download_id") if isinstance(data.get("data"), dict) else None,
                "mode": "moviepilot.download.add",
                "message": data.get("message"),
            }
            summary = self._summary(
                capability="dispatch",
                capability_available=True,
                status=self._status_from_availability(True),
                integration_point="RealHostProbeAdapter.probe_dispatch",
                note="Dispatch probe hit the real MoviePilot `/api/v1/download/add` endpoint with a low-risk validation payload.",
            )
        except HostTransportError as exc:
            preview = {
                "accepted": False,
                "downloader_task_id": None,
                "mode": "host-unavailable",
                "message": str(exc),
            }
            summary = self._degraded_summary(
                capability="dispatch",
                integration_point="RealHostProbeAdapter.probe_dispatch",
                note=str(exc),
                fallback_reason=exc.reason_code,
            )

        return ProbeDispatchPayload(
            summary=summary,
            request_echo=payload.model_dump(mode="json"),
            dispatch_preview=preview,
        )

    def probe_notify(self, payload: ProbeNotifyRequest) -> ProbeNotifyPayload:
        if not self.settings.host_notify_path:
            return ProbeNotifyPayload(
                summary=self._summary(
                    capability="notify",
                    capability_available=False,
                    status="placeholder",
                    integration_point="RealHostProbeAdapter.probe_notify",
                    note="Notify endpoint is not configured yet; keep this capability as placeholder until host contract is confirmed.",
                    fallback_reason="host_notify_path_missing",
                ),
                request_echo=payload.model_dump(mode="json"),
                notification_preview={"title": payload.title, "body": payload.body, "channel": payload.channel, "sent": False},
            )

        try:
            data = self.client.post_json(self.settings.host_notify_path, payload.model_dump(mode="json"))
            preview = {
                "title": payload.title,
                "body": payload.body,
                "channel": payload.channel,
                "sent": bool(data.get("sent", data.get("accepted", False))),
            }
            summary = self._summary(
                capability="notify",
                capability_available=True,
                status=self._status_from_availability(True),
                integration_point="RealHostProbeAdapter.probe_notify",
                note="Notify endpoint was called through configured host settings.",
            )
        except HostTransportError as exc:
            summary = self._degraded_summary(
                capability="notify",
                integration_point="RealHostProbeAdapter.probe_notify",
                note=str(exc),
                fallback_reason=exc.reason_code,
            )
            preview = {"title": payload.title, "body": payload.body, "channel": payload.channel, "sent": False}
        return ProbeNotifyPayload(summary=summary, request_echo=payload.model_dump(mode="json"), notification_preview=preview)

    def config_summary(self) -> ProbeConfigPayload:
        supported = bool(self.settings.host_config_path)
        return ProbeConfigPayload(
            summary=self._summary(
                capability="config",
                capability_available=supported,
                status=self._status_from_availability(supported),
                integration_point="RealHostProbeAdapter.probe_config",
                note="Config capability summary is derived from configured host config endpoint availability.",
                fallback_reason=None if supported else "host_config_path_missing",
            ),
            operation="summary",
            request_echo=ProbeConfigRequest().model_dump(mode="json"),
            config_preview={
                "supported_operations": ["read", "write"],
                "storage_connected": supported,
            },
        )

    def probe_config(self, payload: ProbeConfigRequest) -> ProbeConfigPayload:
        if not self.settings.host_config_path:
            return ProbeConfigPayload(
                summary=self._summary(
                    capability="config",
                    capability_available=False,
                    status="placeholder",
                    integration_point="RealHostProbeAdapter.probe_config",
                    note="Config endpoint is not configured yet.",
                    fallback_reason="host_config_path_missing",
                ),
                operation=payload.operation,
                request_echo=payload.model_dump(mode="json"),
                config_preview={"key": payload.key, "value": payload.value, "persisted": False},
            )

        try:
            data = self.client.post_json(self.settings.host_config_path, payload.model_dump(mode="json"))
            preview = {
                "key": payload.key,
                "value": data.get("value", payload.value),
                "persisted": bool(data.get("persisted", payload.operation == "read")),
            }
            summary = self._summary(
                capability="config",
                capability_available=True,
                status=self._status_from_availability(True),
                integration_point="RealHostProbeAdapter.probe_config",
                note="Config endpoint was called through configured host settings.",
            )
        except HostTransportError as exc:
            preview = {"key": payload.key, "value": payload.value, "persisted": False}
            summary = self._degraded_summary(
                capability="config",
                integration_point="RealHostProbeAdapter.probe_config",
                note=str(exc),
                fallback_reason=exc.reason_code,
            )
        return ProbeConfigPayload(
            summary=summary,
            operation=payload.operation,
            request_echo=payload.model_dump(mode="json"),
            config_preview=preview,
        )

    def _summary(
        self,
        *,
        capability: str,
        capability_available: bool | None,
        status: str,
        integration_point: str,
        note: str,
        fallback_reason: str | None = None,
    ) -> ProbeCapabilitySummary:
        return ProbeCapabilitySummary(
            capability=capability,
            status=status,
            host_online=None if capability != "health" else capability_available,
            capability_available=capability_available,
            adapter_mode=AdapterMode.HOST,
            active_strategy=AdapterStrategy.PREFER_HOST,
            host_integration_enabled=self.settings.host_integration_enabled,
            capability_source="host.probe",
            verification_state=VerificationState(self.settings.host_verification_state),
            fallback_reason=fallback_reason,
            integration_point=integration_point,
            note=note,
            todo=[
                "Capture real MoviePilot request/response samples before marking this capability verified.",
                "Confirm field mapping against the host's real contract.",
            ],
        )

    def _degraded_summary(
        self,
        *,
        capability: str,
        integration_point: str,
        note: str,
        fallback_reason: str,
    ) -> ProbeCapabilitySummary:
        return self._summary(
            capability=capability,
            capability_available=False,
            status="degraded",
            integration_point=integration_point,
            note=note,
            fallback_reason=fallback_reason,
        )

    def _status_from_availability(self, available: bool | None) -> str:
        if available is None:
            return "placeholder"
        if available:
            return "verified" if self.settings.host_verification_state == "verified" else "unverified"
        return "degraded"

    def _extract_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data", payload)
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            return [item for item in data["items"] if isinstance(item, dict)]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return []

    def _extract_health_checks(self, payload: dict[str, Any]) -> dict[str, str | bool | None]:
        data = payload.get("data", payload)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return {
                "host_online": True,
                "plugin_api_registered": None,
                "note": "Host health was inferred from a real MoviePilot list endpoint returning JSON successfully.",
            }
        if isinstance(data, dict):
            status = data.get("status")
            return {
                "host_online": status in {"ok", "healthy", True},
                "plugin_api_registered": data.get("plugin_api_registered"),
                "note": str(data.get("note", "Host health probe completed through configured endpoint.")),
            }
        return {
            "host_online": False,
            "plugin_api_registered": None,
            "note": "Host health response shape was not recognized.",
        }
