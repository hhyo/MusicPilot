"""Dependency providers for MusicPilot backend chains and support objects."""

from __future__ import annotations

import json
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
    RssFeedChartProviderAdapter,
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
from ..chain.chart import MusicChartChain
from ..chain.dashboard import MusicDashboardChain
from ..chain.download import MusicDownloadChain
from ..chain.media import MusicMediaChain
from ..chain.search import MusicSearchChain
from ..chain.subscribe import MusicSubscribeChain
from ..chain.transfer import MusicTransferChain
from ..core.db import SessionLocal, get_db_session
from ..core.config import settings
from ..core.runtime_cache import stable_cache_key
from ..repositories.charts import ChartRepository
from ..repositories.orchestration import OrchestrationRepository
from ..services.charts import ChartService
from ..services.host_capabilities import HostCapabilitiesService
from ..services.dashboard import DashboardService
from ..services.dispatch import DispatchService
from ..services.discovery import DiscoveryAssembler
from ..services.downloads_workspace import DownloadsWorkspaceService
from ..services.host_integration import (
    DispatchAdapterResolver,
    HostIntegrationService,
    OrganizeAdapterResolver,
    HostSearchAdapterResolver,
)
from ..services.host_path_handoff import HostPathHandoffService
from ..services.metadata import MetadataService
from ..services.settings import SettingsService
from ..services.organize import OrganizeService
from ..services.organize_strategy import OrganizeStrategyService
from ..services.pending_handoff import PendingHandoffReconcileService
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


def get_settings_service(session: Session = Depends(get_db_session)) -> SettingsService:
    return SettingsService(session=session, env_settings=settings)


def get_dashboard_service(session: Session = Depends(get_db_session)) -> DashboardService:
    return DashboardService(session=session)


def get_downloads_workspace_service(
    session: Session = Depends(get_db_session),
) -> DownloadsWorkspaceService:
    return DownloadsWorkspaceService(
        session=session,
        dispatch_service=DispatchService(
            session=session,
            resolver=get_dispatch_adapter_resolver(),
        ),
        path_handoff_service=get_host_path_handoff_service(),
    )


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


