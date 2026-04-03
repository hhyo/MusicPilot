"""Shared HTTP client helpers for Phase 5 host-backed adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class HostTransportError(RuntimeError):
    def __init__(self, message: str, *, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(slots=True)
class HostHttpClientConfig:
    base_url: str | None
    timeout_seconds: float
    verify_tls: bool
    auth_token: str | None = None


class HostHttpClient:
    def __init__(self, config: HostHttpClientConfig):
        self.config = config

    def get_json(self, path: str | None) -> dict[str, Any]:
        return self._request_json("GET", path)

    def post_json(self, path: str | None, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", path, payload)

    def _request_json(
        self,
        method: str,
        path: str | None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.config.base_url:
            raise HostTransportError(
                "MUSICPILOT_HOST_BASE_URL is not configured.",
                reason_code="host_base_url_missing",
            )
        if not path:
            raise HostTransportError(
                "The requested host integration path is not configured.",
                reason_code="host_path_missing",
            )

        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"

        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

        try:
            with httpx.Client(timeout=self.config.timeout_seconds, verify=self.config.verify_tls) as client:
                response = client.request(method=method, url=url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise HostTransportError(
                f"Host endpoint returned HTTP {exc.response.status_code}: {url}",
                reason_code="host_http_error",
            ) from exc
        except httpx.RequestError as exc:
            raise HostTransportError(
                f"Host request failed for {url}: {exc}",
                reason_code="host_request_failed",
            ) from exc
        except ValueError as exc:
            raise HostTransportError(
                f"Host endpoint did not return JSON payload: {url}",
                reason_code="host_invalid_json",
            ) from exc

        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {"items": data}

        raise HostTransportError(
            f"Host endpoint returned an unsupported JSON shape: {url}",
            reason_code="host_unsupported_payload",
        )
