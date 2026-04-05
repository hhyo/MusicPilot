"""Dependency providers for MusicPilot backend services."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..adapters.download_dispatch import (
    DownloadDispatchAdapter,
    MockDownloadDispatchAdapter,
    RealDownloadDispatchAdapter,
)
from ..adapters.host_http import HostHttpClient, HostHttpClientConfig
from ..adapters.host_storage_runtime import HostStorageRuntimeBridge
from ..adapters.chart_provider import (
    ChartProviderAdapter,
    ListenBrainzChartProviderAdapter,
    MockChartProviderAdapter,
)
from ..adapters.host_downloader_runtime import HostDownloaderRuntimeBridge
from ..adapters.host_probe import HostProbeAdapter, MockHostProbeAdapter, RealHostProbeAdapter
from ..adapters.host_search import HostSearchAdapter, MockHostSearchAdapter, RealHostSearchAdapter
from ..adapters.metadata_provider import (
    MetadataProviderAdapter,
    MockMetadataProviderAdapter,
    MusicBrainzMetadataProviderAdapter,
)
from ..adapters.organize import MockOrganizeAdapter, OrganizeAdapter, RealOrganizeAdapter
from ..core.db import SessionLocal, get_db_session
from ..core.config import settings
from ..repositories.orchestration import OrchestrationRepository
from ..services.charts import ChartService
from ..services.host_capabilities import HostCapabilitiesService
from ..services.dispatch import DispatchService
from ..services.discovery import DiscoveryAssembler
from ..services.host_integration import (
    DispatchAdapterResolver,
    HostIntegrationService,
    OrganizeAdapterResolver,
    HostSearchAdapterResolver,
)
from ..services.host_path_handoff import HostPathHandoffService
from ..services.metadata import MetadataService
from ..services.mvp_placeholder import MvpPlaceholderService
from ..services.organize import OrganizeService
from ..services.organize_strategy import OrganizeStrategyService
from ..services.query_builder import QueryBuilderService
from ..services.scoring import MusicCandidateScorer
from ..services.search_job import SearchJobService
from ..services.subscription_execution import SubscriptionExecutionService
from ..services.subscription_scheduler import SubscriptionSchedulerService
from ..services.subscriptions import SubscriptionService
from ..services.validation_matrix import HostValidationMatrixService


@lru_cache
def get_host_capabilities_service() -> HostCapabilitiesService:
    return HostCapabilitiesService(
        adapter=get_host_probe_adapter(),
        integration_service=get_host_integration_service(),
        validation_matrix_service=get_validation_matrix_service(),
    )


@lru_cache
def get_mvp_placeholder_service() -> MvpPlaceholderService:
    return MvpPlaceholderService()


@lru_cache
def get_discovery_assembler() -> DiscoveryAssembler:
    return DiscoveryAssembler()


@lru_cache
def get_metadata_provider_adapter() -> MetadataProviderAdapter:
    if settings.metadata_provider_mode == "musicbrainz":
        return MusicBrainzMetadataProviderAdapter(
            base_url=settings.metadata_musicbrainz_base_url,
            user_agent=settings.metadata_provider_user_agent,
            timeout_seconds=settings.metadata_provider_timeout_seconds,
            cache_enabled=settings.metadata_cache_enabled,
            cache_maxsize=settings.metadata_cache_maxsize,
            search_cache_ttl_seconds=settings.metadata_search_cache_ttl_seconds,
            detail_cache_ttl_seconds=settings.metadata_detail_cache_ttl_seconds,
        )
    return MockMetadataProviderAdapter()


@lru_cache
def get_chart_provider_adapter() -> ChartProviderAdapter:
    if settings.chart_provider_mode == "listenbrainz":
        return ListenBrainzChartProviderAdapter(
            base_url=settings.chart_listenbrainz_base_url,
            user_agent=settings.chart_provider_user_agent,
            timeout_seconds=settings.chart_provider_timeout_seconds,
            stats_range=settings.chart_listenbrainz_range,
            count=settings.chart_listenbrainz_count,
            cache_enabled=settings.chart_cache_enabled,
            cache_maxsize=settings.chart_cache_maxsize,
            cache_ttl_seconds=settings.chart_cache_ttl_seconds,
        )
    metadata_adapter = MockMetadataProviderAdapter()
    return MockChartProviderAdapter(metadata_adapter.load_seed_catalog())


@lru_cache
def get_host_http_client() -> HostHttpClient:
    return HostHttpClient(
        HostHttpClientConfig(
            base_url=settings.host_base_url,
            timeout_seconds=settings.host_timeout_seconds,
            verify_tls=settings.host_verify_tls,
            auth_token=settings.host_auth_token,
            auth_mode=settings.host_auth_mode,
            api_key_header_name=settings.host_api_key_header_name,
        )
    )


@lru_cache
def get_host_probe_adapter() -> HostProbeAdapter:
    if settings.host_integration_enabled:
        return RealHostProbeAdapter(settings=settings, client=get_host_http_client())
    return MockHostProbeAdapter()


@lru_cache
def get_host_integration_service() -> HostIntegrationService:
    return HostIntegrationService(settings=settings, probe_adapter=get_host_probe_adapter())


@lru_cache
def get_host_path_handoff_service() -> HostPathHandoffService:
    return HostPathHandoffService(settings=settings, client=get_host_http_client())


@lru_cache
def get_validation_matrix_service() -> HostValidationMatrixService:
    return HostValidationMatrixService(settings=settings)


def get_metadata_service(
    session: Session = Depends(get_db_session),
    adapter: MetadataProviderAdapter = Depends(get_metadata_provider_adapter),
) -> MetadataService:
    return MetadataService(session=session, adapter=adapter)


def get_chart_service(
    adapter: ChartProviderAdapter = Depends(get_chart_provider_adapter),
    discovery_assembler: DiscoveryAssembler = Depends(get_discovery_assembler),
) -> ChartService:
    return ChartService(adapter=adapter, discovery_assembler=discovery_assembler)


def get_query_builder_service(
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> QueryBuilderService:
    return QueryBuilderService(metadata_service=metadata_service)


@lru_cache
def get_host_search_adapter() -> HostSearchAdapter:
    return MockHostSearchAdapter()


@lru_cache
def get_real_host_search_adapter() -> HostSearchAdapter:
    return RealHostSearchAdapter(settings=settings, client=get_host_http_client())


def get_candidate_scorer() -> MusicCandidateScorer:
    return MusicCandidateScorer()


@lru_cache
def get_host_search_adapter_resolver() -> HostSearchAdapterResolver:
    return HostSearchAdapterResolver(
        integration_service=get_host_integration_service(),
        mock_adapter=get_host_search_adapter(),
        host_adapter=get_real_host_search_adapter(),
    )


def get_search_job_service(
    session: Session = Depends(get_db_session),
    metadata_service: MetadataService = Depends(get_metadata_service),
    query_builder: QueryBuilderService = Depends(get_query_builder_service),
    host_search_resolver: HostSearchAdapterResolver = Depends(get_host_search_adapter_resolver),
    scorer: MusicCandidateScorer = Depends(get_candidate_scorer),
) -> SearchJobService:
    return SearchJobService(
        session,
        metadata_service=metadata_service,
        query_builder=query_builder,
        host_search_resolver=host_search_resolver,
        scorer=scorer,
    )


@lru_cache
def get_download_dispatch_adapter() -> DownloadDispatchAdapter:
    return MockDownloadDispatchAdapter()


@lru_cache
def get_real_download_dispatch_adapter() -> DownloadDispatchAdapter:
    return RealDownloadDispatchAdapter(
        settings=settings,
        client=get_host_http_client(),
        path_handoff_service=get_host_path_handoff_service(),
        downloader_runtime=get_host_downloader_runtime_bridge(),
    )


@lru_cache
def get_organize_adapter() -> OrganizeAdapter:
    return MockOrganizeAdapter()


@lru_cache
def get_host_storage_runtime_bridge() -> HostStorageRuntimeBridge:
    return HostStorageRuntimeBridge()


@lru_cache
def get_host_downloader_runtime_bridge() -> HostDownloaderRuntimeBridge:
    return HostDownloaderRuntimeBridge()


@lru_cache
def get_real_organize_adapter() -> OrganizeAdapter:
    return RealOrganizeAdapter(
        settings=settings,
        client=get_host_http_client(),
        storage_runtime=get_host_storage_runtime_bridge(),
    )


@lru_cache
def get_organize_strategy_service() -> OrganizeStrategyService:
    return OrganizeStrategyService(settings=settings)


@lru_cache
def get_dispatch_adapter_resolver() -> DispatchAdapterResolver:
    return DispatchAdapterResolver(
        integration_service=get_host_integration_service(),
        mock_adapter=get_download_dispatch_adapter(),
        host_adapter=get_real_download_dispatch_adapter(),
    )


def get_dispatch_service(
    session: Session = Depends(get_db_session),
    resolver: DispatchAdapterResolver = Depends(get_dispatch_adapter_resolver),
) -> DispatchService:
    return DispatchService(session=session, resolver=resolver)


@lru_cache
def get_organize_adapter_resolver() -> OrganizeAdapterResolver:
    return OrganizeAdapterResolver(
        integration_service=get_host_integration_service(),
        mock_adapter=get_organize_adapter(),
        host_adapter=get_real_organize_adapter(),
    )


def get_subscription_service(
    session: Session = Depends(get_db_session),
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> SubscriptionService:
    return SubscriptionService(session=session, metadata_service=metadata_service)


def get_organize_service(
    session: Session = Depends(get_db_session),
    resolver: OrganizeAdapterResolver = Depends(get_organize_adapter_resolver),
    strategy_service: OrganizeStrategyService = Depends(get_organize_strategy_service),
    path_handoff_service: HostPathHandoffService = Depends(get_host_path_handoff_service),
) -> OrganizeService:
    return OrganizeService(
        session=session,
        resolver=resolver,
        strategy_service=strategy_service,
        path_handoff_service=path_handoff_service,
    )


def get_subscription_execution_service(
    session: Session = Depends(get_db_session),
    search_job_service: SearchJobService = Depends(get_search_job_service),
    organize_service: OrganizeService = Depends(get_organize_service),
    dispatch_service: DispatchService = Depends(get_dispatch_service),
) -> SubscriptionExecutionService:
    return SubscriptionExecutionService(
        session=session,
        search_job_service=search_job_service,
        organize_service=organize_service,
        dispatch_service=dispatch_service,
    )


def build_subscription_execution_service(session: Session) -> SubscriptionExecutionService:
    metadata_service = MetadataService(session=session, adapter=get_metadata_provider_adapter())
    search_job_service = SearchJobService(
        session,
        metadata_service=metadata_service,
        query_builder=QueryBuilderService(metadata_service=metadata_service),
        host_search_resolver=get_host_search_adapter_resolver(),
        scorer=get_candidate_scorer(),
    )
    return SubscriptionExecutionService(
        session=session,
        search_job_service=search_job_service,
        organize_service=OrganizeService(
            session=session,
            resolver=get_organize_adapter_resolver(),
            strategy_service=get_organize_strategy_service(),
            path_handoff_service=get_host_path_handoff_service(),
        ),
        dispatch_service=DispatchService(
            session=session,
            resolver=get_dispatch_adapter_resolver(),
        ),
    )


def build_subscription_scheduler_service(session: Session) -> SubscriptionSchedulerService:
    execution_service = build_subscription_execution_service(session)
    return SubscriptionSchedulerService(
        repository=OrchestrationRepository(session),
        execute_subscription=execution_service.execute,
        default_interval_minutes=settings.subscription_scheduler_default_interval_minutes,
    )


def get_session_factory():
    return SessionLocal
