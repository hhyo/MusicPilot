"""Dependency providers for MusicPilot backend chains and support objects."""

from __future__ import annotations

import json
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..chain.chart import MusicChartChain
from ..chain.dashboard import MusicDashboardChain
from ..chain.download import MusicDownloadChain
from ..chain.media import MusicMediaChain
from ..chain.search import MusicSearchChain
from ..chain.subscribe import MusicSubscribeChain
from ..chain.system import MusicSystemChain
from ..chain.transfer import MusicTransferChain
from ..core.db import SessionLocal, get_db_session
from ..core.config import settings
from ..core.runtime_cache import stable_cache_key
from ..db.charts_oper import ChartsOper
from ..db.orchestration_oper import OrchestrationOper
from ..helper.discovery import MusicDiscoveryBuilder
from ..helper.organize_strategy import MusicOrganizeStrategy
from ..helper.query_builder import MusicQueryBuilder
from ..helper.scoring import MusicCandidateScorer
from ..helper.settings import SettingsHelper
from ..helper.validation_matrix import HostValidationMatrixHelper
from ..modules.chart_provider import (
    ChartProviderAdapter,
    ListenBrainzChartProviderAdapter,
    MockChartProviderAdapter,
    RssFeedChartProviderAdapter,
)
from ..modules.download_dispatch import DownloadDispatchAdapter, MockDownloadDispatchAdapter, RealDownloadDispatchAdapter
from ..modules.host_downloader_runtime import HostDownloaderRuntimeBridge
from ..modules.host_http import HostHttpClient, HostHttpClientConfig
from ..modules.host_integration import DispatchAdapterResolver, HostIntegrationModule, HostSearchAdapterResolver, OrganizeAdapterResolver
from ..modules.host_probe import HostProbeAdapter, MockHostProbeAdapter, RealHostProbeAdapter
from ..modules.host_search import HostSearchAdapter, MockHostSearchAdapter, RealHostSearchAdapter
from ..modules.host_storage_runtime import HostStorageRuntimeBridge
from ..modules.metadata import MetadataModule
from ..modules.metadata_provider import MetadataProviderAdapter, MockMetadataProviderAdapter, MusicBrainzMetadataProviderAdapter
from ..modules.organize import MockOrganizeAdapter, OrganizeAdapter, RealOrganizeAdapter
from ..modules.path_handoff import HostPathHandoff


def get_settings_helper(session: Session = Depends(get_db_session)) -> SettingsHelper:
    return SettingsHelper(session=session, env_settings=settings)


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
    settings_helper: SettingsHelper = Depends(get_settings_helper),
) -> ChartProviderAdapter:
    _ = session
    provider_settings = settings_helper.provider_settings()
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
def get_host_integration_module() -> HostIntegrationModule:
    return HostIntegrationModule(settings=settings, probe_adapter=get_host_probe_adapter())


@lru_cache
def get_host_path_handoff_service() -> HostPathHandoff:
    return HostPathHandoff(settings=settings, client=get_host_http_client())


@lru_cache
def get_validation_matrix_helper() -> HostValidationMatrixHelper:
    return HostValidationMatrixHelper(settings=settings)


def get_metadata_module(
    session: Session = Depends(get_db_session),
    adapter: MetadataProviderAdapter = Depends(get_metadata_provider_adapter),
) -> MetadataModule:
    return MetadataModule(session=session, provider=adapter)


def get_music_media_chain(
    metadata_module: MetadataModule = Depends(get_metadata_module),
    provider: MetadataProviderAdapter = Depends(get_metadata_provider_adapter),
) -> MusicMediaChain:
    return MusicMediaChain(metadata_module=metadata_module, metadata_provider=provider)


def get_music_dashboard_chain(
    session: Session = Depends(get_db_session),
) -> MusicDashboardChain:
    return MusicDashboardChain(session=session)


def get_music_system_chain(
    session: Session = Depends(get_db_session),
) -> MusicSystemChain:
    return MusicSystemChain(
        settings_helper=SettingsHelper(session=session, env_settings=settings),
        host_probe=get_host_probe_adapter(),
        host_integration=get_host_integration_module(),
        validation_matrix=get_validation_matrix_helper(),
    )


