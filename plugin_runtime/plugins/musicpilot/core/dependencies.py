"""Dependency providers for MusicPilot backend services."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..adapters.download_dispatch import DownloadDispatchAdapter, MockDownloadDispatchAdapter
from ..adapters.host_probe import MockHostProbeAdapter
from ..adapters.host_search import HostSearchAdapter, MockHostSearchAdapter
from ..adapters.metadata_provider import MetadataProviderAdapter, MockMetadataProviderAdapter
from ..core.db import get_db_session
from ..services.host_capabilities import HostCapabilitiesService
from ..services.dispatch import DispatchService
from ..services.metadata import MetadataService
from ..services.mvp_placeholder import MvpPlaceholderService
from ..services.query_builder import QueryBuilderService
from ..services.scoring import MusicCandidateScorer
from ..services.search_job import SearchJobService


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


def get_query_builder_service(
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> QueryBuilderService:
    return QueryBuilderService(metadata_service=metadata_service)


@lru_cache
def get_host_search_adapter() -> HostSearchAdapter:
    return MockHostSearchAdapter()


def get_candidate_scorer() -> MusicCandidateScorer:
    return MusicCandidateScorer()


def get_search_job_service(
    session: Session = Depends(get_db_session),
    metadata_service: MetadataService = Depends(get_metadata_service),
    query_builder: QueryBuilderService = Depends(get_query_builder_service),
    host_search_adapter: HostSearchAdapter = Depends(get_host_search_adapter),
    scorer: MusicCandidateScorer = Depends(get_candidate_scorer),
) -> SearchJobService:
    return SearchJobService(
        session,
        metadata_service=metadata_service,
        query_builder=query_builder,
        host_search_adapter=host_search_adapter,
        scorer=scorer,
    )


@lru_cache
def get_download_dispatch_adapter() -> DownloadDispatchAdapter:
    return MockDownloadDispatchAdapter()


def get_dispatch_service(
    session: Session = Depends(get_db_session),
    adapter: DownloadDispatchAdapter = Depends(get_download_dispatch_adapter),
) -> DispatchService:
    return DispatchService(session=session, adapter=adapter)
