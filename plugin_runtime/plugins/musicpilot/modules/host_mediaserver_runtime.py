"""Thin in-process host-runtime bridge for MoviePilot media server sync."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

from .host_http import HostTransportError


class HostMediaServerRuntimeBridge:
    """Execute MoviePilot media server sync from the host plugin process."""

    def __init__(self, *, import_module_func: Callable[[str], Any] = import_module) -> None:
        self._import_module = import_module_func

    def sync(self) -> dict[str, Any]:
        try:
            module = self._import_module("app.chain.mediaserver")
        except Exception as exc:  # pragma: no cover - depends on host runtime
            raise HostTransportError(
                f"MoviePilot media server runtime is only available inside the host plugin process: {exc}",
                reason_code="moviepilot_mediaserver_runtime_unavailable",
            ) from exc

        chain_cls = getattr(module, "MediaServerChain", None)
        if chain_cls is None:
            raise HostTransportError(
                "MoviePilot media server chain is unavailable in the current host runtime.",
                reason_code="moviepilot_mediaserver_chain_missing",
            )

        chain = chain_cls()
        result = chain.sync()
        libraries_synced = None
        if isinstance(result, dict):
            libraries_synced = result.get("libraries_synced")

        return {
            "success": True,
            "sync_status": "synced",
            "message": "",
            "libraries_synced": libraries_synced,
            "integration_point": "HostMediaServerRuntimeBridge.sync",
            "capability_source": "moviepilot.runtime.mediaserver_sync",
        }
