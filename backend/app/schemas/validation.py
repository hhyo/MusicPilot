"""Schemas for manual real-host validation matrix exports."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .integration import VerificationState


class HostValidationMatrixEntry(BaseModel):
    sample_id: str
    sample_name: str
    search_input_type: str
    dispatch_endpoint_type: str | None = None
    path_handoff_source: str | None = None
    path_handoff_status: str | None = None
    transfer_name_result: str | None = None
    transfer_manual_result: str | None = None
    organize_result: str | None = None
    verification_state: VerificationState = VerificationState.UNVERIFIED
    stability_state: Literal["stable", "single_sample", "flaky", "blocked"] = "single_sample"
    attempt_count: int = 0
    success_count: int = 0
    blocker: str | None = None
    note: str
    last_verified_at: datetime | None = None
    raw_summary: dict = Field(default_factory=dict)


class HostValidationMatrixSummary(BaseModel):
    generated_at: datetime | None = None
    sample_count: int = 0
    stable_count: int = 0
    single_sample_count: int = 0
    blocked_count: int = 0
    flaky_count: int = 0
    verified_count: int = 0
    unverified_count: int = 0
    placeholder_count: int = 0
    note: str


class HostValidationMatrixReport(BaseModel):
    phase: str = "Phase 8"
    generated_at: datetime
    samples: list[HostValidationMatrixEntry] = Field(default_factory=list)
    summary: HostValidationMatrixSummary
    note: str


class DownloadValidationSubmission(BaseModel):
    requested_downloader: str
    resolved_downloader: str | None = None
    download_id: str | None = None
    dispatch_status: str
    success: bool = False
    note: str
    host_response_summary: dict = Field(default_factory=dict)


class DownloadValidationHandoff(BaseModel):
    download_hash: str | None = None
    source_path: str | None = None
    handoff_status: str
    verification_state: VerificationState = VerificationState.UNVERIFIED
    note: str
    raw_summary: dict = Field(default_factory=dict)


class DownloadValidationOrganize(BaseModel):
    preview_id: str | None = None
    record_id: str | None = None
    preview_status: str | None = None
    apply_status: str | None = None
    target_library_path: str | None = None
    target_relative_path: str | None = None
    note: str


class DownloadValidationReport(BaseModel):
    generated_at: datetime
    host_base_url: str
    fake_source_path: str
    download_submission: DownloadValidationSubmission
    history_handoff: DownloadValidationHandoff
    organize_result: DownloadValidationOrganize
    overall_status: Literal["success", "partial", "failed"]
    note: str
