"""Matrix-aware runtime strategy decisions for host-backed dispatch and organize flows."""

from __future__ import annotations

from typing import Any

from ..schemas.acquisition import PathHandoffInfo, SearchCandidateDetail
from ..schemas.strategy import HostStrategyDecision, HostStrategySummary
from ..schemas.validation import HostValidationMatrixReport
from .validation_matrix import HostValidationMatrixService


class HostStrategyService:
    def __init__(self, validation_matrix_service: HostValidationMatrixService | None = None):
        self.validation_matrix_service = validation_matrix_service

    def summary(self) -> HostStrategySummary:
        report = self._report()
        note = (
            "Phase 9 默认策略会优先沿用验证矩阵里更稳的 handoff / organize 路径。"
            "当前 `history/transfer` 是 organize replay/fallback 的稳定优先来源；"
            "`download_add` 仅有 single-sample 成功，因此只做谨慎优先；"
            "`download_media + history/download -> organize apply` 已知会被真实宿主重复阻断。"
        )
        if report is None:
            note = (
                "当前未加载到 Phase 8 验证矩阵，策略会退回保守默认值：优先 transfer handoff，"
                "对 host organize apply 保持谨慎。"
            )
        return HostStrategySummary(
            preferred_dispatch_endpoint="download_add",
            preferred_handoff_source="resolved_from_history_transfer",
            preferred_organize_path="history.transfer -> organize apply",
            caution_paths=[
                "download_add + resolved_from_history_download -> organize apply",
            ],
            blocked_paths=[
                "download_media + resolved_from_history_download -> organize apply",
            ],
            note=note,
        )

    def recommend_dispatch(self, candidate: SearchCandidateDetail) -> HostStrategyDecision:
        has_media_reference = self._extract_media_reference(candidate) is not None
        if has_media_reference:
            return HostStrategyDecision(
                stage="dispatch_endpoint",
                selected_path="download_add",
                matrix_status="single_sample",
                risk_level="medium",
                recommended_action="prefer_with_caution",
                reason=(
                    "当前唯一完整真实成功闭环来自 `download_add -> history/download -> transfer/manual`。"
                    "因此在有 media reference 时，Phase 9 默认更偏向 `download_add`。"
                ),
                note=(
                    "这是更适合演示和试运行的 host dispatch 默认路径，但它仍只有单样例真实成功，"
                    "不应被当作多样例稳定成功。"
                ),
                blocked=False,
                source_sample_ids=self._sample_ids(lambda item: item.sample_id == "ordinary_accident_title_add"),
            )

        return HostStrategyDecision(
            stage="dispatch_endpoint",
            selected_path="download_media",
            matrix_status="blocked",
            risk_level="blocked",
            recommended_action="dispatch_only_or_manual_follow_up",
            reason=(
                "当缺少可复用的 media reference 时，仍只能走 `download_media`。"
                "但 Phase 8 已确认这条路径还没有形成稳定的 organize 成功闭环。"
            ),
            note=(
                "该路径可以继续保留给 host dispatch 能力验证，但默认不应再被包装成稳定可整理路径。"
            ),
            blocked=False,
            source_sample_ids=self._sample_ids(
                lambda item: item.dispatch_endpoint_type == "download_media"
            ),
        )

    def evaluate_handoff(
        self,
        *,
        handoff: PathHandoffInfo | None,
        dispatch_endpoint_type: str | None,
    ) -> HostStrategyDecision:
        if handoff is None:
            return HostStrategyDecision(
                stage="path_handoff",
                selected_path="handoff_missing",
                matrix_status="unknown",
                risk_level="high",
                recommended_action="wait_or_retry",
                reason="当前还没有可用的 host path handoff，无法把 organize apply 视作可执行路径。",
                note="请等待宿主 history 同步，或改用已存在的 transfer history replay 路径。",
                blocked=False,
            )

        if handoff.handoff_status == "resolved_from_history_transfer":
            return HostStrategyDecision(
                stage="path_handoff",
                selected_path="resolved_from_history_transfer",
                matrix_status="stable",
                risk_level="low",
                recommended_action="prefer",
                reason="Phase 8 已证明 `history/transfer` 是当前最稳定的 organize replay/fallback 来源。",
                note="当 transfer history 可用时，应优先使用它，而不是继续沿用 history/download 结果。",
                blocked=False,
                source_sample_ids=self._sample_ids(
                    lambda item: item.path_handoff_status == "resolved_from_history_transfer"
                ),
            )

        if handoff.handoff_status == "pending_history_sync":
            return HostStrategyDecision(
                stage="path_handoff",
                selected_path="pending_history_sync",
                matrix_status="unknown",
                risk_level="high",
                recommended_action="retry_history_sync",
                reason="宿主下载已接受，但 history 还没同步出可用路径。",
                note="当前建议等待重试窗口结束，再决定是否继续 organize。",
                blocked=False,
            )

        if handoff.handoff_status == "handoff_unresolved":
            return HostStrategyDecision(
                stage="path_handoff",
                selected_path="handoff_unresolved",
                matrix_status="blocked",
                risk_level="blocked",
                recommended_action="stop_and_report",
                reason="download/transfer history 都没有给出可用路径，当前 organize host apply 缺少输入。",
                note="这种情况不应继续静默尝试 host organize。",
                blocked=True,
            )

        if handoff.handoff_status == "resolved_from_history_download":
            if dispatch_endpoint_type == "download_add":
                return HostStrategyDecision(
                    stage="path_handoff",
                    selected_path="resolved_from_history_download",
                    matrix_status="single_sample",
                    risk_level="medium",
                    recommended_action="allow_manual_caution",
                    reason="该 handoff 来源配合 `download_add` 有 1 条真实成功样例，但还不具备稳定性。",
                    note="可以继续保留，但默认应带风险提示，并优先寻找可替代的 transfer history 记录。",
                    blocked=False,
                    source_sample_ids=self._sample_ids(
                        lambda item: item.sample_id == "ordinary_accident_title_add"
                    ),
                )

            return HostStrategyDecision(
                stage="path_handoff",
                selected_path="resolved_from_history_download",
                matrix_status="blocked",
                risk_level="blocked",
                recommended_action="prefer_transfer_replay",
                reason="Phase 8 已确认 `download_media + history/download` 在 host organize apply 上会重复被真实宿主阻断。",
                note="如果能命中 transfer history，应切到它；否则只建议保留 preview，不建议继续 apply。",
                blocked=True,
                source_sample_ids=self._sample_ids(
                    lambda item: item.dispatch_endpoint_type == "download_media"
                    and item.path_handoff_status == "resolved_from_history_download"
                ),
            )

        return HostStrategyDecision(
            stage="path_handoff",
            selected_path=handoff.handoff_status,
            matrix_status="unknown",
            risk_level="medium",
            recommended_action="manual_review",
            reason="当前 handoff 状态不在已知矩阵规则中，需要人工确认。",
            note="保守策略是不要把它视作稳定 organize 来源。",
            blocked=False,
        )

    def evaluate_organize_apply(
        self,
        *,
        handoff: PathHandoffInfo | None,
        dispatch_endpoint_type: str | None,
    ) -> HostStrategyDecision:
        handoff_decision = self.evaluate_handoff(
            handoff=handoff,
            dispatch_endpoint_type=dispatch_endpoint_type,
        )
        if handoff_decision.blocked:
            return HostStrategyDecision(
                stage="organize_apply",
                selected_path=handoff_decision.selected_path,
                matrix_status=handoff_decision.matrix_status,
                risk_level=handoff_decision.risk_level,
                recommended_action="block_apply",
                reason=handoff_decision.reason,
                note="Phase 9 会在真正触发 host apply 前显式阻断这条已知高风险组合。",
                blocked=True,
                source_sample_ids=handoff_decision.source_sample_ids,
            )

        if handoff_decision.matrix_status == "stable":
            return HostStrategyDecision(
                stage="organize_apply",
                selected_path="history.transfer -> organize_apply",
                matrix_status="stable",
                risk_level="low",
                recommended_action="allow_preferred",
                reason="当前组合在真实矩阵中已形成多样例稳定成功。",
                note="这是当前最推荐的 host organize 路径。",
                blocked=False,
                source_sample_ids=handoff_decision.source_sample_ids,
            )

        if handoff_decision.matrix_status == "single_sample":
            return HostStrategyDecision(
                stage="organize_apply",
                selected_path="history.download -> organize_apply",
                matrix_status="single_sample",
                risk_level="medium",
                recommended_action="allow_manual_caution",
                reason="当前组合只有单条真实成功样例，适合人工确认和演示，不适合当成稳定默认。",
                note="Phase 9 会继续允许它，但不会把它包装成稳态成功路径。",
                blocked=False,
                source_sample_ids=handoff_decision.source_sample_ids,
            )

        return HostStrategyDecision(
            stage="organize_apply",
            selected_path=handoff_decision.selected_path,
            matrix_status=handoff_decision.matrix_status,
            risk_level="high",
            recommended_action="manual_review",
            reason=handoff_decision.reason,
            note="当前没有足够矩阵依据把这条 organize apply 视为稳定可交付路径。",
            blocked=False,
            source_sample_ids=handoff_decision.source_sample_ids,
        )

    def _report(self) -> HostValidationMatrixReport | None:
        if self.validation_matrix_service is None:
            return None
        return self.validation_matrix_service.load_report()

    def _sample_ids(self, predicate) -> list[str]:  # noqa: ANN001
        report = self._report()
        if report is None:
            return []
        return [item.sample_id for item in report.samples if predicate(item)]

    def _extract_media_reference(self, candidate: SearchCandidateDetail) -> dict[str, Any] | None:
        payload = candidate.raw_payload or {}
        reference = payload.get("host_media_reference")
        if isinstance(reference, dict) and any(reference.get(key) for key in ("tmdbid", "tmdb_id", "doubanid", "douban_id")):
            return reference
        context = payload.get("host_context")
        if isinstance(context, dict):
            media = context.get("media_info")
            if isinstance(media, dict) and any(media.get(key) for key in ("tmdbid", "tmdb_id", "doubanid", "douban_id")):
                return media
        return None

    def extract_dispatch_endpoint_type(self, payload: dict[str, Any] | None) -> str | None:
        if not payload:
            return None
        summary = payload.get("host_response_summary")
        if isinstance(summary, dict) and summary.get("endpoint_type"):
            return str(summary["endpoint_type"])
        strategy = payload.get("strategy_decision")
        if isinstance(strategy, dict) and strategy.get("stage") == "dispatch_endpoint" and strategy.get("selected_path"):
            return str(strategy["selected_path"])
        return None
