"""Schemas for Phase 5 host integration wiring and adapter resolution."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AdapterMode(str, Enum):
    MOCK = "mock"
    HOST = "host"


class AdapterSelectionMode(str, Enum):
    MOCK = "mock"
    PREFER_HOST = "prefer_host"
    STRICT_HOST = "strict_host"


class VerificationState(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PLACEHOLDER = "placeholder"


class AdapterResolution(BaseModel):
    adapter_key: str
    adapter_mode: AdapterMode
    selection_mode: AdapterSelectionMode
    capability_source: str
    verification_state: VerificationState
    fallback_reason: str | None = None
    integration_point: str
    host_integration_enabled: bool = False


class HostIntegrationRuntimeState(BaseModel):
    host_integration_enabled: bool
    host_base_url: str | None = None
    verification_state: VerificationState = VerificationState.PLACEHOLDER
    capability_source: str
    host_online: bool | None = None
    search_capability: bool | None = None
    dispatch_capability: bool | None = None
    organize_capability: bool | None = None
    downloaders_available: bool | None = None
    sites_visible: bool | None = None
    search_mode: AdapterSelectionMode = AdapterSelectionMode.MOCK
    dispatch_mode: AdapterSelectionMode = AdapterSelectionMode.MOCK
    organize_mode: AdapterSelectionMode = AdapterSelectionMode.MOCK
    active_search_adapter: str
    active_dispatch_adapter: str
    active_organize_adapter: str
    search_fallback_reason: str | None = None
    dispatch_fallback_reason: str | None = None
    organize_fallback_reason: str | None = None
    note: str
    integration_point: str = Field(
        default=(
            "Host integration wiring is resolved centrally so services can choose explicit mock mode "
            "or explicit host mode without hiding runtime failures behind other business semantics."
        )
    )
