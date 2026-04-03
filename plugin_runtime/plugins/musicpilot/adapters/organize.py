"""Adapter boundary for Phase 6 host-aware organize preview/apply flows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .host_http import HostHttpClient, HostTransportError
from ..core.config import Settings
from ..schemas.acquisition import PathHandoffInfo, SearchCandidateDetail
from ..schemas.integration import AdapterMode, AdapterResolution, AdapterStrategy, VerificationState
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeAdapterResult, OrganizePlan, OrganizeStatus


def _extract_candidate_path_handoff(candidate: SearchCandidateDetail) -> PathHandoffInfo | None:
    raw_payload = candidate.raw_payload or {}
    handoff = raw_payload.get("path_handoff")
    if not handoff:
        return None
    return PathHandoffInfo.model_validate(handoff)


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
            path_handoff=_extract_candidate_path_handoff(candidate),
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
            path_handoff=_extract_candidate_path_handoff(candidate),
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
    """MoviePilot transfer-backed organize adapter.

    Phase 7A verified that MoviePilot does not expose a native ``/organize/preview`` /
    ``/organize/apply`` pair. The closest real host semantics are:
    - ``GET /api/v1/transfer/name`` for naming preview.
    - ``POST /api/v1/transfer/manual`` for manual transfer/apply.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        client: HostHttpClient,
    ):
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
        return self._preview_once(
            candidate=candidate,
            metadata_detail=metadata_detail,
            binding_id=binding_id,
            plan=plan,
        )

    def _preview_once(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        source = self._resolve_source(candidate)
        if not source:
            raise HostTransportError(
                "MoviePilot transfer/name requires a downloaded local file path, but the current candidate/binding only contains remote torrent context.",
                reason_code="moviepilot_transfer_source_path_missing",
            )

        payload = self.client.get_json(
            self.settings.host_transfer_name_path or self.settings.host_organize_preview_path,
            params={"path": source["path"], "filetype": source["filetype"]},
            auth_mode="x_api_key",
        )
        success = bool(payload.get("success"))
        preview_name = self._extract_preview_name(payload)
        relative_path = self._merge_preview_name(plan.target_relative_path, preview_name) if preview_name else plan.target_relative_path
        return self._build_result(
            payload=payload,
            default_status=OrganizeStatus.PREVIEW_READY if success else OrganizeStatus.FAILED,
            default_note=(
                "当前 organize preview 映射到了真实 MoviePilot `/api/v1/transfer/name`。"
                "MoviePilot 只返回重命名后的 `name`，库路径仍由 MusicPilot 本地 organize strategy 负责。"
                "Phase 7B 已拿到真实正向命名样例。"
            ),
            integration_point="RealOrganizeAdapter.preview.moviepilot_transfer_name",
            plan=plan,
            capability_source="moviepilot.runtime.transfer.name",
            verification_state=VerificationState.VERIFIED,
            organizeable=success,
            target_relative_path=relative_path,
            path_handoff=_extract_candidate_path_handoff(candidate),
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
        return self._apply_once(
            organize_job_id=organize_job_id,
            candidate=candidate,
            metadata_detail=metadata_detail,
            binding_id=binding_id,
            plan=plan,
        )

    def _apply_once(
        self,
        *,
        organize_job_id: str,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None,
        plan: OrganizePlan,
    ) -> OrganizeAdapterResult:
        source = self._resolve_source(candidate)
        if not source:
            raise HostTransportError(
                "MoviePilot transfer/manual requires a downloaded local file path, but the current candidate/binding does not expose one.",
                reason_code="moviepilot_transfer_source_path_missing",
            )

        payload = self._build_manual_payload(
            candidate=candidate,
            source=source,
            plan=plan,
        )
        data = self.client.post_json(
            self.settings.host_transfer_manual_path or self.settings.host_organize_apply_path,
            payload,
            params={"background": "false"},
            auth_mode="x_api_key",
        )
        success = bool(data.get("success"))
        default_status = OrganizeStatus.APPLIED if success else OrganizeStatus.FAILED
        return self._build_result(
            payload=data,
            default_status=default_status,
            default_note=(
                "当前 organize apply 映射到了真实 MoviePilot `/api/v1/transfer/manual`。"
                "Phase 7B 已拿到真实 `success=true` 的最小手动整理样例。"
                "但真实文件移动、硬链接、刮削入库和媒体库刷新仍未被本仓库宣称为全部已验证。"
            ),
            integration_point="RealOrganizeAdapter.apply.moviepilot_transfer_manual",
            plan=plan,
            capability_source="moviepilot.runtime.transfer.manual",
            verification_state=VerificationState.VERIFIED,
            organizeable=success,
            path_handoff=_extract_candidate_path_handoff(candidate),
        )

    def _build_manual_payload(
        self,
        *,
        candidate: SearchCandidateDetail,
        source: dict[str, str],
        plan: OrganizePlan,
    ) -> dict[str, Any]:
        return {
            "fileitem": {
                "storage": source["storage"],
                "path": source["path"],
                "type": source["filetype"],
                "name": source["name"],
                "basename": source["basename"],
                "extension": source["extension"],
                "size": candidate.size_bytes,
            },
            "target_path": plan.target_library_path,
            "transfer_type": self.settings.organize_transfer_type,
            "scrape": False,
            "from_history": False,
        }

    def _build_result(
        self,
        *,
        payload: dict[str, Any],
        default_status: OrganizeStatus,
        default_note: str,
        integration_point: str,
        plan: OrganizePlan,
        capability_source: str,
        verification_state: VerificationState,
        organizeable: bool,
        target_relative_path: str | None = None,
        path_handoff: PathHandoffInfo | None = None,
    ) -> OrganizeAdapterResult:
        raw_status = payload.get("organize_status")
        organize_status = default_status
        if isinstance(raw_status, str):
            try:
                organize_status = OrganizeStatus(raw_status)
            except ValueError:
                organize_status = default_status

        return OrganizeAdapterResult(
            organizeable=bool(payload.get("organizeable", organizeable)),
            organize_backend=AdapterMode.HOST,
            adapter_mode=AdapterMode.HOST,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=organize_status,
            target_library_path=str(payload.get("target_library_path") or plan.target_library_path),
            target_relative_path=str(payload.get("target_relative_path") or target_relative_path or plan.target_relative_path),
            strategy_note=str(payload.get("strategy_note") or plan.strategy_note),
            integration_point=integration_point,
            capability_source=capability_source,
            failure_reason=self._optional_text(payload.get("failure_reason") or payload.get("message")),
            path_handoff=path_handoff,
            verification_state=verification_state,
            mock=False,
            note=str(payload.get("note") or default_note),
            adapter_resolution=AdapterResolution(
                adapter_key="real_organize",
                adapter_mode=AdapterMode.HOST,
                strategy=AdapterStrategy.PREFER_HOST,
                capability_source=capability_source,
                verification_state=verification_state,
                integration_point=integration_point,
                host_integration_enabled=self.settings.host_integration_enabled,
            ),
        )

    def _resolve_source(self, candidate: SearchCandidateDetail) -> dict[str, str] | None:
        raw_payload = candidate.raw_payload or {}
        for key in ("host_transfer_source", "source_fileitem"):
            fileitem = raw_payload.get(key)
            if isinstance(fileitem, dict) and fileitem.get("path"):
                path = str(fileitem["path"])
                return {
                    "storage": str(fileitem.get("storage") or "local"),
                    "path": path,
                    "filetype": str(fileitem.get("type") or "file"),
                    "name": str(fileitem.get("name") or path.rsplit("/", 1)[-1]),
                    "basename": str(fileitem.get("basename") or path.rsplit("/", 1)[-1].rsplit(".", 1)[0]),
                    "extension": str(fileitem.get("extension") or self._detect_extension(path)),
                }

        source_path = raw_payload.get("host_transfer_source_path") or raw_payload.get("local_file_path")
        if source_path:
            path = str(source_path)
            name = path.rsplit("/", 1)[-1]
            return {
                "storage": "local",
                "path": path,
                "filetype": str(raw_payload.get("host_transfer_filetype") or "file"),
                "name": name,
                "basename": name.rsplit(".", 1)[0],
                "extension": self._detect_extension(path),
            }
        handoff = raw_payload.get("path_handoff")
        if isinstance(handoff, dict) and handoff.get("source_path"):
            path = str(handoff["source_path"])
            name = str(handoff.get("source_name") or path.rsplit("/", 1)[-1])
            return {
                "storage": "local",
                "path": path,
                "filetype": str(handoff.get("source_filetype") or "file"),
                "name": name,
                "basename": str(handoff.get("source_basename") or name.rsplit(".", 1)[0]),
                "extension": str(handoff.get("source_extension") or self._detect_extension(path)),
            }
        return None

    def _extract_preview_name(self, payload: dict[str, Any]) -> str | None:
        data = payload.get("data")
        if isinstance(data, dict) and data.get("name"):
            return str(data["name"])
        return None

    def _merge_preview_name(self, target_relative_path: str, preview_name: str) -> str:
        if not target_relative_path or "/" not in target_relative_path:
            return preview_name
        parent = target_relative_path.rsplit("/", 1)[0]
        return f"{parent}/{preview_name}"

    def _detect_extension(self, path: str) -> str:
        name = path.rsplit("/", 1)[-1]
        if "." not in name:
            return ""
        return "." + name.rsplit(".", 1)[-1]

    def _optional_text(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
