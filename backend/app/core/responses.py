"""Unified response builders for Phase 1 APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from ..schemas.common import ApiResponse


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _request_id_from(request: Request | None) -> str:
    if request is None:
        return "system-generated"
    return getattr(request.state, "request_id", "request-id-missing")


def build_api_response(
    request: Request | None,
    *,
    success: bool,
    code: str,
    message: str,
    data: Any = None,
    mock: bool = False,
    note: str | None = None,
    todo: list[str] | None = None,
) -> ApiResponse:
    return ApiResponse(
        success=success,
        code=code,
        message=message,
        data=data,
        request_id=_request_id_from(request),
        timestamp=_utc_now(),
        mock=mock,
        note=note,
        todo=todo,
    )


def success_response(
    request: Request | None,
    *,
    data: Any = None,
    message: str = "Success",
    code: str = "OK",
    mock: bool = False,
    note: str | None = None,
    todo: list[str] | None = None,
) -> ApiResponse:
    return build_api_response(
        request,
        success=True,
        code=code,
        message=message,
        data=data,
        mock=mock,
        note=note,
        todo=todo,
    )


def error_json_response(
    request: Request | None,
    *,
    status_code: int,
    code: str,
    message: str,
    data: Any = None,
    mock: bool = False,
    note: str | None = None,
    todo: list[str] | None = None,
) -> JSONResponse:
    payload = build_api_response(
        request,
        success=False,
        code=code,
        message=message,
        data=data,
        mock=mock,
        note=note,
        todo=todo,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))

