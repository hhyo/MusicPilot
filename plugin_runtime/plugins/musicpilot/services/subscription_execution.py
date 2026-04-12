"""Subscription execution orchestration for Phase 6."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.orchestration import OrchestrationRepository
from ..schemas.acquisition import DispatchRequest, QueryPreferences, SearchCandidateDetail, SearchJobCreateRequest
from ..schemas.music_media import MusicMediaInfo, MusicMediaInput
from ..schemas.mvp import DecisionStatus, EntityType, JobStatus, TriggerSource
from ..schemas.orchestration import (
    OrganizeApplyRequest,
    OrganizeStatus,
    OrganizePreviewRequest,
    SubscriptionRunDetail,
    SubscriptionRunListData,
    SubscriptionRunStatus,
    SubscriptionState,
    SubscriptionSummary,
    SubscriptionType,
)
from .dispatch import DispatchService
from .organize import OrganizeService
from .search_job import SearchJobService
from .subscriptions import serialize_run_summary, serialize_subscription


RUN_NOTE = (
    "当前订阅执行器会在手动 run 或最小应用内 scheduler 触发下，同步创建并执行一次 SearchJob，"
    "对最佳 AUTO_DOWNLOAD 候选会继续自动派发并生成 organize preview；"
    "若 preview 已拿到明确本地源文件，则继续自动 apply。"
    "真实 organize apply 仍按 capability 与 adapter 模式选择 host 或 mock。"
)


class SubscriptionExecutionService:
    def __init__(
        self,
        session: Session,
        *,
        search_job_service: SearchJobService,
        organize_service: OrganizeService,
        music_media_chain,
        dispatch_service: DispatchService | None = None,
    ):
        self.session = session
        self.search_job_service = search_job_service
        self.organize_service = organize_service
        self.music_media_chain = music_media_chain
        self.dispatch_service = dispatch_service
        self.repository = OrchestrationRepository(session)

    def execute(self, subscription_id: str) -> SubscriptionRunDetail:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")
        if subscription.status == SubscriptionState.ARCHIVED.value:
            raise HTTPException(status_code=400, detail="Archived subscription can not be executed.")

        run = self.repository.create_run(subscription, note=RUN_NOTE)
        self.repository.mark_run_running(run)
        self.session.flush()

        try:
            job_payload = self._build_job_request(subscription)
            created_job = self.search_job_service.create_job(job_payload)
            executed_job = self.search_job_service.execute_job(created_job.id)
            candidates_data = self.search_job_service.list_candidates(executed_job.id)

            organize_preview = None
            execution_status = self._map_run_status(executed_job.status).value
            summary = {
                "best_score": executed_job.summary.get("best_score", 0.0),
                "candidate_count": candidates_data.total,
                "mock_host_search": executed_job.mock,
                "search_outcome_reason": None,
                "organize_preview_id": None,
                "organize_backend": None,
                "organize_fallback_reason": None,
                "dispatch_status": None,
                "dispatch_backend": None,
                "binding_id": None,
                "last_dispatched_candidate_id": None,
            }
            if candidates_data.total == 0:
                summary["search_outcome_reason"] = self._search_outcome_reason(executed_job)
            if candidates_data.items:
                auto_candidate = self._select_auto_dispatch_candidate(candidates_data.items)
                if auto_candidate is not None and self.dispatch_service is not None:
                    dispatch_result = self.dispatch_service.dispatch(
                        DispatchRequest(
                            result_id=auto_candidate.id,
                            downloader_id=self._resolve_downloader_id(subscription),
                            manual_confirm=True,
                        )
                    )
                    summary.update(
                        {
                            "dispatch_status": dispatch_result.dispatch_status,
                            "dispatch_backend": dispatch_result.dispatch_backend.value,
                            "binding_id": dispatch_result.binding_id,
                            "last_dispatched_candidate_id": dispatch_result.candidate_id,
                        }
                    )
                    if dispatch_result.binding_id:
                        organize_preview = self.organize_service.preview(
                            OrganizePreviewRequest(binding_id=dispatch_result.binding_id),
                            subscription_run_id=run.id,
                        )
                    else:
                        organize_preview = self.organize_service.preview_for_candidate(
                            candidate_id=auto_candidate.id,
                            subscription_run_id=run.id,
                        )
                    if dispatch_result.dispatchable:
                        execution_status = SubscriptionRunStatus.DISPATCHED.value
                        if organize_preview is not None and self._should_auto_apply(organize_preview, auto_candidate):
                            organize_preview = self.organize_service.apply(
                                OrganizeApplyRequest(organize_job_id=organize_preview.id)
                            )
                            execution_status = SubscriptionRunStatus.APPLIED.value
                else:
                    organize_preview = self.organize_service.preview_for_candidate(
                        candidate_id=candidates_data.items[0].id,
                        subscription_run_id=run.id,
                    )
            if organize_preview is not None:
                summary.update(
                    {
                        "organize_preview_id": organize_preview.id,
                        "organize_backend": organize_preview.organize_backend.value,
                        "organize_fallback_reason": organize_preview.fallback_reason,
                    }
                )

            self.repository.mark_run_finished(
                run,
                execution_status=execution_status,
                matched_candidates_count=candidates_data.total,
                summary_json=summary,
                search_job_id=executed_job.id,
                organize_record_id=organize_preview.id if organize_preview else None,
            )
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            failed_run = self.repository.get_run(run.id)
            if failed_run is not None:
                self.repository.mark_run_finished(
                    failed_run,
                    execution_status=SubscriptionRunStatus.FAILED.value,
                    matched_candidates_count=0,
                    summary_json={"candidate_count": 0},
                    error_message=str(exc),
                )
                self.session.commit()
            raise

        return self.get_run_detail(run.id)

    def list_runs(self, subscription_id: str) -> SubscriptionRunListData:
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")
        items = [serialize_run_summary(run) for run in self.repository.list_runs(subscription_id)]
        return SubscriptionRunListData(
            subscription_id=subscription_id,
            items=items,
            total=len(items),
            mock=False,
            note="当前 run 记录反映的是手动或最小应用内 scheduler 触发的同步执行结果。",
        )

    def get_run_detail(self, run_id: str) -> SubscriptionRunDetail:
        run = self.repository.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Subscription run {run_id} was not found.")

        subscription_summary = serialize_subscription(run.subscription)
        metadata_target = self._resolve_metadata_target(run.subscription)
        search_job = (
            self.search_job_service.get_job(run.search_job_id) if run.search_job_id else None
        )
        candidates = (
            self.search_job_service.list_candidates(run.search_job_id).items if run.search_job_id else []
        )
        organize_preview = (
            self.organize_service.get_record(run.organize_record_id) if run.organize_record_id else None
        )

        return SubscriptionRunDetail(
            **serialize_run_summary(run).model_dump(),
            subscription=subscription_summary,
            metadata_target=metadata_target,
            search_job=search_job,
            candidates=candidates,
            organize_preview=organize_preview,
        )

    def _build_job_request(self, subscription) -> SearchJobCreateRequest:
        preferences = QueryPreferences.model_validate(subscription.preference_json or {})
        media_input = self._resolve_music_media_input_snapshot(subscription)
        if media_input is None:
            media_info = self._resolve_or_build_music_media_info(subscription)
            if media_info is not None:
                media_input = self.music_media_chain.input_from_music_media_info(
                    media_info,
                    source_kind="subscription",
                    source_context={
                        "subscription_id": subscription.id,
                        "subscription_type": subscription.subscription_type,
                    },
                    raw_context={"target_id": subscription.target_id},
                )

        if media_input is None:
            media_input = self._build_subscription_provider_input(
                subscription,
                source_kind="subscription",
            )
        return SearchJobCreateRequest(
            input=media_input,
            trigger_source=TriggerSource.SUBSCRIPTION,
            profile_id="default-lossless",
            mode="manual" if subscription.mode == "manual" else "auto",
            preferences=preferences,
        )

    def _resolve_metadata_target(self, subscription) -> MetadataDetail | None:
        media_input = self._resolve_music_media_input_snapshot(subscription)
        if media_input is None:
            media_info = self._resolve_or_build_music_media_info(subscription)
            if media_info is not None:
                media_input = self.music_media_chain.input_from_music_media_info(
                    media_info,
                    source_kind="subscription_detail",
                    source_context={"subscription_id": subscription.id},
                    raw_context={"target_id": subscription.target_id},
                )
        if media_input is None:
            media_input = self._build_subscription_provider_input(
                subscription,
                source_kind="subscription_detail",
            )
        return self.music_media_chain.resolve_detail(media_input).detail

    def _resolve_or_build_music_media_info(self, subscription) -> MusicMediaInfo | None:
        media_info = self._resolve_music_media_info_snapshot(subscription)
        if media_info is not None and media_info.provider_id:
            return media_info

        media_input = self._resolve_music_media_input_snapshot(subscription)
        if media_input is None:
            media_input = self._build_subscription_provider_input(
                subscription,
                source_kind="subscription_resolution",
            )

        resolved = self.music_media_chain.resolve(media_input)
        payload = dict(subscription.target_payload_json or {})
        payload["music_media_input"] = media_input.model_dump(mode="json")
        payload["music_media_info"] = resolved.model_dump(mode="json")
        subscription.target_payload_json = payload
        self.session.flush()
        return resolved

    @staticmethod
    def _resolve_music_media_info_snapshot(subscription) -> MusicMediaInfo | None:
        payload = subscription.target_payload_json or {}
        snapshot = payload.get("music_media_info")
        if not isinstance(snapshot, dict):
            return None
        try:
            return MusicMediaInfo.model_validate(snapshot)
        except Exception:  # pragma: no cover - defensive parse guard
            return None

    def _build_subscription_provider_input(
        self,
        subscription,
        *,
        source_kind: str,
    ) -> MusicMediaInput:
        provider, provider_id = self._resolve_subscription_provider_ref(subscription)
        return self.music_media_chain.input_from_provider_ref(
            entity_type=EntityType(subscription.target_entity_type or subscription.subscription_type),
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context={
                "subscription_id": subscription.id,
                "subscription_type": subscription.subscription_type,
            },
            raw_context={"target_id": subscription.target_id},
        )

    @staticmethod
    def _resolve_subscription_provider_ref(subscription) -> tuple[str, str]:
        payload = subscription.target_payload_json or {}

        media_info = payload.get("music_media_info")
        if isinstance(media_info, dict):
            provider = str(media_info.get("provider") or "").strip()
            provider_id = str(media_info.get("provider_id") or "").strip()
            if provider and provider_id:
                return provider, provider_id

        provider_ref = payload.get("provider_ref")
        if isinstance(provider_ref, dict):
            provider = str(provider_ref.get("provider") or "").strip()
            provider_id = str(provider_ref.get("provider_id") or "").strip()
            if provider and provider_id:
                return provider, provider_id

        provider = str(payload.get("provider") or "").strip()
        provider_id = str(payload.get("provider_id") or "").strip()
        if provider and provider_id:
            return provider, provider_id
        if provider:
            return provider, subscription.target_id

        return "musicbrainz", subscription.target_id

    @staticmethod
    def _resolve_music_media_input_snapshot(subscription) -> MusicMediaInput | None:
        payload = subscription.target_payload_json or {}
        snapshot = payload.get("music_media_input")
        if not isinstance(snapshot, dict):
            return None
        try:
            return MusicMediaInput.model_validate(snapshot)
        except Exception:  # pragma: no cover - defensive parse guard
            return None

    def _map_run_status(self, job_status: JobStatus) -> SubscriptionRunStatus:
        if job_status == JobStatus.DISPATCHED:
            return SubscriptionRunStatus.DISPATCHED
        if job_status == JobStatus.MANUAL_PENDING:
            return SubscriptionRunStatus.MANUAL_PENDING
        if job_status == JobStatus.NO_RESULT:
            return SubscriptionRunStatus.NO_RESULT
        if job_status == JobStatus.FAILED:
            return SubscriptionRunStatus.FAILED
        return SubscriptionRunStatus.MATCHED

    def _select_auto_dispatch_candidate(
        self,
        candidates: list[SearchCandidateDetail],
    ) -> SearchCandidateDetail | None:
        for candidate in candidates:
            if candidate.dispatchable and candidate.decision == DecisionStatus.AUTO_DOWNLOAD:
                return candidate
        return None

    def _resolve_downloader_id(self, subscription) -> str:
        preference_json = subscription.preference_json or {}
        for key in ("downloader_id", "target_downloader"):
            value = preference_json.get(key)
            if isinstance(value, str) and value:
                return value
        return "mock-downloader"

    def _should_auto_apply(
        self,
        organize_preview,
        candidate: SearchCandidateDetail,
    ) -> bool:
        if organize_preview.organize_status != OrganizeStatus.PREVIEW_READY:
            return False
        if organize_preview.path_handoff and organize_preview.path_handoff.source_path:
            return True

        raw_payload = candidate.raw_payload or {}
        if raw_payload.get("host_transfer_source_path") or raw_payload.get("local_file_path"):
            return True
        for key in ("host_transfer_source", "source_fileitem"):
            fileitem = raw_payload.get(key)
            if isinstance(fileitem, dict) and fileitem.get("path"):
                return True
        return False

    @staticmethod
    def _search_outcome_reason(executed_job: SearchJobSummary) -> str:
        active_adapter = executed_job.summary.get("active_search_adapter")
        if active_adapter == "real_host_search":
            return "host_search_no_result"
        return "search_no_result"
