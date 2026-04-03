"""Dependency providers for MusicPilot backend services."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..adapters.host_probe import MockHostProbeAdapter
from ..adapters.metadata_provider import MetadataProviderAdapter, MockMetadataProviderAdapter
from ..core.db import get_db_session
from ..services.host_capabilities import HostCapabilitiesService
from ..services.metadata import MetadataService
from ..services.mvp_placeholder import MvpPlaceholderService


@lru_cache
def get_host_capabilities_service() -> HostCapabilitiesService:
    return HostCapabilitiesService(adapter=MockHostProbeAdapter())


@lru_cache
def get_mvp_placeholder_service() -> MvpPlaceholderService:
    return MvpPlaceholderService()


@lru_cache
def get_metadata_provider_adapter() -> MetadataProviderAdapter:
    return MockMetadataProviderAdapter()


def get_metadata_service(
    session: Session = Depends(get_db_session),
    adapter: MetadataProviderAdapter = Depends(get_metadata_provider_adapter),
) -> MetadataService:
    return MetadataService(session=session, adapter=adapter)
