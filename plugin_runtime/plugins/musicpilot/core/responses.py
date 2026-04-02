"""Unified API response helpers for Phase 0 placeholder endpoints."""

from typing import Any

from ..schemas.common import ApiResponse


def success_response(
    data: dict[str, Any] | list[Any] | None = None,
    message: str = "Success",
    code: str = "OK",
    status_code: int = 200,
) -> ApiResponse:
    return ApiResponse(
        success=True,
        code=code,
        message=message,
        data=data,
        status_code=status_code,
    )
