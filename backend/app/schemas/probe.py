"""Schemas for host probe boundaries and payloads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .integration import AdapterMode, AdapterStrategy, HostIntegrationRuntimeState, VerificationState


class ProbeCapabilitySummary(BaseModel):
    capability: str = Field(..., description="Capability name under probe.")
    status: Literal["mock", "placeholder", "unverified", "verified", "degraded", "disabled"] = Field(
        default="mock"
    )
    host_online: bool | None = Field(
        default=None,
        description="Whether the host is confirmed online. None means not checked in mock mode.",
    )
    capability_available: bool | None = Field(
        default=None,
        description="Whether the capability is confirmed available. None means not checked in mock mode.",
    )
    adapter_mode: AdapterMode = Field(default=AdapterMode.MOCK)
    active_strategy: AdapterStrategy = Field(default=AdapterStrategy.MOCK)
    host_integration_enabled: bool = False
    capability_source: str = "mock.probe"
    verification_state: VerificationState = VerificationState.PLACEHOLDER
    fallback_reason: str | None = None
    integration_point: str = Field(..., description="Future adapter or service handoff point.")
    note: str = Field(..., description="Current placeholder description.")
    todo: list[str] = Field(default_factory=list, description="Integration follow-up items.")


class ProbeSiteItem(BaseModel):
    id: str
    name: str
    enabled: bool
    visibility: Literal["placeholder", "unverified"] = "placeholder"
    note: str


class ProbeDownloaderItem(BaseModel):
    id: str
    name: str
    is_default: bool
    status: Literal["placeholder", "unverified"] = "placeholder"
    note: str


class ProbeSearchRequest(BaseModel):
    keyword: str = Field(default="phase1-smoke-test")
    site_scope: list[str] = Field(default_factory=list)
    dry_run: bool = Field(default=True)


class ProbeDispatchRequest(BaseModel):
    result_id: str = Field(default="mock-result-001")
    downloader_id: str = Field(default="mock-downloader")
    dry_run: bool = Field(default=True)


class ProbeNotifyRequest(BaseModel):
    title: str = Field(default="MusicPilot Probe")
    body: str = Field(default="Phase 1 notification probe placeholder.")
    channel: str = Field(default="system")


class ProbeConfigRequest(BaseModel):
    operation: Literal["read", "write"] = Field(default="read")
    key: str = Field(default="probe.default_profile")
    value: Any = Field(default="placeholder")


class ProbeHealthPayload(BaseModel):
    summary: ProbeCapabilitySummary
    checks: dict[str, str | bool | None]
    runtime_state: HostIntegrationRuntimeState | None = None


class ProbeSitesPayload(BaseModel):
    summary: ProbeCapabilitySummary
    items: list[ProbeSiteItem]


class ProbeSearchPayload(BaseModel):
    summary: ProbeCapabilitySummary
    query_echo: dict[str, Any]
    sample_result_fields: list[str]
    sample_result_count: int


class ProbeDownloadersPayload(BaseModel):
    summary: ProbeCapabilitySummary
    items: list[ProbeDownloaderItem]


class ProbeDispatchPayload(BaseModel):
    summary: ProbeCapabilitySummary
    request_echo: dict[str, Any]
    dispatch_preview: dict[str, Any]


class ProbeNotifyPayload(BaseModel):
    summary: ProbeCapabilitySummary
    request_echo: dict[str, Any]
    notification_preview: dict[str, Any]


class ProbeConfigPayload(BaseModel):
    summary: ProbeCapabilitySummary
    operation: str
    request_echo: dict[str, Any]
    config_preview: dict[str, Any]
