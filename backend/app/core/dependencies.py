"""Dependency providers for Phase 1 services."""

from __future__ import annotations

from functools import lru_cache

from ..adapters.host_probe import MockHostProbeAdapter
from ..services.host_capabilities import HostCapabilitiesService
from ..services.mvp_placeholder import MvpPlaceholderService


@lru_cache
def get_host_capabilities_service() -> HostCapabilitiesService:
    return HostCapabilitiesService(adapter=MockHostProbeAdapter())


@lru_cache
def get_mvp_placeholder_service() -> MvpPlaceholderService:
    return MvpPlaceholderService()

