"""Subscription routes for Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_subscription_execution_service, get_subscription_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.orchestration import (
    CreateSubscriptionRequest,
    SubscriptionState,
    SubscriptionRunStatus,
    SubscriptionType,
    UpdateSubscriptionRequest,
)
from ...services.subscription_execution import SubscriptionExecutionService
from ...services.subscriptions import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", summary="List subscriptions")
async def list_subscriptions(
    request: Request,
    subscription_type: SubscriptionType | None = Query(default=None),
    status: SubscriptionState | None = Query(default=None),
    service: SubscriptionService = Depends(get_subscription_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_subscriptions(
            subscription_type=subscription_type,
            status=status.value if status else None,
        ),
        message="Subscriptions loaded.",
        code="SUBSCRIPTIONS_OK",
        mock=False,
        note="当前订阅列表已支持手动 run 与最小应用内 scheduler。",
    )


@router.post("", summary="Create subscription")
async def create_subscription(
    payload: CreateSubscriptionRequest,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.create_subscription(payload),
        message="Subscription created.",
        code="SUBSCRIPTION_CREATED",
        mock=False,
        note="当前支持 metadata 实体订阅落库；可选择手动 run 或最小应用内 scheduler。",
    )


@router.get("/runs/{run_id}", summary="Get subscription run detail")
async def get_subscription_run(
    run_id: str,
    request: Request,
    service: SubscriptionExecutionService = Depends(get_subscription_execution_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_run_detail(run_id),
        message="Subscription run detail loaded.",
        code="SUBSCRIPTION_RUN_DETAIL_OK",
        mock=False,
        note="当前 run detail 展示的是手动或 scheduler 触发的执行结果与 organize preview/apply 记录。",
    )


@router.get("/{subscription_id}", summary="Get subscription detail")
async def get_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_subscription(subscription_id),
        message="Subscription detail loaded.",
        code="SUBSCRIPTION_DETAIL_OK",
        mock=False,
        note="当前详情聚焦订阅配置、模式与最近执行记录。",
    )


@router.patch("/{subscription_id}", summary="Update subscription")
async def update_subscription(
    subscription_id: str,
    payload: UpdateSubscriptionRequest,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.update_subscription(subscription_id, payload),
        message="Subscription updated.",
        code="SUBSCRIPTION_UPDATED",
        mock=False,
        note="当前可切换 active / paused / archived，并切换 manual / scheduled 模式。",
    )


@router.delete("/{subscription_id}", summary="Archive subscription")
async def archive_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionService = Depends(get_subscription_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.archive_subscription(subscription_id),
        message="Subscription archived.",
        code="SUBSCRIPTION_ARCHIVED",
        mock=False,
        note="当前删除动作为 archive，保留订阅记录供后续回看。",
    )


@router.post("/{subscription_id}/run", summary="Execute a subscription once")
async def run_subscription(
    subscription_id: str,
    request: Request,
    preview_only: bool = Query(default=False),
    retry_run_id: str | None = Query(default=None),
    service: SubscriptionExecutionService = Depends(get_subscription_execution_service),
) -> ApiResponse:
    result = service.execute(
        subscription_id,
        preview_only=preview_only,
        retry_run_id=retry_run_id,
    )
    return success_response(
        request,
        data=result,
        message="Subscription preview generated." if preview_only else "Subscription executed once.",
        code="SUBSCRIPTION_RUN_PREVIEWED" if preview_only else "SUBSCRIPTION_RUN_EXECUTED",
        mock=False,
        note=(
            "preview_only 只生成订阅执行计划与诊断，不触发真实 SearchJob / dispatch / organize。"
            if preview_only
            else "当前执行器会同步创建 SearchJob，并沿用固定的 search/dispatch/organize 调用语义。"
        ),
    )

@router.get("/{subscription_id}/runs", summary="List subscription runs")
async def list_subscription_runs(
    subscription_id: str,
    request: Request,
    execution_status: SubscriptionRunStatus | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1),
    service: SubscriptionExecutionService = Depends(get_subscription_execution_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_runs(
            subscription_id,
            execution_status=execution_status,
            limit=limit,
        ),
        message="Subscription runs loaded.",
        code="SUBSCRIPTION_RUNS_OK",
        mock=False,
        note="当前 run 列表支持按 execution_status 与 limit 聚合回看手动或 scheduler 触发的结果。",
    )
