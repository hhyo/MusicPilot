"""Subscription and organize persistence models for Phase 6."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subscription_type: Mapped[str] = mapped_column(String(32), index=True)
    target_id: Mapped[str] = mapped_column(String(64), index=True)
    target_name: Mapped[str] = mapped_column(String(255))
    target_entity_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    chart_source: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    chart_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    mode: Mapped[str] = mapped_column(String(32), default="manual")
    preference_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    target_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    latest_run_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    runs: Mapped[list["SubscriptionRunModel"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class SubscriptionRunModel(Base):
    __tablename__ = "subscription_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        index=True,
    )
    search_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("search_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    matched_candidates_count: Mapped[int] = mapped_column(Integer, default=0)
    dispatch_recommendation: Mapped[str] = mapped_column(String(32), default="pending")
    organize_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    subscription: Mapped[SubscriptionModel] = relationship(back_populates="runs")


class OrganizeRecordModel(Base):
    __tablename__ = "organize_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subscription_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("subscription_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    search_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("search_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    candidate_id: Mapped[str | None] = mapped_column(
        ForeignKey("search_candidates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    binding_id: Mapped[str | None] = mapped_column(
        ForeignKey("download_bindings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organizeable: Mapped[bool] = mapped_column(Boolean, default=False)
    organize_backend: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    strategy: Mapped[str | None] = mapped_column(String(64), nullable=True)
    library_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    root_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    organize_status: Mapped[str] = mapped_column(String(32), default="planned", index=True)
    target_library_path: Mapped[str] = mapped_column(Text)
    target_relative_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    conflict_policy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    strategy_note: Mapped[str] = mapped_column(Text)
    integration_point: Mapped[str] = mapped_column(Text)
    capability_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fallback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
