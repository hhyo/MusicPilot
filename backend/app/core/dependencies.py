"""Dependency providers for MusicPilot backend services."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..adapters.chart_provider import ChartProviderAdapter, MockChartProviderAdapter
from ..adapters.download_dispatch import DownloadDispatchAdapter, MockDownloadDispatchAdapter
from ..adapters.host_probe import MockHostProbeAdapter
from ..adapters.host_search import HostSearchAdapter, MockHostSearchAdapter
from ..adapters.metadata_provider import MetadataProviderAdapter, MockMetadataProviderAdapter
from ..adapters.organize import MockOrganizeAdapter, OrganizeAdapter
from ..core.db import get_db_session
from ..services.charts import ChartService
from ..services.host_capabilities import HostCapabilitiesService
from ..services.dispatch import DispatchService
from ..services.metadata import MetadataService
from ..services.mvp_placeholder import MvpPlaceholderService
from ..services.organize import OrganizeService
from ..services.query_builder import QueryBuilderService
from ..services.scoring import MusicCandidateScorer
from ..services.search_job import SearchJobService
from ..services.subscription_execution import SubscriptionExecutionService
from ..services.subscriptions import SubscriptionService


@lru_cache
def get_host_capabilities_service() -> HostCapabilitiesService:
    return HostCapabilitiesService(adapter=MockHostProbeAdapter())


@lru_cache
def get_mvp_placeholder_service() -> MvpPlaceholderService:
    return MvpPlaceholderService()


@lru_cache
def get_metadata_provider_adapter() -> MetadataProviderAdapter:
    return MockMetadataProviderAdapter()


@lru_cache
def get_chart_provider_adapter() -> ChartProviderAdapter:
    metadata_adapter = MockMetadataProviderAdapter()
    return MockChartProviderAdapter(metadata_adapter.load_seed_catalog())


def get_metadata_service(
    session: Session = Depends(get_db_session),
    adapter: MetadataProviderAdapter = Depends(get_metadata_provider_adapter),
) -> MetadataService:
    return MetadataService(session=session, adapter=adapter)


def get_chart_service(
    adapter: ChartProviderAdapter = Depends(get_chart_provider_adapter),
) -> ChartService:
    return ChartService(adapter=adapter)


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


@lru_cache
def get_organize_adapter() -> OrganizeAdapter:
    return MockOrganizeAdapter()


def get_dispatch_service(
    session: Session = Depends(get_db_session),
    adapter: DownloadDispatchAdapter = Depends(get_download_dispatch_adapter),
) -> DispatchService:
    return DispatchService(session=session, adapter=adapter)


def get_subscription_service(
    session: Session = Depends(get_db_session),
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> SubscriptionService:
    return SubscriptionService(session=session, metadata_service=metadata_service)


def get_organize_service(
    session: Session = Depends(get_db_session),
    adapter: OrganizeAdapter = Depends(get_organize_adapter),
) -> OrganizeService:
    return OrganizeService(session=session, adapter=adapter)


def get_subscription_execution_service(
    session: Session = Depends(get_db_session),
    search_job_service: SearchJobService = Depends(get_search_job_service),
    organize_service: OrganizeService = Depends(get_organize_service),
) -> SubscriptionExecutionService:
    return SubscriptionExecutionService(
        session=session,
        search_job_service=search_job_service,
        organize_service=organize_service,
    )
