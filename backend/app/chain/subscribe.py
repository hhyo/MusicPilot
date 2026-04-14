"""MoviePilot-aligned music subscribe chain."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from . import MusicChainBase
from ..db.orchestration_oper import OrchestrationOper
from ..schemas.acquisition import DispatchRequest, QueryPreferences, SearchCandidateDetail, SearchJobCreateRequest
from ..schemas.music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMetaBase,
    MusicRecognitionAssessment,
    MusicResolveDetailResponse,
)
from ..schemas.shared import DecisionStatus, EntityType, JobStatus, TriggerSource
from ..schemas.shared import utc_now
from ..schemas.orchestration import (
    CreateChartEntrySubscriptionRequest,
    CreateSubscriptionRequest,
    DiscoveryEntryView,
    OrganizeApplyRequest,
    OrganizePreviewRequest,
    SubscriptionDetail,
    SubscriptionListData,
    SubscriptionRunDetail,
    SubscriptionRunListData,
    SubscriptionRunStatus,
    SubscriptionRunSummary,
    SubscriptionSchedulerDiagnostic,
    SubscriptionSchedulerRunResult,
    SubscriptionSchedulerSummary,
    SubscriptionSchedulerTaskBoundary,
    SubscriptionSchedulerWindow,
    SubscriptionState,
    SubscriptionSummary,
    SubscriptionType,
    UpdateSubscriptionRequest,
)


SUBSCRIPTION_NOTE = (
    "当前订阅模型已落库，可切换手动执行、preview_only 预览、retry 回放或宿主调度执行。"
)

RUN_NOTE = (
    "当前订阅执行器会同步创建并执行一次 SearchJob，"
    "对最佳 AUTO_DOWNLOAD 候选继续自动派发并生成 organize preview；"
    "若 preview 已拿到明确本地源文件，则继续自动 apply。"
)


def normalize_subscription_mode(value: str | None) -> str:
    return value or "manual"


class MusicSubscribeChain(MusicChainBase):
    def __init__(
        self,
        *,
        session,
        music_media_chain=None,
        search_chain=None,
        download_chain=None,
        transfer_chain=None,
        default_interval_minutes: int = 360,
    ) -> None:
        super().__init__(cache_region="music_subscribe_chain")
        self.session = session
        self.music_media_chain = music_media_chain
        self.search_chain = search_chain
        self.download_chain = download_chain
        self.transfer_chain = transfer_chain
        self.oper = OrchestrationOper(session)
        self.default_interval_minutes = default_interval_minutes

    def list_subscriptions(
        self,
        *,
        subscription_type: SubscriptionType | None = None,
        status: str | None = None,
    ) -> SubscriptionListData:
        items = [
            serialize_subscription(subscription)
            for subscription in self.oper.list_subscriptions(
                subscription_type=subscription_type.value if subscription_type else None,
                status=status,
            )
        ]
        return SubscriptionListData(
            items=items,
            total=len(items),
            mock=False,
            note="当前订阅列表反映的是手动 run、preview_only、retry 与宿主调度的真实状态。",
        )

    def get_subscription(self, subscription_id: str) -> SubscriptionDetail:
        subscription = self._require_subscription(subscription_id)
        recent_runs = [
            serialize_run_summary(run)
            for run in sorted(subscription.runs, key=lambda item: item.created_at, reverse=True)[:5]
        ]
        return SubscriptionDetail(**serialize_subscription(subscription).model_dump(), recent_runs=recent_runs)

    def create_subscription(self, payload: CreateSubscriptionRequest) -> SubscriptionSummary:
        if payload.subscription_type == SubscriptionType.CHART_ENTRY:
            raise HTTPException(
                status_code=400,
                detail="Use the chart subscription route for chart_entry subscriptions.",
            )
        self._require_music_media_chain()
        resolved_type = payload.target_entity_type or EntityType(payload.subscription_type.value)
        resolved = self.music_media_chain.resolve_detail_from_target_payload_ref(
            entity_type=resolved_type,
            target_id=payload.target_id,
            target_payload=payload.target_payload,
            source_kind="subscription",
            source_context={
                "subscription_type": payload.subscription_type.value,
                "target_id": payload.target_id,
            },
            raw_context={"target_payload": payload.target_payload},
        )
        media_input = self.music_media_chain.input_from_target_payload_ref(
            entity_type=resolved_type,
            target_id=payload.target_id,
            target_payload=payload.target_payload,
            source_kind="subscription",
            source_context={
                "subscription_type": payload.subscription_type.value,
                "target_id": payload.target_id,
            },
            raw_context={"target_payload": payload.target_payload},
        )
        subscription = self.oper.create_subscription(
            subscription_type=payload.subscription_type.value,
            target_id=payload.target_id,
            target_name=payload.target_name or resolved.detail.title,
            target_entity_type=resolved.detail.entity_type.value,
            chart_source=None,
            chart_name=None,
            mode=normalize_subscription_mode(payload.mode.value),
            preference_json=payload.preference_json,
            target_payload_json=dict(payload.target_payload),
            music_media_input=media_input.model_dump(mode="json"),
            music_meta_base=resolved.base.model_dump(mode="json"),
            music_recognition_assessment=resolved.assessment.model_dump(mode="json"),
            music_media_info=resolved.media.model_dump(mode="json"),
            note=SUBSCRIPTION_NOTE,
        )
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def create_from_chart_entry(
        self,
        *,
        entry: DiscoveryEntryView,
        payload: CreateChartEntrySubscriptionRequest,
    ) -> SubscriptionSummary:
        self._require_music_media_chain()
        if entry.recognition_assessment.state not in {"direct", "ready"}:
            raise HTTPException(
                status_code=400,
                detail=entry.recognition_assessment.note
                or "Chart entry does not have enough music media clues for subscription.",
            )

        resolved = self.music_media_chain.resolve_response_from_base(entry.meta_base)
        chart_entry = entry.entry
        entry_hints = dict(chart_entry.target_payload or {})
        subscription = self.oper.create_subscription(
            subscription_type=SubscriptionType.CHART_ENTRY.value,
            target_id=chart_entry.item_id,
            target_name=chart_entry.target_name,
            target_entity_type=chart_entry.item_type.value,
            chart_source=chart_entry.chart_source,
            chart_name=chart_entry.chart_name,
            mode=normalize_subscription_mode(payload.mode.value),
            preference_json=payload.preference_json,
            target_payload_json={
                "chart_id": chart_entry.chart_id,
                "chart_item_id": chart_entry.item_id,
                "chart_source": chart_entry.chart_source,
                "chart_name": chart_entry.chart_name,
                "rank": chart_entry.rank,
                "target_id": chart_entry.target_id,
                "target_name": chart_entry.target_name,
                "target_entity_type": chart_entry.item_type.value,
                "subtitle": chart_entry.subtitle,
                "entry_target_payload": entry_hints,
                **entry_hints,
            },
            music_media_input=entry.media_input.model_dump(mode="json"),
            music_meta_base=entry.meta_base.model_dump(mode="json"),
            music_recognition_assessment=entry.recognition_assessment.model_dump(mode="json"),
            music_media_info=resolved.media.model_dump(mode="json"),
            note="榜单订阅已在创建时固化统一音乐媒体链识别结果。",
        )
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def update_subscription(
        self,
        subscription_id: str,
        payload: UpdateSubscriptionRequest,
    ) -> SubscriptionSummary:
        subscription = self._require_subscription(subscription_id)
        if payload.status is not None:
            subscription.status = payload.status.value
        if payload.mode is not None:
            subscription.mode = normalize_subscription_mode(payload.mode.value)
        if payload.preference_json is not None:
            subscription.preference_json = payload.preference_json
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def archive_subscription(self, subscription_id: str) -> SubscriptionSummary:
        subscription = self._require_subscription(subscription_id)
        subscription.status = SubscriptionState.ARCHIVED.value
        self.session.commit()
        self.session.refresh(subscription)
        return serialize_subscription(subscription)

    def execute(
        self,
        subscription_id: str,
        *,
        preview_only: bool = False,
        retry_run_id: str | None = None,
    ) -> SubscriptionRunDetail:
        subscription = self._require_subscription(subscription_id)
        if subscription.status == SubscriptionState.ARCHIVED.value:
            raise HTTPException(status_code=400, detail="Archived subscription can not be executed.")

        retry_run = None
        if retry_run_id is not None:
            retry_run = self.oper.get_run(retry_run_id)
            if retry_run is None:
                raise HTTPException(status_code=404, detail=f"Subscription run {retry_run_id} was not found.")
            if retry_run.subscription_id != subscription_id:
                raise HTTPException(status_code=400, detail="retry_run_id must belong to the target subscription.")

        run = self.oper.create_run(subscription, note=self._build_run_note(preview_only, retry_run_id))
        self.oper.mark_run_running(run)
        self.session.flush()

        try:
            job_payload = self._build_job_request(subscription, persist_resolution=not preview_only)
            summary = {
                "execution_mode": "preview" if preview_only else "execute",
                "preview_only": preview_only,
                "retry_run_id": retry_run_id,
                "planned_job": job_payload.model_dump(mode="json"),
                "best_score": 0.0,
                "candidate_count": 0,
                "mock_host_search": None,
                "search_outcome_reason": "preview_only" if preview_only else None,
                "organize_preview_id": None,
                "organize_backend": None,
                "organize_fallback_reason": None,
                "dispatch_status": None,
                "dispatch_backend": None,
                "binding_id": None,
                "last_dispatched_candidate_id": None,
            }
            if retry_run is not None:
                summary["retry_run"] = serialize_run_summary(retry_run).model_dump(mode="json")

            if preview_only:
                self.oper.mark_run_finished(
                    run,
                    execution_status=SubscriptionRunStatus.MANUAL_PENDING.value,
                    matched_candidates_count=0,
                    summary_json=summary,
                    touch_subscription=False,
                )
                self.session.commit()
                return self.get_run_detail(run.id)

            self._require_search_chain()
            created_job = self.search_chain.create_job(job_payload)
            executed_job = self.search_chain.execute_job(created_job.id)
            candidates_data = self.search_chain.list_candidates(executed_job.id)

            organize_preview = None
            execution_status = self._map_run_status(executed_job.status).value
            summary.update(
                {
                    "best_score": executed_job.summary.get("best_score", 0.0),
                    "candidate_count": candidates_data.total,
                    "mock_host_search": executed_job.mock,
                }
            )
            if candidates_data.total == 0:
                summary["search_outcome_reason"] = self._search_outcome_reason(executed_job)
            if candidates_data.items:
                auto_candidate = self._select_auto_dispatch_candidate(candidates_data.items)
                if auto_candidate is not None and self.download_chain is not None:
                    dispatch_result = self.download_chain.dispatch(
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
                        organize_preview = self._require_transfer_chain().preview(
                            OrganizePreviewRequest(binding_id=dispatch_result.binding_id),
                            subscription_run_id=run.id,
                        )
                    else:
                        organize_preview = self._require_transfer_chain().preview_for_candidate(
                            candidate_id=auto_candidate.id,
                            subscription_run_id=run.id,
                        )
                    if dispatch_result.dispatchable:
                        execution_status = SubscriptionRunStatus.DISPATCHED.value
                        if organize_preview is not None and self._should_auto_apply(organize_preview, auto_candidate):
                            organize_preview = self._require_transfer_chain().apply(
                                OrganizeApplyRequest(organize_job_id=organize_preview.id)
                            )
                            execution_status = SubscriptionRunStatus.APPLIED.value
                else:
                    organize_preview = self._require_transfer_chain().preview_for_candidate(
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

            self.oper.mark_run_finished(
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
            failed_run = self.oper.get_run(run.id)
            if failed_run is not None:
                self.oper.mark_run_finished(
                    failed_run,
                    execution_status=SubscriptionRunStatus.FAILED.value,
                    matched_candidates_count=0,
                    summary_json={"candidate_count": 0},
                    error_message=str(exc),
                )
                self.session.commit()
            raise

        return self.get_run_detail(run.id)

    def list_runs(
        self,
        subscription_id: str,
        *,
        execution_status: SubscriptionRunStatus | None = None,
        limit: int | None = None,
    ) -> SubscriptionRunListData:
        self._require_subscription(subscription_id)
        if limit is not None and limit <= 0:
            raise HTTPException(status_code=400, detail="limit must be greater than 0.")
        items = [
            serialize_run_summary(run)
            for run in self.oper.list_runs(
                subscription_id,
                execution_status=execution_status.value if execution_status else None,
                limit=limit,
            )
        ]
        return SubscriptionRunListData(
            subscription_id=subscription_id,
            items=items,
            total=len(items),
            mock=False,
            note="当前 run 记录支持按 execution_status 与 limit 聚合回看手动、preview_only、retry 或 scheduler 触发的执行结果。",
        )

    def get_run_detail(self, run_id: str) -> SubscriptionRunDetail:
        run = self.oper.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Subscription run {run_id} was not found.")

        subscription_summary = serialize_subscription(run.subscription)
        metadata_target = self._resolve_metadata_target(run.subscription)
        search_job = self.search_chain.get_job(run.search_job_id) if run.search_job_id and self.search_chain else None
        candidates = self.search_chain.list_candidates(run.search_job_id).items if run.search_job_id and self.search_chain else []
        organize_preview = (
            self.transfer_chain.get_record(run.organize_record_id)
            if run.organize_record_id and self.transfer_chain
            else None
        )
        return SubscriptionRunDetail(
            **serialize_run_summary(run).model_dump(),
            subscription=subscription_summary,
            metadata_target=metadata_target,
            search_job=search_job,
            candidates=candidates,
            organize_preview=organize_preview,
        )

    def _build_job_request(self, subscription, *, persist_resolution: bool = True) -> SearchJobCreateRequest:
        self._require_music_media_chain()
        preferences = QueryPreferences.model_validate(subscription.preference_json or {})
        media_input = self._load_persisted_music_media_input(subscription)
        if media_input is None:
            media_info = self._resolve_or_build_music_media_info(subscription, persist=persist_resolution)
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
            media_input = self._build_subscription_provider_input(subscription, source_kind="subscription")
        return SearchJobCreateRequest(
            input=media_input,
            trigger_source=TriggerSource.SUBSCRIPTION,
            profile_id="default-lossless",
            mode="manual" if subscription.mode == "manual" else "auto",
            preferences=preferences,
        )

    def _resolve_metadata_target(self, subscription):
        self._require_music_media_chain()
        media_input = self._load_persisted_music_media_input(subscription)
        if media_input is None:
            media_info = self._resolve_or_build_music_media_info(subscription)
            if media_info is not None:
                media_input = self.music_media_chain.input_from_music_media_info(
                    media_info,
                    source_kind="subscription_detail",
                    source_context={"subscription_id": subscription.id},
                    raw_context={"target_id": subscription.target_id},
                )
        if media_input is not None:
            return self.music_media_chain.resolve_detail(media_input).detail
        return self.music_media_chain.resolve_detail_from_target_payload_ref(
            entity_type=EntityType(subscription.target_entity_type or subscription.subscription_type),
            target_id=subscription.target_id,
            target_payload=subscription.target_payload_json or {},
            source_kind="subscription_detail",
            source_context={
                "subscription_id": subscription.id,
                "subscription_type": subscription.subscription_type,
            },
            raw_context={"target_id": subscription.target_id},
        ).detail

    def _resolve_or_build_music_media_info(self, subscription, *, persist: bool = True) -> MusicMediaInfo | None:
        self._require_music_media_chain()
        media_info = self._load_persisted_music_media_info(subscription)
        if media_info is not None and media_info.provider_id:
            return media_info

        media_input = self._load_persisted_music_media_input(subscription)
        if media_input is None:
            resolved = self.music_media_chain.resolve_response_from_target_payload_ref(
                entity_type=EntityType(subscription.target_entity_type or subscription.subscription_type),
                target_id=subscription.target_id,
                target_payload=subscription.target_payload_json or {},
                source_kind="subscription_resolution",
                source_context={
                    "subscription_id": subscription.id,
                    "subscription_type": subscription.subscription_type,
                },
                raw_context={"target_id": subscription.target_id},
            )
            media_input = self._build_subscription_provider_input(subscription, source_kind="subscription_resolution")
        else:
            resolved = self.music_media_chain.resolve_response(media_input)

        if persist:
            subscription.music_media_input = media_input.model_dump(mode="json")
            subscription.music_meta_base = resolved.base.model_dump(mode="json")
            subscription.music_recognition_assessment = resolved.assessment.model_dump(mode="json")
            subscription.music_media_info = resolved.media.model_dump(mode="json")
            self.session.flush()
        return resolved.media

    def _build_subscription_provider_input(self, subscription, *, source_kind: str) -> MusicMediaInput:
        self._require_music_media_chain()
        return self.music_media_chain.input_from_target_payload_ref(
            entity_type=EntityType(subscription.target_entity_type or subscription.subscription_type),
            target_id=subscription.target_id,
            target_payload=subscription.target_payload_json or {},
            source_kind=source_kind,
            source_context={
                "subscription_id": subscription.id,
                "subscription_type": subscription.subscription_type,
            },
            raw_context={"target_id": subscription.target_id},
        )

    def _require_subscription(self, subscription_id: str):
        subscription = self.oper.get_subscription(subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail=f"Subscription {subscription_id} was not found.")
        return subscription

    def _require_music_media_chain(self):
        if self.music_media_chain is None:
            raise HTTPException(status_code=500, detail="Music media chain is not configured.")
        return self.music_media_chain

    def _require_search_chain(self):
        if self.search_chain is None:
            raise HTTPException(status_code=500, detail="Music search chain is not configured.")
        return self.search_chain

    def _require_transfer_chain(self):
        if self.transfer_chain is None:
            raise HTTPException(status_code=500, detail="Music transfer chain is not configured.")
        return self.transfer_chain

    @staticmethod
    def _build_run_note(preview_only: bool, retry_run_id: str | None) -> str:
        mode_label = "preview" if preview_only else "run"
        retry_label = f" retry from {retry_run_id}" if retry_run_id else ""
        return f"{RUN_NOTE} Current action is {mode_label}.{retry_label}".strip()

    @staticmethod
    def _load_persisted_music_media_info(subscription) -> MusicMediaInfo | None:
        payload = subscription.music_media_info or {}
        if not payload:
            return None
        try:
            return MusicMediaInfo.model_validate(payload)
        except Exception:
            return None

    @staticmethod
    def _load_persisted_music_media_input(subscription) -> MusicMediaInput | None:
        payload = subscription.music_media_input or {}
        if not payload:
            return None
        try:
            return MusicMediaInput.model_validate(payload)
        except Exception:
            return None

    @staticmethod
    def _map_run_status(job_status: JobStatus) -> SubscriptionRunStatus:
        if job_status == JobStatus.DISPATCHED:
            return SubscriptionRunStatus.DISPATCHED
        if job_status == JobStatus.MANUAL_PENDING:
            return SubscriptionRunStatus.MANUAL_PENDING
        if job_status == JobStatus.NO_RESULT:
            return SubscriptionRunStatus.NO_RESULT
        if job_status == JobStatus.FAILED:
            return SubscriptionRunStatus.FAILED
        return SubscriptionRunStatus.MATCHED

    @staticmethod
    def _select_auto_dispatch_candidate(candidates: list[SearchCandidateDetail]) -> SearchCandidateDetail | None:
        for candidate in candidates:
            if candidate.dispatchable and candidate.decision == DecisionStatus.AUTO_DOWNLOAD:
                return candidate
        return None

    @staticmethod
    def _resolve_downloader_id(subscription) -> str:
        preference_json = subscription.preference_json or {}
        for key in ("downloader_id", "target_downloader"):
            value = preference_json.get(key)
            if isinstance(value, str) and value:
                return value
        return "mock-downloader"

    @staticmethod
    def _should_auto_apply(organize_preview, candidate: SearchCandidateDetail) -> bool:
        if organize_preview.organize_status.value != "preview_ready":
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
    def _search_outcome_reason(executed_job) -> str:
        active_adapter = executed_job.summary.get("active_search_adapter")
        if active_adapter == "real_host_search":
            return "host_search_no_result"
        return "search_no_result"

    @staticmethod
    def normalize_timestamp(value: datetime, *, default_tz: timezone = timezone.utc) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=default_tz)
        return value.astimezone(default_tz)

    def schedule_interval_minutes(self, subscription) -> int:
        preference_json = getattr(subscription, "preference_json", None) or {}
        value = preference_json.get("schedule_interval_minutes")
        if isinstance(value, int) and value > 0:
            return value
        return self.default_interval_minutes

    def _next_run_at(self, subscription, now: datetime) -> datetime:
        baseline = (
            getattr(subscription, "last_run_at", None)
            or getattr(subscription, "updated_at", None)
            or getattr(subscription, "created_at", None)
            or now
        )
        baseline = self.normalize_timestamp(baseline)
        return baseline + timedelta(minutes=self.schedule_interval_minutes(subscription))

    def _retry_window_minutes(self, subscription) -> int:
        preference_json = getattr(subscription, "preference_json", None) or {}
        value = preference_json.get("scheduler_retry_window_minutes")
        if isinstance(value, int) and value > 0:
            return value
        return self.schedule_interval_minutes(subscription)

    def _duplicate_guard_until(self, subscription, finished_at: datetime) -> datetime:
        return finished_at + timedelta(minutes=self.schedule_interval_minutes(subscription))

    def _retry_eligible_at(self, subscription, finished_at: datetime) -> datetime:
        return finished_at + timedelta(minutes=self._retry_window_minutes(subscription))

    def _skip_reason(self, subscription, now: datetime) -> str | None:
        if normalize_subscription_mode(getattr(subscription, "mode", None)) != "scheduled":
            return "not_scheduled"
        if getattr(subscription, "status", None) != "active":
            return "inactive"
        if self.oper.has_running_run(subscription.id):
            return "running"
        latest_run = self.oper.get_latest_run(subscription.id)
        if latest_run is not None:
            latest_status = str(getattr(latest_run, "execution_status", "") or "")
            finished_at = getattr(latest_run, "finished_at", None)
            if finished_at is not None:
                finished_at = self.normalize_timestamp(finished_at)
                if latest_status == "failed":
                    if now < self._retry_eligible_at(subscription, finished_at):
                        return "retry_window"
                elif now < self._duplicate_guard_until(subscription, finished_at):
                    return "duplicate_guard"
        if now < self._next_run_at(subscription, now):
            return "not_due"
        return None

    def run_pending_once(self, *, now: datetime | None = None) -> dict:
        current_time = self.normalize_timestamp(now or utc_now())
        executed_ids: list[str] = []
        skipped_ids: list[str] = []
        errors: dict[str, str] = {}
        diagnostics: list[SubscriptionSchedulerDiagnostic] = []
        reason_counts: dict[str, int] = {}
        considered = 0

        for subscription in self.oper.list_subscriptions(status="active"):
            considered += 1
            normalized_mode = normalize_subscription_mode(getattr(subscription, "mode", None))
            interval_minutes = self.schedule_interval_minutes(subscription)
            next_run_at = self._next_run_at(subscription, current_time)
            latest_run = self.oper.get_latest_run(subscription.id)
            recent_run_id = getattr(latest_run, "id", None)
            recent_run_status = getattr(latest_run, "execution_status", None)
            finished_at = getattr(latest_run, "finished_at", None)
            duplicate_guard_until = None
            retry_eligible_at = None
            if finished_at is not None:
                normalized_finished_at = self.normalize_timestamp(finished_at)
                if recent_run_status == "failed":
                    retry_eligible_at = self._retry_eligible_at(subscription, normalized_finished_at)
                else:
                    duplicate_guard_until = self._duplicate_guard_until(subscription, normalized_finished_at)
            reason = self._skip_reason(subscription, current_time)
            if reason is not None:
                skipped_ids.append(subscription.id)
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                diagnostics.append(
                    SubscriptionSchedulerDiagnostic(
                        subscription_id=subscription.id,
                        mode=normalized_mode,
                        status=getattr(subscription, "status", "unknown"),
                        reason=reason,
                        due=False,
                        interval_minutes=interval_minutes,
                        last_run_at=getattr(subscription, "last_run_at", None),
                        next_run_at=next_run_at,
                        recent_run_id=recent_run_id,
                        recent_run_status=recent_run_status,
                        duplicate_guard_until=duplicate_guard_until,
                        retry_eligible_at=retry_eligible_at,
                    )
                )
                continue
            try:
                self.execute(subscription.id)
                executed_ids.append(subscription.id)
                reason_counts["executed"] = reason_counts.get("executed", 0) + 1
                diagnostics.append(
                    SubscriptionSchedulerDiagnostic(
                        subscription_id=subscription.id,
                        mode=normalized_mode,
                        status=getattr(subscription, "status", "unknown"),
                        reason="executed",
                        due=True,
                        interval_minutes=interval_minutes,
                        last_run_at=getattr(subscription, "last_run_at", None),
                        next_run_at=next_run_at,
                        recent_run_id=recent_run_id,
                        recent_run_status=recent_run_status,
                        duplicate_guard_until=duplicate_guard_until,
                        retry_eligible_at=retry_eligible_at,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors[subscription.id] = str(exc)
                reason_counts["error"] = reason_counts.get("error", 0) + 1
                diagnostics.append(
                    SubscriptionSchedulerDiagnostic(
                        subscription_id=subscription.id,
                        mode=normalized_mode,
                        status=getattr(subscription, "status", "unknown"),
                        reason="error",
                        due=True,
                        interval_minutes=interval_minutes,
                        last_run_at=getattr(subscription, "last_run_at", None),
                        next_run_at=next_run_at,
                        recent_run_id=recent_run_id,
                        recent_run_status=recent_run_status,
                        duplicate_guard_until=duplicate_guard_until,
                        retry_eligible_at=retry_eligible_at,
                        error_message=str(exc),
                    )
                )

        handoff_reconcile = {"summary": {"applied": 0, "unresolved": 0}}
        if self.transfer_chain is not None:
            handoff_reconcile = self.transfer_chain.reconcile_pending_once()

        summary = SubscriptionSchedulerSummary(
            considered=considered,
            executed=len(executed_ids),
            skipped=len(skipped_ids),
            errors=len(errors),
            handoff_applied=handoff_reconcile["summary"]["applied"],
            handoff_unresolved=handoff_reconcile["summary"]["unresolved"],
        )
        finished_at = utc_now()
        window = SubscriptionSchedulerWindow(
            started_at=current_time,
            finished_at=finished_at,
            duration_seconds=max(0.0, (finished_at - current_time).total_seconds()),
        )
        report = SubscriptionSchedulerRunResult(
            executed_ids=executed_ids,
            skipped_ids=skipped_ids,
            error_ids=list(errors.keys()),
            errors=errors,
            summary=summary,
            reason_counts=reason_counts,
            window=window,
            diagnostics=diagnostics,
            handoff_reconcile=handoff_reconcile,
            task_boundary=SubscriptionSchedulerTaskBoundary(),
        )
        return report.model_dump(mode="json")


def serialize_subscription(subscription) -> SubscriptionSummary:
    return SubscriptionSummary(
        id=subscription.id,
        subscription_type=SubscriptionType(subscription.subscription_type),
        target_id=subscription.target_id,
        target_name=subscription.target_name,
        target_entity_type=subscription.target_entity_type,
        chart_source=subscription.chart_source,
        chart_name=subscription.chart_name,
        status=subscription.status,
        mode=normalize_subscription_mode(subscription.mode),
        preference_json=subscription.preference_json or {},
        target_payload=subscription.target_payload_json or {},
        music_media_input=_parse_optional_music_media_input(subscription.music_media_input),
        music_meta_base=_parse_optional_music_meta_base(subscription.music_meta_base),
        music_recognition_assessment=_parse_optional_music_recognition_assessment(
            subscription.music_recognition_assessment
        ),
        music_media_info=_parse_optional_music_media_info(subscription.music_media_info),
        latest_run_status=subscription.latest_run_status,
        last_run_at=subscription.last_run_at,
        mock=subscription.mock,
        note=subscription.note,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


def serialize_run_summary(run) -> SubscriptionRunSummary:
    return SubscriptionRunSummary(
        id=run.id,
        subscription_id=run.subscription_id,
        search_job_id=run.search_job_id,
        execution_status=SubscriptionRunStatus(run.execution_status),
        matched_candidates_count=run.matched_candidates_count,
        organize_record_id=run.organize_record_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        summary_json=run.summary_json or {},
        music_media_input=_parse_optional_music_media_input(run.music_media_input),
        music_meta_base=_parse_optional_music_meta_base(run.music_meta_base),
        music_recognition_assessment=_parse_optional_music_recognition_assessment(
            run.music_recognition_assessment
        ),
        music_media_info=_parse_optional_music_media_info(run.music_media_info),
        mock=run.mock,
        note=run.note,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _parse_optional_music_media_input(payload) -> MusicMediaInput | None:
    if not payload:
        return None
    return MusicMediaInput.model_validate(payload)


def _parse_optional_music_meta_base(payload) -> MusicMetaBase | None:
    if not payload:
        return None
    return MusicMetaBase.model_validate(payload)


def _parse_optional_music_recognition_assessment(payload) -> MusicRecognitionAssessment | None:
    if not payload:
        return None
    return MusicRecognitionAssessment.model_validate(payload)


def _parse_optional_music_media_info(payload) -> MusicMediaInfo | None:
    if not payload:
        return None
    return MusicMediaInfo.model_validate(payload)