def get_discovery_builder(
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> MusicDiscoveryBuilder:
    return MusicDiscoveryBuilder(music_media_chain=music_media_chain)


def build_music_chart_chain(session: Session) -> MusicChartChain:
    settings_helper = SettingsHelper(session=session, env_settings=settings)
    metadata_module = MetadataModule(session=session, provider=get_metadata_provider_adapter())
    music_media_chain = MusicMediaChain(
        metadata_module=metadata_module,
        metadata_provider=get_metadata_provider_adapter(),
    )
    discovery_assembler = MusicDiscoveryBuilder(music_media_chain=music_media_chain)
    adapter = get_chart_provider_adapter(session=session, settings_helper=settings_helper)
    return MusicChartChain(
        adapter=adapter,
        discovery_assembler=discovery_assembler,
        settings_oper=None,
        charts_oper=ChartsOper(session),
        env_settings=settings,
    )


def get_music_chart_chain(
    adapter: ChartProviderAdapter = Depends(get_chart_provider_adapter),
    discovery_assembler: MusicDiscoveryBuilder = Depends(get_discovery_builder),
    session: Session = Depends(get_db_session),
) -> MusicChartChain:
    return MusicChartChain(
        adapter=adapter,
        discovery_assembler=discovery_assembler,
        settings_oper=None,
        charts_oper=ChartsOper(session),
        env_settings=settings,
    )


def get_music_query_builder(
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> MusicQueryBuilder:
    return MusicQueryBuilder(music_media_chain=music_media_chain)


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
        integration_module=get_host_integration_module(),
        mock_adapter=get_host_search_adapter(),
        host_adapter=get_real_host_search_adapter(),
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
def get_organize_strategy_service() -> MusicOrganizeStrategy:
    return MusicOrganizeStrategy(settings=settings)


@lru_cache
def get_dispatch_adapter_resolver() -> DispatchAdapterResolver:
    return DispatchAdapterResolver(
        integration_module=get_host_integration_module(),
        mock_adapter=get_download_dispatch_adapter(),
        host_adapter=get_real_download_dispatch_adapter(),
    )


def get_music_download_chain(
    session: Session = Depends(get_db_session),
    resolver: DispatchAdapterResolver = Depends(get_dispatch_adapter_resolver),
    path_handoff_service: HostPathHandoff = Depends(get_host_path_handoff_service),
) -> MusicDownloadChain:
    return MusicDownloadChain(
        session=session,
        resolver=resolver,
        path_handoff_service=path_handoff_service,
    )


def get_music_search_chain(
    session: Session = Depends(get_db_session),
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
    query_builder: MusicQueryBuilder = Depends(get_music_query_builder),
    host_search_resolver: HostSearchAdapterResolver = Depends(get_host_search_adapter_resolver),
    scorer: MusicCandidateScorer = Depends(get_candidate_scorer),
) -> MusicSearchChain:
    download_chain = MusicDownloadChain(
        session=session,
        resolver=get_dispatch_adapter_resolver(),
        path_handoff_service=get_host_path_handoff_service(),
    )
    return MusicSearchChain(
        session=session,
        query_builder=query_builder,
        music_media_chain=music_media_chain,
        host_search_resolver=host_search_resolver,
        scorer=scorer,
        dispatch_service=download_chain,
    )


@lru_cache
def get_organize_adapter_resolver() -> OrganizeAdapterResolver:
    return OrganizeAdapterResolver(
        integration_module=get_host_integration_module(),
        mock_adapter=get_organize_adapter(),
        host_adapter=get_real_organize_adapter(),
    )


def get_music_transfer_chain(
    session: Session = Depends(get_db_session),
    resolver: OrganizeAdapterResolver = Depends(get_organize_adapter_resolver),
    strategy_service: MusicOrganizeStrategy = Depends(get_organize_strategy_service),
    path_handoff_service: HostPathHandoff = Depends(get_host_path_handoff_service),
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
) -> MusicTransferChain:
    return MusicTransferChain(
        session=session,
        resolver=resolver,
        strategy_service=strategy_service,
        path_handoff_service=path_handoff_service,
        music_media_chain=music_media_chain,
        handoff_pending_ttl_seconds=settings.host_handoff_pending_ttl_seconds,
    )


def get_music_subscribe_chain(
    session: Session = Depends(get_db_session),
    music_media_chain: MusicMediaChain = Depends(get_music_media_chain),
    search_chain: MusicSearchChain = Depends(get_music_search_chain),
    download_chain: MusicDownloadChain = Depends(get_music_download_chain),
    transfer_chain: MusicTransferChain = Depends(get_music_transfer_chain),
) -> MusicSubscribeChain:
    return MusicSubscribeChain(
        session=session,
        music_media_chain=music_media_chain,
        search_chain=search_chain,
        download_chain=download_chain,
        transfer_chain=transfer_chain,
        default_interval_minutes=settings.subscription_scheduler_default_interval_minutes,
    )


def build_music_subscribe_chain(session: Session) -> MusicSubscribeChain:
    metadata_module = MetadataModule(session=session, provider=get_metadata_provider_adapter())
    music_media_chain = MusicMediaChain(
        metadata_module=metadata_module,
        metadata_provider=get_metadata_provider_adapter(),
    )
    download_chain = MusicDownloadChain(
        session=session,
        resolver=get_dispatch_adapter_resolver(),
        path_handoff_service=get_host_path_handoff_service(),
    )
    search_chain = MusicSearchChain(
        session=session,
        query_builder=MusicQueryBuilder(music_media_chain=music_media_chain),
        music_media_chain=music_media_chain,
        host_search_resolver=get_host_search_adapter_resolver(),
        scorer=get_candidate_scorer(),
        dispatch_service=download_chain,
    )
    transfer_chain = MusicTransferChain(
        session=session,
        resolver=get_organize_adapter_resolver(),
        strategy_service=get_organize_strategy_service(),
        path_handoff_service=get_host_path_handoff_service(),
        music_media_chain=music_media_chain,
        handoff_pending_ttl_seconds=settings.host_handoff_pending_ttl_seconds,
    )
    return MusicSubscribeChain(
        session=session,
        music_media_chain=music_media_chain,
        search_chain=search_chain,
        download_chain=download_chain,
        transfer_chain=transfer_chain,
        default_interval_minutes=settings.subscription_scheduler_default_interval_minutes,
    )


def build_music_transfer_chain(session: Session) -> MusicTransferChain:
    metadata_module = MetadataModule(session=session, provider=get_metadata_provider_adapter())
    music_media_chain = MusicMediaChain(
        metadata_module=metadata_module,
        metadata_provider=get_metadata_provider_adapter(),
    )
    return MusicTransferChain(
        session=session,
        resolver=get_organize_adapter_resolver(),
        strategy_service=get_organize_strategy_service(),
        path_handoff_service=get_host_path_handoff_service(),
        music_media_chain=music_media_chain,
        handoff_pending_ttl_seconds=settings.host_handoff_pending_ttl_seconds,
    )


def get_session_factory():
    return SessionLocal
