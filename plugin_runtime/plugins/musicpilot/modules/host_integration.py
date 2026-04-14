"""Host integration wiring aligned with MoviePilot-style module support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException

from ..core.config import Settings
from ..modules.download_dispatch import DownloadDispatchAdapter
from ..modules.host_http import HostTransportError
from ..modules.host_probe import HostProbeAdapter
from ..modules.host_search import HostSearchAdapter
from ..modules.organize import OrganizeAdapter
from ..schemas.acquisition import DispatchAdapterResult, HostSearchCandidate, QueryBuildResult, SearchCandidateDetail
from ..schemas.integration import (
    AdapterMode,
    AdapterResolution,
    AdapterSelectionMode,
    HostIntegrationRuntimeState,
    VerificationState,
)
from ..schemas.metadata import MetadataDetail
from ..schemas.music_media import MusicMediaInfo
from ..schemas.orchestration import OrganizeAdapterResult, OrganizePlan


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


class HostIntegrationModule:
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
                search_mode=AdapterSelectionMode(self.settings.host_search_mode),
                dispatch_mode=AdapterSelectionMode(self.settings.host_dispatch_mode),
                organize_mode=AdapterSelectionMode(self.settings.host_organize_mode),
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

        search_resolution = self.resolve_search_mode(
            search_capability=search_capability,
            capability_source=capability_source,
            preview_only=True,
        )
        dispatch_resolution = self.resolve_dispatch_mode(
            dispatch_capability=dispatch_capability and downloaders_available,
            capability_source=capability_source,
            preview_only=True,
        )
        organize_resolution = self.resolve_organize_mode(
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
            search_mode=AdapterSelectionMode(self.settings.host_search_mode),
            dispatch_mode=AdapterSelectionMode(self.settings.host_dispatch_mode),
            organize_mode=AdapterSelectionMode(self.settings.host_organize_mode),
            active_search_adapter=search_resolution.adapter_key,
            active_dispatch_adapter=dispatch_resolution.adapter_key,
            active_organize_adapter=organize_resolution.adapter_key,
            search_fallback_reason=search_resolution.fallback_reason,
            dispatch_fallback_reason=dispatch_resolution.fallback_reason,
            organize_fallback_reason=organize_resolution.fallback_reason,
            note=(
                "Adapter wiring is resolved from host capability probe + settings. "
                "Mock mode is only used when explicitly configured or when host integration is disabled."
            ),
        )

    def resolve_search_mode(
        self,
        *,
        search_capability: bool | None,
        capability_source: str,
        preview_only: bool = False,
    ) -> AdapterResolution:
        return self._resolve_mode(
            adapter_key_host="real_host_search",
            adapter_key_mock="mock_host_search",
            selection_mode=AdapterSelectionMode(self.settings.host_search_mode),
            capability_available=search_capability,
            capability_source=capability_source,
            integration_point="HostSearchAdapterResolver",
            preview_only=preview_only,
        )

    def resolve_dispatch_mode(
        self,
        *,
        dispatch_capability: bool | None,
        capability_source: str,
        preview_only: bool = False,
    ) -> AdapterResolution:
        return self._resolve_mode(
            adapter_key_host="real_download_dispatch",
            adapter_key_mock="mock_download_dispatch",
            selection_mode=AdapterSelectionMode(self.settings.host_dispatch_mode),
            capability_available=dispatch_capability,
            capability_source=capability_source,
            integration_point="DispatchAdapterResolver",
            preview_only=preview_only,
        )

    def resolve_organize_mode(
        self,
        *,
        organize_capability: bool | None,
        capability_source: str,
        preview_only: bool = False,
    ) -> AdapterResolution:
        return self._resolve_mode(
            adapter_key_host="real_organize",
            adapter_key_mock="mock_organize",
            selection_mode=AdapterSelectionMode(self.settings.host_organize_mode),
            capability_available=organize_capability,
            capability_source=capability_source,
            integration_point="OrganizeAdapterResolver",
            preview_only=preview_only,
        )

    def run_host_search(
        self,
        *,
        resolver: Callable[[AdapterResolution], HostSearchAdapter],
        query: QueryBuildResult,
        music_media_info: MusicMediaInfo,
    ) -> SearchExecutionResult:
        runtime = self.runtime_state()
        resolution = self.resolve_search_mode(
            search_capability=runtime.search_capability,
            capability_source=runtime.capability_source,
        )
        adapter = resolver(resolution)
        try:
            result = adapter.search(query=query, music_media_info=music_media_info)
        except Exception as exc:  # noqa: BLE001
            fallback = resolution.model_copy(update={"fallback_reason": _build_runtime_error_reason("search_error", exc)})
            if resolution.adapter_mode == AdapterMode.HOST and resolution.selection_mode != AdapterSelectionMode.STRICT_HOST:
                adapter = resolver(
                    self._mock_resolution(
                        adapter_key_mock="mock_host_search",
                        selection_mode=resolution.selection_mode,
                        capability_source=runtime.capability_source,
                        integration_point="HostSearchAdapterResolver",
                        fallback_reason=fallback.fallback_reason,
                    )
                )
                result = adapter.search(query=query, music_media_info=music_media_info)
                return SearchExecutionResult(candidates=result, resolution=_merge_resolution(resolution, fallback))
            raise
        return SearchExecutionResult(candidates=result, resolution=resolution)

    def run_download_dispatch(
        self,
        *,
        resolver: Callable[[AdapterResolution], DownloadDispatchAdapter],
        candidate,
        downloader_id: str,
    ) -> DispatchExecutionResult:
        runtime = self.runtime_state()
        resolution = self.resolve_dispatch_mode(
            dispatch_capability=runtime.dispatch_capability and runtime.downloaders_available,
            capability_source=runtime.capability_source,
        )
        adapter = resolver(resolution)
        try:
            result = adapter.dispatch(candidate=candidate, downloader_id=downloader_id)
        except Exception as exc:  # noqa: BLE001
            fallback = resolution.model_copy(
                update={"fallback_reason": _build_runtime_error_reason("dispatch_error", exc)}
            )
            if resolution.adapter_mode == AdapterMode.HOST and resolution.selection_mode != AdapterSelectionMode.STRICT_HOST:
                adapter = resolver(
                    self._mock_resolution(
                        adapter_key_mock="mock_download_dispatch",
                        selection_mode=resolution.selection_mode,
                        capability_source=runtime.capability_source,
                        integration_point="DispatchAdapterResolver",
                        fallback_reason=fallback.fallback_reason,
                    )
                )
                result = adapter.dispatch(candidate=candidate, downloader_id=downloader_id)
                return DispatchExecutionResult(result=result, resolution=_merge_resolution(resolution, fallback))
            raise
        return DispatchExecutionResult(result=result, resolution=resolution)

    def run_organize(
        self,
        *,
        resolver: Callable[[AdapterResolution], OrganizeAdapter],
        plan: OrganizePlan,
    ) -> OrganizeExecutionResult:
        runtime = self.runtime_state()
        resolution = self.resolve_organize_mode(
            organize_capability=runtime.organize_capability,
            capability_source=runtime.capability_source,
        )
        adapter = resolver(resolution)
        try:
            result = adapter.execute(plan=plan)
        except Exception as exc:  # noqa: BLE001
            fallback = resolution.model_copy(update={"fallback_reason": _build_runtime_error_reason("organize_error", exc)})
            if resolution.adapter_mode == AdapterMode.HOST and resolution.selection_mode != AdapterSelectionMode.STRICT_HOST:
                adapter = resolver(
                    self._mock_resolution(
                        adapter_key_mock="mock_organize",
                        selection_mode=resolution.selection_mode,
                        capability_source=runtime.capability_source,
                        integration_point="OrganizeAdapterResolver",
                        fallback_reason=fallback.fallback_reason,
                    )
                )
                result = adapter.execute(plan=plan)
                return OrganizeExecutionResult(result=result, resolution=_merge_resolution(resolution, fallback))
            raise
        return OrganizeExecutionResult(result=result, resolution=resolution)

    def _resolve_mode(
        self,
        *,
        adapter_key_host: str,
        adapter_key_mock: str,
        selection_mode: AdapterSelectionMode,
        capability_available: bool | None,
        capability_source: str,
        integration_point: str,
        preview_only: bool,
    ) -> AdapterResolution:
        verification_state = VerificationState(self.settings.host_verification_state)

        if selection_mode == AdapterSelectionMode.MOCK:
            return AdapterResolution(
                adapter_key=adapter_key_mock,
                adapter_mode=AdapterMode.MOCK,
                selection_mode=selection_mode,
                capability_source="settings.mode.mock",
                verification_state=VerificationState.PLACEHOLDER,
                integration_point=integration_point,
                host_integration_enabled=self.settings.host_integration_enabled,
                fallback_reason="mode_forced_mock",
            )

        if not self.settings.host_integration_enabled:
            return self._mock_resolution(
                adapter_key_mock=adapter_key_mock,
                selection_mode=selection_mode,
                capability_source="settings.disabled",
                integration_point=integration_point,
                fallback_reason="host_integration_disabled",
            )

        if capability_available is True:
            return AdapterResolution(
                adapter_key=adapter_key_host,
                adapter_mode=AdapterMode.HOST,
                selection_mode=selection_mode,
                capability_source=capability_source,
                verification_state=verification_state,
                integration_point=integration_point,
                host_integration_enabled=True,
            )

        fallback_reason = "host_capability_unavailable" if capability_available is False else "host_capability_unknown"
        if preview_only:
            blocking_reason = (
                f"strict_host_required:{fallback_reason}"
                if selection_mode == AdapterSelectionMode.STRICT_HOST
                else fallback_reason
            )
            return AdapterResolution(
                adapter_key=adapter_key_host,
                adapter_mode=AdapterMode.HOST,
                selection_mode=selection_mode,
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

    def _mock_resolution(
        self,
        *,
        adapter_key_mock: str,
        selection_mode: AdapterSelectionMode,
        capability_source: str,
        integration_point: str,
        fallback_reason: str,
    ) -> AdapterResolution:
        return AdapterResolution(
            adapter_key=adapter_key_mock,
            adapter_mode=AdapterMode.MOCK,
            selection_mode=selection_mode,
            capability_source=capability_source,
            verification_state=VerificationState.PLACEHOLDER,
            fallback_reason=fallback_reason,
            integration_point=integration_point,
            host_integration_enabled=self.settings.host_integration_enabled,
        )

    def _dispatch_capability_from_probe(self, value: bool | None) -> bool | None:
        if self.settings.host_download_add_path:
            return value if value is not None else True
        return value

    def _organize_capability_from_config(self) -> bool | None:
        return False

    def _resolve_bool(self, override: bool | None, value: bool | None) -> bool | None:
        if override is not None:
            return override
        return value

    def _resolve_capability_source(self, default_source: str | None, *, used_override: bool) -> str:
        if used_override:
            return "settings.override"
        return default_source or "host.probe"


class HostSearchAdapterResolver:
    def __init__(
        self,
        *,
        integration_module: HostIntegrationModule,
        mock_adapter: HostSearchAdapter,
        host_adapter: HostSearchAdapter,
    ):
        self.integration_module = integration_module
        self.mock_adapter = mock_adapter
        self.host_adapter = host_adapter

    def search(self, *, query_build: QueryBuildResult, media: MusicMediaInfo) -> SearchExecutionResult:
        runtime_state = self.integration_module.runtime_state()
        resolution = self.integration_module.resolve_search_mode(
            search_capability=runtime_state.search_capability,
            capability_source=runtime_state.capability_source,
        )
        adapter = self.host_adapter if resolution.adapter_mode == AdapterMode.HOST else self.mock_adapter
        try:
            candidates = adapter.search(query_build=query_build, media=media)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Host-backed search adapter failed: "
                    f"{_build_runtime_error_reason('host_search_runtime_error', exc)}"
                ),
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
        integration_module: HostIntegrationModule,
        mock_adapter: DownloadDispatchAdapter,
        host_adapter: DownloadDispatchAdapter,
    ):
        self.integration_module = integration_module
        self.mock_adapter = mock_adapter
        self.host_adapter = host_adapter

    def dispatch(
        self,
        *,
        candidate: SearchCandidateDetail,
        downloader_id: str,
        manual_confirm: bool,
    ) -> DispatchExecutionResult:
        runtime_state = self.integration_module.runtime_state()
        resolution = self.integration_module.resolve_dispatch_mode(
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
            raise HTTPException(
                status_code=503,
                detail=(
                    "Host-backed dispatch adapter failed: "
                    f"{_build_runtime_error_reason('host_dispatch_runtime_error', exc)}"
                ),
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
        integration_module: HostIntegrationModule,
        mock_adapter: OrganizeAdapter,
        host_adapter: OrganizeAdapter,
    ):
        self.integration_module = integration_module
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
        runtime_state = self.integration_module.runtime_state()
        resolution = self.integration_module.resolve_organize_mode(
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
            raise HTTPException(
                status_code=503,
                detail=(
                    "Host-backed organize preview failed: "
                    f"{_build_runtime_error_reason('host_organize_preview_runtime_error', exc)}"
                ),
            ) from exc

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
        runtime_state = self.integration_module.runtime_state()
        resolution = self.integration_module.resolve_organize_mode(
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
            raise HTTPException(
                status_code=503,
                detail=(
                    "Host-backed organize apply failed: "
                    f"{_build_runtime_error_reason('host_organize_apply_runtime_error', exc)}"
                ),
            ) from exc

        return self._finalize_result(result=result, resolution=resolution, runtime_state=runtime_state)

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

    def _resolve_mode(
        self,
        *,
        adapter_key_host: str,
        adapter_key_mock: str,
        selection_mode: AdapterSelectionMode,
        capability_available: bool | None,
        capability_source: str,
        integration_point: str,
        preview_only: bool,
    ) -> AdapterResolution:
        verification_state = VerificationState(self.settings.host_verification_state)

        if selection_mode == AdapterSelectionMode.MOCK:
            return AdapterResolution(
                adapter_key=adapter_key_mock,
                adapter_mode=AdapterMode.MOCK,
                selection_mode=selection_mode,
                capability_source="settings.mode.mock",
                verification_state=VerificationState.PLACEHOLDER,
                integration_point=integration_point,
                host_integration_enabled=self.settings.host_integration_enabled,
                fallback_reason="mode_forced_mock",
            )

        if not self.settings.host_integration_enabled:
            return self._mock_resolution(
                adapter_key_mock=adapter_key_mock,
                selection_mode=selection_mode,
                capability_source="settings.disabled",
                integration_point=integration_point,
                fallback_reason="host_integration_disabled",
            )

        if capability_available is True:
            return AdapterResolution(
                adapter_key=adapter_key_host,
                adapter_mode=AdapterMode.HOST,
                selection_mode=selection_mode,
                capability_source=capability_source,
                verification_state=verification_state,
                integration_point=integration_point,
                host_integration_enabled=True,
            )

        fallback_reason = "host_capability_unavailable" if capability_available is False else "host_capability_unknown"
        if preview_only:
            blocking_reason = (
                f"strict_host_required:{fallback_reason}"
                if selection_mode == AdapterSelectionMode.STRICT_HOST
                else fallback_reason
            )
            return AdapterResolution(
                adapter_key=adapter_key_host,
                adapter_mode=AdapterMode.HOST,
                selection_mode=selection_mode,
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

    def _mock_resolution(
        self,
        *,
        adapter_key_mock: str,
        selection_mode: AdapterSelectionMode,
        capability_source: str,
        integration_point: str,
        fallback_reason: str,
    ) -> AdapterResolution:
        return AdapterResolution(
            adapter_key=adapter_key_mock,
            adapter_mode=AdapterMode.MOCK,
            selection_mode=selection_mode,
            capability_source=capability_source,
            verification_state=VerificationState.PLACEHOLDER,
            fallback_reason=fallback_reason,
            integration_point=integration_point,
            host_integration_enabled=self.settings.host_integration_enabled,
        )

    def _dispatch_capability_from_probe(self, value: bool | None) -> bool | None:
        if self.settings.host_download_add_path:
            return value if value is not None else True
        return value

    def _organize_capability_from_config(self) -> bool | None:
        return True if self.settings.host_transfer_manual_path else None

    def _resolve_bool(self, override: bool | None, value: bool | None) -> bool | None:
        if override is not None:
            return override
        return value

    def _resolve_capability_source(self, default_source: str | None, *, used_override: bool) -> str:
        if used_override:
            return "settings.override"
        return default_source or "host.probe"
