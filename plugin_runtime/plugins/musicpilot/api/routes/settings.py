"""Settings route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service, get_settings_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import ProviderSettingsUpdatePayload, RuleProfile
from ...services.mvp_placeholder import MvpPlaceholderService
from ...services.settings import SettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/providers", summary="Get provider settings")
async def provider_settings(
    request: Request,
    service: SettingsService = Depends(get_settings_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_provider_settings(),
        message="Provider settings loaded.",
        code="SETTINGS_PROVIDERS_OK",
        mock=False,
    )


@router.put("/providers", summary="Update provider settings")
async def update_provider_settings(
    payload: ProviderSettingsUpdatePayload,
    request: Request,
    service: SettingsService = Depends(get_settings_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.update_provider_settings(payload),
        message="Provider settings updated.",
        code="UPDATE_SETTINGS_PROVIDERS_OK",
        mock=False,
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
