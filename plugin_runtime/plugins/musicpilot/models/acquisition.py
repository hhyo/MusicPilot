"""Acquisition persistence models for Phase 3."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SearchJobModel(Base):
    __tablename__ = "search_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trigger_source: Mapped[str] = mapped_column(String(32), index=True)
    profile_id: Mapped[str] = mapped_column(String(64), default="default-lossless")
    mode: Mapped[str] = mapped_column(String(16), default="manual")
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    music_media_input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    music_meta_base: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    music_recognition_assessment: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    music_media_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    query_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidates: Mapped[list["SearchCandidateModel"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    bindings: Mapped[list["DownloadBindingModel"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class SearchCandidateModel(Base):
    __tablename__ = "search_candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    site_name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(512))
    normalized_title: Mapped[str] = mapped_column(String(512), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    seeders: Mapped[int] = mapped_column(Integer, default=0)
    peers: Mapped[int] = mapped_column(Integer, default=0)
    format_tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)
    score_total: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    decision: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    dispatch_status: Mapped[str] = mapped_column(String(32), default="pending")
    dispatchable: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[SearchJobModel] = relationship(back_populates="candidates")
    bindings: Mapped[list["DownloadBindingModel"]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )


class DownloadBindingModel(Base):
    __tablename__ = "download_bindings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("search_candidates.id", ondelete="CASCADE"),
        index=True,
    )
    target_downloader: Mapped[str] = mapped_column(String(64))
    downloader_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dispatchable: Mapped[bool] = mapped_column(Boolean, default=False)
    dispatch_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    integration_point: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    dispatched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[SearchJobModel] = relationship(back_populates="bindings")
    candidate: Mapped[SearchCandidateModel] = relationship(back_populates="bindings")
