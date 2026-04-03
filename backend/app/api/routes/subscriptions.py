"""Subscription routes for Phase 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_subscription_execution_service, get_subscription_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.orchestration import (
    CreateSubscriptionRequest,
    SubscriptionState,
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
        mock=True,
        note="当前订阅列表基于 Phase 4 最小订阅闭环，未接入真实自动调度。",
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
        mock=True,
        note="当前支持 metadata 实体订阅落库；执行器仍是同步最小骨架。",
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
        mock=True,
        note="当前 run detail 展示的是 Phase 4 同步执行结果与 mock organize preview。",
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
        mock=True,
        note="当前详情聚焦订阅配置与最近执行记录，未接入真实计划任务。",
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
        mock=True,
        note="当前可切换 active / paused / archived，并调整最小 preference_json。",
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
        mock=True,
        note="当前删除动作为 archive，保留订阅记录供后续回看。",
    )


@router.post("/{subscription_id}/run", summary="Execute a subscription once")
async def run_subscription(
    subscription_id: str,
    request: Request,
    service: SubscriptionExecutionService = Depends(get_subscription_execution_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.execute(subscription_id),
        message="Subscription executed once.",
        code="SUBSCRIPTION_RUN_EXECUTED",
        mock=True,
        note="当前执行器会同步创建 SearchJob、执行 mock host search，并生成 organize preview。",
    )
 

@router.get("/{subscription_id}/runs", summary="List subscription runs")
async def list_subscription_runs(
    subscription_id: str,
    request: Request,
    service: SubscriptionExecutionService = Depends(get_subscription_execution_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_runs(subscription_id),
        message="Subscription runs loaded.",
        code="SUBSCRIPTION_RUNS_OK",
        mock=True,
        note="当前 run 列表为同步最小执行记录，可用于回看 candidate summary 与 organize 状态。",
    )
