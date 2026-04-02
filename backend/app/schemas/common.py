"""Common schemas shared across Phase 1 APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = Field(..., description="Whether the request succeeded.")
    code: str = Field(..., description="Business status code or error code.")
    message: str = Field(..., description="Human-readable response message.")
    data: Any = Field(default=None, description="Payload data for the current route.")
    request_id: str = Field(..., description="Per-request identifier for tracing.")
    timestamp: datetime = Field(..., description="UTC timestamp for the response payload.")
    mock: bool = Field(default=False, description="Whether the payload is mock or placeholder data.")
    note: str | None = Field(
        default=None,
        description="Additional explanation for placeholder boundaries or special handling.",
    )
    todo: list[str] | None = Field(
        default=None,
        description="Follow-up items for future integration stages when applicable.",
    )


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)
    total: int = Field(default=0, ge=0)