def get_chart_provider_adapter(
    session: Session = Depends(get_db_session),
    settings_service: SettingsService = Depends(get_settings_service),
) -> ChartProviderAdapter:
    _ = session
    provider_settings = settings_service.get_provider_settings()
    feed_payload = [feed.model_dump(mode="json") for feed in provider_settings.chart_rss_feeds]
    cache_key = stable_cache_key(
        "chart_provider_adapter",
        provider_mode=provider_settings.chart_provider_mode.value,
        feeds=feed_payload,
        listenbrainz_base_url=settings.chart_listenbrainz_base_url,
        user_agent=settings.chart_provider_user_agent,
        timeout_seconds=settings.chart_provider_timeout_seconds,
        stats_range=settings.chart_listenbrainz_range,
        count=settings.chart_listenbrainz_count,
        cache_enabled=settings.chart_cache_enabled,
        cache_maxsize=settings.chart_cache_maxsize,
        cache_ttl_seconds=settings.chart_cache_ttl_seconds,
    )
    return _build_chart_provider_adapter(
        cache_key,
        provider_settings.chart_provider_mode.value,
        json.dumps(feed_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        settings.chart_listenbrainz_base_url,
        settings.chart_provider_user_agent,
        settings.chart_provider_timeout_seconds,
        settings.chart_listenbrainz_range,
        settings.chart_listenbrainz_count,
        settings.chart_cache_enabled,
        settings.chart_cache_maxsize,
        settings.chart_cache_ttl_seconds,
    )


@lru_cache(maxsize=32)
def _build_chart_provider_adapter(
    cache_key: str,
    provider_mode: str,
    feeds_json: str,
    listenbrainz_base_url: str,
    user_agent: str,
    timeout_seconds: float,
    stats_range: str,
    count: int,
    cache_enabled: bool,
    cache_maxsize: int,
    cache_ttl_seconds: int,
) -> ChartProviderAdapter:
    _ = cache_key
    if provider_mode == "listenbrainz":
        return ListenBrainzChartProviderAdapter(
            base_url=listenbrainz_base_url,
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
            stats_range=stats_range,
            count=count,
            cache_enabled=cache_enabled,
            cache_maxsize=cache_maxsize,
            cache_ttl_seconds=cache_ttl_seconds,
        )
    if provider_mode == "rss_feed":
        return RssFeedChartProviderAdapter(
            feeds=json.loads(feeds_json),
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
            cache_enabled=cache_enabled,
            cache_maxsize=cache_maxsize,
            cache_ttl_seconds=cache_ttl_seconds,
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


def get_music_media_chain(
    metadata_service: MetadataService = Depends(get_metadata_service),
    adapter: MetadataProviderAdapter = Depends(get_metadata_provider_adapter),
) -> MusicMediaChain:
    return MusicMediaChain(metadata_service=metadata_service, metadata_adapter=adapter)


def get_music_search_chain(
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> MusicSearchChain:
    return MusicSearchChain(metadata_service=metadata_service)


def get_music_download_chain(
    session: Session = Depends(get_db_session),
) -> MusicDownloadChain:
    return MusicDownloadChain(session=session)


def get_music_transfer_chain(
    session: Session = Depends(get_db_session),
) -> MusicTransferChain:
    return MusicTransferChain(session=session)


def get_music_subscribe_chain(
    session: Session = Depends(get_db_session),
) -> MusicSubscribeChain:
    return MusicSubscribeChain(session=session)


def get_music_chart_chain(
    session: Session = Depends(get_db_session),
) -> MusicChartChain:
    return MusicChartChain(session=session)


def get_music_dashboard_chain(
    session: Session = Depends(get_db_session),
) -> MusicDashboardChain:
    return MusicDashboardChain(session=session)


def get_discovery_assembler(
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> DiscoveryAssembler:
    return DiscoveryAssembler(music_media_chain=music_media_chain)


def get_chart_service(
    adapter: ChartProviderAdapter = Depends(get_chart_provider_adapter),
    discovery_assembler: DiscoveryAssembler = Depends(get_discovery_assembler),
    settings_service: SettingsService = Depends(get_settings_service),
    session: Session = Depends(get_db_session),
) -> ChartService:
    return ChartService(
        adapter=adapter,
        discovery_assembler=discovery_assembler,
        settings_service=settings_service,
        chart_repository=ChartRepository(session),
    )


def build_chart_service(session: Session) -> ChartService:
    settings_service = SettingsService(session=session, env_settings=settings)
    metadata_service = MetadataService(session=session, adapter=get_metadata_provider_adapter())
    music_media_chain = MusicMediaChain(
        metadata_service=metadata_service,
        metadata_adapter=get_metadata_provider_adapter(),
    )
    discovery_assembler = DiscoveryAssembler(music_media_chain=music_media_chain)
    adapter = get_chart_provider_adapter(session=session, settings_service=settings_service)
    return ChartService(
        adapter=adapter,
        discovery_assembler=discovery_assembler,
        settings_service=settings_service,
        chart_repository=ChartRepository(session),
    )


def get_query_builder_service(
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> QueryBuilderService:
    return QueryBuilderService(music_media_chain=music_media_chain)


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
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
    query_builder: QueryBuilderService = Depends(get_query_builder_service),
    host_search_resolver: HostSearchAdapterResolver = Depends(get_host_search_adapter_resolver),
    scorer: MusicCandidateScorer = Depends(get_candidate_scorer),
) -> SearchJobService:
    return SearchJobService(
        session,
        query_builder=query_builder,
        music_media_chain=music_media_chain,
        host_search_resolver=host_search_resolver,
        scorer=scorer,
        dispatch_service=DispatchService(
            session=session,
            resolver=get_dispatch_adapter_resolver(),
        ),
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
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> SubscriptionService:
    return SubscriptionService(
        session=session,
        music_media_chain=music_media_chain,
    )


def get_organize_service(
    session: Session = Depends(get_db_session),
    resolver: OrganizeAdapterResolver = Depends(get_organize_adapter_resolver),
    strategy_service: OrganizeStrategyService = Depends(get_organize_strategy_service),
    path_handoff_service: HostPathHandoffService = Depends(get_host_path_handoff_service),
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> OrganizeService:
    return OrganizeService(
        session=session,
        resolver=resolver,
        strategy_service=strategy_service,
        path_handoff_service=path_handoff_service,
        music_media_chain=music_media_chain,
    )


def get_subscription_execution_service(
    session: Session = Depends(get_db_session),
    search_job_service: SearchJobService = Depends(get_search_job_service),
    organize_service: OrganizeService = Depends(get_organize_service),
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
    dispatch_service: DispatchService = Depends(get_dispatch_service),
) -> SubscriptionExecutionService:
    return SubscriptionExecutionService(
        session=session,
        search_job_service=search_job_service,
        organize_service=organize_service,
        music_media_chain=music_media_chain,
        dispatch_service=dispatch_service,
    )


def build_subscription_execution_service(session: Session) -> SubscriptionExecutionService:
    metadata_service = MetadataService(session=session, adapter=get_metadata_provider_adapter())
    music_media_chain = MusicMediaChain(
        metadata_service=metadata_service,
        metadata_adapter=get_metadata_provider_adapter(),
    )
    search_job_service = SearchJobService(
        session,
        query_builder=QueryBuilderService(music_media_chain=music_media_chain),
        music_media_chain=music_media_chain,
        host_search_resolver=get_host_search_adapter_resolver(),
        scorer=get_candidate_scorer(),
        dispatch_service=DispatchService(
            session=session,
            resolver=get_dispatch_adapter_resolver(),
        ),
    )
    return SubscriptionExecutionService(
        session=session,
        search_job_service=search_job_service,
        organize_service=OrganizeService(
            session=session,
            resolver=get_organize_adapter_resolver(),
            strategy_service=get_organize_strategy_service(),
            path_handoff_service=get_host_path_handoff_service(),
            music_media_chain=music_media_chain,
        ),
        music_media_chain=music_media_chain,
        dispatch_service=DispatchService(
            session=session,
            resolver=get_dispatch_adapter_resolver(),
        ),
    )


def build_pending_handoff_reconcile_service(session: Session) -> PendingHandoffReconcileService:
    metadata_service = MetadataService(session=session, adapter=get_metadata_provider_adapter())
    music_media_chain = MusicMediaChain(
        metadata_service=metadata_service,
        metadata_adapter=get_metadata_provider_adapter(),
    )
    return PendingHandoffReconcileService(
        session=session,
        organize_service=OrganizeService(
            session=session,
            resolver=get_organize_adapter_resolver(),
            strategy_service=get_organize_strategy_service(),
            path_handoff_service=get_host_path_handoff_service(),
            music_media_chain=music_media_chain,
        ),
        path_handoff_service=get_host_path_handoff_service(),
        handoff_pending_ttl_seconds=settings.host_handoff_pending_ttl_seconds,
    )


def build_subscription_scheduler_service(session: Session) -> SubscriptionSchedulerService:
    execution_service = build_subscription_execution_service(session)
    pending_handoff_service = build_pending_handoff_reconcile_service(session)
    return SubscriptionSchedulerService(
        repository=OrchestrationRepository(session),
        execute_subscription=execution_service.execute,
        default_interval_minutes=settings.subscription_scheduler_default_interval_minutes,
        reconcile_pending_handoffs=pending_handoff_service.reconcile_pending_once,
    )


def get_session_factory():
    return SessionLocal
