"""Common response schemas shared across placeholder routes."""

from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = Field(default=True, description="Whether the request succeeded.")
    code: str = Field(default="OK", description="Business status code placeholder.")
    message: str = Field(default="Success", description="Human-readable response message.")
    status_code: int = Field(default=200, exclude=True, description="Internal HTTP status placeholder.")
    data: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="Placeholder payload for Phase 0 responses.",
    )
