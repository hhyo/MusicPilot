"""Settings route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import ProviderSettings, RuleProfile
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/providers", summary="Get provider settings placeholder")
async def provider_settings(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.provider_settings(),
        message="Provider settings placeholder is callable.",
        code="SETTINGS_PROVIDERS_PLACEHOLDER",
        mock=True,
        note="当前 provider settings 为 mock 数据，未连接真实配置持久化。",
    )


@router.put("/providers", summary="Update provider settings placeholder")
async def update_provider_settings(
    payload: ProviderSettings,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.update_provider_settings(payload),
        message="Update provider settings placeholder accepted the payload.",
        code="UPDATE_SETTINGS_PROVIDERS_PLACEHOLDER",
        mock=True,
        note="当前只回显 provider 配置，不会写入真实配置存储。",
    )


@router.get("/profiles", summary="Get rule profiles placeholder")
async def rule_profiles(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.profiles(),
        message="Rule profiles placeholder is callable.",
        code="SETTINGS_PROFILES_PLACEHOLDER",
        mock=True,
        note="当前规则 profile 为 mock 数据，未连接真实配置持久化。",
    )


@router.put("/profiles", summary="Update rule profile placeholder")
async def update_rule_profile(
    payload: RuleProfile,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.update_profile(payload),
        message="Update rule profile placeholder accepted the payload.",
        code="UPDATE_SETTINGS_PROFILE_PLACEHOLDER",
        mock=True,
        note="当前只回显 profile 配置，不会写入真实配置存储。",
    )

