"""Helpers for the narrow download validation flow."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from ..schemas.integration import VerificationState
from ..schemas.validation import (
    DownloadValidationHandoff,
    DownloadValidationOrganize,
    DownloadValidationReport,
    DownloadValidationSubmission,
)


def slugify_filename(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "download-validation"


def ensure_fake_music_file(
    root: Path,
    sample_name: str,
    *,
    suffix: str = ".flac",
    content: bytes | str | None = None,
) -> Path:
    sample_dir = root / slugify_filename(sample_name)
    sample_dir.mkdir(parents=True, exist_ok=True)
    file_path = sample_dir / f"{slugify_filename(sample_name)}{suffix}"
    payload = content.encode("utf-8") if isinstance(content, str) else content
    file_path.write_bytes(payload or b"MusicPilot download validation sample\n")
    return file_path


def build_download_validation_report(
    *,
    host_base_url: str,
    fake_source_path: str,
    downloader_name: str,
    download_id: str | None,
    download_hash: str | None,
    path_handoff_status: str,
    organize_record_id: str | None,
    organize_status: str | None,
    preview_id: str | None = None,
    target_library_path: str | None = None,
    target_relative_path: str | None = None,
    resolved_downloader: str | None = None,
    dispatch_status: str = "host_submitted",
    submission_success: bool = True,
    history_note: str = "history download resolved",
    organize_note: str = "organize validation completed",
    submission_note: str = "download submission completed",
    overall_status: str | None = None,
) -> DownloadValidationReport:
    submission = DownloadValidationSubmission(
        requested_downloader=downloader_name,
        resolved_downloader=resolved_downloader,
        download_id=download_id,
        dispatch_status=dispatch_status,
        success=submission_success,
        note=submission_note,
        host_response_summary={
            "download_id": download_id,
            "requested_downloader": downloader_name,
            "resolved_downloader": resolved_downloader,
        },
    )
    history = DownloadValidationHandoff(
        download_hash=download_hash,
        source_path=fake_source_path if path_handoff_status.startswith("resolved") else None,
        handoff_status=path_handoff_status,
        verification_state=VerificationState.VERIFIED
        if path_handoff_status.startswith("resolved")
        else VerificationState.UNVERIFIED,
        note=history_note,
        raw_summary={"download_hash": download_hash, "source_path": fake_source_path},
    )
    organize = DownloadValidationOrganize(
        preview_id=preview_id,
        record_id=organize_record_id,
        preview_status="preview_ready" if preview_id else None,
        apply_status=organize_status,
        target_library_path=target_library_path,
        target_relative_path=target_relative_path,
        note=organize_note,
    )
    computed_status = overall_status
    if computed_status is None:
        computed_status = (
            "success"
            if submission_success and path_handoff_status.startswith("resolved") and organize_status == "applied"
            else "partial"
        )
    return DownloadValidationReport(
        generated_at=datetime.now(timezone.utc),
        host_base_url=host_base_url,
        fake_source_path=fake_source_path,
        download_submission=submission,
        history_handoff=history,
        organize_result=organize,
        overall_status=computed_status,  # type: ignore[arg-type]
        note="Narrow validation of real submission, history handoff, and fake-file organize flow.",
    )
