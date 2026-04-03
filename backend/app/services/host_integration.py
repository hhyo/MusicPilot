"""Central host integration wiring and adapter resolution for Phase 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException

from ..adapters.download_dispatch import DownloadDispatchAdapter
from ..adapters.host_probe import HostProbeAdapter
from ..adapters.host_search import HostSearchAdapter
from ..adapters.organize import OrganizeAdapter
from ..core.config import Settings
from ..adapters.host_http import HostTransportError
from ..schemas.acquisition import DispatchAdapterResult, HostSearchCandidate, QueryBuildResult, SearchCandidateDetail
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterStrategy, HostIntegrationRuntimeState, VerificationState
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeAdapterResult, OrganizePlan, OrganizeStatus


@dataclass(slots=True)
class SearchExecutionResult:
    candidates: list[HostSearchCandidate]
    resolution: AdapterResolution


@dataclass(slots=True)
class DispatchExecutionResult:
    result: DispatchAdapterResult
    resolution: AdapterResolution


@dataclass(slots=True)
class OrganizeExecutionResult:
    result: OrganizeAdapterResult
    resolution: AdapterResolution


def _merge_resolution(current: AdapterResolution | None, fallback: AdapterResolution) -> AdapterResolution:
    if current is None:
        return fallback
    return fallback.model_copy(
        update={
            "capability_source": current.capability_source or fallback.capability_source,
            "verification_state": current.verification_state or fallback.verification_state,
            "fallback_reason": current.fallback_reason or fallback.fallback_reason,
            "integration_point": current.integration_point or fallback.integration_point,
        }
    )


def _build_runtime_error_reason(prefix: str, exc: Exception) -> str:
    if isinstance(exc, HostTransportError):
        return f"{prefix}:{exc.reason_code}"
    return f"{prefix}:{type(exc).__name__}"


class HostIntegrationService:
    def __init__(self, *, settings: Settings, probe_adapter: HostProbeAdapter):
        self.settings = settings
        self.probe_adapter = probe_adapter

    def runtime_state(self) -> HostIntegrationRuntimeState:
        host_enabled = self.settings.host_integration_enabled

        if not host_enabled:
            return HostIntegrationRuntimeState(
                host_integration_enabled=False,
                host_base_url=self.settings.host_base_url,
                verification_state=VerificationState.PLACEHOLDER,
                capability_source="settings.disabled",
                host_online=False,
                search_capability=False,
                dispatch_capability=False,
                organize_capability=False,
                downloaders_available=False,
                sites_visible=False,
                fallback_to_mock=self.settings.host_fallback_to_mock,
                search_strategy=AdapterStrategy(self.settings.host_search_strategy),
                dispatch_strategy=AdapterStrategy(self.settings.host_dispatch_strategy),
                organize_strategy=AdapterStrategy(self.settings.host_organize_strategy),
                active_search_adapter="mock_host_search",
                active_dispatch_adapter="mock_download_dispatch",
                active_organize_adapter="mock_organize",
                search_fallback_reason="host_integration_disabled",
                dispatch_fallback_reason="host_integration_disabled",
                organize_fallback_reason="host_integration_disabled",
                note="Host integration is disabled. MusicPilot will stay on mock adapters.",
            )

        health_payload = self.probe_adapter.probe_health()
        search_payload = self.probe_adapter.search_summary()
        sites_payload = self.probe_adapter.list_sites()
        downloaders_payload = self.probe_adapter.list_downloaders()

        host_online = self._resolve_bool(self.settings.host_assume_healthy, health_payload.summary.host_online)
        search_capability = self._resolve_bool(
            self.settings.host_assume_search_available,
            search_payload.summary.capability_available,
        )
        dispatch_capability = self._resolve_bool(
            self.settings.host_assume_dispatch_available,
            self._dispatch_capability_from_probe(downloaders_payload.summary.capability_available),
        )
        organize_capability = self._resolve_bool(
            self.settings.host_assume_organize_available,
            self._organize_capability_from_config(),
        )
        downloaders_available = self._resolve_bool(
            self.settings.host_assume_downloaders_available,
            downloaders_payload.summary.capability_available,
        )
        sites_visible = self._resolve_bool(
            self.settings.host_assume_sites_visible,
            sites_payload.summary.capability_available,
        )

        capability_source = self._resolve_capability_source(
            health_payload.summary.capability_source,
            used_override=any(
                value is not None
                for value in [
                    self.settings.host_assume_healthy,
                    self.settings.host_assume_search_available,
                    self.settings.host_assume_dispatch_available,
                    self.settings.host_assume_organize_available,
                    self.settings.host_assume_downloaders_available,
                    self.settings.host_assume_sites_visible,
                ]
            ),
        )

        search_resolution = self.resolve_search_strategy(
            search_capability=search_capability,
            capability_source=capability_source,
            preview_only=True,
        )
        dispatch_resolution = self.resolve_dispatch_strategy(
            dispatch_capability=dispatch_capability and downloaders_available,
            capability_source=capability_source,
            preview_only=True,
        )
        organize_resolution = self.resolve_organize_strategy(
            organize_capability=organize_capability,
            capability_source=capability_source,
            preview_only=True,
        )

        return HostIntegrationRuntimeState(
            host_integration_enabled=host_enabled,
            host_base_url=self.settings.host_base_url,
            verification_state=VerificationState(self.settings.host_verification_state),
            capability_source=capability_source,
            host_online=host_online,
            search_capability=search_capability,
            dispatch_capability=dispatch_capability,
            organize_capability=organize_capability,
            downloaders_available=downloaders_available,
            sites_visible=sites_visible,
            fallback_to_mock=self.settings.host_fallback_to_mock,
            search_strategy=AdapterStrategy(self.settings.host_search_strategy),
            dispatch_strategy=AdapterStrategy(self.settings.host_dispatch_strategy),
            organize_strategy=AdapterStrategy(self.settings.host_organize_strategy),
            active_search_adapter=search_resolution.adapter_key,
            active_dispatch_adapter=dispatch_resolution.adapter_key,
            active_organize_adapter=organize_resolution.adapter_key,
            search_fallback_reason=search_resolution.fallback_reason,
            dispatch_fallback_reason=dispatch_resolution.fallback_reason,
            organize_fallback_reason=organize_resolution.fallback_reason,
            note=(
                "Adapter wiring is resolved from host capability probe + settings. "
                "Host-backed adapters are only selected when capability and strategy allow it."
            ),
        )

    def resolve_search_strategy(
        self,
        *,
        search_capability: bool | None,
        capability_source: str,
        preview_only: bool = False,
    ) -> AdapterResolution:
        return self._resolve_strategy(
            adapter_key_host="real_host_search",
            adapter_key_mock="mock_host_search",
            strategy=AdapterStrategy(self.settings.host_search_strategy),
            capability_available=search_capability,
            capability_source=capability_source,
            integration_point="HostSearchAdapterResolver",
            preview_only=preview_only,
        )

    def resolve_dispatch_strategy(
        self,
        *,
        dispatch_capability: bool | None,
        capability_source: str,
        preview_only: bool = False,
    ) -> AdapterResolution:
        return self._resolve_strategy(
            adapter_key_host="real_download_dispatch",
            adapter_key_mock="mock_download_dispatch",
            strategy=AdapterStrategy(self.settings.host_dispatch_strategy),
            capability_available=dispatch_capability,
            capability_source=capability_source,
            integration_point="DispatchAdapterResolver",
            preview_only=preview_only,
        )

    def resolve_organize_strategy(
        self,
        *,
        organize_capability: bool | None,
        capability_source: str,
        preview_only: bool = False,
    ) -> AdapterResolution:
        return self._resolve_strategy(
            adapter_key_host="real_organize",
            adapter_key_mock="mock_organize",
            strategy=AdapterStrategy(self.settings.host_organize_strategy),
            capability_available=organize_capability,
            capability_source=capability_source,
            integration_point="OrganizeAdapterResolver",
            preview_only=preview_only,
        )

    def _resolve_strategy(
        self,
        *,
        adapter_key_host: str,
        adapter_key_mock: str,
        strategy: AdapterStrategy,
        capability_available: bool | None,
        capability_source: str,
        integration_point: str,
        preview_only: bool,
    ) -> AdapterResolution:
        verification_state = VerificationState(self.settings.host_verification_state)

        if strategy == AdapterStrategy.MOCK:
            return AdapterResolution(
                adapter_key=adapter_key_mock,
                adapter_mode=AdapterMode.MOCK,
                strategy=strategy,
                capability_source="settings.strategy.mock",
                verification_state=VerificationState.PLACEHOLDER,
                integration_point=integration_point,
                host_integration_enabled=self.settings.host_integration_enabled,
                fallback_reason="strategy_forced_mock",
            )

        if not self.settings.host_integration_enabled:
            return self._mock_resolution(
                adapter_key_mock=adapter_key_mock,
                strategy=strategy,
                capability_source="settings.disabled",
                integration_point=integration_point,
                fallback_reason="host_integration_disabled",
            )

        if capability_available is True:
            return AdapterResolution(
                adapter_key=adapter_key_host,
                adapter_mode=AdapterMode.HOST,
                strategy=strategy,
                capability_source=capability_source,
                verification_state=verification_state,
                integration_point=integration_point,
                host_integration_enabled=True,
            )

        fallback_reason = "host_capability_unavailable" if capability_available is False else "host_capability_unknown"
        if strategy == AdapterStrategy.STRICT_HOST or not self.settings.host_fallback_to_mock:
            if preview_only:
                blocking_reason = (
                    f"strict_host_required:{fallback_reason}"
                    if strategy == AdapterStrategy.STRICT_HOST
                    else f"host_required_without_mock_fallback:{fallback_reason}"
                )
                return AdapterResolution(
                    adapter_key=adapter_key_host,
                    adapter_mode=AdapterMode.HOST,
                    strategy=strategy,
                    capability_source=capability_source,
                    verification_state=verification_state,
                    fallback_reason=blocking_reason,
                    integration_point=integration_point,
                    host_integration_enabled=self.settings.host_integration_enabled,
                )
            raise HTTPException(
                status_code=503,
                detail=(
                    f"{integration_point} requires host-backed capability, but current state is unavailable: "
                    f"{fallback_reason}."
                ),
            )

        return self._mock_resolution(
            adapter_key_mock=adapter_key_mock,
            strategy=strategy,
            capability_source=capability_source,
            integration_point=integration_point,
            fallback_reason=fallback_reason,
        )

    def _mock_resolution(
        self,
        *,
        adapter_key_mock: str,
        strategy: AdapterStrategy,
        capability_source: str,
        integration_point: str,
        fallback_reason: str,
    ) -> AdapterResolution:
        return AdapterResolution(
            adapter_key=adapter_key_mock,
            adapter_mode=AdapterMode.MOCK,
            strategy=strategy,
            capability_source=capability_source,
            verification_state=VerificationState.PLACEHOLDER,
            fallback_reason=fallback_reason,
            integration_point=integration_point,
            host_integration_enabled=self.settings.host_integration_enabled,
        )

    def _dispatch_capability_from_probe(self, value: bool | None) -> bool | None:
        if self.settings.host_dispatch_path or self.settings.host_download_add_path:
            return value if value is not None else True
        return value

    def _organize_capability_from_config(self) -> bool | None:
        has_any_path = bool(
            self.settings.host_transfer_name_path
            or self.settings.host_transfer_manual_path
            or self.settings.host_organize_preview_path
            or self.settings.host_organize_apply_path
        )
        has_endpoint = bool(self.settings.host_base_url and has_any_path)
        if has_endpoint:
            return True
        if has_any_path:
            return False
        return False

    def _resolve_bool(self, override: bool | None, probe_value: bool | None) -> bool | None:
        if override is not None:
            return override
        return probe_value

    def _resolve_capability_source(self, probe_source: str, *, used_override: bool) -> str:
        if used_override:
            return "config.override"
        return probe_source


class HostSearchAdapterResolver:
    def __init__(
        self,
        *,
        integration_service: HostIntegrationService,
        mock_adapter: HostSearchAdapter,
        host_adapter: HostSearchAdapter,
    ):
        self.integration_service = integration_service
        self.mock_adapter = mock_adapter
        self.host_adapter = host_adapter

    def search(self, *, query_build: QueryBuildResult, detail: MetadataDetail) -> SearchExecutionResult:
        runtime_state = self.integration_service.runtime_state()
        resolution = self.integration_service.resolve_search_strategy(
            search_capability=runtime_state.search_capability,
            capability_source=runtime_state.capability_source,
        )
        adapter = self.host_adapter if resolution.adapter_mode == AdapterMode.HOST else self.mock_adapter

        try:
            candidates = adapter.search(query_build=query_build, detail=detail)
        except Exception as exc:
            if resolution.adapter_mode == AdapterMode.HOST and resolution.strategy == AdapterStrategy.PREFER_HOST and self.integration_service.settings.host_fallback_to_mock:
                fallback_resolution = AdapterResolution(
                    adapter_key="mock_host_search",
                    adapter_mode=AdapterMode.MOCK,
                    strategy=resolution.strategy,
                    capability_source=runtime_state.capability_source,
                    verification_state=VerificationState.PLACEHOLDER,
                    fallback_reason=_build_runtime_error_reason("host_search_runtime_error", exc),
                    integration_point="HostSearchAdapterResolver",
                    host_integration_enabled=self.integration_service.settings.host_integration_enabled,
                )
                candidates = self.mock_adapter.search(query_build=query_build, detail=detail)
                return SearchExecutionResult(
                    candidates=[self._apply_resolution(candidate, fallback_resolution) for candidate in candidates],
                    resolution=fallback_resolution,
                )
            raise HTTPException(
                status_code=503,
                detail=f"Host-backed search adapter failed and no safe fallback was allowed: {exc}",
            ) from exc

        return SearchExecutionResult(
            candidates=[self._apply_resolution(candidate, resolution) for candidate in candidates],
            resolution=resolution,
        )

    def _apply_resolution(self, candidate: HostSearchCandidate, resolution: AdapterResolution) -> HostSearchCandidate:
        effective_resolution = resolution
        if candidate.adapter_resolution is not None:
            effective_resolution = resolution.model_copy(
                update={
                    "capability_source": candidate.adapter_resolution.capability_source or resolution.capability_source,
                    "verification_state": candidate.adapter_resolution.verification_state or resolution.verification_state,
                    "fallback_reason": candidate.adapter_resolution.fallback_reason or resolution.fallback_reason,
                    "integration_point": candidate.adapter_resolution.integration_point or resolution.integration_point,
                }
            )
        candidate.adapter_resolution = effective_resolution
        candidate.mock = effective_resolution.adapter_mode == AdapterMode.MOCK
        if effective_resolution.fallback_reason:
            candidate.note = f"{candidate.note} Fallback reason: {effective_resolution.fallback_reason}."
        candidate.raw_payload = {
            **(candidate.raw_payload or {}),
            "adapter_resolution": effective_resolution.model_dump(mode="json"),
        }
        return candidate


class DispatchAdapterResolver:
    def __init__(
        self,
        *,
        integration_service: HostIntegrationService,
        mock_adapter: DownloadDispatchAdapter,
        host_adapter: DownloadDispatchAdapter,
    ):
        self.integration_service = integration_service
        self.mock_adapter = mock_adapter
        self.host_adapter = host_adapter

    def dispatch(
        self,
        *,
        candidate: SearchCandidateDetail,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DispatchExecutionResult:
        runtime_state = self.integration_service.runtime_state()
        resolution = self.integration_service.resolve_dispatch_strategy(
            dispatch_capability=runtime_state.dispatch_capability and runtime_state.downloaders_available,
            capability_source=runtime_state.capability_source,
        )
        adapter = self.host_adapter if resolution.adapter_mode == AdapterMode.HOST else self.mock_adapter

        try:
            result = adapter.dispatch(
                candidate=candidate,
                downloader_id=downloader_id,
                manual_confirm=manual_confirm,
            )
        except Exception as exc:
            if resolution.adapter_mode == AdapterMode.HOST and resolution.strategy == AdapterStrategy.PREFER_HOST and self.integration_service.settings.host_fallback_to_mock:
                fallback_resolution = AdapterResolution(
                    adapter_key="mock_download_dispatch",
                    adapter_mode=AdapterMode.MOCK,
                    strategy=resolution.strategy,
                    capability_source=runtime_state.capability_source,
                    verification_state=VerificationState.PLACEHOLDER,
                    fallback_reason=_build_runtime_error_reason("host_dispatch_runtime_error", exc),
                    integration_point="DispatchAdapterResolver",
                    host_integration_enabled=self.integration_service.settings.host_integration_enabled,
                )
                fallback_result = self.mock_adapter.dispatch(
                    candidate=candidate,
                    downloader_id=downloader_id,
                    manual_confirm=manual_confirm,
                )
                fallback_result.adapter_resolution = fallback_resolution
                fallback_result.dispatch_backend = AdapterMode.MOCK
                fallback_result.capability_source = runtime_state.capability_source
                fallback_result.fallback_reason = fallback_resolution.fallback_reason
                fallback_result.verification_state = VerificationState.PLACEHOLDER
                fallback_result.note = f"{fallback_result.note} Fallback reason: {fallback_resolution.fallback_reason}."
                return DispatchExecutionResult(result=fallback_result, resolution=fallback_resolution)
            raise HTTPException(
                status_code=503,
                detail=f"Host-backed dispatch adapter failed and no safe fallback was allowed: {exc}",
            ) from exc

        result.adapter_resolution = _merge_resolution(result.adapter_resolution, resolution)
        result.dispatch_backend = result.adapter_resolution.adapter_mode
        result.capability_source = result.capability_source or result.adapter_resolution.capability_source
        result.fallback_reason = result.fallback_reason or result.adapter_resolution.fallback_reason
        result.verification_state = result.adapter_resolution.verification_state
        return DispatchExecutionResult(result=result, resolution=resolution)


class OrganizeAdapterResolver:
    def __init__(
        self,
        *,
        integration_service: HostIntegrationService,
        mock_adapter: OrganizeAdapter,
        host_adapter: OrganizeAdapter,
    ):
        self.integration_service = integration_service
        self.mock_adapter = mock_adapter
        self.host_adapter = host_adapter

    def preview(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
    ) -> OrganizeExecutionResult:
        runtime_state = self.integration_service.runtime_state()
        resolution = self.integration_service.resolve_organize_strategy(
            organize_capability=runtime_state.organize_capability,
            capability_source=runtime_state.capability_source,
        )
        adapter = self.host_adapter if resolution.adapter_mode == AdapterMode.HOST else self.mock_adapter

        try:
            result = adapter.preview(
                candidate=candidate,
                metadata_detail=metadata_detail,
                binding_id=binding_id,
                plan=plan,
            )
        except Exception as exc:
            return self._fallback_preview(
                resolution=resolution,
                runtime_state=runtime_state,
                candidate=candidate,
                metadata_detail=metadata_detail,
                binding_id=binding_id,
                plan=plan,
                exc=exc,
            )

        return self._finalize_result(result=result, resolution=resolution, runtime_state=runtime_state)

    def apply(
        self,
        *,
        organize_job_id: str,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
    ) -> OrganizeExecutionResult:
        runtime_state = self.integration_service.runtime_state()
        resolution = self.integration_service.resolve_organize_strategy(
            organize_capability=runtime_state.organize_capability,
            capability_source=runtime_state.capability_source,
        )
        adapter = self.host_adapter if resolution.adapter_mode == AdapterMode.HOST else self.mock_adapter

        try:
            result = adapter.apply(
                organize_job_id=organize_job_id,
                candidate=candidate,
                metadata_detail=metadata_detail,
                binding_id=binding_id,
                plan=plan,
            )
        except Exception as exc:
            return self._fallback_apply(
                resolution=resolution,
                runtime_state=runtime_state,
                organize_job_id=organize_job_id,
                candidate=candidate,
                metadata_detail=metadata_detail,
                binding_id=binding_id,
                plan=plan,
                exc=exc,
            )

        return self._finalize_result(result=result, resolution=resolution, runtime_state=runtime_state)

    def _fallback_preview(
        self,
        *,
        resolution: AdapterResolution,
        runtime_state: HostIntegrationRuntimeState,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
        exc: Exception,
    ) -> OrganizeExecutionResult:
        if resolution.adapter_mode == AdapterMode.HOST and resolution.strategy == AdapterStrategy.PREFER_HOST and self.integration_service.settings.host_fallback_to_mock:
            fallback_resolution = AdapterResolution(
                adapter_key="mock_organize",
                adapter_mode=AdapterMode.MOCK,
                strategy=resolution.strategy,
                capability_source=runtime_state.capability_source,
                verification_state=VerificationState.PLACEHOLDER,
                    fallback_reason=_build_runtime_error_reason("host_organize_preview_runtime_error", exc),
                integration_point="OrganizeAdapterResolver.preview",
                host_integration_enabled=self.integration_service.settings.host_integration_enabled,
            )
            result = self.mock_adapter.preview(
                candidate=candidate,
                metadata_detail=metadata_detail,
                binding_id=binding_id,
                plan=plan,
            )
            return self._finalize_result(result=result, resolution=fallback_resolution, runtime_state=runtime_state)

        raise HTTPException(
            status_code=503,
            detail=f"Host-backed organize preview failed and no safe fallback was allowed: {exc}",
        ) from exc

    def _fallback_apply(
        self,
        *,
        resolution: AdapterResolution,
        runtime_state: HostIntegrationRuntimeState,
        organize_job_id: str,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
        exc: Exception,
    ) -> OrganizeExecutionResult:
        if resolution.adapter_mode == AdapterMode.HOST and resolution.strategy == AdapterStrategy.PREFER_HOST and self.integration_service.settings.host_fallback_to_mock:
            fallback_resolution = AdapterResolution(
                adapter_key="mock_organize",
                adapter_mode=AdapterMode.MOCK,
                strategy=resolution.strategy,
                capability_source=runtime_state.capability_source,
                verification_state=VerificationState.PLACEHOLDER,
                    fallback_reason=_build_runtime_error_reason("host_organize_apply_runtime_error", exc),
                integration_point="OrganizeAdapterResolver.apply",
                host_integration_enabled=self.integration_service.settings.host_integration_enabled,
            )
            result = self.mock_adapter.apply(
                organize_job_id=organize_job_id,
                candidate=candidate,
                metadata_detail=metadata_detail,
                binding_id=binding_id,
                plan=plan,
            )
            result.organize_status = OrganizeStatus.FALLBACK_APPLIED
            return self._finalize_result(result=result, resolution=fallback_resolution, runtime_state=runtime_state)

        raise HTTPException(
            status_code=503,
            detail=f"Host-backed organize apply failed and no safe fallback was allowed: {exc}",
        ) from exc

    def _finalize_result(
        self,
        *,
        result: OrganizeAdapterResult,
        resolution: AdapterResolution,
        runtime_state: HostIntegrationRuntimeState,
    ) -> OrganizeExecutionResult:
        merged_resolution = _merge_resolution(result.adapter_resolution, resolution)
        result.organize_backend = merged_resolution.adapter_mode
        result.adapter_mode = merged_resolution.adapter_mode
        result.capability_source = result.capability_source or merged_resolution.capability_source or runtime_state.capability_source
        result.fallback_reason = result.fallback_reason or merged_resolution.fallback_reason
        result.verification_state = merged_resolution.verification_state
        result.adapter_resolution = merged_resolution
        result.mock = merged_resolution.adapter_mode == AdapterMode.MOCK
        if result.fallback_reason:
            result.note = f"{result.note} Fallback reason: {result.fallback_reason}."
        return OrganizeExecutionResult(result=result, resolution=resolution)
