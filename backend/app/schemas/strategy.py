"""Schemas for matrix-aware runtime strategy decisions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HostStrategyDecision(BaseModel):
    stage: Literal["dispatch_endpoint", "path_handoff", "organize_apply"]
    selected_path: str
    matrix_status: Literal["stable", "single_sample", "flaky", "blocked", "unknown"] = "unknown"
    risk_level: Literal["low", "medium", "high", "blocked"] = "medium"
    recommended_action: str
    reason: str
    note: str
    blocked: bool = False
    source_sample_ids: list[str] = Field(default_factory=list)


class HostStrategySummary(BaseModel):
    preferred_dispatch_endpoint: str
    preferred_handoff_source: str
    preferred_organize_path: str
    caution_paths: list[str] = Field(default_factory=list)
    blocked_paths: list[str] = Field(default_factory=list)
    note: str
