"""Adapter boundary for Phase 6 host-aware organize preview/apply flows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .host_http import HostHttpClient
from ..core.config import Settings
from ..schemas.acquisition import SearchCandidateDetail
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterStrategy, VerificationState
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeAdapterResult, OrganizePlan, OrganizeStatus


class OrganizeAdapter(ABC):
    @abstractmethod
    def preview(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        """Build an organize preview for the current candidate or binding."""

    @abstractmethod
    def apply(
        self,
        *,
        organize_job_id: str,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        """Apply an organize plan through either mock or host-backed boundary."""


class MockOrganizeAdapter(OrganizeAdapter):
    def preview(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        binding_hint = f" via binding {binding_id}" if binding_id else ""
        return OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=OrganizeStatus.PREVIEW_READY,
            target_library_path=plan.target_library_path,
            target_relative_path=plan.target_relative_path,
            strategy_note=(
                f"{plan.strategy_note} Current mock preview only simulates target path resolution{binding_hint}."
            ),
            integration_point=(
                "Replace MockOrganizeAdapter with a verified MoviePilot organize adapter after organize preview/apply "
                "request and response contracts are confirmed."
            ),
            capability_source="mock.adapter",
            verification_state=VerificationState.PLACEHOLDER,
            mock=True,
            note=(
                "当前为 mock organize preview。它只验证命名与目录映射，不执行真实文件移动、硬链接、"
                "刮削入库或媒体库刷新。"
            ),
            adapter_resolution=AdapterResolution(
                adapter_key="mock_organize",
                adapter_mode=AdapterMode.MOCK,
                strategy=AdapterStrategy.MOCK,
                capability_source="mock.adapter",
                verification_state=VerificationState.PLACEHOLDER,
                integration_point="MockOrganizeAdapter.preview",
                host_integration_enabled=False,
            ),
        )

    def apply(
        self,
        *,
        organize_job_id: str,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        binding_hint = f" via binding {binding_id}" if binding_id else ""
        return OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=OrganizeStatus.APPLIED,
            target_library_path=plan.target_library_path,
            target_relative_path=plan.target_relative_path,
            strategy_note=(
                f"{plan.strategy_note} Mock apply records an applied state for organize job {organize_job_id}{binding_hint}."
            ),
            integration_point=(
                "Replace MockOrganizeAdapter.apply with a verified MoviePilot organize apply adapter after host "
                "library path mapping and media library refresh semantics are confirmed."
            ),
            capability_source="mock.adapter",
            verification_state=VerificationState.PLACEHOLDER,
            mock=True,
            note=(
                "当前为 mock organize apply。它只更新状态记录，不会真实执行文件移动、硬链接、刮削或媒体库刷新。"
            ),
            adapter_resolution=AdapterResolution(
                adapter_key="mock_organize",
                adapter_mode=AdapterMode.MOCK,
                strategy=AdapterStrategy.MOCK,
                capability_source="mock.adapter",
                verification_state=VerificationState.PLACEHOLDER,
                integration_point="MockOrganizeAdapter.apply",
                host_integration_enabled=False,
            ),
        )


class RealOrganizeAdapter(OrganizeAdapter):
    """Host-backed organize preview/apply skeleton for Phase 6."""

    def __init__(self, *, settings: Settings, client: HostHttpClient):
        self.settings = settings
        self.client = client

    def preview(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        payload = self._build_payload(
            candidate=candidate,
            metadata_detail=metadata_detail,
            binding_id=binding_id,
            plan=plan,
            organize_job_id=None,
        )
        data = self.client.post_json(self.settings.host_organize_preview_path, payload)
        return self._build_result(
            payload=data,
            default_status=OrganizeStatus.PREVIEW_READY,
            default_note=(
                "当前 organize preview 来自 configured host organize preview endpoint。字段映射与状态解释仍需真实 "
                "MoviePilot 宿主联调确认。"
            ),
            integration_point="RealOrganizeAdapter.preview",
            plan=plan,
        )

    def apply(
        self,
        *,
        organize_job_id: str,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        payload = self._build_payload(
            candidate=candidate,
            metadata_detail=metadata_detail,
            binding_id=binding_id,
            plan=plan,
            organize_job_id=organize_job_id,
        )
        data = self.client.post_json(self.settings.host_organize_apply_path, payload)
        default_status = OrganizeStatus.APPLY_PENDING
        if bool(data.get("applied", False)):
            default_status = OrganizeStatus.APPLIED
        return self._build_result(
            payload=data,
            default_status=default_status,
            default_note=(
                "当前 organize apply 来自 configured host organize apply endpoint。请求构造与响应解析已落为可联调骨架，"
                "但真实 MoviePilot 文件处理与媒体库刷新语义仍需联调确认。"
            ),
            integration_point="RealOrganizeAdapter.apply",
            plan=plan,
        )

    def _build_payload(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
        organize_job_id: str | None,
    ) -> dict[str, Any]:
        return {
            "organize_job_id": organize_job_id,
            "binding_id": binding_id,
            "candidate": candidate.model_dump(mode="json"),
            "metadata": metadata_detail.model_dump(mode="json") if metadata_detail else None,
            "plan": plan.model_dump(mode="json"),
        }

    def _build_result(
        self,
        *,
        payload: dict[str, Any],
        default_status: OrganizeStatus,
        default_note: str,
        integration_point: str,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        raw_status = payload.get("organize_status")
        organize_status = default_status
        if isinstance(raw_status, str):
            try:
                organize_status = OrganizeStatus(raw_status)
            except ValueError:
                organize_status = default_status

        return OrganizeAdapterResult(
            organizeable=bool(payload.get("organizeable", True)),
            organize_backend=AdapterMode.HOST,
            adapter_mode=AdapterMode.HOST,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=organize_status,
            target_library_path=str(payload.get("target_library_path") or plan.target_library_path),
            target_relative_path=str(payload.get("target_relative_path") or plan.target_relative_path),
            strategy_note=str(payload.get("strategy_note") or plan.strategy_note),
            integration_point=integration_point,
            capability_source="host.endpoint",
            failure_reason=self._optional_text(payload.get("failure_reason")),
            verification_state=VerificationState(self.settings.host_verification_state),
            mock=False,
            note=str(payload.get("note") or default_note),
            adapter_resolution=AdapterResolution(
                adapter_key="real_organize",
                adapter_mode=AdapterMode.HOST,
                strategy=AdapterStrategy.PREFER_HOST,
                capability_source="host.endpoint",
                verification_state=VerificationState(self.settings.host_verification_state),
                integration_point=integration_point,
                host_integration_enabled=self.settings.host_integration_enabled,
            ),
        )

    def _optional_text(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
