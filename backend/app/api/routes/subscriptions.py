"""Subscription route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import CreateSubscriptionRequest, UpdateSubscriptionRequest
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", summary="List subscriptions placeholder")
async def list_subscriptions(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_subscriptions(),
        message="Subscription list placeholder is callable.",
        code="SUBSCRIPTIONS_PLACEHOLDER",
        mock=True,
        note="当前订阅列表是 mock 数据，未连接真实订阅状态机。",
    )


@router.post("", summary="Create subscription placeholder")
async def create_subscription(
    payload: CreateSubscriptionRequest,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.create_subscription(payload),
        message="Create subscription placeholder accepted the payload.",
        code="CREATE_SUBSCRIPTION_PLACEHOLDER",
        mock=True,
        note="当前仅验证订阅创建契约，不会写入真实存储。",
    )


@router.patch("/{subscription_id}", summary="Update subscription placeholder")
async def update_subscription(
    subscription_id: str,
    payload: UpdateSubscriptionRequest,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.update_subscription(subscription_id, payload),
        message="Update subscription placeholder accepted the payload.",
        code="UPDATE_SUBSCRIPTION_PLACEHOLDER",
        mock=True,
        note="当前仅验证订阅更新契约，不会写入真实存储。",
    )


@router.post("/{subscription_id}/run", summary="Run subscription placeholder")
async def run_subscription(
    subscription_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.run_subscription(subscription_id),
        message="Run subscription placeholder is callable.",
        code="RUN_SUBSCRIPTION_PLACEHOLDER",
        mock=True,
        note="当前仅返回 mock job，不会触发真实扫描。",
    )

